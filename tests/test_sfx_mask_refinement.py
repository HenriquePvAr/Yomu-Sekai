"""Mask refinement for stylised SFX lettering and the LaMA retry variant."""
from types import SimpleNamespace

import numpy as np

from yomu.ocr.ocr_balloon import _refine_lettering_mask, _eroded_mask_variant


def _base_mask():
    mask = np.zeros((300, 400), np.uint8)
    mask[100:140, 100:200] = 255
    mask[100:140, 220:320] = 255
    return mask


def _group():
    return SimpleNamespace(classification="sfx", box=(80, 80, 260, 100),
        lines=[SimpleNamespace(box=(80, 80, 260, 100))], cleanup_lines=[],
        background_type="textured_art", background_metrics={})


def _metrics(stroke):
    return {"lettering_stroke_width": stroke, "text_component_pixels": 8000}


def test_refinement_preserves_gaps_and_uses_a_small_halo():
    group = _group()
    refined = _refine_lettering_mask(_base_mask(), group, _metrics(4))
    assert int((refined > 0).sum()) > int((_base_mask() > 0).sum())
    # Closing across separate letters was the overpainting behaviour; forbid it.
    assert not refined[115, 205:215].any()
    ys, xs = np.where(refined > 0)
    pad_x = max(2, int(260 * 0.06))
    pad_y = max(2, int(100 * 0.06))
    assert xs.min() >= 80 - pad_x and xs.max() <= 80 + 260 + pad_x
    assert ys.min() >= 80 - pad_y and ys.max() <= 80 + 100 + pad_y


def test_refinement_respects_measured_stroke():
    group = _group()
    small = _refine_lettering_mask(_base_mask(), group, _metrics(1))
    large = _refine_lettering_mask(_base_mask(), group, _metrics(8))
    assert int((large > 0).sum()) > int((small > 0).sum())


def test_surgical_v4_mask_is_never_expanded_again():
    group = _group()
    assert np.array_equal(
        _refine_lettering_mask(_base_mask(), group, {**_metrics(4), "sfx_glyph_halo_mask": True}),
        _base_mask(),
    )


def test_eroded_variant_shrinks_and_falls_back_when_too_small():
    eroded = _eroded_mask_variant(_base_mask(), radius=5)
    assert int((eroded > 0).sum()) < int((_base_mask() > 0).sum())
    tiny = np.zeros((12, 12), np.uint8)
    tiny[5, 5] = 255
    # erosion would empty the mask: original is returned unchanged
    assert np.array_equal(_eroded_mask_variant(tiny, radius=5), tiny)
