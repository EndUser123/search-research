"""Test bf_agent.py — verify the library is importable and the API surface is correct."""

import sys
from pathlib import Path

# Ensure P:/tools/mcp is on the path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "mcp"))

import pytest

# --------------------------------------------------------------------
# Smoke tests — import and API presence
# --------------------------------------------------------------------

def test_module_import():
    """bf_agent module is importable."""
    import bf_agent
    assert bf_agent is not None

def test_run_simple_exists():
    """run_simple is callable."""
    from bf_agent import run_simple
    assert callable(run_simple)

def test_run_compare_exists():
    """run_compare is callable."""
    from bf_agent import run_compare
    assert callable(run_compare)

def test_run_code_exists():
    """run_code is callable."""
    from bf_agent import run_code
    assert callable(run_code)

def test_bifrost_call_exists():
    """bifrost_call is callable (used internally by compare fan-out)."""
    from bf_agent import bifrost_call
    assert callable(bifrost_call)

def test_tool_functions_exist():
    """Tool functions are importable."""
    from bf_agent import tool_read_file, tool_list_dir, tool_glob, tool_write_file
    assert callable(tool_read_file)
    assert callable(tool_list_dir)
    assert callable(tool_glob)
    assert callable(tool_write_file)

def test_tool_action_model():
    """ToolAction Pydantic model is defined and validates."""
    from bf_agent import ToolAction
    ta = ToolAction(action="read_file", path="P:/test.txt")
    assert ta.action == "read_file"
    assert ta.path == "P:/test.txt"

# --------------------------------------------------------------------
# Config constants are accessible
# --------------------------------------------------------------------

def test_config_constants():
    """VALID_MODELS, VALID_RUN_MODES, BF_ALLOWED_ROOT are exposed."""
    from bf_agent import VALID_MODELS, VALID_RUN_MODES, BF_ALLOWED_ROOT
    assert "M27" in VALID_MODELS
    assert "compare" in VALID_RUN_MODES
    assert "code" in VALID_RUN_MODES
    assert BF_ALLOWED_ROOT == Path("P:/").resolve()

# --------------------------------------------------------------------
# Path guard — tool_read_file rejects paths outside allowed root
# --------------------------------------------------------------------

def test_read_file_rejects_outside_root(tmp_path):
    """tool_read_file returns error for paths outside BF_ALLOWED_ROOT."""
    from bf_agent import tool_read_file
    result = tool_read_file("C:/Windows/System32/")
    assert result["ok"] is False
    assert "denied" in result["error"].lower() or "not accessible" in result["error"].lower()