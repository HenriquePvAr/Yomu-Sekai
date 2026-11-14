"""Asterisk censoring read by the OCR as CJK ideographs must come back as asterisks (no tofu)."""
from komyst.ocr.ocr_engine import clean_ocr_text

IDEOGRAPH = "米"


def test_ideographs_inside_latin_lettering_become_asterisks():
    assert clean_ocr_text(f"YET THAT B {IDEOGRAPH * 4} SEEMS FINE.") == "YET THAT B**** SEEMS FINE."
    assert clean_ocr_text("WHAT THE ※※※!") == "WHAT THE ***!"
    assert clean_ocr_text(f"COUNT ON no{IDEOGRAPH * 2}") == f"COUNT ON no{IDEOGRAPH * 2}"  # noise, not censoring


def test_text_that_is_not_latin_lettering_is_left_alone():
    assert clean_ocr_text(IDEOGRAPH * 2) == IDEOGRAPH * 2
    assert clean_ocr_text(f"A B {IDEOGRAPH}") == f"A B {IDEOGRAPH}"
    assert clean_ocr_text("HELLO WORLD") == "HELLO WORLD"


def test_a_stored_translation_with_censor_ideographs_is_drawn_with_asterisks():
    import numpy as np

    from komyst.ocr import ocr_balloon as ob
    from komyst.ocr.ocr_balloon import OCRLine, TextGroup

    polygon = np.array([[20, 20], [380, 20], [380, 70], [20, 70]], dtype=np.int32)
    line = OCRLine(text="YET THAT B**** SEEMS FINE.", confidence=0.95, polygon=polygon, box=(20, 20, 360, 50),
                   raw_text="x", engine="rapidocr", page=1)
    group = TextGroup(group_id="T", lines=[line], text="YET THAT B**** SEEMS FINE.", classification="speech",
                      inside_balloon_like_region=True, source_engine="rapidocr")
    group.translation = f"MAS AQUELE B {IDEOGRAPH * 4} PARECE BEM."
    from PIL import ImageDraw
    import unittest.mock as mock

    seen = []
    original_text = ImageDraw.ImageDraw.text

    def spy(self, xy, text, *args, **kwargs):
        seen.append(str(text))
        return original_text(self, xy, text, *args, **kwargs)

    image = np.full((120, 420, 3), 255, np.uint8)
    with mock.patch.object(ImageDraw.ImageDraw, "text", spy):
        ob._draw_group_translation(image, group, None)
    drawn = " ".join(seen)
    assert drawn and IDEOGRAPH not in drawn and "B****" in drawn
