"""A resumed job must carry a fresh translation auth envelope, not the expired one it was created with.

Observed: an interrupted job resumed hours later failed with auth_context_expired in translate_many, so its
held reservation could never be settled. The envelope is bound to the job id and expires; resume now seals a
new one from the current session token under the same context id.
"""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import komyst.ui.ui_bridge as ui_bridge
from komyst.runtime.job_store import JobStatus


class ResumeAuthContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._patches = [
            patch.dict(os.environ, {"KOMYST_TEST_RUNTIME_ROOT": str(self.tmp)}),
            patch.object(ui_bridge, "env_status",
                         lambda *a, **k: {"env_exists": True, "nvidia_configured": True}),
            patch.object(ui_bridge, "_current_commit", lambda: "deadbeef"),
            patch.object(ui_bridge, "_current_branch", lambda: "main"),
        ]
        for patcher in self._patches:
            patcher.start()
        self.bridge = ui_bridge.UiBridge()

    def tearDown(self):
        self.bridge.store.close()
        for patcher in self._patches:
            patcher.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _interrupted(self, configuration):
        job_id = self.bridge.store.create_job(
            source_url="https://example.invalid/chapter", output_dir=str(self.tmp / "out"),
            command=["run"], configuration=configuration)
        store = self.bridge.store
        store.claim_next_job("w1", 1)
        store.transition(job_id, JobStatus.STARTING, expected_worker="w1")
        store.transition(job_id, JobStatus.RUNNING, expected_worker="w1", stage="translation")
        store.transition(job_id, JobStatus.INTERRUPTED, expected_worker="w1",
                         interrupted_reason="output_recovery_available", recoverable=1)
        return job_id

    def _resume(self, job_id, token):
        with patch.object(self.bridge, "_require_beta_access") as gate:
            gate.return_value.to_safe_job_metadata.return_value = {"allowed": True}
            return self.bridge.resume(job_id, license_access_token=token)

    def test_resume_reseals_the_envelope_under_the_original_context_id(self):
        job_id = self._interrupted({"translation_enabled": True, "auth_context_id": "ctx-original",
                                    "auth_context_ref": "auth/ctx-original.auth"})
        sealed = {"translation_enabled": True, "auth_context_id": "ctx-original",
                  "auth_context_ref": "auth/ctx-original.auth", "resealed": True}
        with patch.object(self.bridge, "_seal_translation_context", return_value=sealed) as seal:
            result = self._resume(job_id, "token-from-the-current-session")

        job_arg = seal.call_args.args[0]
        self.assertEqual(job_arg["id"], "ctx-original")
        self.assertEqual(seal.call_args.kwargs["license_access_token"], "token-from-the-current-session")
        new_job = self.bridge.store.get_job(result["job_id"])
        self.assertTrue(new_job["configuration"].get("resealed"))
        self.assertEqual(new_job["configuration"]["auth_context_id"], "ctx-original")

    def test_resume_without_a_session_token_keeps_the_old_configuration(self):
        job_id = self._interrupted({"translation_enabled": True, "auth_context_id": "ctx-original"})
        with patch.object(self.bridge, "_seal_translation_context",
                          side_effect=ValueError("auth_handoff_unavailable")):
            result = self._resume(job_id, "")
        new_job = self.bridge.store.get_job(result["job_id"])
        self.assertEqual(new_job["configuration"]["auth_context_id"], "ctx-original")
        self.assertNotIn("resealed", new_job["configuration"])

    def test_a_job_without_translation_is_not_sealed(self):
        job_id = self._interrupted({"translation_enabled": False})
        with patch.object(self.bridge, "_seal_translation_context") as seal:
            self._resume(job_id, "token")
        seal.assert_not_called()
