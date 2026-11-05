import test_support._test_bootstrap as _test_bootstrap  # noqa: F401
from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest

import yomu.pipeline.benchmark_pipeline as bp
from yomu.pipeline.pipeline_cache import fingerprint_files


class PipelineFingerprintTests(unittest.TestCase):
    def test_fingerprint_is_built_from_real_files(self):
        self.assertTrue(bp.PIPELINE_FILES)
        self.assertTrue(all(path.is_file() for path in bp.PIPELINE_FILES))
        names = {path.name for path in bp.PIPELINE_FILES}
        self.assertIn("ocr_balloon.py", names)
        self.assertNotEqual(fingerprint_files(bp.PIPELINE_FILES), fingerprint_files(()))

    def test_a_changed_source_changes_the_fingerprint(self):
        import tempfile, pathlib
        with tempfile.TemporaryDirectory() as tmp:
            f = pathlib.Path(tmp) / "a.py"
            f.write_text("x = 1")
            before = fingerprint_files([f])
            f.write_text("x = 2")
            self.assertNotEqual(before, fingerprint_files([f]))


if __name__ == "__main__":
    unittest.main()
