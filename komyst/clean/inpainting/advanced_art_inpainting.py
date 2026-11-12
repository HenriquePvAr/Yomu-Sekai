"""Optional local advanced art reconstruction for hard textured regions.

The adapter intentionally stays tiny and product-owned.  It does not import or
vendor the GPL manga-image-translator runtime used during #84F28 benchmarking.

Runtime contract:
- model files are external assets, never Git-tracked product code;
- a model is loaded only after an exact SHA256 match;
- failure means unavailable/review, not force-render;
- inference is local only.
"""
from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

import komyst.config.settings as config
from komyst.core.gpu import directml_enabled


@dataclass(frozen=True)
class AdvancedInpaintDescriptor:
    model_id: str
    model_version: str
    expected_sha256: str
    expected_size_bytes: int
    backend: str
    source_url: str
    code_license: str
    model_license: str


ANIME_MANGA_LAMA_LARGE_JIT = AdvancedInpaintDescriptor(
    model_id="anime_manga_lama_large_jit",
    model_version="sanster-iopaint-anime-manga-big-lama-pt",
    expected_sha256=(
        "479d3afdcb7ed2fd944ed4ebcc39ca45b33491f0f2e43eb1000bd623cfb41823"
    ),
    expected_size_bytes=205_717_870,
    backend="torchscript",
    source_url=(
        "https://github.com/Sanster/models/releases/download/"
        "AnimeMangaInpainting/anime-manga-big-lama.pt"
    ),
    code_license="Apache-2.0 adapter pattern; product-owned minimal loader",
    model_license="NEEDS FUTURE REVIEW for public redistribution",
)


class AdvancedInpaintUnavailable(RuntimeError):
    pass


class AdvancedInpaintIntegrityError(RuntimeError):
    pass


class AdvancedArtInpainter:
    """Lazy, reusable local LaMa-family adapter."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        descriptor: AdvancedInpaintDescriptor = ANIME_MANGA_LAMA_LARGE_JIT,
        device: str = "cpu",
    ):
        self.descriptor = descriptor
        self.model_path = Path(model_path or config.ADVANCED_ART_INPAINT_MODEL_PATH)
        self.device = device
        self._model = None
        self._gpu_session = None
        self.gpu_unavailable_reason: str | None = None
        self._lock = threading.Lock()
        self.last_load_seconds: float | None = None
        self._verified_file_key: tuple[int, int] | None = None
        self._verified_digest: str | None = None
        self.metrics = {
            "load_count": 0,
            "hash_count": 0,
            "hash_seconds": 0.0,
            "inference_count": 0,
            "inference_seconds": 0.0,
            "verify_count": 0,
            "hash_lookup_count": 0,
            "hash_cache_hit_count": 0,
            "hash_cache_miss_count": 0,
            "real_hash_compute_count": 0,
        }

    def available(self) -> bool:
        return self.model_path.exists()

    def verify_integrity(self) -> str:
        self.metrics["hash_lookup_count"] += 1
        if not self.model_path.exists():
            raise AdvancedInpaintUnavailable("MODEL_UNAVAILABLE")
        stat = self.model_path.stat()
        key = (int(stat.st_size), int(stat.st_mtime_ns))
        if key == self._verified_file_key and self._verified_digest:
            self.metrics["verify_count"] += 1
            self.metrics["hash_cache_hit_count"] += 1
            return self._verified_digest
        self.metrics["hash_cache_miss_count"] += 1
        hash_started = time.perf_counter()
        digest = _sha256_file(self.model_path)
        self.metrics["hash_count"] += 1
        self.metrics["real_hash_compute_count"] += 1
        self.metrics["hash_seconds"] += time.perf_counter() - hash_started
        expected = str(
            config.ADVANCED_ART_INPAINT_MODEL_SHA256
            or self.descriptor.expected_sha256
        ).lower()
        if digest.lower() != expected:
            raise AdvancedInpaintIntegrityError("MODEL_INTEGRITY_FAILED")
        self._verified_file_key = key
        self._verified_digest = digest.lower()
        self.metrics["verify_count"] += 1
        return self._verified_digest

    def load(self):
        with self._lock:
            if self._model is not None:
                return self._model
            digest = self.verify_integrity()
            started = time.perf_counter()
            if self.device == "cpu" and directml_enabled():
                # Exported from the verified .pt; any failure keeps the CPU model.
                try:
                    from komyst.clean.inpainting import lama_onnx

                    self._gpu_session = lama_onnx.DirectMLSession(
                        lama_onnx.ensure_onnx(self.model_path, digest))
                    self._model = self._gpu_session
                    self.last_load_seconds = time.perf_counter() - started
                    self.metrics["load_count"] += 1
                    return self._model
                except Exception as exc:  # noqa: BLE001 - GPU is an accelerator, never a requirement
                    self._gpu_session = None
                    self.gpu_unavailable_reason = type(exc).__name__
            try:
                import torch

                model = torch.jit.load(
                    str(self.model_path),
                    map_location=self.device,
                ).eval()
                self._model = model
                self.last_load_seconds = time.perf_counter() - started
                self.metrics["load_count"] += 1
                return self._model
            except Exception as exc:  # pragma: no cover - exact torch errors vary
                raise AdvancedInpaintUnavailable("MODEL_LOAD_FAILED") from exc

    def unload(self):
        with self._lock:
            self._model = None
            self._gpu_session = None

    def reconstruct(
        self,
        image_bgr: np.ndarray,
        mask: np.ndarray,
        *,
        debug_capture: dict | None = None,
    ) -> tuple[np.ndarray, dict]:
        """Return a clean image composited only inside ``mask``.

        ``mask > 0`` means REMOVE / RECONSTRUCT.

        ``debug_capture``, when given a dict, is populated with the raw model
        output (``pred_bgr``, at page size and location, uncomposited) and the
        context crop box, so a caller can compare RAW model output against the
        COMPOSITED result in the same offline run (#84F30 evidence).  This is
        opt-in and diagnostic only: normal callers pass nothing, inference and
        the returned ``composited``/``telemetry`` are unchanged either way, and
        nothing is persisted to disk unless the caller chooses to save it.
        """
        if image_bgr is None or mask is None or not np.any(mask > 0):
            raise ValueError("invalid_image_or_mask")
        model = self.load()

        mask_u8 = (mask > 0).astype(np.uint8) * 255
        x, y, w, h, margin = _context_crop(mask_u8, image_bgr.shape)
        crop_bgr = image_bgr[y : y + h, x : x + w]
        crop_mask = mask_u8[y : y + h, x : x + w]
        rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        padded_rgb, original_h, original_w = _pad_to_modulo(rgb, 8)
        padded_mask, _, _ = _pad_to_modulo(crop_mask, 8)
        image_np = _norm_img(padded_rgb)[None]
        mask_np = (_norm_img(padded_mask)[None] > 0).astype(np.float32)
        started = time.perf_counter()
        if model is self._gpu_session:
            pred_rgb = model(image_np, mask_np)[0].transpose(1, 2, 0)
        else:
            import torch

            with torch.no_grad():
                pred = model(torch.from_numpy(image_np).to(self.device), torch.from_numpy(mask_np).to(self.device))
            pred_rgb = pred[0].permute(1, 2, 0).detach().cpu().numpy()
        inference_seconds = time.perf_counter() - started
        self.metrics["inference_count"] += 1
        self.metrics["inference_seconds"] += inference_seconds
        pred_rgb = np.clip(pred_rgb * 255, 0, 255).astype(np.uint8)
        pred_rgb = pred_rgb[:original_h, :original_w]
        pred_bgr = cv2.cvtColor(pred_rgb, cv2.COLOR_RGB2BGR)
        pred_bgr = _match_luminance_and_feather_crop(crop_bgr, pred_bgr, crop_mask)
        composited = image_bgr.copy()
        target_crop = composited[y : y + h, x : x + w]
        target_crop[crop_mask > 0] = pred_bgr[crop_mask > 0]
        composited[y : y + h, x : x + w] = target_crop
        if debug_capture is not None:
            raw_full = image_bgr.copy()
            raw_full[y : y + h, x : x + w] = pred_bgr
            debug_capture["raw_pred_bgr_full"] = raw_full
            debug_capture["raw_pred_bgr_crop"] = pred_bgr.copy()
            debug_capture["context_crop_xywh"] = [int(x), int(y), int(w), int(h)]
        telemetry = {
            "advanced_inpaint_used": True,
            "model_id": self.descriptor.model_id,
            "model_version": self.descriptor.model_version,
            "model_sha256": self.verify_integrity(),
            "model_hash_verified": True,
            "device": "directml" if model is self._gpu_session else self.device,
            "backend": "onnx_directml" if model is self._gpu_session else self.descriptor.backend,
            "inference_ms": int(round(inference_seconds * 1000)),
            "hash_count": int(self.metrics["hash_count"]),
            "hash_lookup_count": int(self.metrics["hash_lookup_count"]),
            "hash_cache_hit_count": int(self.metrics["hash_cache_hit_count"]),
            "hash_cache_miss_count": int(self.metrics["hash_cache_miss_count"]),
            "real_hash_compute_count": int(self.metrics["real_hash_compute_count"]),
            "hash_total_ms": int(round(self.metrics["hash_seconds"] * 1000)),
            "load_ms": (
                int(round(self.last_load_seconds * 1000))
                if self.last_load_seconds is not None else None
            ),
            "mask_semantics": "255/remove_reconstruct",
            "context_crop_xywh": [int(x), int(y), int(w), int(h)],
            "context_margin": int(margin),
        }
        return composited, telemetry


_DEFAULT_INPAINTER: AdvancedArtInpainter | None = None


def get_default_inpainter() -> AdvancedArtInpainter:
    global _DEFAULT_INPAINTER
    if _DEFAULT_INPAINTER is None:
        _DEFAULT_INPAINTER = AdvancedArtInpainter()
    return _DEFAULT_INPAINTER


def reset_default_inpainter_for_tests():
    global _DEFAULT_INPAINTER
    _DEFAULT_INPAINTER = None


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _norm_img(np_img: np.ndarray) -> np.ndarray:
    if len(np_img.shape) == 2:
        np_img = np_img[:, :, None]
    return np_img.transpose((2, 0, 1)).astype("float32") / 255.0


def _pad_to_modulo(img: np.ndarray, mod: int) -> tuple[np.ndarray, int, int]:
    h, w = img.shape[:2]
    ph = (mod - h % mod) % mod
    pw = (mod - w % mod) % mod
    if ph or pw:
        img = cv2.copyMakeBorder(img, 0, ph, 0, pw, cv2.BORDER_REFLECT)
    return img, h, w


def _context_crop(mask: np.ndarray, image_shape) -> tuple[int, int, int, int, int]:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0 or len(ys) == 0:
        raise ValueError("empty_mask")
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    span = max(x1 - x0, y1 - y0)
    # Capped: past ~256 px of context the result barely changes (mean 0.7-1.2
    # levels inside large caption masks) while CPU time grows with the crop.
    margin = min(256, max(32, int(span * 0.45)))
    height, width = image_shape[:2]
    x0 = max(0, x0 - margin)
    y0 = max(0, y0 - margin)
    x1 = min(width, x1 + margin)
    y1 = min(height, y1 + margin)
    return x0, y0, x1 - x0, y1 - y0, margin


def _match_luminance_and_feather_crop(
    crop_bgr: np.ndarray,
    pred_bgr: np.ndarray,
    crop_mask: np.ndarray,
) -> np.ndarray:
    """Correct LAB chroma/luminance drift and feather the inner mask edge.

    Ported and adapted from meangrinch/MangaTranslator's post-inpainting
    boundary normalization:
    - Neutralizes warm/greenish chroma tint (A/B channels) when the surrounding
      12 px ring is monochrome grayscale (a_dev < 3.0 and b_dev < 3.0).
    - Shifts local L along the 3 px inner/outer boundary ring when a uniform
      offset is present, avoiding hard step contours.
    - Blends the 1..2 px inner edge of the mask using a Euclidean distance
      transform strictly inside ``crop_mask > 0`` so zero pixels outside the
      mask are modified.
    """
    inside = crop_mask > 0
    if not np.any(inside) or crop_bgr.shape != pred_bgr.shape:
        return pred_bgr
    result = pred_bgr.copy()
    mask_u8 = inside.astype(np.uint8)
    kernel_ring = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    outer_ring = (cv2.dilate(mask_u8, kernel_ring) > 0) & ~inside
    if int(np.count_nonzero(outer_ring)) >= 32:
        orig_lab = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
        pred_lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB).astype(np.float32)
        a_dev = float(np.mean(np.abs(orig_lab[:, :, 1][outer_ring] - 128.0)))
        b_dev = float(np.mean(np.abs(orig_lab[:, :, 2][outer_ring] - 128.0)))
        lab_modified = False
        if a_dev < 3.0 and b_dev < 3.0:
            pred_a_dev = float(np.mean(np.abs(pred_lab[:, :, 1][inside] - 128.0)))
            pred_b_dev = float(np.mean(np.abs(pred_lab[:, :, 2][inside] - 128.0)))
            if pred_a_dev > a_dev + 1.0 or pred_b_dev > b_dev + 1.0:
                pred_lab[:, :, 1][inside] = 128.0
                pred_lab[:, :, 2][inside] = 128.0
                lab_modified = True
        near_outer = (cv2.dilate(mask_u8, np.ones((7, 7), np.uint8)) > 0) & ~inside
        near_inner = inside & ~(cv2.erode(mask_u8, np.ones((7, 7), np.uint8)) > 0)
        if int(np.count_nonzero(near_outer)) >= 24 and int(np.count_nonzero(near_inner)) >= 24:
            outer_f = near_outer.astype(np.float32)
            inner_f = near_inner.astype(np.float32)
            outer_sup = cv2.blur(outer_f, (15, 15))
            inner_sup = cv2.blur(inner_f, (15, 15))
            paired = near_inner & (outer_sup > 0.05) & (inner_sup > 0.05)
            if int(np.count_nonzero(paired)) >= 24:
                out_l = cv2.blur(orig_lab[:, :, 0] * outer_f, (15, 15)) / np.maximum(outer_sup, 1e-3)
                in_l = cv2.blur(pred_lab[:, :, 0] * inner_f, (15, 15)) / np.maximum(inner_sup, 1e-3)
                l_diff = float(np.median((out_l - in_l)[paired]))
                if 1.0 <= abs(l_diff) <= 18.0:
                    pred_lab[:, :, 0][inside] = np.clip(pred_lab[:, :, 0][inside] + l_diff, 0.0, 255.0)
                    lab_modified = True
        if lab_modified:
            result = cv2.cvtColor(np.clip(pred_lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)

    dist_in = cv2.distanceTransform(mask_u8, cv2.DIST_L2, 3)
    feather_px = 2.0
    edge_band = inside & (dist_in > 0) & (dist_in < feather_px)
    if np.any(edge_band):
        diff = np.max(np.abs(crop_bgr.astype(np.float32) - result.astype(np.float32)), axis=2)
        safe_edge = edge_band & (diff <= 28.0)
        if np.any(safe_edge):
            alpha = np.clip(dist_in[safe_edge] / feather_px, 0.35, 1.0)[:, None]
            blended = (
                result[safe_edge].astype(np.float32) * alpha
                + crop_bgr[safe_edge].astype(np.float32) * (1.0 - alpha)
            )
            result[safe_edge] = np.clip(np.rint(blended), 0, 255).astype(np.uint8)
    return result
