-- NOT APPLIED. Security fix B2: remove the pre-reservation overloads of
-- begin_translation_request. They create requests without request_hash/claim token
-- (outside the replay protocol) and without any per-reservation quota.
-- The only caller (translation-execute) uses the 6-argument version.
drop function if exists public.begin_translation_request(text,uuid,uuid,text,integer);
drop function if exists public.begin_translation_request(text,uuid,text,integer);
