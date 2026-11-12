import test_support._test_bootstrap as _test_bootstrap  # noqa: F401
from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest

import komyst.translation.portuguese_words as pw


class RestoreCorruptedSourceWordsTests(unittest.TestCase):
    def test_mangled_name_returns_to_source_spelling(self):
        out = pw.restore_corrupted_source_words(
            "ESTOU FALANDO DA GEENOM.", "I'M TALKING ABOUT GEHENNA.", ["GEENOM"])
        self.assertEqual(out, "ESTOU FALANDO DA GEHENNA.")

    def test_word_without_a_close_source_counterpart_is_untouched(self):
        text = "AQUELA VADIASSA PARECE BEM."
        self.assertEqual(pw.restore_corrupted_source_words(text, "THAT B**** SEEMS FINE.", ["VADIASSA"]), text)

    def test_source_word_already_present_is_not_reused(self):
        text = "GEHENNA FALOU DA GEENOM."
        out = pw.restore_corrupted_source_words(text, "GEHENNA SPOKE OF GEHENNA.", ["GEENOM"])
        self.assertEqual(out, text)


if __name__ == "__main__":
    unittest.main()
