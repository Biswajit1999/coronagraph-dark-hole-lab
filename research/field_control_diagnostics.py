"""Synthetic complex-field coronagraph control and pairwise-probe diagnostics.

These are linearized mathematical experiments, NOT Roman CGI predictions.
Fields are in arbitrary sqrt-count units and actuator strokes are arbitrary.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class EFCSolution:
    strokes: np.ndarray
    initial_intensity: float
    residual_intensity: float
    stroke_norm: float
    design_condition: float


def _field_and_jacobian(field: np.ndarray, jacobian: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    e = np.asarray(field, dtype=complex)
    g = np.asarray(jacobian, dtype=complex)
    if e.ndim != 1 or g.ndim != 2 or g.shape[0] != e.size or e.size == 0 or g.shape[1] == 0:
        raise ValueError("field must be (pixels,) and Jacobian (pixels, actuators)")
    if not (np.all(np.isfinite(e)) and np.all(np.isfinite(g))):
        raise ValueError("field and Jacobian must be finite")
    return e, g


def efc_solve(field: np.ndarray, jacobian: np.ndarray, alpha: float = 0.0,
              pixel_weights: np.ndarray | None = None) -> EFCSolution:
    """Real-valued DM commands minimizing sum(w*|E+G@u|²)+alpha*||u||².

    Augmented least squares avoids squaring the Jacobian condition number.
    The returned residual is evaluated using the supplied Jacobian, not a
    physical coronagraph propagator. Zero weights are allowed.
    """
    e, g = _field_and_jacobian(field, jacobian)
    if not np.isfinite(alpha) or alpha < 0:
        raise ValueError("alpha must be finite and non-negative")
    w = np.ones(e.size) if pixel_weights is None else np.asarray(pixel_weights, dtype=float)
    if w.shape != e.shape or np.any(~np.isfinite(w)) or np.any(w < 0) or not np.any(w > 0):
        raise ValueError("pixel weights must be finite, non-negative and nonzero")
    sw = np.sqrt(w)
    design = np.concatenate(((sw[:, None] * g).real, (sw[:, None] * g).imag), axis=0)
    target = -np.concatenate(((sw * e).real, (sw * e).imag))
    if alpha > 0:
        design_aug = np.vstack((design, np.sqrt(alpha) * np.eye(g.shape[1])))
        target_aug = np.concatenate((target, np.zeros(g.shape[1])))
    else:
        design_aug, target_aug = design, target
    strokes = np.linalg.lstsq(design_aug, target_aug, rcond=None)[0]
    residual = e + g @ strokes
    singular = np.linalg.svd(design, compute_uv=False)
    condition = float(singular[0] / singular[-1]) if singular[-1] > 0 else float("inf")
    return EFCSolution(
        strokes=strokes,
        initial_intensity=float(np.sum(w * abs(e)**2) / np.sum(w)),
        residual_intensity=float(np.sum(w * abs(residual)**2) / np.sum(w)),
        stroke_norm=float(np.linalg.norm(strokes)),
        design_condition=condition,
    )


def pairwise_probe_estimate(probe_fields: np.ndarray, intensity_differences: np.ndarray,
                            difference_variances: np.ndarray) -> tuple[complex, np.ndarray]:
    """Estimate complex E from I(E+p)-I(E-p)=4 Re(conj(E)*p).

    Independent Gaussian approximation to intensity-difference errors. Return
    complex estimate and 2x2 covariance for (Re E, Im E). Singular probe
    geometries are rejected rather than yielding spurious precision.
    """
    p = np.asarray(probe_fields, dtype=complex)
    d = np.asarray(intensity_differences, dtype=float)
    v = np.asarray(difference_variances, dtype=float)
    if p.ndim != 1 or p.size < 2 or d.shape != p.shape or v.shape != p.shape:
        raise ValueError("at least two matching probe/difference/variance values required")
    if not (np.all(np.isfinite(p)) and np.all(np.isfinite(d)) and np.all(np.isfinite(v))):
        raise ValueError("probe measurements must be finite")
    if np.any(v <= 0):
        raise ValueError("variances must be positive")
    h = 4 * np.column_stack((p.real, p.imag))
    whitened = h / np.sqrt(v[:, None])
    if np.linalg.matrix_rank(whitened) < 2:
        raise ValueError("probes do not identify both field quadratures")
    cov = np.linalg.inv(whitened.T @ whitened)
    estimate = cov @ (whitened.T @ (d / np.sqrt(v)))
    return complex(estimate[0], estimate[1]), cov


def synthetic_probe_recovery(*, seed: int = 20261028, trials: int = 20_000,
                             read_noise_e: float = 1.0) -> dict[str, float]:
    """Poisson plus independent Gaussian-read-noise probe-pair recovery test."""
    if trials < 2 or not np.isfinite(read_noise_e) or read_noise_e < 0:
        raise ValueError("invalid trial count or read noise")
    rng = np.random.default_rng(seed)
    true_e = 3.0 + 2.0j
    probes = np.array([1.3 + 0.1j, -0.2 + 1.4j, 1.0 - 0.8j])
    plus = abs(true_e + probes)**2
    minus = abs(true_e - probes)**2
    variance = plus + minus + 2 * read_noise_e**2
    differences = (rng.poisson(plus, (trials, len(probes)))
                   - rng.poisson(minus, (trials, len(probes)))
                   + rng.normal(0, np.sqrt(2) * read_noise_e, (trials, len(probes))))
    estimates = np.array([pairwise_probe_estimate(probes, row, variance)[0] for row in differences])
    _, cov = pairwise_probe_estimate(probes, plus - minus, variance)
    sample_cov = np.cov(np.column_stack((estimates.real, estimates.imag)), rowvar=False)
    return {
        "trials": trials,
        "true_real": true_e.real, "true_imag": true_e.imag,
        "mean_real": float(np.mean(estimates.real)),
        "mean_imag": float(np.mean(estimates.imag)),
        "predicted_sigma_real": float(np.sqrt(cov[0, 0])),
        "predicted_sigma_imag": float(np.sqrt(cov[1, 1])),
        "empirical_sigma_real": float(np.sqrt(sample_cov[0, 0])),
        "empirical_sigma_imag": float(np.sqrt(sample_cov[1, 1])),
    }


def synthetic_efc_sensitivity(*, seed: int = 20261028,
                              alphas: tuple[float, ...] = (0.0, 0.001, 0.01, 0.1, 1.0),
                              mismatch_fractions: tuple[float, ...] = (0.0, 0.05, 0.15, 0.3)) -> dict[str, object]:
    """Separate regularization/stroke tradeoff and true-Jacobian mismatch tests."""
    rng = np.random.default_rng(seed)
    field = (rng.normal(size=12) + 1j * rng.normal(size=12)) / np.sqrt(2)
    true_g = (rng.normal(size=(12, 30)) + 1j * rng.normal(size=(12, 30))) / np.sqrt(60)
    noise_g = (rng.normal(size=true_g.shape) + 1j * rng.normal(size=true_g.shape))
    noise_g *= np.linalg.norm(true_g) / np.linalg.norm(noise_g)
    regularization = []
    for alpha in alphas:
        s = efc_solve(field, true_g, float(alpha))
        regularization.append({"alpha": float(alpha), "residual_intensity": s.residual_intensity,
                               "stroke_norm": s.stroke_norm})
    mismatch = []
    for fraction in mismatch_fractions:
        model_g = true_g + fraction * noise_g
        s = efc_solve(field, model_g, 0.01)
        actual = float(np.mean(abs(field + true_g @ s.strokes)**2))
        mismatch.append({"relative_jacobian_error": float(fraction),
                         "predicted_intensity": s.residual_intensity,
                         "true_model_intensity": actual})
    return {"kind": "seeded linearized synthetic model", "regularization": regularization,
            "jacobian_mismatch": mismatch}
