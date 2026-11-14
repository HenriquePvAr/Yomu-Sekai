"""The default model folder follows the user data root; the legacy LOCALAPPDATA folder is the fallback."""
from pathlib import Path

import pytest

from komyst.runtime import runtime_paths


def _env(monkeypatch, tmp_path, *, with_user_models, with_legacy_models):
    user = tmp_path / "user"
    legacy_base = tmp_path / "local"
    monkeypatch.delenv("KOMYST_RUNTIME_ISOLATION_GUARD", raising=False)
    monkeypatch.setenv("KOMYST_USER_DATA_ROOT", str(user))
    monkeypatch.setenv("LOCALAPPDATA", str(legacy_base))
    if with_user_models:
        (user / "models").mkdir(parents=True)
    if with_legacy_models:
        (legacy_base / "Komyst" / "models").mkdir(parents=True)
    return user / "models", legacy_base / "Komyst" / "models"


def test_models_root_prefers_the_user_data_root(monkeypatch, tmp_path):
    user, _legacy = _env(monkeypatch, tmp_path, with_user_models=True, with_legacy_models=True)
    assert runtime_paths.models_root() == user


def test_models_root_falls_back_to_the_legacy_folder_when_only_it_exists(monkeypatch, tmp_path):
    _user, legacy = _env(monkeypatch, tmp_path, with_user_models=False, with_legacy_models=True)
    assert runtime_paths.models_root() == legacy


def test_models_root_defaults_to_the_user_data_root_when_nothing_exists(monkeypatch, tmp_path):
    user, _legacy = _env(monkeypatch, tmp_path, with_user_models=False, with_legacy_models=False)
    assert runtime_paths.models_root() == user


def test_models_root_does_not_raise_under_the_hermetic_guard(monkeypatch, tmp_path):
    monkeypatch.setenv("KOMYST_RUNTIME_ISOLATION_GUARD", "1")
    monkeypatch.delenv("KOMYST_TEST_RUNTIME_ROOT", raising=False)
    assert isinstance(runtime_paths.models_root(), Path)


def test_flux_model_dir_uses_the_shared_root(monkeypatch, tmp_path):
    from komyst.clean.inpainting import flux_edit

    user, _legacy = _env(monkeypatch, tmp_path, with_user_models=True, with_legacy_models=False)
    monkeypatch.setattr(flux_edit.settings, "GENERATIVE_INPAINT_MODEL_DIR", "", raising=False)
    assert flux_edit._model_dir() == user / "flux"


def test_lama_default_path_uses_the_shared_root(monkeypatch, tmp_path):
    from komyst.config import settings

    user, _legacy = _env(monkeypatch, tmp_path, with_user_models=True, with_legacy_models=False)
    assert Path(settings._default_lama_large_path()) == user / "anime_manga_lama_large.pt"
