"""Shared pytest fixtures for handoff skill tests."""
from __future__ import annotations

import sys
from pathlib import Path

# Make __lib importable without package install.
SKILL_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = SKILL_ROOT / "__lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
