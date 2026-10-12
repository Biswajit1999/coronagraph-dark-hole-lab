# Broadband, jitter, and count-noise robustness

This extension contains three reduced-order analyses. All inputs are synthetic or
illustrative; none are Roman observations or measurements of flight performance.

## 1. Broadband quadrature convergence

For RMS wavefront error `sigma` and wavelength `lambda`, the existing leakage
surrogate is evaluated as

`C_phase(lambda) = 0.01 [2 pi sigma / lambda]^2`.

A uniform top-hat band is integrated with trapezoidal quadrature. Grids from 5 to
129 wavelengths are compared with a 65,537-point numerical reference. This tests
the numerical integration only; it does not represent chromatic masks, deformable
mirror response, polarization, or a complex electric field.

## 2. Pointing-jitter sensitivity

The explicit sensitivity model is

`C_jitter = C_base + k [sigma_theta / (lambda/D)]^2`,

where `sigma_theta` is RMS line-of-sight jitter in mas, `D = 2.4 m`, and the
default wavelength is 575 nm. The sweep varies both jitter and the unknown
coupling `k`; these coupling values are deliberately not fitted to Roman data.

## 3. Synthetic detector-count recovery

Equal-duration science and background frames are simulated. If the injected
planet expectation is `P`, nuisance expectation per frame is `N`, read noise is
`r`, and each stack has `m` reads, subtraction gives

`E[S - B] = P`, and `Var[S - B] = P + 2N + 2 m r^2`.

The Monte Carlo test uses a fixed seed and compares recovered bias and empirical
scatter with this analytic result. It validates uncertainty propagation, not an
instrument noise budget.

## Reproduce

```bash
python scripts/run_robustness.py
python -m unittest discover -s tests -v
```

Generated JSON, CSV, and SVG evidence is written to `results/`. The SVG labels
the data as a synthetic model prediction and includes units in both axes.
