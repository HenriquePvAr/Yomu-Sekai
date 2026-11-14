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
