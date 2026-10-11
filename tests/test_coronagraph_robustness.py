import unittest

import numpy as np

from research.coronagraph_robustness import (
    broadband_leakage,
    jitter_leakage,
    quadrature_convergence,
    synthetic_count_recovery,
)


class CoronagraphRobustnessTests(unittest.TestCase):
    def test_broadband_quadrature_converges(self):
        rows = quadrature_convergence(sample_counts=(5, 9, 17, 33, 65, 129))
        errors = [row["relative_error"] for row in rows]
        self.assertTrue(all(b < a for a, b in zip(errors, errors[1:])))
        self.assertLess(errors[-1], 2e-6)

    def test_zero_band_matches_monochromatic_limit(self):
        mono = broadband_leakage(24, 575, 0, 2)
        narrow = broadband_leakage(24, 575, 1e-5, 101)
        self.assertAlmostEqual(mono, narrow, delta=mono * 1e-9)

    def test_jitter_is_monotonic_and_symmetric_in_signless_rms(self):
        result = jitter_leakage(1e-9, np.array([0.0, 0.5, 1.0, 2.0]))
        self.assertTrue(np.all(np.diff(result) > 0))
        self.assertEqual(result[0], 1e-9)

    def test_synthetic_recovery_matches_propagated_uncertainty(self):
        result = synthetic_count_recovery(trials=80_000)
        self.assertLess(abs(result.recovery_bias_fraction), 0.01)
        ratio = result.empirical_sigma_electrons / result.analytic_sigma_electrons
        self.assertLess(abs(ratio - 1.0), 0.015)


if __name__ == "__main__":
    unittest.main()
