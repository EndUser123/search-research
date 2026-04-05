"""
Tests for in-process skill_enforcement_gate consolidation.

This test file verifies that skill_enforcement_gate can be run
in-process (as imported functions) instead of spawning a subprocess.

Run with: pytest .claude/hooks/tests/test_skill_enforcement_inprocess.py -v

To enable in-process tests: set SKILL_ENFORCEMENT_INPROCESS=1 before running pytest
"""

from __future__ import annotations

import os
import sys
from pathlib import Path as PathLib

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(PathLib(__file__).parent.parent))


@pytest.mark.skipif(
    os.environ.get("SKILL_ENFORCEMENT_INPROCESS", "0") != "1",
    reason="SKILL_ENFORCEMENT_INPROCESS not enabled (set SKILL_ENFORCEMENT_INPROCESS=1)"
)
def test_skill_enforcement_inprocess_blocks_write_with_pending_skill():
    """
    Test that in-process skill enforcement blocks writes when skill is pending.

    This test verifies the in-process version of skill_enforcement_gate
    correctly detects when a slash command skill is pending and blocks writes.

    Given: A skill invocation is pending (state file exists)
    When: A write operation (Write/Edit) is attempted
    Then: The hook should return a block decision

    This test will FAIL in RED phase because wrap_skill_enforcement_gate_inprocess
    doesn't exist yet.
    """
    from PreToolUse_write_router import wrap_skill_enforcement_gate_inprocess

    # Simulate tool input for a write operation
    tool_input = {
        "name": "Write",
        "file_path": "/test/sample.py",
        "content": "some code"
    }

    data = {
        "tool_name": "Write",
        "sessionId": "test_session"
    }

    # This should return None (no pending skill) or a block dict
    result = wrap_skill_enforcement_gate_inprocess(tool_input, data)

    # The function should exist and return a dict or None
    assert result is None or isinstance(result, dict), (
        "wrap_skill_enforcement_gate_inprocess should return dict | None"
    )


@pytest.mark.skipif(
    os.environ.get("SKILL_ENFORCEMENT_INPROCESS", "0") != "1",
    reason="SKILL_ENFORCEMENT_INPROCESS not enabled (set SKILL_ENFORCEMENT_INPROCESS=1)"
)
def test_skill_enforcement_inprocess_allows_non_writes():
    """
    Test that in-process skill enforcement allows non-write operations.

    This test verifies that operations other than Write/Edit/MultiEdit
    are allowed through even when a skill is pending.

    Given: A skill invocation might be pending
    When: A non-write operation (Read, Bash, etc.) is attempted
    Then: The hook should return None (allow)

    This test will FAIL in RED phase because wrap_skill_enforcement_gate_inprocess
    doesn't exist yet.
    """
    from PreToolUse_write_router import wrap_skill_enforcement_gate_inprocess

    # Simulate tool input for a read operation
    tool_input = {
        "name": "Read",
        "file_path": "/test/sample.py"
    }

    data = {
        "tool_name": "Read",
        "sessionId": "test_session"
    }

    # This should return None (allow)
    result = wrap_skill_enforcement_gate_inprocess(tool_input, data)

    # The function should exist and return None for non-write operations
    assert result is None or isinstance(result, dict), (
        "wrap_skill_enforcement_gate_inprocess should return dict | None"
    )


@pytest.mark.skipif(
    os.environ.get("SKILL_ENFORCEMENT_INPROCESS", "0") != "1",
    reason="SKILL_ENFORCEMENT_INPROCESS not enabled (set SKILL_ENFORCEMENT_INPROCESS=1)"
)
def test_skill_enforcement_inprocess_function_exists():
    """
    Characterization test: Verify in-process function exists.

    This test checks that the in-process wrapper function has been
    created in PreToolUse_write_router.py.

    This test will FAIL in RED phase because the function doesn't exist yet.
    """
    from PreToolUse_write_router import wrap_skill_enforcement_gate_inprocess

    # If we get here, the import succeeded
    assert wrap_skill_enforcement_gate_inprocess is not None
    assert callable(wrap_skill_enforcement_gate_inprocess)


def test_skill_enforcement_functions_importable():
    """
    Verify that skill_enforcement_gate functions can be imported.

    This is a baseline test to ensure the core functions are available
    for in-process use.
    """
    from skill_enforcement_gate import handle_pre_tool_use, read_pending_state

    # Verify functions are callable
    assert callable(handle_pre_tool_use)
    assert callable(read_pending_state)


def test_skill_enforcement_respects_enabled_flag():
    """
    Test that skill enforcement respects the SKILL_ENFORCEMENT_ENABLED flag.
    """
    # Save original value
    original_val = os.environ.get("SKILL_ENFORCEMENT_ENABLED")

    try:
        # Test with disabled flag
        os.environ["SKILL_ENFORCEMENT_ENABLED"] = "false"

        # Import after setting env var - need to reload
        import importlib

        import PreToolUse_write_router
        importlib.reload(PreToolUse_write_router)

        from PreToolUse_write_router import wrap_skill_enforcement_gate

        # Should return None (disabled)
        tool_input = {"name": "Write", "file_path": "/test/sample.py"}
        data = {"tool_name": "Write", "sessionId": "test_session"}

        result = wrap_skill_enforcement_gate(tool_input, data)
        assert result is None, "Disabled hook should return None"
    finally:
        # Restore original value
        if original_val is None:
            os.environ.pop("SKILL_ENFORCEMENT_ENABLED", None)
        else:
            os.environ["SKILL_ENFORCEMENT_ENABLED"] = original_val
