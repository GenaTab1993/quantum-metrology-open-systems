# Worked Example: The Single-Qubit QFI Benchmark

A hand calculation of the single-qubit check that the code runs ($`N = 1`$, $`p = 0.25`$), followed line by line against the code. For the overall structure of the code, see [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md). For the full theory and results, see [README.md](README.md).

---

## Step 0: Defining the Input and the Initial State ($`\rho_0`$)

We feed the code a single qubit ($`N = 1`$) in the plus state.

**In the code:**

```python
ZERO = np.array([[1], [0]], dtype=complex)
ONE = np.array([[0], [1]], dtype=complex)
PLUS = (ZERO + ONE) / np.sqrt(2) # [1/sqrt(2), 1/sqrt(2)]
rho0 = PLUS @ PLUS.conj().T
```

**Mathematically and physically:** The state vector is $`|\psi_0\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle)`$. The initial density matrix $`\rho_0 = |\psi_0\rangle\langle\psi_0|`$ is computed as an outer product:

```math
\rho_0 = \begin{pmatrix} \frac{1}{2} & \frac{1}{2} \\ \frac{1}{2} & \frac{1}{2} \end{pmatrix}
```

---

## Step 1: Parameter Encoding (Schrödinger Picture)

In the analytical single-qubit check, the initial state directly undergoes unitary phase encoding under the rotation generator $`G = \frac{1}{2}Z`$. We want to compute the rate of change of the state with respect to the angle parameter $`\theta`$ (the partial derivative $`\partial_\theta \rho`$) at the point $`\theta = 0`$.

**In the code:**

```python
generator = 0.5 * Z  # Z = [[1, 0], [0, -1]]
d_rho = -1j * (generator @ rho0 - rho0 @ generator)
```

**The physical and mathematical computation (the commutator):**

```math
G = \begin{pmatrix} 0.5 & 0 \\ 0 & -0.5 \end{pmatrix}
```

Let us compute the products:

```math
G\rho_0 = \begin{pmatrix} 0.25 & 0.25 \\ -0.25 & -0.25 \end{pmatrix}, \qquad \rho_0 G = \begin{pmatrix} 0.25 & -0.25 \\ 0.25 & -0.25 \end{pmatrix}
```

We subtract them to obtain the commutator $`[G, \rho_0]`$:

```math
[G, \rho_0] = G\rho_0 - \rho_0 G = \begin{pmatrix} 0 & 0.5 \\ -0.5 & 0 \end{pmatrix}
```

We multiply by $`-i`$ (which is `-1j` in the code):

```math
\texttt{d\_rho} = -i \begin{pmatrix} 0 & 0.5 \\ -0.5 & 0 \end{pmatrix} = \begin{pmatrix} 0 & -0.5i \\ 0.5i & 0 \end{pmatrix}
```

This is the ideal derivative matrix that passes validation in `verify_density_derivative`. Its trace is 0 and it is fully Hermitian.

---

## Step 2: Applying the Non-Unitary Noise Channel (Kraus Channel)

Now we inject the noise. Assume a fixed damping probability $`p = 0.25`$ (as in the check in the code's main function). The Kraus operators for amplitude damping are defined as follows:

```math
E_0 = \begin{pmatrix} 1 & 0 \\ 0 & \sqrt{1-0.25} \end{pmatrix} = \begin{pmatrix} 1 & 0 \\ 0 & \frac{\sqrt{3}}{2} \end{pmatrix}, \qquad E_1 = \begin{pmatrix} 0 & \sqrt{0.25} \\ 0 & 0 \end{pmatrix} = \begin{pmatrix} 0 & 0.5 \\ 0 & 0 \end{pmatrix}
```

**In the code:**

```python
rho_out = apply_kraus_channel(rho0, kraus_ops)
d_rho_out = apply_kraus_channel(d_rho, kraus_ops)
```

**The matrix computations of the channel** $`\sum_k E_k \rho E_k^\dagger`$:

For the state $`\rho_0`$:

```math
E_0 \rho_0 E_0^\dagger = \begin{pmatrix} 0.5 & 0.25\sqrt{3} \\ 0.25\sqrt{3} & 0.375 \end{pmatrix}, \qquad E_1 \rho_0 E_1^\dagger = \begin{pmatrix} 0.125 & 0 \\ 0 & 0 \end{pmatrix}
```

We add them to obtain the outgoing noisy state $`\rho_{\text{out}}`$:

```math
\rho_{\text{out}} = \begin{pmatrix} 0.5 + 0.125 & 0.25\sqrt{3} \\ 0.25\sqrt{3} & 0.375 \end{pmatrix} = \begin{pmatrix} 0.625 & 0.433 \\ 0.433 & 0.375 \end{pmatrix}
```

Note that the trace of the matrix is $`0.625 + 0.375 = 1.0`$ (probability is conserved, as confirmed by `verify_physical_state`).

For the derivative matrix $`\texttt{d\_rho}`$: because the Kraus operators do not depend on $`\theta`$, the channel acts linearly and in the same way on the derivative:

```math
E_0 (\texttt{d\_rho}) E_0^\dagger = \begin{pmatrix} 0 & -0.25i\sqrt{3} \\ 0.25i\sqrt{3} & 0 \end{pmatrix}, \qquad E_1 (\texttt{d\_rho}) E_1^\dagger = \begin{pmatrix} 0 & 0 \\ 0 & 0 \end{pmatrix}
```

We add them to obtain the outgoing noisy state derivative $`\texttt{d\_rho}_{\text{out}}`$:

```math
\texttt{d\_rho}_{\text{out}} = \begin{pmatrix} 0 & -0.433i \\ 0.433i & 0 \end{pmatrix}
```

---

## Step 3: Solving the SLD Equation and Extracting the Final QFI

Now the generic engine `compute_generalized_mixed_qfi` takes the noisy inputs we computed: $`\rho_{\text{out}}`$ and $`\texttt{d\_rho}_{\text{out}}`$.

**1. Diagonalization (spectral decomposition):** The code extracts the eigenvalues ($`p_i`$) and eigenvectors of $`\rho_{\text{out}}`$ using `np.linalg.eigh`. For our matrix, the eigenvalues are:

```math
p_1 = \frac{4 - \sqrt{13}}{8} \approx 0.0493, \qquad p_2 = \frac{4 + \sqrt{13}}{8} \approx 0.9507
```

**2. Projecting the derivative onto the eigenbasis** (`d_rho_eigenbasis`): The code changes the basis of the derivative matrix using the eigenvectors ($`V^\dagger\, \texttt{d\_rho}_{\text{out}}\, V`$). The resulting matrix has zero diagonal entries, and its off-diagonal entries have magnitude $`\frac{\sqrt{3}}{4} \approx 0.433`$, so $`|d_{12}|^2 = \frac{3}{16} = 0.1875`$.

**3. The spectral summation loop of the SLD:** The code runs over all index pairs. Only the two off-diagonal terms are nonzero, and for both the denominator is $`p_1 + p_2 = 1.0`$:

```math
F_Q = \frac{2|d_{12}|^2}{p_1 + p_2} + \frac{2|d_{21}|^2}{p_2 + p_1} = 2 \times 0.1875 + 2 \times 0.1875 = 0.75000000
```

---

## Final Output and Rendering to Graphs

The exact numerical result printed to the terminal is:

```text
[CHECK] Single-qubit benchmark at p = 0.25
        Numerical QFI : 0.75000000
        Theory (1 - p): 0.75000000
        Residual      : 5.551e-16
```

The value matches the closed-form analytical result:

```math
F_Q = 1 - p = 1 - 0.25 = 0.75
```

When the extended 3-qubit experiment is run in `main()`, the code collects these values over 5 time steps, passes them to the matplotlib plotting functions, and produces the four-panel PNG file. It shows the QFI decay curves alongside numerical residuals at the floating-point level ($`10^{-14}`$ to $`10^{-16}`$).
