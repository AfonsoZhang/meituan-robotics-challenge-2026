import math
import tempfile
import unittest
from pathlib import Path

from checks import (JOINTS, classify_image_topics, dashboard_presets, jog_target,
                    joint_state_problems, realsense_usb)


class UsbTest(unittest.TestCase):
    def test_finds_d435i_and_speed(self):
        with tempfile.TemporaryDirectory() as root:
            for name, vendor, product, speed in [('2-1', '8086', '0b3a', '5000'), ('1-4', '046d', 'c52b', '12')]:
                d = Path(root)/name; d.mkdir()
                (d/'idVendor').write_text(vendor+'\n'); (d/'idProduct').write_text(product+'\n'); (d/'speed').write_text(speed+'\n')
            found = realsense_usb(root)
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0]['is_d435i'])
        self.assertEqual(found[0]['speed_mbps'], 5000.0)


class JointStateTest(unittest.TestCase):
    def test_exact_names_pass(self):
        self.assertEqual(joint_state_problems(JOINTS, [0.0]*6), [])

    def test_missing_extra_and_nan(self):
        p = joint_state_problems(JOINTS[:5]+['finger'], [0, 0, 0, 0, 0, float('nan')])
        self.assertEqual(len(p), 3)


class JogTest(unittest.TestCase):
    cur = {j: 0.1*i for i, j in enumerate(JOINTS)}

    def test_only_selected_joint_moves(self):
        t = jog_target(self.cur, 'wrist3_joint', -3, 6)
        self.assertAlmostEqual(t[5], 0.5 - math.radians(3))
        self.assertEqual(t[:5], [self.cur[j] for j in JOINTS[:5]])

    def test_limits_rejected(self):
        for args in [('wrist3_joint', 6, 6), ('wrist3_joint', 0, 6), ('wrist3_joint', 3, 4), ('elbow', 3, 6)]:
            with self.assertRaises(ValueError):
                jog_target(self.cur, *args)
        with self.assertRaises(ValueError):
            jog_target({'shoulder_joint': 0}, 'shoulder_joint', 1, 6)


class TopicTest(unittest.TestCase):
    def test_classify(self):
        stats = {'/camera/camera/color/image_raw': {'encoding': 'rgb8'},
                 '/camera/camera/depth/image_rect_raw': {'encoding': '16UC1'},
                 '/camera/camera/aligned_depth_to_color/image_raw': {'encoding': '16UC1'},
                 '/camera/camera/infra1/image_rect_raw': {'encoding': 'mono8'},
                 '/d435i/depth/image_raw': {'encoding': 'rgb8'}}
        color, depth, aligned = classify_image_topics(stats)
        self.assertEqual(color, ['/camera/camera/color/image_raw'])
        self.assertEqual(len(depth), 2)
        self.assertEqual(aligned, ['/camera/camera/aligned_depth_to_color/image_raw'])

    def test_presets_use_measured_topics(self):
        p = dashboard_presets('/c', '/d')
        self.assertIn('ros2 topic hz /c', [x['cmd'] for x in p])
        self.assertTrue(all(x['kind'] in ('monitor', 'shell') for x in p))


if __name__ == '__main__':
    unittest.main()
