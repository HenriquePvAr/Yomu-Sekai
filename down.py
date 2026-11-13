"""Compatibility launcher; implementation lives in :mod:`komyst.download.down`."""
from komyst.download import down as _implementation
import sys as _sys

_sys.modules[__name__] = _implementation
