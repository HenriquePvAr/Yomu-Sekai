"""Regression for two reconstruction defects that created visible patches.

1. ``_estimated_white_region_fill_color`` forced (245,245,245) whenever the measured
   surround was not white, painting a white patch into grey/tinted regions.
2. ``_restore_lost_local_texture`` injected random grain whenever the ring *mean*
   Laplacian was non-zero, so a smooth ring with a few edges received invented noise.
"""

from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest

import cv2
import numpy as np

import yomu.ocr.ocr_balloon as ob


class WhiteRegionFillColorTest(unittest.TestCase):
    def test_grey_surround_is_not_painted_white(self):
        img = np.full((60, 120, 3), 120, np.uint8)
        mask = np.zeros((60, 120), np.uint8); mask[20:40, 30:90] = 255
        color = ob._estimated_white_region_fill_color(img, mask, (0, 0, 120, 60))
        self.assertEqual(color.tolist(), [120, 120, 120])

    def test_white_surround_still_uses_bright_samples(self):
        img = np.full((60, 120, 3), 238, np.uint8)
        img[20:40, 30:90] = 20
        mask = np.zeros((60, 120), np.uint8); mask[20:40, 30:90] = 255
        color = ob._estimated_white_region_fill_color(img, mask, (0, 0, 120, 60))
        self.assertEqual(color.tolist(), [238, 238, 238])


class TextureRestoreGrainGateTest(unittest.TestCase):
    def _hole(self, shape):
        mask = np.zeros(shape, np.uint8); mask[30:70, 40:120] = 255
        return mask

    def test_smooth_ring_with_an_edge_gets_no_invented_grain(self):
        img = np.full((100, 160, 3), 230, np.uint8)
        img[:, 80:] = 200  # one strong edge crossing the region, otherwise smooth
        mask = self._hole(img.shape[:2])
        flat = img.copy(); flat[mask > 0] = 215
        out = ob._restore_lost_local_texture(flat, img, mask)
        np.testing.assert_array_equal(out, flat)

    def test_grainy_ring_still_receives_texture(self):
        rng = np.random.default_rng(3)
        img = np.clip(140 + rng.normal(0, 12, (100, 160, 1)), 0, 255).astype(np.uint8)
        img = np.repeat(img, 3, axis=2)
        mask = self._hole(img.shape[:2])
        flat = img.copy(); flat[mask > 0] = 140
        out = ob._restore_lost_local_texture(flat, img, mask)
        self.assertGreater(float(cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)[35:65, 45:115].std()), 2.0)


if __name__ == "__main__":
    unittest.main()
