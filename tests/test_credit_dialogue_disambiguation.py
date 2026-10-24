"""Regression: ordinary dialogue words must not turn a balloon into a preserved credit.

"THANK YOU", "OUR TEAM" or "CLEAN THE ROOM" inside a speech/narration region were
classified CREDIT_PRESERVE (never cleaned or translated) and, when left on the page,
were counted as credit residuals instead of ordinary-story residuals.
"""

from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest

import yomu.review.region_taxonomy as tax


class CreditDialogueDisambiguationTest(unittest.TestCase):
    def test_dialogue_with_weak_credit_words_stays_dialogue(self):
        for text in ("THANK YOU!", "THANKS, MAN.", "OUR TEAM WON!", "CLEAN THE ROOM.",
                     "I EDIT VIDEOS.", "THE STAFF IS HERE.", "THANKS TO THE TEAM!"):
            for label, expected in (("speech", tax.DIALOGUE_TRANSLATE),
                                    ("dialogue", tax.DIALOGUE_TRANSLATE),
                                    ("thought", tax.THOUGHT_TRANSLATE)):
                category, _ = tax.normalize(label, text=text)
                self.assertEqual(category, expected, (label, text))
            category, _ = tax.normalize("narration", text=text)
            self.assertEqual(category, tax.NARRATION_TRANSLATE, text)

    def test_real_credits_are_still_preserved_in_dialogue_labels(self):
        for text in ("Translated by NightScans", "Typeset & Redraw: team",
                     "Cleaning: Bob", "Edited by Ana", "Special thanks: everyone",
                     "Proofreader: Kai", "Credits"):
            for label in ("speech", "narration"):
                category, _ = tax.normalize(label, text=text)
                self.assertEqual(category, tax.CREDIT_PRESERVE, (label, text))

    def test_non_dialogue_labels_keep_previous_credit_behavior(self):
        category, _ = tax.normalize("decorative", text="OUR TEAM")
        self.assertEqual(category, tax.CREDIT_PRESERVE)

    def test_strong_credit_predicate(self):
        self.assertFalse(tax.looks_like_strong_credit("THANK YOU!"))
        self.assertFalse(tax.looks_like_strong_credit("OUR TEAM WON!"))
        self.assertTrue(tax.looks_like_strong_credit("Translated by X"))
        self.assertTrue(tax.looks_like_strong_credit("Editor: Y"))
        self.assertTrue(tax.looks_like_strong_credit("Special thanks to readers"))


if __name__ == "__main__":
    unittest.main()
