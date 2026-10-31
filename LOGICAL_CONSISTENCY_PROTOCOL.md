# Logical Consistency Protocol

A model-theoretic consistency check for the theory behind the Quantum Metrology Engine, based on Gödel's completeness theorem. The check is carried out by `logical_consistency_check.py` in exact arithmetic. For the theory and the numerical results, see [README.md](README.md).

This protocol tests whether the mathematical theory used in the project is **internally consistent** and which of its claims are **decided by the theory itself**. It does not test whether the theory describes real physical systems. No experimental data is involved.

---

## 1. What the Completeness Theorem Provides

Gödel's completeness theorem (1929) connects syntax and semantics for first-order logic. For a theory $`T`$ and a sentence $`\varphi`$:

```math
T \models \varphi \iff T \vdash \varphi
```

Here $`T \models \varphi`$ means that $`\varphi`$ is true in every model of $`T`$, and $`T \vdash \varphi`$ means that $`\varphi`$ can be derived from $`T`$. Two consequences are used in this protocol:

1. **Consistency through a model.** $`T`$ is consistent (it does not prove a contradiction) if and only if it has a model. Exhibiting one exact model of all the axioms therefore shows consistency.
2. **Independence through two models.** $`\varphi`$ is independent of $`T`$ (neither provable nor refutable) if and only if some model of $`T`$ satisfies $`\varphi`$ and another model of $`T`$ satisfies $`\neg\varphi`$.

The theorem does **not** say that a physical theory covers every phenomenon, and it says nothing about experiments. The related incompleteness theorems of Gödel apply to theories that contain arithmetic, and they limit what can be said about statements quantified over all $`N`$ (Section 6).

---

## 2. The Theory Under Test

For a fixed number of qubits $`N`$, the objects are complex matrices of size $`2^N \times 2^N`$. The theory $`T`$ consists of the following axioms.

| Axiom | Content |
|---|---|
| A1 | A state $`\rho`$ is Hermitian, positive semidefinite, with $`\mathrm{Tr}\,\rho = 1`$. |
| A2 | Amplitude damping has Kraus operators $`E_0 = \mathrm{diag}(1, q)`$ and $`E_1 = \begin{pmatrix} 0 & r \\ 0 & 0 \end{pmatrix}`$ with $`q^2 + r^2 = 1`$, applied independently to each qubit, and $`\sum_k E_k^\dagger E_k = I`$. |
| A3 | Evolution is $`U(t) = e^{-iHt}`$ with $`H = 0.4\sum_i X_i`$. |
| A4 | Phase encoding gives $`\partial_\theta\rho = -i[G, \rho]`$ with $`G = \tfrac{1}{2}\sum_i Z_i`$, and the channel acts on the derivative as $`\partial_\theta\rho_{\text{out}} = \mathcal{E}(\partial_\theta\rho)`$. |
| A5 | The SLD $`L`$ is a Hermitian solution of $`\partial_\theta\rho = \tfrac{1}{2}(L\rho + \rho L)`$. |
| A6 | The QFI is $`F_Q = \mathrm{Tr}(\rho L^2)`$. |
| A7 | Duality: $`\mathrm{Tr}[A\,\mathcal{E}(\rho)] = \mathrm{Tr}[\mathcal{E}^*(A)\,\rho]`$ with $`\mathcal{E}^*(A) = \sum_k E_k^\dagger A E_k`$. |
| A8 | Time enters through $`c = \cos(0.4t)`$, $`s = \sin(0.4t)`$ with $`c^2 + s^2 = 1`$, and through the damping law $`q = e^{-\gamma t/2}`$ with $`0 < q \leq 1`$. |

Because $`c, s, q, r`$ are treated as real parameters constrained by polynomial relations, every statement about the QFI can be written in the first-order language of real closed fields (real and imaginary parts of the matrix entries are real variables). The first-order theory of real closed fields is complete and decidable (Tarski), which is why a model-based check within this family is meaningful. The script does not implement a decision procedure. It exhibits exact models and exact symbolic identities.

---

## 3. The Protocol

1. **Formalize.** State the axioms A1–A8 and the statements to be classified.
2. **Build exact models.** Choose parameter values with rational $`c, s, q, r`$ (Pythagorean pairs such as $`(3/5, 4/5)`$ and $`(5/13, 12/13)`$), so that every matrix entry is a rational or Gaussian-rational number. Floating-point numbers are not a model of the theory, so they are used only for cross-checks.
3. **Check the axioms in every model.** Each axiom is verified with exact arithmetic (Section 5.1). A model in which all axioms hold is a consistency witness.
4. **Prove what can be proved symbolically.** Single-qubit and closed-form results are derived symbolically, valid for all parameter values (Sections 5.2 and 5.3).
5. **Classify statements.** Each statement is labeled ENTAILED, SUPPORTED, or INDEPENDENT (Section 5.5).
6. **Link to the numerics.** The results table in the README is re-derived with a separate implementation (Section 5.4).

The labels mean:

- **ENTAILED:** holds in every model examined, and an exact or symbolic argument shows it must.
- **SUPPORTED:** holds in every model examined, as exact checks on sampled models only, not as a proof for all parameters.
- **INDEPENDENT:** an exact model satisfies it and another exact model refutes it, so the theory alone does not decide it.

---

## 4. The Model Family

| Parameter | Values |
|---|---|
| Qubits $`N`$ | 1, 2, 3 |
| Probe | Product $`\lvert +\rangle^{\otimes N}`$, GHZ |
| $`(c, s)`$ | $`(1, 0)`$, $`(3/5, 4/5)`$, $`(5/13, 12/13)`$ |
| $`(q, r)`$ | $`(1, 0)`$, $`(4/5, 3/5)`$, $`(3/5, 4/5)`$, $`(5/13, 12/13)`$ |

This gives $`3 \times 2 \times 3 \times 4 = 72`$ exact models.

---

## 5. Results

All 30 checks pass (`python logical_consistency_check.py`, about 13 seconds). The full output is in the appendix.

### 5.1 Axiom checks on all 72 models (exact)

| Check | Models passed |
|---|---|
| Evolved state is Hermitian, has trace 1, and is pure ($`\rho^2 = \rho`$) | 72 / 72 |
| Kraus completeness | 72 / 72 |
| Noisy state is Hermitian, has trace 1, and is positive semidefinite (exact test through the characteristic polynomial) | 72 / 72 |
| Noisy derivative is Hermitian and traceless | 72 / 72 |
| SLD equation has an exact Hermitian solution | 72 / 72 |
| $`\mathrm{Tr}(\rho L^2) = \mathrm{Tr}(\partial\rho\, L)`$ | 72 / 72 |
| Ideal QFI equals the pure-state formula $`4\,\mathrm{Var}(G)`$ | 72 / 72 |
| Kraus-adjoint duality | 72 / 72 |
| Exact QFI agrees with an independent floating-point implementation to $`10^{-9}`$ | 72 / 72 |

A model satisfying all axioms exists, so by the model-existence direction of the completeness theorem the axiom set A1–A8 is consistent for $`N = 1, 2, 3`$ in the sampled region.

### 5.2 Single-qubit benchmark for all $`p`$ (symbolic)

Because $`r`$ enters the noisy state only through $`r^2`$, the relation $`q^2 + r^2 = 1`$ can be applied exactly by substituting $`r^2 = 1 - q^2`$, and the problem depends on $`q`$ alone. Solving the Lyapunov equation symbolically gives:

```math
F_Q(q) = q^2 = 1 - p \qquad \text{for every } 0 < q < 1
```

The determinant of the Lyapunov system is $`q^2(1 - q^2)`$, which is strictly positive on $`(0, 1)`$, so the SLD is unique. This replaces the single-point check at $`p = 0.25`$ in the main simulation with an identity valid for all $`p`$.

### 5.3 Closed-form ideal QFI (symbolic in $`\phi = 0.4t`$)

| Probe | Ideal QFI |
|---|---|
| Product, $`N = 1, 2, 3, 4`$ | $`N`$ (independent of $`\phi`$) |
| GHZ, $`N = 2`$ | $`2 + 2\cos 4\phi`$ |
| GHZ, $`N = 3`$ | $`9 - 6\sin^2 2\phi`$ |
| GHZ, $`N = 4`$ | $`16 - 12\sin^2 2\phi`$ |

For $`N = 3`$ the GHZ value at $`\phi = 0.4t`$ is $`9 - 6\sin^2(0.8t)`$. The maximum is $`N^2`$ in each case.

### 5.4 The README table, re-derived independently

A separate implementation reproduces all 10 rows of the README results table (ideal and noisy QFI) to six decimals, with a maximum deviation of $`4.2\times10^{-7}`$, which is the rounding of the printed values. The ideal GHZ column also matches the closed form $`9 - 6\sin^2(0.8t)`$ (maximum deviation $`2.3\times10^{-7}`$).

### 5.5 Statement classification

| # | Statement | Status | Evidence |
|---|---|---|---|
| S1 | Product ideal QFI equals $`N`$ for all $`t`$ | ENTAILED | Symbolic closed form for $`N \leq 4`$; exact on all sampled models |
| S2 | Product noisy QFI equals $`N(1-p)`$ | SUPPORTED | Exact on all sampled models; $`N = 1`$ proved symbolically for all $`p`$ |
| S3 | Noise never increases the QFI | SUPPORTED | Exact on 72 models; expected from data processing |
| S4 | Ideal QFI is at most $`N^2`$ | ENTAILED | Closed forms for $`N \leq 4`$ |
| S5 | Noisy GHZ beats noisy Product ($`N = 3`$) for every damping value | **INDEPENDENT** | Holds at $`q = 4/5`$, fails at $`q = 3/5`$ (below) |
| S6 | Ideal GHZ is at least the ideal Product for every $`t`$ (all $`N \geq 2`$) | **INDEPENDENT** | Fails for $`N = 2`$, holds for $`N = 3`$ (below) |
| S7 | Noisy GHZ beats noisy Product for $`N = 3`$, $`\gamma = 0.12`$, $`0 \leq t \leq 0.6`$ | Holds in this regime only | Smallest margin 4.06 over 61 sampled times |

**S5, exact witnesses at $`t = 0`$, $`N = 3`$:**

| $`q`$ | GHZ noisy QFI | Product noisy QFI | S5 |
|---|---|---|---|
| $`4/5`$ | $`36864/10225 \approx 3.605`$ | $`48/25 = 1.92`$ | holds |
| $`3/5`$ | $`6561/10225 \approx 0.642`$ | $`27/25 = 1.08`$ | fails |

The crossover at $`t = 0`$ is at $`q^* \approx 0.676`$, that is, $`p^* \approx 0.543`$. For larger damping the Product probe wins.

**S6, witnesses:** for $`N = 2`$ at $`\cos(0.4t) = 3/5`$, the GHZ ideal QFI is exactly $`196/625 \approx 0.314`$, below the Product value 2. For $`N = 3`$ the closed form $`9 - 6\sin^2 2\phi`$ has minimum exactly 3, equal to the Product value.

---

## 6. What This Means for the README

- The README already restricts its GHZ-versus-Product conclusion to the tested configuration. S5 and S6 show that this restriction is necessary: the theory does not decide the ordering in general. The advantage reverses for $`p \gtrsim 0.54`$ ($`N = 3`$, $`t = 0`$), and for $`N = 2`$ the ideal GHZ probe falls below the Product probe at some times.
- The README results table is reproducible by an independent implementation.
- S1, S2 and the single-qubit identity give exact closed forms for quantities the README currently reports as numbers.

## 7. Limits

- **Sampled models, not all parameters.** SUPPORTED means exact checks on the 72 sampled models, not a proof for all parameter values. Only the single-qubit result (5.2) and the closed forms (5.3) are symbolic.
- **Exact arithmetic on rational parameters.** The models use rational $`c, s, q, r`$. Irrational parameters, such as the physical values $`q = e^{-\gamma t/2}`$, are covered only through the float cross-checks.
- **Fixed $`N`$.** The completeness theorem is first-order. Statements quantified over all $`N`$ involve arithmetic, where Gödel's incompleteness theorems apply, so no complete axiomatization of such statements exists. The protocol checks $`N = 1, 2, 3`$ (closed forms up to $`N = 4`$).
- **Floating point is not a model.** The main simulation runs in floating point, so its output is evidence, not a model of the theory. The $`1.066\times10^{-14}`$ residual in the README is a property of the machine used and was not reproduced exactly on another machine (it was $`1.421\times10^{-14}`$ in one re-run).
- **Consistency is not physical truth.** The axioms are a formalization of the model used in the code. A consistent theory can still be physically wrong, and only experiments can test that.
- **Statement set.** The classification covers seven statements chosen for this protocol, not every claim made in the README.

## 8. Running the Check

Requirements: Python 3, NumPy, SymPy.

```bash
python logical_consistency_check.py
```

The script prints each check as PASS or FAIL and exits with code 0 if all checks pass, or 1 otherwise.

---

## Appendix: Output of the Run

```text
==============================================================================
Logical consistency check: Quantum Metrology Engine (exact arithmetic)
==============================================================================

A. Axiom checks on exact models (N in (1, 2, 3), 3 phases, 4 damping values, 2 probes)
  [PASS] evolved state: Hermitian, trace 1, pure (rho^2 = rho)  72/72 models
  [PASS] Kraus completeness: sum E_k^dagger E_k = I  72/72 models
  [PASS] noisy state: Hermitian, trace 1, positive semidefinite  72/72 models
  [PASS] noisy derivative: Hermitian and traceless  72/72 models
  [PASS] SLD equation solvable; exact solution satisfies it  72/72 models
  [PASS] QFI two ways agree: Tr(rho L^2) = Tr(drho L)  72/72 models
  [PASS] ideal QFI = 4 Var(G) (pure-state formula)  72/72 models
  [PASS] Kraus-adjoint duality: Tr[G E(rho)] = Tr[E*(G) rho]  72/72 models
  [PASS] exact QFI matches independent float implementation (1e-9)  72/72 models
  (72 models, 10.5s)

B. Single-qubit benchmark, symbolic in the damping parameter
  [PASS] noisy state and derivative depend on the damping only through q
  [PASS] SLD equation holds identically in q
  [PASS] F_Q(q) - q^2 = 0 identically  (so F_Q = 1 - p for all p)  [F_Q = q**2]
  [PASS] the Lyapunov system is nonsingular for every 0 < q < 1  (the SLD is unique)  [determinant = -q**2*(q - 1)*(q + 1)]

C. Closed-form ideal QFI, symbolic in phi = 0.4 t
  [PASS] N=1 Product: ideal QFI = 1 for every phi
  [PASS] N=1 GHZ = |+>: ideal QFI = 1 for every phi
  [PASS] N=2 Product: ideal QFI = 2 for every phi
  [PASS] N=2 GHZ: ideal QFI = 2*cos(4*phi) + 2
  [PASS] N=3 Product: ideal QFI = 3 for every phi
  [PASS] N=3 GHZ: ideal QFI = 9 - 6*sin(2*phi)**2
  [PASS] N=4 Product: ideal QFI = 4 for every phi
  [PASS] N=4 GHZ: ideal QFI = 16 - 12*sin(2*phi)**2

D. README results table, re-derived with the independent implementation (N = 3)
  [PASS] all 10 table rows (ideal and noisy) reproduced to 6 decimals  max deviation 4.22e-07
  [PASS] README ideal GHZ column equals the closed form 9 - 6 sin^2(0.8 t)  max deviation 2.32e-07

E. Statement-status protocol
  [PASS] S1  Product ideal QFI = N for all t  ENTAILED (symbolic closed form, section C, N <= 4; exact on all sampled models)
  [PASS] S2  Product noisy QFI = N (1 - p)  SUPPORTED (exact on sampled models; N = 1 proved symbolically in section B)
  [PASS] S3  noisy QFI <= ideal QFI  SUPPORTED (exact on 72 models; expected from data processing)
  [PASS] S4  ideal QFI <= N^2  ENTAILED for N <= 4 by the closed forms in section C (their maxima are N^2)
  [PASS] S5  noisy GHZ QFI > noisy Product QFI (N = 3) for every damping value  INDEPENDENT of the theory
        model where S5 holds: q = 4/5  ->  GHZ 36864/10225 = 3.6053, Product 48/25 = 1.9200
        model where S5 fails: q = 3/5  ->  GHZ 6561/10225 = 0.6417, Product 27/25 = 1.0800
        crossover at t = 0: q* = 0.6763, i.e. p* = 0.5426 (GHZ wins for smaller damping)
  [PASS] S6  ideal GHZ QFI >= ideal Product QFI for every t (all N >= 2)  INDEPENDENT of the theory: depends on N
        N = 2 fails:  at cos(0.4t) = 3/5, GHZ = 196/625 = 0.3136 < Product = 2  (closed form gives 196/625)
        N = 3 holds:  closed form 9 - 6 sin^2(2 phi) has minimum 3.0000 = Product value 3
  [PASS] S7  README regime (N = 3, gamma = 0.12, 0 <= t <= 0.6): noisy GHZ > noisy Product  HOLDS in the tested regime only (smallest margin 4.061); see S5

  Status summary: S1=ENTAILED, S2=SUPPORTED, S3=SUPPORTED, S4=ENTAILED, S5=INDEPENDENT, S6=INDEPENDENT, S7=REGIME-ONLY

==============================================================================
All checks passed.
```
