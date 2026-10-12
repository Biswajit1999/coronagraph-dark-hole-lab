"""Reduced-order robustness analyses for high-contrast imaging.

Every result in this module is a model prediction or a synthetic recovery test.
It is not a measurement of Roman CGI performance.  Wavelengths are nanometres,
wavefront errors are picometres RMS, angles are milliarcseconds, and count rates
are electrons per second.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np

RAD_TO_MAS = 206_264_806.247


def phase_leakage_contrast(wfe_pm: float, wavelength_nm: np.ndarray) -> np.ndarray:
    """Return the small-phase surrogate ``0.01 (2 pi sigma/lambda)^2``."""
    if wfe_pm < 0 or np.any(np.asarray(wavelength_nm) <= 0):
        raise ValueError("WFE must be non-negative and wavelength positive")
    ratio = (wfe_pm * 1e-3) / np.asarray(wavelength_nm, dtype=float)
    return 0.01 * (2.0 * np.pi * ratio) ** 2


def broadband_leakage(
    wfe_pm: float,
    centre_nm: float,
    fractional_bandwidth: float,
    samples: int,
) -> float:
    """Integrate leakage over a uniform top-hat spectral band.

    Trapezoidal quadrature is used so its convergence can be audited directly.
    A zero-width band evaluates the monochromatic limit.
    """
    if centre_nm <= 0 or not 0 <= fractional_bandwidth < 2 or samples < 2:
        raise ValueError("invalid band definition")
    if fractional_bandwidth == 0:
        return float(phase_leakage_contrast(wfe_pm, np.array([centre_nm]))[0])
    half_width = 0.5 * centre_nm * fractional_bandwidth
    wavelength = np.linspace(centre_nm - half_width, centre_nm + half_width, samples)
    contrast = phase_leakage_contrast(wfe_pm, wavelength)
    return float(np.trapezoid(contrast, wavelength) / (2.0 * half_width))


def quadrature_convergence(
    wfe_pm: float = 24.0,
    centre_nm: float = 575.0,
    fractional_bandwidth: float = 0.20,
    sample_counts: Iterable[int] = (5, 9, 17, 33, 65, 129),
) -> list[dict[str, float]]:
    """Compare finite spectral grids with a 65,537-point reference integral."""
    reference = broadband_leakage(wfe_pm, centre_nm, fractional_bandwidth, 65_537)
    rows = []
    for count in sample_counts:
        estimate = broadband_leakage(wfe_pm, centre_nm, fractional_bandwidth, int(count))
        rows.append(
            {
                "samples": int(count),
                "contrast": estimate,
                "relative_error": abs(estimate - reference) / reference,
            }
        )
    return rows


def lambda_over_d_mas(wavelength_nm: float, diameter_m: float) -> float:
    """Angular diffraction scale lambda/D in milliarcseconds."""
    if wavelength_nm <= 0 or diameter_m <= 0:
        raise ValueError("wavelength and diameter must be positive")
    return wavelength_nm * 1e-9 / diameter_m * RAD_TO_MAS


def jitter_leakage(
    base_contrast: float,
    jitter_mas: np.ndarray,
    wavelength_nm: float = 575.0,
    diameter_m: float = 2.4,
    coupling: float = 2.0e-7,
) -> np.ndarray:
    """Quadratic low-order leakage surrogate versus RMS pointing jitter.

    ``C = C_base + k (sigma_theta / (lambda/D))^2``.  The coefficient ``k`` is
    explicitly illustrative and is varied by the sensitivity analysis.
    """
    jitter = np.asarray(jitter_mas, dtype=float)
    if base_contrast < 0 or coupling < 0 or np.any(jitter < 0):
        raise ValueError("contrast, coupling, and jitter must be non-negative")
    scale = lambda_over_d_mas(wavelength_nm, diameter_m)
    return base_contrast + coupling * (jitter / scale) ** 2


def jitter_sensitivity(
    jitter_grid_mas: Iterable[float] = (0, 0.2, 0.5, 1.0, 1.5, 2.0),
    coupling_values: Iterable[float] = (1.0e-7, 2.0e-7, 4.0e-7),
    base_contrast: float = 1.0e-9,
) -> list[dict[str, float]]:
    """Sweep jitter and uncertain low-order coupling without fitting observations."""
    rows = []
    grid = np.asarray(tuple(jitter_grid_mas), dtype=float)
    for coupling in coupling_values:
        contrast = jitter_leakage(base_contrast, grid, coupling=float(coupling))
        for jitter, value in zip(grid, contrast, strict=True):
            rows.append(
                {"jitter_mas_rms": float(jitter), "coupling": float(coupling), "contrast": float(value)}
            )
    return rows


@dataclass(frozen=True)
class RecoverySummary:
    trials: int
    exposure_s: float
    injected_planet_electrons: float
    mean_recovered_electrons: float
    recovery_bias_fraction: float
    empirical_sigma_electrons: float
    analytic_sigma_electrons: float
    empirical_snr: float
    analytic_snr: float


def synthetic_count_recovery(
    *,
    trials: int = 20_000,
    seed: int = 20261011,
    exposure_s: float = 1_800.0,
    planet_rate_eps: float = 0.08,
    residual_starlight_rate_eps: float = 0.35,
    background_rate_eps: float = 0.12,
    read_noise_e: float = 1.5,
    reads: int = 12,
) -> RecoverySummary:
    """Recover a synthetic planet count signal with an independent background frame.

    The science and background frames have equal exposure.  Their difference is
    unbiased for the injected planet signal; Poisson variance from both frames
    and Gaussian read noise from both read stacks is propagated analytically.
    """
    values = (exposure_s, planet_rate_eps, residual_starlight_rate_eps, background_rate_eps, read_noise_e)
    if trials < 100 or reads < 1 or any(value < 0 for value in values) or exposure_s == 0:
        raise ValueError("invalid recovery configuration")
    rng = np.random.default_rng(seed)
    planet = planet_rate_eps * exposure_s
    nuisance = (residual_starlight_rate_eps + background_rate_eps) * exposure_s
    science = rng.poisson(planet + nuisance, trials) + rng.normal(0, read_noise_e * np.sqrt(reads), trials)
    background = rng.poisson(nuisance, trials) + rng.normal(0, read_noise_e * np.sqrt(reads), trials)
    recovered = science - background
    analytic_variance = planet + 2.0 * nuisance + 2.0 * reads * read_noise_e**2
    empirical_sigma = float(np.std(recovered, ddof=1))
    mean = float(np.mean(recovered))
    return RecoverySummary(
        trials=trials,
        exposure_s=exposure_s,
        injected_planet_electrons=planet,
        mean_recovered_electrons=mean,
        recovery_bias_fraction=(mean - planet) / planet,
        empirical_sigma_electrons=empirical_sigma,
        analytic_sigma_electrons=float(np.sqrt(analytic_variance)),
        empirical_snr=planet / empirical_sigma,
        analytic_snr=planet / float(np.sqrt(analytic_variance)),
    )


def recovery_dict(**kwargs: float) -> dict[str, float]:
    """JSON-friendly wrapper for :func:`synthetic_count_recovery`."""
    return asdict(synthetic_count_recovery(**kwargs))
