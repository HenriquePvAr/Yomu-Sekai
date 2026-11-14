-- NOT APPLIED. Security fix B3 (additive only): per-user uniqueness.
-- New unique indexes are added next to the global ones. The global
-- yk_reservations(job_id) / translation_requests(request_id) uniques are intentionally
-- KEPT: settle_translation_job, finalize_translation_job, release_yk_reservation and
-- persist_translation_result look rows up by job_id/request_id alone, so dropping the
-- global key would let two users' rows collide there (reservation_job_mismatch, wrong
-- row). PENDING: scope those lookups by user_id, then drop the global indexes.
create unique index if not exists yk_reservations_user_job_uq on public.yk_reservations(user_id, job_id);
create unique index if not exists translation_requests_user_request_uq on public.translation_requests(user_id, request_id);
