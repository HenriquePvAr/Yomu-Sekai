"""Mask refinement for stylised SFX lettering and the LaMA retry variant."""
from types import SimpleNamespace

import numpy as np

from yomu.ocr.ocr_balloon import _refine_lettering_mask, _eroded_mask_variant


def _base_mask():
    mask = np.zeros((300, 400), np.uint8)
    mask[100:140, 100:200] = 255
    mask[100:140, 220:320] = 255
    return mask


def test_refinement_covers_gaps_and_stays_in_the_box():
    group = SimpleNamespace(classification="sfx", box=(80, 80, 260, 100))
    refined = _refine_lettering_mask(_base_mask(), group, {"lettering_stroke_width": 4})
    assert int((refined > 0).sum()) > int((_base_mask() > 0).sum())
    # the gap between the two glyph cores is bridged
    assert bool(refined[115, 205:215].all())
    ys, xs = np.where(refined > 0)
    pad_x = max(2, int(260 * 0.06))
    pad_y = max(2, int(100 * 0.06))
    assert xs.min() >= 80 - pad_x and xs.max() <= 80 + 260 + pad_x
    assert ys.min() >= 80 - pad_y and ys.max() <= 80 + 100 + pad_y


def test_refinement_respects_measured_stroke():
    group = SimpleNamespace(classification="sfx", box=(80, 80, 260, 100))
    small = _refine_lettering_mask(_base_mask(), group, {"lettering_stroke_width": 1})
    large = _refine_lettering_mask(_base_mask(), group, {"lettering_stroke_width": 8})
    assert int((large > 0).sum()) > int((small > 0).sum())


def test_non_sfx_mask_untouched():
    group = SimpleNamespace(classification="speech", box=(80, 80, 260, 100))
    assert np.array_equal(
        _refine_lettering_mask(_base_mask(), group, {"lettering_stroke_width": 4}),
        _base_mask(),
    )


def test_eroded_variant_shrinks_and_falls_back_when_too_small():
    eroded = _eroded_mask_variant(_base_mask(), radius=5)
    assert int((eroded > 0).sum()) < int((_base_mask() > 0).sum())
    tiny = np.zeros((12, 12), np.uint8)
    tiny[5, 5] = 255
    # erosion would empty the mask: original is returned unchanged
    assert np.array_equal(_eroded_mask_variant(tiny, radius=5), tiny)
