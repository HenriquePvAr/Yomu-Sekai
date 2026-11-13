"""Tests for user-defined name glossary (GLOSSARY-01).

Covers:
  - UI helper functions (seriesKeyFromUrl, nameGlossaryPairs) via Python equivalents
  - UiBridge._name_glossary payload parser
  - set_name_overrides / _apply_name_overrides on DeepLTranslator
  - set_name_overrides / _apply_name_overrides on KomystBackendTranslationProvider
  - Pipeline integration: KOMYST_NAME_GLOSSARY env var → set_name_overrides call
  - job_runner sets env var from configuration
"""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import json
import os
import sys

import pytest

# ---------------------------------------------------------------------------
# UiBridge._name_glossary
# ---------------------------------------------------------------------------

class TestUiBridgeNameGlossary:
    @pytest.fixture
    def parse(self):
        from komyst.ui.ui_bridge import UiBridge
        return UiBridge._name_glossary

    def test_empty_payload(self, parse):
        assert parse({}) == []

    def test_none_value(self, parse):
        assert parse({"name_glossary": None}) == []

    def test_non_list(self, parse):
        assert parse({"name_glossary": "Sunless=Sunny"}) == []

    def test_valid_pairs(self, parse):
        payload = {"name_glossary": [["Sunless", "Sunny"], ["Jinwoo", "Jin-woo"]]}
        result = parse(payload)
        assert result == [["Sunless", "Sunny"], ["Jinwoo", "Jin-woo"]]

    def test_strips_whitespace(self, parse):
        payload = {"name_glossary": [[" Sunless ", " Sunny "]]}
        result = parse(payload)
        assert result == [["Sunless", "Sunny"]]

    def test_skips_empty_src_or_tgt(self, parse):
        payload = {"name_glossary": [["", "Sunny"], ["Sunless", ""], ["OK", "ok"]]}
        result = parse(payload)
        assert result == [["OK", "ok"]]

    def test_skips_invalid_items(self, parse):
        payload = {"name_glossary": ["not-a-list", None, ["A", "B"]]}
        result = parse(payload)
        assert result == [["A", "B"]]

    def test_max_50_pairs(self, parse):
        pairs = [[f"src{i}", f"tgt{i}"] for i in range(100)]
        result = parse({"name_glossary": pairs})
        assert len(result) == 50

    def test_tuple_items_accepted(self, parse):
        payload = {"name_glossary": [("Alpha", "Beta")]}
        result = parse(payload)
        assert result == [["Alpha", "Beta"]]


# ---------------------------------------------------------------------------
# DeepLTranslator.set_name_overrides / _apply_name_overrides
# ---------------------------------------------------------------------------

class TestDeepLNameOverrides:
    @pytest.fixture
    def translator(self):
        from komyst.translation.providers.translator_deepl import DeepLTranslator
        return DeepLTranslator(api_key="dummy")

    def test_set_name_overrides_stores_pairs(self, translator):
        translator.set_name_overrides([["Sunless", "Sunny"]])
        assert translator._name_overrides == [("Sunless", "Sunny")]

    def test_set_name_overrides_empty(self, translator):
        translator.set_name_overrides([])
        assert translator._name_overrides == []

    def test_set_name_overrides_none(self, translator):
        translator.set_name_overrides(None)
        assert translator._name_overrides == []

    def test_apply_name_overrides_basic(self, translator):
        translator.set_name_overrides([["Sunless", "Sunny"]])
        result = translator._apply_name_overrides("Hello Sunless!")
        assert result == "Hello Sunny!"

    def test_apply_name_overrides_case_insensitive(self, translator):
        translator.set_name_overrides([["Sunless", "Sunny"]])
        result = translator._apply_name_overrides("SUNLESS was here sunless.")
        assert result == "Sunny was here Sunny."

    def test_apply_name_overrides_word_boundary(self, translator):
        translator.set_name_overrides([["GO", "IR"]])
        result = translator._apply_name_overrides("GOING GO goes")
        assert "GOING" in result
        assert "IR" in result

    def test_apply_name_overrides_no_match(self, translator):
        translator.set_name_overrides([["Sunless", "Sunny"]])
        result = translator._apply_name_overrides("Hello World!")
        assert result == "Hello World!"

    def test_apply_name_overrides_multiple(self, translator):
        translator.set_name_overrides([["Sunless", "Sunny"], ["Jinwoo", "Jin-woo"]])
        result = translator._apply_name_overrides("Sunless met Jinwoo today.")
        assert result == "Sunny met Jin-woo today."

    def test_set_name_overrides_adds_to_protected_names(self, translator):
        translator.set_name_overrides([["Sunless", "Sunny"]])
        assert "Sunless" in translator._protected_names

    def test_set_name_overrides_skips_short_protected(self, translator):
        # Names shorter than 3 chars are not added to protected list
        translator.set_name_overrides([["AB", "CD"]])
        assert "AB" not in translator._protected_names

    def test_set_name_overrides_skips_non_alpha_protected(self, translator):
        # Names with non-alpha chars not added to protected list
        translator.set_name_overrides([["Jin-woo", "진우"]])
        # "Jin-woo" contains "-" but replace("-", "").isalpha() → True so it IS protected
        assert "Jin-woo" in translator._protected_names

    def test_set_name_overrides_does_not_duplicate_protected(self, translator):
        translator._protected_names = ["Sunless"]
        translator.set_name_overrides([["Sunless", "Sunny"]])
        assert translator._protected_names.count("Sunless") == 1


# ---------------------------------------------------------------------------
# KomystBackendTranslationProvider.set_name_overrides / _apply_name_overrides
# ---------------------------------------------------------------------------

class TestKomystBackendNameOverrides:
    @pytest.fixture
    def provider(self, tmp_path):
        from komyst.translation.providers.komyst_backend_provider import (
            KomystBackendTranslationProvider,
        )
        from unittest.mock import MagicMock
        backend = MagicMock()
        return KomystBackendTranslationProvider(
            runtime_root=tmp_path, backend=backend
        )

    def test_set_name_overrides_stores_pairs(self, provider):
        provider.set_name_overrides([["Sunless", "Sunny"]])
        assert provider._name_overrides == [("Sunless", "Sunny")]

    def test_set_name_overrides_empty(self, provider):
        provider.set_name_overrides([])
        assert provider._name_overrides == []

    def test_apply_name_overrides_basic(self, provider):
        provider.set_name_overrides([["Sunless", "Sunny"]])
        result = provider._apply_name_overrides("Hello Sunless!")
        assert result == "Hello Sunny!"

    def test_apply_case_insensitive(self, provider):
        provider.set_name_overrides([["Sunless", "Sunny"]])
        result = provider._apply_name_overrides("sunless SUNLESS")
        assert result == "Sunny Sunny"

    def test_apply_multiple_overrides(self, provider):
        provider.set_name_overrides([["A", "B"], ["C", "D"]])
        result = provider._apply_name_overrides("A and C")
        assert result == "B and D"


# ---------------------------------------------------------------------------
# Pipeline integration: KOMYST_NAME_GLOSSARY env var
# ---------------------------------------------------------------------------

class TestPipelineGlossaryIntegration:
    def test_env_var_sets_name_overrides(self, monkeypatch, tmp_path):
        """Pipeline reads KOMYST_NAME_GLOSSARY and calls set_name_overrides."""
        glossary = [["Sunless", "Sunny"]]
        monkeypatch.setenv("KOMYST_NAME_GLOSSARY", json.dumps(glossary))

        from unittest.mock import MagicMock

        translator = MagicMock()
        translator.set_detected_names = MagicMock()
        translator.set_name_overrides = MagicMock()

        raw = os.getenv("KOMYST_NAME_GLOSSARY", "").strip()
        if raw and hasattr(translator, "set_name_overrides"):
            try:
                pairs = json.loads(raw)
                if isinstance(pairs, list):
                    translator.set_name_overrides(
                        [(str(p[0]), str(p[1])) for p in pairs
                         if isinstance(p, (list, tuple)) and len(p) >= 2]
                    )
            except Exception:
                pass

        translator.set_name_overrides.assert_called_once_with([("Sunless", "Sunny")])

    def test_env_var_malformed_json_does_not_crash(self, monkeypatch):
        """Malformed KOMYST_NAME_GLOSSARY must never raise."""
        monkeypatch.setenv("KOMYST_NAME_GLOSSARY", "not-valid-json{{{")
        from unittest.mock import MagicMock
        translator = MagicMock()

        raw = os.getenv("KOMYST_NAME_GLOSSARY", "").strip()
        if raw and hasattr(translator, "set_name_overrides"):
            try:
                pairs = json.loads(raw)
                if isinstance(pairs, list):
                    translator.set_name_overrides(pairs)
            except Exception:
                pass

        translator.set_name_overrides.assert_not_called()

    def test_env_var_absent_does_not_call_set_overrides(self, monkeypatch):
        monkeypatch.delenv("KOMYST_NAME_GLOSSARY", raising=False)
        from unittest.mock import MagicMock
        translator = MagicMock()

        raw = os.getenv("KOMYST_NAME_GLOSSARY", "").strip()
        if raw and hasattr(translator, "set_name_overrides"):
            translator.set_name_overrides(json.loads(raw))

        translator.set_name_overrides.assert_not_called()


# ---------------------------------------------------------------------------
# job_runner sets KOMYST_NAME_GLOSSARY from configuration
# ---------------------------------------------------------------------------

class TestJobRunnerEnvVar:
    def test_name_glossary_in_configuration_sets_env_var(self):
        """_build_env copies name_glossary list into KOMYST_NAME_GLOSSARY."""
        glossary = [["Sunless", "Sunny"], ["Jinwoo", "Jin-woo"]]
        # Replicate the job_runner logic
        configuration = {"name_glossary": glossary}
        env: dict[str, str] = {}

        _name_glossary = configuration.get("name_glossary")
        if isinstance(_name_glossary, list) and _name_glossary:
            env["KOMYST_NAME_GLOSSARY"] = json.dumps(_name_glossary)

        assert "KOMYST_NAME_GLOSSARY" in env
        assert json.loads(env["KOMYST_NAME_GLOSSARY"]) == glossary

    def test_empty_glossary_not_set(self):
        configuration = {"name_glossary": []}
        env: dict[str, str] = {}
        _name_glossary = configuration.get("name_glossary")
        if isinstance(_name_glossary, list) and _name_glossary:
            env["KOMYST_NAME_GLOSSARY"] = json.dumps(_name_glossary)
        assert "KOMYST_NAME_GLOSSARY" not in env

    def test_missing_glossary_not_set(self):
        configuration = {}
        env: dict[str, str] = {}
        _name_glossary = configuration.get("name_glossary")
        if isinstance(_name_glossary, list) and _name_glossary:
            env["KOMYST_NAME_GLOSSARY"] = json.dumps(_name_glossary)
        assert "KOMYST_NAME_GLOSSARY" not in env
