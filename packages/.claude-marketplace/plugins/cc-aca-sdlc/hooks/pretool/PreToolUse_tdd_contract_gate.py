#!/usr/bin/env python3
"""
PreToolUse TDD Contract Gate for Clean-Room TDD Loop v2.

Enforces Three-File Contract: blocks non-TDD edits to contracted files.

Rules:
- RED phase: Can edit both test files and impl files
- GREEN phase: Can edit impl files, CANNOT edit test files
- REFACTOR phase: Can edit impl files, CANNOT edit test files
- Non-contract files: Always allowed

ADR: P:/docs/adrs/ADR-20260324-clean-room-tdd-loop.md
"""

from __future__ import annotations

# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import os
import sys
from pathlib import Path
from typing import Any

# Add hooks directory to path for imports
hooks_dir = Path(__file__).resolve().parent
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

from tdd.tdd_phase_state import TDDPhaseStateManager


def _is_test_file(file_path: Path) -> bool:
    """Check if a file is a test file based on naming conventions.

    Test file patterns:
    - test_*.py (pytest standard)
    - *_test.py (some frameworks)
    - conftest.py (pytest fixtures)
    - Files in tests/ directories

    Args:
        file_path: Path to check

    Returns:
        True if file matches test file patterns
    """
    name = file_path.name.lower()
    parent = file_path.parent.name.lower()

    # Standard pytest patterns
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if name.endswith("_test.py"):
        return True
    if name == "conftest.py":
        return True

    # Files in tests/ directories
    if parent == "tests" or parent == "test":
        return True

    return False


def _get_impl_for_test(test_path: Path) -> Path:
    """Find the implementation file associated with a test file.

    Patterns:
    - test_foo.py → foo.py
    - foo_test.py → foo.py
    - tests/test_bar.py → bar.py (or tests/bar.py)

    Args:
        test_path: Path to test file

    Returns:
        Expected path to implementation file
    """
    name = test_path.name

    # test_foo.py → foo.py
    if name.startswith("test_"):
        impl_name = name[5:]  # Remove "test_" prefix
        return test_path.parent / impl_name

    # foo_test.py → foo.py
    if name.endswith("_test.py"):
        impl_name = name[:-8] + ".py"  # Remove "_test" suffix
        return test_path.parent / impl_name

    # Fallback: same name in same directory
    return test_path


def _get_state_manager(
    input_data: dict[str, Any],
    state_dir: Path | None = None,
) -> TDDPhaseStateManager:
    """Create a TDDPhaseStateManager from hook input data.

    Args:
        input_data: Hook input containing session_id and terminal_id
        state_dir: Optional state directory override

    Returns:
        Configured TDDPhaseStateManager instance
    """
    session_id = input_data.get("session_id", "default")
    terminal_id = input_data.get("terminal_id", "default")

    return TDDPhaseStateManager(
        session_id=session_id,
        terminal_id=terminal_id,
        state_dir=state_dir,
    )


def process_hook(
    input_data: dict[str, Any],
    state_dir: Path | None = None,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Process PreToolUse hook for TDD contract enforcement.

    Args:
        input_data: Hook input containing:
            - name: Tool name (Edit, Write, etc.)
            - tool_input: Tool-specific input with file_path
            - session_id: Session identifier
            - terminal_id: Terminal identifier
        state_dir: Optional state directory override

    Returns:
        Tuple of (allow, reason, context):
        - allow: True if operation should proceed
        - reason: Human-readable explanation
        - context: Additional context (bypassed flag, etc.)
    """
    # Check bypass environment variable
    bypass_env = os.environ.get("TDD_CONTRACT_BYPASS", "0")
    if bypass_env == "1":
        return True, "TDD contract bypass enabled", {"bypassed": True}

    tool_name = input_data.get("name", "")
    tool_input = input_data.get("tool_input", {})
    file_path_str = tool_input.get("file_path", "")

    # Only check file-modifying tools
    if tool_name not in ("Edit", "Write", "MultiEdit"):
        return True, f"Tool {tool_name} does not modify files", None

    if not file_path_str:
        return True, "No file path specified", None

    file_path = Path(file_path_str)

    # Check if this is a test file
    is_test = _is_test_file(file_path)

    # If not a test file, check if it's in a contract
    if not is_test:
        # For impl files, check if there's an associated test file
        # to determine if they're in a contract
        manager = _get_state_manager(input_data, state_dir)
        all_files = manager.get_all_files()

        # Check if this file is tracked
        str_path = str(file_path)
        if str_path not in all_files:
            # Not in a contract - allow
            return True, "File not in TDD contract", None

        # File is tracked - get its phase
        phase = manager.get_phase(str_path)
        if phase is None:
            return True, "File not in TDD contract", None

        # Impl files can be edited in RED, GREEN, REFACTOR phases
        if phase.can_edit_impl():
            return True, f"Impl file editable in {phase.value} phase", {"phase": phase.value}
        else:
            return False, f"Cannot edit impl file in {phase.value} phase", {"phase": phase.value}

    # This is a test file - find associated impl file
    impl_path = _get_impl_for_test(file_path)
    manager = _get_state_manager(input_data, state_dir)

    # Check if impl file is in a contract
    str_impl_path = str(impl_path)
    phase = manager.get_phase(str_impl_path)

    if phase is None:
        # No contract exists - allow (user may be starting new TDD cycle)
        return True, "No TDD contract for this test file", None

    # Test file edit rules based on phase
    if phase.can_edit_test():
        return True, f"Test file editable in {phase.value} phase", {"phase": phase.value}
    else:
        return (
            False,
            f"Cannot edit test file during {phase.value} phase. "
            f"Test modifications only allowed in RED phase per Three-File Contract.",
            {"phase": phase.value, "impl_file": str_impl_path},
        )


if __name__ == "__main__":
    import json

    # Read input from stdin
    try:
        input_text = sys.stdin.read()
        input_data = json.loads(input_text) if input_text.strip() else {}
    except json.JSONDecodeError:
        print(json.dumps({"decision": "approve"}))
        sys.exit(0)

    allow, reason, context = process_hook(input_data)

    result = {
        "decision": "allow" if allow else "deny",
        "reason": reason,
    }
    if context:
        result["context"] = context

    print(json.dumps(result))
    sys.exit(0 if allow else 2)
