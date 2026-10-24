# Gemini Safe Fallback V2 integration

> **Revisado em:** 2026-10-24 · **Base verificada:** `5f482ce1` · Status: **IMPLEMENTADO, opt-in, default off**.
> The flag is read in `yomu/pipeline/benchmark_pipeline.py` (accepted values `1`/`true`/`yes`) and is not listed in `.env.example`. Since 2026-10-23/24 the default local CLEAN has its own learned (LaMa) fill and OCR re-read gates — see [Clean strategy](../architecture/clean_strategy.md); the remote path described here is unchanged and still optional.

The Gemini capability remains under `yomu.clean.gemini_fallback`. This integration adds only the provider-agnostic Clean strategy boundary. It does not change Authorized Mask Generator V2, the quality metadata contract, the SFX firewall, or the training candidates `case02` and `case03`.

## Residual translation recovery and runtime wiring

The historical SAFE CLEAN capability is now connected at the CLEAN boundary through
an explicit, opt-in `YOMU_ENABLE_GEMINI_SAFE_FALLBACK` flag. Local CLEAN remains the
default and the remote result is accepted only through the existing authorized-mask
and safe-compositing strategy boundary. No mask generator, OCR engine, seam policy,
SFX firewall, or billing rule was changed.

Translation recovery is a separate text-only adapter in
`yomu/translation/gemini_fallback.py`. It runs only after a primary translation
failure or semantic-fidelity failure, never for SFX, proper names, decorative text,
blocked OCR, or failed OCR (`_BLOCKED_CLASSES` in `yomu/translation/gemini_fallback.py`). This SFX exclusion is independent of `TRANSLATE_SFX`, which since 2026-10-24 defaults to `True` and renders known sounds through the local glossary, not through any provider. Candidates are normalized and passed through the same
translation validator before persistence. The adapter is injected by the provider;
there is no embedded credential or historical Gemini text endpoint in this branch.
When unavailable, the path fails closed and records manual review rather than
silently accepting source-language text. Recovery is part of the original logical
translation operation and does not reserve a second YK unit.
