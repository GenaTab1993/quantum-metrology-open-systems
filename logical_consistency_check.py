#!/usr/bin/env python3
"""
Logical consistency check for the Quantum Metrology Engine
==========================================================

Companion script to LOGICAL_CONSISTENCY_PROTOCOL.md.

The main simulation works in floating point, and floating-point arithmetic is
not a mathematical model of the theory. This script re-checks the theory in
EXACT arithmetic (sympy, rational and Gaussian-rational numbers), so every
"True" below is a statement about an actual mathematical structure, not about
a number that agrees up to rounding.

The model family
----------------
A "model" is a choice of
    N        number of qubits (1, 2, 3)
    probe    Product |+>^N  or  GHZ
    (c, s)   cos(phi), sin(phi) with phi = 0.4 * t  (so U(t) = tensor of c*I - i*s*X)
    (q, r)   q = sqrt(1 - p) = exp(-gamma*t/2),  r = sqrt(p),  with q^2 + r^2 = 1

(c, s) and (q, r) are chosen as Pythagorean pairs, so every matrix entry is a
rational or Gaussian-rational number and all linear algebra is exact.

Sections
--------
A. Axiom checks on every model of the family (exact).
B. Symbolic proof that the single-qubit QFI equals q^2 = 1 - p for ALL p.
C. Closed-form ideal QFI for Product and GHZ probes (symbolic in phi).
D. Independent re-derivation of the README results table (floating point).
E. Statement-status protocol: entailed / supported / independent.

Requirements: numpy, sympy.   Run:  python logical_consistency_check.py
Exit code 0 if every check passes, 1 otherwise.
"""

import itertools
import sys
import time

import numpy as np
import sympy as sp
from sympy import I, Matrix, Rational as R, eye, zeros
from sympy import QQ_I
from sympy.polys.matrices import DomainMatrix

FAILURES = []


def report(name, ok, detail=""):
    """Print one PASS/FAIL line and remember failures."""
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


# ============================================================================
# Exact linear algebra helpers
# ============================================================================

X2 = Matrix([[0, 1], [1, 0]])
Z2 = Matrix([[1, 0], [0, -1]])
I2 = eye(2)


def kron(*mats):
    out = mats[0]
    for m in mats[1:]:
        out = sp.kronecker_product(out, m)
    return out


def collective(N, pauli):
    """sum_i pauli_i acting on N qubits."""
    total = zeros(2 ** N)
    for k in range(N):
        total += kron(*[pauli if i == k else I2 for i in range(N)])
    return total


def probe_rho(N, ghz):
    """Exact density matrix of |+>^N or the N-qubit GHZ state."""
    d = 2 ** N
    if ghz:
        rho = zeros(d)
        for i in (0, d - 1):
            for j in (0, d - 1):
                rho[i, j] = R(1, 2)
        return rho
    return Matrix(d, d, lambda i, j: R(1, d))


def unitary(N, c, s):
    """U(t) = exp(-i*H*t) with H = 0.4*sum X_i, written via c = cos(0.4t), s = sin(0.4t)."""
    u = c * I2 - I * s * X2
    return kron(*[u] * N).applyfunc(sp.expand)


def kraus_ops(N, q, r):
    """Global Kraus operators of independent amplitude damping (2**N of them)."""
    e0 = Matrix([[1, 0], [0, q]])
    e1 = Matrix([[0, r], [0, 0]])
    return [kron(*choice) for choice in itertools.product([e0, e1], repeat=N)]


def channel(ops, x):
    return sum((o * x * o.H for o in ops), zeros(x.shape[0])).applyfunc(sp.expand)


def adjoint_channel(ops, a):
    return sum((o.H * a * o for o in ops), zeros(a.shape[0])).applyfunc(sp.expand)


def is_zero(m):
    return all(sp.expand(e) == 0 for e in m)


def is_hermitian(m):
    return is_zero(m - m.H)


def is_psd(m):
    """Exact PSD test for a Hermitian matrix with Gaussian-rational entries.

    The characteristic polynomial of a Hermitian matrix has only real roots.
    A real-rooted polynomial has no negative root iff all elementary symmetric
    functions of the roots are >= 0, i.e. iff (-1)^k * c_k >= 0 for every
    coefficient c_k of det(xI - M).
    """
    coeffs = DomainMatrix.from_Matrix(m).convert_to(QQ_I).charpoly()
    for k, c in enumerate(coeffs):
        value = QQ_I.to_sympy(c) * (-1) ** k
        if sp.im(value) != 0 or sp.re(value) < 0:
            return False
    return True


def solve_sld(rho, drho):
    """Exact Hermitian solution L of  drho = (L*rho + rho*L)/2.

    Row-major vectorisation turns the equation into the linear system
    (rho (x) I + I (x) rho^T) vec(L) = 2 vec(drho). The system is singular when
    rho is rank-deficient, so free variables are set to 0 and the result is
    Hermitised; (L + L^dagger)/2 solves the equation whenever L does.
    Raises ValueError if the system is inconsistent.
    """
    n = rho.shape[0]
    big = sp.kronecker_product(rho, eye(n)) + sp.kronecker_product(eye(n), rho.T)
    rhs = Matrix(n * n, 1, list(drho)) * 2
    aug = big.row_join(rhs).applyfunc(sp.expand)
    rref, pivots = DomainMatrix.from_Matrix(aug).convert_to(QQ_I).rref()
    if n * n in pivots:
        raise ValueError("SLD equation is inconsistent")
    rref = rref.to_Matrix()
    x = zeros(n * n, 1)
    for row, col in enumerate(pivots):
        x[col] = rref[row, n * n]
    L = Matrix(n, n, list(x))
    return ((L + L.H) / 2).applyfunc(sp.expand)


# ============================================================================
# Independent floating-point implementation (used for cross-checks only)
# ============================================================================

def f_kron(*mats):
    out = mats[0]
    for m in mats[1:]:
        out = np.kron(out, m)
    return out


def f_collective(N, pauli):
    i2 = np.eye(2, dtype=complex)
    return sum(f_kron(*[pauli if i == k else i2 for i in range(N)]) for k in range(N))


F_X = np.array([[0, 1], [1, 0]], dtype=complex)
F_Z = np.array([[1, 0], [0, -1]], dtype=complex)


def f_qfi(rho, drho):
    """Spectral SLD formula: F = sum_ij 2|<i|drho|j>|^2 / (p_i + p_j)."""
    w, v = np.linalg.eigh(rho)
    d = v.conj().T @ drho @ v
    total = 0.0
    for i in range(len(w)):
        for j in range(len(w)):
            if w[i] + w[j] > 1e-12:
                total += 2 * abs(d[i, j]) ** 2 / (w[i] + w[j])
    return float(total)


def f_pipeline(N, ghz, c, s, q, r):
    """Ideal and noisy QFI in floating point, given cos/sin of 0.4t and q, r."""
    dim = 2 ** N
    if ghz:
        psi = np.zeros(dim, dtype=complex)
        psi[0] = psi[-1] = 1 / np.sqrt(2)
    else:
        psi = np.ones(dim, dtype=complex) / np.sqrt(dim)
    u1 = c * np.eye(2) - 1j * s * F_X
    U = f_kron(*[u1] * N)
    rho = U @ np.outer(psi, psi.conj()) @ U.conj().T
    G = 0.5 * f_collective(N, F_Z)
    drho = -1j * (G @ rho - rho @ G)
    e0 = np.array([[1, 0], [0, q]], dtype=complex)
    e1 = np.array([[0, r], [0, 0]], dtype=complex)
    ops = [f_kron(*ch) for ch in itertools.product([e0, e1], repeat=N)]

    def apply(x):
        return sum(o @ x @ o.conj().T for o in ops)

    return f_qfi(rho, drho), f_qfi(apply(rho), apply(drho))


def f_pipeline_t(N, ghz, t, gamma=0.12, coupling=0.4):
    """Same pipeline, parametrised by time as in the main simulation."""
    phi = coupling * t
    q = np.exp(-gamma * t / 2)
    return f_pipeline(N, ghz, np.cos(phi), np.sin(phi), q, np.sqrt(1 - q * q))


# ============================================================================
# A. Axiom checks on the exact model family
# ============================================================================

PHASES = [(R(1), R(0)), (R(3, 5), R(4, 5)), (R(5, 13), R(12, 13))]
DAMPINGS = [(R(1), R(0)), (R(4, 5), R(3, 5)), (R(3, 5), R(4, 5)), (R(5, 13), R(12, 13))]
QUBIT_COUNTS = (1, 2, 3)

# Filled during section A and reused in section E.
EXACT = {}   # (N, ghz, phase_index, damping_index) -> (F_ideal, F_noisy)


def section_a():
    print("\nA. Axiom checks on exact models "
          f"(N in {QUBIT_COUNTS}, {len(PHASES)} phases, {len(DAMPINGS)} damping values, 2 probes)")
    names = [
        "evolved state: Hermitian, trace 1, pure (rho^2 = rho)",
        "Kraus completeness: sum E_k^dagger E_k = I",
        "noisy state: Hermitian, trace 1, positive semidefinite",
        "noisy derivative: Hermitian and traceless",
        "SLD equation solvable; exact solution satisfies it",
        "QFI two ways agree: Tr(rho L^2) = Tr(drho L)",
        "ideal QFI = 4 Var(G) (pure-state formula)",
        "Kraus-adjoint duality: Tr[G E(rho)] = Tr[E*(G) rho]",
        "exact QFI matches independent float implementation (1e-9)",
    ]
    tally = {n: [0, 0] for n in names}   # name -> [passed, total]
    t0 = time.time()

    for N in QUBIT_COUNTS:
        G = R(1, 2) * collective(N, Z2)
        ident = eye(2 ** N)
        for ghz in (False, True):
            rho0 = probe_rho(N, ghz)
            for pi, (c, s) in enumerate(PHASES):
                U = unitary(N, c, s)
                rho = (U * rho0 * U.H).applyfunc(sp.expand)
                drho = (-I * (G * rho - rho * G)).applyfunc(sp.expand)
                f_ideal = None
                for di, (q, r) in enumerate(DAMPINGS):
                    ops = kraus_ops(N, q, r)
                    rho_n = channel(ops, rho)
                    drho_n = channel(ops, drho)
                    results = {}

                    results[names[0]] = (is_hermitian(rho) and sp.expand(rho.trace()) == 1
                                         and is_zero(rho * rho - rho))
                    results[names[1]] = is_zero(sum((o.H * o for o in ops), zeros(2 ** N)) - ident)
                    results[names[2]] = (is_hermitian(rho_n) and sp.expand(rho_n.trace()) == 1
                                         and is_psd(rho_n))
                    results[names[3]] = is_hermitian(drho_n) and sp.expand(drho_n.trace()) == 0

                    try:
                        L = solve_sld(rho_n, drho_n)
                        results[names[4]] = is_zero(drho_n - (L * rho_n + rho_n * L) / 2)
                        f_noisy = sp.expand((drho_n * L).trace())
                        results[names[5]] = sp.expand((rho_n * L * L).trace() - f_noisy) == 0
                    except ValueError:
                        results[names[4]] = results[names[5]] = False
                        f_noisy = None

                    if f_ideal is None:   # ideal QFI does not depend on damping
                        Li = solve_sld(rho, drho)
                        f_ideal = sp.expand((drho * Li).trace())
                    var_g = sp.expand((rho * G * G).trace() - (rho * G).trace() ** 2)
                    results[names[6]] = sp.expand(4 * var_g - f_ideal) == 0

                    lhs = sp.expand((G * rho_n).trace())
                    rhs = sp.expand((adjoint_channel(ops, G) * rho).trace())
                    results[names[7]] = sp.expand(lhs - rhs) == 0

                    fi, fn = f_pipeline(N, ghz, float(c), float(s), float(q), float(r))
                    results[names[8]] = (f_noisy is not None
                                         and abs(float(f_noisy) - fn) < 1e-9
                                         and abs(float(f_ideal) - fi) < 1e-9)

                    for n_, ok in results.items():
                        tally[n_][1] += 1
                        tally[n_][0] += bool(ok)
                    EXACT[(N, ghz, pi, di)] = (f_ideal, f_noisy)

    total_models = len(EXACT)
    for n_ in names:
        passed, total = tally[n_]
        report(n_, passed == total, f"{passed}/{total} models")
    print(f"  ({total_models} models, {time.time() - t0:.1f}s)")


# ============================================================================
# B. Symbolic single-qubit theorem: F = q^2 = 1 - p for every p in (0, 1)
# ============================================================================

def positive_on_unit_interval(expr, q):
    """True if the rational function expr(q) is strictly positive for every 0 < q < 1.

    Each polynomial factor of numerator and denominator must have no real root
    inside (0, 1) and be positive at q = 1/2, so its sign never changes there.
    """
    num, den = sp.fraction(sp.together(expr))
    sign = 1
    for part in (num, den):
        for factor, _ in sp.factor_list(part)[1]:
            poly = sp.Poly(factor, q)
            if poly.is_zero:
                return False
            if any(0 < root < 1 for root in sp.real_roots(poly)):
                return False
            value = poly.eval(R(1, 2))
            sign *= 1 if value > 0 else -1
        constant = sp.factor_list(part)[0]
        sign *= 1 if constant > 0 else -1
    return sign > 0


def section_b():
    print("\nB. Single-qubit benchmark, symbolic in the damping parameter")
    q, r = sp.symbols("q r", positive=True)        # q = sqrt(1-p), r = sqrt(p), q^2 + r^2 = 1
    rho0 = Matrix([[R(1, 2), R(1, 2)], [R(1, 2), R(1, 2)]])
    G = Z2 / 2
    d0 = -I * (G * rho0 - rho0 * G)
    e0 = Matrix([[1, 0], [0, q]])
    e1 = Matrix([[0, r], [0, 0]])
    rho_n = (e0 * rho0 * e0.H + e1 * rho0 * e1.H).applyfunc(sp.expand)
    d_n = (e0 * d0 * e0.H + e1 * d0 * e1.H).applyfunc(sp.expand)

    # r enters only through r^2 (the E1 term is quadratic in E1), so the relation
    # q^2 + r^2 = 1 can be applied exactly by substituting r^2 = 1 - q^2.
    rho_n = rho_n.applyfunc(lambda e: sp.expand(e.subs(r ** 2, 1 - q ** 2)))
    d_n = d_n.applyfunc(lambda e: sp.expand(e.subs(r ** 2, 1 - q ** 2)))
    report("noisy state and derivative depend on the damping only through q",
           not any(e.has(r) for e in list(rho_n) + list(d_n)))

    big = sp.kronecker_product(rho_n, eye(2)) + sp.kronecker_product(eye(2), rho_n.T)
    det = sp.factor(big.det())
    x = big.LUsolve(Matrix(4, 1, list(d_n)) * 2)
    L = Matrix(2, 2, list(x))
    L = ((L + L.H) / 2).applyfunc(sp.simplify)
    F = sp.simplify((d_n * L).trace())

    residual = (d_n - (L * rho_n + rho_n * L) / 2).applyfunc(sp.simplify)
    report("SLD equation holds identically in q", is_zero(residual))
    report("F_Q(q) - q^2 = 0 identically  (so F_Q = 1 - p for all p)",
           sp.simplify(F - q ** 2) == 0, f"[F_Q = {F}]")
    report("the Lyapunov system is nonsingular for every 0 < q < 1  (the SLD is unique)",
           positive_on_unit_interval(det, q), f"[determinant = {det}]")


# ============================================================================
# C. Closed-form ideal QFI (symbolic in phi = 0.4 t)
# ============================================================================

def section_c():
    print("\nC. Closed-form ideal QFI, symbolic in phi = 0.4 t")
    phi = sp.symbols("phi", real=True)
    expected_ghz = {
        2: 2 + 2 * sp.cos(4 * phi),
        3: 9 - 6 * sp.sin(2 * phi) ** 2,
        4: 16 - 12 * sp.sin(2 * phi) ** 2,
    }
    for N in (1, 2, 3, 4):
        G = R(1, 2) * collective(N, Z2)
        u = sp.cos(phi) * I2 - I * sp.sin(phi) * X2
        U = kron(*[u] * N)
        d = 2 ** N
        for ghz in (False, True):
            if ghz:
                v = zeros(d, 1)
                v[0] = v[d - 1] = 1 / sp.sqrt(2)
            else:
                v = Matrix([1] * d) / sp.sqrt(d)
            w = U * v
            m1 = (w.H * G * w)[0]
            m2 = (w.H * G * G * w)[0]
            F = sp.simplify(sp.trigsimp(sp.expand(4 * (m2 - m1 ** 2))))
            if not ghz:
                report(f"N={N} Product: ideal QFI = {N} for every phi", sp.simplify(F - N) == 0)
            elif N == 1:
                report("N=1 GHZ = |+>: ideal QFI = 1 for every phi", sp.simplify(F - 1) == 0)
            else:
                ok = sp.simplify(sp.trigsimp(F - expected_ghz[N])) == 0
                report(f"N={N} GHZ: ideal QFI = {sp.simplify(expected_ghz[N])}", ok)


# ============================================================================
# D. Independent re-derivation of the README results table
# ============================================================================

README_TABLE = [  # (probe, t, ideal, noisy)
    ("Product", 0.00, 3.000000, 3.000000), ("GHZ", 0.00, 9.000000, 9.000000),
    ("Product", 0.15, 3.000000, 2.946483), ("GHZ", 0.15, 8.914014, 8.672599),
    ("Product", 0.30, 3.000000, 2.893921), ("GHZ", 0.30, 8.660985, 8.187613),
    ("Product", 0.45, 3.000000, 2.842296), ("GHZ", 0.45, 8.255417, 7.569258),
    ("Product", 0.60, 3.000000, 2.791593), ("GHZ", 0.60, 7.720560, 6.852148),
]


def section_d():
    print("\nD. README results table, re-derived with the independent implementation (N = 3)")
    worst = 0.0
    for probe, t, ideal, noisy in README_TABLE:
        fi, fn = f_pipeline_t(3, probe == "GHZ", t)
        worst = max(worst, abs(fi - ideal), abs(fn - noisy))
    report("all 10 table rows (ideal and noisy) reproduced to 6 decimals",
           worst < 5e-7, f"max deviation {worst:.2e}")
    closed = [9 - 6 * np.sin(2 * 0.4 * t) ** 2 for _, t, _, _ in README_TABLE[1::2]]
    table_ghz = [row[2] for row in README_TABLE[1::2]]
    dev = max(abs(a - b) for a, b in zip(closed, table_ghz))
    report("README ideal GHZ column equals the closed form 9 - 6 sin^2(0.8 t)",
           dev < 5e-7, f"max deviation {dev:.2e}")


# ============================================================================
# E. Statement-status protocol
# ============================================================================
#
# For a statement phi about the model family there are three outcomes:
#   ENTAILED     phi holds in every model examined, and an exact/symbolic argument
#                shows why it must (no countermodel can exist within the family).
#   SUPPORTED    phi holds in every model examined, but only as exact checks on
#                sampled models, not as a proof for all parameters.
#   INDEPENDENT  there is an exact model where phi holds AND an exact model where
#                it fails, so the theory alone does not decide phi.
# ============================================================================

def exact_f(N, ghz, pi, di):
    return EXACT[(N, ghz, pi, di)]


def section_e():
    print("\nE. Statement-status protocol")
    statuses = []

    # S1: Product ideal QFI = N for all t  (entailed by section C)
    ok = all(exact_f(N, False, pi, di)[0] == N
             for N in QUBIT_COUNTS for pi in range(len(PHASES)) for di in range(len(DAMPINGS)))
    report("S1  Product ideal QFI = N for all t", ok,
           "ENTAILED (symbolic closed form, section C, N <= 4; exact on all sampled models)")
    statuses.append(("S1", "ENTAILED"))

    # S2: Product noisy QFI = N * q^2 = N (1 - p)
    ok = all(exact_f(N, False, pi, di)[1] == N * DAMPINGS[di][0] ** 2
             for N in QUBIT_COUNTS for pi in range(len(PHASES)) for di in range(len(DAMPINGS)))
    report("S2  Product noisy QFI = N (1 - p)", ok,
           "SUPPORTED (exact on sampled models; N = 1 proved symbolically in section B)")
    statuses.append(("S2", "SUPPORTED"))

    # S3: noise never increases the QFI
    ok = all(exact_f(*k)[1] <= exact_f(*k)[0] for k in EXACT)
    report("S3  noisy QFI <= ideal QFI", ok,
           f"SUPPORTED (exact on {len(EXACT)} models; expected from data processing)")
    statuses.append(("S3", "SUPPORTED"))

    # S4: ideal QFI <= N^2 (spread of the generator's spectrum)
    ok = all(exact_f(N, g, pi, 0)[0] <= N ** 2
             for N in QUBIT_COUNTS for g in (False, True) for pi in range(len(PHASES)))
    report("S4  ideal QFI <= N^2", ok,
           "ENTAILED for N <= 4 by the closed forms in section C (their maxima are N^2)")
    statuses.append(("S4", "ENTAILED"))

    # S5: noisy GHZ > noisy Product for every damping value: INDEPENDENT
    c, s = R(1), R(0)                                   # t = 0
    G = R(1, 2) * collective(3, Z2)

    def noisy_pair(q, r):
        out = []
        for ghz in (True, False):
            rho = probe_rho(3, ghz)
            d = (-I * (G * rho - rho * G)).applyfunc(sp.expand)
            ops = kraus_ops(3, q, r)
            rn, dn = channel(ops, rho), channel(ops, d)
            out.append(sp.expand((dn * solve_sld(rn, dn)).trace()))
        return out

    q_win, r_win = R(4, 5), R(3, 5)
    q_lose, r_lose = R(3, 5), R(4, 5)
    g_win, p_win = noisy_pair(q_win, r_win)
    g_lose, p_lose = noisy_pair(q_lose, r_lose)
    holds_somewhere = g_win > p_win
    fails_somewhere = g_lose < p_lose
    report("S5  noisy GHZ QFI > noisy Product QFI (N = 3) for every damping value",
           holds_somewhere and fails_somewhere,
           "INDEPENDENT of the theory")
    print(f"        model where S5 holds: q = 4/5  ->  GHZ {g_win} = {float(g_win):.4f}, "
          f"Product {p_win} = {float(p_win):.4f}")
    print(f"        model where S5 fails: q = 3/5  ->  GHZ {g_lose} = {float(g_lose):.4f}, "
          f"Product {p_lose} = {float(p_lose):.4f}")
    lo, hi = 0.3, 0.95                                   # locate the crossover (float)
    for _ in range(60):
        mid = (lo + hi) / 2
        fg = f_pipeline(3, True, 1.0, 0.0, mid, np.sqrt(1 - mid * mid))[1]
        fp = f_pipeline(3, False, 1.0, 0.0, mid, np.sqrt(1 - mid * mid))[1]
        lo, hi = (mid, hi) if fg < fp else (lo, mid)
    print(f"        crossover at t = 0: q* = {lo:.4f}, i.e. p* = {1 - lo * lo:.4f} "
          "(GHZ wins for smaller damping)")
    statuses.append(("S5", "INDEPENDENT"))

    # S6: ideal GHZ QFI >= ideal Product QFI for every t: depends on N
    #   N = 2: closed form 2 + 2 cos(4 phi) dips below 2; exact witness below.
    c, s = R(3, 5), R(4, 5)
    G2 = R(1, 2) * collective(2, Z2)
    rho = (unitary(2, c, s) * probe_rho(2, True) * unitary(2, c, s).H).applyfunc(sp.expand)
    d = (-I * (G2 * rho - rho * G2)).applyfunc(sp.expand)
    f2 = sp.expand((d * solve_sld(rho, d)).trace())
    closed2 = sp.nsimplify(2 + 2 * sp.cos(4 * sp.acos(sp.Rational(3, 5))))
    n3_min = min(float(9 - 6 * np.sin(2 * ph) ** 2) for ph in np.linspace(0, np.pi, 4001))
    report("S6  ideal GHZ QFI >= ideal Product QFI for every t (all N >= 2)",
           f2 < 2 and n3_min >= 3 - 1e-12,
           "INDEPENDENT of the theory: depends on N")
    print(f"        N = 2 fails:  at cos(0.4t) = 3/5, GHZ = {f2} = {float(f2):.4f} < Product = 2"
          f"  (closed form gives {closed2})")
    print(f"        N = 3 holds:  closed form 9 - 6 sin^2(2 phi) has minimum {n3_min:.4f} = Product value 3")
    statuses.append(("S6", "INDEPENDENT"))

    # S7: README regime: noisy GHZ > noisy Product for gamma = 0.12, t in [0, 0.6]
    ts = np.linspace(0, 0.6, 61)
    ok = all(f_pipeline_t(3, True, t)[1] > f_pipeline_t(3, False, t)[1] - 1e-12 for t in ts)
    margin = min(f_pipeline_t(3, True, t)[1] - f_pipeline_t(3, False, t)[1] for t in ts)
    report("S7  README regime (N = 3, gamma = 0.12, 0 <= t <= 0.6): noisy GHZ > noisy Product", ok,
           f"HOLDS in the tested regime only (smallest margin {margin:.3f}); see S5")
    statuses.append(("S7", "REGIME-ONLY"))

    print("\n  Status summary: " + ", ".join(f"{k}={v}" for k, v in statuses))


# ============================================================================
# main
# ============================================================================

def main():
    print("=" * 78)
    print("Logical consistency check: Quantum Metrology Engine (exact arithmetic)")
    print("=" * 78)
    section_a()
    section_b()
    section_c()
    section_d()
    section_e()
    print("\n" + "=" * 78)
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED:")
        for name in FAILURES:
            print("  -", name)
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
