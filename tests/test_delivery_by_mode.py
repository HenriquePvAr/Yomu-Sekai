"""Lean delivery: what stays in the output folder, per mode and per job status."""
import json

import pytest

from komyst.pipeline.benchmark_pipeline import _translation_txt
from komyst.runtime.delivery import finalize_delivery
from komyst.runtime.output_plan import normalize_output_plan

PDF = ["chapter.pdf"]
TRANSLATED = ["images/translated/001.png"]
CLEAN = ["images/clean/001.png"]
PSD = ["psd/001.psd"]
QC = ["qc/quality_report.json", "qc/review_manifest.json"]
TEXT = ["translation/translation.json", "translation/traducao.txt"]
TRASH = ["debug/x.png", "smart_input_pages/a.png", "smart_split_contact_sheet.jpg"]
# Read after completion by the runner, re-export, review or resume: never removed.
ALWAYS_KEPT = ["input/001.png", "pages/page_001.png", "progress.json", "quality_report.json",
               ".translation_results/a.json", "translation_ready.json",
               "yk_reservation.json", "artifact_manifest.json"]
# preset -> (files the pipeline writes for it, what the user must be left with)
MODES = {
    "traducao_pronta": (PDF + TRANSLATED + CLEAN, PDF),
    "apenas_clean": (CLEAN, CLEAN),
    "traducao_clean": (CLEAN + TEXT, CLEAN + TEXT),
    "apenas_traducao": (TEXT, TEXT),
    # Completo keeps translated images: the review manifest points at them.
    "profissional": (PDF + TRANSLATED + CLEAN + PSD + QC, PDF + TRANSLATED + CLEAN + PSD + QC),
}


def _tree(root, produced=()):
    for rel in [*produced, *TRASH, *ALWAYS_KEPT]:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}" if rel.endswith(".json") else "x", encoding="utf-8")
    return root


def _left(root):
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("preset", sorted(MODES))
def test_finished_job_keeps_only_the_mode_deliverables(tmp_path, preset):
    produced, delivered = MODES[preset]
    root = _tree(tmp_path, produced)
    res = finalize_delivery(root, normalize_output_plan(preset), "finished")
    assert _left(root) == set(delivered) | set(ALWAYS_KEPT)
    assert res["removed"]


def test_custom_plan_keeps_only_marked_operations(tmp_path):
    root = _tree(tmp_path, CLEAN + TRANSLATED + PSD)
    plan = normalize_output_plan("personalizado", operations={"clean"})
    finalize_delivery(root, plan, "finished")
    assert "images/clean/001.png" in _left(root)
    assert not (root / "images/translated").exists() and not (root / "psd").exists()


@pytest.mark.parametrize("status", ["review_required", "failed", "interrupted", "cancelled", "running"])
def test_non_finished_status_deletes_nothing(tmp_path, status):
    root = _tree(tmp_path, PDF + TRANSLATED + CLEAN)
    before = _left(root)
    res = finalize_delivery(root, normalize_output_plan("traducao_pronta"), status)
    assert _left(root) == before and res["removed"] == []


def test_keep_work_files_deletes_nothing(tmp_path):
    root = _tree(tmp_path, CLEAN + TRANSLATED)
    before = _left(root)
    finalize_delivery(root, normalize_output_plan("apenas_clean"), "finished", keep_work_files=True)
    assert _left(root) == before


def test_manifest_forgets_removed_artifacts(tmp_path):
    root = _tree(tmp_path, PDF + TRANSLATED + CLEAN)
    (root / "artifact_manifest.json").write_text(json.dumps({
        "requested_artifacts": ["translated_image", "final_pdf"],
        "produced_artifacts": ["translated_image", "final_pdf"],
        "artifact_status": {"translated_image": "produced", "final_pdf": "produced"},
    }), encoding="utf-8")
    finalize_delivery(root, normalize_output_plan("traducao_pronta"), "finished")
    manifest = json.loads((root / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert manifest["requested_artifacts"] == ["final_pdf"]
    assert manifest["artifact_status"] == {"final_pdf": "produced"}


def test_translation_txt_has_page_original_translation():
    tm = {"pages": [{"page_index": 2, "regions": [{"source": "Hi", "target": "Oi"}]}]}
    assert _translation_txt(tm) == "Página: 2\nOriginal: Hi\nTradução: Oi\n"
