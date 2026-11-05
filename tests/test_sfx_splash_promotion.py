"""Full-width splash SFX lettering must not vanish from the pipeline."""
from types import SimpleNamespace

from unittest import mock

from yomu.config import settings as config
from yomu.ocr.ocr_balloon import (
    _filter_groups,
    _should_translate_group,
    known_sound_translation_target,
)


def _group(text, *, confidence=0.9, box=(0, 1703, 799, 615), classification="decorative",
           background_type="textured_art", ignored=False):
    return SimpleNamespace(
        text=text,
        confidence=confidence,
        box=box,
        classification=classification,
        background_type=background_type,
        background_metrics={},
        ignored=ignored,
        preserve_as_name=False,
        ocr_quality_blocked=False,
        sent_to_translation=False,
        translation_valid=False,
        review_translate_override="auto",
    )


def test_oversized_known_sound_is_not_dropped_as_too_large():
    group = _group("RMBLE")  # RUMBLE with a dropped letter, full-width splash
    with mock.patch.object(config, "TRANSLATE_SFX", True):
        _filter_groups([group], (1416, 800, 3))
    assert not group.ignored


def test_oversized_non_sound_is_still_dropped():
    group = _group("SKRRTTXX")  # not a known sound
    _filter_groups([group], (1416, 800, 3))
    assert group.ignored
    assert group.ignore_reason == "group_too_large"


def test_decorative_known_sound_is_promoted_to_translation():
    group = _group("SMSH", box=(160, 1265, 618, 551), classification="decorative")
    with mock.patch.object(config, "TRANSLATE_SFX", True):
        assert known_sound_translation_target(group) == "PÁ"
        assert _should_translate_group(group) is True


def test_decorative_non_sound_is_not_promoted():
    group = _group("SKRRTTXX", classification="decorative")
    with mock.patch.object(config, "TRANSLATE_SFX", True):
        assert known_sound_translation_target(group) is None
        assert _should_translate_group(group) is False


def test_known_sound_off_when_translate_sfx_disabled():
    group = _group("SMSH", classification="decorative")
    with mock.patch.object(config, "TRANSLATE_SFX", False):
        assert known_sound_translation_target(group) is None
