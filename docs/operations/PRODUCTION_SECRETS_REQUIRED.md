# Production secrets contract

> **Base verificada:** `5f482ce1` (branch `main`) · **Revisado em:** 2026-10-24

These names are deployment-only and must never be bundled into the desktop client. The
"Consumer in repository" column was checked with `git grep` at the base above; a name with no
consumer is a reserved contract name, not a live integration.

| Name | Purpose | Consumer in repository | Status |
| --- | --- | --- | --- |
| `DEEPL_API_KEY` | server-side DeepL proxy | `supabase/functions/translation-execute/index.ts`; presence reported by `tools/release/check_beta_configuration.py` | IMPLEMENTED |
| `AYET_PUBLISHER_API_KEY` | ayeT callback HMAC verification (backend only) | `supabase/functions/rewarded-ad-callback/index.ts` | IMPLEMENTED (provider-gated) |
| `SMTP_PASSWORD` | transactional email provider | presence reported by `tools/release/check_beta_configuration.py` (with `SMTP_HOST`, `SMTP_USER`) | PARTIAL (checked, not consumed by Python runtime) |
| Supabase server credentials (`SUPABASE_SECRET_KEY` in Edge Functions) | server-side control-plane operations only | `supabase/functions/*` | IMPLEMENTED (server only) |
| `BILLING_API_KEY`, `BILLING_WEBHOOK_SECRET` | hosted billing provider | none | PLANNED |
| `AD_PROVIDER_SECRET` | rewarded-ad verification (generic) | none | PLANNED |
| `AYET_REWARDED_ADSLOT_ID` | ayeT placement identifier (non-secret config) | none (the callback reads `adslot_id` from the request) | PLANNED |
| Update signing private key | release publisher only | not an environment variable: `scripts/sign_release.py --key <path-to-pem>` | IMPLEMENTED (file path argument) |

Use the sanitized configuration checker (`python tools/release/check_beta_configuration.py`)
before activation; it reads only process environment variables and prints only
`READY`/`NOT_CONFIGURED` states (`BILLING` and `REWARDED_ADS` are reported as a fixed
`DISABLED`). Values are not documented here.
