"""Compatibility launcher; implementation lives in :mod:`yomu.commands.run_webtoon`."""
from yomu.commands import run_webtoon as _implementation
import sys as _sys

if __name__ == "__main__":
    # main() returns the pipeline report; a dict passed to SystemExit exits 1, which
    # made every worker job "failed" even with the PDF written.
    from yomu.ui.ui_helpers import pipeline_report_exit_code as _exit_code
    raise SystemExit(_exit_code(_implementation.main()))
_sys.modules[__name__] = _implementation
