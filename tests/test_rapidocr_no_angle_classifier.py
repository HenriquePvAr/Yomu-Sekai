"""Page OCR runs without RapidOCR's 0/180 angle classifier.

Comic lettering is never upside down; the classifier flipped upright lines
("WHO?!" -> "j2OHM", "YOU TWO," -> "'OML nOK") on Fujiyama-san ch. 66.
"""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import unittest
from unittest import mock

import numpy as np

import yomu.ocr.ocr_engine as oe


class NoAngleClassifierTests(unittest.TestCase):
    def test_page_read_disables_cls(self):
        calls = []

        def fake_rapidocr(image, **kwargs):
            calls.append(kwargs)
            return [], 0.0

        engine = oe.OCREngine("rapidocr")
        with mock.patch.object(engine, "_get_rapidocr", return_value=fake_rapidocr):
            engine._detect_with_rapidocr(np.full((40, 40, 3), 255, np.uint8))
        self.assertEqual(calls, [{"use_cls": False}])


if __name__ == "__main__":
    unittest.main()


class FrequentWordQualityTests(unittest.TestCase):
    """Ch. 66: "LET'S RACE", "ALRIGHT", "HOLDING FOX" were held back as OCR damage."""

    def test_frequent_words_are_not_ocr_damage(self):
        from tests.test_rapidocr_region_recovery import _scored_group
        for text in ("Let's race", "Alright", '"HOLDING FOX"', "WANT A GIRLFRIEND~"):
            with self.subTest(text=text):
                group = _scored_group(text)
                self.assertNotIn("dictionary_near_miss", group.quality_reasons)
                self.assertNotIn("compact_word_segmentation_candidate", group.quality_reasons)
                self.assertNotIn("many_improbable_characters", group.quality_reasons)
