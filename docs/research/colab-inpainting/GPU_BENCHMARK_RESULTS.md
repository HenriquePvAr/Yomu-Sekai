# GPU inpainting benchmark results

## Status: one synthetic T4 smoke; quality gate failed closed

One authenticated Colab T4 runtime and one synthetic-image inference were used. No Yomu/project image was uploaded, and no Gemini, DeepL, YK, or Google AI API was called. The inference output was blocked by the checkpoint's safety checker, which returned a black image; it is not a valid clean result. No retry was made. There is no model winner and no quality or page-throughput result.

| Measure | Result | Evidence state |
|---|---:|---|
| GPU model / VRAM | Tesla T4 / 15,360 MiB | Colab runtime telemetry |
| System RAM | 13.61 GiB total; 12.67 GiB reported available | Runtime telemetry |
| Model download | 2.74 GB, 16 files | Pinned checkpoint revision below |
| Cold model load | 30.734 s | One run |
| Inference | 6.001 s; 512×512, 12 steps, seed 20261019 | One synthetic image; safety checker blocked output |
| Peak allocated/reserved VRAM | 3,416,621,568 / 3,716,153,344 bytes | CUDA peak counters |
| Compute units before/after | `NOT_AVAILABLE` | Exact account balance/delta not exposed in the inspected UI |
| Quality / OCR residual / line-art preservation | `NOT_VALIDATED` | Safety checker returned black image; no retry |
| Pages/minute | `NOT_MEASURED` | No per-page runs |
| 50 / 100 / 200 page chapter estimates | `NOT_ESTIMATED` | No comparable sample timings; no extrapolation justified |

Notebook and execution record: [Yomu_Inpainting_Synthetic_T4_Smoke](https://colab.research.google.com/drive/1uRo12M1RIlUn8X7WdiZOgnTQSW3qYQyd). It used `stable-diffusion-v1-5/stable-diffusion-inpainting` at revision `8a4288a76071f7280aedbdb3253bdb9e9d5d84bb` (CreativeML OpenRAIL-M; legal/commercial review required before any Yomu integration). Model load succeeded after an isolated runtime-only `torchao==0.18.0` compatibility install and runtime restart. The safety checker was preserved and not bypassed. Synthetic source SHA-256: `4f6b10b5795e10901af3cff54a9af76840fa06415d0cbbcc48474a36e1f29260`; mask: `1a762e3794e62f17f55268cbcd5f3abdba8c24ae37d0ab152bd7639a2e34d95f`; blocked donor: `e9c4a470ad900801f7de4f9402eb27af8a1cc00eac80d618ef16bac39fb27d33`; composed output: `897c7f95bfc5179ea41a4f3cda5b03a644e41efd8ad85424387f8b1cb35ae257`.

Composition check: `outside_mask_changed_pixels=0` proves only that the compositor honored the mask boundary. The donor was black, so `text_removal_semantically_verified=false`; no Clean-quality or model acceptance claim follows from that pixel-boundary check.

## Prior experiment that is not an inpainting benchmark

The existing isolated `experiments/kaggle_qwen_fallback_lab` reports one Kaggle run of **Qwen3-VL-8B-Instruct** at 161.901 s including load/inference. That experiment is an image/text fallback lab, not masked inpainting, not a Colab run, and not comparable to page-clean throughput. It is explicitly excluded from model rankings.

## Next gate

The authorized one-image run is complete. Because its output was blocked, do not retry or disable the safety checker under this authorization. A further inference requires a fresh owner decision on the model/fixture and compute budget. Before product use, resolve OpenRAIL-M terms and verify checkpoint provenance. The Colab T4 runtime was shut down after the run.

## Comparison template

| model@revision | image/mask hash | GPU/VRAM | load s | infer s | peak VRAM | CU delta | outside-mask pixels | OCR residual | visual review |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| pending | pending | pending | — | — | — | — | — | — | — |
