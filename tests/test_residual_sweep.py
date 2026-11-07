"""Residual sweep: report source text the primary OCR never detected."""
from types import SimpleNamespace
from unittest import mock

import numpy as np

from yomu.config import settings as config
from yomu.ocr.residual_sweep import sweep_page_residuals


def _fake_gateway(detections):
    gateway = SimpleNamespace(unavailable_reason="", _next_id=0)
    gateway.sweep = lambda image: detections
    return gateway


def test_sweep_reports_only_undetected_regions():
    page = np.full((100, 200, 3), 255, np.uint8)
    detections = [
        {"box": [10, 10, 40, 20], "text": "CLINK", "confidence": 0.9},   # fantasma
        {"box": [60, 50, 22, 7], "text": "GRIP", "confidence": 0.9},    # já conhecido (0.6x)
        {"box": [150, 10, 30, 20], "text": "A", "confidence": 0.9},      # curto demais
        {"box": [20, 70, 40, 20], "text": "SUS", "confidence": 0.2},     # conf baixa
    ]
    known = [(100, 84, 36, 12)]  # GRIP em escala cheia
    with mock.patch("yomu.ocr.subprocess_ocr._ensure_gateway", return_value=_fake_gateway(detections)):
        residuals = sweep_page_residuals(page, known, page_index=4)
    texts = [r["text"] for r in residuals]
    assert "CLINK" in texts
    assert "GRIP" not in texts
    assert "A" not in texts
    assert "SUS" not in texts


def test_sweep_quiet_when_engine_unavailable():
    with mock.patch("yomu.ocr.subprocess_ocr._ensure_gateway", return_value=None):
        assert sweep_page_residuals(np.zeros((50, 50, 3), np.uint8), [], page_index=1) == []


def test_sweep_disabled_by_flag():
    with mock.patch.object(config, "OCR_RESIDUAL_SWEEP", False):
        assert sweep_page_residuals(np.zeros((50, 50, 3), np.uint8), [], page_index=1) == []
