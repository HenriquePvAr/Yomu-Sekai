import test_support._test_bootstrap as _test_bootstrap  # noqa: F401
from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest
from types import SimpleNamespace

import komyst.ocr.ocr_balloon as ob


def _group(boxes):
    return SimpleNamespace(lines=[SimpleNamespace(box=b) for b in boxes])


class SourceTextAlignmentTests(unittest.TestCase):
    def test_left_edges_aligned_with_ragged_right_is_left(self):
        self.assertEqual(ob._source_text_alignment(_group([(10, 0, 200, 20), (10, 25, 120, 20), (10, 50, 160, 20)])), "left")

    def test_right_edges_aligned_is_right(self):
        self.assertEqual(ob._source_text_alignment(_group([(110, 0, 200, 20), (190, 25, 120, 20), (150, 50, 160, 20)])), "right")

    def test_centred_lines_stay_centre(self):
        self.assertEqual(ob._source_text_alignment(_group([(50, 0, 200, 20), (90, 25, 120, 20), (70, 50, 160, 20)])), "center")

    def test_two_credit_lines_flush_right_are_right(self):
        self.assertEqual(ob._source_text_alignment(_group([(487, 691, 260, 29), (522, 726, 224, 26)])), "right")

    def test_equal_widths_and_single_line_stay_centre(self):
        self.assertEqual(ob._source_text_alignment(_group([(10, 0, 150, 20), (10, 25, 152, 20)])), "center")
        self.assertEqual(ob._source_text_alignment(_group([(10, 0, 150, 20)])), "center")


if __name__ == "__main__":
    unittest.main()
