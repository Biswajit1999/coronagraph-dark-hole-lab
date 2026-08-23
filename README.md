# Coronagraph Dark Hole Lab

An interactive reduced-order model of electric-field-conjugation (EFC) convergence in a high-contrast coronagraphic dark hole.

[![CI](https://github.com/Biswajit1999/coronagraph-dark-hole-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/Biswajit1999/coronagraph-dark-hole-lab/actions/workflows/ci.yml)
[![MIT License](https://img.shields.io/badge/license-MIT-violet.svg)](LICENSE)

**[Launch the interactive laboratory →](https://biswajit1999.github.io/coronagraph-dark-hole-lab/)**

## Purpose

Direct imaging of faint exoplanets requires suppression of diffracted starlight and quasi-static speckles. A coronagraph removes the ideal on-axis field; a deformable mirror (DM) and focal-plane estimator then work to suppress residual coherent structure over a selected image region. This project exposes the sensitivity of that loop to entering wavefront error, wavelength, DM sampling, gain, and regularisation.

## Research question

Which parameter limits the final contrast in a simplified EFC loop: entering phase leakage, convergence rate, spatial control authority, or the regularisation floor?

## Features

- small-aberration phase-leakage estimate from `2πσ/λ`;
- explicit actuator- and regularisation-dependent contrast floor;
- 40-step EFC energy envelope;
- deterministic coherent-speckle modulation;
- final contrast, suppression factor, half-log convergence time, phase RMS, and nominal DM control radius;
- log-contrast SVG diagnostic and accessible table;
- Motion-based state continuity with `prefers-reduced-motion` support;
- tested monotonic envelope, actuator scaling, and zero-gain limit.

## Reduced-order model

Initial leakage is represented as

```text
C0 = 0.01 (2π σ_WFE / λ)².
```

The illustrative controllability floor is

```text
Cfloor = 10⁻¹⁰ + (σ_WFE/λ)² Nact⁻⁴ (1 + 120 μ),
```

and EFC convergence follows

```text
C(i) = Cfloor + (C0 - Cfloor) exp[-2 g i / (1 + 18 μ)].
```

These equations deliberately separate input leakage, convergence, and floor. Their coefficients are exploratory and must be replaced by an instrument's optical Jacobian and measured estimator/control performance.

## Start

```bash
git clone https://github.com/Biswajit1999/coronagraph-dark-hole-lab.git
cd coronagraph-dark-hole-lab
npm install
npm run dev
```

## Test and build

```bash
npm run check
```

## Repository map

```text
src/science.ts       contrast floor and convergence model
src/science.test.ts  monotonicity and limiting-case tests
src/project.ts       controls, claims, and assumptions
src/Chart.tsx        log-contrast diagnostic
docs/METHODS.md      relation to full focal-plane control
design-system/       persisted visual-system recommendation
```

## How to use the experiment

1. Set gain to zero and identify entering leakage.
2. Restore gain and watch the exponential region.
3. Increase actuator count; note when the 40-iteration state, rather than the floor, is limiting.
4. Increase regularisation and compare numerical conservatism with achieved contrast.
5. Sweep wavelength at fixed physical WFE.

## Scope boundary

This is a hypothesis and sensitivity workbench, not an end-to-end physical-optics simulator. It does not propagate a complex pupil, construct a coronagraph model, calculate an interaction matrix, estimate a field from probe images, solve the regularised inverse problem, or model broadband response.

The displayed `λ/D` radius is the nominal DM Nyquist radius, not a guarantee of corrected area or throughput.

## Research-grade extension path

- use HCIPy, PROPER, or an equivalent diffraction engine;
- construct a complex-valued Jacobian from DM influence functions;
- implement pair-wise probing and noisy detector frames;
- compare EFC, stroke minimisation, and model-free control;
- model amplitude and phase aberrations jointly;
- sweep bandwidth, polarization, jitter, and low-order aberrations;
- validate against a published testbed or laboratory contrast curve;
- publish seeds, calibration products, raw frames, and provenance.

## References

- Give'on, A. et al. (2007), *Broadband wavefront correction algorithm for high-contrast imaging systems*, SPIE 6691, [doi:10.1117/12.733122](https://doi.org/10.1117/12.733122).
- Groff, T. D. et al. (2016), *Methods and limitations of focal plane sensing, estimation, and control in high-contrast imaging*, [JATIS 2, 011009](https://doi.org/10.1117/1.JATIS.2.1.011009).
- Ruane, G. et al. (2018), *Review of high-contrast imaging systems for current and future ground- and space-based telescopes*, [SPIE 10698](https://doi.org/10.1117/12.2312948).

## Citation and license

See [`CITATION.cff`](CITATION.cff). Licensed under [MIT](LICENSE).
