import unittest
import numpy as np
from research.injection_diagnostics import matched_amplitude, injection_recovery, equicorrelated_covariance

class Tests(unittest.TestCase):
    def test_exact(self):
        a,e = matched_amplitude([2,4],[1,2],np.eye(2))
        self.assertAlmostEqual(a,2)
        self.assertAlmostEqual(e,1/np.sqrt(5))
    def test_throughput(self):
        result = injection_recovery(np.ones(3),np.array([1.,0.,0.]),[1,3],lambda a: .6*a,np.eye(3))
        self.assertTrue(all(abs(x[2]-.6)<1e-12 for x in result))
    def test_mutating_subtractor_preserves_injection_baseline(self):
        background = np.array([10., 5., 2.])

        def in_place_subtract(image):
            image *= 0.6
            return image

        result = injection_recovery(background, [1., 0., 0.], [1, 3], in_place_subtract, np.eye(3))
        np.testing.assert_allclose([row[2] for row in result], [0.6, 0.6])
        np.testing.assert_array_equal(background, [10., 5., 2.])

    def test_rejects_asymmetric_covariance(self):
        with self.assertRaisesRegex(ValueError, "covariance must be symmetric"):
            matched_amplitude([2, 4], [1, 2], [[1, 0.8], [0.1, 1]])
    def test_correlated(self):
        c = equicorrelated_covariance(2,.5,3)
        self.assertAlmostEqual(c[0,1],2.)
        self.assertTrue(np.min(np.linalg.eigvalsh(c))>0)
    def test_bad(self):
        with self.assertRaises(ValueError): equicorrelated_covariance(1,-.6,3)
if __name__=='__main__': unittest.main()
