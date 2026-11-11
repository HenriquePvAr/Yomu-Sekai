import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

from yomu.pipeline.benchmark_pipeline import _sfx_policy_summary


def test_unignored_sfx_not_sent_is_valid_when_translation_disabled():
    result = _sfx_policy_summary([
        {"classification": "sfx", "ignored": False, "sent_to_nvidia": False}
    ], translate_sfx=False)
    assert result["sfx_policy_valid"] is True
    assert result["sfx_not_ignored_groups"] == 1
    assert result["sfx_sent_to_provider_groups"] == 0


def test_sfx_sent_to_provider_violates_policy_when_translation_disabled():
    result = _sfx_policy_summary([
        {"classification": "sfx", "ignored": False, "sent_to_nvidia": True}
    ], translate_sfx=False)
    assert result["sfx_policy_valid"] is False
    assert result["sfx_sent_to_provider_groups"] == 1


def test_enabled_sfx_translation_allows_sfx_sent_to_provider():
    result = _sfx_policy_summary([
        {"classification": "sfx", "ignored": False, "sent_to_nvidia": True}
    ], translate_sfx=True)
    assert result["sfx_policy_valid"] is True
