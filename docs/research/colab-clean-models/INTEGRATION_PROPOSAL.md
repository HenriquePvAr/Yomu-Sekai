# Yomu inpainting integration proposal

Status: **research proposal only; no model is approved for product integration**.

## Current boundary

The existing product adapter is `yomu/clean/inpainting/advanced_art_inpainting.py`. It loads the pinned Anime-Manga Big-LaMa TorchScript file only after checking its expected size/hash, uses a `uint8` mask where nonzero means “remove/reconstruct”, and composites the donor only inside that mask. Missing or mismatched weights fail closed. The checkpoint's redistribution/use rights remain unresolved. One private-page T4 inference failed visual review; one separate easy CPU synthetic case was acceptable, but that is not broad validation or a GPU comparison. Neither result makes this adapter/checkpoint a recommended winner or commercial deployment choice.

## Candidate contract (future, gated)

Any future candidate should implement the existing adapter boundary rather than create a parallel cleaner:

- Input: immutable source image, same-size single-channel authorized mask, and a provenance record identifying page/region ownership and mask hash.
- Mask semantics: nonzero pixels are eligible for reconstruction; empty, mismatched-size, non-finite, or ambiguous masks are rejected before model execution.
- Output: same-size RGB/BGR donor plus model ID, immutable code/weight revision, artifact SHA-256, precision, seed/configuration, device, load/inference timings, and bounded memory telemetry.
- Composition: the source remains authoritative outside the authorized mask. Compare the final composite against the source there and reject on any changed pixel; do not trust a model's claimed mask adherence.
- Quality: text-removal evidence, boundary review, protected-art review, and a human `REVIEW_REQUIRED` outcome for uncertain ownership or reconstruction. A clean artifact is not verified merely because a file was written.
- Failure: timeout, OOM, unavailable weights, invalid output, or failed quality gate produces explicit review/failure state; never silently return the source as a successful clean.

## Evaluation gate before product work

1. Clear exact code, checkpoint, base-model, and dependency terms for the intended use.
2. Evaluate on synthetic overlays with known clean ground truth, identical masks, calibration/selection/holdout separation, and a frozen Yomu baseline.
3. Require both pixel-exact outside-mask preservation and visual acceptance of text removal, line art, texture, and protected art.
4. Repeat across easy, medium, hard, and extreme cases; keep ambiguous ownership as `REVIEW_REQUIRED`.
5. Compare speed, peak VRAM/RAM, load time, failures, and quality on the same hardware/settings. Do not extrapolate a single T4 result to chapter throughput.
6. Only after the benchmark and license gates pass, propose a product change behind an explicit opt-in, with provenance, bounded timeout, cancellation, and deterministic fallback/review semantics.

## Routing hypothesis (not implemented)

Retain existing local strategies for simple regions; consider a specialized mask-conditioned candidate for textured backgrounds only after evidence shows improvement over the current Yomu baseline. Route high ambiguity, text intertwined with characters/line art, or insufficient context to human review. A generative editor without a proven binary-mask contract is a separate experiment, not a drop-in inpainting backend.

No production code, model weights, private pages, credentials, or Colab runtime state are included in this proposal.
