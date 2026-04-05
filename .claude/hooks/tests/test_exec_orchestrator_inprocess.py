"""Tests for in-process exec_orchestrator consolidation."""

from __future__ import annotations

import os
import sys
from pathlib import Path as PathLib

sys.path.insert(0, str(PathLib(__file__).parent.parent))
os.environ["EXEC_ORCHESTRATOR_INPROCESS"] = "1"


def test_exec_orchestrator_inprocess_function_exists():
    """Characterization test: Verify in-process function exists."""
    from PreToolUse_write_router import wrap_exec_orchestrator_inprocess
    assert wrap_exec_orchestrator_inprocess is not None


def test_exec_orchestrator_is_exec_mode_importable():
    """Verify that is_exec_mode function can be imported."""
    from exec_orchestrator import is_exec_mode
    assert callable(is_exec_mode)
