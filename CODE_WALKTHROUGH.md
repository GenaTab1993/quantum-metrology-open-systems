# Code Walkthrough: Quantum Metrology Engine

A step-by-step explanation of what the simulation does and how the code is organized. For the full theory, the complete results table, and the validation details, see [README.md](README.md). The code itself is in `quantum-metrology-open-systems.ipynb`.

---

## Step 1: The Chronological Physical Pipeline

In the simulation, the density matrix $`\rho`$ of a multi-qubit register passes through four physical stages, sampled at discrete times:

1. **Probe State Preparation** ($`\rho_0`$): The system starts either in a separable Product state ($`|+\rangle^{\otimes N}`$) or in a maximally entangled Greenberger-Horne-Zeilinger state ($`|\mathrm{GHZ}\rangle`$).
2. **Unitary Pre-Evolution** ($`U(t)`$): Before the parameter is encoded, the probe evolves under a transverse Pauli-$`X`$ Hamiltonian ($`H = 0.4 \sum_i X_i`$), a sum of single-qubit terms.
3. **Parameter Encoding** ($`\theta`$): The unknown parameter $`\theta`$ is encoded on the evolved state through the collective phase generator $`G = \frac{1}{2} \sum_i Z_i`$.
4. **Open System Dissipation** ($`\mathcal{E}`$): Each qubit undergoes independent amplitude damping (energy relaxation) from its environment.

---

## Step 2: The Core Algebraic Engine – Resolving the SLD Matrix

Because the damping channel turns pure states into mixed states, a statevector description is no longer sufficient. The engine evaluates sensitivity through the Symmetric Logarithmic Derivative (SLD) equation:

```math
\frac{\partial \rho}{\partial \theta} = \frac{1}{2}\left( L_\theta \rho + \rho L_\theta \right)
```

To solve this Lyapunov-type equation numerically, the engine diagonalizes the noisy output density matrix, $`\rho = \sum_i p_i |i\rangle\langle i|`$. Projecting the parameter derivative onto this eigenbasis gives the QFI as the sum:

```math
F_Q = \sum_{i,j} \frac{2\,\left|\langle i|\,\partial_\theta \rho\,|j\rangle\right|^2}{p_i + p_j}
```

The QFI sets the quantum Cramér-Rao bound on the variance of any unbiased estimator $`\hat{\theta}`$, where $`\nu`$ is the number of independent repetitions:

```math
\mathrm{Var}(\hat{\theta}) \geq \frac{1}{\nu F_Q}
```

A higher QFI therefore lowers the bound on the achievable variance.

---

## Step 3: Software Core Infrastructure and Function Architecture

The code is organized into separate functional blocks.

### 1. Numerical Validation and Spectral Solver

- **`verify_physical_state` and `verify_density_derivative`:** Validation functions that check physical requirements numerically, within a tolerance. They check that $`\mathrm{Tr}(\rho) = 1`$, that $`\rho`$ is Hermitian ($`\rho = \rho^\dagger`$) and positive semi-definite (via its eigenvalues), and that $`\mathrm{Tr}(\partial_\theta \rho) = 0`$.
- **`compute_generalized_mixed_qfi`:** Evaluates the SLD sum above. It skips terms where $`p_i + p_j`$ is not larger than a small threshold (`if denominator > tol`), which excludes the zero-eigenvalue subspace of $`\rho`$ and avoids division by zero. The final QFI value is clamped at zero from below, so tiny negative round-off errors do not produce a negative result.

### 2. Tensor Products and Quantum Channels

- **`tensor_product_operators`:** Builds Kronecker products of a sequence of local operators, which gives global operators of dimension $`2^N \times 2^N`$ ($`8 \times 8`$ for the 3-qubit setup).
- **`build_amplitude_damping_kraus`:** Builds the $`2^N`$ global Kraus operators for independent amplitude damping with damping probability $`p`$. In the main loop, $`p(t) = 1 - e^{-\gamma t}`$.
- **`apply_dual_kraus_map`:** Implements the adjoint channel, $`\mathcal{E}^*(A) = \sum_k E_k^\dagger A E_k`$, used in the duality check on observable expectation values.

---

## Step 4: Quantitative Execution, Logs, and Visual Interpretation

Here is the full console output from the simulation:

```text
====================================================================================
QUANTUM METROLOGY ENGINE — QFI ANALYSIS
====================================================================================
State            t         p      Ideal QFI      Noisy QFI
------------------------------------------------------------------------------------
[CHECK] Single-qubit benchmark at p = 0.25
        Numerical QFI : 0.75000000
        Theory (1 - p): 0.75000000
        Residual      : 5.551e-16
------------------------------------------------------------------------------------
Product      0.000   0.00000       3.000000       3.000000
GHZ          0.000   0.00000       9.000000       9.000000
Product      0.150   0.01784       3.000000       2.946483
GHZ          0.150   0.01784       8.914014       8.672599
Product      0.300   0.03536       3.000000       2.893921
GHZ          0.300   0.03536       8.660985       8.187613
Product      0.450   0.05257       3.000000       2.842296
GHZ          0.450   0.05257       8.255417       7.569258
Product      0.600   0.06947       3.000000       2.791593
GHZ          0.600   0.06947       7.720560       6.852148
------------------------------------------------------------------------------------
CONSISTENCY CHECKS
Maximum ideal QFI picture residual : 1.066e-14
Maximum Kraus duality residual      : 2.220e-16
[OK] Single-qubit analytical benchmark passed.
[OK] Ideal-picture QFI invariance passed.
[OK] Kraus-adjoint duality check passed.
```

### Panel 1: Product-State Analysis (Baseline)

- **Ideal QFI = 3.000000:** Constant at all sampled times. The initial state $`|+\rangle^{\otimes N}`$ is an eigenstate of the Hamiltonian, so it only acquires a global phase during the pre-evolution.
- **Noisy QFI = 2.791593** (t = 0.6, time-step index 4): A 6.95% reduction relative to the ideal value. In this simulation the Product probe loses a smaller fraction of its QFI to damping than the GHZ probe (6.95% versus 11.25% at t = 0.6).

### Panel 2: Entangled GHZ-State Analysis

- **Ideal QFI (t = 0) = 9.000000:** This is the Heisenberg scaling for this generator ($`F_Q = N^2 = 3^2 = 9`$).
- **Ideal QFI (t = 0.6) = 7.720560:** A 14.2% drop in the ideal case. The GHZ state is not an eigenstate of the Hamiltonian, so the evolution changes the state before the parameter is encoded, which changes its sensitivity to the generator.
- **Noisy QFI = 6.852148:** Damping lowers it by 11.25% relative to the ideal value at t = 0.6, a larger fractional loss than for the Product probe. Even so, it is about 2.45 times the noisy Product QFI at this time. This is a result for this three-qubit configuration only.

### Residual and Duality Verification (Panels 3 and 4)

- **Maximum ideal QFI picture residual: 1.066e-14** (in the reported run). For ideal unitary evolution, the Schrödinger and Heisenberg calculations agree to within floating-point precision.
- **Maximum Kraus duality residual: 2.220e-16.** The identity

  ```math
  \mathrm{Tr}\left[ A\,\mathcal{E}(\rho) \right] = \mathrm{Tr}\left[ \mathcal{E}^*(A)\,\rho \right]
  ```

  holds to machine precision for the tested states, which is a consistency check of the Kraus implementation. The noisy QFI is computed directly from the damped state and its derivative, so no commutator shortcut is assumed under noise.
