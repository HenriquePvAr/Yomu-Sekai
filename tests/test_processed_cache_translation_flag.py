"""A page processed without translation is never served to a run that translates.

The queue once ran three chapters with translation off; a rerun with translation on
reused those cached pages and rendered the English source back.
"""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import os
import unittest
from unittest import mock

import yomu.pipeline.benchmark_pipeline as bp


class ProcessedCacheTranslationFlagTests(unittest.TestCase):
    def test_translation_flag_is_part_of_the_cache_config(self):
        with mock.patch.dict(os.environ, {"TRANSLATION_ENABLED": "0"}):
            off = bp._relevant_output_config("fp")
        with mock.patch.dict(os.environ, {"TRANSLATION_ENABLED": "1"}):
            on = bp._relevant_output_config("fp")
        self.assertFalse(off["translation_enabled"])
        self.assertTrue(on["translation_enabled"])
        self.assertNotEqual(off, on)


if __name__ == "__main__":
    unittest.main()
