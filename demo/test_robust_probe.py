import tempfile
import unittest
from pathlib import Path
import numpy as np
from robust_probe import reference
from gravity_check import gravity_from_potential

class ProbeTests(unittest.TestCase):
    def test_smooth_reference_returns_to_start(self):
        class K:
            def startup_clear(self,q,b):return True
            def tcp(self,q):return np.array(q[:3])
        p=reference(np.zeros(6),K())
        for i in [0,19,139,-1]:
            np.testing.assert_allclose(p[i]['q'],0,atol=1e-12)
            np.testing.assert_allclose(p[i]['dq'],0,atol=1e-12)
            np.testing.assert_allclose(p[i]['ddq'],0,atol=1e-12)
        i=79
        finite=(-np.array(p[i+2]['q'])+8*np.array(p[i+1]['q'])-8*np.array(p[i-1]['q'])+p[i-2]['q'])/1.2
        np.testing.assert_allclose(finite,p[i]['dq'],atol=1e-7)

    def test_gravity_includes_fixed_payload_branch(self):
        xml='''<robot name="test"><link name="base_link"/>
        <link name="arm"><inertial><mass value="2"/><origin xyz="0.1 0 0"/></inertial></link>
        <joint name="shoulder_joint" type="revolute"><parent link="base_link"/><child link="arm"/><axis xyz="0 1 0"/></joint>
        <link name="payload"><inertial><mass value="3"/><origin xyz="0.2 0 0"/></inertial></link>
        <joint name="payload_mount" type="fixed"><parent link="arm"/><child link="payload"/><origin xyz="0.3 0 0"/></joint></robot>'''
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'robot.urdf';p.write_text(xml)
            q=np.zeros(6);q[0]=.4
            g=gravity_from_potential(p,q)
            self.assertAlmostEqual(g[0],-(2*.1+3*.5)*9.81*np.cos(.4),places=7)
            np.testing.assert_allclose(g[1:],0,atol=1e-8)

if __name__=='__main__':unittest.main()
