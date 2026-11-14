-- NOT APPLIED. Security fixes M2/B1: column-level UPDATE for client roles.
-- comments: the author may only change content and deleted_at (soft delete). With no
-- UPDATE on moderation_status/chapter_id/parent_id/author_id the author cannot undo a
-- moderation action or move the comment to a chapter they cannot read. Triggers still
-- maintain updated_at/edited_at (privileges are not checked for trigger writes).
revoke update on public.comments from authenticated;
grant update (content, deleted_at) on public.comments to authenticated;

-- profiles: every column stays writable except the backend-only object keys.
-- ponytail: public_role stays writable because the profile form
-- (social_repository.update_my_profile) sends it; making it backend-only needs a client change.
revoke update on public.profiles from authenticated;
do $$
declare cols text;
begin
  select string_agg(quote_ident(column_name), ', ' order by ordinal_position) into cols
    from information_schema.columns
   where table_schema = 'public' and table_name = 'profiles'
     and column_name not in ('avatar_object_key', 'banner_object_key');
  execute format('grant update (%s) on public.profiles to authenticated', cols);
end $$;
