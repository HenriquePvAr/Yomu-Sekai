"""Compatibility launcher; implementation lives in :mod:`komyst.commands.start_tradutor`."""
from komyst.commands import start_tradutor as _implementation
import sys as _sys

if __name__ == "__main__":
    raise SystemExit(_implementation.main())
_sys.modules[__name__] = _implementation
