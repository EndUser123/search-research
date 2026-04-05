#!/usr/bin/env python3
"""Tests for PreToolUse_auto_format.py - Auto-format on edit.

RED PHASE: These tests define expected behavior for the auto-format hook.

The auto-format hook is ADVISORY - it always returns continue:True
but provides warnings for formatting issues that could be auto-fixed.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestAutoFormatHook:
    """Test PreToolUse_auto_format hook behavior."""

    def _run_hook(self, tool_name: str, file_path: str, content: str) -> dict:
        """Run the auto-format hook and return parsed JSON output."""
        input_data = {
            "tool_name": tool_name,
            "tool_input": {
                "file_path": file_path,
                "content": content,
            },
        }

        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parent.parent / "PreToolUse_auto_format.py"),
            ],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail(
                f"Hook returned non-JSON output: {result.stdout!r}\nstderr: {result.stderr!r}"
            )

    def test_continues_for_non_python_files(self):
        """Non-Python files should pass through without blocking."""
        output = self._run_hook(
            "Write",
            "test.js",
            "const x = 1;",
        )
        assert output["continue"] is True
        # Should not have any formatting warnings for non-Python
        assert "warning" not in output or "python" not in output.get("warning", "").lower()

    def test_continues_for_read_only_tool(self):
        """Read tool should not trigger format check."""
        output = self._run_hook(
            "Read",
            "test.py",
            "",
        )
        assert output["continue"] is True

    def test_warns_on_missing_final_newline(self):
        """Should warn when file lacks final newline."""
        content = "x = 1"  # No trailing newline
        output = self._run_hook("Write", "test.py", content)
        assert output["continue"] is True
        # Should have a warning about missing newline
        assert "warning" in output or "newline" in output.get("warning", "").lower()

    def test_warns_on_trailing_whitespace(self):
        """Should warn when trailing whitespace is detected."""
        content = "x = 1   \n"  # Trailing spaces
        output = self._run_hook("Write", "test.py", content)
        assert output["continue"] is True
        assert "warning" in output

    def test_handles_empty_content(self):
        """Empty content should not cause errors or warnings."""
        output = self._run_hook("Write", "test.py", "")
        assert output["continue"] is True
        # Empty file is not a formatting issue

    def test_valid_python_no_warning(self):
        """Valid Python code with proper formatting should pass without warnings."""
        content = "x = 1\n"  # Proper trailing newline
        output = self._run_hook("Write", "test.py", content)
        assert output["continue"] is True
        # No formatting warnings for properly formatted code
        assert "warning" not in output

    def test_long_lines_warn(self):
        """Should warn when lines exceed typical length limits."""
        content = "x = " + "a" * 100 + "\n"  # Line > 88 chars (ruff default)
        output = self._run_hook("Write", "test.py", content)
        assert output["continue"] is True
        # Ruff would flag this - hook should warn
        assert "warning" in output

    def test_edit_tool_also_checked(self):
        """Edit tool should also be checked for formatting issues."""
        content = "x = 1   \n"  # Trailing whitespace
        output = self._run_hook("Edit", "test.py", content)
        assert output["continue"] is True
        assert "warning" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
