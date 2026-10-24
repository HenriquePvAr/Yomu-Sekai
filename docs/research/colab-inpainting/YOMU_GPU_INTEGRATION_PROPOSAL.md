# Yomu GPU integration proposal (research only)

No production code or contract is changed by this proposal. The current Yomu route remains authoritative.

## Existing pipeline boundary

The production clean strategy declares `clean` in `OutputPlan`, runs local cleanup first, and considers remote work only for `LOCAL_RECONSTRUCTION_HARD` with sufficient confidence and an authorized mask. SFX, invalid source, uncertain ownership/mask, transport errors, alignment/seam failures, and safety violations remain fail-closed. A remote RAW is only a donor: align it, composite it over the original inside the authorized mask, then require the existing outside-mask pixel recount and quality certificate before persisting a Safe Final.

Relevant implementation:

- `yomu/clean/orchestrator.py` — local-first strategy boundary.
- `yomu/clean/inpainting/art_text_inpainting.py` and `multiscale_patch_synthesis.py` — mask/texture/donor contracts and local reconstruction.
- `yomu/clean/inpainting/advanced_art_inpainting.py` — optional, hash-pinned TorchScript model adapter; defaults to CPU; no model downloads at runtime.
- `yomu/clean/gemini_fallback/` — separate remote Gemini path and Safe Clean contracts; do not duplicate it for Colab.
- `docs/architecture/clean_strategy.md` — frozen route/safety summary.

## Proposed evaluation-to-product path

1. **Offline benchmark only:** use synthetic/commercially-cleared fixture, explicit mask, fixed seed/model revision, and human review. Keep notebook images in ephemeral runtime storage.
2. **Choose only on evidence:** compare current LaMa-family adapter (after checkpoint-license review) with a true mask-conditioned candidate. Prompt-edit models are separate candidates and must be evaluated as untrusted RAW donors.
3. **Local provider abstraction (future, not this task):** if GPU inference wins, inject a provider at the existing reconstruction boundary. Keep current input contract (source, owned target, authorized mask, dimensions, request identity) and return RAW + model/version/hash + timing metadata. Do not widen the mask or relax ownership.
4. **Safety remains in Yomu:** treat provider output as a proposal; alignment, strict mask composite, outside-mask pixel recount, source-text residual validation, seam/texture checks, SFX/protected-region check, certificate, and final artifact persistence stay client-side and fail closed.
5. **Durable serving:** Colab is not the production worker. If the benchmark supports GPU operation, deploy to a controlled GPU VM/service with private authenticated API, queue/lease, idempotency, bounded retries, deadline/cancel, health/readiness, model pinning, artifact retention/erasure policy, and observability. Reuse the existing provider boundary rather than introducing another Gemini-like path.
6. **Fallback:** if GPU service is unavailable, retain local CPU/patch synthesis or route to manual review. Never report a clean success from an unverified original/source fallback.

## Batch and caching

Batching may amortize model load and GPU scheduling, but batch across independent region crops only when dimensions/mask handling are compatible. Preserve per-region ownership and result identity. Cache key should include source hash, mask hash, model revision/weight digest, preprocessing version, precision, and inference parameters. A cache hit must still pass current safety/semantic validation. Retry only idempotent pre-inference transport failures; never duplicate an ambiguous generation after the provider may have started.

## 80 GB decision

Do not pay for 80 GB based on model size alone. A larger GPU can make large edit models resident or enable batches, but it does not prove better reconstruction and cannot by itself reduce single-image diffusion steps or data transfer. First compare a small mask model on the same crops using cold/warm latency and quality. Benchmark 80 GB only if the smaller GPU demonstrably OOMs, requires costly offload, or cannot reach an approved throughput target.

## Gates before any integration

- Clear checkpoint/weight redistribution and training-data license, especially for the Yomu-configured anime/manga TorchScript checkpoint.
- Establish actual Colab plan/unit balance and safe runtime availability.
- Obtain paired, human-reviewed mask-inpainting results and real end-to-end timing.
- Confirm the model honors the mask as a conditioning contract; if not, treat it as an image editor and enforce donor-only composition.
- Preserve all frozen schemas, billing, YK, provider, quality, SFX, and review contracts.
- Separate research, candidate code, and production release approval. This mission grants no production integration or deployment.
