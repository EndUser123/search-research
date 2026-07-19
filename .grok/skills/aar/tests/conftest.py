"""Pytest configuration: make the AAR ``__lib/`` modules importable.

Existing tests (``test_aar_protocol.py``, ``test_aar_reference_model.py``)
import only from SKILL.md text and need no ``__lib`` access, so this conftest
is additive — it does not alter their behaviour.
"""

import sys
from pathlib import Path

_LIB_DIR = Path(__file__).resolve().parent.parent / "__lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))
