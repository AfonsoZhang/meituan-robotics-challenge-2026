import unittest

import numpy as np

from detector import depth_to_meters


class DepthToMetersTest(unittest.TestCase):
    def test_16uc1_millimetres_equal_32fc1_metres_with_row_padding(self):
        mm = np.array([[280, 1000, 0], [500, 65535, 1234]], np.uint16)
        padded = np.zeros((2, 4), np.uint16); padded[:, :3] = mm   # step 含 1 列填充
        m = mm.astype(np.float32)/1000
        a = depth_to_meters('16UC1', 2, 3, 8, padded.tobytes())
        b = depth_to_meters('32FC1', 2, 3, 12, m.tobytes())
        np.testing.assert_array_equal(np.isnan(a), np.isnan(b))
        np.testing.assert_allclose(a[~np.isnan(a)], b[~np.isnan(b)])
        self.assertTrue(np.isnan(a[0, 2]))

    def test_invalid_32fc1_values_become_nan(self):
        d = np.array([[0.5, np.inf, -1.0, 0.0]], np.float32)
        out = depth_to_meters('32FC1', 1, 4, 16, d.tobytes())
        self.assertEqual(out[0, 0], np.float32(0.5))
        self.assertTrue(np.isnan(out[0, 1:]).all())

    def test_rejects_other_formats(self):
        with self.assertRaises(ValueError):
            depth_to_meters('mono8', 1, 1, 1, b'\0')
        with self.assertRaises(ValueError):
            depth_to_meters('32FC1', 1, 1, 4, b'\0'*4, is_bigendian=True)


if __name__ == '__main__':
    unittest.main()
