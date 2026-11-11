"""Subprocess OCR gateway: heavy engines run isolated, crashes never kill the pipeline."""
import json
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import pytest

from yomu.ocr.subprocess_ocr import SubprocessOcrGateway

STUB_WORKER = Path(__file__).resolve().parent / "_stub_ocr_worker.py"


@pytest.fixture
def stub_gateway(tmp_path):
    (tmp_path / "stub.py").write_text(
        "import json, sys\n"
        "for line in sys.stdin:\n"
        '    req = json.loads(line)\n'
        '    sys.stdout.write(json.dumps({"id": req["id"], "reads": ["CLANK"]}) + "\\n")\n'
        "    sys.stdout.flush()\n",
        encoding="utf-8",
    )
    gateway = SubprocessOcrGateway(worker_cmd=[sys.executable, str(tmp_path / "stub.py")])
    yield gateway
    gateway.shutdown()


def test_gateway_roundtrip(stub_gateway):
    image = np.zeros((40, 80, 3), np.uint8)
    assert stub_gateway.reads(image) == ["CLANK"]
    assert stub_gateway.reads(image) == ["CLANK"]


def test_gateway_restarts_once_then_fails_closed(stub_gateway):
    image = np.zeros((40, 80, 3), np.uint8)
    assert stub_gateway.reads(image) == ["CLANK"]
    # Simulate a native crash: kill the child. The retry re-spawns and serves.
    stub_gateway._process.kill()
    assert stub_gateway.reads(image) == ["CLANK"]
    # Second crash exhausts the restart budget -> unavailable (None), not an exception.
    stub_gateway._process.kill()
    assert stub_gateway.reads(image) is None
    assert stub_gateway.unavailable_reason
    # Stays unavailable without further spawning.
    assert stub_gateway.reads(image) is None


def test_gateway_skips_non_json_protocol_noise(tmp_path):
    (tmp_path / "noisy.py").write_text(
        "import json, sys\n"
        'print("ReduceMeanCheckIfOneDNNSupport")\n'
        "sys.stdout.flush()\n"
        "for line in sys.stdin:\n"
        '    req = json.loads(line)\n'
        '    sys.stdout.write("junk line\\n")\n'
        '    sys.stdout.write(json.dumps({"id": req["id"], "reads": ["PÁ"]}) + "\\n")\n'
        "    sys.stdout.flush()\n",
        encoding="utf-8",
    )
    gateway = SubprocessOcrGateway(worker_cmd=[sys.executable, str(tmp_path / "noisy.py")])
    try:
        assert gateway.reads(np.zeros((20, 20, 3), np.uint8)) == ["PÁ"]
    finally:
        gateway.shutdown()


def test_spawn_failure_is_unavailable(tmp_path):
    gateway = SubprocessOcrGateway(worker_cmd=["/nonexistent/binary.exe"])
    assert gateway.reads(np.zeros((8, 8, 3), np.uint8)) is None
    assert "spawn_failed" in gateway.unavailable_reason


def test_gateway_spawn_is_hidden_and_preserves_protocol_pipes(monkeypatch):
    import os
    observed = {}
    def spawn(command, **kwargs):
        observed.update(kwargs)
        return object()
    monkeypatch.setattr(subprocess, "Popen", spawn)
    gateway = SubprocessOcrGateway(worker_cmd=["test-ocr-worker"])
    assert gateway._spawn()
    assert observed["stdin"] == subprocess.PIPE
    assert observed["stdout"] == subprocess.PIPE
    assert observed["stderr"] == subprocess.DEVNULL
    assert observed["shell"] is False
    if os.name == "nt":
        assert observed["creationflags"] & subprocess.CREATE_NO_WINDOW
        assert observed["startupinfo"].dwFlags & subprocess.STARTF_USESHOWWINDOW


def test_phase_release_stops_worker_and_later_read_can_reopen(stub_gateway, monkeypatch):
    from yomu.ocr import subprocess_ocr as so
    image = np.zeros((40,80,3), np.uint8)
    assert stub_gateway.reads(image) == ["CLANK"]
    process = stub_gateway._process
    monkeypatch.setattr(so, "_gateway", stub_gateway)
    command = stub_gateway._worker_cmd
    factory = so.SubprocessOcrGateway
    monkeypatch.setattr(so, "SubprocessOcrGateway", lambda: factory(worker_cmd=command))
    so.shutdown_subprocess_ocr()
    assert process.poll() is not None and so._gateway is None
    try:
        assert so.subprocess_paddle_reads(image) == ["CLANK"]
        assert so._gateway._process.pid != process.pid
    finally:
        so.shutdown_subprocess_ocr()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows headless dependency policy")
def test_dependency_children_are_hidden_without_losing_pipes_or_group_flags(monkeypatch):
    from yomu.runtime.process_options import configure_headless_subprocesses
    observed = {}
    class OriginalPopen:
        def __init__(self, *args, **kwargs):
            observed.update(kwargs)
    monkeypatch.setattr(subprocess, "Popen", OriginalPopen)
    configure_headless_subprocesses()
    installed = subprocess.Popen
    configure_headless_subprocesses()
    assert subprocess.Popen is installed
    startup = subprocess.STARTUPINFO()
    subprocess.Popen(["where.exe", "ccache"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     startupinfo=startup, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    assert observed["creationflags"] & subprocess.CREATE_NO_WINDOW
    assert observed["creationflags"] & subprocess.CREATE_NEW_PROCESS_GROUP
    assert observed["stdout"] == observed["stdin"] == subprocess.PIPE
    assert observed["startupinfo"] is not startup
    assert not startup.dwFlags & subprocess.STARTF_USESHOWWINDOW
    assert observed["startupinfo"].dwFlags & subprocess.STARTF_USESHOWWINDOW


@pytest.mark.skipif(sys.platform != "win32", reason="Windows console attachment")
def test_hidden_child_has_no_attached_console_and_keeps_stdout():
    from yomu.runtime.process_options import hidden_console_options
    result = subprocess.run([sys.executable, "-c",
        "import ctypes; print(int(bool(ctypes.windll.kernel32.GetConsoleWindow())))"],
        capture_output=True, text=True, timeout=10, **hidden_console_options())
    assert result.returncode == 0
    assert result.stdout.strip() == "0"
