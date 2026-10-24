# Training Candidate Contract V1

> **Revisado em:** 2026-10-24 · **Base verificada:** `5f482ce1` · Status: **IMPLEMENTADO** in `evaluate_training_candidate()` (`yomu/clean/gemini_fallback/quality.py`).

A case becomes a training candidate only when the deterministic evaluator reports every required gate as passing: completed transport, valid mask and alignment, zero outside-mask changes, seam pass, OCR removal pass, SFX firewall pass or not applicable, non-target pass or not applicable, acceptable visual quality, and delegated technical-review provenance.

```mermaid
flowchart LR
    M["Quality metadata<br/>SAFE_CLEAN_QUALITY_V1"] --> G{"All 11 checks pass?<br/>completed, transport, mask,<br/>alignment, outside_mask = 0,<br/>seam, OCR removal, SFX,<br/>non-target, visual quality,<br/>review provenance"}
    G -->|yes| C["training_candidate = true<br/>ALL_GATES_PASS"]
    G -->|no| R["training_candidate = false<br/>GATE_MISSING reason codes"]
```

Missing or inconclusive metadata fails closed: an absent value never satisfies a gate. One nuance verified in code: an absent `status` is read as `COMPLETED`, so the completion check relies on the transport/mask/validation gates to fail closed. Binary artifacts remain external to the repository; this repository stores only small manifests and evidence.
