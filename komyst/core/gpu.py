"""Whether the ONNX models (RapidOCR, LaMa) may run on the GPU through DirectML."""
from __future__ import annotations

import functools
import importlib.metadata
import os
import sys
import threading

import komyst.config.settings as config

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


def inference_device_status() -> dict[str, object]:
    """Describe configured inference mode and the ONNX providers actually available."""
    setting = str(os.environ.get("GPU_INFERENCE", config.GPU_INFERENCE)).strip().lower()
    try:
        import onnxruntime

        providers = list(onnxruntime.get_available_providers())
    except Exception:  # noqa: BLE001 - missing/broken optional runtime is diagnostic data.
        providers = []

    def installed(distribution: str) -> bool:
        try:
            importlib.metadata.version(distribution)
            return True
        except importlib.metadata.PackageNotFoundError:
            return False
        except Exception:  # noqa: BLE001 - broken metadata must not block a job.
            return False

    cpu_package = installed("onnxruntime")
    directml_package = installed("onnxruntime-directml")
    dml_available = DIRECTML_PROVIDER in providers
    gpu_requested = setting not in {"off", "cpu", "0", "false", "no"}
    return {
        "gpu_inference_requested": setting,
        "onnxruntime_available_providers": providers,
        "onnxruntime_package_installed": cpu_package,
        "onnxruntime_directml_package_installed": directml_package,
        "conflicting_onnxruntime_distributions": cpu_package and directml_package,
        "directml_provider_available": dml_available,
        "configured_onnx_device": "directml" if gpu_requested and dml_available else "cpu",
    }


def log_inference_device_warning(status: dict[str, object]) -> None:
    """Warn in the job log when auto silently has to use CPU for ONNX inference."""
    if status.get("gpu_inference_requested") != "auto" or status.get("directml_provider_available"):
        return
    if status.get("conflicting_onnxruntime_distributions"):
        detail = (
            "both onnxruntime and onnxruntime-directml distributions are installed; "
            "they share the onnxruntime module directory. Uninstall onnxruntime, then "
            "reinstall onnxruntime-directml and verify DmlExecutionProvider."
        )
    else:
        detail = (
            "onnxruntime does not expose DmlExecutionProvider; install the supported "
            "onnxruntime-directml package and verify the provider list."
        )
    print(
        "GPU_INFERENCE_WARNING requested=auto effective=cpu "
        f"directml_provider_available=false detail={detail}",
        flush=True,
    )
