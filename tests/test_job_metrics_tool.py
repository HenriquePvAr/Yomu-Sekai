import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "audit" / "job_metrics.py"
SPEC = importlib.util.spec_from_file_location("job_metrics_tool", MODULE_PATH)
job_metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(job_metrics)


def test_collect_metrics_reads_minimal_run_and_excludes_cleaned_pages(tmp_path):
    (tmp_path / "timing_report.json").write_text(json.dumps({
        "total_seconds": 12.5,
        "stage_seconds": {"ocr": 2.0, "render": 3.5},
        "inference_devices": {
            "gpu_inference_requested": "auto",
            "ocr_effective_device": "directml",
            "lama_effective_device": "cpu",
        },
    }), encoding="utf-8")
    (tmp_path / "artifact_manifest.json").write_text(json.dumps({
        "provenance": {
            "1": {"clean_certificate": {"reason": "verified"}},
            "2": {"clean_certificate": {"reason": "no_text"}},
        }
    }), encoding="utf-8")
    (tmp_path / "quality_report.json").write_text(json.dumps({
        "summary": {"quality_validation": {
            "translation_accounting": {"translated": 3},
            "severity": "PASS",
            "reason_codes": [],
            "physical_gate_passed": True,
            "physical_source_residual_count": 0,
        }},
        "pages": [{"translation_terminal_items": [
            {"translation_final_state": "translated", "translation_final_reason": "accepted", "cleanup_fill_source": "lama"},
            {"translation_final_state": "preserved_original", "translation_final_reason": "review", "cleanup_fill_source": "local"},
        ]}],
    }), encoding="utf-8")
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "page_001.png").write_bytes(b"1234")
    (pages / "page_001_cleaned.png").write_bytes(b"ignored")
    (pages / "page_002.png").write_bytes(b"123456")

    result = job_metrics.collect_metrics(tmp_path)

    assert result["total_seconds"] == 12.5
    assert result["stage_seconds"] == {"ocr": 2.0, "render": 3.5}
    assert result["inference_devices"]["ocr_effective_device"] == "directml"
    assert result["inference_devices"]["lama_effective_device"] == "cpu"
    assert result["clean_certificate_reason_counts_by_page"] == {"no_text": 1, "verified": 1}
    assert result["translation_accounting"] == {"translated": 3}
    assert result["severity"] == "PASS"
    assert result["physical_gate_passed"] is True
    assert result["physical_source_residual_count"] == 0
    assert result["translation_terminal_state_reason_counts"] == {
        "preserved_original | review": 1,
        "translated | accepted": 1,
    }
    assert result["cleanup_fill_source_counts"] == {"lama": 1, "local": 1}
    assert result["page_count"] == 2
    assert result["total_bytes"] >= 10
    assert result["resource_monitoring"] is None
    assert "Dispositivos de inferência" in job_metrics.render_table(result)


def test_compare_reports_difference():
    a = {"run_id": "a", "total_seconds": 10, "page_count": 2,
         "megabytes_per_page": 1.0, "total_bytes": 100, "severity": "PASS",
         "physical_gate_passed": True, "physical_source_residual_count": 0,
         "stage_seconds": {"ocr": 4}}
    b = {**a, "run_id": "b", "total_seconds": 15,
         "stage_seconds": {"ocr": 6}}
    rendered = job_metrics.render_comparison(a, b)
    assert "total_seconds | 10 | 15 | 5" in rendered
    assert "stage:ocr | 4 | 6 | 2" in rendered
