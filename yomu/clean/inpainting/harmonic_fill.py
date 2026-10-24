"""Experimental Dirichlet harmonic fill for locally smooth manga backgrounds.

This module only proposes pixels inside an authorized mask. Its status is a
conservative acceptance gate, not a claim that originally occluded artwork was
recovered. Structural, textured, contaminated, or under-specified boundaries
remain review items.
"""
from __future__ import annotations

import time
from typing import Any

import cv2
import numpy as np

from yomu.clean.ownership.glyph_art_boundary_review import hough_segments


_SAFE_BACKGROUND_CLASSES = frozenset({"uniform", "smooth_gradient"})
_SPATIAL_TO_HARMONIC_CLASS = {
    "PROVEN_UNIFORM": "uniform",
    "SMOOTH_NONUNIFORM": "smooth_gradient",
    "STRUCTURED_OR_TEXTURED": "complex",
    "INSUFFICIENT_EVIDENCE": "unknown",
}
_POLARITIES = frozenset({
    "dark_text_on_light_bg", "light_text_on_dark_bg", "mixed_unknown", "unknown",
})


def convert_spatial_background_class(spatial_class: str) -> dict[str, str]:
    """Map the production spatial class to the solver contract, without approval."""
    original = str(spatial_class or "").strip().upper()
    if original not in _SPATIAL_TO_HARMONIC_CLASS:
        raise ValueError("harmonic_spatial_background_class_invalid")
    converted = _SPATIAL_TO_HARMONIC_CLASS[original]
    reason = {
        "PROVEN_UNIFORM": "uniform_spatial_evidence_maps_to_uniform_candidate",
        "SMOOTH_NONUNIFORM": "smooth_spatial_evidence_maps_to_gradient_candidate",
        "STRUCTURED_OR_TEXTURED": "structured_art_maps_conservatively_to_complex",
        "INSUFFICIENT_EVIDENCE": "insufficient_spatial_evidence_maps_to_unknown",
    }[original]
    return {
        "source": "local_background_spatial_class",
        "original_class": original,
        "converted_class": converted,
        "decision_reason": reason,
        "conversion_approves_reconstruction": "false",
    }


def _diagnose_soft_crossing_edge(gray: np.ndarray, target: np.ndarray) -> dict[str, Any]:
    """Shadow-only detector for low-contrast axis-aligned edges crossing a mask.

    It records paired Sobel support at opposite mask sides. It does not influence
    the solver status; the 6-level floor and four-times-noise threshold are
    diagnostic hypotheses, not calibrated safety limits.
    """
    target = np.asarray(target, dtype=bool)
    if not target.any():
        return {"candidate": False, "decision_impact": False, "reason": "empty_mask"}
    gray_f = np.asarray(gray, dtype=np.float32)
    gx = cv2.Sobel(gray_f, cv2.CV_32F, 1, 0, ksize=3) / 8.0
    gy = cv2.Sobel(gray_f, cv2.CV_32F, 0, 1, ksize=3) / 8.0
    distance = cv2.distanceTransform((~target).astype(np.uint8), cv2.DIST_L2, 3)
    reference = (~target) & (distance >= 3.0) & (distance <= 8.0)
    laplacian = cv2.Laplacian(gray_f, cv2.CV_32F, ksize=3)
    residual = laplacian[reference]
    center = float(np.median(residual)) if residual.size else 0.0
    noise_sigma = float(1.4826 * np.median(np.abs(residual - center)) / 8.0) if residual.size else 0.0
    threshold = max(6.0, 4.0 * noise_sigma)
    height, width = target.shape
    component_count, labels, stats, _ = cv2.connectedComponentsWithStats(
        target.astype(np.uint8), 8,
    )
    evidence = []
    for component_id in range(1, component_count):
        x0, y0, box_w, box_h, _area = (int(value) for value in stats[component_id])
        x1, y1 = x0 + box_w - 1, y0 + box_h - 1
        rows = np.arange(y0, y1 + 1)
        cols = np.arange(x0, x1 + 1)
        orientations = []
        # Horizontal strokes have vertical gradients at opposite mask sides.
        if x0 >= 4 and x1 + 4 < width:
            left = np.median(gy[rows[:, None], np.array([x0 - 4, x0 - 3])], axis=1)
            right = np.median(gy[rows[:, None], np.array([x1 + 3, x1 + 4])], axis=1)
            paired = (np.abs(left) >= threshold) & (np.abs(right) >= threshold) & (left * right > 0)
            orientations.append({"orientation": "horizontal", "paired_bins": int(paired.sum()),
                                 "peak_gradient": float(max(np.max(np.abs(left), initial=0.0),
                                                             np.max(np.abs(right), initial=0.0)))})
        # Vertical strokes have horizontal gradients above and below the mask.
        if y0 >= 4 and y1 + 4 < height:
            top = np.median(gx[np.array([y0 - 4, y0 - 3])[:, None], cols], axis=0)
            bottom = np.median(gx[np.array([y1 + 3, y1 + 4])[:, None], cols], axis=0)
            paired = (np.abs(top) >= threshold) & (np.abs(bottom) >= threshold) & (top * bottom > 0)
            orientations.append({"orientation": "vertical", "paired_bins": int(paired.sum()),
                                 "peak_gradient": float(max(np.max(np.abs(top), initial=0.0),
                                                             np.max(np.abs(bottom), initial=0.0)))})
        evidence.append({"component_id": component_id, "bbox_xyxy": [x0, y0, x1 + 1, y1 + 1],
                         "orientations": orientations,
                         "candidate": any(row["paired_bins"] >= 2 for row in orientations)})
    candidate = any(row["candidate"] for row in evidence)
    return {
        "candidate": bool(candidate), "decision_impact": False,
        "reason": "paired_low_contrast_sobel_support" if candidate else "no_paired_support",
        "noise_sigma_estimate": round(noise_sigma, 4),
        "gradient_threshold": round(threshold, 4),
        "threshold_hypothesis": "max(6, 4 * sigma_noise)",
        "components": evidence,
    }


def classify_boundary_evidence(
    gray: np.ndarray,
    target: np.ndarray,
    boundary_ring: np.ndarray,
    reference_ring: np.ndarray,
    auto_suspect: np.ndarray,
    caller_suspect: np.ndarray,
    *,
    polarity_cut: float,
    confirmed_lettering: np.ndarray | None = None,
    structural_conflict: bool = False,
) -> dict[str, Any]:
    """Classify boundary evidence without treating a color outlier as text.

    The only benign override is deliberately narrow: automatically detected,
    small and sparse components must also have matching low-luminance variation
    in a farther reference ring. Caller evidence is never downgraded by image
    statistics. These experimental thresholds are conservative controls for the
    isolated harmonic solver, not universal lettering thresholds.
    """
    gray = np.asarray(gray)
    target = np.asarray(target, dtype=bool)
    boundary_ring = np.asarray(boundary_ring, dtype=bool)
    reference_ring = np.asarray(reference_ring, dtype=bool)
    auto_suspect = np.asarray(auto_suspect, dtype=bool)
    caller_suspect = np.asarray(caller_suspect, dtype=bool)
    confirmed = (np.zeros(target.shape, dtype=bool) if confirmed_lettering is None
                 else np.asarray(confirmed_lettering, dtype=bool))
    if not (gray.shape == target.shape == boundary_ring.shape == reference_ring.shape
            == auto_suspect.shape == caller_suspect.shape == confirmed.shape):
        raise ValueError("harmonic_boundary_evidence_shape_mismatch")

    boundary_values = gray[boundary_ring]
    reference_values = gray[reference_ring]
    reference_threshold = (
        float(np.median(boundary_values)) - max(12.0, float(polarity_cut) * 0.5)
        if boundary_values.size else 0.0
    )
    reference_support = (
        float(np.mean(reference_values <= reference_threshold))
        if reference_values.size else 0.0
    )
    reference_std = float(np.std(reference_values.astype(np.float32))) if reference_values.size else 0.0
    boundary_std = float(np.std(boundary_values.astype(np.float32))) if boundary_values.size else 0.0
    labels_count, labels, stats, _ = cv2.connectedComponentsWithStats(
        auto_suspect.astype(np.uint8), 8,
    )
    component_rows: list[dict[str, Any]] = []
    auto_sizes: list[int] = []
    for label in range(1, labels_count):
        component = labels == label
        size = int(stats[label, cv2.CC_STAT_AREA])
        auto_sizes.append(size)
        component_rows.append({
            "component_id": int(label), "origin": "automatic_polarity_outlier",
            "category": "UNCERTAIN_BOUNDARY", "pixels": size,
            "contour_coverage": size / max(1, int(np.count_nonzero(boundary_ring))),
            "reference_support_fraction": reference_support,
        })

    coverage = int(np.count_nonzero(auto_suspect)) / max(1, int(np.count_nonzero(boundary_ring)))
    background_supported = bool(
        auto_suspect.any()
        and not caller_suspect.any()
        and max(auto_sizes, default=0) <= 10
        and coverage <= 0.02
        and reference_support >= 0.05
        and reference_std >= 0.75 * boundary_std
    )
    if background_supported:
        for row in component_rows:
            row["category"] = "BENIGN_BACKGROUND_VARIATION"
            row["evidence"] = "sparse_small_auto_components_with_persistent_far_band_variation"
    if caller_suspect.any():
        component_rows.append({
            "component_id": None, "origin": "caller_supplied",
            "category": "UNCERTAIN_BOUNDARY", "pixels": int(caller_suspect.sum()),
            "contour_coverage": int(caller_suspect.sum()) / max(1, int(boundary_ring.sum())),
            "evidence": "caller_suspicions_are_never_downgraded_by_color_statistics",
        })
    if confirmed.any():
        component_rows.append({
            "component_id": None, "origin": "explicit_labeled_reference",
            "category": "CONFIRMED_LETTERING_FRINGE", "pixels": int(confirmed.sum()),
            "contour_coverage": int(confirmed.sum()) / max(1, int(boundary_ring.sum())),
            "evidence": "explicit_labeled_reference_only",
        })

    overall_category = (
        "STRUCTURAL_ART_CONFLICT" if structural_conflict
        else "CONFIRMED_LETTERING_FRINGE" if confirmed.any()
        else "UNCERTAIN_BOUNDARY" if caller_suspect.any()
        else "BENIGN_BACKGROUND_VARIATION" if background_supported
        else "UNCERTAIN_BOUNDARY" if auto_suspect.any() else None
    )

    return {
        "components": component_rows,
        "overall_category": overall_category,
        "automatic_category": (
            "BENIGN_BACKGROUND_VARIATION" if background_supported
            else "UNCERTAIN_BOUNDARY" if auto_suspect.any() else None
        ),
        "caller_category": "UNCERTAIN_BOUNDARY" if caller_suspect.any() else None,
        "automatic_pixels": int(auto_suspect.sum()),
        "caller_pixels": int(caller_suspect.sum()),
        "automatic_contour_coverage": coverage,
        "reference_band": {"pixels": int(reference_values.size),
                           "low_polarity_support_fraction": reference_support,
                           "std_gray": reference_std},
        "boundary_band": {"pixels": int(boundary_values.size), "std_gray": boundary_std},
        "benign_evidence": background_supported,
        "experimental_thresholds": {
            "max_component_pixels": 10, "max_contour_coverage": 0.02,
            "min_far_band_support_fraction": 0.05,
            "min_far_to_near_std_ratio": 0.75,
        },
    }


def _has_crossing_boundary_structure(gray: np.ndarray, target: np.ndarray) -> bool:
    """Detect aligned gradient evidence on opposite sides of masked spans.

    Paired gradients are required so an isolated nearby parallel edge is not
    treated as a crossing. Directional scans include soft, ~25-level edges the
    legacy Canny gate misses, without lowering a global edge threshold.
    """
    target = np.asarray(target, dtype=bool)
    if not target.any():
        return False
    gx = cv2.Sobel(gray.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3) / 8.0
    gy = cv2.Sobel(gray.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3) / 8.0
    if _has_collinear_edge_bridge(gray, target):
        return True
    ys, xs = np.where(target)
    height, width = target.shape
    for angle in np.deg2rad(np.arange(0, 180, 15, dtype=np.float32)):
        along_x, along_y = float(np.cos(angle)), float(np.sin(angle))
        normal_x, normal_y = -along_y, along_x
        along = xs * along_x + ys * along_y
        across = np.rint(xs * normal_x + ys * normal_y).astype(np.int32)
        paired_bins = 0
        for band in np.unique(across):
            selected = across == band
            span = along[selected]
            if span.size < 3 or float(np.ptp(span)) < 4.0:
                continue
            start_s, end_s = float(span.min() - 2.0), float(span.max() + 2.0)
            center_x = float(band) * normal_x
            center_y = float(band) * normal_y
            points = (
                (int(round(center_x + start_s * along_x)),
                 int(round(center_y + start_s * along_y))),
                (int(round(center_x + end_s * along_x)),
                 int(round(center_y + end_s * along_y))),
            )
            (x0, y0), (x1, y1) = points
            if not (0 <= x0 < width and 0 <= y0 < height
                    and 0 <= x1 < width and 0 <= y1 < height):
                continue
            first_gx, first_gy = float(gx[y0, x0]), float(gy[y0, x0])
            second_gx, second_gy = float(gx[y1, x1]), float(gy[y1, x1])
            first = first_gx * normal_x + first_gy * normal_y
            second = second_gx * normal_x + second_gy * normal_y
            first_mag = float(np.hypot(first_gx, first_gy))
            second_mag = float(np.hypot(second_gx, second_gy))
            if (abs(first) >= 8.0 and abs(second) >= 8.0
                    and abs(first) >= 0.85 * first_mag
                    and abs(second) >= 0.85 * second_mag
                    and first * second > 0):
                paired_bins += 1
                if paired_bins >= 2:
                    return True
    return False


def _has_collinear_edge_bridge(gray: np.ndarray, target: np.ndarray) -> bool:
    """Find two visible, aligned edge segments whose gap crosses the mask."""
    edges = cv2.Canny(gray, 8, 24)
    # Ignore the target and its immediate raster boundary; only visible support
    # beyond the hole can establish a bridge.
    excluded = cv2.dilate(np.asarray(target, dtype=np.uint8), np.ones((3, 3), np.uint8)) > 0
    edges[excluded] = 0
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180.0, threshold=7,
        minLineLength=8, maxLineGap=3,
    )
    segments = []
    for raw in hough_segments(lines):
        x0, y0, x1, y1 = (int(v) for v in raw)
        dx, dy = x1 - x0, y1 - y0
        length = float(np.hypot(dx, dy))
        if length < 8.0:
            continue
        angle = float(np.arctan2(dy, dx))
        vx, vy = np.cos(angle), np.sin(angle)
        nx, ny = -vy, vx
        s0, s1 = x0 * vx + y0 * vy, x1 * vx + y1 * vy
        c = ((x0 + x1) * nx + (y0 + y1) * ny) * 0.5
        segments.append((angle, min(s0, s1), max(s0, s1), c))
    ty, tx = np.where(target)
    for index, first in enumerate(segments):
        a0, s0_min, s0_max, c0 = first
        vx, vy = np.cos(a0), np.sin(a0)
        nx, ny = -vy, vx
        target_s = tx * vx + ty * vy
        target_c = tx * nx + ty * ny
        hole_s_min, hole_s_max = float(target_s.min()), float(target_s.max())
        hole_c_min, hole_c_max = float(target_c.min()), float(target_c.max())
        if not (hole_c_min - 2.0 <= c0 <= hole_c_max + 2.0):
            continue
        for second in segments[index + 1:]:
            a1, s1_min, s1_max, c1 = second
            delta = abs(a0 - a1) % np.pi
            if min(delta, np.pi - delta) > np.deg2rad(8.0):
                continue
            if abs(c0 - c1) > 3.0:
                continue
            if ((s0_max < hole_s_min and s1_min > hole_s_max)
                    or (s1_max < hole_s_min and s0_min > hole_s_max)):
                return True
    return False


def _has_unresolved_edge_structure(edge_band: np.ndarray, target: np.ndarray) -> bool:
    """Keep Canny edges in review unless each is an isolated parallel neighbor."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        np.asarray(edge_band, dtype=np.uint8), 8,
    )
    if count <= 1:
        return False
    ys_target, xs_target = np.where(target)
    min_x, max_x = int(xs_target.min()), int(xs_target.max())
    min_y, max_y = int(ys_target.min()), int(ys_target.max())
    for label in range(1, count):
        if stats[label, cv2.CC_STAT_AREA] < 2:
            continue
        ys, xs = np.where(labels == label)
        if xs.max() < min_x:
            expected_angle = 90.0
        elif xs.min() > max_x:
            expected_angle = 90.0
        elif ys.max() < min_y or ys.min() > max_y:
            expected_angle = 0.0
        else:
            return True
        points = np.column_stack((xs, ys)).astype(np.float32)
        covariance = np.cov(points, rowvar=False) if len(points) > 1 else np.zeros((2, 2))
        eigenvalues, eigenvectors = np.linalg.eigh(covariance)
        direction = eigenvectors[:, int(np.argmax(eigenvalues))]
        angle = abs(float(np.degrees(np.arctan2(direction[1], direction[0])))) % 180.0
        delta = abs(angle - expected_angle)
        if min(delta, 180.0 - delta) > 15.0:
            return True
    return False


def harmonic_boundary_fill(
    image_bgr: np.ndarray,
    authorized_mask: np.ndarray,
    *,
    background_class: str = "unknown",
    spatial_class: str | None = None,
    polarity: str = "unknown",
    protected_art_mask: np.ndarray | None = None,
    possible_contamination_mask: np.ndarray | None = None,
    tolerance: float = 0.05,
    max_iterations: int = 3000,
    relaxation: float = 1.7,
    contamination_band_px: int = 12,
) -> dict[str, Any]:
    """Solve ``laplacian(u) = 0`` around a hole with fixed Dirichlet pixels.

    A red-black SOR stencil is run on a compact ROI containing the authorized
    mask and nearby suspected source lettering. Suspected exterior pixels are
    treated as unknown while solving, but are never copied to the output. The
    returned image can differ from the input only inside ``authorized_mask``;
    protected pixels are copied byte-for-byte. ``status`` is ``accepted`` only
    for a converged smooth/uniform region with an uncontaminated, non-structural
    boundary and no protected overlap. Other finite candidates are diagnostics
    only and must not be shipped as CLEAN.

    ``possible_contamination_mask`` and automatic polarity outliers are only
    suspicions. They are not semantic lettering labels and never expand the
    authorized write mask.
    """
    started = time.perf_counter()
    if spatial_class is not None:
        class_metadata = convert_spatial_background_class(spatial_class)
        background_class = class_metadata["converted_class"]
    else:
        class_metadata = {
            "source": "direct_solver_argument",
            "original_class": str(background_class),
            "converted_class": str(background_class),
            "decision_reason": "legacy_explicit_class_argument",
            "conversion_approves_reconstruction": "false",
        }
    image = np.asarray(image_bgr)
    mask_input = np.asarray(authorized_mask)
    if image.ndim != 3 or image.shape[2] != 3 or image.dtype != np.uint8:
        raise ValueError("harmonic_image_must_be_uint8_bgr")
    if mask_input.shape != image.shape[:2]:
        raise ValueError("harmonic_authorized_mask_shape_mismatch")
    if not np.isfinite(float(tolerance)) or float(tolerance) <= 0:
        raise ValueError("harmonic_tolerance_must_be_positive")
    if int(max_iterations) < 1:
        raise ValueError("harmonic_max_iterations_must_be_positive")
    if not 1.0 <= float(relaxation) < 2.0:
        raise ValueError("harmonic_relaxation_out_of_range")
    if int(contamination_band_px) < 1:
        raise ValueError("harmonic_contamination_band_must_be_positive")
    if background_class not in {
        "uniform", "smooth_gradient", "repetitive_texture", "line_art",
        "complex", "unknown",
    }:
        raise ValueError("harmonic_background_class_invalid")
    if polarity not in _POLARITIES:
        raise ValueError("harmonic_polarity_invalid")

    target = mask_input > 0
    protected = np.zeros(target.shape, dtype=bool)
    if protected_art_mask is not None:
        protected_input = np.asarray(protected_art_mask)
        if protected_input.shape != target.shape:
            raise ValueError("harmonic_protected_mask_shape_mismatch")
        protected = protected_input > 0
    possible_contamination = np.zeros(target.shape, dtype=bool)
    contamination_was_supplied = possible_contamination_mask is not None
    if contamination_was_supplied:
        contamination_input = np.asarray(possible_contamination_mask)
        if contamination_input.shape != target.shape:
            raise ValueError("harmonic_contamination_mask_shape_mismatch")
        possible_contamination = contamination_input > 0

    candidate = image.copy()
    h, w = target.shape
    target_y, target_x = np.where(target)
    if target_y.size == 0:
        return {
            "candidate_bgr": candidate,
            "status": "no_op",
            "accepted": False,
            "converged": True,
            "iterations": 0,
            "residual_linf": 0.0,
            "authorized_pixels": 0,
            "changed_pixels_outside_authorized_mask": 0,
            "protected_pixels_changed": 0,
            "rejection_reasons": ["empty_authorized_mask"],
            "classification": class_metadata,
            "soft_edge_diagnostic": {"candidate": False, "decision_impact": False,
                                      "reason": "empty_mask"},
            "runtime_ms": (time.perf_counter() - started) * 1000.0,
        }

    if (target_y.min() == 0 or target_x.min() == 0
            or target_y.max() == h - 1 or target_x.max() == w - 1):
        return _rejected_result(
            candidate, image, started, target, protected, 0,
            "mask_touches_image_border", classification=class_metadata,
        )

    # Include an explicit safety collar around the write mask. The extra 1 px
    # is required for the 4-neighbour finite-difference stencil.
    padding = max(2, int(contamination_band_px) + 1)
    x0 = max(0, int(target_x.min()) - padding)
    x1 = min(w, int(target_x.max()) + padding + 1)
    y0 = max(0, int(target_y.min()) - padding)
    y1 = min(h, int(target_y.max()) + padding + 1)
    roi = np.s_[y0:y1, x0:x1]
    local_target = target[roi]
    local_protected = protected[roi]
    local_possible = possible_contamination[roi].copy()
    local_image = image[roi]
    kernel = np.ones((3, 3), dtype=np.uint8)
    target_halo = cv2.dilate(local_target.astype(np.uint8), kernel, iterations=1) > 0
    boundary_ring = target_halo & ~local_target

    # Estimate possible polarity-consistent fringe samples from robust boundary
    # statistics. Such pixels are excluded from the Dirichlet values and logged;
    # the detector cannot distinguish letter halo from nearby line art.
    gray = cv2.cvtColor(local_image, cv2.COLOR_BGR2GRAY)
    boundary_values = gray[boundary_ring]
    auto_suspect = np.zeros(local_target.shape, dtype=bool)
    median = float(np.median(boundary_values)) if boundary_values.size else 0.0
    mad = float(np.median(np.abs(boundary_values.astype(np.float32) - median))) if boundary_values.size else 0.0
    polarity_cut = max(24.0, 3.0 * 1.4826 * mad)
    if polarity == "dark_text_on_light_bg" and boundary_values.size:
        auto_suspect = boundary_ring & (gray.astype(np.float32) < median - polarity_cut)
    elif polarity == "light_text_on_dark_bg" and boundary_values.size:
        auto_suspect = boundary_ring & (gray.astype(np.float32) > median + polarity_cut)

    # The caller's supplied evidence may lie just beyond the immediate ring.
    # Retain only nearby samples in this compact domain; never dilate the write
    # mask or assign semantic text labels to these suspects.
    local_possible |= auto_suspect
    if np.any(local_target):
        distance_to_target = cv2.distanceTransform(
            (~local_target).astype(np.uint8), cv2.DIST_L2, 3)
    else:  # pragma: no cover - target is non-empty by construction
        distance_to_target = np.full(local_target.shape, np.inf, np.float32)
    caller_suspect = possible_contamination[roi] & ~local_target
    reference_ring = (
        ~local_target & ~local_protected
        & (distance_to_target >= 3.0) & (distance_to_target <= 8.0)
    )
    suspect_domain = (
        local_possible & ~local_target
        & (distance_to_target <= float(contamination_band_px))
    )
    solve_domain = (local_target & ~local_protected) | suspect_domain
    known_boundary = boundary_ring & ~local_possible & ~local_protected
    # Also use clean boundary samples immediately outside the computational
    # suspect band to close its outer edge with Dirichlet values.
    solve_halo = cv2.dilate(solve_domain.astype(np.uint8), kernel, iterations=1) > 0
    known_boundary |= solve_halo & ~solve_domain & ~local_possible & ~local_protected
    known_boundary &= ~solve_domain

    protected_overlap = int(np.count_nonzero(local_target & local_protected))
    boundary_edge_map = cv2.Canny(gray, 55, 155) > 0
    outer_structure_band = (
        cv2.dilate(
            solve_domain.astype(np.uint8),
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)),
            iterations=1,
        ) > 0
    ) & ~cv2.dilate(
        solve_domain.astype(np.uint8),
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
        iterations=1,
    ).astype(bool)
    boundary_edge_pixels = int(np.count_nonzero(boundary_edge_map & outer_structure_band))
    paired_crossing = _has_crossing_boundary_structure(gray, local_target)
    soft_edge_diagnostic = _diagnose_soft_crossing_edge(gray, local_target)
    unresolved_edge = _has_unresolved_edge_structure(
        boundary_edge_map & outer_structure_band, local_target,
    )
    structural_crossing = paired_crossing or unresolved_edge
    boundary_evidence = classify_boundary_evidence(
        gray, local_target, boundary_ring, reference_ring, auto_suspect,
        caller_suspect, polarity_cut=polarity_cut,
        structural_conflict=structural_crossing,
    )
    boundary_count = int(np.count_nonzero(known_boundary))
    trusted_values = local_image[known_boundary]
    if trusted_values.size:
        trusted_gray = cv2.cvtColor(
            trusted_values.reshape(-1, 1, 3), cv2.COLOR_BGR2GRAY
        ).reshape(-1)
        boundary_stats = {
            "sample_count": int(trusted_values.shape[0]),
            "median_bgr": [float(v) for v in np.median(trusted_values, axis=0)],
            "std_bgr": [float(v) for v in np.std(trusted_values.astype(np.float32), axis=0)],
            "luminance_p10_p50_p90": [
                float(v) for v in np.percentile(trusted_gray, [10, 50, 90])
            ],
            "edge_pixels": boundary_edge_pixels,
            "edge_fraction": boundary_edge_pixels / max(1, boundary_count),
        }
    else:
        boundary_stats = {
            "sample_count": 0, "median_bgr": None, "std_bgr": None,
            "luminance_p10_p50_p90": None, "edge_pixels": boundary_edge_pixels,
            "edge_fraction": 0.0,
        }

    reasons: list[str] = []
    if background_class not in _SAFE_BACKGROUND_CLASSES:
        reasons.append("background_class_not_harmonic_safe")
    if polarity in {"unknown", "mixed_unknown"}:
        reasons.append("text_polarity_unknown")
    if protected_overlap:
        reasons.append("protected_art_intersects_authorized_mask")
    if np.any(caller_suspect) or (
            np.any(auto_suspect) and not boundary_evidence["benign_evidence"]):
        reasons.append("possible_boundary_contamination_requires_review")
    if structural_crossing:
        reasons.append("structural_edge_touches_dirichlet_boundary")
    if boundary_count == 0:
        reasons.append("no_trusted_dirichlet_boundary")
        return _metadata_result(
            candidate, image, started, target, protected, False, 0, float("inf"),
            solve_domain, known_boundary, boundary_stats, reasons,
            contamination_was_supplied, int(np.count_nonzero(possible_contamination)),
            int(np.count_nonzero(suspect_domain)), (x0, y0, x1, y1),
            boundary_evidence=boundary_evidence,
            classification=class_metadata,
            soft_edge_diagnostic=soft_edge_diagnostic,
            structural_crossing=structural_crossing,
            structural_reason=("paired_opposite_side_gradients" if paired_crossing
                               else "edge_orientation_not_isolated_parallel" if unresolved_edge else None),
        )
    if not np.any(solve_domain):
        reasons.append("no_unprotected_target_pixels")
        return _metadata_result(
            candidate, image, started, target, protected, True, 0, 0.0,
            solve_domain, known_boundary, boundary_stats, reasons,
            contamination_was_supplied, int(np.count_nonzero(possible_contamination)),
            int(np.count_nonzero(suspect_domain)), (x0, y0, x1, y1),
            boundary_evidence=boundary_evidence,
            classification=class_metadata,
            soft_edge_diagnostic=soft_edge_diagnostic,
            structural_crossing=structural_crossing,
            structural_reason=("paired_opposite_side_gradients" if paired_crossing
                               else "edge_orientation_not_isolated_parallel" if unresolved_edge else None),
        )

    # Seed unknowns with the trusted boundary mean, then solve each channel
    # independently. Red-black ordering is deterministic and substantially
    # accelerates convergence over Jacobi for long OCR masks.
    field = local_image.astype(np.float64)
    seed = np.mean(trusted_values.astype(np.float64), axis=0)
    field[solve_domain] = seed
    yy, xx = np.indices(solve_domain.shape)
    checker = (yy + xx) & 1
    active_even = solve_domain & (checker == 0)
    active_odd = solve_domain & (checker == 1)
    residual_linf = float("inf")
    iterations = 0
    omega = float(relaxation)
    # 4-neighbour mean with edge replication (identical to np.pad(mode="edge")),
    # as one OpenCV filter over the whole ROI instead of padded copies and
    # boolean fancy indexing per sweep (~50 ms per iteration on a caption).
    # float32 in place; convergence is checked every 4th sweep (it can only stop
    # later, i.e. more converged, than a per-sweep check).
    cross = np.array([[0.0, 0.25, 0.0], [0.25, 0.0, 0.25], [0.0, 0.25, 0.0]], np.float32)
    field = field.astype(np.float32)
    even_weight = (omega * active_even.astype(np.float32))[..., None]
    odd_weight = (omega * active_odd.astype(np.float32))[..., None]
    domain_weight = solve_domain.astype(np.float32)[..., None]
    shape = field.shape

    def _neighbor_mean(values):
        return cv2.filter2D(values, -1, cross, borderType=cv2.BORDER_REPLICATE).reshape(shape)

    for iterations in range(1, int(max_iterations) + 1):
        delta = _neighbor_mean(field)
        delta -= field
        delta *= even_weight
        field += delta
        delta = _neighbor_mean(field)
        delta -= field
        delta *= odd_weight
        field += delta
        if iterations % 4 and iterations != int(max_iterations):
            continue
        delta = _neighbor_mean(field)
        delta -= field
        np.abs(delta, out=delta)
        delta *= domain_weight
        residual_linf = float(delta.max(initial=0.0))
        if residual_linf <= float(tolerance):
            break
    converged = residual_linf <= float(tolerance)

    local_candidate = candidate[roi]
    write_mask = local_target & ~local_protected
    local_candidate[write_mask] = np.clip(
        np.rint(field[write_mask]), 0, 255
    ).astype(np.uint8)
    candidate[roi] = local_candidate
    if not converged:
        reasons.append("solver_did_not_converge")
    accepted = converged and not reasons
    return _metadata_result(
        candidate, image, started, target, protected, converged, iterations,
        residual_linf, solve_domain, known_boundary, boundary_stats, reasons,
        contamination_was_supplied, int(np.count_nonzero(possible_contamination)),
        int(np.count_nonzero(suspect_domain)), (x0, y0, x1, y1), accepted=accepted,
        boundary_evidence=boundary_evidence,
        classification=class_metadata,
        soft_edge_diagnostic=soft_edge_diagnostic,
        structural_crossing=structural_crossing,
        structural_reason=("paired_opposite_side_gradients" if paired_crossing
                           else "edge_orientation_not_isolated_parallel" if unresolved_edge else None),
    )


def _rejected_result(candidate, source, started, target, protected, suspect_count, reason,
                     *, classification=None):
    return _metadata_result(
        candidate, source, started, target, protected, False, 0, float("inf"),
        np.zeros(target.shape, bool), np.zeros(target.shape, bool),
        {"sample_count": 0, "median_bgr": None, "std_bgr": None,
         "luminance_p10_p50_p90": None, "edge_pixels": 0, "edge_fraction": 0.0},
        [reason], False, int(suspect_count), 0, None,
        classification=classification,
    )


def _metadata_result(
    candidate, source, started, target, protected, converged, iterations, residual_linf,
    solve_domain, known_boundary, boundary_stats, reasons, contamination_supplied,
    contamination_pixels, suspect_pixels, roi, *, accepted=False,
    boundary_evidence=None, structural_crossing=False, structural_reason=None,
    classification=None, soft_edge_diagnostic=None,
):
    changed = np.any(candidate != source, axis=2)
    changed_pixels = int(np.count_nonzero(changed & ~target))
    protected_changed = int(np.count_nonzero(changed & protected))
    return {
        "candidate_bgr": candidate,
        "status": "accepted" if accepted else ("review_required" if reasons else "rejected"),
        "accepted": bool(accepted),
        "converged": bool(converged),
        "iterations": int(iterations),
        "residual_linf": float(residual_linf),
        "authorized_pixels": int(np.count_nonzero(target)),
        "computational_unknown_pixels": int(np.count_nonzero(solve_domain)),
        "dirichlet_boundary": boundary_stats,
        "boundary_evidence": boundary_evidence or {},
        "classification": classification or {},
        "soft_edge_diagnostic": soft_edge_diagnostic or {
            "candidate": False, "decision_impact": False, "reason": "not_evaluated",
        },
        "structural_evidence": {
            "category": "STRUCTURAL_ART_CONFLICT" if structural_crossing else None,
            "crossing_detected": bool(structural_crossing),
            "canny_edge_pixels_in_legacy_band": int(boundary_stats.get("edge_pixels", 0)),
            "gate_reason": structural_reason,
        },
        "boundary_contamination": {
            "caller_mask_supplied": bool(contamination_supplied),
            "caller_suspect_pixels": int(contamination_pixels),
            "nearby_suspect_pixels_excluded_from_dirichlet": int(suspect_pixels),
            "automatically_detected_as_text": False,
        },
        "roi_xyxy": list(roi) if roi is not None else None,
        "changed_pixels_outside_authorized_mask": changed_pixels,
        "protected_pixels_changed": protected_changed,
        "rejection_reasons": list(dict.fromkeys(reasons)),
        "runtime_ms": (time.perf_counter() - started) * 1000.0,
    }
