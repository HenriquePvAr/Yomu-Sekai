"""The root launcher must turn the pipeline report into a process exit code.

``main()`` returns the report dict; ``SystemExit(dict)`` exits 1, so every worker
job ended ``failed`` (or ``interrupted``) even though the PDF had been written.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_PROBE = """
import runpy, sys
sys.path.insert(0, {root!r})
import yomu.commands.run_webtoon as impl
impl.main = lambda: {report!r}
runpy.run_path({launcher!r}, run_name="__main__")
"""


def _exit_code(report):
    code = _PROBE.format(root=str(ROOT), report=report, launcher=str(ROOT / "run_webtoon.py"))
    return subprocess.run([sys.executable, "-c", code], capture_output=True, cwd=ROOT, timeout=120).returncode


def test_review_required_report_exits_zero():
    report = {"pdf_path": "out.pdf", "quality_validation": {"status": "review_required"}}
    assert _exit_code(report) == 0


def test_report_without_output_exits_one():
    assert _exit_code({"quality_validation": {}}) == 1
