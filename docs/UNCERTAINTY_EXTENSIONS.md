# Reduced-order uncertainty diagnostics (synthetic)

All numbers here are **illustrative model outputs**, not Roman CGI measurements or flight predictions. This module does not implement diffraction, a DM Jacobian, wavelength-dependent coronagraph transmission, or speckle correlations.

1. **Exact broadband integration:** For the pre-existing surrogate `C(lambda)=0.01(2π sigma_WFE/lambda)^2` and a uniform top-hat of full fractional width `f`, the exact mean is `C(lambda0)/(1-f²/4)` for `0<=f<2`. The numerical trapezoid implementation is independently checked against this expression rather than another numerical grid.
2. **Correlated uncertainty:** For `C=C0+k*(j/L)^2` with `L=lambda/D` in mas, propagate the covariance of `(C0,k,j)` using the Jacobian `(1,(j/L)^2,2kj/L²)`, then compare to seeded Gaussian Monte Carlo. The reported fraction of negative-parameter draws flags unphysical samples; a small-uncertainty Gaussian model is assumed and must not be used for broad bounded priors. The coupling `k` is not an empirical Roman calibration.
3. **Science/background allocation:** For independent frames of durations `ts,tb`, background-subtracted planet counts are `S-(ts/tb)B` with variance `(P+N)ts + N ts²/tb + r²[ns+(ts/tb)² nb]`. Sweep fixed `ts+tb` to quantify the gain over equal time; in the photon-only limit the optimum science fraction is `sqrt(P+N)/(sqrt(P+N)+sqrt(N))`. Real temporal drift, overheads and calibration systematics are excluded.

Run from the repository root with `python scripts/analyze_uncertainty_extensions.py` and `python -m unittest discover -s tests -v`. Results are seeded synthetic JSON and CSV in `results/uncertainty_extensions/`. No existing data products are replaced.
