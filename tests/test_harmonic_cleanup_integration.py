"""Integration: _apply_cleanup_mask uses an accepted harmonic candidate for smooth backdrops.

With CLEAN_HARMONIC_FILL enabled, a solid_* group whose spatial class is
SMOOTH_NONUNIFORM used to be denied the constant fill and sent to review without the
harmonic solver ever being called. A constant fill over such a backdrop paints letter
silhouettes; the harmonic candidate is now attempted and used when its gates accept.
"""

from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest
from unittest import mock

import cv2
import numpy as np

import yomu.config.settings as config
import yomu.ocr.ocr_balloon as ob
from yomu.ocr.ocr_engine import OCRLine


def _case(gradient):
    h, w = 120, 360
    x = np.arange(w, dtype=np.float32)[None, :]
    lum = np.repeat(225 + gradient * x / (w - 1), h, axis=0)
    image = np.repeat(lum[..., None], 3, axis=2).astype(np.uint8)
    glyph = np.zeros((h, w), np.uint8)
    cv2.putText(glyph, "SAFE TEXT", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.6, 255, 4, cv2.LINE_8)
    image[glyph > 0] = 15
    clean = np.repeat(lum[..., None], 3, axis=2).astype(np.uint8)
    polygon = np.array([[20, 30], [340, 30], [340, 95], [20, 95]], np.int32)
    line = OCRLine("SAFE TEXT", 0.97, polygon, (20, 30, 320, 65), "SAFE TEXT", engine="synthetic",
                   metadata={"ocr_line_id": "h1"})
    group = ob.TextGroup(group_id="h", lines=[line], text="SAFE TEXT", classification="speech")
    group.background_type, group.background_metrics = ob._classify_background_region(image, group)
    mask = (cv2.dilate(glyph, np.ones((3, 3), np.uint8)) > 0).astype(np.uint8) * 255
    return image, clean, group, mask


class HarmonicCleanupIntegrationTest(unittest.TestCase):
    def test_flag_off_keeps_constant_fill(self):
        image, _clean, group, mask = _case(gradient=25.0)
        with mock.patch.object(config, "CLEAN_HARMONIC_FILL", False):
            out = ob._apply_cleanup_mask(image.copy(), image, group, mask, strategy="primary")
        if group.background_metrics.get("local_background_class", "").startswith("solid"):
            self.assertEqual(group.background_metrics.get("cleanup_fill_source"), "local_ring_median")
            self.assertEqual(len(np.unique(out[mask > 0].reshape(-1, 3), axis=0)), 1)

    def test_flag_on_smooth_backdrop_uses_harmonic_and_removes_silhouette(self):
        image, clean, group, mask = _case(gradient=25.0)
        metrics = group.background_metrics
        self.assertEqual(metrics.get("local_background_spatial_class"), "SMOOTH_NONUNIFORM", metrics)
        self.assertTrue(metrics.get("local_background_class", "").startswith("solid"), metrics)
        with mock.patch.object(config, "CLEAN_HARMONIC_FILL", True):
            group.spatial_harmonic_gate_rejected = False
            out = ob._apply_cleanup_mask(image.copy(), image, group, mask, strategy="primary")
        self.assertEqual(group.background_metrics.get("cleanup_fill_source"), "harmonic_boundary_fill",
                         group.background_metrics.get("harmonic_fill"))
        self.assertFalse(group.spatial_harmonic_gate_rejected)
        inside = mask > 0
        harmonic_error = float(np.abs(out[inside].astype(int) - clean[inside].astype(int)).mean())
        constant = image.copy(); constant[inside] = np.median(image[(cv2.dilate(mask, np.ones((7, 7), np.uint8)) > 0) & ~inside], axis=0)
        constant_error = float(np.abs(constant[inside].astype(int) - clean[inside].astype(int)).mean())
        self.assertLess(harmonic_error, constant_error)
        self.assertLess(harmonic_error, 2.0)
        self.assertTrue(np.array_equal(out[~inside], image[~inside]))

    def test_flag_on_uniform_backdrop_keeps_exact_constant_fill(self):
        image, _clean, group, mask = _case(gradient=0.0)
        self.assertEqual(group.background_metrics.get("local_background_spatial_class"), "PROVEN_UNIFORM")
        with mock.patch.object(config, "CLEAN_HARMONIC_FILL", True):
            out = ob._apply_cleanup_mask(image.copy(), image, group, mask, strategy="primary")
        self.assertEqual(group.background_metrics.get("cleanup_fill_source"), "local_ring_median")
        self.assertEqual(out[mask > 0].reshape(-1, 3).tolist()[0], [225, 225, 225])


if __name__ == "__main__":
    unittest.main()
