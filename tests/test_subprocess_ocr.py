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
