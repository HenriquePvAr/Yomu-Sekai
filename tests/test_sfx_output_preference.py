"""SFX preference changes typesetting, never ownership of the CLEAN layer."""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import os
import threading
from dataclasses import replace
from unittest.mock import patch

import numpy as np

from yomu.community.community_store import CommunityStore
from yomu.ocr import ocr_balloon as ob
from yomu.ocr.ocr_engine import OCRLine
from yomu.ui.ui_bridge import UiBridge
from yomu.core.page_processing_contracts import PreTranslationPageResult
from yomu.pipeline import benchmark_pipeline as bp


def sound():
    line = OCRLine(text="CRACKLE", raw_text="CRACKLE", confidence=.99, box=(10, 10, 50, 20),
                   polygon=np.array([[10,10],[60,10],[60,30],[10,30]], np.float32),
                   metadata={"ocr_line_id": "owned-sound"})
    return ob.TextGroup("sound", lines=[line], text="CRACKLE", classification="sfx")


def test_disabled_sfx_stays_in_final_but_is_cleaned_in_capture():
    group = sound()
    original = np.full((60, 80, 3), 100, np.uint8)
    cleaned = original.copy()
    mask = np.zeros(original.shape[:2], np.uint8)
    mask[10:30, 10:60] = 255
    cleaned[mask > 0] = 200
    capture = {}
    timings = {}
    with patch.object(ob.config, "TRANSLATE_SFX", False), patch.object(
        ob, "_clean_source_for_clean_artifact", return_value=(cleaned, mask, "primary", True)
    ) as cleanup:
        ob._apply_classification_policy(group)
        assert group.ignored and group.ignore_reason == "sfx_translation_disabled"
        assert ob.get_cleanable_translatable_groups([group]) == [group]
        final, _ = ob.render_analyzed_image(original, group.lines, [], [group], capture=capture,
                                            stage_timings=timings)
    cleanup.assert_called_once()
    np.testing.assert_array_equal(final, original)
    np.testing.assert_array_equal(capture["cleaned_bgr"], cleaned)
    assert timings["inpainting"] > 0
    assert timings["cleanup"] == timings["inpainting"]


def test_sound_without_line_ownership_is_not_erased():
    group = sound()
    group.lines[0].metadata.clear()
    with patch.object(ob.config, "TRANSLATE_SFX", False):
        assert ob.get_cleanable_translatable_groups([group]) == []


def test_explicitly_ignored_sfx_is_still_protected():
    group = sound()
    group.ignored = True
    group.ignore_reason = "protected_editorial_art"
    assert ob.get_cleanable_translatable_groups([group]) == []


def test_glossary_promotion_refreshes_stale_weak_policy_for_clean_and_target():
    for enabled in (False, True):
        group = sound()
        group.classification = "unknown"
        group.text = group.lines[0].text = "BLAZE"
        group.ignored = True
        group.ignore_reason = "weak_unknown_text"
        with patch.object(ob.config, "TRANSLATE_SFX", enabled):
            ob._promote_glossary_sounds([group])
            assert group.classification == "sfx"
            assert ob.get_cleanable_translatable_groups([group]) == [group]
            assert bool(ob.get_translatable_groups([group])) is enabled


def test_frozen_glossary_sound_with_stale_weak_ignore_still_enters_clean():
    group = sound()
    group.ignored = True
    group.ignore_reason = "weak_unknown_text"
    group.classification_reason = "glossary_sound_outside_balloon"
    assert ob.get_cleanable_translatable_groups([group]) == [group]


def test_partial_v4_mask_tries_existing_component_extractor_without_waiving_guard():
    group = sound()
    source = np.full((60, 80, 3), 180, np.uint8)
    partial = np.zeros(source.shape[:2], np.uint8)
    partial[10:20, 10:20] = 255
    with patch.object(ob, "_sfx_glyph_halo_mask", return_value=(partial,
            {"text_component_pixels": 1, "sfx_glyph_halo_mask": True})), patch.object(
        ob, "_component_text_mask", return_value=(np.zeros_like(partial),
            {"text_component_pixels": 0})) as fallback:
        result, mask, metrics = ob._remove_text_for_group(source, source, group)
    fallback.assert_called_once()
    assert not metrics["mask_valid"] and not mask.any()
    np.testing.assert_array_equal(result, source)


def test_stylized_sound_above_detection_floor_does_not_require_a_dictionary_word_to_clean():
    group = sound()
    group.text = "CRAdKVE"
    group.lines[0].text = group.text
    group.lines[0].confidence = .61
    assert ob._ocr_unintelligible_source_text(group.text)
    with patch.object(ob.config, "TRANSLATE_SFX", False):
        assert ob.get_cleanable_translatable_groups([group]) == [group]
    group.lines[0].confidence = .5
    assert ob.get_cleanable_translatable_groups([group]) == []


def test_preference_is_boolean_persistent_and_does_not_reset_other_settings(tmp_path):
    store = CommunityStore(tmp_path / "community.db")
    try:
        store.save_user_settings("user", {"theme": "rubra"})
        saved = store.save_user_settings("user", {"translate_sfx": True})
        assert saved["translate_sfx"] is True
        assert saved["theme"] == "rubra"
        assert store.user_settings("other")["translate_sfx"] is False
        assert store.save_user_settings("user", {"translate_sfx": "false"})["translate_sfx"] is False
    finally:
        store.close()


def test_job_snapshot_does_not_use_truthy_string_for_sfx():
    for value, expected in [(True, True), (False, False), ("false", False)]:
        normalized = {"translation_provider": "deepl", "translate_sfx": value}
        snapshot = UiBridge._translation_configuration_snapshot({}, normalized)
        assert snapshot["translate_sfx"] is expected


def test_folder_uses_shell_action_after_root_validation(tmp_path):
    folder = tmp_path / "run"
    folder.mkdir()
    bridge = UiBridge.__new__(UiBridge)
    bridge.output_root = tmp_path
    with patch("yomu.ui.ui_bridge.os.startfile", create=True) as shell, patch.object(
        bridge, "_focus_explorer_window"
    ) as focus:
        bridge._open_artifact_path(str(folder))
    if os.name == "nt":
        shell.assert_called_once_with(str(folder.resolve()), "explore")
        focus.assert_called_once_with(folder.name)


def test_sweep_overlaps_other_page_analysis_and_preserves_order():
    # Deterministic concurrency proof: sweep for page 1 must start before page 2
    # can finish analysis. The former end-of-phase sweep could not do this.
    sweep_started = threading.Event()
    def analysis(context, **kwargs):
        if context.page_index == 2:
            assert sweep_started.wait(2), "sweep was deferred until all analysis completed"
        return PreTranslationPageResult(page_index=context.page_index, analyzable=True,
                                        page_state={"index": context.page_index})
    def sweep(result, state):
        sweep_started.set()
        return replace(result, timings={"residual_sweep": .1})
    with patch.object(bp, "_pipeline_page_workers", return_value=2), patch.object(
        bp, "process_pre_translation_page", side_effect=analysis
    ), patch.object(bp, "_auto_fix_residual_sfx", side_effect=sweep) as swept:
        results = bp.process_pre_translation_pages(
            [{"index": 1}, {"index": 2}], image_paths=[], ocr_lang="eng",
            fast_ocr_budget=None, errors_folder=".", include_residual_sweep=True)
    assert swept.call_count == 2
    assert [result.page_index for result in results] == [1, 2]
