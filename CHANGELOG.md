# Changelog

All notable changes to Yomu Sekai (Tradutor IA) are recorded here. Dates are ISO-8601.
This file records source-level changes; it is not a release/tag log.

## [Unreleased] — main — 2026-10-24 (`5f482ce1`)

### Changed — clean, render & SFX
- Sound effects are translated by default (`TRANSLATE_SFX=True`) using a pt-BR onomatopoeia
  glossary (`assets/lexicon/sfx_en_pt.json`); unknown sounds keep their original lettering.
- New render flags (default `True`, code-only in `yomu/config/settings.py`):
  `RENDER_FIT_BALLOON_SHAPE` (wrap to the balloon shape) and `RENDER_MATCH_SOURCE_SLANT`
  (match measured source slant).
- Evidence-based cleanup/reconstruction gates; `tests/test_cleanup_fixed_mask_reconstruction_red.py`
  now passes and is a regular contract.

### Changed — repository
- Requirement profiles moved to `requirements/` (`requirements.txt` stays at the root;
  `requirements/requirements-beta.txt` includes it via `-r ../requirements.txt`).
- Root pointer stubs `PRODUCTION_SECRETS_REQUIRED.md` and `SEMANTIC_CLASSIFICATION_AUDIT.md`
  removed; canonical copies live in `docs/operations/` and `docs/architecture/`.

### Notes
- Enabled translation jobs always go through the authenticated `yomu_backend` provider; the
  CLI never calls DeepL directly (`--translation-provider` is metadata/guard).
- Hermetic suite: ~6160 passed, 0 failed (`python -m pytest -q`).

## 0.9.1 quality-freeze consolidation — 2026-09-25 (source-level, untagged)

Consolidation of the Beta 0.9.1 quality-freeze work. No pinned image/CV dependency changed;
the production behavior contract of the freeze is preserved. See
[`docs/QUALITY_FREEZE.md`](docs/QUALITY_FREEZE.md) for the validated-state addendum.

### Fixed — pipeline & source
- Comix dynamic materialization: bounded resolver retry (3 passes, per-page budget 25s) for
  the intermittently-flaky canonical materialization; full 105/105 download proven.
- Partial page scope: the download gate is graded against the **selected** pages, not the
  whole canonical chapter, so any `1 ≤ N ≤ total` completes (proven physically at N=5).
- Runtime root resolution: a job's trusted state (auth envelope, queue DB, diagnostics)
  follows the explicit `TRADUTOR_RUNTIME_ROOT` / DB parent and is never relocated by
  `output_dir`; fixes `auth_context_missing_or_corrupt` in the translation runner.

### Fixed — output contract
- `output_format` now propagates end to end (UI → config → `command_json` → post-analysis
  rebuild → runner argv → manifest → history) for PDF/PNG/PSD; a fail-closed invariant
  (`assert_command_output_format`) rejects any config/command divergence before processing.
- PSD export: one two-layer PSD per page (`Original` base, `Translated` top); PNG export:
  final reconstructed pages. Neither is overridden by the internal canonical PDF.

### Fixed — UI & history
- Start button re-enables after a pre-job start failure without a reload; active-job
  concurrency block preserved.
- History and result cards are format-aware ("Tradução/Download · PDF|PNG|PSD"), derived
  from the canonical `output_format`, never from `pdf_path`; the internal PDF is no longer
  offered as a user artifact for PNG/PSD jobs.
- Processing modes reduced to Quality and Download-only ("Rápido" hidden); primary button
  label follows the mode.

### Fixed — profile media & OAuth
- Profile-media upstream failures use a bounded exponential backoff (30s → 60s → 120s cap)
  that clears immediately on success; the optional remote-profile enrichment logs a
  sanitized breadcrumb on failure while staying fail-open.

### Packaging
- Canonical Yomu ICO applied to the EXE, installer, shortcuts and the uninstall entry.

### Tests
- Added hermetic regression coverage: output-format propagation, partial-scope download
  gate, PSD/PNG exporters, runtime-root resolution, secure auth-context runtime, profile
  backoff, format-aware history labels, start-retry, Comix resolver retry, and more.
