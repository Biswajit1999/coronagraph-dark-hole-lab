import unittest

import numpy as np

from research.field_control_diagnostics import (
    efc_solve, pairwise_probe_estimate, synthetic_efc_sensitivity,
    synthetic_probe_recovery,
)


class FieldControlTests(unittest.TestCase):
    def test_real_stroke_reduces_intensity(self):
        e = np.array([1 + 2j, -0.5 + 1j])
        g = np.array([[1, 1j, 0, 0], [0, 0, 1, 1j]])
        fit = efc_solve(e, g)
        self.assertLess(fit.residual_intensity, 1e-25)
        self.assertTrue(np.isrealobj(fit.strokes))

    def test_regularization_suppresses_strokes(self):
        e = np.array([1 + 2j])
        g = np.array([[1, 1j]])
        norms = [efc_solve(e, g, a).stroke_norm for a in (0, 0.1, 1, 10)]
        self.assertTrue(all(x > y for x, y in zip(norms, norms[1:])))

    def test_probe_quadratures_recovered_exactly(self):
        e = 2.3 - 0.7j
        p = np.array([1 + 0j, 1j, 1 + 1j])
        diff = abs(e + p)**2 - abs(e - p)**2
        fit, cov = pairwise_probe_estimate(p, diff, np.ones(3))
        self.assertAlmostEqual(fit.real, e.real, places=12)
        self.assertAlmostEqual(fit.imag, e.imag, places=12)
        self.assertTrue(np.all(np.linalg.eigvalsh(cov) > 0))

    def test_degenerate_probes_fail(self):
        with self.assertRaises(ValueError):
            pairwise_probe_estimate(np.array([1+0j, 2+0j]), np.ones(2), np.ones(2))

    def test_weight_validation(self):
        with self.assertRaises(ValueError):
            efc_solve(np.ones(2), np.ones((2, 3)), pixel_weights=np.array([1, -1]))

    def test_seeded_probe_recovery_matches_analytic_covariance(self):
        r = synthetic_probe_recovery(trials=12000)
        self.assertLess(abs(r["mean_real"] - r["true_real"]), 0.09)
        self.assertLess(abs(r["mean_imag"] - r["true_imag"]), 0.09)
        for axis in ("real", "imag"):
            self.assertLess(abs(r[f"empirical_sigma_{axis}"] / r[f"predicted_sigma_{axis}"] - 1), 0.04)

    def test_mismatch_zero_matches_predicted(self):
        r = synthetic_efc_sensitivity()
        first = r["jacobian_mismatch"][0]
        self.assertAlmostEqual(first["predicted_intensity"], first["true_model_intensity"], places=12)
        self.assertGreater(r["jacobian_mismatch"][-1]["true_model_intensity"], first["true_model_intensity"])


if __name__ == "__main__":
    unittest.main()
