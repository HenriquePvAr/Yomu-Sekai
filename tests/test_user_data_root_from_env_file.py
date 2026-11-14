r"""The data root in the project .env must apply to every process, not only after `settings` is imported.

The launcher and the worker resolve the runtime folder before importing settings, so a process started
without KOMYST_USER_DATA_ROOT in its environment used %LOCALAPPDATA%\Komyst while the UI used the data
root from .env: the resumed job sat in one queue and the worker polled another, silently.
"""
from pathlib import Path

import pytest

from komyst.runtime import local_environment, runtime_paths


@pytest.fixture()
def clean_env(monkeypatch, tmp_path):
    for name in ("KOMYST_USER_DATA_ROOT", "KOMYST_RUNTIME_ISOLATION_GUARD", "KOMYST_HERMETIC_TEST_ENV",
                 "KOMYST_TEST_RUNTIME_ROOT"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setattr(runtime_paths, "_PROJECT_ENV_LOADED", False, raising=False)
    return tmp_path


def test_data_root_comes_from_the_project_env_file_when_the_process_has_none(clean_env, monkeypatch):
    env_file = clean_env / ".env"
    env_file.write_text(f"KOMYST_USER_DATA_ROOT={clean_env / 'data'}\n", encoding="utf-8")
    monkeypatch.setattr(local_environment, "LOCAL_ENV_PATH", env_file)
    monkeypatch.setattr(local_environment, "LOCAL_ENV_OVERRIDE_PATH", clean_env / ".env.local")

    assert runtime_paths.default_user_data_root() == clean_env / "data"
    assert runtime_paths.runtime_root() == clean_env / "data" / "runtime"


def test_a_value_already_in_the_process_environment_wins(clean_env, monkeypatch):
    env_file = clean_env / ".env"
    env_file.write_text(f"KOMYST_USER_DATA_ROOT={clean_env / 'from_file'}\n", encoding="utf-8")
    monkeypatch.setattr(local_environment, "LOCAL_ENV_PATH", env_file)
    monkeypatch.setenv("KOMYST_USER_DATA_ROOT", str(clean_env / "from_process"))

    assert runtime_paths.default_user_data_root() == clean_env / "from_process"


def test_without_any_configuration_the_local_app_data_default_is_kept(clean_env, monkeypatch):
    monkeypatch.setattr(local_environment, "LOCAL_ENV_PATH", clean_env / "missing.env")
    monkeypatch.setattr(local_environment, "LOCAL_ENV_OVERRIDE_PATH", clean_env / "missing.local")

    assert runtime_paths.default_user_data_root() == clean_env / "local" / runtime_paths.APP_DIR_NAME


def test_a_broken_env_file_does_not_break_path_resolution(clean_env, monkeypatch):
    env_file = clean_env / ".env"
    env_file.write_text("THIS IS NOT = = VALID\n=\n", encoding="utf-8")
    monkeypatch.setattr(local_environment, "LOCAL_ENV_PATH", env_file)

    assert isinstance(runtime_paths.default_user_data_root(), Path)
