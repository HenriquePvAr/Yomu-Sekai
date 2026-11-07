"""Page-level residual sweep: surface source text the pipeline never detected.

Ghosts like the "CLINK" on ep. 285 p4 happen because the primary OCR never
reads the stylised lettering at all - it is invisible to every downstream
mask, validator and accounting. The sweep runs the isolated Paddle worker on
the page and reports text regions that overlap no known group box, so the
quality report shows exactly what stayed English and where.
"""
from __future__ import annotations

import numpy as np
import cv2

from yomu.config import settings

_SWEEP_SCALE = 0.6
_MIN_OVERLAP_IOU = 0.10
_MIN_READ_CONFIDENCE = 0.55


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
    small = cv2.resize(original_bgr, (max(1, int(width * _SWEEP_SCALE)), max(1, int(height * _SWEEP_SCALE))))
    detections = gateway.sweep(small)
    if not detections:
        return []
    inv = 1.0 / _SWEEP_SCALE
    known = [tuple(int(v) for v in box[:4]) for box in (known_boxes or []) if box]
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
