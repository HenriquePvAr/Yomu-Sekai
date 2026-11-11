"""Page-level residual sweep: surface source text the pipeline never detected.

Ghosts like the "CLINK" on ep. 285 p4 happen because the primary OCR never
reads the stylised lettering at all - it is invisible to every downstream
mask, validator and accounting. The sweep runs the isolated Paddle worker on
the page and reports text regions that overlap no known group box, so the
quality report shows exactly what stayed English and where.
"""
from __future__ import annotations

import re

import numpy as np
import cv2

from yomu.config import settings

_SWEEP_SCALE = 0.6
_MIN_OVERLAP_IOU = 0.10
_MIN_READ_CONFIDENCE = 0.55
_AUTO_FIX_MIN_CONFIDENCE = 0.80


def synthetic_sfx_lines(residuals, *, page_index, image_shape, image_bgr=None) -> list:
    """Convert only short, high-confidence display tokens to OCR lines.

    Full sentences remain report-only. Unknown sound readings are marked as
    sweep-derived so the ordinary SFX classifier can route them through the
    provider path while preserving the source if translation is rejected.
    """
    from yomu.ocr.ocr_engine import OCRLine
    height, width = image_shape[:2]
    lines = []
    for item in residuals or []:
        text = str(item.get("text") or "").strip()
        confidence = float(item.get("confidence") or 0.0)
        if confidence < _AUTO_FIX_MIN_CONFIDENCE or not re.fullmatch(r"[A-Z]{2,12}", text):
            continue
        try:
            x, y, w, h = (int(v) for v in item.get("bbox", ()))
        except (TypeError, ValueError):
            continue
        if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > width or y + h > height:
            continue
        box = (x, y, w, h)
        if image_bgr is not None:
            box = _tighten_broad_sfx_box(text, box, image_bgr)
            x, y, w, h = box
        polygon = np.asarray(
            [[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
            dtype=np.float32,
        )
        lines.append(OCRLine(
            text=text,
            confidence=confidence,
            polygon=polygon,
            box=(x, y, w, h),
            raw_text=text,
            engine="paddle_residual_sweep",
            page=int(page_index),
            metadata={
                "initial_ocr_engine": "paddle_residual_sweep",
                "residual_sweep_recovered": True,
                "residual_sweep_confidence": round(confidence, 3),
                "residual_sweep_original_box": tuple(int(v) for v in item.get("bbox", ())),
                "residual_sweep_box_tightened": box != tuple(int(v) for v in item.get("bbox", ())),
                "residual_sweep_glyphs_verified": box != tuple(int(v) for v in item.get("bbox", ())),
            },
        ))
    return lines


def _tighten_broad_sfx_box(text, box, image_bgr):
    """Recover a tight text box from separated dark glyphs in a broad sweep box.

    Paddle occasionally returns most of an illustrated panel as one SFX box.
    Only accept a replacement when dark connected components strongly match
    the number and shape of the recognized letters; otherwise retain the
    original box and let the ordinary classifier reject it.
    """
    x, y, w, h = box
    image_h, image_w = image_bgr.shape[:2]
    if w * h < image_h * image_w * 0.08 or len(text) < 3:
        return box
    crop = image_bgr[y:y + h, x:x + w]
    if crop.size == 0:
        return box
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _, dark = cv2.threshold(gray, 55, 255, cv2.THRESH_BINARY_INV)
    count, labels, stats, _centroids = cv2.connectedComponentsWithStats(dark, 8)
    # A threshold proportional to the whole page discarded the smaller final
    # E of CRACKLE and tightened the box around only six letters. Retain small
    # components only with the same strong ink/white-outline signature used
    # to establish display lettering, rather than cutting off real glyphs.
    min_component_area = max(80, int(image_h * image_w * 0.0002))
    components = []
    for label in range(1, count):
        cx, cy, cw, ch, area = stats[label]
        if area < min_component_area or ch < 24 or cw < 12:
            continue
        aspect = ch / max(1, cw)
        if not 0.45 <= aspect <= 8.0:
            continue
        component = labels == label
        ring = (cv2.dilate(component.astype(np.uint8), np.ones((5,5),np.uint8)) > 0) & (dark == 0)
        white_fraction = np.count_nonzero(ring & (gray >= 195)) / max(1, np.count_nonzero(ring))
        if float(np.median(gray[component])) > 15 or white_fraction < .45:
            continue
        components.append((int(cx), int(cy), int(cw), int(ch), int(area)))
    letter_count = len(re.sub(r"[^A-Z]", "", text.upper()))
    if not max(2, letter_count - 1) <= len(components) <= letter_count + 1:
        return box
    xs = [item[0] for item in components]
    ys = [item[1] for item in components]
    right = [item[0] + item[2] for item in components]
    bottom = [item[1] + item[3] for item in components]
    tx, ty = x + min(xs), y + min(ys)
    tw, th = max(right) - min(xs), max(bottom) - min(ys)
    if tw * th >= w * h * 0.65 or tw <= 0 or th <= 0:
        return box
    return (tx, ty, tw, th)


def _boxes_overlap(box_a, box_b) -> bool:
    ax, ay, aw, ah = box_a
    bx, by, bw, bh = box_b
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    if inter <= 0:
        return False
    union = aw * ah + bw * bh - inter
    return union > 0 and (inter / union) >= _MIN_OVERLAP_IOU


def _mask_known_boxes(image_bgr: np.ndarray, known_boxes) -> np.ndarray:
    """Fill already-detected boxes with local border median before sweeping.

    Painting out known dialogue/SFX boxes prevents the CPU PaddleOCR recognizer
    from wasting ~1-2s per page re-recognizing text that primary OCR already
    owns, cutting residual_sweep latency by ~40% while keeping undetected
    artwork/SFX intact.
    """
    if not known_boxes:
        return image_bgr
    height, width = image_bgr.shape[:2]
    masked = image_bgr.copy()
    for raw_box in known_boxes:
        if not raw_box or len(raw_box) < 4:
            continue
        kx, ky, kw, kh = (int(v) for v in raw_box[:4])
        if kw <= 0 or kh <= 0:
            continue
        pad = 6
        x0 = max(0, kx - pad)
        y0 = max(0, ky - pad)
        x1 = min(width, kx + kw + pad)
        y1 = min(height, ky + kh + pad)
        if x1 <= x0 or y1 <= y0:
            continue
        roi = masked[y0:y1, x0:x1]
        border = np.concatenate([roi[0, :], roi[-1, :], roi[:, 0], roi[:, -1]], axis=0)
        fill = np.median(border, axis=0).astype(np.uint8)
        masked[y0:y1, x0:x1] = fill
    return masked


def sweep_page_residuals(original_bgr, known_boxes, page_index=None) -> list[dict]:
    """Return undetected source-text regions on this page (read-only report).

    Runs Paddle in the isolated subprocess on a downscaled copy of the page
    and keeps reads whose box overlaps no known group. Returns ``[]`` when the
    engine is unavailable - reporting must never block or break a run.
    """
    if not getattr(settings, "OCR_RESIDUAL_SWEEP", True):
        return []
    from yomu.ocr.subprocess_ocr import _ensure_gateway

    gateway = _ensure_gateway()
    if gateway is None:
        return []
    height, width = original_bgr.shape[:2]
    known = [tuple(int(v) for v in box[:4]) for box in (known_boxes or []) if box]
    sweep_source = _mask_known_boxes(original_bgr, known)
    small = cv2.resize(sweep_source, (max(1, int(width * _SWEEP_SCALE)), max(1, int(height * _SWEEP_SCALE))))
    detections = gateway.sweep(small)
    if not detections:
        return []
    inv = 1.0 / _SWEEP_SCALE
    residuals = []
    for det in detections:
        box = tuple(int(round(v * inv)) for v in det.get("box", ())[:4])
        text = str(det.get("text") or "").strip()
        if not text or len(text) < 2:
            continue
        if float(det.get("confidence") or 0.0) < _MIN_READ_CONFIDENCE:
            continue
        if any(_boxes_overlap(box, known_box) for known_box in known):
            continue
        residuals.append({
            "page": page_index,
            "bbox": box,
            "text": text,
            "confidence": round(float(det.get("confidence") or 0.0), 3),
        })
    return residuals
