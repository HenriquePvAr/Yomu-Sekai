"""A name an honorific abbreviation addresses is a name, even when it is an English word.

ep. 33: "TALK WITH MS. GO ALONE" came back from DeepL as "go alone" and the
render kept "SRA. GO ALONE" in English.
"""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import json
import unittest

import yomu.ocr.ocr_balloon as ob
from yomu.translation import honorific_names
from yomu.translation.providers.translator_deepl import DeepLTranslator


class HonorificNameTests(unittest.TestCase):
    def test_short_english_word_after_honorific_is_a_name(self):
        text = "TODAY I'LL TALK WITH MS. GO ALONE."
        self.assertEqual(ob.honorific_addressed_names(text), ["GO"])
        self.assertIn("GO", ob.detect_proper_name_spans(text))

    def test_verbs_and_conjunctions_are_not_names(self):
        self.assertEqual(ob.honorific_addressed_names("I MISS YOU"), [])
        self.assertEqual(ob.honorific_addressed_names("LET'S GO NOW"), [])
        self.assertEqual(ob.honorific_addressed_names("MR. AND MRS. KIM"), ["KIM"])

    def test_name_is_local_to_its_group(self):
        addressed = ob.TextGroup(group_id="BALAO_1", lines=[], text="TALK WITH MS. GO ALONE.")
        verb = ob.TextGroup(group_id="BALAO_2", lines=[], text="LET'S GO.")
        ob.propagate_chapter_declared_names([addressed, verb])
        self.assertIn("GO", addressed.detected_proper_names)
        self.assertNotIn("GO", verb.detected_proper_names)

    def test_xml_protection_round_trip(self):
        protected = honorific_names.protect_for_xml("MS. GO & <ME>")
        self.assertEqual(protected, "MS. <x>GO</x> &amp; &lt;ME&gt;")
        self.assertEqual(honorific_names.unprotect_xml("Sra. <x>Go</x> &amp; eu"), "Sra. Go & eu")
        self.assertIsNone(honorific_names.protect_for_xml("I MISS YOU"))


class DeepLProtectsHonorificNamesTests(unittest.TestCase):
    def _translator(self, reply):
        calls = []

        def transport(url, headers, body, timeout):
            calls.append(json.loads(body.decode("utf-8")))
            return 200, json.dumps({"translations": [{"text": text} for text in reply]})

        return DeepLTranslator(api_key="test-key-not-a-real-credential",
                               base_url="https://api-free.deepl.com", transport=transport), calls

    def test_addressed_name_goes_in_an_ignored_tag(self):
        deepl, calls = self._translator(["Falar com a Sra. <x>Go</x> sozinha.", "Eu &amp; ele."])
        out = deepl.translate_many(["TALK WITH MS. GO ALONE.", "ME & HIM."])
        self.assertEqual(calls[0]["text"], ["TALK WITH MS. <x>GO</x> ALONE.", "ME &amp; HIM."])
        self.assertEqual(calls[0]["tag_handling"], "xml")
        self.assertEqual(calls[0]["ignore_tags"], ["x"])
        self.assertEqual(out, ["Falar com a Sra. Go sozinha.", "Eu & ele."])

    def test_batch_without_names_is_unchanged(self):
        deepl, calls = self._translator(["Vamos."])
        deepl.translate_many(["LET'S GO & RUN."])
        self.assertEqual(calls[0]["text"], ["LET'S GO & RUN."])
        self.assertNotIn("tag_handling", calls[0])


if __name__ == "__main__":
    unittest.main()
