"""Subprocess gateway for heavy OCR engines (Paddle).

Spawns ``python -m yomu.ocr.subprocess_ocr_worker`` and exchanges JSON lines
over pipes. Native engine crashes kill only the child; the gateway restarts
it once and then reports the engine as unavailable (fail-closed: callers fall
back to whatever they did before). Per-request timeout bounds a hung engine.
"""
from __future__ import annotations

import base64
import cv2
import json
import subprocess
import sys
import threading

_REQUEST_TIMEOUT_SECONDS = 45.0
_RESTART_BUDGET = 1


class SubprocessOcrGateway:
    """One gateway per pipeline process; lazily spawns the worker."""

    def __init__(self, worker_cmd: list[str] | None = None) -> None:
        self._lock = threading.Lock()
        self._worker_cmd = worker_cmd or [
            sys.executable, "-m", "yomu.ocr.subprocess_ocr_worker",
        ]
        self._process: subprocess.Popen | None = None
        self._next_id = 0
        self._restarts = 0
        self.unavailable_reason = ""

    def _spawn(self) -> bool:
        try:
            self._process = subprocess.Popen(
                self._worker_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                cwd=None,
            )
            return True
        except OSError as exc:
            self.unavailable_reason = f"spawn_failed:{exc}"
            self._process = None
            return False

    def _close(self) -> None:
        process, self._process = self._process, None
        if process is None:
            return
        try:
            if process.stdin:
                process.stdin.close()
            process.terminate()
            process.wait(timeout=5)
        except Exception:  # noqa: BLE001
            try:
                process.kill()
            except Exception:  # noqa: BLE001
                pass

    def _restart_or_give_up(self, reason: str) -> None:
        self._close()
        if self._restarts < _RESTART_BUDGET:
            self._restarts += 1
            self.unavailable_reason = ""
            self._spawn()
        else:
            self.unavailable_reason = reason

    def reads(self, image_bgr) -> list[str] | None:
        """Return the worker's reads, or ``None`` when the engine is unavailable."""
        response = self._request(image_bgr, kind="reads")
        if response is None or response.get("error"):
            return None
        return [str(read) for read in (response.get("reads") or [])]

    def sweep(self, image_bgr) -> list[dict] | None:
        """Full-page detections with boxes, or ``None`` when unavailable."""
        response = self._request(image_bgr, kind="sweep")
        if response is None or response.get("error"):
            return None
        return [dict(item) for item in (response.get("detections") or []) if isinstance(item, dict)]

    def _request(self, image_bgr, *, kind: str) -> dict | None:
        with self._lock:
            ok, encoded = cv2.imencode(".png", image_bgr)
            if not ok:
                return None
            for _attempt in range(2):
                if self._process is None:
                    if self.unavailable_reason or not self._spawn():
                        return None
                assert self._process is not None
                assert self._process.stdin is not None
                assert self._process.stdout is not None
                self._next_id += 1
                request_id = self._next_id
                payload = json.dumps({
                    "id": request_id,
                    "kind": kind,
                    "image_b64": base64.b64encode(encoded.tobytes()).decode("ascii"),
                })
                try:
                    self._process.stdin.write((payload + "\n").encode("utf-8"))
                    self._process.stdin.flush()
                    # Paddle's native oneDNN layer prints log lines ("ReduceMeanCheckIfOneDNNSupport")
                    # to stdout next to the protocol; skip everything that is not a
                    # JSON frame (bounded, so a chatty child cannot stall us forever).
                    line = b""
                    for _ in range(500):
                        line = self._process.stdout.readline()
                        if not line or line.lstrip().startswith(b"{"):
                            break
                except (OSError, ValueError):
                    self._restart_or_give_up("worker_io_dead")
                    continue
                if not line:
                    self._restart_or_give_up("worker_crashed")
                    continue
                try:
                    response = json.loads(line)
                except ValueError:
                    self._restart_or_give_up("worker_bad_frame")
                    continue
                if response.get("error"):
                    self._restart_or_give_up(str(response.get("engine_error") or response["error"]))
                    return response
                return response
            return None

    def shutdown(self) -> None:
        with self._lock:
            self._close()


_gateway: SubprocessOcrGateway | None = None
_gateway_lock = threading.Lock()


def _ensure_gateway() -> "SubprocessOcrGateway | None":
    global _gateway
    with _gateway_lock:
        if _gateway is None:
            _gateway = SubprocessOcrGateway()
        if _gateway.unavailable_reason:
            return None
    return _gateway


def subprocess_paddle_reads(image_bgr) -> list[str] | None:
    """Module-level entry used by the SFX re-OCR escalation."""
    gateway = _ensure_gateway()
    if gateway is None:
        return None
    return gateway.reads(image_bgr)


def shutdown_subprocess_ocr() -> None:
    global _gateway
    with _gateway_lock:
        if _gateway is not None:
            _gateway.shutdown()
            _gateway = None
