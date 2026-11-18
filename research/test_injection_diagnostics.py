import unittest
import numpy as np
from injection_diagnostics import matched_amplitude, injection_recovery, equicorrelated_covariance

class Tests(unittest.TestCase):
    def test_exact(self):
        a,e = matched_amplitude([2,4],[1,2],np.eye(2))
        self.assertAlmostEqual(a,2)
        self.assertAlmostEqual(e,1/np.sqrt(5))
    def test_throughput(self):
        result = injection_recovery(np.ones(3),np.array([1.,0.,0.]),[1,3],lambda a: .6*a,np.eye(3))
        self.assertTrue(all(abs(x[2]-.6)<1e-12 for x in result))
    def test_correlated(self):
        c = equicorrelated_covariance(2,.5,3)
        self.assertAlmostEqual(c[0,1],2.)
        self.assertTrue(np.min(np.linalg.eigvalsh(c))>0)
    def test_bad(self):
        with self.assertRaises(ValueError): equicorrelated_covariance(1,-.6,3)
if __name__=='__main__': unittest.main()
