"""Glyph shape is measured per OCR line, not over the whole balloon.

A Wimp's Tower Strategy Guide ep. 33: upright, centred comic lettering read as
-28 degrees italic serif, because the shear test and the stroke ratios ran over
lines of different lengths at once.
"""
import os
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import yomu.ocr.ocr_balloon as ob
from yomu.ocr.ocr_engine import OCRLine

FONTS = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"


def _balloon(font_file, lines, size=34):
    font_path = FONTS / font_file
    if not font_path.exists():
        raise unittest.SkipTest(f"{font_file} not installed")
    font = ImageFont.truetype(str(font_path), size)
    image = Image.new("RGB", (640, 80 + 52 * len(lines)), "white")
    draw = ImageDraw.Draw(image)
    ocr_lines = []
    for index, text in enumerate(lines):
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        x = (640 - (right - left)) // 2
        y = 40 + index * 52
        draw.text((x - left, y - top), text, font=font, fill="black")
        box = (x - 4, y - 4, right - left + 8, bottom - top + 8)
        bx, by, bw, bh = box
        polygon = np.array([[bx, by], [bx + bw, by], [bx + bw, by + bh], [bx, by + bh]], dtype=np.int32)
        ocr_lines.append(OCRLine(text=text, confidence=0.99, polygon=polygon, box=box,
                                 raw_text=text, engine="rapidocr", page=1))
    bgr = np.asarray(image)[:, :, ::-1].copy()
    group = ob.TextGroup(group_id="BALAO_1", lines=ocr_lines, text=" ".join(lines))
    return bgr, group


class PerLineGlyphStyleTests(unittest.TestCase):
    LINES = ["YOU DID", "GREAT FOR A", "FIRST PRACTICE", "RUN."]

    def _style(self, font_file):
        bgr, group = _balloon(font_file, self.LINES)
        return ob.extract_glyph_style_profile(bgr, group, group.box)

    def test_centred_upright_lines_are_not_italic(self):
        style = self._style("comicbd.ttf")
        self.assertEqual(style["slant"], "normal", style)

    def test_monoline_comic_lettering_is_not_serif(self):
        self.assertNotEqual(self._style("comicbd.ttf")["family_class"], "serif")

    def test_serif_type_is_serif(self):
        self.assertEqual(self._style("georgia.ttf")["family_class"], "serif")

    def test_uniform_lines_have_no_size_hierarchy(self):
        bgr, group = _balloon("georgia.ttf", self.LINES)
        self.assertIsNone(ob._source_line_scale_ratios(group, bgr))


class VariantVoteTieBreakTests(unittest.TestCase):
    """ep. 33: two reads each backed by several variants; the cleaner one wins."""

    def _attempt(self, text, confidence=0.95):
        return {"text": text, "normalized_text": ob._source_recovery_normalized(text),
                "word_signature": ob._source_recovery_word_signature(text), "confidence": confidence}

    def test_read_without_lost_boundary_wins(self):
        attempts = [self._attempt("IT'S ALREADY A WORK OF ART")] * 3 + [self._attempt("ITSALREADY A WORK OF ART")] * 3
        agreement = ob._source_recovery_agreement(attempts)
        self.assertTrue(agreement["trusted"], agreement)
        self.assertEqual(agreement["canonical_source"], "IT'S ALREADY A WORK OF ART")

    def test_equally_clean_reads_stay_untrusted(self):
        attempts = [self._attempt("COME TO US TOO")] * 2 + [self._attempt("COME TO ME TOO")] * 2
        self.assertFalse(ob._source_recovery_agreement(attempts)["trusted"])


if __name__ == "__main__":
    unittest.main()
