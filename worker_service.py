"""Compatibility launcher; implementation lives in :mod:`komyst.runtime.worker_service`."""
from komyst.runtime import worker_service as _implementation
import sys as _sys

if __name__ == "__main__":
    raise SystemExit(_implementation.main())
_sys.modules[__name__] = _implementation
