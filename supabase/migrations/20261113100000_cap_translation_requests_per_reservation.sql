-- NOT APPLIED. Security fix A1: one reservation must not pay for unlimited translation.
--
-- begin_translation_request now bounds the requests and characters that may be
-- attached to a single reservation. Caps are derived from the reservation's own
-- cost (r.amount = YK charged for one chapter), not from a free-floating number:
--   * characters: 5 provider batches of the existing 100,000-char batch ceiling
--     (komyst_backend_provider MAX_BATCH_CHARS / translation-execute) per YK;
--   * requests:   50 per YK (one chapter is a few batches; the rest is retry headroom).
-- Counted over every request row of the reservation (any status) so failed retries
-- also consume headroom. The reservation row is locked FOR UPDATE just above the
-- count, which serialises concurrent begins and makes the count race-free.
-- Idempotent replays of an existing request_id return before this check and are free.
create or replace function public.begin_translation_request(
  p_request_id text,p_device_id uuid,p_reservation_id uuid,p_job_id text,
  p_character_count integer,p_request_hash text
) returns jsonb language plpgsql security definer
set search_path=pg_catalog,public as $$
declare u uuid:=auth.uid(); l uuid; r public.yk_reservations%rowtype; q public.translation_requests%rowtype; tid uuid; nt uuid;
  used_requests integer; used_chars bigint;
begin
  if u is null then raise exception 'unauthorized'; end if;
  if nullif(trim(p_request_id),'') is null or p_character_count<0 or nullif(trim(p_request_hash),'') is null then raise exception 'invalid_translation_request'; end if;
  if coalesce((select enabled from public.beta_feature_flags where name='translation_enabled'),false)=false then raise exception 'translation_disabled'; end if;
  select * into q from public.translation_requests where request_id=trim(p_request_id) and user_id=u for update;
  if q.id is not null then
    if q.request_hash is distinct from trim(p_request_hash) or q.job_id is distinct from p_job_id then raise exception 'idempotency_conflict'; end if;
    if q.status='completed' then return jsonb_build_object('request_id',q.request_id,'status','completed','idempotent',true,'result',q.result); end if;
    if q.result is not null then return jsonb_build_object('request_id',q.request_id,'status','provider_succeeded','idempotent',true,'result',q.result); end if;
    if q.provider_started_at is not null then return jsonb_build_object('request_id',q.request_id,'status','provider_outcome_unknown','idempotent',true); end if;
    if q.claim_expires_at is null or q.claim_expires_at>now() then return jsonb_build_object('request_id',q.request_id,'status','in_progress','idempotent',true); end if;
    nt:=gen_random_uuid();
    update public.translation_requests set claim_token=nt,claim_generation=claim_generation+1,claimed_at=now(),claim_expires_at=now()+interval '30 seconds' where id=q.id and provider_started_at is null and (claim_expires_at is null or claim_expires_at<=now());
    if not found then return jsonb_build_object('request_id',q.request_id,'status','in_progress','idempotent',true); end if;
    return jsonb_build_object('request_id',q.request_id,'status','reclaimed','idempotent',false,'claim_token',nt,'claim_generation',q.claim_generation+1,'reservation_id',q.reservation_id);
  end if;
  select * into r from public.yk_reservations where id=p_reservation_id and user_id=u for update;
  if r.id is null or r.status<>'reserved' then raise exception 'reservation_invalid'; end if;
  if p_job_id is not null and trim(p_job_id)<>r.job_id then raise exception 'reservation_job_mismatch'; end if;
  select count(*),coalesce(sum(character_count),0) into used_requests,used_chars from public.translation_requests where reservation_id=r.id;
  if used_requests+1>r.amount*50 or used_chars+p_character_count>r.amount::bigint*500000 then raise exception 'reservation_quota_exceeded'; end if;
  select id into l from public.licenses where user_id=u and status='active' and (expires_at is null or expires_at>now()) order by expires_at desc nulls last limit 1;
  if l is null then raise exception 'license_not_found'; end if;
  if not exists(select 1 from public.license_devices where id=p_device_id and user_id=u and license_id=l and status='active') then raise exception 'device_not_found'; end if;
  nt:=gen_random_uuid();
  insert into public.translation_requests(request_id,user_id,license_id,device_id,job_id,reservation_id,provider,status,character_count,started_at,request_hash,claimed_at,claim_expires_at,claim_token,claim_generation)
    values(trim(p_request_id),u,l,p_device_id,r.job_id,p_reservation_id,'deepl','processing',p_character_count,now(),trim(p_request_hash),now(),now()+interval '30 seconds',nt,1) returning id into tid;
  return jsonb_build_object('id',tid,'request_id',trim(p_request_id),'status','processing','reservation_id',p_reservation_id,'provider','deepl','claim_token',nt,'claim_generation',1);
end $$;

-- CREATE OR REPLACE keeps existing grants; restate them so the contract is explicit.
revoke all on function public.begin_translation_request(text,uuid,uuid,text,integer,text) from public,anon;
grant execute on function public.begin_translation_request(text,uuid,uuid,text,integer,text) to authenticated,service_role,postgres;
