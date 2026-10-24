"""Generic local-background reconstruction tests, independent of any chapter."""

import cv2
import numpy as np

import yomu.ocr.ocr_balloon as ob
from yomu.ocr.ocr_engine import OCRLine


def _group(box=(40, 40, 140, 40)):
    x, y, w, h = box
    polygon = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=np.int32)
    line = OCRLine(
        text="SOURCE TEXT",
        raw_text="SOURCE TEXT",
        confidence=0.99,
        polygon=polygon,
        box=box,
        engine="synthetic",
        page=1,
    )
    group = ob.TextGroup(group_id="local-background", lines=[line], text=line.text)
    group.classification = "speech"
    return group


def _mask(shape=(120, 220), box=(70, 50, 70, 20)):
    x, y, w, h = box
    result = np.zeros(shape, dtype=np.uint8)
    result[y:y + h, x:x + w] = 255
    return result


def _apply(fill, *, profile="solid_colored", text_fill=(245, 245, 245)):
    image = np.full((120, 220, 3), fill, dtype=np.uint8)
    mask = _mask()
    image[mask > 0] = text_fill
    group = _group()
    group.background_type = "textured_art"
    group.background_metrics = {
        "local_background_class": profile,
        "local_background_median_bgr": list(fill),
        "local_background_sample_count": 100,
    }
    return image, mask, group


def test_local_profile_preserves_light_dark_gray_and_chroma_without_defaults():
    for fill, text in [
        ((255, 255, 255), (20, 20, 20)),
        ((8, 8, 8), (245, 245, 245)),
        ((122, 122, 122), (245, 245, 245)),
        ((185, 55, 35), (245, 245, 245)),
        ((30, 210, 90), (20, 20, 20)),
    ]:
        image, mask, group = _apply(fill, text_fill=text)
        cleaned = ob._apply_cleanup_mask(image, image, group, mask)
        error = np.abs(cleaned[mask > 0].astype(np.int16) - np.asarray(fill, dtype=np.int16))
        assert float(np.percentile(error, 99)) <= 1.0


def test_estimator_classifies_local_colored_and_dark_contexts():
    for fill, expected in [
        ((245, 245, 245), "solid_light"),
        ((12, 12, 12), "solid_dark"),
        ((35, 110, 185), "solid_colored"),
    ]:
        image = np.full((120, 220, 3), fill, dtype=np.uint8)
        group = _group()
        mask = _mask()
        profile = ob._estimate_local_background_profile(
            image, group, mask, (40, 40, 140, 40)
        )
        assert profile["local_background_class"] == expected
        assert profile["local_background_spatial_class"] == "PROVEN_UNIFORM"


def test_spatial_profile_separates_gradient_structure_and_insufficient_samples():
    mask = _mask()
    group = _group()
    gradient = np.zeros((120, 220, 3), dtype=np.uint8)
    for row in range(gradient.shape[0]):
        gradient[row, :, :] = 40 + int(150 * row / (gradient.shape[0] - 1))
    gradient[mask > 0] = (0, 0, 0)
    profile = ob._estimate_local_background_profile(gradient, group, mask, (40, 40, 140, 40))
    assert profile["local_background_spatial_class"] == "SMOOTH_NONUNIFORM"

    yy, xx = np.indices((120, 220))
    tone = ((xx // 3 + yy // 3) % 2 * 190 + 40).astype(np.uint8)
    structured = np.repeat(tone[:, :, None], 3, axis=2)
    glyph_mask = np.zeros_like(mask)
    glyph_mask[55:67, 100:120] = 255
    profile = ob._estimate_local_background_profile(structured, group, glyph_mask, (40, 40, 140, 40))
    assert profile["local_background_spatial_class"] == "STRUCTURED_OR_TEXTURED"

    tiny_mask = np.zeros((120, 220), dtype=np.uint8)
    tiny_mask[59:61, 109:111] = 255
    profile = ob._estimate_local_background_profile(structured, group, tiny_mask, (108, 58, 4, 4))
    assert profile["local_background_spatial_class"] == "INSUFFICIENT_EVIDENCE"


def test_spatial_gate_denies_nonuniform_constant_fill_only_when_enabled(monkeypatch):
    image, mask, group = _apply((245, 245, 245), text_fill=(0, 0, 0))
    group.background_metrics["local_background_spatial_class"] = "SMOOTH_NONUNIFORM"
    monkeypatch.setattr(ob.config, "CLEAN_HARMONIC_FILL", False)
    baseline = ob._apply_cleanup_mask(image, image, group, mask)
    assert np.all(baseline[mask > 0] == np.array([245, 245, 245], dtype=np.uint8))

    monkeypatch.setattr(ob.config, "CLEAN_HARMONIC_FILL", True)
    experimental = ob._apply_cleanup_mask(image, image, group, mask)
    assert not np.all(experimental[mask > 0] == np.array([245, 245, 245], dtype=np.uint8))
    assert np.array_equal(experimental[mask == 0], image[mask == 0])


def test_spatial_gate_fallback_is_diagnostic_and_never_promoted_to_clean_safe(monkeypatch):
    image = np.full((120, 220, 3), (235, 235, 235), dtype=np.uint8)
    mask = _mask()
    image[mask > 0] = (0, 0, 0)
    group = _group()
    group.background_type = "textured_art"
    group.background_metrics = {
        "local_background_class": "solid_light",
        "local_background_spatial_class": "SMOOTH_NONUNIFORM",
        "local_background_median_bgr": [235, 235, 235],
        "local_background_sample_count": 128,
    }
    monkeypatch.setattr(ob.config, "CLEAN_HARMONIC_FILL", True)
    monkeypatch.setattr(
        ob,
        "_remove_text_for_group",
        lambda current, original, _group, strategy="primary": (
            current.copy(), mask.copy(), {"mask_valid": True, "strategy": strategy}
        ),
    )
    monkeypatch.setattr(
        ob,
        "_uncovered_source_text_evidence",
        lambda *_args, **_kwargs: {"measured": True, "source_text_pixels": 100},
    )
    monkeypatch.setattr(ob, "_source_removal_incomplete", lambda *_args: False)
    overlay_calls = []

    def overlay(canvas, authorized_mask, **_kwargs):
        overlay_calls.append(1)
        candidate = canvas.copy()
        candidate[authorized_mask > 0] = (220, 220, 220)
        return candidate

    monkeypatch.setattr(ob, "_apply_textured_caption_overlay", overlay)

    _cleaned, _used_mask, _strategy, clean_ok = ob._clean_source_for_clean_artifact(
        image, image, group,
    )

    assert overlay_calls
    assert clean_ok is False
    assert group.spatial_harmonic_gate_rejected is True
    assert group.clean_disposition != "LOCAL_SAFE"
    attempts = group.clean_artifact_validation["attempts"]
    assert any(
        attempt.get("reason") == "spatial_gate_candidate_diagnostic_only"
        for attempt in attempts
    )


def test_spatial_gate_off_preserves_clean_fill_behavior(monkeypatch):
    image, mask, group = _apply((245, 245, 245), text_fill=(0, 0, 0))
    group.background_metrics["local_background_spatial_class"] = "SMOOTH_NONUNIFORM"
    monkeypatch.setattr(ob.config, "CLEAN_HARMONIC_FILL", False)
    cleaned = ob._apply_cleanup_mask(image, image, group, mask)
    assert np.array_equal(cleaned[mask > 0], np.broadcast_to(
        np.array([245, 245, 245], dtype=np.uint8),
        (np.count_nonzero(mask), 3),
    ))


def test_gradient_profile_is_not_flattened_to_a_fixed_color():
    image = np.zeros((120, 220, 3), dtype=np.uint8)
    for row in range(image.shape[0]):
        value = 35 + int(180 * row / (image.shape[0] - 1))
        image[row, :, :] = value
    mask = _mask()
    image[mask > 0] = (250, 250, 250)
    group = _group()
    group.background_type = "textured_art"
    group.background_metrics = {
        "local_background_class": "gradient",
        "local_background_median_bgr": [120, 120, 120],
        "local_background_sample_count": 100,
    }
    cleaned = ob._apply_cleanup_mask(image, image, group, mask)
    values = cleaned[mask > 0][:, 0]
    assert int(values.max()) - int(values.min()) > 10


def test_local_color_mismatch_is_reported_by_cleanup_metrics():
    original, mask, group = _apply((30, 210, 90))
    cleaned = original.copy()
    cleaned[mask > 0] = (255, 255, 255)
    metrics = ob._local_background_reconstruction_metrics(original, cleaned, group, mask)
    assert metrics["local_background_color_mismatch"] is True

