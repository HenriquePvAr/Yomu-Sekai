"""Prune old terminal chapter runs while preserving app history and publications."""
from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Any, Callable


def _published_run_ids(community_db_path: str | Path | None) -> set[str]:
    if not community_db_path:
        return set()
    db = Path(community_db_path)
    if not db.is_file():
        return set()
    try:
        connection = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
        try:
            rows = connection.execute(
                "SELECT source_run_id, output_dir FROM community_posts "
                "WHERE lower(status)='published' AND deleted_at IS NULL"
            ).fetchall()
        finally:
            connection.close()
    except sqlite3.Error:
        # Unavailable publication state must fail closed: retain all candidate runs.
        return {"*"}
    published: set[str] = set()
    for run_id, output_dir in rows:
        if run_id:
            published.add(str(run_id))
        if output_dir:
            published.add(Path(str(output_dir)).name)
    return published


def prune_chapter_runs(
    chapter_dir: str | Path,
    keep: int,
    protected_run_ids: set[str] | list[str] | tuple[str, ...] = (),
    *,
    current_run_id: str = "",
    jobs: list[dict[str, Any]] | None = None,
    community_db_path: str | Path | None = None,
    delete_tree: Callable[[Path], tuple[bool, str]] | None = None,
    hide_record: Callable[[dict[str, Any]], Any] | None = None,
) -> dict[str, Any]:
    """Remove old UUID run directories using the UI's deletion primitives.

    ``delete_tree`` must be the same confined remover used by the UI and
    ``hide_record`` its history tombstone writer. Passing neither disables
    deletion, which keeps standalone callers fail-safe.
    """
    root = Path(chapter_dir).resolve()
    keep_count = max(0, int(keep))
    if keep_count == 0 or not root.is_dir() or delete_tree is None or hide_record is None:
        return {"removed": [], "preserved": [], "disabled": keep_count == 0}
    runs: list[Path] = []
    for child in root.iterdir():
        if not child.is_dir() or child.is_symlink():
            continue
        try:
            uuid.UUID(child.name)
        except ValueError:
            continue
        runs.append(child)
    runs.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    preserve = set(str(item) for item in protected_run_ids)
    if current_run_id:
        preserve.add(str(current_run_id))
    active_states = {"running", "queued", "interrupted", "claiming", "starting", "cancelling"}
    rows_by_run: dict[str, list[dict[str, Any]]] = {}
    for job in jobs or []:
        rows_by_run.setdefault(str(job.get("run_id") or ""), []).append(job)
    published = _published_run_ids(community_db_path)
    removed: list[str] = []
    preserved: list[dict[str, str]] = []
    for index, folder in enumerate(runs):
        run_id = folder.name
        reasons = []
        if index < keep_count:
            reasons.append("newest_keep_count")
        if run_id in preserve:
            reasons.append("protected")
        if "*" in published or run_id in published:
            reasons.append("published")
        if any(str(job.get("status") or "").casefold() in active_states
               for job in rows_by_run.get(run_id, [])):
            reasons.append("job_not_terminal")
        if reasons:
            preserved.append({"run_id": run_id, "reason": ",".join(reasons)})
            continue
        record = {"id": run_id, "run_id": run_id, "output_folder": str(folder)}
        try:
            hide_record(record)
        except Exception as exc:  # noqa: BLE001 - retention must never break the job
            preserved.append({"run_id": run_id, "reason": f"history_hide_failed:{type(exc).__name__}"})
            continue
        try:
            success, _reason = delete_tree(folder)
        except Exception as exc:  # noqa: BLE001 - retention must never break the job
            success = False
            _reason = type(exc).__name__
        if success:
            removed.append(run_id)
        else:
            preserved.append({"run_id": run_id, "reason": f"delete_failed:{_reason}"})
    return {"removed": removed, "preserved": preserved, "disabled": False}
