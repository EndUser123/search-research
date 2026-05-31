#!/usr/bin/env python3
"""PostToolUse Hook: Artifact Validator for Grounded Artifact Validation.

Injects grounded artifact context when available and cleans up on success.
"""



# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

