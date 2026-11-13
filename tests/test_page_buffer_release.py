"""F1.1-F1.3: a rendered page must not keep its image buffers alive."""
from types import SimpleNamespace

import cv2
import numpy as np

from komyst.ocr.ocr_balloon import TextGroup, release_group_buffers
from komyst.pipeline import benchmark_pipeline as bp


def _state():
    page = np.zeros((40, 30, 3), np.uint8)
    return {
        "index": 1,
        "original_bgr": page,
        "clean_local_base": page.copy(),
        "_preflight_render": {"result": (page.copy(), {})},
        "candidates": [object(), object()],
        "raw_lines": [object(), object(), object()],
        "groups": [SimpleNamespace(group_id="g1", box=(2, 3, 4, 5))],
        "debug_data": {"items": []},
        "status": "completed",
    }


def test_release_drops_images_and_scratch_lists_but_keeps_what_reports_read():
    state = _state()
    bp._release_page_buffers(state)
    for name in ("original_bgr", "clean_local_base", "_preflight_render", "candidates", "raw_lines"):
        assert name not in state
    assert len(state["groups"]) == 1 and state["debug_data"] == {"items": []}
    assert state["page_hw"] == (40, 30)
    assert bp._released_count(state, "raw_lines") == 3
    assert bp._released_count(state, "candidates") == 2
    bp._release_page_buffers(state)  # idempotent: counts are not overwritten by a second call
    assert bp._released_count(state, "raw_lines") == 3


def test_clean_target_snapshot_is_identical_after_release():
    state = _state()
    before = bp._clean_target_snapshot(state)
    assert before[0]["geometry"] == [2, 3, 4, 5]
    bp._release_page_buffers(state)
    assert bp._clean_target_snapshot(state) == before


def test_group_count_trace_is_identical_after_release():
    state = _state()
    state["ocr_completed"] = True
    before = bp._group_count_trace([state])
    bp._release_page_buffers(state)
    assert bp._group_count_trace([state]) == before


def test_release_group_buffers_clears_the_six_page_sized_attributes():
    group = TextGroup(group_id="g")
    page = np.zeros((10, 10), bool)
    group._fill_source_bgr = page
    group.authorized_fill_extension = page
    group.structure_protect_mask = page
    group.light_enclosure_interior = page
    group._caption_effect_layers = object()
    group.fill_alternatives = [page]
    release_group_buffers(group)
    assert group._fill_source_bgr is None
    assert group.authorized_fill_extension is None
    assert group.structure_protect_mask is None
    assert group.light_enclosure_interior is None
    assert group._caption_effect_layers is None
    assert group.fill_alternatives == []


def test_post_translation_page_returns_no_preflight_render(tmp_path, monkeypatch):
    rng = np.random.default_rng(7)
    source = rng.integers(0, 256, (30, 30, 3), dtype=np.uint8)
    src = tmp_path / "s.png"
    assert cv2.imwrite(str(src), source)
    state = {
        "index": 1, "image_path": str(src), "output_path": str(tmp_path / "o.png"),
        "original_bgr": source, "raw_lines": [], "candidates": [], "groups": [],
        "_preflight_render": {"signature": "x", "result": (source, {}), "capture": {}},
    }
    monkeypatch.setattr(bp, "_plan_pipeline_flags", lambda: {"want_clean": False, "want_typeset": True})
    monkeypatch.setattr(bp, "_save_page_processed_cache", lambda _s: None)
    monkeypatch.setattr(bp, "render_analyzed_image",
                        lambda src_img, *_a, **_k: (src_img.copy(), {"items": []}))
    result = bp.process_post_translation_page(state)
    assert result.error is None, result.error
    assert result.page_state["_preflight_render"] is None
    state.update(result.page_state)  # what the caller does: the aggregate state is overwritten
    assert state["_preflight_render"] is None
