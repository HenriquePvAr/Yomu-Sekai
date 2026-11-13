"""RAM guard before loading heavy local models (LaMa, FLUX).

Unknown free memory never blocks: without ``psutil`` the guard allows everything.
Every denial is counted so the timing report can show how often it fired.
"""
from __future__ import annotations

import threading

_SKIPPED: dict[str, int] = {"lama_skipped_low_memory": 0, "flux_skipped_low_memory": 0}
_LOCK = threading.Lock()


def available_ram_mb() -> float | None:
    """Free physical RAM in MB, or ``None`` when it cannot be measured."""
    try:
        import psutil

        return psutil.virtual_memory().available / (1024 * 1024)
    except Exception:  # noqa: BLE001 - no psutil / no reading: do not block
        return None


def allow(feature: str, need_mb: float) -> bool:
    """True when ``feature`` ("lama"/"flux") may run; a denial is counted."""
    free = available_ram_mb()
    if free is None or free >= float(need_mb):
        return True
    with _LOCK:
        key = f"{feature}_skipped_low_memory"
        _SKIPPED[key] = _SKIPPED.get(key, 0) + 1
    return False


def skipped_counters() -> dict[str, int]:
    with _LOCK:
        return dict(_SKIPPED)


def reset_counters() -> None:
    with _LOCK:
        for key in _SKIPPED:
            _SKIPPED[key] = 0
