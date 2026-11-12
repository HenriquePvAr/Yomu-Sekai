"""Compatibility launcher; implementation lives in :mod:`komyst.ui.app`."""
from komyst.ui import app as _implementation
import sys as _sys

if __name__ == "__main__":
    raise SystemExit(_implementation.main())
_sys.modules[__name__] = _implementation
