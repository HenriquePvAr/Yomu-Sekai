import test_support._test_bootstrap as _test_bootstrap  # noqa: F401
from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest

from yomu.review import region_taxonomy as rt


class SeriesTitleLogoTests(unittest.TestCase):
    def tearDown(self):
        rt.set_series_identity("")

    def test_the_works_own_title_is_a_logo_not_story(self):
        rt.set_series_identity("hero-killer")
        self.assertTrue(rt.looks_like_series_title("HERO KILLER"))
        self.assertTrue(rt.looks_like_strong_credit("HERO KILLER"))

    def test_other_text_and_unknown_series_are_untouched(self):
        rt.set_series_identity("hero-killer")
        self.assertFalse(rt.looks_like_series_title("HERO"))
        self.assertFalse(rt.looks_like_series_title("I AM A HERO KILLER"))
        rt.set_series_identity("")
        self.assertFalse(rt.looks_like_series_title("HERO KILLER"))


if __name__ == "__main__":
    unittest.main()
