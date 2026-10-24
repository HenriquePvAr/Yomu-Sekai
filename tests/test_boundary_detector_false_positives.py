"""Glyph/art boundary detector: letter rows and halftone are not art; corner diagonals are."""
import cv2
import numpy as np

from yomu.clean.ownership.glyph_art_boundary_review import (
    _outside_ridge_fraction,
    detect_linear_boundary_conflict,
)


def _text_image(background):
    image = background.copy()
    cv2.putText(image, "WORD", (70, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (10, 10, 10), 6, cv2.LINE_AA)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    glyph = (gray < 60).astype(np.uint8) * 255
    mask = cv2.dilate(glyph, np.ones((3, 3), np.uint8))
    ys, xs = np.where(glyph > 0)
    box = (int(xs.min()), int(ys.min()), int(np.ptp(xs)) + 1, int(np.ptp(ys)) + 1)
    return image, mask, box


def test_letter_row_over_a_dark_region_edge_is_not_art():
    # Bottom half darker: Otsu merges the row of letters with the dark region and
    # Hough used to report the top/bottom of the row as a crossing line.
    background = np.full((150, 300, 3), 200, np.uint8)
    background[80:] = 120
    image, mask, box = _text_image(background)
    result = detect_linear_boundary_conflict(image, mask, [box])
    assert result["candidate_segment_count"] == 0


def test_halftone_network_merged_with_glyph_contours_is_not_a_curve():
    background = np.full((150, 300, 3), 215, np.uint8)
    for yy in range(0, 150, 4):
        for xx in range(0, 300, 4):
            cv2.circle(background, (xx, yy), 1, (120, 120, 120), -1)
    image, mask, box = _text_image(background)
    result = detect_linear_boundary_conflict(image, mask, [box])
    assert result["candidate_curved_segment_count"] == 0


def test_diagonal_clipping_a_box_corner_is_reviewed():
    background = np.full((150, 300, 3), 220, np.uint8)
    image, mask, box = _text_image(background)
    x, y, w, h = box
    # Enters through the top edge and leaves through the left edge, over the "W".
    cv2.line(image, (x + 40, y - 30), (x - 30, y + h + 10), (10, 10, 10), 2, cv2.LINE_AA)
    mask_with_line = mask.copy()
    result = detect_linear_boundary_conflict(image, mask_with_line, [box])
    assert result["status"] == "review_required"


def test_ridge_fraction_separates_line_from_region_edge():
    gray = np.full((60, 120), 200, np.uint8)
    cv2.line(gray, (0, 30), (119, 30), 20, 2)
    exclude = np.zeros_like(gray)
    assert _outside_ridge_fraction(gray, exclude, (0, 30, 119, 30), True) > 0.9
    step = np.full((60, 120), 200, np.uint8)
    step[30:] = 60
    assert _outside_ridge_fraction(step, exclude, (0, 30, 119, 30), True) < 0.1
    exclude[:] = 255
    assert _outside_ridge_fraction(gray, exclude, (0, 30, 119, 30), True) is None
