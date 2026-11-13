"""Deterministic artifacts and fail-closed drafts for glyph/art boundaries."""
from __future__ import annotations

import hashlib
import json
from typing import Any

import cv2
import numpy as np

SCHEMA_VERSION = "1"
BOUNDARY_DETECTOR_METHOD = "scaled_hough_curved_edges_conflict_detector_v2"
CLASSIFICATIONS = {
    "glyph_fill", "glyph_outline", "glyph_antialias", "glyph_shadow",
    "glyph_punctuation", "protected_art", "uncertain",
}


def _canonical(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def hough_segments(lines: Any) -> np.ndarray:
    """Normalise ``cv2.HoughLinesP`` output to ``(N, 4)`` int32 segments.

    OpenCV returns ``(N, 1, 4)`` up to 4.x and ``(N, 4)`` from 5.0. Anything
    whose trailing axis is not four coordinates means "no lines".
    """
    if lines is None:
        return np.empty((0, 4), dtype=np.int32)
    candidate = np.asarray(lines)
    if candidate.ndim < 2 or candidate.shape[-1] != 4:
        return np.empty((0, 4), dtype=np.int32)
    return candidate.reshape(-1, 4).astype(np.int32, copy=False)


def _outside_ridge_fraction(
    gray: np.ndarray, exclude: np.ndarray, segment: tuple[int, int, int, int],
    dark: bool,
) -> float | None:
    """Fraction of a segment's off-glyph samples that are a thin line, not a region edge.

    Sampled only where the segment leaves the (dilated) removable mask: an art line
    there is darker (or lighter) than both sides 4 px away. The top or bottom of a
    row of letters merged with a dark background by Otsu is not. ``None`` means the
    segment never leaves the mask, so there is nothing to judge.
    """
    ax, ay, bx, by = segment
    length = float(np.hypot(bx - ax, by - ay))
    if length < 1.0:
        return None
    t = np.linspace(0.0, 1.0, max(2, int(length) + 1))
    cx, cy = ax + t * (bx - ax), ay + t * (by - ay)
    nx, ny = -(by - ay) / length * 4.0, (bx - ax) / length * 4.0
    h, w = gray.shape
    def sample(px, py):
        ix = np.clip(np.rint(px).astype(int), 0, w - 1)
        iy = np.clip(np.rint(py).astype(int), 0, h - 1)
        return ix, iy
    ix, iy = sample(cx, cy)
    outside = exclude[iy, ix] == 0
    if np.count_nonzero(outside) < 6:
        return None
    center = gray[iy, ix].astype(np.float32)
    side_a = gray[sample(cx + nx, cy + ny)[::-1]].astype(np.float32)
    side_b = gray[sample(cx - nx, cy - ny)[::-1]].astype(np.float32)
    sign = 1.0 if dark else -1.0
    ridge = (sign * (side_a - center) >= 12.0) & (sign * (side_b - center) >= 12.0)
    return float(np.mean(ridge[outside]))


def bitmap_hash(mask: np.ndarray) -> str:
    return hashlib.sha256(
        ((np.asarray(mask) > 0).astype(np.uint8) * 255).tobytes()).hexdigest()


def _curved_crossing_components(
    gray: np.ndarray, authorized: np.ndarray,
    box: tuple[int, int, int, int],
) -> tuple[list[np.ndarray], int]:
    """Return only curved edge components that cross an OCR box and its mask.

    This is a conservative conflict signal: it does not say whether an edge is
    hair, clothing, a halftone boundary, or a glyph. Components fully contained
    by the OCR box or dominated by authorized text pixels are excluded so
    ordinary curved letter strokes do not turn a no-conflict result into a
    review by themselves.
    """
    x, y, width, height = box
    edges = cv2.Canny(gray, 40, 120, L2gradient=True)
    contour_band = cv2.dilate(authorized, np.ones((5, 5), np.uint8)) > 0
    edges = cv2.morphologyEx(
        edges, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        (edges > 0).astype(np.uint8), connectivity=8)
    minimum_span = max(24, int(round(min(width, height) * 1.50)))
    curves: list[np.ndarray] = []
    glyph_dominated_count = 0
    for label in range(1, count):
        left = int(stats[label, cv2.CC_STAT_LEFT])
        top = int(stats[label, cv2.CC_STAT_TOP])
        span_x = int(stats[label, cv2.CC_STAT_WIDTH])
        span_y = int(stats[label, cv2.CC_STAT_HEIGHT])
        area = int(stats[label, cv2.CC_STAT_AREA])
        crosses = (
            (left <= x and left + span_x >= x + width)
            or (top <= y and top + span_y >= y + height)
        )
        if area < minimum_span or not crosses or max(span_x, span_y) < minimum_span:
            continue
        ys, xs = np.where(labels == label)
        if xs.size < minimum_span:
            continue
        local_authorized = authorized[ys, xs] > 0
        if not np.any(local_authorized):
            continue
        # The glyph's own Canny contour runs 1-2 px outside the removable mask;
        # only edge pixels beyond that band are evidence of something else.
        outside_count = int(xs.size - np.count_nonzero(contour_band[ys, xs]))
        outside_mask_count = int(xs.size - np.count_nonzero(local_authorized))
        # Text contours can join across a word after the small edge-closing
        # operation. Require the same edge component to continue materially
        # outside the removable pixels before treating it as crossing artwork.
        if outside_count < max(12, int(np.ceil(xs.size * 0.15))):
            glyph_dominated_count += 1
            continue
        # A curve's Canny trace is ~2 px per unit of span; halftone or hatching
        # merged with the glyph contours is a dense network, not a crossing line.
        if outside_mask_count > 5 * max(span_x, span_y):
            glyph_dominated_count += 1
            continue
        points = np.column_stack((xs, ys)).astype(np.float32)
        vx, vy, x0, y0 = [float(value) for value in cv2.fitLine(
            points, cv2.DIST_L2, 0, 0.01, 0.01).reshape(-1)]
        residual = np.abs((xs - x0) * vy - (ys - y0) * vx)
        # Canny outlines of a straight stroke remain close to its fitted axis;
        # the high quantile requires visible bending instead of a stray edge.
        if float(np.percentile(residual, 90)) <= max(1.5, min(width, height) * 0.035):
            continue
        component = np.zeros(gray.shape, np.uint8)
        component[ys, xs] = 255
        curves.append(component)
    return curves, glyph_dominated_count


def detect_linear_boundary_conflict(
    source_bgr: np.ndarray, authorized_text_mask: np.ndarray,
    regions: list[tuple[int, int, int, int]],
) -> dict[str, Any]:
    """Find line-like or curved structures intersecting removable glyph pixels.

    This is deliberately a conflict detector, not an art classifier. A stroke
    may be lettering, line art, or both; intersecting structures block cleanup
    and require boundary review. A negative result means only that this bounded
    detector found no crossing candidate; it is not proof of general art safety.
    Detection never expands the authorized mask.
    """
    image = np.asarray(source_bgr)
    authorized = (np.asarray(authorized_text_mask) > 0).astype(np.uint8) * 255
    if (image.ndim != 3 or image.shape[2] != 3
            or image.shape[:2] != authorized.shape):
        raise ValueError("boundary_conflict_shape_mismatch")

    gray_full = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    exclude = cv2.dilate(authorized, np.ones((5, 5), np.uint8))
    structure = np.zeros(authorized.shape, np.uint8)
    segments: list[tuple[int, int, int, int]] = []
    segment_count = 0
    curved_count = 0
    glyph_dominated_curve_count = 0
    for box in regions:
        try:
            x, y, width, height = (int(value) for value in box)
        except (TypeError, ValueError):
            continue
        if width <= 0 or height <= 0:
            continue
        margin_x = max(3, int(round(width * 0.12)))
        margin_y = max(3, int(round(height * 0.12)))
        x0, y0 = max(0, x - margin_x), max(0, y - margin_y)
        x1 = min(image.shape[1], x + width + margin_x)
        y1 = min(image.shape[0], y + height + margin_y)
        if x1 - x0 < 8 or y1 - y0 < 8:
            continue
        roi = cv2.cvtColor(image[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
        roi_width, roi_height = roi.shape[1], roi.shape[0]
        minimum_length = max(
            12, int(round(min(width * 0.60, height * 1.50))))
        _threshold_value, binary = cv2.threshold(
            roi, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        # Otsu's selected polarity can invert on light lettering or dark regions.
        dark_polarity = float(np.median(roi)) >= 127.0
        polarity = binary if dark_polarity else cv2.bitwise_not(binary)
        sources = (polarity,)
        for evidence in sources:
            lines = cv2.HoughLinesP(
                evidence, 1, np.pi / 180,
                threshold=max(8, int(round(minimum_length * 0.08))),
                minLineLength=minimum_length,
                maxLineGap=max(2, min(6, int(round(roi_height * 0.08)))),
            )
            for raw in hough_segments(lines):
                ax, ay, bx, by = (int(value) for value in raw)
                if np.hypot(bx - ax, by - ay) < minimum_length:
                    continue
                ax_global, bx_global = ax + x0, bx + x0
                ay_global, by_global = ay + y0, by + y0
                crosses_box = (
                    (ax_global < x and bx_global > x + width)
                    or (bx_global < x and ax_global > x + width)
                    or (ay_global < y and by_global > y + height)
                    or (by_global < y and ay_global > y + height)
                )
                spans_box = (
                    (abs(bx - ax) >= width * 0.65
                     and abs(by - ay) <= max(2, height * 0.12))
                    or (abs(by - ay) >= height * 0.65
                        and abs(bx - ax) <= max(2, width * 0.12))
                ) and np.hypot(bx - ax, by - ay) >= 1.5 * height
                # ^ a single glyph stroke ("!", "I", "l") is never much longer than
                # the line height; only a longer contained segment is art-like.
                # A diagonal clipping a corner, or a hair tip ending inside the
                # box, has one end outside and still runs through the box.
                def inside(px: int, py: int) -> bool:
                    return x <= px <= x + width and y <= py <= y + height
                enters_box = inside(ax_global, ay_global) != inside(bx_global, by_global)
                if not (crosses_box or spans_box or enters_box):
                    continue
                if crosses_box or enters_box:
                    # A glyph stroke ("I", "l") pokes a few pixels past a tight OCR
                    # box; art crossing the lettering runs well beyond it.
                    steps = max(2, int(np.hypot(bx_global - ax_global, by_global - ay_global)))
                    t = np.linspace(0.0, 1.0, steps)
                    outside = sum(
                        not inside(int(round(ax_global + f * (bx_global - ax_global))),
                                   int(round(ay_global + f * (by_global - ay_global))))
                        for f in t)
                    if outside < max(4, 0.4 * min(width, height)) and not spans_box:
                        continue
                centerline = np.zeros((roi_height, roi_width), np.uint8)
                cv2.line(centerline, (ax, ay), (bx, by), 255, 1, cv2.LINE_8)
                if float(np.mean(evidence[centerline > 0] > 0)) < 0.85:
                    continue
                if spans_box and not (crosses_box or enters_box):
                    # A contained art line is continuous; the top or bottom of a row
                    # of letters is broken at least by the spaces between words.
                    steps = int(max(abs(bx - ax), abs(by - ay))) + 1
                    run_x = np.rint(np.linspace(ax, bx, steps)).astype(int)
                    run_y = np.rint(np.linspace(ay, by, steps)).astype(int)
                    on_line = evidence[run_y, run_x] > 0
                    gaps = np.diff(np.flatnonzero(np.r_[True, on_line, True])) - 1
                    if gaps.size and int(gaps.max()) > max(2, int(round(0.25 * height))):
                        continue
                ridge = _outside_ridge_fraction(
                    gray_full, exclude,
                    (ax_global, ay_global, bx_global, by_global), dark_polarity)
                if ridge is not None and ridge < 0.6:
                    continue
                segment = np.zeros((roi_height, roi_width), np.uint8)
                cv2.line(segment, (ax, ay), (bx, by), 255, 2, cv2.LINE_8)
                destination = structure[y0:y1, x0:x1]
                destination[:] = cv2.bitwise_or(destination, segment)
                segments.append((ax_global, ay_global, bx_global, by_global))
                segment_count += 1
            vertical_length = max(12, int(round(height * 0.65)))
            if vertical_length >= minimum_length:
                continue
            vertical_margin = max(margin_y, int(round(height * 0.40)))
            vertical_y0 = max(0, y - vertical_margin)
            vertical_y1 = min(image.shape[0], y + height + vertical_margin)
            vertical_roi = cv2.cvtColor(
                image[vertical_y0:vertical_y1, x0:x1], cv2.COLOR_BGR2GRAY)
            _vertical_threshold, vertical_binary = cv2.threshold(
                vertical_roi, 0, 255,
                cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
            vertical_evidence = (
                vertical_binary if float(np.median(vertical_roi)) >= 127.0
                else cv2.bitwise_not(vertical_binary))
            vertical_lines = cv2.HoughLinesP(
                vertical_evidence, 1, np.pi / 180,
                threshold=max(8, int(round(vertical_length * 0.08))),
                minLineLength=vertical_length,
                maxLineGap=max(2, min(6, int(round(vertical_roi.shape[0] * 0.08)))),
            )
            vertical_segments = hough_segments(vertical_lines)
            if not len(vertical_segments):
                continue
            vertical_candidates: list[tuple[float, int, int]] = []
            for raw_vertical in vertical_segments:
                ax, ay, bx, by = (int(value) for value in raw_vertical)
                if (abs(by - ay) < vertical_length
                        or abs(bx - ax) > max(2, int(round(width * 0.12)))):
                    continue
                centerline = np.zeros(vertical_roi.shape, np.uint8)
                cv2.line(centerline, (ax, ay), (bx, by), 255, 1, cv2.LINE_8)
                if float(np.mean(vertical_evidence[centerline > 0] > 0)) < 0.85:
                    continue
                vertical_candidates.append((
                    float((ax + bx) / 2.0 + x0),
                    min(ay, by) + vertical_y0, max(ay, by) + vertical_y0))
            merged_verticals: list[list[float]] = []
            for center_x, top_y, bottom_y in sorted(
                    vertical_candidates, key=lambda item: item[1]):
                match = next((item for item in merged_verticals
                              if abs(center_x - item[0])
                              <= max(3.0, width * 0.03)
                              and top_y <= item[2] + vertical_length * 0.50), None)
                if match is None:
                    merged_verticals.append([center_x, float(top_y), float(bottom_y)])
                else:
                    match[0] = (match[0] + center_x) / 2.0
                    match[1] = min(match[1], float(top_y))
                    match[2] = max(match[2], float(bottom_y))
            for center_x, top_y, bottom_y in merged_verticals:
                if not (top_y < y and bottom_y > y + height):
                    continue
                ridge = _outside_ridge_fraction(
                    gray_full, exclude,
                    (int(round(center_x)), int(top_y), int(round(center_x)), int(bottom_y)),
                    dark_polarity)
                # Vertical stems of letters in successive rows ("I" over the stem of
                # "D") merge into one long run here but never leave the lettering;
                # an art line is seen outside it.
                if ridge is None or ridge < 0.6:
                    continue
                cv2.line(
                    structure,
                    (int(round(center_x)), int(round(top_y))),
                    (int(round(center_x)), int(round(bottom_y))),
                    255, 2, cv2.LINE_8)
                segments.append((int(round(center_x)), int(top_y),
                                 int(round(center_x)), int(bottom_y)))
                segment_count += 1

        local_authorized = authorized[y0:y1, x0:x1]
        curve_components, rejected_glyph_components = _curved_crossing_components(
            roi, local_authorized, (x - x0, y - y0, width, height),
        )
        glyph_dominated_curve_count += rejected_glyph_components
        for component in curve_components:
            # Widen only the evidence map by one pixel for Canny edge placement;
            # the authorized cleanup mask itself is never changed.
            expanded = cv2.dilate(component, np.ones((3, 3), np.uint8), iterations=1)
            destination = structure[y0:y1, x0:x1]
            destination[:] = cv2.bitwise_or(destination, expanded)
            curved_count += 1

    overlap = cv2.bitwise_and(structure, authorized)
    conflict_pixels = int(np.count_nonzero(overlap))
    return {
        "status": "review_required" if conflict_pixels else "no_conflict_detected",
        "reason_codes": (["GLYPH_ART_BOUNDARY_UNCERTAIN"]
                         if conflict_pixels else []),
        "candidate_segment_count": segment_count,
        "candidate_segments": segments,
        "candidate_curved_segment_count": curved_count,
        "excluded_glyph_dominated_curve_count": glyph_dominated_curve_count,
        "candidate_line_mask": structure,
        "conflict_mask": overlap,
        "candidate_line_mask_hash": bitmap_hash(structure),
        "conflict_pixel_count": conflict_pixels,
        "method": BOUNDARY_DETECTOR_METHOD,
        "scope": "linear_and_curved_crossing_evidence_only_not_general_art_safety",
    }


def build_conflict_artifact(
    conflict_bitmap: np.ndarray, *, identity: dict[str, str],
    glyph_envelope_id: str, protected_art_hash: str,
    previous_mask_hash: str,
) -> dict[str, Any]:
    mask = (np.asarray(conflict_bitmap) > 0).astype(np.uint8) * 255
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(
        (mask > 0).astype(np.uint8), 8)
    segments = []
    for label in range(1, count):
        component = (labels == label).astype(np.uint8) * 255
        x, y, w, h, pixels = [int(value) for value in stats[label]]
        contour_data = cv2.findContours(
            component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        contour_bytes = b"".join(
            np.asarray(contour, np.int32).tobytes() for contour in contour_data)
        segment_payload = {
            "segment_bitmap_hash": bitmap_hash(component),
            "bounds": [x, y, x + w, y + h],
            "pixel_count": pixels,
            "centroid": [
                round(float(centroids[label][0]), 4),
                round(float(centroids[label][1]), 4),
            ],
            "contour_hash": hashlib.sha256(contour_bytes).hexdigest(),
            "suggested_classification": "uncertain",
            "suggested_confidence": 0.0,
            "reason_codes": ["glyph_art_evidence_conflict"],
        }
        segments.append({
            **segment_payload,
            "segment_id": _digest(segment_payload),
        })
    segments.sort(key=lambda item: item["segment_id"])
    manifest_hash = _digest([
        item["segment_id"] for item in segments])
    payload = {
        "schema_version": SCHEMA_VERSION,
        "identity": {str(k): str(v) for k, v in identity.items()},
        "glyph_envelope_id": str(glyph_envelope_id),
        "protected_art_hash": str(protected_art_hash),
        "previous_mask_hash": str(previous_mask_hash),
        "conflict_bitmap_hash": bitmap_hash(mask),
        "conflict_pixel_count": int((mask > 0).sum()),
        "component_manifest_hash": manifest_hash,
        "segment_manifest_hash": manifest_hash,
        "status": "pending_human_boundary_review",
    }
    return {
        **payload,
        "conflict_artifact_id": _digest(payload),
        "segments": segments,
        "conflict_bitmap": mask,
    }


def normalize_review_draft(
    *, conflict_artifact_id: str, owner: str,
    segment_decisions: dict[str, str] | None = None,
    brush_operations: list[dict[str, Any]] | None = None,
    segment_operations: list[dict[str, Any]] | None = None,
    view_state: dict[str, Any] | None = None,
    confirm: bool = False,
) -> dict[str, Any]:
    decisions = {
        str(segment): str(classification)
        for segment, classification in (segment_decisions or {}).items()}
    if any(value not in CLASSIFICATIONS for value in decisions.values()):
        raise ValueError("boundary_review_classification_invalid")
    operations = list(brush_operations or [])
    segment_ops = list(segment_operations or [])
    uncertain = sum(1 for value in decisions.values() if value == "uncertain")
    unresolved = sum(1 for value in decisions.values() if not value)
    if confirm and (uncertain or unresolved or not decisions):
        raise ValueError("boundary_review_uncertainty_remaining")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "owner": str(owner),
        "conflict_artifact_id": str(conflict_artifact_id),
        "segment_decisions": dict(sorted(decisions.items())),
        "brush_operations": operations,
        "segment_operations": segment_ops,
        "view_state": dict(view_state or {}),
        "status": "confirmed" if confirm else (
            "blocked_with_uncertainty" if uncertain else "draft"),
    }
    return {
        **payload,
        "decision_payload_hash": _digest(payload),
        "review_decision_id": _digest({
            "owner": owner,
            "conflict_artifact_id": conflict_artifact_id,
            "payload": payload,
        }),
    }
