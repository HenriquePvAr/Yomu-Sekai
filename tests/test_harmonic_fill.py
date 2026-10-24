from __future__ import annotations

import unittest

import cv2
import numpy as np

from yomu.clean.inpainting.harmonic_fill import (
    classify_boundary_evidence,
    convert_spatial_background_class,
    harmonic_boundary_fill,
)


class HarmonicBoundaryFillTests(unittest.TestCase):
    def _mask(self, shape=(48, 56), box=(16, 16, 32, 32)):
        mask = np.zeros(shape, np.uint8)
        x0, y0, x1, y1 = box
        mask[y0:y1, x0:x1] = 255
        return mask

    def _solve(self, image, mask, **kwargs):
        return harmonic_boundary_fill(
            image,
            mask,
            spatial_class="SMOOTH_NONUNIFORM",
            polarity="dark_text_on_light_bg",
            tolerance=0.02,
            max_iterations=4000,
            **kwargs,
        )

    def test_spatial_class_conversion_is_conservative_and_does_not_approve(self):
        expected = {
            "PROVEN_UNIFORM": "uniform",
            "SMOOTH_NONUNIFORM": "smooth_gradient",
            "STRUCTURED_OR_TEXTURED": "complex",
            "INSUFFICIENT_EVIDENCE": "unknown",
        }
        for spatial, harmonic in expected.items():
            with self.subTest(spatial=spatial):
                metadata = convert_spatial_background_class(spatial)
                self.assertEqual(metadata["source"], "local_background_spatial_class")
                self.assertEqual(metadata["original_class"], spatial)
                self.assertEqual(metadata["converted_class"], harmonic)
                self.assertEqual(metadata["conversion_approves_reconstruction"], "false")
        with self.assertRaisesRegex(ValueError, "spatial_background_class_invalid"):
            convert_spatial_background_class("line_art")

    def test_solver_records_spatial_conversion_but_complex_remains_review(self):
        image = np.full((48, 56, 3), 210, np.uint8)
        mask = self._mask()
        image[mask > 0] = 0
        result = harmonic_boundary_fill(
            image, mask, spatial_class="STRUCTURED_OR_TEXTURED",
            polarity="dark_text_on_light_bg", max_iterations=100,
        )
        self.assertEqual(result["classification"]["original_class"], "STRUCTURED_OR_TEXTURED")
        self.assertEqual(result["classification"]["converted_class"], "complex")
        self.assertEqual(result["status"], "review_required")
        self.assertIn("background_class_not_harmonic_safe", result["rejection_reasons"])

    def test_constant_dirichlet_boundary_remains_constant(self):
        image = np.full((48, 56, 3), (216, 224, 232), np.uint8)
        mask = self._mask()
        image[mask > 0] = (0, 0, 0)

        result = self._solve(image, mask)

        self.assertTrue(result["converged"])
        self.assertEqual(result["status"], "accepted")
        self.assertTrue(np.array_equal(
            result["candidate_bgr"][mask > 0],
            np.broadcast_to(
                np.array([216, 224, 232], np.uint8),
                (np.count_nonzero(mask), 3),
            ),
        ))
        self.assertEqual(result["changed_pixels_outside_authorized_mask"], 0)

    def test_planar_dirichlet_boundary_recovers_discrete_harmonic_plane(self):
        y, x = np.indices((52, 64))
        image = np.stack((40 + 2 * x + y, 50 + x + 2 * y, 70 + x + y), axis=2)
        expected = image.astype(np.uint8)
        mask = self._mask((52, 64), (19, 17, 41, 35))
        image = expected.copy()
        image[mask > 0] = (0, 0, 0)

        result = self._solve(image, mask)

        self.assertTrue(result["converged"])
        error = np.abs(
            result["candidate_bgr"][mask > 0].astype(np.int16)
            - expected[mask > 0].astype(np.int16)
        )
        self.assertLessEqual(float(error.max()), 1.0)
        self.assertLessEqual(result["residual_linf"], 0.02)

    def test_contaminated_boundary_samples_are_unknown_not_dirichlet_donors(self):
        image = np.full((48, 56, 3), 180, np.uint8)
        mask = self._mask()
        image[mask > 0] = (0, 0, 0)
        contamination = np.zeros(mask.shape, np.uint8)
        contamination[15, 23] = 255
        image[15, 23] = (0, 0, 0)

        first = self._solve(image, mask, possible_contamination_mask=contamination)
        changed = image.copy()
        changed[15, 23] = (255, 255, 255)
        second = self._solve(changed, mask, possible_contamination_mask=contamination)

        self.assertEqual(first["status"], "review_required")
        self.assertIn(
            "possible_boundary_contamination_requires_review",
            first["rejection_reasons"],
        )
        self.assertTrue(np.array_equal(
            first["candidate_bgr"][mask > 0],
            second["candidate_bgr"][mask > 0],
        ))
        self.assertTrue(np.array_equal(
            first["candidate_bgr"][mask == 0], image[mask == 0],
        ))

    def test_external_lettering_evidence_keeps_region_in_review_without_mask_growth(self):
        image = np.full((48, 56, 3), 190, np.uint8)
        mask = self._mask()
        image[mask > 0] = 20
        evidence = np.zeros(mask.shape, np.uint8)
        evidence[14:17, 20:28] = 255

        result = self._solve(image, mask, possible_contamination_mask=evidence)

        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["authorized_pixels"], int(np.count_nonzero(mask)))
        self.assertEqual(result["changed_pixels_outside_authorized_mask"], 0)
        self.assertEqual(
            result["boundary_contamination"]["caller_suspect_pixels"],
            int(np.count_nonzero(evidence)),
        )

    def test_protected_art_is_preserved_and_intersection_requires_review(self):
        image = np.full((48, 56, 3), 210, np.uint8)
        mask = self._mask()
        image[mask > 0] = 0
        protected = np.zeros(mask.shape, np.uint8)
        protected[23, 16:32] = 255
        image[23, 16:32] = (12, 18, 24)

        result = self._solve(image, mask, protected_art_mask=protected)

        self.assertEqual(result["status"], "review_required")
        self.assertIn("protected_art_intersects_authorized_mask", result["rejection_reasons"])
        self.assertTrue(np.array_equal(
            result["candidate_bgr"][protected > 0], image[protected > 0],
        ))
        self.assertEqual(result["protected_pixels_changed"], 0)

    def test_structural_line_touching_boundary_is_not_accepted(self):
        image = np.full((48, 56, 3), 235, np.uint8)
        image[23:25, :, :] = 20
        mask = self._mask()
        image[mask > 0] = 0

        result = self._solve(image, mask)

        self.assertEqual(result["status"], "review_required")
        self.assertIn(
            "structural_edge_touches_dirichlet_boundary",
            result["rejection_reasons"],
        )
        self.assertEqual(result["changed_pixels_outside_authorized_mask"], 0)

    def test_low_contrast_structural_edge_crossing_mask_requires_review(self):
        image = np.full((64, 72, 3), 210, np.uint8)
        image[30:32, :, :] = 185  # 25-level edge, below the legacy Canny low threshold.
        mask = self._mask((64, 72), (24, 20, 48, 44))
        image[mask > 0] = 0

        result = self._solve(image, mask)

        self.assertTrue(result["structural_evidence"]["crossing_detected"])
        self.assertEqual(result["structural_evidence"]["category"], "STRUCTURAL_ART_CONFLICT")
        self.assertIn("structural_edge_touches_dirichlet_boundary", result["rejection_reasons"])
        self.assertTrue(result["soft_edge_diagnostic"]["candidate"])
        self.assertFalse(result["soft_edge_diagnostic"]["decision_impact"])

    def test_low_contrast_diagonal_edge_bridge_requires_review(self):
        image = np.full((80, 80, 3), 210, np.uint8)
        cv2.line(image, (8, 60), (70, 10), (185, 185, 185), 1)
        mask = self._mask((80, 80), (24, 24, 56, 56))
        image[mask > 0] = 0

        result = self._solve(image, mask)

        self.assertTrue(result["structural_evidence"]["crossing_detected"])
        self.assertIn("structural_edge_touches_dirichlet_boundary", result["rejection_reasons"])

    def test_parallel_art_edge_near_mask_is_not_a_crossing(self):
        image = np.full((80, 80, 3), 210, np.uint8)
        image[20:22, 8:72] = (65, 70, 75)
        mask = self._mask((80, 80), (24, 24, 56, 56))
        image[mask > 0] = 0

        result = self._solve(image, mask)

        self.assertFalse(result["structural_evidence"]["crossing_detected"])
        self.assertFalse(result["soft_edge_diagnostic"]["candidate"])
        self.assertFalse(result["soft_edge_diagnostic"]["decision_impact"])
        self.assertEqual(result["status"], "accepted")

    def test_sparse_outliers_with_far_band_support_can_be_accepted(self):
        image = np.full((180, 180, 3), 250, np.uint8)
        mask = np.zeros((180, 180), np.uint8)
        mask[26:154, 26:154] = 255
        image[mask > 0] = 0
        ring = (cv2.dilate((mask > 0).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & (mask == 0)
        ring_coords = np.argwhere(ring)
        suspects = ring_coords[[0, 128, 256, 384]]
        image[suspects[:, 0], suspects[:, 1]] = (220, 220, 220)
        yy, _ = np.indices(mask.shape)
        distance = cv2.distanceTransform((mask == 0).astype(np.uint8), cv2.DIST_L2, 3)
        reference = (mask == 0) & (distance >= 3) & (distance <= 8)
        image[reference & (yy % 3 == 0)] = (225, 225, 225)

        result = harmonic_boundary_fill(
            image, mask, background_class="smooth_gradient",
            polarity="dark_text_on_light_bg", tolerance=0.1, max_iterations=1000,
        )

        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["boundary_evidence"]["automatic_pixels"], 4)
        self.assertEqual(
            result["boundary_evidence"]["automatic_category"],
            "BENIGN_BACKGROUND_VARIATION",
        )
        self.assertEqual(result["changed_pixels_outside_authorized_mask"], 0)

    def test_sparse_auto_outliers_need_persistent_far_band_evidence(self):
        shape = (80, 80)
        target = np.zeros(shape, bool)
        target[24:56, 24:56] = True
        ring = (cv2.dilate(target.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & ~target
        distance = cv2.distanceTransform((~target).astype(np.uint8), cv2.DIST_L2, 3)
        reference = (~target) & (distance >= 3) & (distance <= 8)
        gray = np.full(shape, 250, np.uint8)
        gray[reference & (np.indices(shape)[0] % 3 == 0)] = 225
        auto = np.zeros(shape, bool)
        auto[ring] = False
        auto_coords = np.argwhere(ring)[:2]
        auto[auto_coords[:, 0], auto_coords[:, 1]] = True

        evidence = classify_boundary_evidence(
            gray, target, ring, reference, auto, np.zeros(shape, bool), polarity_cut=24,
        )

        self.assertEqual(evidence["automatic_category"], "BENIGN_BACKGROUND_VARIATION")
        self.assertTrue(evidence["benign_evidence"])
        self.assertEqual(evidence["components"][0]["origin"], "automatic_polarity_outlier")

    def test_caller_suspect_is_never_downgraded_to_benign(self):
        shape = (80, 80)
        target = np.zeros(shape, bool)
        target[24:56, 24:56] = True
        ring = (cv2.dilate(target.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & ~target
        distance = cv2.distanceTransform((~target).astype(np.uint8), cv2.DIST_L2, 3)
        reference = (~target) & (distance >= 3) & (distance <= 8)
        gray = np.full(shape, 250, np.uint8)
        gray[reference & (np.indices(shape)[0] % 3 == 0)] = 225
        auto = np.zeros(shape, bool)
        auto[ring] = True
        caller = np.zeros(shape, bool)
        caller[30, 23] = True

        evidence = classify_boundary_evidence(
            gray, target, ring, reference, auto, caller, polarity_cut=24,
        )

        self.assertFalse(evidence["benign_evidence"])
        self.assertEqual(evidence["caller_category"], "UNCERTAIN_BOUNDARY")
        self.assertIn("never_downgraded", evidence["components"][-1]["evidence"])

    def test_confirmed_fringe_category_requires_explicit_labeled_reference(self):
        shape = (16, 16)
        target = np.zeros(shape, bool)
        target[5:11, 5:11] = True
        ring = (cv2.dilate(target.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & ~target
        gray = np.full(shape, 220, np.uint8)
        confirmed = np.zeros(shape, bool)
        confirmed[5, 7:10] = True

        evidence = classify_boundary_evidence(
            gray, target, ring, np.zeros(shape, bool), np.zeros(shape, bool),
            np.zeros(shape, bool), polarity_cut=24, confirmed_lettering=confirmed,
        )

        self.assertEqual(evidence["overall_category"], "CONFIRMED_LETTERING_FRINGE")
        self.assertEqual(evidence["components"][-1]["origin"], "explicit_labeled_reference")

    def test_connected_automatic_fringe_is_not_downgraded_by_far_texture(self):
        shape = (80, 80)
        target = np.zeros(shape, bool)
        target[24:56, 24:56] = True
        ring = (cv2.dilate(target.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & ~target
        distance = cv2.distanceTransform((~target).astype(np.uint8), cv2.DIST_L2, 3)
        reference = (~target) & (distance >= 3) & (distance <= 8)
        gray = np.full(shape, 250, np.uint8)
        gray[reference & (np.indices(shape)[0] % 3 == 0)] = 225
        auto = np.zeros(shape, bool)
        auto[ring & (np.indices(shape)[0] == 23)] = True

        evidence = classify_boundary_evidence(
            gray, target, ring, reference, auto, np.zeros(shape, bool), polarity_cut=24,
        )

        self.assertEqual(evidence["automatic_category"], "UNCERTAIN_BOUNDARY")
        self.assertFalse(evidence["benign_evidence"])

    def test_repetitive_texture_class_is_rejected_even_when_solver_converges(self):
        image = np.indices((48, 56)).sum(axis=0) % 2
        image = np.repeat((image * 220 + 20).astype(np.uint8)[:, :, None], 3, axis=2)
        mask = self._mask()
        result = harmonic_boundary_fill(
            image, mask, background_class="repetitive_texture",
            polarity="dark_text_on_light_bg", tolerance=0.05,
            max_iterations=4000,
        )

        self.assertEqual(result["status"], "review_required")
        self.assertIn("background_class_not_harmonic_safe", result["rejection_reasons"])

    def test_empty_mask_and_invalid_shape_do_not_mutate_source(self):
        image = np.full((24, 32, 3), 90, np.uint8)
        empty = np.zeros(image.shape[:2], np.uint8)
        result = harmonic_boundary_fill(image, empty)
        self.assertEqual(result["status"], "no_op")
        self.assertTrue(np.array_equal(result["candidate_bgr"], image))
        with self.assertRaisesRegex(ValueError, "authorized_mask_shape_mismatch"):
            harmonic_boundary_fill(image, np.zeros((23, 32), np.uint8))

    def test_mask_touching_image_edge_is_fail_closed(self):
        image = np.full((24, 32, 3), 90, np.uint8)
        mask = np.zeros(image.shape[:2], np.uint8)
        mask[:4, 8:14] = 255

        result = harmonic_boundary_fill(
            image, mask, background_class="uniform",
            polarity="dark_text_on_light_bg",
        )

        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["rejection_reasons"], ["mask_touches_image_border"])
        self.assertTrue(np.array_equal(result["candidate_bgr"], image))

    def test_deterministic_results_and_runtime_report_for_small_and_larger_rois(self):
        for size in (32, 96):
            image = np.full((size + 24, size + 24, 3), 160, np.uint8)
            mask = np.zeros(image.shape[:2], np.uint8)
            start = 12
            mask[start:start + size, start:start + size] = 255
            image[mask > 0] = 0
            args = dict(
                background_class="uniform",
                polarity="dark_text_on_light_bg",
                tolerance=0.05,
                max_iterations=4000,
            )
            first = harmonic_boundary_fill(image, mask, **args)
            second = harmonic_boundary_fill(image, mask, **args)
            self.assertTrue(np.array_equal(first["candidate_bgr"], second["candidate_bgr"]))
            self.assertLessEqual(first["iterations"], args["max_iterations"])
            self.assertGreaterEqual(first["runtime_ms"], 0.0)
            self.assertEqual(first["changed_pixels_outside_authorized_mask"], 0)

    def test_large_sloped_roi_records_iterative_convergence_and_cpu_time(self):
        height, width = 144, 176
        y, x = np.indices((height, width))
        image = np.stack((
            100 + x // 5 + y // 9,
            120 + x // 8 + y // 5,
            140 + x // 9 + y // 7,
        ), axis=2).clip(0, 255).astype(np.uint8)
        mask = np.zeros((height, width), np.uint8)
        mask[28:116, 32:144] = 255
        image[mask > 0] = (0, 0, 0)

        result = harmonic_boundary_fill(
            image, mask, background_class="smooth_gradient",
            polarity="dark_text_on_light_bg", tolerance=0.1,
            max_iterations=6000,
        )

        self.assertGreater(result["iterations"], 1)
        self.assertLessEqual(result["iterations"], 6000)
        self.assertGreaterEqual(result["runtime_ms"], 0.0)
        self.assertTrue(np.isfinite(result["residual_linf"]))
        self.assertEqual(result["changed_pixels_outside_authorized_mask"], 0)


if __name__ == "__main__":
    unittest.main()
