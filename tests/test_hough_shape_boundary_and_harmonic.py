"""Regression: boundary detector and harmonic solver must accept both HoughLinesP shapes.

OpenCV <5 returns ``(N, 1, 4)``; OpenCV 5 returns ``(N, 4)``. Indexing the legacy axis
raised ``IndexError`` on the pinned OpenCV 5 build whenever any line was detected, which
failed the whole page. Shapes are exercised by patching HoughLinesP, so the suite is
version-agnostic; the unpatched cases run against whatever OpenCV is installed.
"""

from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest
from unittest import mock

import cv2
import numpy as np

import yomu.clean.inpainting.harmonic_fill as harmonic_fill
import yomu.clean.ownership.glyph_art_boundary_review as boundary_review
from yomu.clean.ownership.glyph_art_boundary_review import (
    detect_linear_boundary_conflict,
    hough_segments,
)

_REAL_HOUGH = cv2.HoughLinesP


def _crossing_case():
    image = np.full((120, 200, 3), 235, np.uint8)
    cv2.line(image, (0, 60), (199, 60), (20, 20, 20), 2)
    mask = np.zeros((120, 200), np.uint8)
    mask[50:70, 80:120] = 255
    return image, mask


def _hough_as(shape):
    def patched(*args, **kwargs):
        result = _REAL_HOUGH(*args, **kwargs)
        if result is None:
            return None
        flat = np.asarray(result).reshape(-1, 4)
        return flat.reshape(-1, 1, 4) if shape == "legacy" else flat
    return patched


class HoughSegmentsTest(unittest.TestCase):
    def test_legacy_and_flat_shapes_are_identical(self):
        segs = [(1, 2, 3, 4), (5, 6, 7, 8)]
        legacy = np.array([[s] for s in segs], np.int32)
        flat = np.array(segs, np.int32)
        np.testing.assert_array_equal(hough_segments(legacy), hough_segments(flat))
        self.assertEqual(hough_segments(flat).shape, (2, 4))

    def test_none_and_invalid_mean_no_lines(self):
        self.assertEqual(hough_segments(None).shape, (0, 4))
        self.assertEqual(hough_segments(np.zeros((3, 3), np.int32)).shape, (0, 4))
        self.assertEqual(hough_segments(np.zeros(4, np.int32)).shape, (0, 4))


class BoundaryDetectorHoughShapeTest(unittest.TestCase):
    def test_crossing_line_is_reviewed_on_installed_opencv(self):
        image, mask = _crossing_case()
        result = detect_linear_boundary_conflict(image, mask, [(80, 50, 40, 20)])
        self.assertEqual(result["status"], "review_required")

    def test_both_shapes_give_identical_detection(self):
        image, mask = _crossing_case()
        outcomes = []
        for shape in ("legacy", "flat"):
            with mock.patch.object(boundary_review.cv2, "HoughLinesP", _hough_as(shape)):
                result = detect_linear_boundary_conflict(image, mask, [(80, 50, 40, 20)])
            outcomes.append((result["status"], result["candidate_segment_count"],
                             result["candidate_line_mask_hash"]))
        self.assertEqual(outcomes[0], outcomes[1])


class HarmonicHoughShapeTest(unittest.TestCase):
    def test_solver_runs_with_detected_lines_on_installed_opencv(self):
        image, mask = _crossing_case()
        result = harmonic_fill.harmonic_boundary_fill(
            image, mask, polarity="dark_text_on_light_bg")
        self.assertIn(result["status"], {"accepted", "review_required", "rejected"})
        self.assertNotEqual(result["status"], "accepted")

    def test_both_shapes_give_identical_solver_result(self):
        image, mask = _crossing_case()
        outcomes = []
        for shape in ("legacy", "flat"):
            with mock.patch.object(harmonic_fill.cv2, "HoughLinesP", _hough_as(shape)):
                result = harmonic_fill.harmonic_boundary_fill(
                    image, mask, polarity="dark_text_on_light_bg")
            outcomes.append((result["status"], tuple(result["rejection_reasons"]),
                             result["candidate_bgr"].tobytes()))
        self.assertEqual(outcomes[0], outcomes[1])


if __name__ == "__main__":
    unittest.main()
