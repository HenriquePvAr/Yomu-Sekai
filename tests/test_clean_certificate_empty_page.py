import test_support._test_bootstrap as _test_bootstrap  # noqa: F401
from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np

import yomu.pipeline.benchmark_pipeline as bp


def _state(folder, groups):
    image = np.full((60, 80, 3), 200, dtype=np.uint8)
    source = Path(folder) / "source.png"
    clean = Path(folder) / "clean.png"
    cv2.imwrite(str(source), image)
    cv2.imwrite(str(clean), image)
    return {
        "image_path": str(source), "cleaned_path": str(clean), "original_bgr": image,
        "ocr_metadata": {"ocr_sufficiency": "OCR_SUFFICIENT"},
        "groups": groups, "clean_verified": True, "run_id": "run", "index": 1,
        "clean_result": {"status": "COMPLETED", "outside_mask_changed_pixels": 0},
    }


def _group(disposition):
    return SimpleNamespace(
        group_id="BALAO_1", region_id="REGION_001", classification="narration",
        box=(5, 5, 20, 10), text="HELLO", canonical_source_text="HELLO",
        clean_disposition=disposition, clean_remote_candidate=False, clean_remote_eligible=False,
        clean_remote_attempted=False, clean_remote_result="", clean_local_attempted=False,
        clean_artifact_validation={}, manual_review_required=False,
    )


class CleanCertificateTargetsTests(unittest.TestCase):
    def test_page_without_text_targets_can_be_certified(self):
        with tempfile.TemporaryDirectory() as folder:
            certificate = bp._make_clean_certificate(_state(folder, []), "job")
        self.assertEqual(certificate["status"], "PASS")

    def test_page_with_only_preserved_regions_can_be_certified(self):
        with tempfile.TemporaryDirectory() as folder:
            certificate = bp._make_clean_certificate(_state(folder, [_group("PRESERVE_SFX")]), "job")
        self.assertEqual(certificate["status"], "PASS")

    def test_non_review_ignored_decorative_and_untranslated_sfx_preserve_cleanly(self):
        from yomu.clean.disposition import RegionDisposition, classify_group_disposition
        import yomu.ocr.ocr_balloon as ob
        dec = SimpleNamespace(
            classification="decorative", ignored=True, ignore_reason="decorative_text",
            preserve_as_name=False, ocr_quality_blocked=False, text="BLAZE",
            manual_review_required=False,
        )
        disp, _ = classify_group_disposition(dec)
        self.assertEqual(disp, RegionDisposition.PRESERVE_ART)
        sfx = SimpleNamespace(
            classification="sfx", ignored=False, preserve_as_name=False,
            ocr_quality_blocked=False, text="THUNe", manual_review_required=True,
        )
        self.assertEqual(ob.get_cleanable_translatable_groups([sfx]), [])
        self.assertEqual(sfx.clean_disposition, RegionDisposition.PRESERVE_SFX.value)
        self.assertFalse(sfx.manual_review_required)

    def test_target_without_a_final_disposition_still_blocks(self):
        for disposition in ("", "PENDING_LOCAL", "NOT_A_DISPOSITION"):
            with self.subTest(disposition=disposition), tempfile.TemporaryDirectory() as folder:
                certificate = bp._make_clean_certificate(_state(folder, [_group(disposition)]), "job")
                self.assertEqual(certificate["status"], "REVIEW_REQUIRED")
                self.assertEqual(certificate["reason"], "target_or_ownership_incomplete")


if __name__ == "__main__":
    unittest.main()
