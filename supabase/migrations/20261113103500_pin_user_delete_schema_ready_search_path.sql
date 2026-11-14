-- NOT APPLIED. Security fix I4: empty search_path (catalog reads only; pg_catalog is
-- always implicitly searched) and revoke from every client role, not just PUBLIC.
alter function public.komyst_user_delete_schema_ready() set search_path = '';
revoke all on function public.komyst_user_delete_schema_ready() from public, anon, authenticated;
grant execute on function public.komyst_user_delete_schema_ready() to service_role;
