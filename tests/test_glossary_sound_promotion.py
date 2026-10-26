"""Text made only of glossary sounds, outside any closed balloon, is a sound effect.

Shadow Slave ch. 13: "HUFF HUFF" lettered over the art was read as speech and
typeset in the dialogue font.
"""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import unittest

import numpy as np

import yomu.ocr.ocr_balloon as ob
from yomu.ocr.ocr_engine import OCRLine


def _group(text, *, enclosed=False, classification="speech"):
    line = OCRLine(text=text, confidence=0.9, polygon=np.zeros((4, 2), np.int32), box=(10, 10, 80, 20),
                   raw_text=text, engine="t", page=1)
    line.metadata = {"visual_white_region_enclosed": enclosed}
    group = ob.TextGroup(group_id="BALAO_1", lines=[line], text=text)
    group.classification = classification
    return group


class GlossarySoundPromotionTests(unittest.TestCase):
    def test_sound_on_the_art_becomes_sfx(self):
        group = _group("HUFF HUFF")
        ob._promote_glossary_sounds([group])
        self.assertEqual(group.classification, "sfx")

    def test_sound_inside_a_balloon_and_real_sentences_stay(self):
        inside, sentence = _group("HUFF HUFF", enclosed=True), _group("SO COLD...")
        ob._promote_glossary_sounds([inside, sentence])
        self.assertEqual(inside.classification, "speech")
        self.assertEqual(sentence.classification, "speech")


if __name__ == "__main__":
    unittest.main()
