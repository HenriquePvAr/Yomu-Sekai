# Better Auth local preparation

> **Status: PARCIAL — prepared, never activated.** Reviewed 2026-10-24 · Verified base `5f482ce1`.
> Production/default authentication is Supabase (`yomu/community/community_auth.py::build_auth_provider`
> falls back to `supabase`; see [SUPABASE_AUTH.md](SUPABASE_AUTH.md)). No cutover to Better Auth
> happened: the active backend cutover of 2026-09-29 (commit `8b0053fe`) moved to a new Supabase
> project, and `scripts/auth-migration/migrate.ts` still throws by design. The code below remains
> in the repository as an optional, local-only provider.

This repository keeps Supabase as the default authentication provider. Better Auth is prepared behind an explicit provider flag and a same-origin proxy so the UI can be exercised locally without exposing cookies, tokens, or admin credentials to the browser.

## Current state

- Default provider: `supabase`
- Optional provider: `better_auth`
- Public browser path: `/api/auth/*`
- Internal local service path: `http://127.0.0.1:<port>/api/auth/*`
- Canonical app session check: `/api/community/auth/session`

The Python UI (`yomu/ui/app.py`, route `/api/auth/*`) only enables the proxy when the active provider is `better_auth` (`AUTH_PROVIDER=better_auth`, which takes precedence, or `COMMUNITY_AUTH_PROVIDER=better_auth`). The internal Better Auth URL must point to a loopback HTTP host. Non-loopback URLs fail closed.

## Required local variables

Do not commit values. None of these variables is listed in `.env.example`; they are read
only by `apps/auth-service/src/config.ts`, `yomu/community/community_auth.py` and `yomu/ui/app.py`.

```text
AUTH_PROVIDER=better_auth
BETTER_AUTH_SECRET=<at least 32 bytes>
BETTER_AUTH_URL=http://127.0.0.1:8080
BETTER_AUTH_INTERNAL_URL=http://127.0.0.1:8787
BETTER_AUTH_DATABASE_PATH=<optional; default %LOCALAPPDATA%\TradutorIA\runtime\better-auth.sqlite3>
BETTER_AUTH_TRUSTED_ORIGINS=http://127.0.0.1:8080
TRADUTOR_AUTH_SERVICE_HOST=127.0.0.1
TRADUTOR_AUTH_SERVICE_PORT=8787
```

The auth service refuses to bind to anything other than `127.0.0.1`/`localhost`.

Google OAuth remains disabled unless both `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are configured
(these are the names the code reads; earlier revisions of this file cited `BETTER_AUTH_GOOGLE_*`
and `BETTER_AUTH_DATABASE_URL`, which the code never read).

## Local commands

From `apps/auth-service` (Node >= 24):

```powershell
npm ci
npm run typecheck
npm test
npm run build
```

No remote migration is executed by these commands.

## Migration scripts

The files under `scripts/auth-migration/` are intentionally dry-run first:

- `audit.ts` reads planned inputs and reports safe metadata.
- `dry-run.ts` validates that migration settings are present without writing remotely.
- `migrate.ts` is disabled and throws until an explicit remote migration plan is approved.
- `verify.ts` describes the post-cutover checks.

Rollback remains Supabase by changing the provider flag back to `supabase` and restarting the local UI/backend.
