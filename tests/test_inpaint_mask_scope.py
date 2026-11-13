"""Contracts for proportional cleanup masks over simple and complex art."""
from __future__ import annotations

import numpy as np

import komyst.ocr.ocr_balloon as ob
from komyst.ocr.ocr_engine import OCRLine


def _group(background="textured_art", box=(30, 30, 80, 24)):
    x, y, w, h = box
    line = OCRLine(
        text="BLAST", confidence=0.98,
        polygon=np.asarray([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=np.float32),
        box=box, raw_text="BLAST", engine="synthetic", page=0,
    )
    group = ob.TextGroup(group_id="scope-test", lines=[line], text="BLAST")
    group.background_type = background
    group.background_metrics = {
        "local_background_class": "structured_or_textured" if background == "textured_art" else "solid_light"
    }
    return group


def test_complex_mask_adds_only_a_small_proportional_halo():
    group = _group()
    seed = np.zeros((120, 160), dtype=np.uint8)
    seed[38:42, 40:45] = 255
    seed[38:42, 54:59] = 255

    refined = ob._refine_lettering_mask(seed, group, {
        "background_type": "textured_art",
        "lettering_stroke_width": 7,
        "text_component_pixels": 80,
    })

    assert np.count_nonzero(refined) > np.count_nonzero(seed)
    assert np.count_nonzero(refined) <= 2 * 80
    # No morphological close may bridge separate strokes into a filled bar.
    assert not np.any(refined[38:42, 47:52])


def test_oversized_complex_seed_is_still_attempted_without_extra_growth():
    group = _group()
    seed = np.zeros((120, 160), dtype=np.uint8)
    seed[30:70, 30:70] = 255

    refined = ob._refine_lettering_mask(seed, group, {
        "background_type": "textured_art",
        "lettering_stroke_width": 6,
        "text_component_pixels": 300,
    })

    # The caller still sends this bounded candidate through the local cleanup
    # attempt and visual gates; the helper simply refuses to inflate it further.
    assert np.array_equal(refined, seed)


def test_plain_balloon_uses_a_line_scaled_halo_too():
    group = _group("white_balloon", box=(30, 30, 80, 30))
    seed = np.zeros((120, 160), dtype=np.uint8)
    seed[40:44, 50:55] = 255

    refined = ob._refine_lettering_mask(seed, group, {
        "background_type": "white_balloon",
        "lettering_stroke_width": 5,
        "text_component_pixels": 40,
    })

    assert np.count_nonzero(refined) > np.count_nonzero(seed)
    assert np.count_nonzero(refined) <= 3 * 40


def test_change_measurement_separates_mask_changes_from_leaks():
    before = np.zeros((20, 20, 3), dtype=np.uint8)
    after = before.copy()
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[5:10, 5:10] = 255
    after[6:8, 6:8] = 255
    after[0, 0] = 255

    metrics = ob._inpaint_change_metrics(before, after, mask)

    assert metrics["changed_pixels_in_mask"] == 4
    assert metrics["changed_pixels_outside_mask"] == 1
    assert metrics["changed_fraction_in_mask"] == 0.16

def test_sfx_glyph_halo_mask_rejects_boundary_touching_art_and_keeps_glyph_halo():
    img = np.full((160, 200, 3), 180, dtype=np.uint8)
    # Dark panel border/art line cutting through top and bottom of ROI (touches ROI boundary)
    img[30:130, 45:50] = 10
    # White background speedline touching ROI right boundary
    img[70:76, 110:150] = 250
    # Dark SFX glyph interior inside ROI (does NOT touch ROI boundary [30:130, 40:150])
    img[60:95, 75:95] = 15
    # White outline coupled to the dark SFX glyph (within 5px of dark core)
    img[57:98, 72:75] = 248
    img[57:98, 95:98] = 248

    group = _group('sfx_area', box=(40, 30, 110, 100))
    group.classification = 'sfx'
    mask, _stroke_w = ob._sfx_glyph_halo_mask(img, group)

    # Dark glyph core + coupled white outline are masked
    assert np.all(mask[65:90, 78:92] == 255)
    assert np.any(mask[65:90, 72:75] == 255)
    # Boundary-touching dark art line and uncoupled white speedline are NOT masked
    assert int(np.count_nonzero(mask[32:45, 45:50])) == 0
    assert int(np.count_nonzero(mask[70:76, 130:148])) == 0

def test_clean_commit_reuses_accepted_pixels_without_another_inference(monkeypatch):
    import numpy as np
    from types import SimpleNamespace
    from komyst.ocr import ocr_balloon as ob

    original = np.full((60, 80, 3), 100, np.uint8)
    current = original.copy()
    current[:5] = 71  # An earlier CLEAN region must survive this commit.
    candidate = np.full_like(original, 230)  # Carries unrelated rendered pixels.
    mask = np.zeros(original.shape[:2], np.uint8)
    mask[20:30, 25:45] = 255
    group = SimpleNamespace()

    def unexpected(*args, **kwargs):
        raise AssertionError("accepted candidate must not trigger another fill")

    monkeypatch.setattr(ob, "_learned_texture_fill", unexpected)
    monkeypatch.setattr(ob, "_apply_cleanup_mask_fill", unexpected)
    result = ob._apply_cleanup_mask(current, original, group, mask,
                                    accepted_candidate=candidate)
    np.testing.assert_array_equal(result[mask == 0], current[mask == 0])
    np.testing.assert_array_equal(result[mask > 0], candidate[mask > 0])


def test_v4_ceiling_keeps_owned_tapered_ends_outside_rotated_ocr_polygon(monkeypatch):
    group = _group("sfx_area", box=(20,20,100,70))
    group.classification = "sfx"
    group.lines[0].polygon = np.array([[25,20],[115,35],[100,65],[40,50]], np.float32)
    image = np.full((120,160,3), 220, np.uint8)
    observed = {}
    def mask(_image, _group, maximum_mask=None, **kwargs):
        observed["ceiling"] = maximum_mask.copy()
        return np.zeros(image.shape[:2], np.uint8), {"text_component_pixels": 0}
    monkeypatch.setattr(ob, "_sfx_glyph_halo_mask", mask)
    monkeypatch.setattr(ob, "_component_text_mask", lambda *args, **kwargs:
                        (np.zeros(image.shape[:2], np.uint8), {"text_component_pixels": 0}))
    _, removal_mask, metrics = ob._remove_text_for_group(image, image, group)
    assert observed["ceiling"][85,110] == 255
    # Enlarging a ceiling must never itself invent removable pixels.
    assert not removal_mask.any() and not metrics["mask_valid"]

