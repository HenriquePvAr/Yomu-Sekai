"""CLEAN_COMPARE_FILLS must not force the learned fill where the classic fill is trivially safe."""
from types import SimpleNamespace
from unittest import mock

import numpy as np

import komyst.ocr.ocr_balloon as ob


def _group(**metrics):
    base = {"local_background_class": "solid_light", "local_background_luminance_std": 2.0}
    base.update(metrics)
    return SimpleNamespace(background_metrics=base, classification="speech",
                           spatial_harmonic_gate_rejected=False, lines=[])


def test_trivially_safe_only_when_every_condition_holds():
    assert ob._classic_fill_is_trivially_safe(_group())
    assert ob._classic_fill_is_trivially_safe(_group(local_background_class="solid_dark"))
    assert not ob._classic_fill_is_trivially_safe(_group(local_background_class="textured_art"))
    assert not ob._classic_fill_is_trivially_safe(_group(local_background_luminance_std=6.5))
    assert not ob._classic_fill_is_trivially_safe(_group(local_background_luminance_std=None))
    sfx = _group(); sfx.classification = "sfx"
    assert not ob._classic_fill_is_trivially_safe(sfx)
    rejected = _group(); rejected.spatial_harmonic_gate_rejected = True
    assert not ob._classic_fill_is_trivially_safe(rejected)
    assert not ob._classic_fill_is_trivially_safe(SimpleNamespace())


def _run(group):
    image = np.full((40, 40, 3), 200, np.uint8)
    mask = np.zeros((40, 40), np.uint8); mask[10:20, 10:20] = 255
    with mock.patch.object(ob, "_learned_texture_fill", return_value=None) as learned, \
            mock.patch.object(ob, "_apply_cleanup_mask_fill", return_value=image.copy()), \
            mock.patch.object(ob, "_inside_white_enclosure", return_value=False), \
            mock.patch.object(ob, "_measure_structure_continuations"), \
            mock.patch.object(ob, "_flatten_dark_backdrop_residue", side_effect=lambda r, *a, **k: r), \
            mock.patch.object(ob.config, "CLEAN_COMPARE_FILLS", True), \
            mock.patch.object(ob.config, "CLEAN_SURFACE_FILL", False):
        ob._apply_cleanup_mask(image, image, group, mask)
    return learned


def test_flat_background_does_not_call_the_learned_fill_with_force():
    learned = _run(_group())
    assert not any(call.kwargs.get("force") for call in learned.call_args_list)


def test_textured_background_still_forces_the_learned_fill():
    learned = _run(_group(local_background_class="textured_art"))
    assert any(call.kwargs.get("force") for call in learned.call_args_list)
