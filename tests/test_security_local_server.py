"""Local-server security contract: trace path safety, owner scoping, Host/Origin guard.

Hermetic: stub ASGI app, temporary job store and runtime root, no network, no worker.
"""

from __future__ import annotations

import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

import komyst.ui.app as app_ui
from komyst.community.community_auth import RequestPrincipal
from komyst.runtime.job_store import JobStatus, JobStore
from komyst.ui.ui_bridge import UiBridge

JOB_A = "a" * 32
JOB_B = "b" * 32
JSON_HEADERS = {"content-type": "application/json"}


class _Req:
    def __init__(self, body, headers=None):
        self._body = body
        self.headers = headers if headers is not None else dict(JSON_HEADERS)

    async def json(self):
        return self._body


def _principal(owner):
    return RequestPrincipal(
        user_id=owner, authenticated=True, roles=frozenset({"user"}),
        auth_source="local_test", session_id="s-" + owner)


# ---- M3: /api/ui/source-trace -------------------------------------------------

@pytest.mark.parametrize("bad", ["../x", "..\\x", "/../../x", "a/b", "a\\b", "x" * 81, "..", "a b"])
def test_source_trace_rejects_unsafe_trace_id(tmp_path, monkeypatch, bad):
    monkeypatch.setattr(app_ui, "DIAGNOSTICS_ROOT", tmp_path / "diag")
    (tmp_path / "diag").mkdir()
    with pytest.raises(HTTPException) as err:
        asyncio.run(app_ui.api_source_trace(_Req({"trace_id": bad})))
    assert err.value.status_code == 400
    assert not list(tmp_path.rglob("*.jsonl"))


def test_source_trace_writes_only_inside_diagnostics_root(tmp_path, monkeypatch):
    root = tmp_path / "diag"
    root.mkdir()
    monkeypatch.setattr(app_ui, "DIAGNOSTICS_ROOT", root)
    asyncio.run(app_ui.api_source_trace(_Req({"trace_id": "abc-1.2_x", "event": "E"})))
    files = list(tmp_path.rglob("*.jsonl"))
    assert [f.parent for f in files] == [root]


def test_source_trace_requires_json_content_type_and_local_origin(tmp_path, monkeypatch):
    monkeypatch.setattr(app_ui, "DIAGNOSTICS_ROOT", tmp_path)
    with pytest.raises(HTTPException) as plain:
        asyncio.run(app_ui.api_source_trace(_Req({"trace_id": "a"}, {"content-type": "text/plain"})))
    assert plain.value.status_code == 415
    with pytest.raises(HTTPException) as foreign:
        asyncio.run(app_ui.api_source_trace(_Req(
            {"trace_id": "a"}, {**JSON_HEADERS, "origin": "https://evil.example"})))
    assert foreign.value.status_code == 403


# ---- B5/B6/B7/I7: Host / Origin guard -----------------------------------------

def _guarded_client():
    async def inner(scope, receive, send):
        await JSONResponse({"ok": True})(scope, receive, send)

    return TestClient(
        app_ui.LocalRequestGuardMiddleware(inner),
        base_url=f"http://127.0.0.1:{app_ui.APP_PORT}", client=("127.0.0.1", 50000))


def test_host_outside_allow_list_is_400():
    client = _guarded_client()
    assert client.get("/x").status_code == 200
    assert client.get("/x", headers={"host": f"localhost:{app_ui.APP_PORT}"}).status_code == 200
    assert client.get("/x", headers={"host": "evil.example"}).status_code == 400
    assert client.get("/x", headers={"host": f"127.0.0.1:{app_ui.APP_PORT + 1}"}).status_code == 400


def test_foreign_origin_is_refused_on_state_changes_only():
    client = _guarded_client()
    assert client.post("/x", headers={"origin": "https://evil.example"}).status_code == 403
    assert client.delete("/x", headers={"origin": "null"}).status_code == 403
    same = f"http://localhost:{app_ui.APP_PORT}"
    assert client.post("/x", headers={"origin": same}).status_code == 200
    assert client.post("/x").status_code == 200  # no Origin: curl/urllib/tests
    assert client.get("/x", headers={"origin": "https://evil.example"}).status_code == 200


def test_socketio_handshake_with_foreign_origin_is_refused():
    client = _guarded_client()
    assert client.get("/_nicegui_ws/socket.io/", headers={"origin": "https://evil.example"}).status_code == 403


def test_guard_is_installed_on_the_real_app():
    assert any(m.cls is app_ui.LocalRequestGuardMiddleware for m in app_ui.app.user_middleware)


def test_telemetry_and_client_state_require_json(monkeypatch):
    monkeypatch.setenv("KOMYST_RUNTIME_MODE", "desktop")
    for call in (app_ui.api_control_plane_trace, app_ui.desktop_client_state):
        with pytest.raises(HTTPException) as err:
            asyncio.run(call(_Req({}, {"content-type": "text/plain"})))
        assert err.value.status_code == 415


def test_update_routes_require_an_authenticated_user(monkeypatch):
    def deny(request, mutate=False):
        raise HTTPException(status_code=401, detail="authentication_required")

    monkeypatch.setattr(app_ui, "_ui_principal", deny)
    called = []
    monkeypatch.setattr(app_ui.update_transport, "UpdateTransport", lambda: called.append(1))
    for call, args in (
        (app_ui.api_update_download, (SimpleNamespace(headers={}),)),
        (app_ui.api_update_install, (SimpleNamespace(headers={}), {"handoff_token": "t"})),
        (app_ui.api_update_download_cancel, (SimpleNamespace(headers={}), "t")),
    ):
        with pytest.raises(HTTPException) as err:
            call(*args)
        assert err.value.status_code == 401
    assert not called


# ---- M4: history delete scoped to owner ---------------------------------------

def _bridge_with_job(tmp_path, owner):
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.create_job(
        job_id=JOB_A, source_url="", output_dir=str(tmp_path / "output" / JOB_A),
        command=["offline-fixture"],
        configuration={"job_type": "translation", "community_owner_id": owner,
                       "ownership_schema_version": 1},
        initial_status=JobStatus.QUEUED)
    store._conn.execute("UPDATE jobs SET status=? WHERE id=?", (JobStatus.FINISHED, JOB_A))
    store._conn.commit()
    bridge = UiBridge.__new__(UiBridge)
    bridge.store = store
    bridge.output_root = tmp_path / "output"
    bridge._history_payload = lambda: []
    bridge.history_store = SimpleNamespace(load=lambda: [])
    bridge._job_record = lambda job: {
        "id": job["id"], "job_id": job["id"], "run_id": job.get("run_id"),
        "output_folder": job["output_dir"], "slug": "s"}
    return bridge, store


def test_other_owner_cannot_resolve_or_delete_a_history_record(tmp_path):
    bridge, store = _bridge_with_job(tmp_path, "owner-a")
    try:
        record, _ = bridge._find_local_artifact_record(JOB_A, "owner-a")
        assert record["job_id"] == JOB_A
        with pytest.raises(ValueError, match="local_artifact_not_found"):
            bridge._find_local_artifact_record(JOB_A, "owner-b")
        with pytest.raises(ValueError, match="local_artifact_not_found"):
            bridge.delete_local_artifact(
                JOB_A, delete_files=True, confirm="EXCLUIR", owner_id="owner-b")
        # history file records bound to a job of another owner are invisible too
        bridge.history_store = SimpleNamespace(load=lambda: [{"id": "h1", "job_id": JOB_A}])
        with pytest.raises(ValueError, match="local_artifact_not_found"):
            bridge._find_local_artifact_record("h1", "owner-b")
    finally:
        store.close()


def test_history_delete_route_returns_404_for_another_owner(tmp_path, monkeypatch):
    bridge, store = _bridge_with_job(tmp_path, "owner-a")
    monkeypatch.setattr(app_ui, "BRIDGE", bridge)
    monkeypatch.setattr(app_ui, "_ui_principal", lambda request, mutate=False: _principal("owner-b"))
    try:
        with pytest.raises(HTTPException) as err:
            app_ui.api_history_delete(
                SimpleNamespace(), {"local_artifact_id": JOB_A, "confirmation": "EXCLUIR"})
        assert err.value.status_code == 404
    finally:
        store.close()


# ---- B8: refinement decision job binding --------------------------------------

def test_refinement_decision_with_divergent_job_is_400(monkeypatch):
    monkeypatch.setattr(app_ui, "_owned_ui_job", lambda *a, **k: _principal("owner-a"))
    with pytest.raises(HTTPException) as err:
        app_ui.api_human_translation_refinement_decision(
            SimpleNamespace(),
            {"job_id": "mine", "option": "keep_current",
             "result": {"request": {"job_id": "someone-elses"}}})
    assert err.value.status_code == 400


# ---- B9: editor assets bound to their job -------------------------------------

def test_editor_asset_of_another_job_is_404(tmp_path, monkeypatch):
    bridge = UiBridge.__new__(UiBridge)
    bridge.runtime_root = tmp_path
    folder = tmp_path / "human_mask_editor" / "tok"
    folder.mkdir(parents=True)
    (folder / "a.png").write_bytes(b"x")
    bridge._bind_asset_dir(folder, JOB_A)
    assert bridge.human_mask_editor_asset("human_mask_editor/tok/a.png", JOB_A).is_file()
    for other in (JOB_B, ""):
        with pytest.raises(ValueError):
            bridge.human_mask_editor_asset("human_mask_editor/tok/a.png", other)

    monkeypatch.setattr(app_ui, "BRIDGE", bridge)
    monkeypatch.setattr(app_ui, "_owned_ui_job", lambda *a, **k: _principal("owner-b"))
    with pytest.raises(HTTPException) as err:
        app_ui.api_human_mask_asset(
            SimpleNamespace(), job_id=JOB_B, asset="human_mask_editor/tok/a.png")
    assert err.value.status_code == 404


# ---- B11: quality report escapes ----------------------------------------------

def test_quality_report_html_escapes_url_and_pdf_path():
    from komyst.pipeline.benchmark_pipeline import _quality_report_html

    evil = '"><script>alert(1)</script>'
    page_report = {
        "summary": {"url": evil, "ocr_engine": "<b>", "ocr_fallback_engine": "x",
                    "pdf_path": f"C:/out/{evil}.pdf", "processed_images": 0, "total_seconds": 0},
        "totals": {"k": evil},
        "pages": [],
    }
    out = _quality_report_html(page_report)
    assert "<script>alert" not in out
    assert "&lt;script&gt;" in out and "&quot;" in out
