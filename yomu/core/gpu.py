"""Whether the ONNX models (RapidOCR, LaMa) may run on the GPU through DirectML."""
from __future__ import annotations

import functools
import os
import sys
import threading

import yomu.config.settings as config

DIRECTML_PROVIDER = "DmlExecutionProvider"
# One Run on the DirectML device at a time, across *all* sessions: two sessions
# (RapidOCR and LaMa) running at once crash the process with an access violation.
DIRECTML_LOCK = threading.Lock()


@functools.lru_cache(maxsize=1)
def _directml_installed() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import onnxruntime
    except Exception:  # noqa: BLE001 - no runtime, no GPU
        return False
    return DIRECTML_PROVIDER in onnxruntime.get_available_providers()


def directml_enabled() -> bool:
    setting = str(os.environ.get("GPU_INFERENCE", config.GPU_INFERENCE)).strip().lower()
    return setting not in {"off", "cpu", "0", "false", "no"} and _directml_installed()
