"""Owned caption glows: spatial colour proof, protected art and negative fills."""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import hashlib
from types import SimpleNamespace

import cv2
import numpy as np

from yomu.clean.ownership import lettering_effects as le
from yomu.ocr import ocr_balloon as ob


def scene():
    h, w = 320, 640
    yy, xx = np.mgrid[:h, :w]
    background = np.stack((40+xx*.12, 6+yy*.05, 25+xx*.07), axis=2).astype(np.uint8)
    core = np.zeros((h, w), np.uint8)
    cv2.putText(core, "LASER BLAST", (60, 168), cv2.FONT_HERSHEY_SIMPLEX, 1.8, 255, 3, cv2.LINE_8)
    glow = np.clip(cv2.GaussianBlur(core.astype(np.float32), (0, 0), 8)*5/255, 0, 1)
    source = np.clip(background*(1-glow[:, :, None])+np.array([235, 55, 155])*glow[:, :, None], 0, 255).astype(np.uint8)
    source[core > 0] = 0
    cv2.line(source, (20, 35), (610, 265), (255, 255, 255), 2)
    cv2.line(background, (20, 35), (610, 265), (255, 255, 255), 2)
    core[np.all(source >= 225, axis=2)] = 0
    layers = le.build_effect_layers(source, core, [(57, 124, 390, 49)])
    return source, background, core, layers


def test_uniform_coloured_background_does_not_invent_a_glow():
    source, _, core, _ = scene()
    source[:] = (120, 25, 80)
    source[core > 0] = 0
    assert le.build_effect_layers(source, core, [(57, 124, 390, 49)]) is None


def test_compositor_never_changes_protected_or_unauthorized_pixels():
    source, background, _, layers = scene()
    assert layers is not None
    candidate = le.composite_effect(source, background, layers)
    np.testing.assert_array_equal(candidate[layers.authorized == 0], source[layers.authorized == 0])
    np.testing.assert_array_equal(candidate[layers.protected > 0], source[layers.protected > 0])
    assert np.any(candidate != source)


def test_neighboring_text_is_not_owned_by_the_effect():
    source, _, core, layers = scene()
    assert layers is not None
    assert le.build_effect_layers(source, core, [(57, 124, 390, 49)],
                                  neighbor_boxes=[(150, 130, 35, 30)]) is None


def test_spatial_boundary_rejects_flat_black_and_global_median_fill():
    source, background, _, layers = scene()
    assert layers is not None
    # Strong spatial variation matters here: a near-uniform surface can
    # legitimately be reconstructed with its median colour.
    xx = np.indices(source.shape[:2])[1]
    gradient = np.stack((xx*.23, xx*.18, xx*.20), axis=2)
    source = np.clip(source.astype(float)+gradient, 0, 255).astype(np.uint8)
    background = np.clip(background.astype(float)+gradient, 0, 255).astype(np.uint8)
    good = le.composite_effect(source, background, layers)
    result = le.paired_boundary_color(source, good, layers.authorized,
                                     protected_mask=layers.protected)
    assert result["measured"] and result["passed"], result
    for color in ((0, 0, 0), np.median(source[layers.authorized == 0], axis=0)):
        bad = source.copy()
        bad[layers.authorized > 0] = color
        result = le.paired_boundary_color(source, bad, layers.authorized,
                                         protected_mask=layers.protected)
        assert result["measured"] and not result["passed"], result


def test_sparse_boundary_fails_closed():
    image = np.zeros((20, 20, 3), np.uint8)
    mask = np.zeros((20, 20), np.uint8)
    mask[8, 8] = 255
    assert le.paired_boundary_color(image, image, mask)["passed"] is False


def test_mutating_source_or_mask_invalidates_effect_authority():
    source, _, _, layers = scene()
    assert layers is not None
    group = SimpleNamespace(_caption_effect_layers=layers,
        source_completeness={"status": "pass"},
        _caption_effect_source_hash=hashlib.sha256(source.tobytes()).hexdigest())
    assert ob._active_caption_effect_layers(source, group, layers.authorized) is layers
    changed = source.copy()
    changed[0, 0] ^= 1
    assert ob._active_caption_effect_layers(changed, group, layers.authorized) is None
    mask = layers.authorized.copy()
    mask[0, 0] ^= 255
    assert ob._active_caption_effect_layers(source, group, mask) is None


def test_changing_a_protected_art_pixel_is_rejected():
    source, background, _, layers = scene()
    assert layers is not None
    group = SimpleNamespace(_caption_effect_layers=layers,
        source_completeness={"status": "pass"},
        _caption_effect_source_hash=hashlib.sha256(source.tobytes()).hexdigest())
    candidate = le.composite_effect(source, background, layers)
    ys, xs = np.where((layers.protected > 0) & (layers.effect > 0))
    candidate[ys[0], xs[0]] = 0
    metrics = {}
    assert ob._reconstruction_gate_failure(source, candidate, group, layers.authorized,
                                          "speed_lines", "caption_effect", metrics) == "protected_effect_art_changed"


def test_sfx_never_uses_caption_glow_repair(monkeypatch):
    monkeypatch.setattr(ob.config, "GENERATIVE_CAPTION_REPAIR_ENABLED", True)
    image = np.zeros((80, 100, 3), np.uint8)
    group = ob.TextGroup("sound", classification="sfx", text="CRACKLE")
    _, mask, metrics = ob._caption_effect_cleanup(image, image, group)
    assert not mask.any() and not metrics["mask_valid"]
    assert "caption_effect" not in ob._cleanup_strategies(group)


def test_cached_pixels_cannot_bypass_current_source_completeness(monkeypatch):
    from yomu.clean.inpainting import flux_edit
    from yomu.ocr.ocr_engine import OCRLine
    source = np.zeros((120, 180, 3), np.uint8)
    member = OCRLine(text="SOURCE", raw_text="SOURCE", confidence=.99,
        box=(20, 30, 130, 48), polygon=np.array([[20,30],[150,30],[150,78],[20,78]]),
        engine="synthetic", metadata={"ocr_line_id": "changed-source-id"})
    group = ob.TextGroup("caption", lines=[member], text="SOURCE", classification="narration")
    key = hashlib.sha256(source.tobytes()+repr([
        (member.text, tuple(member.box), member.confidence, member.metadata["ocr_line_id"])
    ]).encode()).hexdigest()
    group._caption_effect_result = {"source_key": key, "accepted": True}
    monkeypatch.setattr(flux_edit, "available", lambda **kwargs: True)
    monkeypatch.setattr(ob.source_completeness, "check_live_group",
                        lambda *args, **kwargs: {"status": "unavailable"})
    _, mask, metrics = ob._caption_effect_cleanup(source, source, group)
    assert not mask.any() and not metrics["mask_valid"]
    assert metrics["reason"] == "caption_effect_source_not_complete"
