import test_support._test_bootstrap as _test_bootstrap  # noqa: F401
from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from komyst.review.source_readiness import SourceReadinessStore, default_workspace_id
from komyst.ui.ui_bridge import UiBridge

UI = (Path(__file__).resolve().parents[1] / "static" / "komyst_ui.js").read_text(encoding="utf-8")


class WorkspacePolicyAlwaysActiveTests(unittest.TestCase):
    def _active(self, db):
        store = SourceReadinessStore(db)
        try:
            return store.active_workspace_policy(owner="local", workspace_id=default_workspace_id(db))
        finally:
            store.close()

    def test_a_revoked_default_policy_is_restored_at_the_next_start(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "jobs.sqlite3"
            UiBridge._ensure_default_workspace_policy(db)
            self.assertIsNotNone(self._active(db))
            store = SourceReadinessStore(db)
            try:
                store.revoke_workspace_policy(owner="local", workspace_id=default_workspace_id(db),
                                              revoked_by="local")
            finally:
                store.close()
            self.assertIsNone(self._active(db))
            UiBridge._ensure_default_workspace_policy(db)
            self.assertEqual(self._active(db).status, "active")

    def test_an_active_policy_is_left_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "jobs.sqlite3"
            UiBridge._ensure_default_workspace_policy(db)
            first = self._active(db).policy_id
            UiBridge._ensure_default_workspace_policy(db)
            self.assertEqual(self._active(db).policy_id, first)

    @unittest.skipUnless(shutil.which("node"), "node is required")
    def test_a_policy_that_has_not_loaded_is_not_a_refusal_but_an_explicit_one_is(self):
        start = UI.index("function workspacePolicyAllowsProcessing()")
        end = UI.index("function minimumSourceInputIsValid()")
        script = (
            "const appState = {settings: {}};\n" + UI[start:end] + "\n"
            "const results = [];\n"
            "results.push(workspacePolicyAllowsProcessing());\n"
            "appState.settings = {workspace_source_policy: {}};\n"
            "results.push(workspacePolicyAllowsProcessing());\n"
            "appState.settings = {workspace_source_policy: {status: 'active', all_submitted_sources_authorized: true}};\n"
            "results.push(workspacePolicyAllowsProcessing());\n"
            "appState.settings = {workspace_source_policy: {status: 'revoked', all_submitted_sources_authorized: false}};\n"
            "results.push(workspacePolicyAllowsProcessing());\n"
            "appState.settings = {workspace_source_policy: {status: 'inactive'}};\n"
            "results.push(workspacePolicyAllowsProcessing());\n"
            "console.log(JSON.stringify(results));\n"
        )
        out = subprocess.run(["node", "-e", script], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), "[true,true,true,false,false]")


if __name__ == "__main__":
    unittest.main()
