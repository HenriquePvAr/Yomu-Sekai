"""Regression: mid-tone backgrounds (118 < median < 138) are masked and measured.

Before: a fixed 5x5 black/top-hat only caught the edges of bold lettering (hollow
mask), and the removal verifier skipped mid-tone lines entirely, so every such
group was forced to review as "unmeasured" even after a correct clean.
"""

from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest

import cv2
import numpy as np

import yomu.ocr.ocr_balloon as ob
from yomu.ocr.ocr_engine import OCRLine


def _midtone_case(stroke=7):
    h, w = 90, 300
    image = np.full((h, w, 3), 128, np.uint8)
    glyph = np.zeros((h, w), np.uint8)
    cv2.putText(glyph, "HOLD", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.9, 255, stroke, cv2.LINE_8)
    text = glyph > 0
    image[text] = 30
    polygon = np.array([[12, 14], [288, 14], [288, 80], [12, 80]], np.int32)
    line = OCRLine("HOLD", 0.95, polygon, (12, 14, 276, 66), "HOLD", engine="synthetic",
                   metadata={"ocr_line_id": "m1"})
    group = ob.TextGroup(group_id="mid", lines=[line], text="HOLD", classification="speech")
    return image, text, group


class MidtoneKernelTest(unittest.TestCase):
    def test_kernel_grows_with_line_height(self):
        self.assertEqual(ob._midtone_stroke_kernel(20).shape, (7, 7))
        self.assertEqual(ob._midtone_stroke_kernel(10).shape, (5, 5))
        self.assertEqual(ob._midtone_stroke_kernel(66).shape, (21, 21))
        self.assertEqual(ob._midtone_stroke_kernel(500).shape, (31, 31))


class MidtoneVerificationTest(unittest.TestCase):
    def test_covered_midtone_text_is_verified(self):
        image, text, group = _midtone_case()
        cleaned = image.copy(); cleaned[text] = 128
        mask = (cv2.dilate(text.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0).astype(np.uint8) * 255
        evidence = ob._uncovered_source_text_evidence(image, cleaned, group, mask)
        self.assertTrue(evidence["measured"])
        self.assertEqual(ob._source_removal_status(group, evidence), ob.SOURCE_REMOVAL_VERIFIED)

    def test_uncovered_midtone_text_is_rejected(self):
        image, text, group = _midtone_case()
        half = text.copy(); half[:, 150:] = False
        cleaned = image.copy(); cleaned[half] = 128
        mask = half.astype(np.uint8) * 255
        evidence = ob._uncovered_source_text_evidence(image, cleaned, group, mask)
        self.assertTrue(evidence["measured"])
        self.assertEqual(ob._source_removal_status(group, evidence), ob.SOURCE_REMOVAL_REJECTED)


class MidtoneComponentMaskTest(unittest.TestCase):
    def test_bold_midtone_lettering_mask_is_not_hollow(self):
        image, text, group = _midtone_case(stroke=9)
        maximum = np.full(text.shape, 255, np.uint8)
        mask, _metrics = ob._component_text_mask(image, group, maximum, strategy="primary")
        covered = np.count_nonzero((mask > 0) & text) / max(1, np.count_nonzero(text))
        self.assertGreaterEqual(covered, 0.95)


if __name__ == "__main__":
    unittest.main()
