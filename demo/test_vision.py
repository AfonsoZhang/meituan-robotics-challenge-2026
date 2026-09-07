"""Fail-closed perception and local IK regression, independent of Gazebo."""
import unittest
import numpy as np
from vision import correction, NOMINAL_YELLOW

class VisionGates(unittest.TestCase):
    def candidate(self):
        return dict(color='yellow',center_xy=NOMINAL_YELLOW+np.array([.006,0]),
                    size_ok=True,depth_valid=.99,n_body=1000,body_top_z=.05,
                    handle_top_z=.08,yaw_deg=90,long_mm=80,short_mm=70)

    def test_known_translation(self):
        np.testing.assert_allclose(correction([self.candidate()]),[.006,0])

    def test_reject_ambiguous_or_missing(self):
        for ds in ([],[self.candidate(),self.candidate()]):
            with self.assertRaises(ValueError): correction(ds)

    def test_reject_unobservable_or_outside_envelope(self):
        for key,value in [('body_top_z',float('nan')),('depth_valid',.5),('handle_top_z',0),('yaw_deg',100),
                          ('center_xy',NOMINAL_YELLOW+[.02,0]),('center_xy',[float('nan'),0])]:
            d=self.candidate();d[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): correction([d])

class LocalIK(unittest.TestCase):
    def test_shift_source_keep_destination_and_orientation(self):
        from metrics import Kinematics
        from vision import translated_plan, flange
        # Synthetic six-axis chain: exercise FK/IK without installed ROS assets.
        kin = Kinematics.__new__(Kinematics)
        kin.chain = [(np.array(p),np.eye(3),np.array(a,dtype=float)) for p,a in [
            ([0,0,.2],[0,0,1]),([.1,0,0],[0,1,0]),([.2,0,0],[0,1,0]),
            ([.15,0,0],[1,0,0]),([.1,0,0],[0,1,0]),([.05,0,0],[0,0,1])]]
        kin.limits = [(-6.28,6.28)]*6
        q = [.3,.4,-.8,.2,.5,.1]
        plan = [dict(q=q.copy(),tcp=kin.tcp(q).tolist(),col=0) for _ in range(118)]
        corrected,error = translated_plan(kin,plan,np.array([.006,0]))
        np.testing.assert_allclose(kin.tcp(corrected[35]['q'])-kin.tcp(q),[.006,0,0],atol=1e-5)
        np.testing.assert_allclose(flange(kin,corrected[35]['q'])[1],flange(kin,q)[1],atol=1e-5)
        self.assertEqual(corrected[80]['q'],q)
        self.assertEqual(plan[35]['q'],q)
        self.assertLess(error,1e-5)

if __name__ == '__main__': unittest.main()
