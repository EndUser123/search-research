"""Pytest bootstrap: make ``check/__lib`` importable as flat modules.

Adds the sibling ``__lib`` directory to ``sys.path`` so test files can do
``import event_model``, ``import transcript_parser``, etc. without package
machinery. This mirrors how ``preprocessor.py`` self-bootstraps in
production.
"""

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_LIB = _HERE.parent / "__lib"
if _LIB.is_dir() and str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
