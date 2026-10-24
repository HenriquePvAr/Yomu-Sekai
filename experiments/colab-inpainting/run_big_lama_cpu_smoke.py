"""Run one offline Big-LaMa CPU smoke on a deterministic synthetic fixture.

This research-only script never downloads weights or reads manga pages. It
requires the exact checkpoint already configured in Yomu and writes evidence
to a fresh temporary directory unless --output is explicitly supplied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Running a repository research script by path places only its own directory
# on sys.path; resolve the checkout root explicitly without relying on cwd.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from yomu.clean.inpainting.advanced_art_inpainting import (
    ANIME_MANGA_LAMA_LARGE_JIT,
    AdvancedArtInpainter,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_fixture() -> tuple[Image.Image, Image.Image, Image.Image]:
    width, height = 640, 896
    clean = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(clean)
    draw.rectangle((56, 52, 584, 844), outline=(20, 20, 20), width=4)
    draw.ellipse((170, 148, 470, 448), outline=(20, 20, 20), width=6)
    draw.arc((208, 190, 432, 416), 5, 175, fill=(45, 45, 45), width=4)
    draw.line((105, 562, 535, 562), fill=(25, 25, 25), width=3)
    draw.line((105, 594, 535, 674), fill=(65, 65, 65), width=2)

    source = clean.copy()
    overlay = ImageDraw.Draw(source)
    try:
        font = ImageFont.truetype("arial.ttf", 38)
    except OSError:
        font = ImageFont.load_default()
    text = "SYNTHETIC TEST"
    origin = (170, 286)
    box = overlay.textbbox(origin, text, font=font, stroke_width=1)
    overlay.text(origin, text, font=font, fill=(0, 0, 0), stroke_width=1, stroke_fill=(0, 0, 0))

    mask = Image.new("L", source.size, 0)
    padding = 14
    ImageDraw.Draw(mask).rectangle(
        (box[0] - padding, box[1] - padding, box[2] + padding, box[3] + padding),
        fill=255,
    )
    return source, mask, clean


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if args.output is None:
        out = Path(tempfile.mkdtemp(prefix="yomu-big-lama-cpu-"))
    else:
        out = args.output
        out.mkdir(parents=True, exist_ok=False)
    source, mask_img, ground_truth = make_fixture()
    source_np = np.asarray(source)
    mask = np.asarray(mask_img, dtype=np.uint8)
    gt_np = np.asarray(ground_truth)
    inside = mask > 0
    overlay_pixels = np.any(source_np != gt_np, axis=2)
    overlay_outside = int(overlay_pixels[~inside].sum())
    if overlay_outside:
        raise RuntimeError("fixture_text_outside_authorized_mask")

    model_path = args.checkpoint
    inpainter = AdvancedArtInpainter(model_path=model_path, device="cpu")
    actual_hash = inpainter.verify_integrity()
    source.save(out / "synthetic_source.png")
    mask_img.save(out / "authorized_mask.png")
    ground_truth.save(out / "ground_truth_clean.png")

    capture: dict = {}
    started = time.perf_counter()
    result_bgr, telemetry = inpainter.reconstruct(
        cv2.cvtColor(source_np, cv2.COLOR_RGB2BGR), mask, debug_capture=capture
    )
    wall_seconds = time.perf_counter() - started
    final = Image.fromarray(cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB))
    raw_bgr = capture["raw_pred_bgr_full"]
    raw = Image.fromarray(cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2RGB))
    final_np = np.asarray(final)
    outside_changed = int(np.any(source_np != final_np, axis=2)[~inside].sum())
    delta = final_np[inside].astype(np.float32) - gt_np[inside].astype(np.float32)
    mse = float(np.mean(np.square(delta)))
    metrics = {
        "masked_mae": float(np.mean(np.abs(delta))),
        "masked_rmse": float(np.sqrt(mse)),
        "masked_psnr_db": None if mse == 0 else float(20 * np.log10(255 / np.sqrt(mse))),
        "perfect_masked_match": mse == 0,
    }

    raw.save(out / "raw_model_donor.png")
    final.save(out / "final_composite.png")
    labels = ["source", "mask", "ground truth", "raw donor", "final"]
    panels = [source, mask_img.convert("RGB"), ground_truth, raw, final]
    sheet = Image.new("RGB", (source.width * len(panels), source.height + 32), "white")
    sheet_draw = ImageDraw.Draw(sheet)
    for index, (label, panel) in enumerate(zip(labels, panels)):
        x = index * source.width
        sheet_draw.text((x + 8, 8), label, fill=(0, 0, 0))
        sheet.paste(panel, (x, 32))
    sheet.save(out / "comparison.png")

    try:
        import psutil

        peak_rss = int(psutil.Process().memory_info().rss)
    except Exception:
        peak_rss = None
    report = {
        "status": "REVIEW_REQUIRED",
        "visual_review": "REQUIRED",
        "model_id": ANIME_MANGA_LAMA_LARGE_JIT.model_id,
        "model_version": ANIME_MANGA_LAMA_LARGE_JIT.model_version,
        "checkpoint_sha256": actual_hash,
        "checkpoint_bytes": inpainter.model_path.stat().st_size,
        "device": "cpu",
        "inference_wall_seconds_including_lazy_load": wall_seconds,
        "load_seconds": inpainter.last_load_seconds,
        "inference_seconds": inpainter.metrics["inference_seconds"],
        "process_rss_after_inference_bytes": peak_rss,
        "image_size": list(source.size),
        "mask_pixels": int(inside.sum()),
        "fixture_text_outside_mask_pixels": overlay_outside,
        "outside_mask_changed_pixels": outside_changed,
        "inside_mask_ground_truth_metrics": metrics,
        "telemetry": telemetry,
        "artifacts": {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(out.glob("*.png"))},
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"output_dir": str(out), **report}, indent=2))
    return 0 if outside_changed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
