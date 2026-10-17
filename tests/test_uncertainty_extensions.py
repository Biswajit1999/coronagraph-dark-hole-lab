import unittest

import numpy as np

from research.uncertainty_extensions import (
    background_subtracted_snr, correlated_jitter_uncertainty,
    exact_top_hat_phase_leakage, exposure_allocation_sweep, top_hat_quadrature_audit,
)


class CoronagraphUncertaintyTests(unittest.TestCase):
    def test_exact_band_zero_width(self):
        mono = .01 * (2*np.pi*24e-3/575)**2
        self.assertAlmostEqual(exact_top_hat_phase_leakage(24,575,0), mono, delta=mono*1e-12)

    def test_exact_band_analytic_scaling(self):
        c = exact_top_hat_phase_leakage(24,575,0)
        self.assertAlmostEqual(exact_top_hat_phase_leakage(24,575,.4)/c, 1/.96)

    def test_quadrature_second_order_convergence(self):
        e = [r['relative_error'] for r in top_hat_quadrature_audit(grids=(9,17,33,65))]
        self.assertTrue(all(b<a for a,b in zip(e,e[1:])))
        self.assertTrue(all(3.5<a/b<4.5 for a,b in zip(e,e[1:])))

    def test_invalid_band(self):
        with self.assertRaises(ValueError): exact_top_hat_phase_leakage(1,575,2)
        with self.assertRaises(ValueError): exact_top_hat_phase_leakage(-1,575,.2)

    def test_zero_covariance_exact(self):
        r=correlated_jitter_uncertainty((1e-9,2e-7,1.),np.zeros((3,3)),trials=300)
        self.assertEqual(r.delta_method_sigma,0.)
        self.assertAlmostEqual(r.monte_carlo_mean,r.nominal_contrast,delta=1e-21)

    def test_correlated_delta_method_against_mc(self):
        std=np.array([1e-10,1e-8,.03])
        corr=np.array([[1,.4,0],[.4,1,-.2],[0,-.2,1]])
        r=correlated_jitter_uncertainty((1e-9,2e-7,1.),np.outer(std,std)*corr,trials=50000)
        self.assertLess(abs(r.delta_method_sigma/r.monte_carlo_sigma-1),.03)
        self.assertEqual(r.invalid_draw_fraction,0)

    def test_reject_non_psd(self):
        with self.assertRaises(ValueError):
            correlated_jitter_uncertainty((1e-9,2e-7,1.),np.array([[1,2,0],[2,1,0],[0,0,1.]]),trials=300)

    def test_snr_no_nuisance_no_read_noise(self):
        snr=background_subtracted_snr(100,100,.1,0,read_noise_e=0)
        self.assertAlmostEqual(snr,np.sqrt(10))

    def test_photon_only_optimum(self):
        r=exposure_allocation_sweep(read_noise_e=0,grid_points=981)
        self.assertAlmostEqual(r['optimal_science_fraction'],r['photon_limit_optimal_fraction'],delta=.002)

    def test_optimized_split_not_worse_than_equal(self):
        r=exposure_allocation_sweep()
        self.assertGreaterEqual(r['optimal_snr'],r['equal_split_snr']-1e-12)

    def test_bad_exposure(self):
        with self.assertRaises(ValueError): background_subtracted_snr(10,0,.1,.3)

if __name__=='__main__': unittest.main()
