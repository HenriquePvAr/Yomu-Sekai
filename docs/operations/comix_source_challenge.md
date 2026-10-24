# Comix: challenge-aware source flow

> **Base verificada:** `5f482ce1` (branch `main`) · **Revisado em:** 2026-10-24
>
> Code: `yomu/download/readers/scrapling_reader_resolver.py`, `yomu/download/comix_session.py`,
> `yomu/download/down.py`, `yomu/runtime/worker_service.py` (state transition) and
> `static/tradutor_ui.js` (button label).

The Comix source path keeps the existing direct-reader and adaptive browser resolver. A browser challenge is classified as `challenge_required`; it is never bypassed or treated as a generic terminal access denial.

When a claimed URL job reaches that outcome, the worker persists `waiting_source_verification`, records the diagnostic reason, and leaves the job resumable. The UI shows the existing source-review panel with an explicit instruction for the owner to complete legitimate verification in the browser. “Continuar após verificação” resumes the same job through `/api/ui/source/verification/resume`; it does not create a second job or silently retry a scraper.

The main output-format selector was removed. The effective output contract remains owned by the existing OutputPlan; the legacy `output_format` value is retained only as compatibility metadata.

This flow never asks for or stores credentials or tokens, and it does not call an automatic
CAPTCHA/Turnstile solver: the resolver passes `solve_cloudflare=False`. Two browser details
are documented here so the statement above is not read as broader than it is:

- If the optional `cloakbrowser` package is installed in the environment (it is not part of any
  profile in `requirements/`), the dynamic resolver launches that browser binary non-headless
  with its window off-screen (`--window-position=-32000,-32000`) instead of headless system
  Chrome. This is a browser choice, not a solver; a visible challenge still ends as
  `challenge_required`.
- The only cookie handled is the owner-obtained `cf_clearance` described below.

## Owner-obtained Cloudflare clearance

When the owner legitimately completes a visible Comix challenge in the dedicated Chrome profile (`comix_cdp_profile`), the UI-only CDP capture path may persist the resulting `cf_clearance` and matching User-Agent under `%LOCALAPPDATA%\YomuSekai\comix_cf_cookie.json` (temporary directory if `LOCALAPPDATA` is unset). The file is outside Git and its value is never logged or sent to Discord. The resolver may replay that owner-provided clearance through the existing dynamic browser path (Scrapling `StealthyFetcher` with `solve_cloudflare=False`), and `RequestsTransport` sets it on `.comix.to` for image downloads.

Capture is controlled by `YOMU_COMIX_CF_AUTOCAPTURE`: the UI entry point (`yomu.ui.app.main`) sets it to `1` by default with `setdefault`, so it is on whenever the UI is launched and stays off in processes that do not set it (worker, CLI). Set `YOMU_COMIX_CF_AUTOCAPTURE=0` before starting the UI to turn capture off. `YOMU_DISABLE_COMIX_CF_PROFILE=1` (also `true`/`yes`) disables clearance reuse. Expiration is expected; an expired clearance returns to the same recoverable human-verification state.
