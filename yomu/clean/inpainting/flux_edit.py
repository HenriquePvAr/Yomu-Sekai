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
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

from yomu.config import settings

_DEFAULT_MODEL_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "TradutorIA" / "models" / "flux"


def _model_dir() -> Path:
    return Path(getattr(settings, "GENERATIVE_INPAINT_MODEL_DIR", "") or _DEFAULT_MODEL_DIR)


def available() -> bool:
    if not getattr(settings, "GENERATIVE_INPAINT_ENABLED", False):
        return False
    directory = _model_dir()
    return all(
        (directory / name).is_file()
        for name in ("sd-cli.exe", "flux-2-klein-4b-Q4_0.gguf", "flux2-vae.safetensors", "qwen3-4b-q4_k_m.gguf")
    )


def flux_edit_inpaint(
    image_bgr: np.ndarray,
    mask: np.ndarray,
    *,
    prompt: str = "",
    steps: int = 4,
    timeout_seconds: float = 240.0,
) -> np.ndarray | None:
    """Regenerate ``mask`` pixels conditioned on the surrounding art.

    Returns the composited image (only inside the mask changed) or ``None``
    on any failure - callers stay fail-closed and fall back to review.
    """
    if not available() or image_bgr is None or mask is None:
        return None
    directory = _model_dir()
    mask_u8 = (np.asarray(mask) > 0).astype(np.uint8) * 255
    if not np.any(mask_u8):
        return None
    with tempfile.TemporaryDirectory(prefix="yomu-flux-") as tmp:
        tmp_path = Path(tmp)
        input_path = tmp_path / "input.png"
        mask_path = tmp_path / "mask.png"
        output_path = tmp_path / "output.png"
        cv2.imwrite(str(input_path), image_bgr)
        cv2.imwrite(str(mask_path), mask_u8)
        command = [
            str(directory / "sd-cli.exe"),
            "--diffusion-model", str(directory / "flux-2-klein-4b-Q4_0.gguf"),
            "--vae", str(directory / "flux2-vae.safetensors"),
            "--llm", str(directory / "qwen3-4b-q4_k_m.gguf"),
            "-M", "img_gen",
            "-r", str(input_path),
            "--mask", str(mask_path),
            "-p", prompt or "seamless manga artwork background",
            "-o", str(output_path),
            "--cfg-scale", "1.0",
            "--sampling-method", "euler",
            "--steps", str(int(steps)),
            "-W", str(int(image_bgr.shape[1])),
            "-H", str(int(image_bgr.shape[0])),
            "--offload-to-cpu",
        ]
        try:
            result = subprocess.run(
                command,
                cwd=str(directory),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0 or not output_path.is_file():
            return None
        generated = cv2.imread(str(output_path))
        if generated is None:
            return None
        if generated.shape[:2] != image_bgr.shape[:2]:
            generated = cv2.resize(generated, (image_bgr.shape[1], image_bgr.shape[0]))
        composited = np.asarray(image_bgr).copy()
        composited[mask_u8 > 0] = generated[mask_u8 > 0]
        return composited
