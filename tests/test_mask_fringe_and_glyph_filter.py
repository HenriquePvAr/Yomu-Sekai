"""Mask completeness: lettering fringe/outline, bold tight boxes, large glyph components."""
import cv2
import numpy as np

import yomu.ocr.ocr_balloon as ob
from yomu.ocr.ocr_engine import OCRLine


def _word_alpha(shape=(80, 160), text="WORD", thickness=12):
    big = np.zeros((shape[0] * 4, shape[1] * 4), np.uint8)
    cv2.putText(big, text, (96, 224), cv2.FONT_HERSHEY_SIMPLEX, 4.6, 255, thickness, cv2.LINE_AA)
    return cv2.resize(big, (shape[1], shape[0]), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0


def _group_for(alpha, text="WORD"):
    ys, xs = np.where(alpha > 0.05)
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    poly = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], np.int32)
    line = OCRLine(text, 0.97, poly, (x0, y0, x1 - x0, y1 - y0), text, engine="synthetic",
                   metadata={"ocr_line_id": "t"})
    return ob.TextGroup(group_id="t", lines=[line], text=text, classification="speech")


def _composite(background, alpha, ink):
    out = background.astype(np.float32) * (1 - alpha[..., None]) + ink * alpha[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def test_bold_word_in_tight_box_is_cleaned_on_flat_background():
    # The box median is the ink here; polarity must come from the band outside the box.
    alpha = _word_alpha()
    image = _composite(np.full((80, 160, 3), 235, np.uint8), alpha, 15)
    group = _group_for(alpha)
    cleaned, _mask, _strategy, ok = ob._clean_source_for_clean_artifact(image.copy(), image, group)
    assert ok, group.clean_artifact_validation
    assert int(cv2.cvtColor(cleaned, cv2.COLOR_BGR2GRAY).min()) > 200


def test_white_outline_round_dark_text_joins_the_mask():
    alpha = _word_alpha()
    ring = np.clip(cv2.dilate(alpha, np.ones((5, 5), np.uint8)) - alpha, 0, 1)
    background = np.full((80, 160, 3), 170, np.uint8)
    image = _composite(_composite(background, ring, 245), alpha, 15)
    core = ((alpha > 0.2) * 255).astype(np.uint8)
    group = _group_for(alpha)
    fringe, metrics = ob._antialias_fringe_mask(image, core, group)
    outline_px = (ring > 0.5) & (alpha < 0.2)
    covered = (fringe > 0) | (core > 0)
    assert metrics["antialias_fringe_pixels"] > 0
    assert np.count_nonzero(outline_px & covered) >= 0.8 * np.count_nonzero(outline_px)


def test_art_stroke_touching_a_glyph_is_not_taken_as_fringe():
    alpha = _word_alpha()
    background = np.full((80, 160, 3), 25, np.uint8)
    cv2.line(background, (0, 0), (159, 79), (130, 130, 130), 3)
    image = _composite(background, alpha, 245)
    core = ((alpha > 0.5) * 255).astype(np.uint8)
    line_px = np.zeros((80, 160), np.uint8)
    cv2.line(line_px, (0, 0), (159, 79), 255, 3)
    # Beyond the fringe reach (2 px): line pixels in a narrow gap between letters
    # are indistinguishable from fringe and are reconstructed with the word anyway.
    far_from_glyph = (line_px > 0) & (cv2.dilate((alpha > 0.05).astype(np.uint8), np.ones((5, 5), np.uint8)) == 0)
    fringe, _metrics = ob._antialias_fringe_mask(image, core, _group_for(alpha))
    assert np.count_nonzero((fringe > 0) & far_from_glyph) == 0


def test_large_glyph_components_are_kept_and_background_shapes_dropped():
    shape = (60, 120)
    joined = np.zeros(shape, np.uint8)
    cv2.putText(joined, "MW", (4, 52), cv2.FONT_HERSHEY_SIMPLEX, 2.0, 255, 9)
    _n, labels = cv2.connectedComponents(joined)
    biggest = labels == np.bincount(labels[labels > 0]).argmax()
    ys, xs = np.where(biggest)
    w, h = int(np.ptp(xs)) + 1, int(np.ptp(ys)) + 1
    assert not ob._component_is_background_shaped(biggest, int(biggest.sum()), w, h)

    solid = np.zeros(shape, bool)
    solid[5:55, 5:115] = True
    assert ob._component_is_background_shaped(solid, int(solid.sum()), 110, 50)

    frame = solid.copy()
    frame[8:52, 8:112] = False
    assert ob._component_is_background_shaped(frame, int(frame.sum()), 110, 50)

    stroke = np.zeros(shape, np.uint8)
    cv2.line(stroke, (0, 0), (119, 59), 1, 2)
    assert ob._component_is_background_shaped(stroke > 0, int(stroke.sum()), 120, 60)


def test_exclamation_line_keeps_its_glyph():
    alpha = _word_alpha(text="!", thickness=18)
    image = _composite(np.full((80, 160, 3), 235, np.uint8), alpha, 15)
    group = _group_for(alpha, text="!")
    _cleaned, mask, metrics = ob._remove_text_for_group(image.copy(), image, group, strategy="primary")
    ink = alpha > 0.5
    assert metrics.get("text_component_pixels", 0) > 0
    assert np.count_nonzero(ink & (mask > 0)) >= 0.95 * np.count_nonzero(ink)
