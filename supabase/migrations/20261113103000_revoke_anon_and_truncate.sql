-- NOT APPLIED. Security fix B4: defence in depth on the commercial/control-plane tables.
-- Earlier revokes covered only INSERT/UPDATE/DELETE from authenticated. Here:
--  * anon loses every privilege on tables with no anon-readable policy;
--  * authenticated loses TRUNCATE/REFERENCES/TRIGGER everywhere listed;
--  * I1 (informative): plans(active), progression_ranks, beta_feature_flags and
--    beta_remote_config have RLS policies without TO, hence anon-readable. Kept as is
--    (pricing/feature/min-version config usable pre-login); anon only keeps SELECT.
revoke all on public.licenses, public.license_devices, public.subscriptions, public.yk_ledger,
  public.yk_daily_claims, public.yk_reservations, public.ad_reward_events, public.admin_audit_log,
  public.staff_members, public.beta_invites, public.device_challenges, public.license_sessions,
  public.progression_ledger, public.translation_requests, public.admin_idempotency_keys
  from anon;
revoke insert, update, delete, truncate, references, trigger on
  public.plans, public.progression_ranks, public.beta_feature_flags, public.beta_remote_config
  from anon;
revoke truncate, references, trigger on
  public.plans, public.licenses, public.license_devices, public.subscriptions, public.yk_ledger,
  public.yk_daily_claims, public.yk_reservations, public.ad_reward_events, public.admin_audit_log,
  public.progression_ranks, public.beta_feature_flags, public.beta_remote_config,
  public.staff_members, public.beta_invites, public.device_challenges, public.license_sessions,
  public.progression_ledger, public.translation_requests, public.admin_idempotency_keys
  from authenticated;
