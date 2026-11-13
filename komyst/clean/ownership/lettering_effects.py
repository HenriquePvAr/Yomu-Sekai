"""Owned chromatic glow around verified caption glyphs, separate from SFX v4.

The OCR boundary supplies a complete, traceable glyph core. These primitives
measure the surrounding effect and preserve visible white line art. They do not
turn arbitrary OCR rectangles into removal masks or waive reconstruction gates.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import cv2
import numpy as np


@dataclass
class LetteringEffectLayers:
    glyph: np.ndarray
    glow: np.ndarray
    effect: np.ndarray
    authorized: np.ndarray
    protected: np.ndarray
    feather_radius: int
    crop_box: tuple[int, int, int, int]
    profile: dict


def build_effect_layers(image_bgr, glyph_mask, line_boxes, *, neighbor_boxes=()):
    """Return an evidenced dark-ink/chromatic-glow envelope, or None.

    This requires a real radial drop in a coherent chromatic halo, rather than
    assuming every dark caption on a coloured background has a glow.
    """
    image = np.asarray(image_bgr)
    core = np.asarray(glyph_mask) > 0
    if image.ndim != 3 or core.shape != image.shape[:2] or not np.any(core):
        return None
    boxes = [tuple(int(v) for v in box) for box in line_boxes]
    if not boxes or any(w <= 0 or h < 36 for _, _, w, h in boxes):
        return None
    height = float(np.median([h for _, _, _, h in boxes]))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    if float(np.median(gray[core])) > 25:
        return None
    distance = cv2.distanceTransform((~core).astype(np.uint8), cv2.DIST_L2, 5)
    chromatic = (hsv[:, :, 1] >= 65) & (gray < 220)
    near_band = (distance > 0) & (distance <= max(3, .08 * height))
    far_band = (distance >= .30 * height) & (distance <= .50 * height)
    near, far = near_band & chromatic, far_band & chromatic
    if (np.count_nonzero(near) < 100 or np.count_nonzero(far) < 100
            or np.count_nonzero(near) / max(1, np.count_nonzero(near_band)) < .55):
        return None
    near_value = float(np.median(hsv[:, :, 2][near]))
    far_value = float(np.median(hsv[:, :, 2][far]))
    hue = float(np.median(hsv[:, :, 0][near]))
    hue_delta = np.abs(hsv[:, :, 0].astype(np.float32) - hue)
    hue_delta = np.minimum(hue_delta, 180 - hue_delta)
    coherence = float(np.mean(hue_delta[near] <= 18))
    if near_value - far_value < 25 or coherence < .70:
        return None

    # Counters belong to the glow of these verified caption glyphs. SFX masks
    # never reach this function, so their v4 hole-fill contract is unchanged.
    u8 = core.astype(np.uint8) * 255
    flood = cv2.copyMakeBorder(u8, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    cv2.floodFill(flood, None, (0, 0), 255)
    filled = u8 | cv2.bitwise_not(flood[1:-1, 1:-1])
    radius = max(4, min(48, 2 * round(.40 * max(h for _, _, _, h in boxes) / 2)))
    effect = cv2.dilate(filled, cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * radius + 1, 2 * radius + 1)))
    # Every pixel must still be attached to traced source-line geometry.
    envelope = np.zeros(core.shape, np.uint8)
    ih, iw = core.shape
    for x, y, w, h in boxes:
        envelope[max(0, y-radius-4):min(ih, y+h+radius+4),
                 max(0, x-radius-4):min(iw, x+w+radius+4)] = 255
    effect &= envelope
    if np.count_nonzero(effect) / effect.size > .16:
        return None
    for x, y, w, h in neighbor_boxes or ():
        if np.any(effect[max(0, y):min(ih, y+h), max(0, x):min(iw, x+w)]):
            return None
    protected = ((gray >= 225) & (hsv[:, :, 1] <= 40)).astype(np.uint8) * 255
    authorized = effect.copy()
    authorized[protected > 0] = 0
    if np.any(core & (authorized == 0)):
        return None
    # Explicit glow ownership requires the measured hue and chroma. The broader
    # reconstruction envelope may also contain background and cannot by itself
    # authorize darkening an unrelated light object.
    glow = ((effect > 0) & ~core & chromatic & (hue_delta <= 20))
    glow[protected > 0] = False
    ys, xs = np.nonzero(effect)
    margin = max(32, round(height * .45))
    x1 = max(0, (int(xs.min()) - margin) // 32 * 32)
    y1 = max(0, (int(ys.min()) - margin) // 32 * 32)
    x2 = min(iw, math.ceil((int(xs.max()) + 1 + margin) / 32) * 32)
    y2 = min(ih, math.ceil((int(ys.max()) + 1 + margin) / 32) * 32)
    if (x2-x1)*(y2-y1) > 1_048_576:
        return None
    return LetteringEffectLayers(
        glyph=u8, glow=glow.astype(np.uint8)*255, effect=effect, authorized=authorized,
        protected=protected, feather_radius=max(2, min(12, round(height*.11))),
        crop_box=(x1, y1, x2-x1, y2-y1),
        profile={"schema": 1, "source_effect_verified": True,
                 "glyph_pixels": int(np.count_nonzero(core)),
                 "glow_pixels": int(np.count_nonzero(glow)),
                 "effect_pixels": int(np.count_nonzero(authorized)),
                 "effect_page_ratio": round(float(np.count_nonzero(authorized)/core.size), 7),
                 "halo_radius": radius, "halo_near_value": near_value,
                 "halo_far_value": far_value, "halo_hue": round(hue, 3),
                 "halo_hue_coherence": round(coherence, 4)},
    )


def composite_effect(image_bgr, generated_bgr, layers):
    """Blend inside the authorized effect only, preserving protected lines exactly."""
    image, generated = np.asarray(image_bgr), np.asarray(generated_bgr)
    if image.shape != generated.shape or layers.authorized.shape != image.shape[:2]:
        raise ValueError("effect_composite_shape_mismatch")
    # Protected line holes must not introduce a feather halo around each line.
    effect = layers.effect > 0
    distance = cv2.distanceTransform(effect.astype(np.uint8), cv2.DIST_L2, 5)
    alpha = np.clip(distance / max(1, layers.feather_radius), 0, 1)
    alpha = .5 - .5 * np.cos(np.pi * alpha)
    alpha[layers.authorized == 0] = 0
    result = image.copy()
    inside = layers.authorized > 0
    weights = alpha[inside, None]
    result[inside] = np.clip(np.rint(image[inside]*(1-weights) + generated[inside]*weights), 0, 255).astype(np.uint8)
    return result


def paired_boundary_color(original_bgr, candidate_bgr, mask, *, protected_mask=None):
    """Colour continuity measured in local pairs rather than a global ring median."""
    original, candidate = np.asarray(original_bgr), np.asarray(candidate_bgr)
    if original.shape != candidate.shape or np.asarray(mask).shape != original.shape[:2]:
        return {"measured": False, "passed": False, "reason": "shape_mismatch"}
    u8 = (np.asarray(mask) > 0).astype(np.uint8)
    if not np.any(u8):
        return {"measured": False, "passed": False, "reason": "empty_mask"}
    outer = (cv2.dilate(u8, np.ones((7, 7), np.uint8)) > 0) & ~(u8 > 0)
    inner = (u8 > 0) & ~(cv2.erode(u8, np.ones((7, 7), np.uint8)) > 0)
    if protected_mask is not None:
        protect = cv2.dilate((np.asarray(protected_mask)>0).astype(np.uint8), np.ones((11, 11), np.uint8)) > 0
        outer &= ~protect
        inner &= ~protect
    of, inf = outer.astype(np.float32), inner.astype(np.float32)
    osup, isup = cv2.blur(of, (21, 21)), cv2.blur(inf, (21, 21))
    paired = inner & (osup > .04) & (isup > .04)
    count = int(np.count_nonzero(paired))
    coverage = count / max(1, int(np.count_nonzero(inner)))
    if count < 128 or coverage < .15:
        return {"measured": False, "passed": False, "reason": "insufficient_boundary_support",
                "sample_pixels": count, "coverage": round(coverage, 4)}
    errors = []
    for channel in range(3):
        before = cv2.blur(original[:, :, channel].astype(np.float32)*of, (21, 21))/np.maximum(osup, .001)
        after = cv2.blur(candidate[:, :, channel].astype(np.float32)*inf, (21, 21))/np.maximum(isup, .001)
        errors.append(np.abs(before-after))
    values = np.mean(errors, axis=0)[paired]
    median, p95 = float(np.median(values)), float(np.percentile(values, 95))
    return {"measured": True, "passed": median <= 12 and p95 <= 30,
            "reason": "ok" if median <= 12 and p95 <= 30 else "local_boundary_color_mismatch",
            "sample_pixels": count, "coverage": round(coverage, 4),
            "median_error": round(median, 4), "p95_error": round(p95, 4)}
