-- NOT APPLIED. Security fix I4: empty search_path (catalog reads only; pg_catalog is
-- always implicitly searched) and revoke from every client role, not just PUBLIC.
--
-- The function was created by an already-applied migration under its original name
-- (yomu_user_delete_schema_ready). The repository copy of that migration was later rewritten to
-- komyst_user_delete_schema_ready by the package rename, so production and a fresh database
-- disagree on the name. Harden whichever of the two exists; do nothing if neither does.
do $$
declare
  fn text;
begin
  foreach fn in array array['komyst_user_delete_schema_ready', 'yomu_user_delete_schema_ready'] loop
    if to_regprocedure(format('public.%I()', fn)) is not null then
      execute format('alter function public.%I() set search_path = %L', fn, '');
      execute format('revoke all on function public.%I() from public, anon, authenticated', fn);
      execute format('grant execute on function public.%I() to service_role', fn);
    end if;
  end loop;
end
$$;
