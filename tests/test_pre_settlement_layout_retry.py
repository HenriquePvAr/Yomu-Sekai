"""Provider-backed layout retries must close before wallet settlement."""
from __future__ import annotations

from unittest import mock

import numpy as np
import pytest

import yomu.pipeline.benchmark_pipeline as bp
from yomu.ocr.ocr_balloon import TextGroup
from yomu.translation.providers.yomu_backend_provider import SystemicTranslationFailure


def _state():
    group = TextGroup(group_id="synthetic-layout", lines=[], text="Long source text")
    group.classification = "speech"
    group.sent_to_translation = True
    group.translation = "Texto inicial muito longo"
    group.translation_candidate = group.translation
    group.translation_valid = True
    group.text_overflow_ratio = 0.5
    return {
        "index": 1,
        "status": "pending",
        "original_bgr": np.zeros((80, 160, 3), dtype=np.uint8),
        "raw_lines": [],
        "candidates": [],
        "groups": [group],
        "image_path": "synthetic.png",
    }, group


def test_layout_retry_runs_while_reservation_is_held():
    state, group = _state()

    class Translator:
        def __init__(self):
            self.calls = 0

        def translate_strict(self, *_args, **_kwargs):
            self.calls += 1
            return "Curto"

    def render(*_args, **_kwargs):
        # The next dry pass sees the shortened candidate as fitting.
        if group.translation == "Curto":
            group.text_overflow_ratio = 0.0
        return state["original_bgr"], {}

    translator = Translator()
    records = []
    with mock.patch.object(bp, "render_analyzed_image", side_effect=render):
        retried = bp._resolve_layout_overflow_before_settlement(
            [state], translator, records
        )

    assert retried == 1
    assert translator.calls == 1
    assert records[0]["retry_type"] == "layout_overflow"


def test_systemic_layout_error_is_not_converted_to_regional_fallback():
    state, _group = _state()

    class Translator:
        def translate_strict(self, *_args, **_kwargs):
            raise SystemicTranslationFailure("reservation_already_settled")

    with mock.patch.object(bp, "render_analyzed_image", return_value=(state["original_bgr"], {})):
        with pytest.raises(SystemicTranslationFailure, match="reservation_already_settled"):
            bp._resolve_layout_overflow_before_settlement([state], Translator(), [])


def test_render_signature_changes_only_with_the_translation_state():
    from types import SimpleNamespace
    from yomu.pipeline.benchmark_pipeline import _translation_render_signature

    group = SimpleNamespace(translation="OI", translation_candidate="OI", translation_valid=True)
    before = _translation_render_signature([group])
    assert _translation_render_signature([group]) == before   # unchanged: preflight render reusable
    group.translation = "OLÁ"                                  # a layout retry changed it
    assert _translation_render_signature([group]) != before


def _residual_group():
    group = TextGroup(group_id="residual", lines=[], text="I'LL BE SPEAKING WITH MS. GO ALONE TODAY.")
    group.classification = "narration"
    group.sent_to_translation = True
    group.translation = "HOJE VOU CONVERSAR COM A SRA. GO ALONE."
    group.translation_valid = True
    group.visual_attempts = [{"reason": "source_tokens_detected_after_render",
                              "post_render_ocr": {"residual_source_tokens": ["GOALONE"]}}]
    return group


@pytest.mark.parametrize("answer, accepted", [
    ("HOJE VOU CONVERSAR A SÓS COM A SRA. GO.", True),
    ("HOJE CONVERSO COM A SRA. GO ALONE.", False),
])
def test_render_residual_english_is_retranslated_once(answer, accepted):
    group = _residual_group()
    calls = []

    class Translator:
        def translate_strict(self, source, **kwargs):
            calls.append(kwargs["validation_reason"])
            return answer

    records = []
    retried = bp._retry_residual_source_translations([group], Translator(), records)
    assert "GOALONE" in calls[0]
    assert retried == (1 if accepted else 0)
    assert (group.translation == answer) is accepted
    # At most two requests per region, however many preflight passes follow.
    bp._retry_residual_source_translations([group], Translator(), records)
    assert bp._retry_residual_source_translations([group], Translator(), records) == 0
    assert len(calls) == (1 if accepted else 2)
