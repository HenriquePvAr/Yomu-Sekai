"""Tests for LANG-01: multi-language OCR source support."""
import unittest

from yomu.ocr.ocr_models import (
    CJK_LANGS,
    CYRILLIC_LANGS,
    LATIN_EXTRA_LANGS,
    source_is_cjk,
    source_is_english,
)
from yomu.review import region_taxonomy


class TestSourceIsEnglish(unittest.TestCase):
    def test_numeric_choice_3(self):
        self.assertTrue(source_is_english("3"))

    def test_en_code(self):
        self.assertTrue(source_is_english("en"))
        self.assertTrue(source_is_english("eng"))
        self.assertTrue(source_is_english("EN"))

    def test_japanese_not_english(self):
        self.assertFalse(source_is_english("1"))
        self.assertFalse(source_is_english("ja"))
        self.assertFalse(source_is_english("jpn"))
        self.assertFalse(source_is_english("japan"))

    def test_korean_not_english(self):
        self.assertFalse(source_is_english("2"))
        self.assertFalse(source_is_english("ko"))
        self.assertFalse(source_is_english("kor"))

    def test_cjk_not_english(self):
        self.assertFalse(source_is_english("zh"))
        self.assertFalse(source_is_english("ch"))

    def test_cyrillic_not_english(self):
        self.assertFalse(source_is_english("ru"))
        self.assertFalse(source_is_english("cyrillic"))

    def test_latin_extra_not_english(self):
        self.assertFalse(source_is_english("es"))

    def test_empty_and_none_safe(self):
        self.assertFalse(source_is_english(""))
        self.assertFalse(source_is_english(None))


class TestSourceIsCjk(unittest.TestCase):
    def test_japanese_choices(self):
        self.assertTrue(source_is_cjk("1"))
        self.assertTrue(source_is_cjk("ja"))
        self.assertTrue(source_is_cjk("jpn"))
        self.assertTrue(source_is_cjk("japan"))

    def test_korean_choices(self):
        self.assertTrue(source_is_cjk("2"))
        self.assertTrue(source_is_cjk("ko"))
        self.assertTrue(source_is_cjk("kor"))
        self.assertTrue(source_is_cjk("korean"))

    def test_chinese_choices(self):
        self.assertTrue(source_is_cjk("zh"))
        self.assertTrue(source_is_cjk("ch"))
        self.assertTrue(source_is_cjk("chinese"))

    def test_english_not_cjk(self):
        self.assertFalse(source_is_cjk("3"))
        self.assertFalse(source_is_cjk("en"))
        self.assertFalse(source_is_cjk("eng"))

    def test_cyrillic_not_cjk(self):
        self.assertFalse(source_is_cjk("ru"))
        self.assertFalse(source_is_cjk("cyrillic"))

    def test_latin_not_cjk(self):
        self.assertFalse(source_is_cjk("es"))
        self.assertFalse(source_is_cjk("latin"))

    def test_empty_and_none_safe(self):
        self.assertFalse(source_is_cjk(""))
        self.assertFalse(source_is_cjk(None))


class TestLangSets(unittest.TestCase):
    def test_cjk_langs_covers_all_scripts(self):
        for code in ("ja", "jpn", "japan", "ko", "kor", "korean", "zh", "ch", "chinese"):
            self.assertIn(code, CJK_LANGS, f"{code} missing from CJK_LANGS")

    def test_cyrillic_langs(self):
        self.assertIn("ru", CYRILLIC_LANGS)
        self.assertIn("cyrillic", CYRILLIC_LANGS)

    def test_latin_extra_langs(self):
        self.assertIn("es", LATIN_EXTRA_LANGS)
        self.assertIn("latin", LATIN_EXTRA_LANGS)


class TestWeakLabelNonEnglishGate(unittest.TestCase):
    """weak_label_semantic_promotion_allowed with non-English source_lang."""

    allowed = staticmethod(region_taxonomy.weak_label_semantic_promotion_allowed)

    # --- existing English behaviour unchanged ---
    def test_english_prose_promoted(self):
        self.assertTrue(self.allowed("decorative", "BY THE NIGHTMARE SPELL"))

    def test_english_contraction_promoted(self):
        self.assertTrue(self.allowed("unknown", "I'M SORRY!!"))

    def test_english_single_sfx_blocked(self):
        self.assertFalse(self.allowed("unknown", "BOOM"))

    # --- non-weak label always passes regardless of lang ---
    def test_non_weak_label_passes_any_lang(self):
        self.assertTrue(self.allowed("dialogue", "x", source_lang="ja"))
        self.assertTrue(self.allowed("thought", "x", source_lang="ko"))

    # --- non-English: 4+ chars = semantic ---
    def test_japanese_long_text_promoted(self):
        self.assertTrue(self.allowed("unknown", "日本語テスト", source_lang="ja"))
        self.assertTrue(self.allowed("unknown", "AAAA", source_lang="ja"))  # 4 chars

    def test_japanese_short_text_blocked(self):
        self.assertFalse(self.allowed("unknown", "日本", source_lang="ja"))  # 2 chars
        self.assertFalse(self.allowed("unknown", "ABC", source_lang="ja"))   # 3 chars

    def test_korean_4_chars_promoted(self):
        self.assertTrue(self.allowed("decorative", "한국어!", source_lang="ko"))

    def test_chinese_4_chars_promoted(self):
        self.assertTrue(self.allowed("unknown", "中文测试", source_lang="zh"))

    def test_russian_promoted(self):
        self.assertTrue(self.allowed("unknown", "Привет мир", source_lang="ru"))

    def test_spanish_promoted(self):
        self.assertTrue(self.allowed("unknown", "Hola mundo!", source_lang="es"))

    # --- numeric choice codes resolve correctly ---
    def test_choice_1_ja_gate(self):
        self.assertTrue(self.allowed("unknown", "テスト!", source_lang="1"))
        self.assertFalse(self.allowed("unknown", "テ", source_lang="1"))

    def test_choice_2_ko_gate(self):
        self.assertTrue(self.allowed("unknown", "안녕하세요", source_lang="2"))

    def test_choice_3_english_gate(self):
        # "BOOM" should still be blocked with source_lang "3" (=English)
        self.assertFalse(self.allowed("unknown", "BOOM", source_lang="3"))


if __name__ == "__main__":
    unittest.main()


class TestNonLatinOcrQuality(unittest.TestCase):
    """English-only OCR heuristics must not flag every CJK/Hangul/Cyrillic letter as damage."""

    def _scored(self, text):
        import numpy as np
        from yomu.ocr.ocr_balloon import TextGroup, rapidocr_region_decision, score_group_ocr_quality
        from yomu.ocr.ocr_engine import OCRLine

        line = OCRLine(text=text, confidence=0.95,
                       polygon=np.array([[10, 10], [210, 10], [210, 45], [10, 45]], dtype=np.int32),
                       box=(10, 10, 200, 35), raw_text=text, engine="rapidocr", page=1)
        group = TextGroup(group_id="T001", lines=[line], text=text, classification="speech",
                          inside_balloon_like_region=True, source_engine="rapidocr")
        group.quality_score, group.quality_reasons = score_group_ocr_quality(group)
        return group, rapidocr_region_decision(group)

    def test_non_latin_speech_is_not_an_ocr_artifact(self):
        for text in ("どうして来たの？", "你为什么来这里？", "왜 여기 왔어?", "Почему ты здесь?"):
            with self.subTest(text=text):
                group, decision = self._scored(text)
                self.assertEqual(group.quality_reasons, ["non_latin_script"])
                self.assertEqual(decision, "accept")

    def test_english_scoring_is_unchanged(self):
        group, _ = self._scored("DO YOU KNOW WHY THEY'RE TRYING TO COME HERE?")
        self.assertNotIn("non_latin_script", group.quality_reasons)
        group, _ = self._scored("CAFÉ AU LAIT")
        self.assertNotIn("non_latin_script", group.quality_reasons)
