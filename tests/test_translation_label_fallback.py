"""When rebuilding the art under a translated region is unsafe, the translation is
placed without touching that art: a sound keeps its lettering with the Portuguese
beside it, dialogue over art goes in an opaque caption box grown to fit.
"""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import unittest

import numpy as np

import yomu.ocr.ocr_balloon as ob
from yomu.ocr.ocr_engine import OCRLine


def _group(text, translation, box, classification):
    x, y, w, h = box
    line = OCRLine(text=text, confidence=0.9, polygon=np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]]),
                   box=box, raw_text=text, engine="t", page=1)
    group = ob.TextGroup(group_id="BALAO_1", lines=[line], text=text)
    group.classification = classification
    group.translation = translation
    group.translation_valid = True
    return group


class TranslationLabelTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(0)
        self.page = rng.integers(0, 255, (600, 500, 3), dtype=np.uint8)  # busy art

    def test_sound_keeps_its_lettering_and_gets_a_subtitle(self):
        group = _group("HUFF", "HUNF", (200, 100, 120, 60), "sfx")
        page, allowed, box, mode = ob._render_translation_label(self.page.copy(), self.page, group, None)
        self.assertEqual(mode, "sfx_subtitle")
        x, y, w, h = group.box
        np.testing.assert_array_equal(page[y:y + h, x:x + w], self.page[y:y + h, x:x + w])
        lx, ly, lw, lh = box
        self.assertGreater(np.abs(page[ly:ly + lh, lx:lx + lw].astype(int) - self.page[ly:ly + lh, lx:lx + lw]).sum(), 0)
        self.assertTrue(allowed[ly + lh // 2, lx + lw // 2])

    def test_sound_avoids_other_text(self):
        group = _group("HUFF", "HUNF", (200, 100, 120, 60), "sfx")
        below = (150, 160, 220, 80)
        _page, _allowed, box, _mode = ob._render_translation_label(
            self.page.copy(), self.page, group, None, occupied_boxes=[below])
        self.assertFalse(ob._boxes_overlap(box, below))

    def test_dialogue_goes_in_a_box_that_covers_the_source_and_fits(self):
        group = _group("SO COLD...", "ESTÁ TÃO FRIO AQUI EM CIMA...", (180, 300, 90, 40), "speech")
        page, _allowed, box, mode = ob._render_translation_label(self.page.copy(), self.page, group, None)
        self.assertEqual(mode, "caption_box")
        lx, ly, lw, lh = box
        x, y, w, h = group.box
        self.assertTrue(lx <= x and ly <= y and lx + lw >= x + w and ly + lh >= y + h)
        self.assertTrue(group.rendered_lines)

    def test_rejected_translation_is_not_eligible_but_a_fit_failure_is(self):
        group = _group("SO COLD...", "FRIO", (10, 10, 50, 20), "speech")
        group.translation_valid = False
        group.translation_validation_reason = "semantic_drift"
        self.assertFalse(ob._translation_label_eligible(group))
        group.translation_validation_reason = "text_does_not_fit_region"
        self.assertTrue(ob._translation_label_eligible(group))
        group.translation_validation_reason = "translation_box_outside_safe_area"
        self.assertTrue(ob._translation_label_eligible(group))

    def test_narrow_box_widens_instead_of_breaking_words(self):
        group = _group("THERE'S NO NEED, REALLY!", "NÃO HÁ NECESSIDADE, DE VERDADE!", (220, 300, 40, 70), "speech")
        ob._render_translation_label(self.page.copy(), self.page, group, None)
        self.assertIn("NECESSIDADE,", " ".join(group.rendered_lines).split())


if __name__ == "__main__":
    unittest.main()
