from __future__ import annotations

import io
import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

from yomu.core import gpu


def _metadata_version(name: str) -> str:
    versions = {
        "onnxruntime": "1.31.1",
        "onnxruntime-directml": "1.24.4",
    }
    if name in versions:
        return versions[name]
    raise gpu.importlib.metadata.PackageNotFoundError(name)


def test_auto_warns_when_cpu_and_directml_distributions_collide():
    fake_runtime = SimpleNamespace(get_available_providers=lambda: ["CPUExecutionProvider"])
    with (
        patch.dict(os.environ, {"GPU_INFERENCE": "auto"}),
        patch.dict(sys.modules, {"onnxruntime": fake_runtime}),
        patch.object(gpu.importlib.metadata, "version", side_effect=_metadata_version),
    ):
        status = gpu.inference_device_status()
        stream = io.StringIO()
        with patch("sys.stdout", stream):
            gpu.log_inference_device_warning(status)

    assert status["directml_provider_available"] is False
    assert status["conflicting_onnxruntime_distributions"] is True
    assert status["configured_onnx_device"] == "cpu"
    assert "GPU_INFERENCE_WARNING requested=auto effective=cpu" in stream.getvalue()
    assert "Uninstall onnxruntime" in stream.getvalue()
    assert "DmlExecutionProvider" in stream.getvalue()


def test_auto_does_not_warn_when_directml_provider_is_available():
    fake_runtime = SimpleNamespace(
        get_available_providers=lambda: ["DmlExecutionProvider", "CPUExecutionProvider"]
    )
    with (
        patch.dict(os.environ, {"GPU_INFERENCE": "auto"}),
        patch.dict(sys.modules, {"onnxruntime": fake_runtime}),
        patch.object(gpu.importlib.metadata, "version", side_effect=_metadata_version),
    ):
        status = gpu.inference_device_status()
        stream = io.StringIO()
        with patch("sys.stdout", stream):
            gpu.log_inference_device_warning(status)

    assert status["configured_onnx_device"] == "directml"
    assert stream.getvalue() == ""
