# Yomu Sekai clean reconstruction benchmark — current state

**Mission:** `YOMU_SEKAI_COLAB_AI_CLEAN_RECONSTRUCTION_BENCHMARK_V1`
**Result:** `PARTIAL`
**Scope:** research only; production pipeline unchanged.

## Execution boundary

The connected Google Drive tool provided read-only access to the saved Colab notebook `Yomu_Big_LaMa_Colab_Benchmark_V4`. Its saved outputs prove one successful Anime-Manga Big-LaMa inference on a Tesla T4. Current runtime liveness, free VRAM, RAM, CUDA driver, and Colab unit/billing state remain unverified. The user asked to keep the runtime connected; it was not disconnected. A local CPU synthetic inference ran in an earlier continuation; this continuation generated a five-case synthetic dataset and prepared a runner without starting any Colab/model inference or paid resource.

The saved Colab notebook contains one successful model inference on an owner-provided test page, plus an earlier parse-time `IndentationError` execution that did not enter inference. The separate Stable Diffusion 1.5 T4 smoke is historical. The fixtures/settings differ, so their latency is not comparable.

## Recorded runs

| Model | Evidence | Runtime / settings | Integrity | Visual result | Decision |
|---|---|---|---|---|---|
| Anime-Manga Big-LaMa | Saved Colab execution; owner-provided page, kept private | Tesla T4; 795×960; download 6.1 s; load 0.943 s; infer 3.0492 s; peak allocated/reserved 228,058,112 / 262,144,000 bytes | Outside-mask changed pixels: 0; 4,895 changed within 5,123-pixel mask | `FAIL`: target `BAM` SFX region is replaced with conspicuous black streaks; not a usable reconstruction | Reject as winner; exactly one successful inference |
| Anime-Manga Big-LaMa | Local CPU smoke; synthetic line-art with known ground truth | CPU; 640×896; load 6.143 s; infer 5.977 s; total wall 12.179 s; RSS after run 701,403,136 bytes (not peak) | Outside-mask changed pixels: 0; masked MAE/RMSE/PSNR 3.57 / 18.49 / 22.79 dB | `PASS_FOR_THIS_SIMPLE_FIXTURE_ONLY`: text gone; circle/lines visually reconstructed with small pixel error | One sample; no GPU comparison; no model winner |
| Stable Diffusion 1.5 Inpainting | Existing notebook and `docs/research/colab-inpainting/GPU_BENCHMARK_RESULTS.md` | T4; 512×512; 12 steps; load 30.734 s; infer 6.001 s | Outside-mask changed pixels: 0 | `FAIL`: safety checker returned a black donor | Rejected; protections remain enabled |

On the same synthetic source and mask, the Yomu OpenCV Telea primitive (radius 3) scored masked MAE/RMSE/PSNR 10.48 / 34.94 / 17.26 dB. This is not the full Yomu candidate-selection pipeline. A one-fixture improvement is not evidence for replacement or routing.

For Big-LaMa, the pinned checkpoint is 205,717,870 bytes with SHA-256 `479d3afdcb7ed2fd944ed4ebcc39ca45b33491f0f2e43eb1000bd623cfb41823`; the saved notebook records the matching size/hash before loading. The Yomu descriptor already records the checkpoint's public-redistribution license review as open. A successful hash check establishes byte identity, not rights to distribute or commercially use the weights.

`outside_mask_changed_pixels=0` proves the final compositor preserved pixels outside the mask. It does not prove text removal, fidelity, or overall image quality.

## Existing Yomu baseline

The comparison already documented in `docs/research/colab-inpainting/INPAINTING_MODELS_COMPARISON.md` identifies the current OpenCV patch-synthesis/reconstruction path as the production baseline and the SHA-verified TorchScript LaMa adapter as optional. Both remain unchanged. The adapter fails closed when weights are unavailable or their hash is wrong; an experimental model must not be enabled as production behavior from this benchmark alone.

## Benchmark status

- Dataset cases with actual outputs reviewed: 3 single-image runs, including 2 historical T4 smokes and 1 local synthetic CPU smoke; not a balanced benchmark set.
- Clean ground-truth cases with model output: 1 synthetic case; no ground truth for the historical runs.
- Prepared synthetic set: 5 cases (1 calibration, 3 selection, 1 extreme holdout), none run through a model; the earlier CPU case is a separate smoke fixture.
- Independent holdout model outputs: 0.
- Individual visually acceptable outputs: 1 simple synthetic CPU case; no model has enough evidence for an overall quality claim.
- Model ranking / winners: none; `PROVISIONAL_NOT_RANKED`.
- Pages/minute, chapter throughput, representative median/worst-case score, and statistically meaningful comparison: `NOT_MEASURED`.
- YK, DeepL, paid Gemini/image API calls, production writes, and new Colab resource provisioning: 0.

## Shortlist and gates

See [MODEL_SHORTLIST.md](MODEL_SHORTLIST.md), [MODEL_LICENSE_MATRIX.md](MODEL_LICENSE_MATRIX.md), and [BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md). The PowerPaint v2.1 model card currently labels the model artifact Apache-2.0; MAT's official repository says its code and models are for research purposes only. Neither fact alone clears an entire code/weights/base/dependency stack for commercial integration.

The current pinned official PowerPaint app path is not approved for this benchmark: it disables the safety checker and deserializes a `.bin` component with `torch.load`. The inspected SDXL inpainting snapshot has safe-tensor weights but no safety-checker component. Neither is eligible to run under the current preserve-safety gate until the missing safe checker/adapter is supplied and validated.

The evidence log is [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md); current environment visibility is [COLAB_ENVIRONMENT.md](COLAB_ENVIRONMENT.md). No model is ranked as a winner: the T4 page smoke and separate SD 1.5 smoke failed quality/safety acceptance; one easy synthetic CPU sample is insufficient to establish a winner or GPU comparison.

Before another Colab inference, verify that the existing runtime is still active and free/authorized for the intended run, record the account-visible unit state without exposing account data, and run only a single synthetic case per model. Preserve safety filters. Do not use a private manga page as a public example or upload it unless separately cleared.

## Reproducibility entrypoints

- Existing guarded notebook: `experiments/colab-inpainting/yomu_inpainting_benchmark.ipynb`.
- Deterministic 5-case dataset generator: `experiments/colab-inpainting/build_synthetic_benchmark.py`; the generated archive checksum and split are in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).
- One-image Colab runner (prepared, not executed): `experiments/colab-inpainting/run_big_lama_colab_smoke.py`; it requires two explicit confirmation flags and refuses batch/holdout execution.
- Existing experiment notes: `experiments/colab-inpainting/README.md`.
- Existing Yomu integration proposal: `docs/research/colab-inpainting/YOMU_GPU_INTEGRATION_PROPOSAL.md`.
- The private Colab page/output must not be copied into Git; see [VISUAL_REVIEW.md](VISUAL_REVIEW.md) and [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for sanitized evidence.
- Model ranking remains explicitly provisional: [MODEL_RANKING.md](MODEL_RANKING.md).

The local guarded notebook remains synthetic-only. The one-image Colab runner is prepared but unexecuted because this host has no Colab execution MCP. The local CPU smoke script, [run_big_lama_cpu_smoke.py](../../../experiments/colab-inpainting/run_big_lama_cpu_smoke.py), records source, mask, ground truth, raw donor, final composite, hashes, and metrics outside Git. One Big-LaMa inference completed on CPU; outside-mask changes were zero and that single simple sample looked acceptable, but it is not a Colab result or model-level pass. The saved Colab notebook contains the separate private-page T4 inference summarized above.

## Remaining external gate

One simple synthetic CPU sample is promising, while the T4 SFX/page sample failed. The current Colab runtime/compute-unit state is unknown and this Codex host exposes Drive read-only, not Colab execution tools. Next, run the same deterministic fixture on Colab only after a verified execution path, runtime/resource state, and model artifact gates are available; do not repeat the private Big-LaMa page test or SD 1.5 smoke.
