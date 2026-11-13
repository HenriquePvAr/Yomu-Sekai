"""Last-chance SFX region re-OCR (rapidocr crop + optional PaddleOCR escalation).

Fixture crops come from the physically validated ep. 285 runs (regions whose
page-level OCR reads were garbled: PElW, ULANE, VAS, HUR, AMCK, THUNe).
"""
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import importlib.util
import pytest

from komyst.config import settings as config
from komyst.ocr.sfx_region_reocr import _is_candidate, repair_sfx_region_reads

_FIXTURES = Path(__file__).resolve().parent.parent / "test_fixtures" / "sfx_region_reocr"
_PADDLE_AVAILABLE = importlib.util.find_spec("paddleocr") is not None


def _group(text, *, classification="sfx", background_type="sfx_area", confidence=0.9):
    return SimpleNamespace(
        text=text,
        classification=classification,
        background_type=background_type,
        confidence=confidence,
        ignored=False,
        fallback_used=False,
        ocr_quality_blocked=False,
        quality_reasons=[],
        box=(0, 0, 64, 32),
    )


def _page_with_fixture(name):
    # The original crop at native resolution is the input: group.box addresses it
    # directly, like the real pipeline's region crop.
    crop = cv2.imread(str(_FIXTURES / name))
    assert crop is not None, f"missing fixture {name}"
    group = _group(name.split("_", 1)[1].rsplit(".", 1)[0])
    group.box = (0, 0, crop.shape[1], crop.shape[0])
    return crop, group


def test_candidate_selection():
    with mock.patch.object(config, "TRANSLATE_SFX", True):
        assert _is_candidate(_group("ULANE")) is True           # garbled short sfx
        assert _is_candidate(_group("CLANK")) is False          # already a known sound
        assert _is_candidate(_group("VAS", confidence=0.95)) is True   # sfx background
        assert _is_candidate(_group("HERO")) is True   # candidacy is permissive; fuzzy refusal guards adoption
        assert _is_candidate(_group("A", background_type="white_balloon")) is False  # too short
        ignored = _group("ULANE"); ignored.ignored = True
        assert _is_candidate(ignored) is False


def test_rapidocr_crop_repairs_pelw():
    page, group = _page_with_fixture("014_PElW.png")
    with mock.patch.object(config, "TRANSLATE_SFX", True), \
            mock.patch.object(config, "OCR_SFX_PADDLE_ESCALATION", False):
        repairs = repair_sfx_region_reads([group], page, page_index=14)
    assert repairs, "expected a repair for PElW (crop re-reads PEW)"
    assert group.text == repairs[0]["to"]
    from komyst.translation.sfx_glossary import translate_sfx_fuzzy
    assert translate_sfx_fuzzy(group.text) is not None


@pytest.mark.skipif(not _PADDLE_AVAILABLE, reason="paddleocr not installed")
def test_paddle_escalation_repairs_ulane():
    page, group = _page_with_fixture("015_ULANE.png")
    with mock.patch.object(config, "TRANSLATE_SFX", True), \
            mock.patch.object(config, "OCR_SFX_PADDLE_ESCALATION", True):
        repairs = repair_sfx_region_reads([group], page, page_index=15)
    assert repairs, "expected Paddle escalation to recover CLANK from ULANE"
    assert group.sfx_reocr_repair["engine"] == "paddle"
    from komyst.translation.sfx_glossary import translate_sfx_fuzzy
    assert translate_sfx_fuzzy(group.text) is not None


def test_no_repair_when_engines_find_nothing():
    page, group = _page_with_fixture("058_HUR.png")
    with mock.patch.object(config, "TRANSLATE_SFX", True), \
            mock.patch.object(config, "OCR_SFX_PADDLE_ESCALATION", False), \
            mock.patch("komyst.ocr.sfx_region_reocr._rapid_crop_reads", return_value=[]):
        repairs = repair_sfx_region_reads([group], page, page_index=58)
    assert repairs == []
    assert not hasattr(group, "sfx_reocr_repair")
