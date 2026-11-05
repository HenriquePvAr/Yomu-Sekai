import test_support._test_bootstrap as _test_bootstrap  # noqa: F401
from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import tempfile
import unittest
import unittest.mock
from pathlib import Path
from types import SimpleNamespace

import yomu.pipeline.benchmark_pipeline as benchmark_pipeline


class RunManifestIdentityTests(unittest.TestCase):
    def test_job_run_id_is_preserved_in_run_manifest(self):
        output = Path(tempfile.mkdtemp()) / "chapter" / "3a396e01-77d9-44b4-95a0-4759e2e7eb17"
        report = {
            "job_run_id": "3a396e01-77d9-44b4-95a0-4759e2e7eb17",
            "run_signature": "signature",
            "status": "review_required",
            "quality_validation": {"passed": False, "manual_review_required_groups": 1},
            "pdf_path": str(output / "chapter.pdf"),
        }

        manifest = benchmark_pipeline._output_run_manifest(
            output,
            report,
            SimpleNamespace(model="fake-offline"),
        )

        self.assertEqual(manifest["run_id"], "3a396e01-77d9-44b4-95a0-4759e2e7eb17")
        self.assertEqual(manifest["slug"], "3a396e01-77d9-44b4-95a0-4759e2e7eb17")

    def test_manifest_records_the_commit_seen_at_run_start_not_the_current_head(self):
        output = Path(tempfile.mkdtemp()) / "chapter" / "run"
        report = {"job_run_id": "run", "run_signature": "s", "status": "completed",
                  "quality_validation": {"passed": True}, "pdf_path": str(output / "c.pdf")}
        with unittest.mock.patch.object(benchmark_pipeline, "_GIT_AT_RUN_START",
                                        {"commit_hash": "start", "branch": "dev"}), \
             unittest.mock.patch.object(benchmark_pipeline, "_git_metadata",
                                        return_value={"commit_hash": "moved-later", "branch": "dev"}):
            manifest = benchmark_pipeline._output_run_manifest(
                output, report, SimpleNamespace(model="fake-offline"))
        self.assertEqual(manifest["commit_hash"], "start")


if __name__ == "__main__":
    unittest.main()
