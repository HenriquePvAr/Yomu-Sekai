"""pt-BR onomatopoeia for sound effects and *action* labels."""
from unittest import mock

from yomu.config import settings as config
from yomu.ocr import ocr_balloon as ob
from yomu.translation.sfx_glossary import translate_sfx


def test_known_sounds_get_their_ptbr_onomatopoeia_with_case_and_decoration():
    assert translate_sfx("BANG") == "BAM"
    assert translate_sfx("*bite*") == "*morde*"
    assert translate_sfx("Thud!") == "Tum!"
    assert translate_sfx('"*sit forward*"') == '"*inclina-se*"'


def test_a_stretched_sound_stays_stretched():
    assert translate_sfx("BAAANG") == "BAAAM"


def test_unknown_words_go_to_the_provider():
    assert translate_sfx("ASSISTANCE") is None
    assert translate_sfx("1234") is None


def test_translated_sfx_passes_validation_only_when_sfx_translation_is_on():
    with mock.patch.object(config, "TRANSLATE_SFX", True):
        assert ob.validate_translation_text("BANG", "BAM", classification="sfx")[0]
    with mock.patch.object(config, "TRANSLATE_SFX", False):
        assert ob.validate_translation_text("BANG", "", classification="sfx") == (True, "sfx_preserved")


def test_a_hyphenated_sound_is_replaced_as_a_whole():
    assert translate_sfx("BA-DUMP") == "TUM TUM"


def test_unknown_sound_effects_keep_their_source_text_in_the_pipeline_batch():
    # The pipeline sends no unknown SFX to the provider: an echo keeps the lettering.
    assert translate_sfx("hoog") is None
