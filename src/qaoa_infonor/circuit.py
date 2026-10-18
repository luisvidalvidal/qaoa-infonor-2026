"""Verify direct statevector QAOA against the logical gate decomposition."""
import math
import numpy as np

from .experiment import instance, statevector_probs


def apply_rz(amp, theta, qubit):
    indices = np.arange(amp.size)
    z = 1 - 2 * ((indices >> qubit) & 1)
    return amp * np.exp(-0.5j * theta * z)


def apply_cnot(amp, control, target):
    indices = np.arange(amp.size)
    mapped = indices ^ ((((indices >> control) & 1) << target))
    out = np.empty_like(amp)
    out[mapped] = amp
    return out


def apply_rx(amp, beta, qubit):
    out = amp.copy()
    step = 1 << qubit
    c, s = np.cos(beta), -1j * np.sin(beta)
    for start in range(0, amp.size, 2 * step):
        a = np.arange(start, start + step)
        b = a + step
        va, vb = amp[a].copy(), amp[b].copy()
        out[a] = c * va + s * vb
        out[b] = s * va + c * vb
    return out


def ising_coefficients(inst, penalty=None, alpha=None):
    penalty = inst["penalty"] if penalty is None else penalty
    alpha = inst["alpha"] if alpha is None else alpha
    n, k = inst["n"], inst["k"]
    q = penalty * (1 - 2 * k) - inst["s"]
    qij = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            qij[i, j] = 2 * penalty - alpha * inst["w"][i, j]
    h = np.array([
        -q[i] / 2 - sum(qij[min(i, j), max(i, j)] for j in range(n) if j != i) / 4
        for i in range(n)
    ])
    J = qij / 4
    c = penalty * k * k + q.sum() / 2 + sum(
        qij[i, j] for i in range(n) for j in range(i + 1, n)
    ) / 4
    return c, h, J


def direct_statevector(inst, theta, p):
    n = inst["n"]
    gamma, beta = np.asarray(theta[:p]), np.asarray(theta[p:])
    amp = np.full(2**n, 1 / math.sqrt(2**n), dtype=complex)
    for layer in range(p):
        amp *= np.exp(-1j * gamma[layer] * inst["C"])
        for i in range(n):
            amp = apply_rx(amp, beta[layer], i)
    return amp


def decomposed_statevector(inst, theta, p, include_constant=True):
    n = inst["n"]
    gamma, beta = np.asarray(theta[:p]), np.asarray(theta[p:])
    amp = np.full(2**n, 1 / np.sqrt(2**n), dtype=complex)
    c, h, J = ising_coefficients(inst)
    for layer in range(p):
        if include_constant:
            amp *= np.exp(-1j * gamma[layer] * c)
        for i in range(n):
            amp = apply_rz(amp, 2 * gamma[layer] * h[i], i)
        for i in range(n):
            for j in range(i + 1, n):
                amp = apply_cnot(amp, i, j)
                amp = apply_rz(amp, 2 * gamma[layer] * J[i, j], j)
                amp = apply_cnot(amp, i, j)
        for i in range(n):
            amp = apply_rx(amp, beta[layer], i)
    return amp


def phase_aligned_error(reference, candidate):
    overlap = np.vdot(candidate, reference)
    phase = overlap / abs(overlap)
    return float(np.max(np.abs(reference - phase * candidate)))


if __name__ == "__main__":
    maximum_with_c = 0.0
    maximum_phase_aligned = 0.0
    maximum_probability = 0.0
    for n in (4, 6, 8):
        inst = instance(n)
        for p in (1, 2, 3):
            gamma = np.linspace(0.173, 0.731, p)
            beta = np.linspace(0.419, 1.237, p)
            theta = np.r_[gamma, beta]
            direct = direct_statevector(inst, theta, p)
            with_c = decomposed_statevector(inst, theta, p, include_constant=True)
            without_c = decomposed_statevector(inst, theta, p, include_constant=False)
            maximum_with_c = max(maximum_with_c, float(np.max(np.abs(direct - with_c))))
            maximum_phase_aligned = max(
                maximum_phase_aligned, phase_aligned_error(direct, without_c)
            )
            expected_probs = statevector_probs(inst, theta, p)
            maximum_probability = max(
                maximum_probability,
                float(np.max(np.abs(expected_probs - np.abs(with_c) ** 2))),
            )
    assert maximum_with_c < 1e-12, f"amplitude error with c {maximum_with_c:.3e}"
    assert maximum_phase_aligned < 1e-12, f"phase-aligned error {maximum_phase_aligned:.3e}"
    assert maximum_probability < 1e-12, f"probability error {maximum_probability:.3e}"
    print(
        f"OK: max amplitude error with c = {maximum_with_c:.3e}; "
        f"max phase-aligned error without c = {maximum_phase_aligned:.3e}; "
        f"max probability error = {maximum_probability:.3e}"
    )
