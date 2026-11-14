-- NOT APPLIED. Settlement must not be blocked by a failed request that produced no output.
--
-- Observed: a batch of 60 items completed, then an optional single-item retry was rejected by the
-- provider and recorded as status='failed' (result null). settle_translation_job('consume') and
-- finalize_translation_job both required EVERY request of the job to be 'completed', so the job
-- could neither be consumed (translation_job_not_complete) nor released (a completed request
-- exists, provider_success_cannot_be_released): the reservation stayed stuck and the paid job died.
--
-- A 'failed' row with a null result delivered and billed nothing, so both functions now skip it.
-- Rows that are processing, provider_succeeded or otherwise unresolved still block settlement.

create or replace function public.finalize_translation_job(
  p_job_id text,
  p_reservation_id uuid
) returns jsonb
language plpgsql security definer
set search_path = pg_catalog, public as $$
declare
  q public.translation_requests%rowtype;
  r public.yk_reservations%rowtype;
  total_requests integer := 0;
  completed_requests integer := 0;
  v_user uuid;
  progression_inserted integer := 0;
begin
  if nullif(trim(p_job_id), '') is null or p_reservation_id is null then
    raise exception 'invalid_translation_job';
  end if;

  for q in select * from public.translation_requests
            where job_id = trim(p_job_id) order by request_id for update loop
    if q.reservation_id is distinct from p_reservation_id then
      raise exception 'reservation_job_mismatch';
    end if;
    v_user := q.user_id;
    -- A request that failed without any provider output (for example an optional single-item
    -- retry the provider rejected) delivered and billed nothing, so it must not block settling
    -- the batches that did complete.
    if q.status = 'failed' and q.result is null then continue; end if;
    total_requests := total_requests + 1;
    if q.status = 'completed' then completed_requests := completed_requests + 1; end if;
    if q.provider <> 'deepl' then raise exception 'translation_provider_mismatch'; end if;
  end loop;
  if total_requests = 0 then raise exception 'translation_job_not_found'; end if;
  if completed_requests <> total_requests then raise exception 'translation_job_not_complete'; end if;

  select * into r from public.yk_reservations
   where id = p_reservation_id and job_id = trim(p_job_id) and user_id = v_user for update;
  if r.id is null then raise exception 'reservation_not_found'; end if;
  if r.status = 'consumed' then
    return jsonb_build_object('job_id', trim(p_job_id), 'reservation_id', r.id,
      'status', 'consumed', 'idempotent', true, 'yk_debited', 0, 'xp_credited', 0);
  end if;
  if r.status <> 'reserved' then raise exception 'reservation_not_reserved'; end if;

  update public.yk_reservations set status = 'consumed', updated_at = now() where id = r.id;

  -- The daily debit inherits the expiry captured at reservation time so it
  -- leaves the active balance together with the credit that funded it.
  if r.daily_amount > 0 then
    insert into public.yk_ledger(user_id, amount, bucket, event_type, reference_id, expires_at)
      values (v_user, -r.daily_amount, 'daily', 'translation_debit', trim(p_job_id), r.daily_expires_at);
  end if;
  if r.subscription_amount > 0 then
    insert into public.yk_ledger(user_id, amount, bucket, event_type, reference_id)
      values (v_user, -r.subscription_amount, 'subscription', 'translation_debit', trim(p_job_id));
  end if;
  if r.permanent_amount > 0 then
    insert into public.yk_ledger(user_id, amount, bucket, event_type, reference_id)
      values (v_user, -r.permanent_amount, 'permanent', 'translation_debit', trim(p_job_id));
  end if;

  insert into public.progression_ledger(user_id, amount, event_type, reference_id)
    values (v_user, 10, 'translation', trim(p_job_id)) on conflict do nothing;
  get diagnostics progression_inserted = row_count;

  return jsonb_build_object('job_id', trim(p_job_id), 'reservation_id', r.id,
    'status', 'consumed', 'idempotent', false, 'yk_debited', r.amount,
    'xp_credited', case when progression_inserted = 1 then 10 else 0 end);
end $$;

create or replace function public.settle_translation_job(
  p_job_id text,
  p_reservation_id uuid,
  p_action text,
  p_idempotency_key text
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_user uuid := auth.uid();
  r public.yk_reservations%rowtype;
  q record;
  v_requests integer := 0;
  v_processing integer := 0;
  v_completed integer := 0;
  v_result_persisted integer := 0;
  v_expected_status text;
  v_result jsonb;
begin
  if v_user is null then raise exception 'unauthorized'; end if;
  if nullif(trim(p_job_id), '') is null or p_reservation_id is null
     or p_action is null or p_action not in ('consume', 'release')
     or p_idempotency_key is null
     or p_idempotency_key !~ '^[A-Za-z0-9][A-Za-z0-9:_.-]{15,199}$' then
    raise exception 'invalid_settlement_request';
  end if;

  perform pg_advisory_xact_lock(hashtextextended(v_user::text, 0));
  if not exists (select 1 from public.yk_reservations
                  where id = p_reservation_id and job_id = trim(p_job_id)
                    and user_id = v_user) then
    raise exception 'reservation_not_found';
  end if;
  -- Match the existing begin/finalize lock order (request rows, then reservation)
  -- to avoid a settlement-vs-provider deadlock.
  for q in
    select user_id, reservation_id, status, provider, result
      from public.translation_requests
     where job_id = trim(p_job_id)
     for update
  loop
    if q.user_id <> v_user or q.reservation_id is distinct from p_reservation_id then
      raise exception 'reservation_job_mismatch';
    end if;
    -- Failed without provider output: nothing delivered or billed (see finalize_translation_job).
    if q.status = 'failed' and q.result is null then continue; end if;
    v_requests := v_requests + 1;
    if q.status = 'processing' then v_processing := v_processing + 1; end if;
    if q.status = 'completed' then v_completed := v_completed + 1; end if;
    if q.result is not null then v_result_persisted := v_result_persisted + 1; end if;
    if p_action = 'consume' and (q.status <> 'completed' or q.provider <> 'deepl') then
      raise exception 'translation_job_not_complete';
    end if;
  end loop;

  select * into r from public.yk_reservations
   where id = p_reservation_id and job_id = trim(p_job_id) and user_id = v_user
   for update;
  if r.id is null then raise exception 'reservation_not_found'; end if;

  if r.status in ('consumed', 'released') then
    v_expected_status := case when p_action = 'consume' then 'consumed' else 'released' end;
    if r.status <> v_expected_status then raise exception 'reservation_terminal_conflict'; end if;
    return jsonb_build_object('job_id', trim(p_job_id), 'reservation_id', r.id,
      'status', r.status, 'idempotent', true, 'yk_debited', 0, 'xp_credited', 0);
  end if;
  if r.status <> 'reserved' then raise exception 'reservation_state_invalid'; end if;
  if exists (select 1 from public.yk_reservations
              where user_id = v_user and settlement_idempotency_key = p_idempotency_key
                and id <> r.id) then
    raise exception 'idempotency_key_conflict';
  end if;

  if p_action = 'consume' then
    if v_requests = 0 then raise exception 'translation_job_not_found'; end if;
    if v_result_persisted <> v_requests then raise exception 'translation_result_not_persisted'; end if;
    -- Reuse the canonical server-side ledger/XP transaction. This function is
    -- transactionally nested; any failure rolls back the settlement metadata too.
    v_result := public.finalize_translation_job(trim(p_job_id), r.id);
    update public.yk_reservations
       set settlement_action = 'consume',
           settlement_idempotency_key = p_idempotency_key,
           settled_at = now(), updated_at = now()
     where id = r.id;
    return v_result || jsonb_build_object('idempotent', false);
  end if;

  -- A client may only abandon before any provider output exists. Even one
  -- completed request/result makes the reservation non-refundable: partial
  -- provider success is recoverable work, not grounds for a client refund.
  if v_processing > 0 then raise exception 'translation_request_in_flight'; end if;
  if v_completed > 0 or v_result_persisted > 0 then
    raise exception 'provider_success_cannot_be_released';
  end if;
  update public.yk_reservations
     set status = 'released', settlement_action = 'release',
         settlement_idempotency_key = p_idempotency_key,
         settled_at = now(), updated_at = now()
   where id = r.id;
  return jsonb_build_object('job_id', trim(p_job_id), 'reservation_id', r.id,
    'status', 'released', 'idempotent', false, 'yk_debited', 0, 'xp_credited', 0);
end;
$$;

revoke all on function public.finalize_translation_job(text, uuid) from public, anon, authenticated;
grant execute on function public.finalize_translation_job(text, uuid) to service_role, postgres;

revoke all on function public.settle_translation_job(text, uuid, text, text) from public, anon;
grant execute on function public.settle_translation_job(text, uuid, text, text) to authenticated;
