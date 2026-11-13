from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

from komyst.commands.run_webtoon import _pipeline_main_status


def test_structural_page_failure_is_logged_as_failed_even_when_pdf_exists():
    assert _pipeline_main_status({
        "status": "error",
        "pdf_path": "chapter.pdf",
        "quality_validation": {"invalid_or_blank_pages": [34]},
    }) == ("failed", "error")


def test_quality_review_is_preserved_as_review_required():
    assert _pipeline_main_status({
        "status": "review_required",
        "pdf_path": "chapter.pdf",
        "quality_validation": {"manual_review_required_groups": 1},
    }) == ("review_required", "review_required")


def test_missing_report_status_uses_structural_quality_classification():
    assert _pipeline_main_status({
        "pdf_path": "chapter.pdf",
        "quality_validation": {"invalid_or_blank_pages": [34]},
    }) == ("failed", "error")
