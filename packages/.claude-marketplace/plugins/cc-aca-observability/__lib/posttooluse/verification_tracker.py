#!/usr/bin/env python3
"""
Verification Tracker Hook

Tracks whether verification commands were actually executed:
- Test execution: pytest, unittest
- Type checking: mypy, pyright
- Linting: ruff, flake8

PRINCIPLE: Structural facts (tool use) cannot be gamed like vocabulary patterns.

Writes to state file for stop_success_validator to read.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

from _bootstrap import state_root
STATE_DIR = state_root()
STATE_DIR.mkdir(parents=True, exist_ok=True)


# === TERMINAL DETECTION ===
def _get_terminal_id() -> str:
    """Get terminal ID for state file scoping.

    FAIL-FAST: If terminal_detection fails, this hook will not run
    rather than silently breaking isolation and allowing cross-terminal
    warning leakage.
    """
    try:
        # Import terminal detection module
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "terminal_detection", Path(__file__).resolve().parent.parent / "terminal_detection.py"
        )
        if spec and spec.loader:
            terminal_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(terminal_module)
            terminal_id = terminal_module.detect_terminal_id()
            if terminal_id:
                return terminal_id
    except Exception as e:
        _logger.error("ERROR: terminal_detection failed: %s", e)
        _logger.warning("verification_tracker: Cannot ensure terminal isolation. Aborting.")
        sys.exit(1)

    # Fail-fast: No terminal ID means we can't ensure isolation
    _logger.error("ERROR: terminal_detection returned empty terminal_id")
    _logger.warning("verification_tracker: Cannot ensure terminal isolation. Aborting.")
    sys.exit(1)


def _get_state_file() -> Path:
    """Get terminal-scoped state file path."""
    terminal_id = _get_terminal_id()
    safe_terminal_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", terminal_id)
    return STATE_DIR / f"verification_state_{safe_terminal_id}.json"


# Detect ACTUAL tool execution, not claims about execution
VERIFICATION_COMMANDS = [
    # Test frameworks
    (r"pytest\b", "pytest"),
    (r"python\s+-m\s+pytest", "pytest"),
    (r"python\s+-m\s+unittest", "unittest"),
    # Type checkers
    (r"mypy\b", "mypy"),
    (r"pyright\b", "pyright"),
    # Linters
    (r"ruff\s+check", "ruff"),
    (r"flake8\b", "flake8"),
    (r"pylint\b", "pylint"),
    # Direct test script execution
    (r"python\s+[^\s]*test[^\s]*\.py", "test_script"),
    # Node test runners
    (r"npm\s+test", "npm_test"),
    (r"npx\s+jest", "jest"),
]


def _create_default_state(terminal_id: str) -> dict:
    """Create fresh default verification state.

    Args:
        terminal_id: Terminal identifier for session isolation

    Returns:
        Default state dictionary with all required fields
    """
    return {
        "code_modified": False,
        "modified_files": [],
        "modification_timestamps": {},
        "verification_executed": False,
        "verification_types": [],
        "session_start": datetime.now(UTC).isoformat(),
        "terminal_id": terminal_id,
        "pid": os.getpid(),
        "files_touched": [],
    }


class VerificationTracker(PostToolUseHook):
    """Track verification commands executed during session."""

    env_var = "VERIFICATION_TRACKER_ENABLED"
    default_enabled = True

    def __init__(self):
        """Initialize tracker and cache state file path and terminal ID."""
        super().__init__()
        # Cache terminal_id for consistent session isolation
        self._terminal_id = _get_terminal_id()
        # Cache state file path to support test patches
        self._state_file = _get_state_file()

    def _load_state(self) -> dict:
        """Load current session state."""
        if self._state_file.exists():
            try:
                with open(self._state_file) as f:
                    state = json.load(f)
                    # Ensure files_touched exists for backward compatibility
                    if "files_touched" not in state:
                        state["files_touched"] = []
                    return state
            except (OSError, json.JSONDecodeError):
                pass
        return _create_default_state(self._terminal_id)

    def _save_state(self, state: dict) -> None:
        """Save session state."""
        try:
            with open(self._state_file, "w") as f:
                json.dump(state, f, indent=2)
        except OSError:
            pass

    def process(
        self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """Track code modifications and verification executions."""
        if not tool_name:
            return {"passed": True}

        state = self._load_state()

        # Track code modifications with timestamps
        if tool_name in ("Write", "Edit", "MultiEdit"):
            file_path = tool_input.get("file_path") or tool_input.get("path", "")
            if file_path:
                normalized = file_path.replace("\\", "/")
                code_extensions = [".py", ".ts", ".js", ".tsx", ".jsx", ".rs", ".go"]

                if any(normalized.endswith(ext) for ext in code_extensions):
                    state["code_modified"] = True
                    # Track timestamp for cross-terminal filtering
                    state["modification_timestamps"][normalized] = datetime.now(UTC).isoformat()
                    if normalized not in state["modified_files"]:
                        state["modified_files"].append(normalized)

                # Track files_touched for Write and Edit operations
                if tool_name in ("Write", "Edit"):
                    operation = "write" if tool_name == "Write" else "edit"
                    state["files_touched"].append(
                        {
                            "path": normalized,
                            "operation": operation,
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    )

        # Track verification execution
        elif tool_name == "Bash":
            command = tool_input.get("command", "")
            for pattern, vtype in VERIFICATION_COMMANDS:
                if re.search(pattern, command, re.IGNORECASE):
                    state["verification_executed"] = True
                    if vtype not in state["verification_types"]:
                        state["verification_types"].append(vtype)

        self._save_state(state)
        return {"passed": True}  # Silent tracker


def get_verification_state() -> dict:
    """Get current verification state (for use by stop hook)."""
    state_file = _get_state_file()
    if state_file.exists():
        try:
            with open(state_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return _create_default_state(_get_terminal_id())


def clear_verification_state() -> None:
    """Clear state after stop hook processes it."""
    state_file = _get_state_file()
    try:
        if state_file.exists():
            state_file.unlink()
    except OSError:
        pass
