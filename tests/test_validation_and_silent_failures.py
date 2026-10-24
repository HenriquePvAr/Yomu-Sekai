"""Verifier coverage vs crossing art, OCR tiling sufficiency, token completeness, re-OCR errors."""
from unittest.mock import patch

import cv2
import numpy as np

import yomu.ocr.ocr_balloon as ob
from yomu.ocr import source_completeness as completeness
from yomu.ocr.ocr_engine import OCR_INSUFFICIENT, OCR_REVIEW, OCR_SUFFICIENT, OCREngine, OCRLine


def _group(text, box):
    x, y, w, h = box
    poly = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], np.int32)
    line = OCRLine(text, 0.97, poly, box, text, engine="synthetic", metadata={"ocr_line_id": "v"})
    return ob.TextGroup(group_id="v", lines=[line], text=text, classification="speech")


def test_art_line_running_through_the_box_is_not_uncovered_source_text():
    image = np.full((120, 300, 3), 235, np.uint8)
    cv2.putText(image, "WORD", (80, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (15, 15, 15), 4, cv2.LINE_AA)
    cv2.line(image, (0, 78), (299, 78), (20, 20, 20), 3)  # panel line through the box
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    glyph = np.zeros_like(gray)
    glyph[30:75] = (gray[30:75] < 150) * 255
    mask = cv2.dilate(glyph, np.ones((5, 5), np.uint8))
    cleaned = image.copy()
    cleaned[mask > 0] = 235
    removal = ob._uncovered_source_text_evidence(image, cleaned, _group("WORD", (75, 30, 150, 52)), mask)
    assert removal["measured"]
    assert removal["source_text_coverage"] >= 0.98, removal
    assert ob._source_removal_status(_group("WORD", (75, 30, 150, 52)), removal) == ob.SOURCE_REMOVAL_VERIFIED


def test_glyph_left_inside_the_box_is_still_uncovered():
    image = np.full((120, 300, 3), 235, np.uint8)
    cv2.putText(image, "WORD", (80, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (15, 15, 15), 4, cv2.LINE_AA)
    mask = np.zeros(image.shape[:2], np.uint8)  # nothing cleaned
    removal = ob._uncovered_source_text_evidence(image, image.copy(), _group("WORD", (75, 30, 150, 52)), mask)
    assert removal["source_text_coverage"] < 0.5


def _tiling_engine():
    engine = object.__new__(OCREngine)
    engine.engine = "rapidocr"
    engine.last_run_metadata = {}
    return engine


def test_tall_page_tiling_keeps_worst_tile_sufficiency_at_top_level():
    engine = _tiling_engine()
    verdicts = iter([OCR_SUFFICIENT, OCR_INSUFFICIENT, OCR_REVIEW, OCR_SUFFICIENT])

    def single(_img, **_kwargs):
        engine.last_run_metadata = {"ocr_sufficiency": next(verdicts, OCR_SUFFICIENT),
                                    "engine_unavailable": False}
        return []

    tall = np.zeros((engine.TALL_IMAGE_TILE_MAX_HEIGHT * 3, 200, 3), np.uint8)
    with patch.object(engine, "_detect_lines_single", side_effect=single):
        engine.detect_lines(tall)
    assert engine.last_run_metadata["tall_image_tiling"]["tile_count"] > 1
    assert engine.last_run_metadata["ocr_sufficiency"] == OCR_INSUFFICIENT
    assert engine.last_run_metadata["engine_unavailable"] is False


def _line(text, line_id="L1"):
    return {"line_id": line_id, "text": text, "raw_text": text, "bbox": [0, 0, 100, 20], "parent_ids": []}


def test_completeness_matches_whole_tokens_not_substrings():
    result = completeness.check([_line("HERE IT IS")], downstream_text="THERE IT IS",
                                downstream_boxes=[(0, 0, 100, 20)])
    assert "HERE" in result["missing_tokens"]


def test_completeness_still_accepts_spacing_repair_both_ways():
    merged = completeness.check([_line("LOST CONTROL")], downstream_text="LOSTCONTROL",
                                downstream_boxes=[(0, 0, 100, 20)])
    split = completeness.check([_line("LOSTCONTROL")], downstream_text="LOST CONTROL",
                               downstream_boxes=[(0, 0, 100, 20)])
    assert merged["missing_tokens"] == [] and split["missing_tokens"] == []


def test_reocr_engine_errors_are_recorded_not_swallowed():
    class Broken:
        engine = "rapidocr"

        def detect_lines(self, *_args, **_kwargs):
            raise RuntimeError("model crashed")

    errors = []
    assert ob._reocr_crop_candidates([Broken()], np.zeros((10, 10, 3), np.uint8), errors=errors) == []
    assert errors == [{"engine": "rapidocr", "stage": "detect", "exception_type": "RuntimeError"}]

    init_errors = []
    with patch.object(ob, "OCREngine", side_effect=ImportError("no model")):
        assert ob._reocr_engines_for("en", init_errors) == []
    assert init_errors and init_errors[0]["stage"] == "init"


def test_textured_fill_pulled_off_the_ring_level_is_rejected():
    rng = np.random.default_rng(3)
    image = np.clip(120 + rng.normal(0, 6, (80, 160, 1)), 0, 255).repeat(3, axis=2).astype(np.uint8)
    mask = np.zeros((80, 160), np.uint8)
    cv2.putText(mask, "WORD", (25, 55), cv2.FONT_HERSHEY_SIMPLEX, 1.2, 255, 5)
    group = _group("WORD", (25, 25, 110, 35))
    group.background_metrics = {"local_background_class": "textured_art"}
    shifted = image.copy()
    shifted[mask > 0] = np.clip(shifted[mask > 0].astype(int) + 40, 0, 255).astype(np.uint8)
    assert ob._textured_fill_shift_metrics(image, shifted, group, mask)["textured_fill_shift_rejected"]
    assert not ob._textured_fill_shift_metrics(image, image.copy(), group, mask)["textured_fill_shift_rejected"]
    group.background_metrics = {"local_background_class": "solid_light"}
    assert not ob._textured_fill_shift_metrics(image, shifted, group, mask)["textured_fill_shift_rejected"]


def test_telea_source_neutralises_a_leftover_outline_without_touching_the_image():
    image = np.full((80, 160, 3), 120, np.uint8)
    mask = np.zeros((80, 160), np.uint8)
    mask[30:50, 40:120] = 255
    ring = (cv2.dilate(mask, np.ones((3, 3), np.uint8)) > 0) & (mask == 0)
    image[ring] = 245  # white outline the mask missed
    source = ob._telea_source_without_fringe(image, mask)
    assert int(source[ring].max()) < 140
    assert int(image[ring].min()) == 245  # caller's image untouched
