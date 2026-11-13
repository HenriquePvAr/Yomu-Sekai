"""Residual sweep: report source text the primary OCR never detected."""
from types import SimpleNamespace
from unittest import mock

import numpy as np

from komyst.config import settings as config
from komyst.ocr.residual_sweep import (
    sweep_mode,
    sweep_page_residuals,
    sweep_unavailable_reason,
    synthetic_sfx_lines,
)
from komyst.ocr.ocr_balloon import TextGroup, get_translatable_groups
from komyst.ocr.ocr_engine import OCRLine
from komyst.core.page_processing_contracts import PreTranslationPageResult
import komyst.pipeline.benchmark_pipeline as pipeline


def _fake_gateway(detections):
    gateway = SimpleNamespace(unavailable_reason="", _next_id=0)
    gateway.sweep = lambda image: detections
    return gateway


def test_sweep_reports_only_undetected_regions():
    page = np.full((100, 200, 3), 255, np.uint8)
    detections = [
        {"box": [10, 10, 40, 20], "text": "CLINK", "confidence": 0.9},   # fantasma
        {"box": [60, 50, 22, 7], "text": "GRIP", "confidence": 0.9},    # já conhecido (0.6x)
        {"box": [150, 10, 30, 20], "text": "A", "confidence": 0.9},      # curto demais
        {"box": [20, 70, 40, 20], "text": "SUS", "confidence": 0.2},     # conf baixa
    ]
    known = [(100, 84, 36, 12)]  # GRIP em escala cheia
    with mock.patch("komyst.ocr.subprocess_ocr._ensure_gateway", return_value=_fake_gateway(detections)):
        residuals = sweep_page_residuals(page, known, page_index=4)
    texts = [r["text"] for r in residuals]
    assert "CLINK" in texts
    assert "GRIP" not in texts
    assert "A" not in texts
    assert "SUS" not in texts


def test_sweep_quiet_when_engine_unavailable():
    with mock.patch("komyst.ocr.subprocess_ocr._ensure_gateway", return_value=None):
        assert sweep_page_residuals(np.zeros((50, 50, 3), np.uint8), [], page_index=1) == []


def test_sweep_disabled_by_flag():
    with mock.patch.object(config, "OCR_RESIDUAL_SWEEP", False):
        assert sweep_page_residuals(np.zeros((50, 50, 3), np.uint8), [], page_index=1) == []


def test_only_high_confidence_short_display_tokens_become_synthetic_ocr_lines():
    detections = [
        {"bbox": [1, 2, 20, 10], "text": "CLINK", "confidence": 0.92},
        {"bbox": [30, 2, 20, 10], "text": "BLAST", "confidence": 0.99},
        {"bbox": [60, 2, 20, 10], "text": "THUNA", "confidence": 0.99},
        {"bbox": [1, 15, 30, 10], "text": "FIRE IS WEAK", "confidence": 0.99},
        {"bbox": [1, 30, 20, 10], "text": "CLINK", "confidence": 0.60},
    ]

    lines = synthetic_sfx_lines(detections, page_index=4, image_shape=(50, 100, 3))

    assert [line.text for line in lines] == ["CLINK", "BLAST", "THUNA"]
    assert lines[0].engine == "paddle_residual_sweep"
    assert lines[0].page == 4


def test_broad_sfx_detection_tightens_to_matching_glyph_components():
    image = np.full((500, 800, 3), 220, dtype=np.uint8)
    for x in (25, 175, 325, 475, 625):
        image[180:300, x:x + 60] = 0
    detection = [{"bbox": [0, 80, 800, 400], "text": "BLAST", "confidence": .99}]

    lines = synthetic_sfx_lines(
        detection, page_index=52, image_shape=image.shape, image_bgr=image,
    )

    assert len(lines) == 1
    assert lines[0].box == (25, 180, 660, 120)
    assert lines[0].metadata["residual_sweep_box_tightened"] is True


def test_broad_sfx_detection_keeps_box_when_glyph_evidence_is_ambiguous():
    image = np.full((500, 800, 3), 220, dtype=np.uint8)
    image[180:300, 25:85] = 0
    detection = [{"bbox": [0, 80, 800, 400], "text": "BLAST", "confidence": .99}]

    lines = synthetic_sfx_lines(
        detection, page_index=52, image_shape=image.shape, image_bgr=image,
    )

    assert lines[0].box == (0, 80, 800, 400)
    assert lines[0].metadata["residual_sweep_box_tightened"] is False


def test_tightening_keeps_smaller_final_letter_and_excludes_unoutlined_art():
    image = np.full((1200,800,3),220,np.uint8)
    for x in (30,130,230,330,430,530):
        image[500:620,x:x+50] = 0
    image[550:620,630:650] = 0  # Real smaller E, below old page-area floor.
    image[800:1000,30:120] = 30  # Unoutlined art is not a glyph.
    lines = synthetic_sfx_lines([{"bbox":[0,300,800,800],"text":"CRACKLE","confidence":.98}],
        page_index=12,image_shape=image.shape,image_bgr=image)
    assert lines[0].box == (30,500,620,120)


def test_unknown_sweep_sfx_can_reach_translation_after_visual_classification():
    line = OCRLine(
        text="THUA", confidence=0.848,
        polygon=np.asarray([[0, 40], [80, 40], [80, 50], [0, 50]], dtype=np.float32),
        box=(0, 40, 80, 10), raw_text="THUA", engine="paddle_residual_sweep",
        page=52, metadata={"residual_sweep_recovered": True},
    )
    group = TextGroup(group_id="SWEEP_P52_0_40", lines=[line], text="THUA")
    group.classification = "sfx"
    group.classification_evidence = {"residual_sweep_recovered": True}

    with mock.patch.object(config, "TRANSLATE_SFX", True):
        assert get_translatable_groups([group]) == [group]


def test_auto_fix_injects_only_groups_accepted_by_visual_classifier():
    image = np.zeros((50, 100, 3), dtype=np.uint8)
    existing = TextGroup(group_id="BALAO_1", classification="sfx")
    state = {"index": 4, "original_bgr": image, "groups": [existing], "raw_lines": []}
    result = PreTranslationPageResult(
        page_index=4, groups=(existing,), page_state=state, analyzable=True,
    )

    def classify(_image, lines, *, page_index):
        group = TextGroup(group_id="BALAO_1", lines=list(lines), text="CLINK")
        group.classification = "sfx"
        group.background_type = "sfx_area"
        assert page_index == 4
        return [], [group]

    detections = [{"page": 4, "bbox": (10, 10, 30, 15), "text": "CLINK", "confidence": .92}]
    with mock.patch.object(pipeline, "sweep_page_residuals", return_value=detections), \
         mock.patch.object(pipeline, "analyze_image_array", side_effect=classify), \
         mock.patch.object(config, "TRANSLATE_SFX", True):
        updated = pipeline._auto_fix_residual_sfx(result, state)

    assert state["residual_sweep_auto_fix"] == {
        "detected": 1, "synthetic_candidates": 1, "accepted": 1,
    }
    assert len(updated.translation_items) == 1
    assert updated.translation_items[0].text == "CLINK"
    assert updated.translation_items[0].source_engine == "paddle_residual_sweep"

def test_mask_known_boxes_fills_detected_region_with_border_median():
    from komyst.ocr.residual_sweep import _mask_known_boxes
    img = np.full((100, 120, 3), 240, dtype=np.uint8)
    # Dark text inside known box (20, 20, 40, 30)
    img[25:45, 25:55] = 0
    masked = _mask_known_boxes(img, [(20, 20, 40, 30)])
    # Original must not be mutated
    assert np.all(img[25:45, 25:55] == 0)
    # Known box must be filled with border median (~240)
    assert np.all(masked[25:45, 25:55] >= 230)


def test_rejected_large_ocr_box_cannot_hide_panel_from_independent_sweep():
    from types import SimpleNamespace
    large = OCRLine(text="RMKE", raw_text="RMKE", confidence=.58,
        box=(0, 100, 800, 900), polygon=np.array([[0,100],[800,100],[800,1000],[0,1000]]))
    established = OCRLine(text="DIALOGUE", raw_text="DIALOGUE", confidence=.99,
        box=(40, 20, 200, 40), polygon=np.array([[40,20],[240,20],[240,60],[40,60]]))
    credit = OCRLine(text="ASSISTANTS", raw_text="ASSISTANTS", confidence=.99,
        box=(20,1050,350,80), polygon=np.array([[20,1050],[370,1050],[370,1130],[20,1130]]))
    state = {"raw_lines": [large, established, credit], "groups": [], "candidates": [
        SimpleNamespace(line=large, ignored=True, ignore_reason="box_too_large"),
        SimpleNamespace(line=established, ignored=False, ignore_reason=""),
        SimpleNamespace(line=credit, ignored=True, ignore_reason="credit")]}
    known = pipeline._residual_sweep_known_boxes(state)
    assert large.box not in known
    assert established.box in known and credit.box in known


def test_weak_sound_reading_is_exposed_for_recheck_without_lowering_clean_floor():
    member = OCRLine(text="FluCK",raw_text="FluCK",confidence=.4,
        box=(10,10,50,60),polygon=np.array([[10,10],[60,10],[60,70],[10,70]]))
    group = TextGroup("g",lines=[member],text=member.text,classification="sfx")
    group.ignored=True;group.ignore_reason="sfx_translation_disabled"
    assert pipeline._residual_sweep_known_boxes({"raw_lines":[member],"groups":[group]}) == []


def test_rejected_ocr_clone_cannot_remask_the_same_physical_line():
    import copy
    from types import SimpleNamespace
    member = OCRLine(text="RMKE",raw_text="RMKE",confidence=.9,
        box=(0,10,800,900),polygon=np.array([[0,10],[800,10],[800,910],[0,910]]),
        metadata={"ocr_line_id":"same-source"})
    candidate = SimpleNamespace(line=copy.deepcopy(member),ignored=True,ignore_reason="box_too_large")
    assert pipeline._residual_sweep_known_boxes({"raw_lines":[member],"candidates":[candidate]}) == []


def test_repeated_sound_requires_both_independent_read_and_measured_glyphs():
    import copy
    from komyst.ocr import ocr_balloon as ob
    image = np.full((600,800,3),220,np.uint8)
    for x in (40,180,320,460,600):image[250:370,x:x+50]=0
    lines = synthetic_sfx_lines([{"bbox":[0,100,800,450],"text":"PSHHH","confidence":.97}],
                               page_index=6,image_shape=image.shape,image_bgr=image)
    member = lines[0]
    assert ob._line_ignore_reason(member,image.shape) == ""
    weak = copy.deepcopy(member); weak.confidence=.85
    assert ob._line_ignore_reason(weak,image.shape) == "noise_like_text"
    unmeasured = copy.deepcopy(member);unmeasured.metadata.pop("residual_sweep_glyphs_verified")
    assert ob._line_ignore_reason(unmeasured,image.shape) == "noise_like_text"
    primary = copy.deepcopy(member);primary.engine="rapidocr"
    assert ob._line_ignore_reason(primary,image.shape) == "noise_like_text"

def test_mode_off_never_starts_paddle():
    with mock.patch.object(config, "OCR_RESIDUAL_SWEEP_MODE", "off"),             mock.patch("komyst.ocr.subprocess_ocr._ensure_gateway") as gateway:
        assert sweep_mode() == "off"
        assert sweep_page_residuals(np.zeros((50, 50, 3), np.uint8), [], page_index=1) == []
    gateway.assert_not_called()


def test_unavailable_paddle_is_reported_with_its_reason():
    gateway = SimpleNamespace(unavailable_reason="spawn_failed:boom")
    with mock.patch("komyst.ocr.subprocess_ocr._gateway", gateway):
        assert sweep_unavailable_reason() == "spawn_failed:boom"
    with mock.patch("komyst.ocr.subprocess_ocr._gateway", None):
        assert sweep_unavailable_reason() == ""
