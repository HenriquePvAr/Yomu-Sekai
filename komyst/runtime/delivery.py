"""Lean delivery: once a job finishes successfully, drop work files the chosen mode does not
deliver.

Deliberately conservative. Only artifacts proven unread after completion are removed:

* canonical artifact folders (``images/translated``, ``images/clean``, ``psd``) the plan does
  not deliver (the "Tradução pronta" preset delivers only the PDF) -- ``images/translated`` is also dropped when the PDF already carries those pages
  and no review manifest points at them (no QC operation);
* pure debug output (``debug/``, ``smart_input_pages/``, ``smart_split_contact_sheet.jpg``).

NOT touched, because the runner, re-export, review or resume still read them: ``input/``,
``pages/``, ``progress.json``, ``quality_report.json``, ``.translation_results/``,
``translation_ready.json``, ``yk_reservation.json`` and every manifest.

It runs only for a ``finished`` job; ``review_required``, ``failed``, ``interrupted`` and
cancelled jobs keep everything so they can be reviewed, re-exported and resumed.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from komyst.runtime.output_plan import Operation, plan_artifact_types

# "completed" is the plan's wording; the job store calls the same terminal state "finished".
DELIVERY_STATUSES = frozenset({"finished", "completed"})

_ARTIFACT_DIRS = {
    "translated_image": "images/translated",
    "clean_image": "images/clean",
    "editable_psd": "psd",
}
_WORK_ENTRIES = ("debug", "smart_input_pages", "smart_split_contact_sheet.jpg")


def _unrequested_artifacts(plan) -> set:
    wanted = set(plan_artifact_types(plan.operations))
    # "Tradução pronta" runs CLEAN internally but delivers only the PDF.
    if plan.preset == "traducao_pronta":
        wanted = {"final_pdf"}
    # The PDF already carries the translated pages. Keep the images only when a review
    # manifest (QC) references them.
    if "final_pdf" in wanted and Operation.QC not in plan.operations:
        wanted.discard("translated_image")
    return set(_ARTIFACT_DIRS) - wanted


def _remove(path: Path) -> bool:
    try:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        elif path.exists() or path.is_symlink():
            path.unlink()
        else:
            return False
        return True
    except OSError:
        return False


def _forget_in_manifest(output_dir: Path, kinds: set) -> None:
    """Stop the artifact manifest from claiming artifacts that were just removed."""
    path = output_dir / "artifact_manifest.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if not isinstance(manifest, dict):
        return
    for key in ("requested_artifacts", "produced_artifacts", "unavailable_artifacts"):
        if isinstance(manifest.get(key), list):
            manifest[key] = [k for k in manifest[key] if k not in kinds]
    for key in ("artifact_status", "capabilities"):
        if isinstance(manifest.get(key), dict):
            for kind in kinds:
                manifest[key].pop(kind, None)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def finalize_delivery(output_dir, plan, job_status, *, keep_work_files: bool = False) -> dict:
    """Remove work files not delivered by ``plan``. Returns ``{"removed": [...], "skipped": reason}``."""
    if str(job_status or "").lower() not in DELIVERY_STATUSES:
        return {"removed": [], "skipped": "status_not_finished"}
    if keep_work_files:
        return {"removed": [], "skipped": "keep_work_files"}
    root = Path(output_dir)
    if not root.is_dir() or not plan.operations:
        return {"removed": [], "skipped": "nothing_to_do"}
    removed = []
    dropped = set()
    for kind in sorted(_unrequested_artifacts(plan)):
        if _remove(root / _ARTIFACT_DIRS[kind]):
            removed.append(_ARTIFACT_DIRS[kind])
            dropped.add(kind)
    for name in _WORK_ENTRIES:
        if _remove(root / name):
            removed.append(name)
    if dropped:
        _forget_in_manifest(root, dropped)
    return {"removed": removed, "skipped": ""}
