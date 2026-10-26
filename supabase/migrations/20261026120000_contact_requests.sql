-- Source requests ("Solicitar fonte") and feedback sent from the app.
-- Every message is kept here first, so nothing is lost when e-mail delivery is
-- unavailable; the contact-request Edge Function then e-mails the team inbox.

create table if not exists public.contact_requests (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    kind text not null,
    url text,
    message text,
    created_at timestamptz not null default now(),
    constraint contact_requests_kind check (kind in ('source_request', 'feedback')),
    constraint contact_requests_url_len check (url is null or char_length(url) <= 500),
    constraint contact_requests_message_len check (message is null or char_length(message) <= 2000),
    constraint contact_requests_has_content check (
        (kind = 'source_request' and url ~ '^https?://') or (kind = 'feedback' and char_length(trim(message)) >= 3)
    )
);

create index if not exists contact_requests_user_created_idx
    on public.contact_requests (user_id, created_at desc);

-- No direct table access: rows are written only through the function below.
alter table public.contact_requests enable row level security;
revoke all on public.contact_requests from anon, authenticated;

create or replace function public.submit_contact_request(
  p_kind text,
  p_url text default null,
  p_message text default null
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_user uuid := auth.uid();
  v_recent integer;
  v_id uuid;
  v_profile record;
  v_email text;
begin
  if v_user is null then raise exception 'unauthorized'; end if;
  select count(*) into v_recent from public.contact_requests
   where user_id = v_user and created_at > now() - interval '1 hour';
  if v_recent >= 5 then raise exception 'rate_limited'; end if;

  insert into public.contact_requests (user_id, kind, url, message)
  values (v_user, p_kind, nullif(trim(p_url), ''), nullif(trim(p_message), ''))
  returning id into v_id;

  select username, display_name into v_profile from public.profiles where id = v_user;
  select email into v_email from auth.users where id = v_user;
  return jsonb_build_object(
    'id', v_id,
    'username', v_profile.username,
    'display_name', v_profile.display_name,
    'email', v_email
  );
end;
$$;

revoke all on function public.submit_contact_request(text, text, text) from public, anon;
grant execute on function public.submit_contact_request(text, text, text) to authenticated;
