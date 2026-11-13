"""Words the OCR glued together are split by English word frequency before translation.

ep. 33: DeepL read "IT'S SOLIFELIKE" as "É COMO O SOLIFEL", "WEPLANTO MAKETHESE"
as a company ("A WEPLANTO") and "WHENISAFRONT" as "ISAFRONT".
"""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import unittest

import komyst.ocr.ocr_balloon as ob
from komyst.review.region_taxonomy import segment_words


class SegmentWordsTests(unittest.TestCase):
    def test_glued_ordinary_words_split_by_frequency(self):
        cases = {
            "WEPLANTO": ["WE", "PLAN", "TO"],
            "WHENISAFRONT": ["WHEN", "IS", "A", "FRONT"],
            "LEATHERTHIS": ["LEATHER", "THIS"],
            "THEYEVEN": ["THEY", "EVEN"],
            "HANDITOVER": ["HAND", "IT", "OVER"],
            "IFIATLEAST": ["IF", "I", "AT", "LEAST"],
            "ITUP": ["IT", "UP"],
        }
        for token, words in cases.items():
            self.assertEqual(segment_words(token), words, token)

    def test_names_sounds_and_misreads_stay_whole(self):
        # Korean names, onomatopoeia, a drawn-out interjection, a one-letter misread.
        for token in ("DAEHYEON", "YEONHAGO", "SITAGER", "RUSTILE", "ICHIGONYANYAN",
                      "AAAAAH", "SUMMONOR"):
            self.assertIsNone(segment_words(token), token)


class SplitGluedSourceWordsTests(unittest.TestCase):
    def test_sentence_is_split_and_words_are_kept(self):
        self.assertEqual(
            ob.split_glued_source_words("WEPLANTO MAKETHESE AVAILABLE TOTHEPRIVATE SECTOR."),
            "WE PLAN TO MAKE THESE AVAILABLE TO THE PRIVATE SECTOR.")

    def test_protected_name_is_not_split(self):
        self.assertEqual(ob.split_glued_source_words("ASK TOSKIN.", protected=["TOSKIN"]), "ASK TOSKIN.")
        self.assertEqual(ob.split_glued_source_words("ASK TOSKIN."), "ASK TO SKIN.")


class SourceRepairTests(unittest.TestCase):
    def test_misread_letter_attested_by_the_chapter(self):
        words = ob.chapter_source_words(["IF WE WANT THE HIDES,"])
        self.assertEqual(ob.split_glued_source_words("MAKE THESE HIPES AVAILABLE", chapter_words=words),
                         "MAKE THESE HIDES AVAILABLE")

    def test_dominant_common_word_and_apostrophe_shape(self):
        self.assertEqual(ob.split_glued_source_words("WE'VE PLRCHASED"), "WE'VE PURCHASED")
        self.assertEqual(ob.split_glued_source_words("WHY COLLDN'T IT"), "WHY COULDN'T IT")

    def test_chapter_name_glued_to_a_token(self):
        self.assertEqual(ob.split_glued_source_words("I'M GWANG-ILJEON,", chapter_names=["JEON"]),
                         "I'M GWANG-IL JEON,")

    def test_unproven_tokens_stay(self):
        for text in ("DAEHYEON TRADING", "CLUNA", "SUMMONOR,"):
            self.assertEqual(ob.split_glued_source_words(text), text)


if __name__ == "__main__":
    unittest.main()


class GluedBeforeContractionAndAbbreviationTests(unittest.TestCase):
    def test_glued_words_before_a_contraction_tail_are_split(self):
        self.assertEqual(ob.split_glued_source_words("ONELEAD'S"), "ONE LEAD'S")
        self.assertEqual(ob.split_glued_source_words("onelead's"), "one lead's")

    def test_real_contractions_stay_whole(self):
        for token in ("WE'RE", "DON'T", "COULDN'T", "IT'S", "SHE'LL", "THEY'VE", "I'M"):
            self.assertEqual(ob.split_glued_source_words(token), token, token)

    def test_a_protected_name_before_a_contraction_is_not_split(self):
        self.assertEqual(
            ob.split_glued_source_words("DAEHYEON'S", protected=("DAEHYEON",)), "DAEHYEON'S")

    def test_common_abbreviation_counts_as_a_word_piece(self):
        self.assertEqual(segment_words("THECEO"), ["THE", "CEO"])
        self.assertEqual(segment_words("THEDNA"), ["THE", "DNA"])
        self.assertEqual(ob.split_glued_source_words("THECEO"), "THE CEO")

    def test_name_like_tokens_do_not_gain_a_split_from_abbreviations(self):
        for token in ("JINHOSEO", "SEONHO", "DAEHYEON", "PAEHYEOK"):
            self.assertIsNone(segment_words(token), token)

