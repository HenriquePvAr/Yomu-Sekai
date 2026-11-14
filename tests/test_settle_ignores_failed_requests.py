"""A failed request that produced no provider output must not block settling the job.

Observed in production: a 60-item batch completed, then an optional single-item retry was rejected
by the provider and recorded as failed. consume then raised translation_job_not_complete and release
raised provider_success_cannot_be_released, so the reservation stayed stuck and the paid job died.
Runs on a real PostgreSQL (same container harness as test_yk_postgres_integration; skipped without Docker).
"""
from __future__ import annotations

import pytest

psycopg = pytest.importorskip("psycopg")

from tests.test_yk_postgres_integration import db, migrated_dsn  # noqa: F401  (fixtures)


def _funded_job(db, tag, *, batches=1):
    uid, license_id, device_id = db.user("free")
    db.as_user(uid, "select public.set_passive_ads_enabled(true)")
    db.as_user(uid, "select public.claim_daily_yk()")
    job = f"{tag}-{uid}"
    reservation = db.translate_chapter(uid, license_id, device_id, job, batches=batches)
    return uid, license_id, device_id, job, reservation["reservation_id"]


def _extra_request(db, uid, license_id, device_id, job, rid, *, status, result_sql="null", suffix="extra"):
    db.conn.execute(
        "insert into public.translation_requests"
        "(request_id,user_id,license_id,device_id,job_id,reservation_id,provider,status,result)"
        f" values(%s,%s,%s,%s,%s,%s,'deepl',%s,{result_sql})",
        (f"{job}-{suffix}", uid, license_id, device_id, job, rid, status))


def _settle(db, uid, job, rid):
    return db.as_user(uid, "select public.settle_translation_job(%s,%s,'consume',%s)",
                      (job, rid, f"yk-settlement-v1:{uid}:consume"))


def test_failed_retry_without_output_does_not_block_consume(db):
    uid, license_id, device_id, job, rid = _funded_job(db, "settle-failed-retry")
    _extra_request(db, uid, license_id, device_id, job, rid, status="failed")
    result = _settle(db, uid, job, rid)
    assert result["status"] == "consumed" and result["yk_debited"] == 1
    assert db.balances(uid)["daily"] == 4


def test_request_still_processing_keeps_blocking_consume(db):
    uid, license_id, device_id, job, rid = _funded_job(db, "settle-processing")
    _extra_request(db, uid, license_id, device_id, job, rid, status="processing")
    with pytest.raises(psycopg.errors.RaiseException, match="translation_job_not_complete"):
        _settle(db, uid, job, rid)
    assert db.balances(uid)["daily"] == 5


def test_failed_request_that_kept_provider_output_still_blocks_consume(db):
    uid, license_id, device_id, job, rid = _funded_job(db, "settle-failed-with-output")
    _extra_request(db, uid, license_id, device_id, job, rid, status="failed",
                   result_sql="'{\"items\": []}'::jsonb")
    with pytest.raises(psycopg.errors.RaiseException, match="translation_job_not_complete"):
        _settle(db, uid, job, rid)


def test_job_with_only_failed_requests_cannot_be_consumed(db):
    uid, license_id, device_id = db.user("free")
    db.as_user(uid, "select public.set_passive_ads_enabled(true)")
    db.as_user(uid, "select public.claim_daily_yk()")
    job = f"settle-only-failed-{uid}"
    rid = db.as_user(uid, "select public.reserve_translation_yk(%s,%s)", (job, device_id))["reservation_id"]
    _extra_request(db, uid, license_id, device_id, job, rid, status="failed")
    with pytest.raises(psycopg.errors.RaiseException, match="translation_job_not_found"):
        _settle(db, uid, job, rid)
    assert db.balances(uid)["daily"] == 5


def test_finalizer_also_skips_failed_request_without_output(db):
    uid, license_id, device_id, job, rid = _funded_job(db, "finalize-failed-retry")
    _extra_request(db, uid, license_id, device_id, job, rid, status="failed")
    result = db.conn.execute("select public.finalize_translation_job(%s,%s)", (job, rid)).fetchone()[0]
    assert result["status"] == "consumed"
    assert db.balances(uid)["daily"] == 4
