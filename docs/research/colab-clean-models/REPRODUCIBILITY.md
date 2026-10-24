# Reproducibility record

## Existing saved Colab run

- Notebook title: `Yomu_Big_LaMa_Colab_Benchmark_V4` (the owner-provided Google Drive notebook; its private link is recorded in `COLAB_ENVIRONMENT.md`).
- Model: Yomu Anime-Manga Big-LaMa TorchScript checkpoint.
- Public checkpoint source: `https://github.com/Sanster/models/releases/download/AnimeMangaInpainting/anime-manga-big-lama.pt`.
- Expected checkpoint size: 205,717,870 bytes.
- Expected SHA-256: `479d3afdcb7ed2fd944ed4ebcc39ca45b33491f0f2e43eb1000bd623cfb41823`.
- Saved Colab output verified the size and hash before `torch.jit.load`.
- Runtime snapshot: Tesla T4; Python 3.13.15; PyTorch 2.11.0+cu130; total VRAM 15,637,086,208 bytes.
- Input: one owner-provided test page and one aligned mask, 795×960. The image itself and its hashes are omitted here to avoid publishing private test material.
- One actual inference completed: 3.0492 s; peak torch allocated/reserved VRAM 228,058,112 / 262,144,000 bytes. Checkpoint download/load were 6.1 / 0.943 s.
- A preceding notebook cell execution failed with `IndentationError` before executing its body; the subsequent corrected execution completed one inference. It was not a second model generation.
- The successful code saves `source.png`, `mask.png`, `raw_model_output.png`, `final_composite.png`, and `mask_overlay.png` under `/content/yomu_big_lama_v4/evidence/`, and displays a contact sheet. The saved notebook retains the displayed montage; the ephemeral `/content` files have not been independently retrieved or hash-verified.

## Reproduction constraints

- Do not rerun the same page/model inference. The visual result failed.
- Do not use private test images as public benchmark material.
- The checkpoint's redistribution/use rights remain unresolved even though its bytes are hash-pinned.
- The saved notebook did not record RAM, free VRAM, CUDA driver/runtime version, Colab compute-unit state, or paid/free resource status.
- The local guarded Colab harness is `experiments/colab-inpainting/yomu_inpainting_benchmark.ipynb`; the CPU script below is a separate, local-only run.

## Local CPU synthetic control

- Command: `python experiments/colab-inpainting/run_big_lama_cpu_smoke.py` from the repository root.
- The script performs no network access, requires the already-present Yomu-configured checkpoint, verifies its SHA-256 through the product adapter, and writes evidence to a fresh `%TEMP%/yomu-big-lama-cpu-*` directory.
- Fixture: deterministic 640×896 synthetic panel/ellipse/line art, overlaid `SYNTHETIC TEST`, rectangular authorized mask; the clean source is ground truth and the script asserts zero overlay pixels outside the mask.
- One CPU inference completed at `%TEMP%/yomu-big-lama-cpu-62u349j6`; SHA-256 matched `479d3afdcb7ed2fd944ed4ebcc39ca45b33491f0f2e43eb1000bd623cfb41823` and file size was 205,717,870 bytes.
- Load 6.143 s; inference 5.977 s; wall including lazy load 12.179 s; process RSS after run 701,403,136 bytes (not peak). No GPU used.
- Outside-mask changed pixels: 0. Masked MAE/RMSE/PSNR: 3.57 / 18.49 / 22.79 dB. Human visual review found this simple sample acceptable, but it is one easy synthetic case only.
- Same-mask OpenCV Telea primitive baseline: MAE/RMSE/PSNR 10.48 / 34.94 / 17.26 dB. This is not the entire Yomu local-candidate pipeline.
- Comparison image: `%TEMP%/yomu-big-lama-cpu-62u349j6/comparison.png`. No private input was used or copied into Git.

## Five-case synthetic dataset and Colab runner

- Generate the dataset: `python experiments/colab-inpainting/build_synthetic_benchmark.py`.
- Cases: `easy_balloon` (calibration), `medium_gradient` (selection), `medium_halftone` (selection), `hard_line_art` (selection), and `extreme_sfx` (reserved holdout). Every case has source, authorized mask, clean ground truth, protected-art mask, and glyph mask.
- The manifest records per-file SHA-256/size, case category/split, mask pixel count, and asserts zero overlay pixels outside the authorized mask and zero authorized-mask/protected-art overlap.
- The archive generated twice identically: SHA-256 `fecc96834bb46ec357219740ebc6f465c3d2d8db5147dcd64b434c30f795b8bc`; current copy `%TEMP%/yomu-synthetic-clean-set-o1lzhcgm.zip`. Dataset preview: `%TEMP%/yomu-synthetic-clean-set-fl8egofu/dataset_preview.png`.
- One-image Colab runner: `experiments/colab-inpainting/run_big_lama_colab_smoke.py`. It validates the dataset archive and input hashes, refuses overwrites/holdout/batch, requires explicit flags, verifies checkpoint size/SHA-256 before TorchScript load, measures actual GPU/runtime fields, composites only inside the authorized mask, and writes a report plus PNG evidence. It has **not** been run; the Colab runtime and compute-unit state remain unverified.
