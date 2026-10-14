"""Analytic audits of the *illustrative* coronagraph contrast and count models.

This is not a Roman CGI instrument-performance estimator. The coefficients and
noise assumptions deliberately match the reduced-order research surrogate.
WFE: pm RMS; wavelength: nm; pointing jitter: mas RMS; rates: electrons/s.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

PHASE_FACTOR = 0.01
RAD_TO_MAS = 206_264_806.247


def _finite_nonnegative(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return value


def exact_top_hat_leakage(wfe_pm: float, centre_nm: float, bandwidth_fraction: float) -> float:
    """Exact uniform-wavelength average of 0.01 (2*pi*sigma/lambda)^2.

    The average of lambda**-2 on [lo,hi] is 1/(lo*hi), including the
    monochromatic limit. This benchmarks numerical quadrature independently.
    It does *not* include a wavelength-dependent coronagraph optical response.
    """
    wfe = _finite_nonnegative("wfe_pm", wfe_pm) * 1e-3
    centre = float(centre_nm)
    width = float(bandwidth_fraction)
    if not math.isfinite(centre) or centre <= 0 or not math.isfinite(width) or not 0 <= width < 2:
        raise ValueError("centre_nm must be positive and 0 <= bandwidth_fraction < 2")
    lo, hi = centre * (1 - width / 2), centre * (1 + width / 2)
    return PHASE_FACTOR * (2 * math.pi * wfe)**2 / (lo * hi)


def trapezoid_bias(wfe_pm: float, centre_nm: float, bandwidth_fraction: float,
                   samples: int) -> dict[str, float]:
    """Signed and absolute quadrature error relative to the exact model."""
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 2:
        raise ValueError("samples must be an integer >= 2")
    exact = exact_top_hat_leakage(wfe_pm, centre_nm, bandwidth_fraction)
    if bandwidth_fraction == 0:
        numeric = exact
    else:
        import numpy as np
        lo = centre_nm * (1 - bandwidth_fraction / 2)
        hi = centre_nm * (1 + bandwidth_fraction / 2)
        wavelength = np.linspace(lo, hi, samples)
        signal = PHASE_FACTOR * (2 * np.pi * wfe_pm * 1e-3 / wavelength)**2
        numeric = float(np.trapezoid(signal, wavelength) / (hi - lo))
    return {"samples": samples, "exact_contrast": exact, "numeric_contrast": numeric,
            "signed_bias": numeric - exact,
            "relative_error": abs(numeric - exact) / exact if exact > 0 else 0.0}


def jitter_budget(base_contrast: float, maximum_contrast: float, coupling: float,
                  wavelength_nm: float = 575.0, diameter_m: float = 2.4) -> dict[str, float | bool]:
    """Invert C=C0+k*(jitter/(lambda/D))**2 for the admissible RMS jitter.

    A budget below the no-jitter floor is infeasible. A zero coupling leaves
    jitter unconstrained *by this model*; infinity is not an instrument limit.
    """
    base = _finite_nonnegative("base_contrast", base_contrast)
    maximum = _finite_nonnegative("maximum_contrast", maximum_contrast)
    k = _finite_nonnegative("coupling", coupling)
    wavelength = float(wavelength_nm)
    diameter = float(diameter_m)
    if not math.isfinite(wavelength) or not math.isfinite(diameter) or wavelength <= 0 or diameter <= 0:
        raise ValueError("wavelength and diameter must be positive finite values")
    scale = wavelength * 1e-9 / diameter * RAD_TO_MAS
    feasible = maximum >= base
    jitter = (scale * math.sqrt((maximum - base) / k) if feasible and k > 0
              else math.inf if feasible else math.nan)
    return {"feasible": feasible, "lambda_over_d_mas": scale,
            "max_jitter_mas_rms": jitter, "contrast_margin": maximum - base}


@dataclass(frozen=True)
class ExposureBudget:
    exposure_s: float
    expected_planet_electrons: float
    variance_electrons_squared: float
    expected_snr: float
    photon_variance_fraction: float


def exposure_budget(exposure_s: float, planet_rate_eps: float, nuisance_rate_eps: float,
                    read_noise_e: float, reads_per_frame: int) -> ExposureBudget:
    """Equal-duration independent science/background subtraction noise budget.

    SNR=P*t / sqrt((P+2*N)*t + 2*m*r**2). A constant number of reads is
    assumed, independent of exposure duration. No correlated speckle noise.
    """
    t = _finite_nonnegative("exposure_s", exposure_s)
    p = _finite_nonnegative("planet_rate_eps", planet_rate_eps)
    n = _finite_nonnegative("nuisance_rate_eps", nuisance_rate_eps)
    r = _finite_nonnegative("read_noise_e", read_noise_e)
    if isinstance(reads_per_frame, bool) or not isinstance(reads_per_frame, int) or reads_per_frame < 1:
        raise ValueError("reads_per_frame must be an integer >= 1")
    photon = (p + 2*n) * t
    variance = photon + 2*reads_per_frame*r*r
    snr = p*t/math.sqrt(variance) if variance else 0.0
    return ExposureBudget(t, p*t, variance, snr, photon/variance if variance else 0.0)


def exposure_for_snr(target_snr: float, planet_rate_eps: float, nuisance_rate_eps: float,
                     read_noise_e: float, reads_per_frame: int) -> float:
    """Positive root of the background-subtracted SNR exposure equation."""
    target = _finite_nonnegative("target_snr", target_snr)
    p = _finite_nonnegative("planet_rate_eps", planet_rate_eps)
    n = _finite_nonnegative("nuisance_rate_eps", nuisance_rate_eps)
    r = _finite_nonnegative("read_noise_e", read_noise_e)
    if isinstance(reads_per_frame, bool) or not isinstance(reads_per_frame, int) or reads_per_frame < 1:
        raise ValueError("reads_per_frame must be an integer >= 1")
    if target == 0:
        return 0.0
    if p == 0:
        raise ValueError("positive SNR is impossible without planet photons")
    a = p + 2*n
    b = 2*reads_per_frame*r*r
    # Stable positive root; avoids unnecessary cancellation.
    return (target**2*a + math.hypot(target**2*a, 2*p*target*math.sqrt(b))) / (2*p*p)
