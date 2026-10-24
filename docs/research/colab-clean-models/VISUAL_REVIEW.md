# Visual review — Anime-Manga Big-LaMa T4 smoke

**Verdict: FAIL for clean quality.** This is a review of the saved display output from `Yomu_Big_LaMa_Colab_Benchmark_V4`, not a new run.

- The input was the owner-provided manga test page uploaded for this experiment. The page and image outputs remain private and are intentionally not stored in this repository.
- The authorized mask selects the `BAM` sound-effect region at the top-right of the first panel. The saved montage shows the source, mask, raw output, and strict final composite.
- In the raw and final panels, the SFX glyphs are replaced by conspicuous dark/black streaks rather than a plausible reconstruction of the underlying panel art. This is a visible failure, not an acceptable removal.
- The saved metrics report `outside_mask_changed_pixels=0`, `inside_mask_changed_pixels=4895`, and `mask_pixels=5123`. That proves the compositor limited changes to the mask; it does not redeem the in-mask artifacts.
- The original source, mask, raw donor, and final composite are written by the notebook code under `/content/yomu_big_lama_v4/evidence/`. Their durable export/continued availability was not independently verified. The Drive notebook's saved display output is the available visual evidence.
- No clean ground truth exists for this page/mask. OCR residuals, PSNR/SSIM, and objective reconstruction fidelity are therefore **NOT_MEASURED**.

**Decision:** Big-LaMa is not a winner. Do not repeat this same inference. A different predeclared synthetic case with known clean ground truth is required to evaluate another candidate; first clear checkpoint rights and runtime/resource gates.

## Separate local CPU synthetic control

The reproducible local script `experiments/colab-inpainting/run_big_lama_cpu_smoke.py` was run once against the same configured, hash-verified checkpoint, on a synthetic 640×896 line-art fixture with known clean ground truth. It is separate from the private T4 page result above and is not a GPU/Colab run.

- The visible `SYNTHETIC TEST` overlay was removed. The circular line art and surrounding panel geometry are largely continuous in the final composite; minor in-mask pixel differences remain.
- The exact compositor changed **0** pixels outside the authorized mask. The known text overlay was fully inside the mask.
- Against the clean ground truth, masked MAE/RMSE/PSNR were 3.57 / 18.49 / 22.79 dB. On the same image/mask, the OpenCV Telea primitive scored 10.48 / 34.94 / 17.26 dB; this primitive comparison is not a full Yomu pipeline benchmark.
- This single easy synthetic sample is an individual visual success, not enough to overcome the T4 SFX failure, resolve checkpoint rights, establish a GPU comparison, or declare Big-LaMa a winner.
- Evidence is kept locally outside the repository at `%TEMP%/yomu-big-lama-cpu-62u349j6/comparison.png`; artifacts include source, mask, ground truth, raw donor, final, and a JSON report.
