"""Build a deterministic, synthetic-only manga-cleaning evaluation set.

No network, private pages, model weights, or paid services are used. Output is
written to a new temporary directory (or a caller-specified new directory).
The extreme case is reserved as holdout and must not guide model tuning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


WIDTH, HEIGHT = 640, 896
CASES = (
    ("easy_balloon", "easy", "calibration", "HELLO THERE"),
    ("medium_gradient", "medium", "selection", "OVER THE HILLS"),
    ("medium_halftone", "medium", "selection", "GOOD LUCK!"),
    ("hard_line_art", "hard", "selection", "SFX CRASH!"),
    ("extreme_sfx", "extreme", "holdout", "KRAK!"),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_background(case_id: str) -> tuple[np.ndarray, np.ndarray]:
    if case_id == "medium_gradient":
        top = np.array([245, 232, 220], dtype=np.float32)
        bottom = np.array([178, 198, 224], dtype=np.float32)
        rows = np.linspace(0.0, 1.0, HEIGHT, dtype=np.float32)[:, None, None]
        image = np.repeat(top[None, None, :] * (1 - rows) + bottom[None, None, :] * rows, WIDTH, axis=1)
    else:
        image = np.full((HEIGHT, WIDTH, 3), 255, dtype=np.uint8)
        if case_id == "medium_halftone":
            for y in range(180, 710, 18):
                for x in range(45, 595, 18):
                    cv2.circle(image, (x, y), 2, (175, 175, 175), -1, cv2.LINE_8)

    image = np.clip(image, 0, 255).astype(np.uint8)
    protected = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)

    # Panel frame and case-specific protected line art.
    cv2.rectangle(image, (42, 46), (598, 850), (28, 28, 28), 4, cv2.LINE_AA)
    if case_id == "easy_balloon":
        cv2.ellipse(image, (320, 444), (220, 150), 0, 0, 360, (20, 20, 20), 4, cv2.LINE_AA)
        cv2.ellipse(protected, (320, 444), (220, 150), 0, 0, 360, 255, 4, cv2.LINE_AA)
    elif case_id == "medium_gradient":
        cv2.line(image, (64, 650), (580, 570), (35, 35, 35), 5, cv2.LINE_AA)
        cv2.line(image, (90, 690), (540, 622), (80, 80, 80), 2, cv2.LINE_AA)
        cv2.circle(image, (500, 250), 74, (48, 48, 48), 3, cv2.LINE_AA)
        cv2.circle(protected, (500, 250), 74, 255, 3, cv2.LINE_AA)
    elif case_id == "medium_halftone":
        cv2.ellipse(image, (320, 455), (245, 170), 0, 0, 360, (25, 25, 25), 4, cv2.LINE_AA)
        cv2.ellipse(protected, (320, 455), (245, 170), 0, 0, 360, 255, 4, cv2.LINE_AA)
    elif case_id == "hard_line_art":
        for offset in range(-180, 220, 32):
            cv2.line(image, (100 + offset, 230), (470 + offset, 650), (35, 35, 35), 3, cv2.LINE_AA)
        cv2.ellipse(image, (500, 265), (58, 78), 0, 0, 360, (20, 20, 20), 4, cv2.LINE_AA)
        cv2.ellipse(protected, (500, 265), (58, 78), 0, 0, 360, 255, 4, cv2.LINE_AA)
    else:  # extreme_sfx: dense motion hatching beside protected character art.
        for offset in range(-100, 360, 20):
            cv2.line(image, (120 + offset, 170), (330 + offset, 650), (25, 25, 25), 2, cv2.LINE_AA)
        cv2.circle(image, (505, 510), 65, (18, 18, 18), 4, cv2.LINE_AA)
        cv2.ellipse(image, (505, 510), (30, 42), 0, 0, 360, (25, 25, 25), 3, cv2.LINE_AA)
        cv2.circle(protected, (505, 510), 69, 255, 5, cv2.LINE_AA)
        cv2.ellipse(protected, (505, 510), (30, 42), 0, 0, 360, 255, 4, cv2.LINE_AA)
    return image, protected


def build_case(case_id: str, text: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    clean, protected = make_background(case_id)
    source = clean.copy()
    glyph = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    scale = 1.18 if case_id not in {"hard_line_art", "extreme_sfx"} else 1.65
    thickness = 3 if scale < 1.5 else 5
    x = 160 if case_id not in {"hard_line_art", "extreme_sfx"} else 145
    y = 448 if case_id != "extreme_sfx" else 462
    font = cv2.FONT_HERSHEY_DUPLEX if case_id != "extreme_sfx" else cv2.FONT_HERSHEY_TRIPLEX
    cv2.putText(glyph, text, (x, y), font, scale, 255, thickness, cv2.LINE_AA)

    # SFX has a white outer stroke; both glyph and outline are in the authorized
    # text geometry. The remaining dilation is a fixed reconstruction halo.
    if case_id in {"hard_line_art", "extreme_sfx"}:
        cv2.putText(source, text, (x, y), font, scale, (255, 255, 255), thickness + 8, cv2.LINE_AA)
        cv2.putText(source, text, (x, y), font, scale, (8, 8, 8), thickness, cv2.LINE_AA)
        cv2.putText(glyph, text, (x, y), font, scale, 255, thickness + 8, cv2.LINE_AA)
    else:
        cv2.putText(source, text, (x, y), font, scale, (12, 12, 12), thickness, cv2.LINE_AA)

    mask = cv2.dilate(glyph, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)), iterations=1)
    overlay = np.any(source != clean, axis=2)
    overlay_outside = int(overlay[mask == 0].sum())
    overlap = int(np.logical_and(mask > 0, protected > 0).sum())
    if overlay_outside:
        raise RuntimeError(f"{case_id}:overlay_pixels_outside_mask={overlay_outside}")
    if overlap:
        raise RuntimeError(f"{case_id}:authorized_mask_overlaps_protected_art={overlap}")
    return source, mask, clean, protected, glyph


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None, help="new output directory; must not already exist")
    args = parser.parse_args()
    if args.output is None:
        out = Path(tempfile.mkdtemp(prefix="yomu-synthetic-clean-set-"))
    else:
        out = args.output
        out.mkdir(parents=True, exist_ok=False)

    manifest = {
        "schema": "yomu-synthetic-clean-benchmark.v1",
        "synthetic_only": True,
        "dimensions": [WIDTH, HEIGHT],
        "split_policy": "calibration and selection may guide; holdout is frozen and must not tune parameters",
        "cases": [],
    }
    preview = Image.new("RGB", (WIDTH * 3, HEIGHT * len(CASES)), "white")
    for row, (case_id, category, split, text) in enumerate(CASES):
        source, mask, clean, protected, glyph = build_case(case_id, text)
        case_dir = out / case_id
        case_dir.mkdir()
        items = {
            "source.png": source,
            "authorized_mask.png": mask,
            "ground_truth_clean.png": clean,
            "protected_art_mask.png": protected,
            "glyph_mask.png": glyph,
        }
        files = {}
        for name, array in items.items():
            path = case_dir / name
            Image.fromarray(array).save(path)
            payload = path.read_bytes()
            files[name] = {"bytes": len(payload), "sha256": digest(payload)}
        preview.paste(Image.fromarray(source), (0, row * HEIGHT))
        preview.paste(Image.fromarray(cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)), (WIDTH, row * HEIGHT))
        preview.paste(Image.fromarray(clean), (WIDTH * 2, row * HEIGHT))
        manifest["cases"].append({
            "id": case_id,
            "category": category,
            "split": split,
            "synthetic_text": text,
            "authorized_mask_pixels": int(np.count_nonzero(mask)),
            "protected_art_pixels": int(np.count_nonzero(protected)),
            "overlay_pixels_outside_authorized_mask": 0,
            "authorized_mask_protected_art_overlap": 0,
            "files": files,
        })

    preview.save(out / "dataset_preview.png")
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    archive = out.with_suffix(".zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(p for p in out.rglob("*") if p.is_file()):
            info = zipfile.ZipInfo(path.relative_to(out).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            zf.writestr(info, path.read_bytes())
    print(json.dumps({
        "dataset_dir": str(out),
        "archive": str(archive),
        "archive_sha256": digest(archive.read_bytes()),
        "dataset_size": len(manifest["cases"]),
        "ground_truth_cases": len(manifest["cases"]),
        "tuning_cases": sum(c["split"] != "holdout" for c in manifest["cases"]),
        "holdout_cases": sum(c["split"] == "holdout" for c in manifest["cases"]),
        "all_mask_gates_pass": all(
            c["overlay_pixels_outside_authorized_mask"] == 0
            and c["authorized_mask_protected_art_overlap"] == 0
            for c in manifest["cases"]
        ),
        "manifest": str(manifest_path),
        "preview": str(out / "dataset_preview.png"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
