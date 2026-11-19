# Synthetic injection and correlated-noise diagnostics (18 November 2026)

Three calculations: (1) Cholesky-whitened fixed-template matched-filter amplitude and formal uncertainty, (2) companion injection **before** a supplied deterministic subtraction operator with baseline-corrected throughput, and (3) positive-definite equicorrelated noise covariance for sensitivity tests.

From the repository root, run `python -m unittest -v research.test_injection_diagnostics` (NumPy required).

This is a synthetic linear-algebra testbed, not a Roman CGI OS11 measured throughput, flight-performance forecast or on-sky result. The noise model does not represent spatially nonstationary speckles. Injection recovery must be repeated using a physically meaningful optical processing pipeline; the identity/scaling operator tests only numerical behaviour. AI-assisted implementation; Biswajit Jana is the requested sole Git author.
