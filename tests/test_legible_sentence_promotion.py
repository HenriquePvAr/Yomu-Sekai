import test_support._test_bootstrap as _test_bootstrap  # noqa: F401
from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest

from yomu.ocr import ocr_balloon as ob
from yomu.review import region_taxonomy


def _group(text, confidence=0.99, classification="decorative", container="narration"):
    line = ob.OCRLine(
        text=text, confidence=confidence, polygon=None, box=(0, 0, 100, 20),
        raw_text=text, engine="test",
    )
    group = ob.TextGroup(group_id="WEAK_1", lines=[line], text=text, classification=classification)
    group.preserve_as_name = False
    group.detected_proper_names = []
    group.ocr_quality_blocked = False
    group.ignored = True
    group.ignore_reason = "decorative_text" if classification == "decorative" else "weak_unknown_text"
    group.inside_balloon_like_region = container == "balloon"
    group.inside_narration_box_like_region = container == "narration"
    group.parent_balloon_id = "BOX_1" if container else ""
    group.background_type = {
        "balloon": "white_balloon",
        "narration": "narration_box",
    }.get(container, "textured_art")
    return group


class LegibleSentencePromotionTests(unittest.TestCase):
    def test_legible_sentence_in_narration_box_is_promoted(self):
        group = _group("We should return home", container="narration")

        self.assertTrue(ob._legible_sentence_promotion_allowed(group))
        ob._apply_classification_policy(group)
        self.assertEqual(group.classification, "unknown")
        self.assertFalse(group.ignored)
        self.assertTrue(group.story_display_promoted)

    def test_two_word_punctuated_sentence_in_balloon_is_promoted(self):
        self.assertTrue(ob._legible_sentence_promotion_allowed(
            _group("Come back!", container="balloon")
        ))

    def test_legible_store_sign_on_art_without_container_stays_preserved(self):
        group = _group("POTATO King of French cooking", container=None)
        group.background_type = "textured_art"
        group.background_metrics = {"local_texture_mean": 9.0, "edge_density": 0.08}
        # Reproduce the REF-B artifact: a nearby-region flag was true even though
        # the local background was textured art and there was no real container.
        group.inside_narration_box_like_region = True
        group.translation_validation_reason = "local_hard"
        group.remote_fallback_configured = False

        self.assertFalse(ob._legible_sentence_promotion_allowed(group))
        self.assertFalse(ob._decorative_textured_story_promotion_allowed(group))
        ob._apply_classification_policy(group)
        self.assertEqual(group.classification, "decorative")
        self.assertTrue(group.ignored)
        self.assertEqual(group.ignore_reason, "decorative_text")
        self.assertFalse(ob._should_translate_group(group))

    def test_single_word_sfx_or_action_is_not_promoted(self):
        self.assertFalse(ob._legible_sentence_promotion_allowed(_group("FROWN")))
        self.assertFalse(ob._legible_sentence_promotion_allowed(_group("BOOM!")))

    def test_low_confidence_is_not_promoted(self):
        self.assertFalse(ob._legible_sentence_promotion_allowed(_group("Come back!", 0.89)))

    def test_non_dictionary_word_is_not_promoted(self):
        self.assertFalse(ob._legible_sentence_promotion_allowed(_group("ZQX arrives today.")))

    def test_credit_and_url_are_not_promoted(self):
        self.assertFalse(ob._legible_sentence_promotion_allowed(
            _group("STORY BY:KKULBEOL ART BY:BEOLKKUL")
        ))
        self.assertFalse(ob._legible_sentence_promotion_allowed(
            _group("Read more at https://example.com")
        ))

    def test_series_title_is_not_promoted(self):
        region_taxonomy.set_series_identity("hero-killer")
        try:
            self.assertFalse(ob._legible_sentence_promotion_allowed(_group("Hero Killer")))
        finally:
            region_taxonomy.set_series_identity("")

    def test_unknown_group_can_use_the_same_structural_rule(self):
        self.assertTrue(ob._legible_sentence_promotion_allowed(
            _group("The door is open.", classification="unknown", container="narration")
        ))


if __name__ == "__main__":
    unittest.main()
