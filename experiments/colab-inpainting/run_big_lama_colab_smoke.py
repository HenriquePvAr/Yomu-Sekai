"""Run exactly one Big-LaMa GPU smoke on one synthetic benchmark case in Colab.

This research-only runner never reads private pages, loops over cases, retries,
or shuts down the runtime. It requires explicit confirmation flags and a fresh
output directory. Check Colab resource authorization in the UI before running.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import stat
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

import cv2
import numpy as np
from PIL import Image, ImageDraw


WEIGHT_URL = (
    "https://github.com/Sanster/models/releases/download/"
    "AnimeMangaInpainting/anime-manga-big-lama.pt"
)
WEIGHT_SIZE = 205_717_870
WEIGHT_SHA256 = "479d3afdcb7ed2fd944ed4ebcc39ca45b33491f0f2e43eb1000bd623cfb41823"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_checkpoint(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        temporary = path.with_name(path.name + ".download-part")
        if temporary.exists():
            raise RuntimeError(f"incomplete_download_exists: {temporary.name}; inspect it manually")
        urllib.request.urlretrieve(WEIGHT_URL, temporary)
        if temporary.stat().st_size != WEIGHT_SIZE or sha256(temporary) != WEIGHT_SHA256:
            raise RuntimeError("checkpoint_size_or_sha256_mismatch; refusing to load")
        temporary.replace(path)
    if path.stat().st_size != WEIGHT_SIZE or sha256(path) != WEIGHT_SHA256:
        raise RuntimeError("checkpoint_size_or_sha256_mismatch; refusing to load")


def context_crop(mask: np.ndarray, image_shape: tuple[int, ...]) -> tuple[int, int, int, int, int]:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        raise ValueError("empty_mask")
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    margin = max(32, int(max(x1 - x0, y1 - y0) * 0.45))
    height, width = image_shape[:2]
    x0, y0 = max(0, x0 - margin), max(0, y0 - margin)
    x1, y1 = min(width, x1 + margin), min(height, y1 + margin)
    return x0, y0, x1 - x0, y1 - y0, margin


def norm_img(array: np.ndarray) -> np.ndarray:
    if array.ndim == 2:
        array = array[:, :, None]
    return array.transpose((2, 0, 1)).astype(np.float32) / 255.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-zip", type=Path, required=True)
    parser.add_argument("--case-id", choices=("easy_balloon", "medium_gradient", "medium_halftone", "hard_line_art"), default="easy_balloon")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, default=Path("/content/models/anime-manga-big-lama.pt"))
    parser.add_argument("--confirm-one-inference", action="store_true")
    parser.add_argument("--confirm-research-only-rights-open", action="store_true")
    args = parser.parse_args()
    if not args.confirm_one_inference or not args.confirm_research_only_rights_open:
        parser.error("pass both confirmation flags after checking the runtime/resource gate and accepting research-only unresolved rights")
    if args.case_id == "extreme_sfx":
        parser.error("extreme holdout is reserved; do not use it for smoke or tuning")
    if args.output.exists():
        parser.error("output directory must be new; refusing to overwrite evidence")
    if not args.dataset_zip.is_file():
        parser.error("dataset_zip_not_found")

    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA_GPU_NOT_AVAILABLE; no model loaded")
    device = torch.device("cuda:0")
    gpu_name = torch.cuda.get_device_name(0)
    total_vram = int(torch.cuda.get_device_properties(0).total_memory)
    free_vram, total_vram_reported = torch.cuda.mem_get_info(0)
    if int(total_vram_reported) != total_vram:
        raise RuntimeError("gpu_vram_probe_mismatch")

    with tempfile.TemporaryDirectory(prefix="yomu-colab-fixtures-") as temp_name:
        extract_dir = Path(temp_name)
        with zipfile.ZipFile(args.dataset_zip) as archive:
            total_uncompressed = 0
            for info in archive.infolist():
                member = PurePosixPath(info.filename)
                if member.is_absolute() or ".." in member.parts or "\\" in info.filename or ":" in info.filename:
                    raise RuntimeError("unsafe_dataset_archive_path")
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise RuntimeError("symlink_in_dataset_archive")
                total_uncompressed += info.file_size
            if total_uncompressed > 50 * 1024 * 1024:
                raise RuntimeError("dataset_archive_expands_beyond_50_mib_limit")
            bad = archive.testzip()
            if bad:
                raise RuntimeError(f"dataset_zip_corrupt_member:{bad}")
            archive.extractall(extract_dir)
        manifest = json.loads((extract_dir / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("schema") != "yomu-synthetic-clean-benchmark.v1" or not manifest.get("synthetic_only"):
            raise RuntimeError("unexpected_dataset_contract")
        entries = [item for item in manifest["cases"] if item["id"] == args.case_id]
        if len(entries) != 1:
            raise RuntimeError("case_id_not_unique_in_manifest")
        entry = entries[0]
        if entry.get("split") == "holdout":
            raise RuntimeError("holdout_case_cannot_be_used_for_smoke_or_tuning")
        case_dir = extract_dir / args.case_id
        for name, descriptor in entry["files"].items():
            target = case_dir / name
            if not target.is_file() or target.stat().st_size != descriptor["bytes"] or sha256(target) != descriptor["sha256"]:
                raise RuntimeError(f"fixture_integrity_failed:{name}")
        source_image = Image.open(case_dir / "source.png").convert("RGB")
        mask_image = Image.open(case_dir / "authorized_mask.png").convert("L")
        ground_truth_image = Image.open(case_dir / "ground_truth_clean.png").convert("RGB")
        protected_image = Image.open(case_dir / "protected_art_mask.png").convert("L")
        if len({source_image.size, mask_image.size, ground_truth_image.size, protected_image.size}) != 1:
            raise RuntimeError("fixture_dimensions_mismatch")

        source_rgb = np.asarray(source_image)
        mask_u8 = np.asarray(mask_image, dtype=np.uint8)
        protected = np.asarray(protected_image) > 0
        target_mask = mask_u8 > 0
        if np.any(target_mask & protected):
            raise RuntimeError("authorized_mask_overlaps_protected_art")
        if not np.any(target_mask):
            raise RuntimeError("empty_mask")
        source_bgr = cv2.cvtColor(source_rgb, cv2.COLOR_RGB2BGR)
        x, y, w, h, margin = context_crop(mask_u8, source_bgr.shape)
        crop_bgr = source_bgr[y:y+h, x:x+w]
        crop_mask = mask_u8[y:y+h, x:x+w]
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        ph, pw = (8 - crop_rgb.shape[0] % 8) % 8, (8 - crop_rgb.shape[1] % 8) % 8
        if ph or pw:
            crop_rgb = cv2.copyMakeBorder(crop_rgb, 0, ph, 0, pw, cv2.BORDER_REFLECT)
            crop_mask = cv2.copyMakeBorder(crop_mask, 0, ph, 0, pw, cv2.BORDER_REFLECT)
        original_h, original_w = min(h, crop_rgb.shape[0]), min(w, crop_rgb.shape[1])
        image_tensor = torch.from_numpy(norm_img(crop_rgb)).unsqueeze(0).to(device)
        mask_tensor = torch.from_numpy(norm_img(crop_mask)).unsqueeze(0).to(device)
        mask_tensor = (mask_tensor > 0).float()

        checkpoint_present_before = args.checkpoint.is_file()
        checkpoint_prepare_started = time.perf_counter()
        ensure_checkpoint(args.checkpoint)
        checkpoint_prepare_seconds = time.perf_counter() - checkpoint_prepare_started
        try:
            import psutil
            host_ram_before = int(psutil.virtual_memory().available)
        except Exception:
            host_ram_before = None
        torch.cuda.reset_peak_memory_stats(device)
        load_started = time.perf_counter()
        model = torch.jit.load(str(args.checkpoint), map_location=device).eval()
        torch.cuda.synchronize(device)
        load_seconds = time.perf_counter() - load_started
        inference_started = time.perf_counter()
        with torch.inference_mode():
            prediction = model(image_tensor, mask_tensor)
        torch.cuda.synchronize(device)
        inference_seconds = time.perf_counter() - inference_started
        pred_rgb = prediction[0].permute(1, 2, 0).detach().cpu().numpy()
        pred_rgb = np.clip(pred_rgb * 255, 0, 255).astype(np.uint8)[:original_h, :original_w]
        pred_bgr = cv2.cvtColor(pred_rgb, cv2.COLOR_RGB2BGR)

        final_bgr = source_bgr.copy()
        raw_bgr = source_bgr.copy()
        raw_bgr[y:y+h, x:x+w] = pred_bgr[:h, :w]
        final_crop = final_bgr[y:y+h, x:x+w]
        final_crop[crop_mask[:h, :w] > 0] = pred_bgr[:h, :w][crop_mask[:h, :w] > 0]
        final_bgr[y:y+h, x:x+w] = final_crop
        final_rgb = cv2.cvtColor(final_bgr, cv2.COLOR_BGR2RGB)
        outside_changed = int(np.any(final_rgb != source_rgb, axis=2)[~target_mask].sum())
        if outside_changed != 0:
            raise RuntimeError(f"outside_mask_changed_pixels={outside_changed}")
        gt = np.asarray(ground_truth_image)
        error = final_rgb[target_mask].astype(np.float32) - gt[target_mask].astype(np.float32)
        mse = float(np.mean(error ** 2))

        args.output.mkdir(parents=True, exist_ok=False)
        Image.fromarray(source_rgb).save(args.output / "source.png")
        mask_image.save(args.output / "authorized_mask.png")
        ground_truth_image.save(args.output / "ground_truth_clean.png")
        Image.fromarray(cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2RGB)).save(args.output / "raw_model_donor.png")
        final_image = Image.fromarray(final_rgb)
        final_image.save(args.output / "final_composite.png")
        panels = [("source", source_image), ("mask", mask_image.convert("RGB")), ("ground truth", ground_truth_image), ("final", final_image)]
        preview = Image.new("RGB", (source_image.width * len(panels), source_image.height + 28), "white")
        draw = ImageDraw.Draw(preview)
        for index, (label, panel) in enumerate(panels):
            left = index * source_image.width
            draw.text((left + 6, 5), label, fill="black")
            preview.paste(panel, (left, 28))
        preview.save(args.output / "comparison.png")

        try:
            import psutil
            host_ram_available = int(psutil.virtual_memory().available)
        except Exception:
            host_ram_available = None
        report = {
            "status": "REVIEW_REQUIRED",
            "model_id": "anime_manga_lama_large_jit",
            "device": gpu_name,
            "total_vram_bytes": total_vram,
            "free_vram_before_load_bytes": int(free_vram),
            "torch_version": torch.__version__,
            "cuda_runtime": torch.version.cuda,
            "python": os.sys.version.split()[0],
            "checkpoint_url": WEIGHT_URL,
            "checkpoint_size_bytes": args.checkpoint.stat().st_size,
            "checkpoint_sha256": sha256(args.checkpoint),
            "checkpoint_present_before_run": checkpoint_present_before,
            "checkpoint_prepare_seconds": checkpoint_prepare_seconds,
            "checkpoint_rights": "UNRESOLVED; research-only evaluation; not cleared for redistribution or commercial use",
            "case_id": args.case_id,
            "category": entry["category"],
            "split": entry["split"],
            "image_size": list(source_image.size),
            "mask_pixels": int(target_mask.sum()),
            "protected_art_overlap_pixels": 0,
            "context_crop_xywh": [x, y, w, h],
            "context_margin": margin,
            "load_seconds": load_seconds,
            "inference_seconds": inference_seconds,
            "peak_allocated_vram_bytes": int(torch.cuda.max_memory_allocated(device)),
            "peak_reserved_vram_bytes": int(torch.cuda.max_memory_reserved(device)),
            "host_ram_available_before_bytes": host_ram_before,
            "host_ram_available_after_bytes": host_ram_available,
            "outside_mask_changed_pixels": outside_changed,
            "masked_mae": float(np.mean(np.abs(error))),
            "masked_rmse": float(math.sqrt(mse)),
            "masked_psnr_db": None if mse == 0 else float(20 * math.log10(255 / math.sqrt(mse))),
            "visual_review": "REQUIRED",
            "artifacts": {},
        }
        report["artifacts"] = {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(args.output.glob("*.png"))
        }
        (args.output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({"output_dir": str(args.output), **report}, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
