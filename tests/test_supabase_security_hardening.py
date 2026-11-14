"""Supabase security hardening (audit A1, M1, M2, B1-B4, I4, I5).

Behaviour is proven on a real PostgreSQL (same container harness as
test_yk_postgres_integration; skipped without Docker). Source-level checks cover
the edge functions. These migrations are NOT applied to any remote database.
"""
from __future__ import annotations

import uuid
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

from tests.test_yk_postgres_integration import db, migrated_dsn  # noqa: F401  (fixtures)

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = ROOT / "supabase/functions"


def _enable_translation(db):
    db.conn.execute(
        "insert into public.beta_feature_flags(name,enabled) values('translation_enabled',true) "
        "on conflict (name) do update set enabled=true")


def _begin(db, uid, device_id, rid, request_id, chars):
    job = db.conn.execute("select job_id from public.yk_reservations where id=%s", (rid,)).fetchone()[0]
    return db.as_user(
        uid, "select public.begin_translation_request(%s,%s,%s,%s,%s,%s)",
        (request_id, device_id, rid, job, chars, "h" + request_id))


def _reserved(db):
    uid, _lic, dev = db.user()
    db.credit(uid, 5, "permanent")
    _enable_translation(db)
    job = "job-" + uuid.uuid4().hex[:8]
    rid = db.as_user(uid, "select public.reserve_translation_yk(%s,%s)", (job, dev))["reservation_id"]
    return uid, dev, rid


# --- A1 ---------------------------------------------------------------------
def test_multi_batch_chapter_still_works_within_reservation_quota(db):
    uid, dev, rid = _reserved(db)
    for i in range(5):  # a chapter of several full-size batches
        assert _begin(db, uid, dev, rid, f"ok-{uuid.uuid4().hex}", 100_000)["status"] == "processing"


def test_reservation_character_quota_is_enforced(db):
    uid, dev, rid = _reserved(db)
    for _ in range(5):
        _begin(db, uid, dev, rid, f"c-{uuid.uuid4().hex}", 100_000)
    with pytest.raises(psycopg.errors.RaiseException, match="reservation_quota_exceeded"):
        _begin(db, uid, dev, rid, f"c-{uuid.uuid4().hex}", 1)


def test_reservation_request_quota_is_enforced(db):
    uid, dev, rid = _reserved(db)
    for _ in range(50):
        _begin(db, uid, dev, rid, f"r-{uuid.uuid4().hex}", 1)
    with pytest.raises(psycopg.errors.RaiseException, match="reservation_quota_exceeded"):
        _begin(db, uid, dev, rid, f"r-{uuid.uuid4().hex}", 1)


def test_idempotent_replay_is_not_blocked_by_quota(db):
    uid, dev, rid = _reserved(db)
    first = _begin(db, uid, dev, rid, "same-req", 500_000)
    assert first["status"] == "processing"
    assert _begin(db, uid, dev, rid, "same-req", 500_000)["idempotent"] is True


# --- B2 ---------------------------------------------------------------------
def test_legacy_begin_overloads_are_gone(db):
    for sig in ("text,uuid,uuid,text,integer", "text,uuid,text,integer"):
        assert db.conn.execute(
            f"select to_regprocedure('public.begin_translation_request({sig})')").fetchone()[0] is None
    assert db.conn.execute(
        "select to_regprocedure('public.begin_translation_request(text,uuid,uuid,text,integer,text)')"
    ).fetchone()[0] is not None


# --- M2 / B1 ----------------------------------------------------------------
def test_comment_author_cannot_touch_moderation_or_chapter(db):
    uid, _l, _d = db.user()
    cols = db.conn.execute(
        "select column_name from information_schema.column_privileges "
        "where table_schema='public' and table_name='comments' "
        "and grantee='authenticated' and privilege_type='UPDATE'").fetchall()
    assert {c[0] for c in cols} == {"content", "deleted_at"}


def test_profile_object_keys_are_not_client_writable(db):
    cols = {c[0] for c in db.conn.execute(
        "select column_name from information_schema.column_privileges "
        "where table_schema='public' and table_name='profiles' "
        "and grantee='authenticated' and privilege_type='UPDATE'").fetchall()}
    assert "avatar_object_key" not in cols and "banner_object_key" not in cols
    assert {"bio", "display_name", "username"} <= cols  # profile form keeps working


# --- M1 ---------------------------------------------------------------------
def test_consume_device_challenge_is_service_role_only(db):
    q = "select has_function_privilege(%s, %s, 'execute')"
    for sig in ("public.consume_device_challenge(uuid,text)",
                "public.consume_device_challenge(uuid,text,uuid)"):
        for role in ("authenticated", "anon"):
            assert db.conn.execute(q, (role, sig)).fetchone()[0] is False, (role, sig)
    assert db.conn.execute(q, ("service_role", "public.consume_device_challenge(uuid,text,uuid)")).fetchone()[0]


def test_device_verify_edge_consumes_with_service_role():
    src = (FUNCTIONS / "device-verify/index.ts").read_text(encoding="utf-8")
    consume = src[src.index("consume_device_challenge") - 400:]
    assert "SUPABASE_SERVICE_ROLE_KEY" in consume and "p_user_id" in consume


# --- B3 ---------------------------------------------------------------------
def test_per_user_unique_indexes_exist(db):
    names = {r[0] for r in db.conn.execute("select indexname from pg_indexes where schemaname='public'")}
    assert {"yk_reservations_user_job_uq", "translation_requests_user_request_uq"} <= names


# --- B4 ---------------------------------------------------------------------
@pytest.mark.parametrize("table", [
    "licenses", "license_devices", "subscriptions", "yk_ledger", "yk_daily_claims",
    "yk_reservations", "ad_reward_events", "admin_audit_log", "translation_requests",
    "device_challenges", "beta_invites"])
def test_anon_has_no_privileges_on_private_tables(db, table):
    for priv in ("select", "insert", "update", "delete", "truncate"):
        assert db.conn.execute("select has_table_privilege('anon',%s,%s)",
                               (f"public.{table}", priv)).fetchone()[0] is False


@pytest.mark.parametrize("table", ["plans", "beta_feature_flags", "beta_remote_config", "progression_ranks"])
def test_public_config_tables_are_read_only_for_anon(db, table):
    assert db.conn.execute("select has_table_privilege('anon',%s,'select')", (f"public.{table}",)).fetchone()[0]
    for priv in ("insert", "update", "delete", "truncate"):
        assert db.conn.execute("select has_table_privilege('anon',%s,%s)",
                               (f"public.{table}", priv)).fetchone()[0] is False


@pytest.mark.parametrize("table", ["licenses", "yk_ledger", "yk_reservations", "translation_requests", "plans"])
def test_authenticated_cannot_truncate(db, table):
    assert db.conn.execute("select has_table_privilege('authenticated',%s,'truncate')",
                           (f"public.{table}",)).fetchone()[0] is False


# --- I4 ---------------------------------------------------------------------
def test_user_delete_schema_ready_has_empty_search_path(db):
    cfg = db.conn.execute(
        "select proconfig from pg_proc where proname='komyst_user_delete_schema_ready'").fetchone()[0]
    assert cfg is not None and any(c.replace(" ", "") in ('search_path=""', "search_path=") for c in cfg)
    assert db.conn.execute(
        "select has_function_privilege('authenticated','public.komyst_user_delete_schema_ready()','execute')"
    ).fetchone()[0] is False


# --- I5 ---------------------------------------------------------------------
def test_rewarded_callback_has_no_dead_code():
    src = (FUNCTIONS / "rewarded-ad-callback/index.ts").read_text(encoding="utf-8")
    assert "credit_ayet_rewarded_ad" not in src and "hmacHex" not in src
    assert "rewarded_ads_disabled" in src and "503" in src
