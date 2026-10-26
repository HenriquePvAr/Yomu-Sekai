"""The LaMa GPU session is built in the background after OCR, not mid-render."""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import os
import unittest
from unittest import mock

import yomu.pipeline.benchmark_pipeline as bp


class LamaPrewarmTests(unittest.TestCase):
    def test_hermetic_tests_never_load_the_model(self):
        with mock.patch.dict(os.environ, {"TRADUTOR_IA_HERMETIC_TEST_ENV": "1"}):
            self.assertIsNone(bp._prewarm_learned_inpainter())

    def test_render_runs_load_the_inpainter_in_background(self):
        inpainter = mock.Mock()
        with mock.patch.dict(os.environ, {"TRADUTOR_IA_HERMETIC_TEST_ENV": "0"}), \
                mock.patch("yomu.core.gpu.directml_enabled", return_value=True), \
                mock.patch("yomu.clean.inpainting.advanced_art_inpainting.get_default_inpainter",
                           return_value=inpainter):
            thread = bp._prewarm_learned_inpainter()
            thread.join(5)
        inpainter.load.assert_called_once()

    def test_no_render_no_prewarm(self):
        with mock.patch.dict(os.environ, {"TRADUTOR_IA_HERMETIC_TEST_ENV": "0", "YOMU_EFFECTIVE_OPS": "translate"}):
            self.assertIsNone(bp._prewarm_learned_inpainter())


if __name__ == "__main__":
    unittest.main()


class PageShapedSmartSplitTests(unittest.TestCase):
    def _images(self, sizes):
        import tempfile
        from pathlib import Path
        from PIL import Image
        root = Path(tempfile.mkdtemp())
        paths = []
        for index, size in enumerate(sizes):
            path = root / f"{index:03}.png"
            Image.new("RGB", size, "white").save(path)
            paths.append(str(path))
        return paths

    def test_manga_pages_are_not_resplit(self):
        self.assertTrue(bp._images_are_page_shaped(self._images([(1125, 1600)] * 5)))

    def test_webtoon_strips_still_split(self):
        self.assertFalse(bp._images_are_page_shaped(self._images([(800, 6000)] * 5)))
