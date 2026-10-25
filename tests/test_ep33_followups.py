"""Regions A Wimp's Tower Strategy Guide ep. 33 left in English or in review."""
import os
import unittest
from unittest import mock

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


class LocalSnapshotRootTests(unittest.TestCase):
    def test_snapshots_live_under_the_runtime_root(self):
        with mock.patch.dict(os.environ, {"TRADUTOR_RUNTIME_ROOT": os.path.abspath("rt_probe")}), \
                mock.patch.object(local_folder_input, "LOCAL_SNAPSHOT_ROOT", None), \
                mock.patch("pathlib.Path.mkdir"), mock.patch("pathlib.Path.resolve", lambda self: self):
            root = local_folder_input.snapshot_workspace_root()
        self.assertEqual(root.name, "local_sources")
        self.assertNotIn(".cache", root.parts)


if __name__ == "__main__":
    unittest.main()
