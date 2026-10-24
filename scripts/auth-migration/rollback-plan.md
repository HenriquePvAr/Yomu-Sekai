# Better Auth migration rollback plan

> **Status: PARCIAL / not activated** (reviewed 2026-10-24, base `5f482ce1`). The Better Auth
> cutover never happened; Supabase is the default and active provider. `migrate.ts` still throws.
> See `docs/BETTER_AUTH_MIGRATION.md`.

This task prepares migration tooling only. Do not run a remote cutover without an
operator-approved backup and a dry-run report for the exact target environment.

Rollback outline:

1. keep `AUTH_PROVIDER=supabase` or `COMMUNITY_AUTH_PROVIDER=supabase`;
2. stop the local Better Auth service;
3. keep Better Auth tables for audit, but do not delete Supabase users;
4. verify community ownership through the existing Supabase/local-session provider;
5. re-run the dry-run before any future attempt.

Never log password hashes, session tokens, cookies, service-role keys or full e-mail
addresses in migration reports.

