import test_support._test_bootstrap as _test_bootstrap  # noqa: F401
from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest
from types import SimpleNamespace

import yomu.ocr.ocr_balloon as ob


def _group(text, confidence=0.99):
    return SimpleNamespace(
        text=text, classification="decorative", preserve_as_name=False, quality_reasons=[],
        confidence=confidence, main_text_score=0.6,
        background_metrics={"context_saturation_mean": 84.0, "context_dark_pixel_ratio": 0.3,
                            "context_white_pixel_ratio": 0.1})


class TypesetCaptionPromotionTests(unittest.TestCase):
    def test_named_move_on_bright_art_is_promoted(self):
        self.assertTrue(ob._decorative_short_display_story_promotion_allowed(_group("DAEMON LASERBLAST")))

    def test_repeated_effect_and_single_word_stay_preserved(self):
        self.assertFalse(ob._decorative_short_display_story_promotion_allowed(_group("BOOM BOOM")))
        self.assertFalse(ob._decorative_short_display_story_promotion_allowed(_group("BLAST")))

    def test_uncertain_reading_is_not_promoted(self):
        self.assertFalse(ob._decorative_short_display_story_promotion_allowed(_group("DAEMON LASERBLAST", 0.88)))


if __name__ == "__main__":
    unittest.main()
