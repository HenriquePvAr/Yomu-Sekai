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


def test_fuzzy_lookup_repairs_ocr_misread_sfx():
    from yomu.translation.sfx_glossary import translate_sfx_fuzzy

    assert translate_sfx_fuzzy("CLAMTER") == "BARULHO"   # CLATTER, one misread
    assert translate_sfx_fuzzy("BVAZE") == "FASH"        # BLAZE
    assert translate_sfx_fuzzy("FluCK") == "FLIN"        # FLICK
    assert translate_sfx_fuzzy("GRIB") == "AGARRA"       # GRIP, same-length substitution
    assert translate_sfx_fuzzy("RMBLE") == "RRRUM"       # RUMBLE, dropped letter
    assert translate_sfx_fuzzy("CRAdKVE") == "CREC CREC"  # CRACKLE, two misreads
    assert translate_sfx_fuzzy("RiMBCE") == "RRRUM"      # RUMBLE, two misreads


def test_fuzzy_lookup_never_rewrites_real_words_or_names():
    from yomu.translation.sfx_glossary import translate_sfx_fuzzy

    # "ROCK?" is a shouted name/an English word, not a misread of "TOCK".
    assert translate_sfx_fuzzy("RocK?") is None
    assert translate_sfx_fuzzy("HERO") is None
    assert translate_sfx_fuzzy("GIFT") is None
    assert translate_sfx_fuzzy("FIRE") is None


def test_fuzzy_lookup_stays_fail_closed_on_short_garbled_tokens():
    from yomu.translation.sfx_glossary import translate_sfx_fuzzy

    # Too short to disambiguate safely: keeping the source is better than a
    # wrong onomatopoeia.
    assert translate_sfx_fuzzy("VAS") is None
    assert translate_sfx_fuzzy("HUR") is None
    assert translate_sfx_fuzzy("AMCK") is None


def test_fuzzy_lookup_allows_vowel_omission_on_short_tokens():
    from yomu.translation.sfx_glossary import translate_sfx_fuzzy

    # OCR on stylized caps drops vowels: "SMSH" is "SMASH".
    assert translate_sfx_fuzzy("SMSH") == "PÁ"


def test_fuzzy_lookup_falls_back_to_exact_behavior():
    from yomu.translation.sfx_glossary import translate_sfx_fuzzy

    assert translate_sfx_fuzzy("BANG") == "BAM"
    assert translate_sfx_fuzzy("BAAANG") == "BAAAM"
    assert translate_sfx_fuzzy("BA-DUMP") == "TUM TUM"
    assert translate_sfx_fuzzy("ASSISTANCE") is None
