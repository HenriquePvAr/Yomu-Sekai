"""A translation carrying a non-Portuguese word gets one retry that can only improve it.

ep. 33: DeepL returned "ESTOVA ESPERANDO QUE VOCÊ PERGUNTASSE." and every
validator passed, because the text is Portuguese overall.
"""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import unittest

import yomu.ocr.ocr_balloon as ob
from yomu.translation.portuguese_words import unknown_target_words


class UnknownTargetWordsTests(unittest.TestCase):
    def test_non_words_are_found_and_names_are_not(self):
        self.assertEqual(unknown_target_words("ESTOVA ESPERANDO QUE VOCÊ PERGUNTASSE.", "I WAS WAITING"), ["ESTOVA"])
        self.assertEqual(unknown_target_words("ANTES DE SAÍRMOS DA TORRE.", "BEFORE WE LEAVE"), [])
        self.assertEqual(unknown_target_words("SOU SEOKJIN KIM, DA ILSUNG.", "I'M SEOKJINKIM OF ILSUNG"), [])


class _Translator:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def translate_strict(self, text, **kwargs):
        self.calls.append(kwargs.get("validation_reason"))
        return self.reply


def _group(translation):
    group = ob.TextGroup(group_id="BALAO_1", lines=[], text="I WAS WAITING FOR YOU TO ASK.")
    group.classification = "speech"
    group.translation = group.translation_candidate = translation
    group.translation_valid = True
    return group


class RetryUnknownTargetWordsTests(unittest.TestCase):
    def test_better_candidate_is_adopted(self):
        group, records = _group("ESTOVA ESPERANDO QUE VOCÊ PERGUNTASSE."), []
        translator = _Translator("ESTAVA ESPERANDO QUE VOCÊ PERGUNTASSE.")
        ob._retry_unknown_target_words(group, translator, False, records)
        self.assertEqual(translator.calls, ["target_unknown_words:ESTOVA"])
        self.assertEqual(group.translation, "ESTAVA ESPERANDO QUE VOCÊ PERGUNTASSE.")
        self.assertTrue(records[-1]["valid"])

    def test_no_better_candidate_leaves_the_region_alone(self):
        group, records = _group("ESTOVA ESPERANDO QUE VOCÊ PERGUNTASSE."), []
        ob._retry_unknown_target_words(group, _Translator("ESTOVA ESPERANDO QUE VOCÊ PERGUNTASSE!"), False, records)
        self.assertEqual(group.translation, "ESTOVA ESPERANDO QUE VOCÊ PERGUNTASSE.")
        self.assertTrue(group.translation_valid)
        self.assertFalse(records[-1]["valid"])

    def test_clean_translation_costs_no_call(self):
        translator = _Translator("x")
        ob._retry_unknown_target_words(_group("ESTAVA ESPERANDO."), translator, False, [])
        self.assertEqual(translator.calls, [])


if __name__ == "__main__":
    unittest.main()
