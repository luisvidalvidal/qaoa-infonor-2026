import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from qaoa_infonor.verify import verify
from qaoa_infonor.experiment import instance, statevector_probs, apply_readout
from qaoa_infonor.circuit import ising_coefficients, direct_statevector, decomposed_statevector

class ReproducibilityTests(unittest.TestCase):
    def test_all_supplied_records(self):
        self.assertEqual(verify()['optimizations_replayed'],690)

    def test_nondefault_parameters_and_gates(self):
        for n in (4,6,8):
            inst=instance(n,alpha=1.0,penalty=4.5)
            c,h,J=ising_coefficients(inst); z=1-2*inst['states']
            np.testing.assert_allclose(c+z@h+np.einsum('bi,ij,bj->b',z,J,z),inst['C'],atol=1e-12,rtol=0)
            for p in (1,2,3):
                theta=np.random.default_rng(n+p).uniform(.1,1,2*p)
                np.testing.assert_allclose(direct_statevector(inst,theta,p),decomposed_statevector(inst,theta,p),atol=1e-12,rtol=0)

    def test_uniform_and_readout_limits(self):
        inst=instance(4)
        probs=statevector_probs(inst,[0.,0.],1)
        np.testing.assert_allclose(probs,np.full(16,1/16),atol=1e-14)
        delta=np.zeros(16); delta[3]=1
        np.testing.assert_allclose(apply_readout(delta,4,0),delta)
        np.testing.assert_allclose(apply_readout(delta,4,.5),np.full(16,1/16))
        self.assertAlmostEqual(apply_readout(delta,4,.03).sum(),1)

if __name__=='__main__': unittest.main()
