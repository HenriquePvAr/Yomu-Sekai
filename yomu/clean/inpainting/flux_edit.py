"""Generative inpainting via stable-diffusion.cpp (FLUX.2 klein) as a subprocess.

LaMA-large reconstructs most regions well, but the hardest artwork (large
splash lettering over detailed art, unusual palettes) can still land in
review. FLUX.2 klein is an instruction/edit model: given the page crop and a
mask it regenerates the masked area conditioned on the surrounding art -
the strongest available reconstruction. It runs OUTSIDE the pipeline
(sd-cli.exe subprocess, Vulkan on the RX 6600), opt-in via
GENERATIVE_INPAINT_ENABLED, and its output faces the same validators as the
LaMA path before anything ships.
"""
from __future__ import annotations

import os
import hashlib
import subprocess
import tempfile
import threading
import time
from collections import OrderedDict
from pathlib import Path

import cv2
import numpy as np

from yomu.config import settings
from yomu.runtime.process_options import hidden_console_options

_DEFAULT_MODEL_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "TradutorIA" / "models" / "flux"


def _model_dir() -> Path:
    return Path(getattr(settings, "GENERATIVE_INPAINT_MODEL_DIR", "") or _DEFAULT_MODEL_DIR)


def manga_reconstruction_prompt(group=None) -> str:
    """Build a conservative edit instruction from non-text region metadata.

    Source lettering is intentionally never copied into the prompt: FLUX must
    reconstruct the artwork under the mask, not redraw or translate text.
    """
    background = str(getattr(group, "background_type", "") or "").lower()
    if background in {"white_balloon", "narration_box"}:
        surface = "the same clean, even balloon or narration-box interior"
    elif background in {"gradient", "smooth_gradient"}:
        surface = "the same smooth color gradient and lighting"
    elif background in {"textured_art", "structured_or_textured", "screentone"}:
        surface = "the same manga line art, screentone, hatching, and texture"
    else:
        surface = "the same surrounding manga artwork, colors, and texture"
    return (
        f"Restore only the masked area as {surface}. Continue nearby shapes and contours naturally. "
        "Preserve the composition and every unmasked pixel. Do not add lettering, words, symbols, "
        "objects, borders, or new effects."
    )


def available(*, purpose="general") -> bool:
    flag = "GENERATIVE_CAPTION_REPAIR_ENABLED" if purpose == "caption_effect" else "GENERATIVE_INPAINT_ENABLED"
    if purpose not in {"general", "caption_effect"} or not getattr(settings, flag, False):
        return False
    directory = _model_dir()
    return all(
        (directory / name).is_file()
        for name in ("sd-cli.exe", "flux-2-klein-4b-Q4_0.gguf", "flux2-vae.safetensors", "qwen3-4b-q4_k_m.gguf")
    )


_EDIT_CACHE = OrderedDict()
_EDIT_LOCK = threading.Lock()


def flux_reference_edit(
    image_bgr: np.ndarray,
    *,
    prompt: str = "",
    steps: int = 4,
    timeout_seconds: float = 240.0,
    purpose: str = "general",
    telemetry: dict | None = None,
    diagnostic_path: str | Path | None = None,
) -> np.ndarray | None:
    """Edit an aligned reference crop; callers must authorize/composite its pixels.

    Native ``--mask`` is not combined with reference editing: the installed
    backend produces invalid latent regions in that combination. The removal
    mask belongs to the external, verified compositor. Cache is process-local;
    a force/cache-off chapter never reuses a previous process's reconstruction.
    """
    metrics = telemetry if telemetry is not None else {}
    if not available(purpose=purpose) or image_bgr is None:
        metrics["reason"] = "generative_model_disabled_or_unavailable"
        return None
    directory = _model_dir()
    source = np.asarray(image_bgr)
    if source.ndim != 3 or source.dtype != np.uint8 or source.shape[0]*source.shape[1] > 1_048_576:
        metrics["reason"] = "generative_crop_invalid_or_excessive"
        return None
    prompt = prompt or "Restore the surrounding manga artwork and remove all lettering. Preserve colors and composition."
    files = [directory / name for name in ("sd-cli.exe", "flux-2-klein-4b-Q4_0.gguf", "flux2-vae.safetensors", "qwen3-4b-q4_k_m.gguf")]
    try:
        identity = tuple((str(p.resolve()), p.stat().st_size, p.stat().st_mtime_ns) for p in files)
    except OSError:
        metrics["reason"] = "generative_asset_unavailable"
        return None
    key = hashlib.sha256(source.tobytes()+repr((source.shape, prompt, steps, identity)).encode()).hexdigest()
    queued = time.perf_counter()
    with _EDIT_LOCK:
        metrics["queue_seconds"] = round(time.perf_counter()-queued, 6)
        cached = _EDIT_CACHE.get(key)
        if cached is not None:
            _EDIT_CACHE.move_to_end(key)
            metrics.update({"cache_hit": True, "reason": "ok"})
            return cached.copy()
        started = time.perf_counter()
        from yomu.core.gpu import DIRECTML_LOCK
        # Native Vulkan must share the same device budget as the DirectML
        # sessions. A separate FLUX-only lock allowed concurrent LaMA/OCR work
        # to compete with the edit's allocation peak on the same adapter.
        gpu_queued = time.perf_counter()
        with DIRECTML_LOCK:
            metrics["gpu_queue_seconds"] = round(time.perf_counter()-gpu_queued, 6)
            generated = _run_reference_edit(
                source, directory, prompt, steps, timeout_seconds, metrics,
                diagnostic_path=diagnostic_path,
            )
        metrics.update({"cache_hit": False, "wall_seconds": round(time.perf_counter()-started, 6)})
        if generated is not None:
            _EDIT_CACHE[key] = generated.copy()
            while len(_EDIT_CACHE) > 4:
                _EDIT_CACHE.popitem(last=False)
        return generated


def _stderr_tail(path: Path, *, lines: int = 40) -> str:
    """Read only the final stderr lines without loading an unbounded log."""
    with path.open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        end = stream.tell()
        start = end
        data = b""
        while start > 0 and data.count(b"\n") <= lines:
            amount = min(8192, start)
            start -= amount
            stream.seek(start)
            data = stream.read(amount) + data
    tail = data.splitlines()[-lines:]
    return b"\n".join(tail).decode("utf8", errors="replace")


def _persist_process_failure(stderr_path: Path, metrics: dict, diagnostic_path) -> None:
    if diagnostic_path is None:
        return
    destination = Path(diagnostic_path)
    try:
        tail = _stderr_tail(stderr_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(tail + ("\n" if tail else ""), encoding="utf8")
        metrics["diagnostic_log_path"] = str(destination)
    except OSError as exc:
        metrics["diagnostic_log_error"] = type(exc).__name__


def _run_reference_edit(source, directory, prompt, steps, timeout_seconds, metrics,
                        *, diagnostic_path=None):
    height, width = source.shape[:2]
    padded = cv2.copyMakeBorder(source, 0, (-height) % 32, 0, (-width) % 32, cv2.BORDER_REFLECT_101)
    if padded.shape[0]*padded.shape[1] > 1_048_576:
        metrics["reason"] = "generative_padded_crop_excessive"
        return None
    with tempfile.TemporaryDirectory(prefix="yomu-flux-") as tmp:
        tmp_path = Path(tmp)
        input_path = tmp_path / "input.png"
        output_path = tmp_path / "output.png"
        cv2.imwrite(str(input_path), padded)
        command = [
            str(directory / "sd-cli.exe"),
            "--diffusion-model", str(directory / "flux-2-klein-4b-Q4_0.gguf"),
            "--vae", str(directory / "flux2-vae.safetensors"),
            "--llm", str(directory / "qwen3-4b-q4_k_m.gguf"),
            "-M", "img_gen",
            "-r", str(input_path),
            "-p", prompt,
            "-o", str(output_path),
            "--cfg-scale", "1.0",
            "--sampling-method", "euler",
            "--steps", str(int(steps)),
            "-W", str(int(padded.shape[1])),
            "-H", str(int(padded.shape[0])),
            "--offload-to-cpu",
            "-s", "42",
        ]
        try:
            with (tmp_path / "stderr.log").open("wb") as error_log:
                result = subprocess.run(
                    command,
                    cwd=str(directory),
                    stdout=subprocess.DEVNULL,
                    stderr=error_log,
                    stdin=subprocess.DEVNULL,
                    timeout=timeout_seconds,
                    **hidden_console_options(),
                )
        except (OSError, subprocess.TimeoutExpired):
            metrics["reason"] = "generative_process_failed_or_timed_out"
            _persist_process_failure(tmp_path / "stderr.log", metrics, diagnostic_path)
            return None
        if result.returncode != 0 or not output_path.is_file():
            metrics["reason"] = "generative_output_missing"
            metrics["return_code"] = int(result.returncode)
            error_path = tmp_path / "stderr.log"
            if error_path.is_file():
                with error_path.open("rb") as stream:
                    stream.seek(max(0, error_path.stat().st_size-16384))
                    tail = stream.read().decode("utf8", errors="replace").lower()
                metrics["process_failure_category"] = (
                    "device_memory" if any(word in tail for word in
                        ("out of memory", "out_of_device_memory", "failed to allocate"))
                    else "device_lost" if "device_lost" in tail else "output_or_process_failure")
            _persist_process_failure(error_path, metrics, diagnostic_path)
            return None
        generated = cv2.imread(str(output_path))
        if generated is None:
            return None
        if generated.shape != padded.shape:
            metrics["reason"] = "generative_output_geometry_mismatch"
            return None
        metrics["reason"] = "ok"
        return generated[:height, :width].copy()


def flux_edit_inpaint(image_bgr, mask, *, prompt="", steps=4, timeout_seconds=240.0):
    """General compatibility adapter: return only a mask-bounded composite."""
    if image_bgr is None or mask is None or np.asarray(mask).shape != image_bgr.shape[:2]:
        return None
    inside = np.asarray(mask) > 0
    if not np.any(inside):
        return None
    ys, xs = np.nonzero(inside)
    h, w = inside.shape
    x1, y1 = max(0, int(xs.min())-64), max(0, int(ys.min())-64)
    x2, y2 = min(w, int(xs.max())+65), min(h, int(ys.max())+65)
    generated = flux_reference_edit(image_bgr[y1:y2, x1:x2], prompt=prompt, steps=steps, timeout_seconds=timeout_seconds)
    if generated is None:
        return None
    composited = np.asarray(image_bgr).copy()
    local_inside = inside[y1:y2, x1:x2]
    composited[y1:y2, x1:x2][local_inside] = generated[local_inside]
    return composited
