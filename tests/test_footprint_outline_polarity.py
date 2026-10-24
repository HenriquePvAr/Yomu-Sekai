"""Regression: the lettering footprint must not absorb bright artwork next to dark text.

Page 03 (V8): a light column behind a dark caption satisfied the footprint's
opposite-polarity rule and added ~2.8k bright artwork pixels to the cleanup mask.
A genuine white outline that hugs the glyph must still be included.
"""

from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest

import cv2
import numpy as np

import yomu.ocr.ocr_balloon as ob


def _dark_core(shape, box):
    core = np.zeros(shape, bool)
    x0, y0, x1, y1 = box
    core[y0:y1, x0:x1] = True
    return core


class OutlinePolarityEvidenceTest(unittest.TestCase):
    def test_white_outline_hugging_dark_glyph_is_kept(self):
        h, w = 80, 160
        gray = np.full((h, w), 128, np.uint8)
        core = _dark_core((h, w), (40, 30, 120, 50))
        ring = (cv2.dilate(core.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & ~core
        gray[ring] = 250
        gray[core] = 10
        dark = gray < 60
        light = gray > 200
        _dark, kept = ob._outline_polarity_evidence(gray, core.astype(np.uint8) * 255, dark, light, 20, False)
        self.assertEqual(int((kept & ring).sum()), int(ring.sum()))

    def test_bright_art_extending_away_from_glyph_is_rejected(self):
        h, w = 80, 160
        gray = np.full((h, w), 128, np.uint8)
        core = _dark_core((h, w), (40, 30, 120, 50))
        gray[:, 20:40] = 252  # light column touching the glyph and running off the region
        gray[core] = 10
        dark = gray < 60
        light = gray > 200
        _dark, kept = ob._outline_polarity_evidence(gray, core.astype(np.uint8) * 255, dark, light, 20, False)
        self.assertEqual(int(kept[:, 20:40].sum()), 0)

    def test_light_text_keeps_dark_outline_and_rejects_dark_art(self):
        h, w = 80, 160
        gray = np.full((h, w), 128, np.uint8)
        core = _dark_core((h, w), (40, 30, 120, 50))
        ring = (cv2.dilate(core.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & ~core
        gray[ring] = 8
        gray[:, 130:150] = 5  # dark art far from the glyph
        gray[core] = 245
        dark = gray < 60
        light = gray > 200
        kept_dark, _light = ob._outline_polarity_evidence(gray, core.astype(np.uint8) * 255, dark, light, 20, False)
        self.assertEqual(int((kept_dark & ring).sum()), int(ring.sum()))
        self.assertEqual(int(kept_dark[:, 130:150].sum()), 0)

    def test_empty_seed_is_a_no_op(self):
        gray = np.full((20, 20), 128, np.uint8)
        dark = np.zeros((20, 20), bool); light = np.ones((20, 20), bool)
        d, l = ob._outline_polarity_evidence(gray, np.zeros((20, 20), np.uint8), dark, light, 10, False)
        self.assertIs(d, dark); self.assertIs(l, light)


if __name__ == "__main__":
    unittest.main()
