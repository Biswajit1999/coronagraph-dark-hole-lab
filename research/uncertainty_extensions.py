"""Reproducible reduced-order coronagraph uncertainty and observing-time diagnostics.

All coefficients are illustrative, not Roman CGI performance calibrations.
Inputs: wavelength nm, WFE pm, jitter mas, rates electrons/second.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

RAD_TO_MAS = 206_264_806.247


def exact_top_hat_phase_leakage(wfe_pm: float, centre_nm: float, fractional_width: float) -> float:
    """Closed-form uniform-band mean of 0.01*(2*pi*WFE/lambda)**2.

    For a top-hat centred on lambda0 with full fractional width f,
    <lambda^-2> = lambda0^-2/(1-f**2/4). Valid for 0<=f<2.
    """
    if not all(np.isfinite([wfe_pm, centre_nm, fractional_width])):
        raise ValueError("parameters must be finite")
    if wfe_pm < 0 or centre_nm <= 0 or not 0 <= fractional_width < 2:
        raise ValueError("WFE nonnegative; centre positive; 0 <= width < 2")
    phase = 2 * np.pi * wfe_pm * 1e-3 / centre_nm
    return float(0.01 * phase**2 / (1 - fractional_width**2 / 4))


def top_hat_quadrature_audit(
    wfe_pm: float = 24.0,
    centre_nm: float = 575.0,
    fractional_width: float = 0.2,
    grids: tuple[int, ...] = (5, 9, 17, 33, 65, 129),
) -> list[dict[str, float]]:
    """Independently check trapezoid integration against an exact integral."""
    reference = exact_top_hat_phase_leakage(wfe_pm, centre_nm, fractional_width)
    if not grids or any(int(n) != n or n < 2 for n in grids):
        raise ValueError("grids must contain integers >=2")
    out = []
    for n in grids:
        x = np.linspace(centre_nm * (1 - fractional_width / 2),
                        centre_nm * (1 + fractional_width / 2), int(n))
        if fractional_width == 0:
            estimate = reference
        else:
            y = 0.01 * (2 * np.pi * wfe_pm * 1e-3 / x)**2
            estimate = float(np.trapezoid(y, x) / np.ptp(x))
        out.append({"grid_size": int(n), "trapezoid_contrast": estimate,
                    "exact_contrast": reference,
                    "absolute_error": abs(estimate - reference),
                    "relative_error": abs(estimate - reference) / reference if reference else 0.0})
    return out


def _jitter_scale(wavelength_nm: float, diameter_m: float) -> float:
    if not all(np.isfinite([wavelength_nm, diameter_m])) or wavelength_nm <= 0 or diameter_m <= 0:
        raise ValueError("positive finite wavelength and aperture required")
    return wavelength_nm * 1e-9 / diameter_m * RAD_TO_MAS


@dataclass(frozen=True)
class JitterUncertainty:
    nominal_contrast: float
    delta_method_sigma: float
    monte_carlo_mean: float
    monte_carlo_sigma: float
    monte_carlo_p05: float
    monte_carlo_p95: float
    trials: int
    invalid_draw_fraction: float


def correlated_jitter_uncertainty(
    nominal: tuple[float, float, float],
    covariance: np.ndarray,
    *,
    wavelength_nm: float = 575.0,
    diameter_m: float = 2.4,
    trials: int = 50_000,
    seed: int = 20261017,
) -> JitterUncertainty:
    """Delta-method and Monte Carlo for C=C0+k*(jitter/(lambda/D))**2.

    Parameters are (base contrast, coupling, RMS jitter in mas). Covariance
    uses the same units in row/column order; off-diagonal terms are retained.
    Untruncated Gaussian draws are used for delta-method comparability. The
    reported invalid fraction flags draws with physically negative parameters.
    """
    mu = np.asarray(nominal, dtype=float)
    cov = np.asarray(covariance, dtype=float)
    if mu.shape != (3,) or cov.shape != (3, 3) or trials < 100:
        raise ValueError("nominal shape (3,), covariance (3,3), trials>=100")
    if not np.all(np.isfinite(mu)) or not np.all(np.isfinite(cov)) or np.any(mu < 0):
        raise ValueError("finite nonnegative nominal values and finite covariance required")
    if not np.allclose(cov, cov.T, rtol=1e-10, atol=1e-24):
        raise ValueError("covariance must be symmetric")
    if np.min(np.linalg.eigvalsh(cov)) < -1e-22:
        raise ValueError("covariance must be positive semidefinite")
    scale = _jitter_scale(wavelength_nm, diameter_m)
    c0, k, j = mu
    gradient = np.array([1., (j / scale)**2, 2 * k * j / scale**2])
    delta_variance = float(gradient @ cov @ gradient)
    if delta_variance < -1e-20:
        raise ValueError("negative delta variance")
    rng = np.random.default_rng(seed)
    draws = rng.multivariate_normal(mu, cov, size=trials, check_valid="raise", tol=1e-12)
    invalid = float(np.mean(np.any(draws < 0, axis=1)))
    contrast = draws[:, 0] + draws[:, 1] * (draws[:, 2] / scale)**2
    return JitterUncertainty(
        nominal_contrast=float(c0 + k * (j / scale)**2),
        delta_method_sigma=float(np.sqrt(max(0., delta_variance))),
        monte_carlo_mean=float(np.mean(contrast)),
        monte_carlo_sigma=float(np.std(contrast, ddof=1)),
        monte_carlo_p05=float(np.quantile(contrast, .05)),
        monte_carlo_p95=float(np.quantile(contrast, .95)),
        trials=trials,
        invalid_draw_fraction=invalid,
    )


def background_subtracted_snr(
    science_s: float,
    background_s: float,
    planet_rate_eps: float,
    nuisance_rate_eps: float,
    *,
    read_noise_e: float = 1.5,
    science_reads: int = 12,
    background_reads: int = 12,
) -> float:
    """Expected SNR of S-(ts/tb)*B for independent science/background frames.

    Variance = (P+N)*ts + N*ts**2/tb + r**2*(ns+(ts/tb)**2*nb).
    Ignores overheads, drift, systematic backgrounds and temporal correlations.
    """
    values = (science_s, background_s, planet_rate_eps, nuisance_rate_eps, read_noise_e)
    if not all(np.isfinite(values)) or science_s <= 0 or background_s <= 0 or any(v < 0 for v in values[2:]):
        raise ValueError("exposures positive and all rates/read noise nonnegative and finite")
    if science_reads < 1 or background_reads < 1:
        raise ValueError("read counts must be positive")
    ratio = science_s / background_s
    variance = ((planet_rate_eps + nuisance_rate_eps) * science_s
                + nuisance_rate_eps * science_s * ratio
                + read_noise_e**2 * (science_reads + ratio**2 * background_reads))
    return float(planet_rate_eps * science_s / np.sqrt(variance)) if variance > 0 else 0.0


def exposure_allocation_sweep(
    total_s: float = 3600.,
    planet_rate_eps: float = 0.08,
    nuisance_rate_eps: float = 0.47,
    *,
    read_noise_e: float = 1.5,
    science_reads: int = 12,
    background_reads: int = 12,
    grid_points: int = 199,
) -> dict[str, object]:
    """Grid-search optimal science/background split under a fixed wall-clock budget."""
    if total_s <= 0 or not np.isfinite(total_s) or grid_points < 5:
        raise ValueError("total_s>0 and grid_points>=5 required")
    fractions = np.linspace(.01, .99, grid_points)
    snr = [background_subtracted_snr(total_s*f, total_s*(1-f),
                                    planet_rate_eps, nuisance_rate_eps,
                                    read_noise_e=read_noise_e,
                                    science_reads=science_reads,
                                    background_reads=background_reads)
           for f in fractions]
    index = int(np.argmax(snr))
    equal_snr = background_subtracted_snr(total_s/2, total_s/2,
                                          planet_rate_eps, nuisance_rate_eps,
                                          read_noise_e=read_noise_e,
                                          science_reads=science_reads,
                                          background_reads=background_reads)
    photon_fraction = (np.sqrt(planet_rate_eps+nuisance_rate_eps) /
                       (np.sqrt(planet_rate_eps+nuisance_rate_eps)+np.sqrt(nuisance_rate_eps))) if nuisance_rate_eps > 0 else 1.0
    return {"optimal_science_fraction": float(fractions[index]),
            "optimal_snr": float(snr[index]), "equal_split_snr": float(equal_snr),
            "photon_limit_optimal_fraction": float(photon_fraction),
            "relative_gain_vs_equal": float(snr[index] / equal_snr - 1) if equal_snr else 0.,
            "rows": [{"science_fraction": float(f), "snr": float(s)} for f, s in zip(fractions, snr, strict=True)]}


def example_summary() -> dict[str, object]:
    """Stable seeded synthetic illustration; not a measured contrast or SNR."""
    mu = (1e-9, 2e-7, 1.)
    std = np.array([1e-10, 1e-8, .05])
    corr = np.array([[1., .25, 0.], [.25, 1., -.3], [0., -.3, 1.]])
    covariance = np.outer(std, std) * corr
    return {"quadrature": top_hat_quadrature_audit(),
            "jitter": asdict(correlated_jitter_uncertainty(mu, covariance)),
            "allocation": exposure_allocation_sweep()}
