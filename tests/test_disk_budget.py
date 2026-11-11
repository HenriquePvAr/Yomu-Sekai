import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import os
import sys
from unittest import mock
from pathlib import Path

from yomu.runtime import disk_budget
from yomu.runtime.job_store import JobStatus, JobStore
from yomu.runtime.job_runner import run_job


def test_required_space_uses_plan_reserve_and_page_estimate():
    assert disk_budget.required_mb("profissional", 10) == 3600
    assert disk_budget.required_mb("apenas_clean", 10) == 1080
    assert disk_budget.required_mb("traducao_pronta", 10) == 1150
    assert disk_budget.required_mb("profissional", None) == 3000


def test_check_reports_free_and_required_space(tmp_path):
    usage = mock.Mock(free=2_000 * 1024 * 1024)
    with mock.patch.object(disk_budget.shutil, "disk_usage", return_value=usage):
        enough, details = disk_budget.check(tmp_path, "default", page_count=10)
    assert enough is True
    assert details["free_mb"] == 2000
    assert details["required_mb"] == 1150
    assert details["sufficient"] is True


def test_check_rejects_insufficient_professional_budget(tmp_path):
    usage = mock.Mock(free=3_100 * 1024 * 1024)
    with mock.patch.object(disk_budget.shutil, "disk_usage", return_value=usage):
        enough, details = disk_budget.check(tmp_path, "profissional", page_count=2)
    assert enough is False
    assert details["required_mb"] == 3120


def test_runner_fails_before_launch_when_start_budget_is_insufficient(tmp_path):
    db = tmp_path / "jobs.sqlite3"
    output = tmp_path / "output" / "chapter" / "run"
    store = JobStore(db)
    command = [sys.executable, str(Path(__file__).parents[1] / "test_support" / "fake_pipeline.py")]
    job_id = store.create_job(
        source_url="https://example.invalid/chapter",
        output_dir=str(output), command=command,
        configuration={"output_plan": "default", "output_format": "pdf"},
    )
    claimed = store.claim_next_job("disk-test-worker", os.getpid())
    assert claimed and claimed["id"] == job_id
    store.transition(job_id, JobStatus.STARTING, expected_worker="disk-test-worker")
    store.close()

    with mock.patch.object(disk_budget, "check", return_value=(False, {
            "free_mb": 10, "required_mb": 1000, "output_plan": "default"})), \
         mock.patch("yomu.runtime.job_runner.subprocess.Popen", side_effect=AssertionError("pipeline launched")):
        result = run_job(job_id, str(db), "disk-test-worker", str(tmp_path / "job.log"))

    assert result == 2
    final_store = JobStore(db)
    try:
        job = final_store.get_job(job_id)
        assert job["status"] == JobStatus.FAILED
        assert job["reason_code"] == "insufficient_disk_space"
        assert "Espaço em disco insuficiente" in job["error_message"]
    finally:
        final_store.close()
