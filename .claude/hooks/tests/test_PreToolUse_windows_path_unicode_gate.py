#!/usr/bin/env python3
"""Tests for PreToolUse_windows_path_unicode_gate.py hook.

Tests that the hook detects invalid Python escape sequences in Windows paths
within python -c commands.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_hook(command: str) -> dict:
    """Run the windows_path_unicode_gate hook with a command.

    Returns the hook result dict. Hook outputs JSON to stderr.
    """
    hook_path = Path(__file__).parent.parent / "PreToolUse_windows_path_unicode_gate.py"
    data = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(data),
        capture_output=True,
        text=True,
    )
    # Hook outputs to stderr (via print to sys.stderr)
    if result.stderr:
        try:
            return json.loads(result.stderr)
        except json.JSONDecodeError:
            pass
    return {"continue": True}


def test_backslash_dot_blocked():
    """Test that backslash-dot pattern is blocked."""
    # Use raw string to avoid Python escape processing
    result = run_hook(r'python -c "import sys; sys.path.insert(0, \'P:\\.claude\\skills\\rns\')"')
    assert result.get("continue") is False, "Should block backslash-dot pattern"
    assert "WINDOWS PATH" in result.get("reason", "")


def test_backslash_s_blocked():
    """Test that backslash-s pattern is blocked."""
    result = run_hook(r'python -c "x = \'C:\\skills\\name\'"')
    assert result.get("continue") is False, "Should block backslash-s pattern"


def test_backslash_c_blocked():
    """Test that backslash-c pattern is blocked."""
    result = run_hook(r'python -c "path = \'C:\\config\'"')
    assert result.get("continue") is False, "Should block backslash-c pattern"


def test_backslash_U_uppercase_blocked():
    """Test that backslash-U pattern is blocked."""
    result = run_hook(r'python -c "path = \'C:\\Users\\name\'"')
    assert result.get("continue") is False, "Should block backslash-U pattern"


def test_raw_string_allowed():
    """Test that raw string r\"...\" is allowed."""
    result = run_hook('python -c r"import sys; sys.path.insert(0, \'P:\\.claude\\skills\\rns\')"')
    assert result.get("continue") is True, "Should allow raw string"


def test_forward_slashes_allowed():
    """Test that forward slashes in Windows paths are allowed."""
    result = run_hook('python -c "import sys; sys.path.insert(0, \'P:/.claude/skills/rns\')"')
    assert result.get("continue") is True, "Should allow forward slashes"


def test_valid_escapes_allowed():
    """Test that valid Python escape sequences are allowed."""
    # \\n (newline) and \\t (tab) should be allowed
    result = run_hook('python -c "x = \'\\n\\t\'"')
    assert result.get("continue") is True, "Should allow valid escape sequences"


def test_no_python_c_allowed():
    """Test that non-python-c commands are allowed."""
    result = run_hook('echo "C:\\.claude\\skills\\rns"')
    assert result.get("continue") is True, "Should allow non-python-c commands"


def test_disabled_hook_allows():
    """Test that disabled hook (via env var) allows commands."""
    import os
    old_val = os.environ.get("WINDOWS_PATH_UNICODE_GATE_ENABLED")
    try:
        os.environ["WINDOWS_PATH_UNICODE_GATE_ENABLED"] = "false"
        result = run_hook('python -c "x = \'C:\\\\.claude\\skills\\rns\'"')
        assert result.get("continue") is True, "Disabled hook should allow"
    finally:
        if old_val is None:
            os.environ.pop("WINDOWS_PATH_UNICODE_GATE_ENABLED", None)
        else:
            os.environ["WINDOWS_PATH_UNICODE_GATE_ENABLED"] = old_val


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
