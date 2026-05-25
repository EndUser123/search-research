#!/usr/bin/env python3
"""Verify HookBytecodeGuard fires on hook .py file edits."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from posttooluse.PostToolUse_hook_bytecode_guard import HookBytecodeGuard


def _make_data(tool_name: str, file_path: str) -> dict:
    return {
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path},
        "tool_response": {},
    }


class TestHookBytecodeGuard:
    """Verify HookBytecodeGuard clears bytecode for hook file edits."""

    def test_edit_on_hook_file_clears_cache(self) -> None:
        guard = HookBytecodeGuard()
        # Simulate an Edit to a hook .py file under the hooks directory
        data = _make_data("Edit", "P:/.claude/hooks/__lib/path_sanitizer.py")
        result = guard.run(data)

        assert result["passed"] is True
        assert result.get("skipped") is not True, f"Should not skip: {result}"
        assert result["metadata"]["hook_name"] == "path_sanitizer"
        assert result["metadata"]["cache_cleared"] is True

    def test_write_on_hook_file_clears_cache(self) -> None:
        guard = HookBytecodeGuard()
        data = _make_data("Write", "P:/.claude/hooks/posttooluse/python_syntax_checker.py")
        result = guard.run(data)

        assert result["passed"] is True
        assert result.get("skipped") is not True, f"Should not skip: {result}"
        assert result["metadata"]["hook_name"] == "python_syntax_checker"

    def test_edit_on_non_hook_file_skips(self) -> None:
        guard = HookBytecodeGuard()
        # Use a real .py file that exists but is NOT under the hooks directory
        data = _make_data("Edit", "P:/.claude/settings.json")
        result = guard.run(data)

        assert result["skipped"] is True
        # File exists but is not a .py file, so it skips with "not_python"
        assert result["reason"] == "not_python"

    def test_edit_on_non_python_file_skips(self) -> None:
        guard = HookBytecodeGuard()
        data = _make_data("Edit", "P:/.claude/hooks/README.md")
        result = guard.run(data)

        assert result["skipped"] is True
        assert result["reason"] == "not_python"

    def test_edit_on_nonexistent_file_skips(self) -> None:
        guard = HookBytecodeGuard()
        data = _make_data("Edit", "P:/.claude/hooks/__lib/nonexistent_hook.py")
        result = guard.run(data)

        assert result["skipped"] is True
        assert result["reason"] == "file_not_found"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))