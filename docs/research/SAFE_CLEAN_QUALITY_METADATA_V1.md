# Safe Clean Quality Metadata V1

> **Revisado em:** 2026-10-24 · **Base verificada:** `5f482ce1` · Status: **IMPLEMENTADO** (research path, opt-in Gemini SAFE CLEAN only).

`yomu.clean.gemini_fallback.quality` (`yomu/clean/gemini_fallback/quality.py`) defines the versioned metadata contract (`QUALITY_METADATA_VERSION = "SAFE_CLEAN_QUALITY_V1"`, mask generator `AUTHORIZED_MASK_GENERATOR_V2`) through `build_quality_metadata()` and the deterministic promotion evaluator `evaluate_training_candidate()`. The contract records transport, mask, alignment, seam, OCR, SFX, non-target, visual-quality, provenance, and outside-mask pixel evidence. The evaluator returns stable reason codes (`<GATE>_GATE_MISSING`, or `ALL_GATES_PASS`) so review and candidate packaging are reproducible.

This metadata applies only to the opt-in remote SAFE CLEAN path (`YOMU_ENABLE_GEMINI_SAFE_FALLBACK=1`, see [Gemini Safe Fallback V2](GEMINI_SAFE_FALLBACK_V2.md)). The default local CLEAN pipeline has its own gates, described in [Clean strategy](../architecture/clean_strategy.md).
