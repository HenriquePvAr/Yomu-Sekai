"""Isolated OCR worker: runs Paddle (or any heavy engine) OUT of the pipeline process.

The pipeline spawns ``sys.executable -m yomu.ocr.subprocess_ocr_worker`` and
talks JSON-lines over stdin/stdout. A native crash inside Paddle's oneDNN
kills only this process; the parent marks the engine unavailable for the rest
of the run (fail-closed) and the pipeline keeps going.
"""
from __future__ import annotations

import base64
import json
import sys

import cv2
import numpy as np

_ENGINE = None
_ENGINE_ERROR = ""


def _engine():
    global _ENGINE, _ENGINE_ERROR
    if _ENGINE is not None or _ENGINE_ERROR:
        return _ENGINE
    try:
        from paddleocr import PaddleOCR

        _ENGINE = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            lang="en",
        )
    except Exception as exc:  # noqa: BLE001 - any import/init failure = unavailable
        _ENGINE_ERROR = f"{type(exc).__name__}: {exc}"
    return _ENGINE


def _reads(image_bgr: np.ndarray) -> list[str]:
    return [str(item.get("text") or "") for item in _detections(image_bgr)]


def _detections(image_bgr: np.ndarray) -> list[dict]:
    engine = _engine()
    if engine is None:
        return []
    results = engine.predict(image_bgr)
    detections: list[dict] = []
    for result in results:
        data = result if isinstance(result, dict) else getattr(result, "json", {})
        if not isinstance(data, dict):
            continue
        texts = data.get("rec_texts")
        texts = [str(t) for t in texts] if texts is not None else []
        scores_raw = data.get("rec_scores")
        scores = [float(s) for s in scores_raw] if scores_raw is not None else []
        boxes_raw = data.get("rec_boxes")
        boxes = list(boxes_raw) if boxes_raw is not None else []
        for index, text in enumerate(texts):
            box = []
            if index < len(boxes):
                entry = boxes[index]
                raw = [int(round(float(v))) for v in list(entry)[:4]] if hasattr(entry, "__len__") else []
                if len(raw) == 4:
                    box = raw
            detections.append({
                "text": text,
                "confidence": scores[index] if index < len(scores) else 0.0,
                "box": box,
            })
    return detections


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            blob = base64.b64decode(str(request.get("image_b64") or ""))
            array = np.frombuffer(blob, dtype=np.uint8)
            image = cv2.imdecode(array, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("image_decode_failed")
            if str(request.get("kind") or "") == "sweep":
                response = {"id": request.get("id"), "detections": _detections(image)}
            else:
                response = {"id": request.get("id"), "reads": _reads(image)}
        except Exception as exc:  # noqa: BLE001 - report, never die silently
            response = {
                "id": (json.loads(line).get("id") if line.startswith("{") else None),
                "reads": [],
                "error": f"{type(exc).__name__}: {exc}"[:200],
                "engine_error": _ENGINE_ERROR[:200],
            }
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
