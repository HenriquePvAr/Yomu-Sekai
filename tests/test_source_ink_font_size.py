import test_support._test_bootstrap as _test_bootstrap  # noqa: F401
from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import komyst.ocr.ocr_balloon as ob
from komyst.ocr.ocr_balloon import OCRLine, TextGroup, render_analyzed_image

FONT = Path(__file__).resolve().parents[1] / "assets" / "fonts" / "comicrelief-bold.ttf"


def _page_with_lettering(size=44, pad=7):
    """A white page with two black capital lines, as in a speech balloon; boxes carry padding."""
    font = ImageFont.truetype(str(FONT), size)
    image = Image.new("RGB", (700, 400), "white")
    draw = ImageDraw.Draw(image)
    boxes, ink_heights = [], []
    for index, text in enumerate(("NOT TOO", "SHABBY.")):
        origin = (60, 120 + index * 70)
        left, top, right, bottom = draw.textbbox(origin, text, font=font)
        draw.text(origin, text, font=font, fill=(0, 0, 0))
        boxes.append((left - pad, top - pad, (right - left) + 2 * pad, (bottom - top) + 2 * pad))
        ink_heights.append(bottom - top)
    bgr = np.array(image)[:, :, ::-1].copy()
    return bgr, boxes, float(np.median(ink_heights))


def _group(text, boxes, translation):
    lines = []
    for word, box in zip(text.split(" ", 1) if " " in text else [text], boxes):
        x, y, w, h = box
        polygon = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=np.int32)
        lines.append(OCRLine(text=word, confidence=0.95, polygon=polygon, box=box, raw_text=word,
                             engine="rapidocr", page=1))
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    x1 = max(b[0] + b[2] for b in boxes); y1 = max(b[1] + b[3] for b in boxes)
    group = TextGroup(group_id="T", lines=lines, text=text, classification="speech",
                      inside_balloon_like_region=True, source_engine="rapidocr")
    group.translation = translation
    group.translation_candidate = translation
    group.translation_valid = True
    group.sent_to_translation = True
    return group


class SourceInkFontSizeTests(unittest.TestCase):
    # These pin the size rule; the face is held to the role's so a raster font match does not
    # change which size the rule starts from.
    def setUp(self):
        patcher = mock.patch.object(ob.config, "FONT_RASTER_MATCH", False, create=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_cap_ratio_of_a_bundled_face_is_a_sane_share_of_the_size(self):
        ratio = ob._font_cap_ratio(ImageFont.truetype(str(FONT), 100))
        self.assertTrue(0.55 < ratio < 0.85, ratio)

    def test_ink_height_ignores_the_padding_of_the_ocr_box(self):
        image, boxes, ink = _page_with_lettering()
        measured = ob._source_ink_cap_height(image, _group("NOT TOO SHABBY.", boxes, "NAO ESTA TAO RUIM"))
        self.assertAlmostEqual(measured, ink, delta=4)
        self.assertLess(measured, boxes[0][3])

    def test_a_line_taller_than_its_box_is_not_trusted(self):
        image, boxes, _ = _page_with_lettering()
        tiny = [(b[0], b[1] + 14, b[2], 12) for b in boxes]  # boxes far shorter than their ink
        self.assertEqual(ob._source_ink_cap_height(image, _group("NOT TOO SHABBY.", tiny, "x")), 0.0)

    def test_render_starts_from_the_real_letter_height(self):
        # The reference chapter's speech lettering is classified comic_sans_style (a plain
        # speech balloon); pin that class so the scene stands for it, not for display lettering.
        original = ob.typography_profile_for_region

        def comic_style(*args, **kwargs):
            profile = original(*args, **kwargs)
            profile["font_class"] = "comic_sans_style"
            return profile

        image, boxes, ink = _page_with_lettering()
        group = _group("NOT TOO SHABBY.", boxes, "NAO ESTA TAO RUIM ASSIM.")
        with mock.patch.object(ob, "typography_profile_for_region", comic_style):
            render_analyzed_image(image, [], [], [group], page_index=1)
        derived = group.font_runtime_validation["typography_profile"].get("font_size_from_source_ink")
        old_start = int(float(np.median([b[3] for b in boxes])) * 0.78)
        self.assertIsNotNone(derived)
        self.assertGreater(derived["size"], old_start)
        self.assertLessEqual(group.font_size, derived["size"])

    def test_display_lettering_also_starts_from_the_real_letter_height(self):
        """Its fixed share of the OCR box drew a shout at about half the source height."""
        original = ob.typography_profile_for_region

        def display_style(*args, **kwargs):
            profile = original(*args, **kwargs)
            profile["font_class"] = "tall_display"
            profile["style_source"] = "original_pixels"
            return profile

        image, boxes, _ = _page_with_lettering()
        group = _group("NOT TOO SHABBY.", boxes, "NAO ESTA TAO RUIM ASSIM.")
        with mock.patch.object(ob, "typography_profile_for_region", display_style):
            render_analyzed_image(image, [], [], [group], page_index=1)
        derived = group.font_runtime_validation["typography_profile"].get("font_size_from_source_ink")
        self.assertIsNotNone(derived)
        self.assertLessEqual(group.font_size, derived["size"])

    def test_a_translated_sound_effect_keeps_its_own_size_rule(self):
        image, boxes, _ = _page_with_lettering()
        group = _group("NOT TOO SHABBY.", boxes, "NAO ESTA TAO RUIM ASSIM.")
        group.classification = "sfx"
        render_analyzed_image(image, [], [], [group], page_index=1)
        profile = (getattr(group, "font_runtime_validation", None) or {}).get("typography_profile") or {}
        self.assertIsNone(profile.get("font_size_from_source_ink"))


if __name__ == "__main__":
    unittest.main()
