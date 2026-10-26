"""Regions A Wimp's Tower Strategy Guide ep. 33 left in English or in review."""
import os
import unittest
from unittest import mock

import numpy as np

import yomu.ocr.ocr_balloon as ob
from yomu.download.local import local_folder_input
from yomu.review import region_taxonomy
from yomu.translation import semantic_fidelity


class SoundsWrittenTheSameTests(unittest.TestCase):
    def test_known_sound_echo_is_the_translation(self):
        self.assertTrue(ob._same_sound_in_target("HUM HUM", "HUM HUM"))
        self.assertTrue(ob._same_sound_in_target("AH...", "AH..."))

    def test_unknown_word_echo_is_not(self):
        self.assertFalse(ob._same_sound_in_target("PLEASE", "PLEASE"))


class ImpersonalPredicateTests(unittest.TestCase):
    def test_its_amazing_is_not_an_action(self):
        self.assertFalse(semantic_fidelity._state_replaced_action("WAH!IT'S AMAZING.", "UAU! É INCRÍVEL."))

    def test_personal_progressive_still_checked(self):
        self.assertTrue(semantic_fidelity._state_replaced_action("I'M LEAVING.", "ESTOU CANSADO."))


class GluedSentencePromotionTests(unittest.TestCase):
    def test_glued_sentence_counts_its_words(self):
        self.assertTrue(region_taxonomy.weak_label_semantic_promotion_allowed(
            "decorative", "THEMORE WERUNIT, THEEASIER IT'LL GET."))

    def test_contraction_is_a_clause_but_a_possessive_sign_is_not(self):
        allowed = region_taxonomy.weak_label_semantic_promotion_allowed
        self.assertTrue(allowed("unknown", "I'M SORRY!!"))
        self.assertTrue(allowed("decorative", "THAT'S RIGHT."))
        self.assertFalse(allowed("decorative", "JOE'S DINER."))
        self.assertFalse(allowed("decorative", "CRASH!"))


class LocalSnapshotRootTests(unittest.TestCase):
    def test_snapshots_live_under_the_runtime_root(self):
        with mock.patch.dict(os.environ, {"TRADUTOR_RUNTIME_ROOT": os.path.abspath("rt_probe")}), \
                mock.patch.object(local_folder_input, "LOCAL_SNAPSHOT_ROOT", None), \
                mock.patch("pathlib.Path.mkdir"), mock.patch("pathlib.Path.resolve", lambda self: self):
            root = local_folder_input.snapshot_workspace_root()
        self.assertEqual(root.name, "local_sources")
        self.assertNotIn(".cache", root.parts)


class CreditAndSplitWordTests(unittest.TestCase):
    def _category(self, text, label="narration"):
        return region_taxonomy.resolve_region_policy(
            original_classification=label, source_text=text, preserve_as_name=False,
            evidence={"confidence": 0.9})["normalized_classification"]

    def test_glued_staff_roll_and_chapter_end_are_credits(self):
        self.assertEqual(self._category("ArtPlanA AdaptationPyoPyo"), "credit_preserve")
        self.assertEqual(self._category("To be continued", "speech"), "credit_preserve")

    def test_all_caps_dialogue_with_art_is_not_a_credit(self):
        self.assertNotEqual(self._category("IT'S ALREADY A WORK OF ART EXACTLY AS IT IS!!!", "unknown"),
                            "credit_preserve")

    def test_split_word_is_ambiguous_only_when_it_spells_a_word(self):
        self.assertTrue(ob._split_word_ambiguous("VISIT OR"))
        self.assertFalse(ob._split_word_ambiguous("COME ON, CHEERS!"))

    def test_dictionary_word_is_not_suspicious_garbage(self):
        self.assertEqual(semantic_fidelity.suspicious_source_tokens(
            "INCLUDING IRONCLAD", "INCLUINDO O IRONCLAD"), ())
        self.assertEqual(semantic_fidelity.suspicious_source_tokens(
            "A RAT FROM SLLM", "UM RATO DO SLLM"), ("SLLM",))


class SurfaceFillTests(unittest.TestCase):
    def _canvas(self, gradient=True, line=False):
        h, w = 160, 260
        yy, xx = np.mgrid[0:h, 0:w]
        base = (60 + 0.6 * xx).astype(np.uint8) if gradient else np.full((h, w), 120, np.uint8)
        image = np.dstack([base, base, np.full((h, w), 140, np.uint8)]).copy()
        if line:
            image[:, 128:132] = 20
        mask = np.zeros((h, w), np.uint8)
        mask[60:100, 80:180] = 255
        image[mask > 0] = 250
        return image, mask

    def test_gradient_is_filled_continuously(self):
        image, mask = self._canvas()
        filled, metrics = ob._surface_fill(image, mask)
        self.assertEqual(metrics["surface_fill_reason"], "fitted")
        row = filled[80, 80:180, 0].astype(int)
        self.assertLess(abs(row[0] - (60 + 0.6 * 80)), 12)
        self.assertLess(abs(row[-1] - (60 + 0.6 * 179)), 12)

    def test_uniform_backdrop_and_crossing_art_are_left_to_other_fills(self):
        image, mask = self._canvas(gradient=False)
        self.assertIsNone(ob._surface_fill(image, mask)[0])
        image, mask = self._canvas(line=True)
        self.assertIsNone(ob._surface_fill(image, mask)[0])


if __name__ == "__main__":
    unittest.main()
