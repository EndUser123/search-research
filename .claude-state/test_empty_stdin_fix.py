#!/usr/bin/env python3
"""Regression tests for empty stdin handling in PreToolUse subprocess hooks.

Tests the fix for: JSONDecodeError when stdin is empty/whitespace-only.
File: P:/.claude/hooks/tests/test_pretooluse_empty_stdin_fix.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Hooks are at P:/.claude/hooks (absolute path, not relative to worktree)
HOOKS_DIR = Path("P:/") / ".claude" / "hooks"
RECURSIVE_FILE = HOOKS_DIR / "recursive_failure_detector.py"
INVESTIGATION_FILE = HOOKS_DIR / "PreToolUse_investigation_gate.py"


def run_hook_subprocess(
    hook_file: Path,
    input_data: dict | None = None,
    *,
    timeout: float = 10.0,
) -> subprocess.CompletedProcess:
    """Run a hook subprocess and return the result."""
    if input_data is not None:
        input_str = json.dumps(input_data)
    else:
        input_str = ""

    return subprocess.run(
        [sys.executable, str(hook_file)],
        input=input_str,
        capture_output=True,
        text=True,
        cwd=str(HOOKS_DIR),
        timeout=timeout,
    )


class TestRecursiveFailureDetectorEmptyStdin:
    """Empty stdin regression tests for recursive_failure_detector.py."""

    def test_empty_stdin_allows(self) -> None:
        """Empty stdin should exit 0 with continue=true, not JSONDecodeError."""
        result = run_hook_subprocess(RECURSIVE_FILE, input_data=None)
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"
        # Should print {"continue": true} to stdout
        try:
            output = json.loads(result.stdout.strip())
            assert output.get("continue") is True
        except json.JSONDecodeError:
            pytest.fail(f"stdout was not JSON: {result.stdout!r}")

    def test_whitespace_only_stdin_allows(self) -> None:
        """Whitespace-only stdin should exit 0, not JSONDecodeError."""
        result = subprocess.run(
            [sys.executable, str(RECURSIVE_FILE)],
            input="   \n\t  \n",
            capture_output=True,
            text=True,
            cwd=str(HOOKS_DIR),
            timeout=10.0,
        )
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"

    def test_valid_edit_json_allows(self) -> None:
        """Valid Edit JSON should still work and return empty dict (no block)."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "test.py", "old_string": "a", "new_string": "b"},
            "session_id": "test-session",
            "terminal_id": "test-terminal",
        }
        result = run_hook_subprocess(RECURSIVE_FILE, input_data)
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"
        # Should be valid JSON
        try:
            output = json.loads(result.stdout.strip())
            assert isinstance(output, dict)
        except json.JSONDecodeError:
            pytest.fail(f"stdout was not JSON: {result.stdout!r}")


class TestInvestigationGateEmptyStdin:
    """Empty stdin regression tests for PreToolUse_investigation_gate.py."""

    def test_empty_stdin_allows(self) -> None:
        """Empty stdin should exit 0, not JSONDecodeError."""
        result = run_hook_subprocess(INVESTIGATION_FILE, input_data=None)
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"

    def test_whitespace_only_stdin_allows(self) -> None:
        """Whitespace-only stdin should exit 0, not JSONDecodeError."""
        result = subprocess.run(
            [sys.executable, str(INVESTIGATION_FILE)],
            input="   \n\t  \n",
            capture_output=True,
            text=True,
            cwd=str(HOOKS_DIR),
            timeout=10.0,
        )
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"

    def test_valid_edit_json_with_investigation_blocks(self) -> None:
        """Valid Edit JSON for uninvestigated file should block (normal behavior)."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "test.py", "old_string": "a", "new_string": "b"},
            "session_id": "test-session",
            "terminal_id": "test-terminal",
            "transcript_entries": [],
        }
        result = run_hook_subprocess(INVESTIGATION_FILE, input_data)
        # Should exit 2 (block) or 0 (allow) depending on state — but NOT 1 (error)
        assert result.returncode in (0, 2), f"Expected exit 0 or 2, got {result.returncode}. stderr: {result.stderr}"
        # Should be valid JSON, not a traceback
        try:
            output = json.loads(result.stdout.strip())
            assert "decision" in output
        except json.JSONDecodeError:
            pytest.fail(f"stdout was not JSON: {result.stdout!r}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
