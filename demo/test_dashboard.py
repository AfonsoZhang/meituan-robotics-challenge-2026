import unittest

import numpy as np

from dashboard import PRESETS, same_origin, terminal_spec, to_bgr


class ToBgrTest(unittest.TestCase):
    def test_rgb8_swaps_channels_and_drops_row_padding(self):
        rgb = np.zeros((2, 3, 3), np.uint8); rgb[..., 0] = 200   # 纯红
        padded = np.zeros((2, 3*3+4), np.uint8); padded[:, :9] = rgb.reshape(2, 9)
        out = to_bgr('rgb8', 2, 3, 13, padded.tobytes())
        self.assertEqual(out.shape, (2, 3, 3))
        self.assertTrue((out[..., 2] == 200).all() and (out[..., 0] == 0).all())

    def test_depth_invalid_pixels_are_black_and_near_is_brighter_index(self):
        d = np.array([[0.2, 1.5, np.nan, 0.0]], np.float32)
        out = to_bgr('32FC1', 1, 4, 16, d.tobytes())
        self.assertTrue((out[0, 2] == 0).all() and (out[0, 3] == 0).all())
        self.assertFalse((out[0, 0] == out[0, 1]).all())

    def test_16uc1_millimetres_match_32fc1_metres(self):
        mm = np.array([[500, 1000]], np.uint16)
        m = mm.astype(np.float32)/1000
        np.testing.assert_array_equal(to_bgr('16UC1', 1, 2, 4, mm.tobytes()), to_bgr('32FC1', 1, 2, 8, m.tobytes()))

    def test_unknown_encoding_rejected(self):
        with self.assertRaises(ValueError):
            to_bgr('yuv422', 1, 1, 2, b'\0\0')


class TerminalSpecTest(unittest.TestCase):
    def idx(self, kind):
        return next(i for i, p in enumerate(PRESETS) if p['kind'] == kind)

    def test_readonly_runs_monitor_command_without_shell_or_input(self):
        argv, typed, accept = terminal_spec(self.idx('monitor'), readonly=True)
        self.assertEqual(argv[:2], ['bash', '-c'])
        self.assertEqual((typed, accept), (b'', False))

    def test_readonly_refuses_shell_and_launch_presets(self):
        for kind in ('shell', 'type'):
            with self.assertRaises(PermissionError):
                terminal_spec(self.idx(kind), readonly=True)

    def test_launch_preset_is_typed_without_enter(self):
        argv, typed, accept = terminal_spec(self.idx('type'), readonly=False)
        self.assertEqual(argv, ['bash', '-i'])
        self.assertFalse(typed.endswith(b'\n'))
        self.assertTrue(accept)


class SameOriginTest(unittest.TestCase):
    class Req:
        def __init__(self, origin, host='127.0.0.1:8765'):
            self.headers = {} if origin is None else {'Origin': origin}
            self.host = host

    def test_cross_site_page_refused(self):
        self.assertFalse(same_origin(self.Req('https://evil.example')))
        self.assertFalse(same_origin(self.Req('http://127.0.0.1:9999')))

    def test_same_page_and_non_browser_allowed(self):
        self.assertTrue(same_origin(self.Req('http://127.0.0.1:8765')))
        self.assertTrue(same_origin(self.Req(None)))


if __name__ == '__main__':
    unittest.main()
