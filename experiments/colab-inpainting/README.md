# Colab inpainting experiment harness

This folder contains isolated research assets. It does not modify the Yomu production pipeline or run model inference automatically.

## Current evidence

- The owner-provided `Yomu_Big_LaMa_Colab_Benchmark_V4` notebook records one real Anime-Manga Big-LaMa inference on a Tesla T4 using an owner-authorized test page. The output preserved pixels outside the mask but failed visual review on the `BAM` SFX region. Do not repeat that page/model run.
- One separate local CPU Big-LaMa inference on a synthetic line-art fixture removed the overlay and preserved all outside-mask pixels. It is a single easy case, not a GPU comparison or model-level approval. Its reproduction script is `run_big_lama_cpu_smoke.py`.
- A deterministic five-case synthetic dataset generator is `build_synthetic_benchmark.py`. It produces one calibration case, three selection cases, and a reserved extreme holdout, with source/mask/clean ground truth/protected-art mask and per-file hashes. It was generated twice with identical archive hash.
- `run_big_lama_colab_smoke.py` is prepared to run exactly one selected non-holdout case in Colab. It has not been executed; it requires an active, resource-authorized GPU runtime and explicit confirmation flags. It verifies the checkpoint SHA-256 before loading and never iterates or retries.
- `yomu_inpainting_benchmark.ipynb` is a guarded generic harness with strict compositing and metric gates; it is not itself a Colab execution connection.
- `yomu_real_manga_colab_v1.ipynb` now uses a private Drive folder (`Yomu Colab Research`) for hash-pinned input sync and unique, non-overwriting result folders. A persistent one-shot lock prevents an automatic duplicate inference after interruption. Normal Colab Drive authorization may still be required. The four inference booleans remain false; no inference is triggered by opening or preparing the notebook.
- `colab_drive_sync.py` validates the reviewed input ZIP locally before it is sent through the Google Drive connector and validates a downloaded result folder using its artifact manifest. It does not contact external services or carry credentials.
- The Google Drive connector successfully uploaded the current input bundle to the private research folder; SHA-256 and byte count are recorded in the task report. Drive sharing was not changed.
- `colab_drive_sync.py inspect-candidates <zip>` validates user-supplied image-only PNG archives without extraction, reports per-image dimensions/SHA-256, and returns `PASS_MASKS_REQUIRED` rather than treating unmasked images as inference-ready. The current 11-image candidate ZIP is in the same private Drive folder; its images still require individually reviewed masks before any run.

## Resource and rights gates

The current Colab runtime liveness is not observable from this Codex session because no Colab execution/runtime tools are exposed. Keep the runtime connected as requested; do not start a run until the active runtime/GPU is confirmed in Colab. The owner has authorized use of credits for this evaluation, but this does not grant the unresolved checkpoint redistribution/commercial rights. Do not enable an upgraded plan, buy units, or launch larger hardware.

The Big-LaMa checkpoint size/hash are pinned. Sanster's model release links to `dreMaz/AnimeMangaInpainting`, whose model card declares MIT; the exact training-data provenance is not independently documented here. Keep this experiment research-only, do not package weights into Yomu, and retain the owner acknowledgment gate. Preserve safety/composition checks and human visual review. Never use private Yomu pages in the synthetic dataset.

See `../../docs/research/colab-clean-models/MASTER_BENCHMARK_STATE.md` for the current evidence and ranking status.
