#!/usr/bin/env python3
from __future__ import annotations

"""
TDD State - In-process adapter.

Handles TDD phase transitions after tool execution.
Absorbed from PostToolUse_tdd_state.py.

Original matcher: ^(Bash|WebFetch|Read|Glob|Write|Edit)$

NOTE: The standalone PostToolUse_tdd_state.py main() was truncated/incomplete.
This adapter delegates to the well-defined handle_* functions from the module.
"""

import sys
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

_hooks_dir = Path(__file__).resolve().parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))


# State directory checked before importing tdd_core (avoids 80ms import cost)
_TDD_STATE_DIR = _hooks_dir.parent / ".state" / "tdd-state"

# Cheap test-command keywords checked before importing tdd_core
_TEST_KEYWORDS = ("pytest", "unittest", "test_", "_test.py")


class TDDStateHook(PostToolUseHook):
    """Handles TDD phase transitions after tool execution."""

    tool_matcher = {"Bash", "Write", "Edit"}

    def _has_active_state_files(self) -> bool:
        """Check if any TDD state files exist without importing tdd_core."""
        if not _TDD_STATE_DIR.exists():
            return False
        return any(_TDD_STATE_DIR.glob("tdd.*.json"))

    def _looks_like_test_command(self, command: str) -> bool:
        """Cheap check before importing tdd_core.is_test_command."""
        cmd_lower = command.lower()
        return any(kw in cmd_lower for kw in _TEST_KEYWORDS)

    def _looks_like_test_file(self, path: str) -> bool:
        """Cheap check before importing TDDConfig."""
        name = Path(path).name.lower()
        return name.startswith("test_") or name.endswith("_test.py") or "/tests/" in path.replace("\\", "/")

    def _get_tdd_updated_at(self, test_file: str | None) -> str | None:
        """Get the updated_at timestamp from TDD state for deduplication.

        Returns None if state doesn't exist or has no updated_at.
        """
        if not test_file:
            return None
        try:
            from tdd_core import TDDState, normalize_path
            tdd = TDDState(normalize_path(test_file))
            state = tdd.load()
            return state.get("updated_at")
        except (OSError, ImportError, KeyError):
            return None

    def _get_updated_at_for_operation(self, tool_name: str, tool_input: dict[str, Any]) -> tuple[str | None, str | None]:
        """Get relevant TDD state timestamp before operation.

        Returns:
            tuple: (test_file, updated_at_timestamp)
            - test_file: The test file path (or None if not applicable)
            - updated_at: The timestamp before operation (or None)
        """
        if tool_name in ("Write", "Edit"):
            file_path = tool_input.get("file_path", "")
            if not file_path:
                return None, None
            # For test files, check their own state
            if self._looks_like_test_file(file_path):
                return file_path, self._get_tdd_updated_at(file_path)
            # For impl files, check active cycle
            return None, None  # Will be detected via find_active_tdd_cycle if needed

        elif tool_name == "Bash":
            # For test runs, extract test file from command or find active cycle
            command = tool_input.get("command", "")
            if command and self._looks_like_test_command(command):
                try:
                    from tdd_core import (
                        TDDState,
                        extract_test_file_from_command,
                        find_active_tdd_cycle,
                    )
                    test_file = extract_test_file_from_command(command)
                    if not test_file:
                        tdd = find_active_tdd_cycle()
                        if tdd:
                            state = tdd.load()
                            test_file = state.get("test_file")
                    return test_file, self._get_tdd_updated_at(test_file) if test_file else (None, None)
                except ImportError:
                    pass
            return None, None

        return None, None

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        # Cheap early exits BEFORE importing tdd_core (~80ms saved when no TDD active)
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            if not command or not self._looks_like_test_command(command):
                return {"passed": True}

        elif tool_name in ("Write", "Edit"):
            file_path = tool_input.get("file_path", "")
            if not file_path:
                return {"passed": True}
            # Skip import if not a test file AND no active TDD cycle
            if not self._looks_like_test_file(file_path) and not self._has_active_state_files():
                return {"passed": True}

        # Past cheap gates — now do the heavy imports
        from PostToolUse_tdd_state import (
            handle_impl_file_write,
            handle_test_file_write,
            handle_test_run,
        )
        from tdd_core import TDDConfig, cleanup_expired_states

        cleanup_expired_states()
        config = TDDConfig()

        # === DEDUPLICATION GUARD ===
        # Capture state timestamp BEFORE operation to detect if state was actually modified
        # This prevents double-injection when both global and skill hooks fire
        test_file_before, updated_at_before = self._get_updated_at_for_operation(tool_name, tool_input)

        result_data = None

        if tool_name in ("Write", "Edit"):
            file_path = tool_input.get("file_path", "")
            result_data = handle_test_file_write(file_path, config)
            if not result_data:
                result_data = handle_impl_file_write(file_path, config)

        elif tool_name == "Bash":
            command = tool_input.get("command", "")
            exit_code = tool_response.get("exit_code", 0) if isinstance(tool_response, dict) else 0
            stdout = ""
            stderr = ""
            if isinstance(tool_response, dict):
                stdout = str(tool_response.get("stdout", tool_response.get("output", "")))
                stderr = str(tool_response.get("stderr", ""))
            result_data = handle_test_run(command, exit_code, stdout, stderr)

        # === DEDUPLICATION GUARD (continued) ===
        # Only inject if state was actually modified (updated_at changed)
        if result_data and result_data.get("message"):
            # Check if state was actually updated
            updated_at_after = self._get_tdd_updated_at(test_file_before) if test_file_before else None
            if updated_at_before != updated_at_after:
                # State was modified - this hook made the change
                return {"passed": True, "injection": result_data["message"]}
            else:
                # State unchanged - skill hook already handled it, skip duplicate injection
                return {"passed": True}

        return {"passed": True}
