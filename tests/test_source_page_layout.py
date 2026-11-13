import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import tempfile
import unittest
from pathlib import Path

from PIL import Image

import komyst.pipeline.benchmark_pipeline as bp
from komyst.download.sources.chapter_source import ComixAdapter, WebtoonsAdapter


def _images(size, count=5):
    folder = Path(tempfile.mkdtemp())
    paths = []
    for index in range(count):
        path = folder / f"{index}.png"
        Image.new("RGB", size, "white").save(path)
        paths.append(str(path))
    return paths


class SourcePageLayoutTests(unittest.TestCase):
    def test_webtoons_declares_a_strip_and_others_stay_unknown(self):
        self.assertEqual(WebtoonsAdapter().page_layout, "strip")
        self.assertEqual(ComixAdapter().page_layout, "")

    def test_strip_chunk_that_looks_like_a_page_is_still_split(self):
        chunks = _images((800, 1280))  # aspect 1.6: judged "page-shaped" by shape alone
        self.assertTrue(bp._images_are_page_shaped(chunks))
        self.assertTrue(bp._source_needs_smart_split({"page_layout": "strip"}, chunks))

    def test_unknown_source_keeps_the_shape_rule(self):
        self.assertFalse(bp._source_needs_smart_split({}, _images((800, 1280))))
        self.assertTrue(bp._source_needs_smart_split({}, _images((800, 6000))))


if __name__ == "__main__":
    unittest.main()
