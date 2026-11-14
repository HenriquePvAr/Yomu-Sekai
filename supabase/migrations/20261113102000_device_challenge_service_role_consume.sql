-- NOT APPLIED. Security fix M1 (part 1): proof of device possession.
-- consume_device_challenge(uuid,text) was callable by authenticated, so a client could
-- burn a challenge without the Ed25519 signature check done in the device-verify edge
-- function. Consumption moves to a service_role-only overload that takes the owner
-- explicitly; the edge function calls it after verifying the signature.
-- PENDING (part 2): no RPC consults device_challenges yet, so heartbeat/reservation do
-- not require a recent verified device session.
revoke all on function public.consume_device_challenge(uuid,text) from public,anon,authenticated;

create or replace function public.consume_device_challenge(p_challenge_id uuid,p_nonce_hash text,p_user_id uuid)
returns jsonb language plpgsql security definer set search_path=pg_catalog,public as $$
declare v_id uuid;
begin
  if p_user_id is null then raise exception 'forbidden'; end if;
  update public.device_challenges set consumed_at=now() where id=p_challenge_id and user_id=p_user_id and consumed_at is null and expires_at>now() and nonce_hash=p_nonce_hash returning id into v_id;
  if v_id is null then
    if exists(select 1 from public.device_challenges where id=p_challenge_id and user_id=p_user_id and consumed_at is not null) then raise exception 'device_challenge_consumed';
    elsif exists(select 1 from public.device_challenges where id=p_challenge_id and user_id=p_user_id and expires_at<=now()) then raise exception 'device_challenge_expired';
    else raise exception 'device_challenge_invalid'; end if;
  end if;
  return jsonb_build_object('challenge_id',v_id,'consumed',true);
end $$;
revoke all on function public.consume_device_challenge(uuid,text,uuid) from public,anon,authenticated;
grant execute on function public.consume_device_challenge(uuid,text,uuid) to service_role,postgres;
