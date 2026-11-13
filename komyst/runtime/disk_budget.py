"""Conservative free-space estimates for chapter job outputs."""
from __future__ import annotations

import errno
import shutil
from pathlib import Path
from typing import Any


MB_PER_PAGE = {"profissional": 60, "apenas_clean": 8, "default": 15}
MIN_FREE_MB_AT_START = {"profissional": 3000, "default": 1000}


class InsufficientDiskSpace(OSError):
    """Raised when the destination cannot safely hold the planned output."""

    def __init__(self, details: dict[str, Any]):
        self.details = details
        super().__init__(errno.ENOSPC, "insufficient_disk_space")


def _plan_key(output_plan: object) -> str:
    value = str(output_plan or "").strip().casefold()
    if value in {"profissional", "professional", "professional_qc", "completo"}:
        return "profissional"
    if value in {"apenas_clean", "clean_only"}:
        return "apenas_clean"
    return "default"


def required_mb(output_plan: object, page_count: int | None = None) -> int:
    key = _plan_key(output_plan)
    reserve_key = "profissional" if key == "profissional" else "default"
    pages = max(0, int(page_count or 0))
    per_page = MB_PER_PAGE[key]
    minimum = MIN_FREE_MB_AT_START[reserve_key]
    return minimum + pages * per_page


def free_mb(path: str | Path) -> int:
    return int(shutil.disk_usage(Path(path)).free // (1024 * 1024))


def check(path: str | Path, output_plan: object,
          page_count: int | None = None) -> tuple[bool, dict[str, Any]]:
    key = _plan_key(output_plan)
    available = free_mb(path)
    needed = required_mb(key, page_count)
    details = {
        "path": str(Path(path)),
        "output_plan": key,
        "page_count": max(0, int(page_count or 0)),
        "free_mb": available,
        "required_mb": needed,
        "sufficient": available >= needed,
    }
    return details["sufficient"], details
