import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

from unittest import mock

import pytest

from yomu.ui import source_previews as previews


def test_unknown_source_never_starts_browser():
    with mock.patch.object(previews.threading, "Thread") as thread:
        with pytest.raises(ValueError):
            previews.source_preview("https://localhost/private")
        thread.assert_not_called()


def test_one_refresh_per_source_and_cache_expires():
    with mock.patch.object(previews, "_cache", {}), \
            mock.patch.object(previews.threading, "Thread") as thread, \
            mock.patch.object(previews.time, "monotonic", return_value=100):
        assert previews.source_preview("vortex")["refreshing"]
        previews.source_preview("vortex")
        assert thread.call_count == 1
        with mock.patch.object(previews, "_capture", return_value="data:image/jpeg;base64,YQ=="):
            previews._refresh("vortex")
        first = previews.source_preview("vortex")
        assert first["image"] and not first["refreshing"]
        assert thread.call_count == 1
        with mock.patch.object(previews.time, "monotonic", return_value=161):
            assert previews.source_preview("vortex")["refreshing"]
        assert thread.call_count == 2


def test_failed_refresh_preserves_last_good_preview_and_timestamp():
    entry = {"image": "last-good", "captured_at": 42, "refreshing": True, "error": False}
    with mock.patch.object(previews, "_cache", {"webtoon": entry}), \
            mock.patch.object(previews, "_capture", side_effect=RuntimeError("private details")):
        previews._refresh("webtoon")
    assert entry["image"] == "last-good"
    assert entry["captured_at"] == 42
    assert entry["error"] and not entry["refreshing"]
