# Reproducible clean-reconstruction benchmark protocol

Status: **five-case synthetic set prepared; GPU comparison not executed**. The connected Colab runtime has not been verified through a supported tool in this session. Keep it connected as requested. Do not claim GPU telemetry or start another inference until an authorized Colab execution path/resource state is verified.

## Dataset and split

- Use only synthetic, owned, or explicitly licensed page-like artwork. Keep private pages/artifacts outside Git and public reports.
- Prefer a clean source plus deterministic synthetic text/SFX overlays, yielding known `GROUND_TRUTH_CLEAN`, `TEXT_OVERLAY_IMAGE`, and `AUTHORIZED_MASK`.
- Label each case EASY / MEDIUM / HARD / EXTREME; hold out cases before prompt, mask, or parameter tuning. Extreme ambiguity may correctly resolve to `REVIEW_REQUIRED`.
- Record source hashes, dimensions, color mode, overlay/font/seed, mask hash, split, and ownership/rights notes.
- Do not use one repeatedly tuned fixture as an independent benchmark.
- Reproducible generator: `experiments/colab-inpainting/build_synthetic_benchmark.py`; the current set has one calibration case, three selection cases, and one sealed extreme holdout. Its manifest asserts zero overlay pixels outside each authorized mask and zero overlap with protected-art masks.

## Frozen comparison contract

For every evaluated candidate use the same input, mask, resolution, color conversion, and final compositor. Record the exact model revision, weight file and SHA-256, code commit, dependency lock, precision, scheduler/settings, seed, and any prompt/task mode. Run the Yomu current Clean path as the mandatory control. Keep image-editing-only systems in a separate track unless they demonstrably accept and honor the same binary mask.

The model may propose pixels, but `FINAL_COMPOSITE` must take candidate pixels only within `AUTHORIZED_MASK` and preserve the source everywhere else. Verify dimensions/channels and count outside-mask changes exactly; any nonzero value rejects the artifact. This gate is independent of visual quality and text-removal success.

## One-image smoke gate

Before a larger benchmark, run at most one synthetic case per candidate only after artifact rights, revision/hash, runtime GPU, available memory, and resource authorization are verified. Measure model download/load separately from inference; record wall time, peak allocated/reserved VRAM, peak host RAM, resolution, OOM/error, output hash, and environment versions. Do not install paid resources, alter account billing, call paid APIs, or launch parallel model loads.

Review the original, mask, raw model output, and strict final composite at native size and enlarged crops. Record separately:

- target text residuals/ghosts and target removal verdict;
- reconstruction continuity, line/halftone/texture fidelity, halos/seams, and invented detail;
- protected-art damage and outside-mask pixel counts;
- machine metrics against ground truth (only when clean ground truth exists) and subjective human review;
- `PASS`, `FAIL`, or `REVIEW_REQUIRED` with a concrete reason.

No single metric or attractive crop establishes overall success. Do not claim a model winner until there are varied cases, an untouched holdout, baseline comparison, and adequate review coverage.

## Scale-up and reporting

The five-case varied set is prepared after one acceptable easy synthetic CPU smoke; its holdout remains sealed from tuning. Before model execution, verify runtime, artifact rights, and resource authorization. Keep cases/masks/compositor identical across models and serialize large models on one GPU. Record throughput as measured; never extrapolate chapter throughput from one image. A 40–80 GB GPU comparison is a later gate, not an automatic next run. `run_big_lama_colab_smoke.py` is a one-image-only runner and must not be looped over the set.

Final report must distinguish: research performed, weights downloaded, models loaded, inferences executed, visually accepted cases, rejected cases, and unmeasured fields. Preserve raw output and final composite privately; do not check in weights or private manga. No production integration, YK, DeepL, Gemini, paid provider, or chapter job is part of this protocol.
