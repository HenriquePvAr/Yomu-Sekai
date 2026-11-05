# SFX fuzzy, termos protegidos e métricas — validação física ep. 285 (Hero Killer)

Evidence levels per AGENTS.md: `TESTED_FROZEN` = unit/focused tests;
`PHYSICALLY_VERIFIED` = paid full run on the authorized reference chapter.

## What changed

- `yomu/translation/sfx_glossary.py`: `translate_sfx_fuzzy` — OCR-tolerant lookup over
  `assets/lexicon/sfx_en_pt.json` (246 -> 265 entries). Guards: real English words never
  match (ROCK stays a name); <=3 letters have no slack; 4-letter tokens tolerate
  same-length substitution or vowel omission only; Damerau distance (transposition = 1).
  ~0.3 ms/call.
- `yomu/translation/terms_glossary.py` + `assets/lexicon/terms_en_pt.json`: protected
  lore terms (GEHENNA, EST, GIFT, TU'UMLIM) repaired post-provider in the
  `apply_group_translations` funnel; ambiguity-safe (two candidates at the same
  distance = untouched).
- `yomu/ocr/ocr_balloon.py`: full-width splash SFX no longer dropped as `group_too_large`;
  `known_sound_translation_target` promotes decorative/unintelligible known sounds;
  classification policy no longer ignores known sounds as `weak_unknown_text`.
- `yomu/translation/providers/yomu_backend_provider.py`: `api_requests`/`api_texts`/
  `cache_hits` counted in `_translate_batch_with_reservation` (the path `translate_many`
  actually uses).
- `yomu/pipeline/benchmark_pipeline.py`: `classification_grouping` no longer
  double-counts re-OCR/selective/full-page fallback time.
- `yomu/ui/app.py` + `yomu/ui/ui_bridge.py`: `/api/ui/open` instrumented
  (`OPEN_ARTIFACT_ROUTE_*` in `routes_current.jsonl`); Windows open failures surface as
  `open_failed` instead of a silent 500.

## Physical validation — 3 paid runs, same config (quality, force, cache off, DeepL)

| Metric | Run 1 `d482cecc` (pre-fix) | Run 2 `77650365` | Run 3 `b374a1ba` |
|---|---|---|---|
| Total time | 254.6 s | 336.1 s | **303.7 s** |
| Translated groups | 56 | 58 | **61** |
| Preserved in English | 16 | 10 | **6** |
| Texts sent to provider | 0 (bug) | 0 (bug) | **62 (fixed)** |
| Inpainting | 67.6 s | 117.2 s | 139.6 s |
| Redraw | 18.4 s | 27.9 s | 33.0 s |
| OCR selective fallback | 55.5 s | 56.4 s | 49.5 s |
| Classification (real, after timing split) | n/a (double-counted at 115.3 s) | 70.9 s | 66.9 s |
| Translation stage | 9.1 s | 9.2 s | 9.1 s |

Run 3 output: `C:\Users\henri\AppData\Local\TradutorIA\output\hero_killer_episode_285\b374a1ba-7343-4525-8f0f-ba113626bb75`

The +49 s vs run 1 is the cost of cleaning/redrawing ~13 SFX regions that used to be
abandoned in English; translation itself is unchanged (~9 s).

## PHYSICALLY_VERIFIED in run 3

- Splash `RUMBLE` -> `RRRUM` (page 3, full-width, previously dropped as group_too_large).
- `CRAdKVE` -> `CREC CREC` (page 9), `GRIB` -> `AGARRA` (p13), `SMOOSH` -> `SPLUSH` (p10),
  `PEW` -> `PIU` (p14/p19), `CRACKLE` -> `CREC CREC` (p18), `GRIP` -> `APERTA` (p8),
  `CLANK` -> `CLANG` (p15), `BLAZE`/`FluCK`/`RiMBCE` translated (runs 2->3 gate fixes).
- `GEENOM` provider output repaired to `GEHENNA` in the final page item (p33).
- `Textos enviados ao provedor: 62` in `timing_report.txt`.

## Deliberately preserved (fail-closed) in run 3

- `RocK?` (proper name), `FLAP` (pt-BR rendering equals source), `VAS`/`HUR`/`AMCK`/
  `THUNe` (OCR damage beyond safe fuzzy limits; editable via the review UI).

## Remaining gates

- 15 groups rendered as `rendered_on_learned_clean_rescue` -> human review queue.
- 4 pre-existing mask-geometry test failures (reproduce on clean `f274feb`; unrelated).
- Credits page (p65) preserved by policy — product decision if credits should translate.
- PaddleOCR fallback engine not enabled: `paddleocr` not installed; fuzzy lookup covers
  the observed cases at ~0 ms marginal cost. `OCR_FALLBACK_ENGINE=paddle` remains
  available after `requirements-paddle.txt` is installed.

## Tests

17 new tests (`tests/test_sfx_glossary.py`, `tests/test_sfx_splash_promotion.py`,
`tests/test_terms_glossary.py`, `tests/test_yomu_backend_provider.py`).
Full suite at final snapshot: 6372 passed, 4 failed (pre-existing, confirmed on clean
HEAD via `git worktree`), 785 subtests passed.
