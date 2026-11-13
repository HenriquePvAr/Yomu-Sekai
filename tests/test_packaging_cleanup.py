"""Installer cleanup contract for the beta desktop package."""

from pathlib import Path
import re
from komyst.review.source_readiness import SourceReadinessStore, default_workspace_id
from komyst.ui.ui_bridge import UiBridge


ROOT = Path(__file__).resolve().parents[1]
ISS = ROOT / "packaging" / "Komyst.iss"


def test_uninstaller_cleans_volatile_state_without_removing_device_identity():
    script = ISS.read_text(encoding="utf-8")
    assert "[UninstallDelete]" in script
    for path in (
        r"{localappdata}\Komyst\runtime\jobs.sqlite3",
        r"{localappdata}\Komyst\runtime\ui_history.json",
        r"{localappdata}\Komyst\runtime\logs",
        r"{localappdata}\Komyst\runtime\cache",
        r"{localappdata}\Komyst\runtime\output",
        r"{localappdata}\Komyst\runtime\temp",
        r"{localappdata}\Komyst\cache",
        r"{localappdata}\Komyst\output",
        r"{localappdata}\Komyst\temp",
    ):
        assert f'Name: "{path}"' in script
    assert r"{localappdata}\Komyst\device-identity.bin" not in script
    # Device identity and the cleaned-up runtime state now share one canonical data
    # folder (Komyst), so the regression this guards against is no longer "a second,
    # differently-named folder leaks into UninstallDelete" but "UninstallDelete grows an
    # entry that targets device-identity.bin directly, or the bare folder root (which
    # would take device-identity.bin down with it)".
    uninstall_delete_section = script.split("[UninstallDelete]", 1)[1].split("[", 1)[0]
    assert "device-identity.bin" not in uninstall_delete_section
    assert 'Name: "{localappdata}\\Komyst"' not in uninstall_delete_section


def test_installer_version_matches_single_beta_version_source():
    script = ISS.read_text(encoding="utf-8")
    assert "#ifndef ProductVersion" in script
    assert "AppVersion={#ProductVersion}" in script
    assert "OutputBaseFilename=Komyst-{#ProductVersion}-Setup-x64" in script


def test_installer_copies_onedir_contents_to_app_root():
    script = ISS.read_text(encoding="utf-8")
    assert 'Source: "{#BundleRoot}\\Komyst\\Komyst\\*"; DestDir: "{app}"' in script
    assert 'Source: "{#BundleRoot}\\Komyst\\*"; DestDir: "{app}"' not in script
    assert r"{app}\Komyst\Komyst.exe" not in script
    assert "[InstallDelete]" in script
    assert 'Type: filesandordirs; Name: "{app}\\Komyst"' in script


def test_updates_surface_has_no_beta3_visual_marker():
    shell = (ROOT / "ui" / "ui_shell.html").read_text(encoding="utf-8")
    assert 'data-update-test-marker="beta.3"' not in shell
    assert "Update test · beta.3" not in shell


def test_clean_production_workspace_seeds_safe_source_policy_once(tmp_path):
    db = tmp_path / "jobs.sqlite3"
    # The helper is the production-only path; test roots themselves intentionally
    # remain opt-in and are not auto-authorized.
    UiBridge._ensure_default_workspace_policy(db)
    store = SourceReadinessStore(db)
    try:
        policy = store.active_workspace_policy(owner="local", workspace_id=default_workspace_id(db))
        assert policy is not None
        assert policy.status == "active"
        assert policy.all_submitted_sources_authorized is True
        assert "desconhecidas" in policy.authorization_statement
    finally:
        store.close()
