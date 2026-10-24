# Benchmark results ledger

Completed inference runs are listed here, separated by hardware and evidence type. The recorded local CPU smoke ran in an earlier continuation; this continuation generated the varied synthetic set and prepared, but did not execute, a Colab runner.

| Model | Run status | Input | Load / inference | Peak GPU memory | Outside-mask changes | Visual verdict |
|---|---|---:|---:|---:|---:|---|
| Anime-Manga Big-LaMa (saved Colab execution) | One successful inference on the owner-provided test page; keep input/output private | Tesla T4; 795×960; download 6.1 s | 0.943 s load / 3.0492 s inference | 228,058,112 B allocated; 262,144,000 B reserved | 0; 4,895 changed within 5,123 mask pixels | FAIL: `BAM` SFX target has conspicuous black-streak artifacts |
| Anime-Manga Big-LaMa (local CPU control) | One deterministic synthetic line-art/text-overlay fixture with clean ground truth | CPU; 640×896; 20,358-pixel rectangular mask | 6.143 s load / 5.977 s inference; 12.179 s wall including lazy load | Not applicable | 0; masked MAE 3.57, RMSE 18.49, PSNR 22.79 dB | Single easy fixture visually acceptable; not sufficient for a model win |
| Stable Diffusion 1.5 Inpainting | Historical T4 smoke; not repeated | 512×512, 12 steps | 30.734 s / 6.001 s | approximately 3.18 GiB allocated | 0 | FAIL: safety checker produced a black donor; protection was not bypassed |

These runs used different inputs, resolutions, model families, and configurations; their times are not a fair speed comparison. Outside-mask equality certifies compositor behavior only, not removal quality or fidelity.

On the same synthetic source and mask, the Yomu OpenCV Telea primitive (radius 3) scored masked MAE 10.48, RMSE 34.94, and PSNR 17.26 dB. This is a primitive baseline only, not the complete Yomu candidate-selection/worker path. One fixture cannot establish generalization or beat the production baseline.

## Coverage and ranking

- New Colab model runs in this mission continuation: **0**; one local CPU Big-LaMa smoke was executed.
- Single-image outputs reviewed: **3** (two historical T4 smokes and one synthetic CPU sample).
- Synthetic ground-truth cases with model output: **1**; independent holdout cases: **0**.
- Prepared varied synthetic set: **5** cases (1 calibration, 3 selection, 1 reserved extreme holdout); no model outputs on this set yet.
- Untouched holdout cases: **0**.
- Visually acceptable individual samples: **1 easy synthetic CPU case**; accepted models/winners: **0**.
- Valid model ranking: **NONE / PROVISIONAL_NOT_RANKED**.
- Comparative throughput, representative latency, and confidence intervals: **NOT_MEASURED**.

The saved Colab notebook and local smoke both verified checkpoint SHA-256 `479d3afdcb7ed2fd944ed4ebcc39ca45b33491f0f2e43eb1000bd623cfb41823` (205,717,870 bytes). The hash establishes identity only; checkpoint redistribution/use-rights review remains open. The local synthetic evidence is outside Git at `%TEMP%/yomu-big-lama-cpu-62u349j6/`; the owner's private page remains excluded from the repository.

The new synthetic set is generated outside Git by `experiments/colab-inpainting/build_synthetic_benchmark.py`. Its deterministic archive was produced twice with the same SHA-256 `fecc96834bb46ec357219740ebc6f465c3d2d8db5147dcd64b434c30f795b8bc`; the current copy is `%TEMP%/yomu-synthetic-clean-set-o1lzhcgm.zip`. No model was run on these five cases.
