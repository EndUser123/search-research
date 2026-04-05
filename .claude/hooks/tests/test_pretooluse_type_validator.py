#!/usr/bin/env python3
"""Tests for PreToolUse_type_validator.py - Type mismatch detection at write-time.

Tests the PreToolUse hook that blocks code files at workspace root and detects
double-extension bypass attempts (e.g. malware.py.txt).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Path to the hook under test
HOOK_PATH = Path(__file__).resolve().parent.parent / "PreToolUse_type_validator.py"


def run_hook(tool_name: str, file_path: str) -> dict:
    """Run the type validator hook with given input and return parsed output."""
    input_data = {
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path},
    }
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


class TestDoubleExtensionDetection:
    """Test double-extension bypass detection."""

    def test_malware_py_txt_blocked(self):
        """malware.py.txt should be blocked (double-extension bypass)."""
        result = run_hook("Write", "P:/malware.py.txt")
        assert result["continue"] is False
        assert "double-extension" in result["reason"].lower()

    def test_script_py_config_blocked(self):
        """script.py.config should be blocked (double-extension bypass)."""
        result = run_hook("Write", "P:/script.py.config")
        assert result["continue"] is False
        assert "double-extension" in result["reason"].lower()

    def test_document_txt_allowed(self):
        """document.txt should be allowed (valid config file)."""
        result = run_hook("Write", "P:/document.txt")
        assert result["continue"] is True

    def test_nested_double_extension_blocked(self):
        """file.py.bak should be blocked (double-extension with code segment)."""
        result = run_hook("Write", "P:/old_code.py.bak")
        assert result["continue"] is False
        assert "double-extension" in result["reason"].lower()

    def test_normal_config_file_allowed(self):
        """Normal config files at root should be allowed."""
        allowed = [
            "P:/config.toml",
            "P:/settings.json",
            "P:/.env",
            "P:/pyproject.toml",
            "P:/setup.cfg",
        ]
        for path in allowed:
            result = run_hook("Write", path)
            assert result["continue"] is True, f"Expected allow for {path}"


class TestCodeExtensionBlocking:
    """Test that code files are blocked at workspace root."""

    def test_python_file_blocked_at_root(self):
        """Python files at workspace root should be blocked."""
        result = run_hook("Write", "P:/script.py")
        assert result["continue"] is False
        assert "TYPE MISMATCH" in result["reason"]

    def test_javascript_file_blocked_at_root(self):
        """JavaScript files at workspace root should be blocked."""
        result = run_hook("Write", "P:/app.js")
        assert result["continue"] is False

    def test_executable_blocked_at_root(self):
        """Executable files at workspace root should be blocked."""
        for ext in [".exe", ".bat", ".ps1", ".sh"]:
            result = run_hook("Write", f"P:/script{ext}")
            assert result["continue"] is False, f"Expected block for {ext}"

    def test_non_code_file_allowed_at_root(self):
        """Non-code files at workspace root should be allowed."""
        allowed = [
            "P:/README.md",
            "P:/data.json",
            "P:/notes.txt",
            "P:/image.png",
        ]
        for path in allowed:
            result = run_hook("Write", path)
            assert result["continue"] is True, f"Expected allow for {path}"


class TestSubdirectoryAllowance:
    """Test that files outside workspace root are allowed."""

    def test_python_file_in_claude_allowed(self):
        """Python files in .claude/ directory should be allowed."""
        result = run_hook("Write", "P:/.claude/hooks/script.py")
        assert result["continue"] is True

    def test_python_file_in_subdirectory_allowed(self):
        """Python files in subdirectories should be allowed."""
        result = run_hook("Write", "P:/src/module.py")
        assert result["continue"] is True

    def test_code_file_in_hooks_dir_allowed(self):
        """Code files in hooks directory should be allowed (special case)."""
        result = run_hook("Write", "P:/.claude/hooks/script.py")
        assert result["continue"] is True

    def test_md_file_in_hooks_dir_allowed(self):
        """Markdown files in hooks directory are standard, should be allowed."""
        result = run_hook("Write", "P:/.claude/hooks/README.md")
        assert result["continue"] is True


class TestEditToolSupport:
    """Test that the hook also handles Edit tool."""

    def test_edit_python_file_blocked(self):
        """Edit of Python file at root should be blocked."""
        result = run_hook("Edit", "P:/script.py")
        assert result["continue"] is False

    def test_edit_config_file_allowed(self):
        """Edit of config file at root should be allowed."""
        result = run_hook("Edit", "P:/config.toml")
        assert result["continue"] is True


class TestNonWriteTools:
    """Test that non-Write/Edit tools pass through."""

    def test_read_tool_passthrough(self):
        """Read tool should pass through (not be blocked)."""
        result = run_hook("Read", "P:/anything.py")
        assert result["continue"] is True

    def test_bash_tool_passthrough(self):
        """Bash tool should pass through (not be blocked)."""
        result = run_hook("Bash", "P:/script.py")
        assert result["continue"] is True


class TestTransientErrorHandling:
    """Test fail-open behavior on transient errors."""

    def test_empty_file_path_allowed(self):
        """Empty file path should be allowed (transient/pass-through)."""
        result = run_hook("Write", "")
        assert result["continue"] is True

    def test_missing_tool_name_allowed(self):
        """Missing tool name should pass through."""
        input_data = {"tool_input": {"file_path": "P:/script.py"}}
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )
        parsed = json.loads(result.stdout)
        assert parsed["continue"] is True


class TestHookMetadata:
    """Test that blocked responses include required metadata."""

    def test_blocked_response_has_terminal_id(self):
        """Blocked responses should include terminal_id."""
        result = run_hook("Write", "P:/script.py")
        if result["continue"] is False:
            assert "terminal_id" in result

    def test_blocked_response_has_session_id(self):
        """Blocked responses should include session_id."""
        result = run_hook("Write", "P:/script.py")
        if result["continue"] is False:
            assert "session_id" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
