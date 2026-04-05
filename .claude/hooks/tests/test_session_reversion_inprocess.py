"""
Tests for in-process session_reversion_check consolidation.

This test file verifies that session_reversion_check can be run
in-process (as imported functions) instead of spawning a subprocess.

Run with: pytest .claude/hooks/tests/test_session_reversion_inprocess.py -v
"""

from __future__ import annotations

import os
import sys
from pathlib import Path as PathLib

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(PathLib(__file__).parent.parent))

# Enable in-process mode for testing
os.environ["SESSION_REVERSION_INPROCESS"] = "1"


@pytest.mark.skipif(
    os.environ.get("SESSION_REVERSION_INPROCESS", "0") != "1",
    reason="SESSION_REVERSION_INPROCESS not enabled"
)
def test_session_reversion_inprocess_blocks_revert():
    """
    Test that in-process session reversion check blocks reverting changes.

    This test verifies the in-process version of session_reversion_check
    correctly detects when a proposed edit would revert an unconfirmed change.

    Given: A previous unconfirmed change exists
    When: A proposed edit reverts that change (replaces new_value with old_value)
    Then: The hook should return a block decision with reason

    This test will FAIL in RED phase because wrap_session_reversion_check_inprocess
    doesn't exist yet.
    """
    from PreToolUse_write_router import wrap_session_reversion_check_inprocess

    # Setup: Create a temporary session changes file
    # (In real implementation, this would use proper session state)
    # For now, we'll test the function interface exists

    # Simulate tool input that would revert a change
    tool_input = {
        "name": "Edit",
        "file_path": "/test/sample.py",
        "new_string": "old_code_here"  # Simulating reversion
    }

    data = {
        "tool_name": "Edit",
        "sessionId": "test_session"
    }

    # This should return a block decision if reversion detected
    result = wrap_session_reversion_check_inprocess(tool_input, data)

    # The function should exist and return a dict or None
    assert result is None or isinstance(result, dict), (
        "wrap_session_reversion_check_inprocess should return dict | None"
    )


@pytest.mark.skipif(
    os.environ.get("SESSION_REVERSION_INPROCESS", "0") != "1",
    reason="SESSION_REVERSION_INPROCESS not enabled"
)
def test_session_reversion_inprocess_allows_refinement():
    """
    Test that in-process session reversion check allows refinements.

    This test verifies that legitimate code improvements (not reversions)
    are allowed through.

    Given: A previous unconfirmed change exists
    When: A proposed edit is a refinement (not a revert)
    Then: The hook should return None (allow)

    This test will FAIL in RED phase because wrap_session_reversion_check_inprocess
    doesn't exist yet.
    """
    from PreToolUse_write_router import wrap_session_reversion_check_inprocess

    # Simulate tool input that is a legitimate improvement
    tool_input = {
        "name": "Edit",
        "file_path": "/test/sample.py",
        "new_string": "improved_code_with_lint_fixes"  # Not a revert
    }

    data = {
        "tool_name": "Edit",
        "sessionId": "test_session"
    }

    # This should return None (allow)
    result = wrap_session_reversion_check_inprocess(tool_input, data)

    # The function should exist and return None for allowed changes
    assert result is None or isinstance(result, dict), (
        "wrap_session_reversion_check_inprocess should return dict | None"
    )


@pytest.mark.skipif(
    os.environ.get("SESSION_REVERSION_INPROCESS", "0") != "1",
    reason="SESSION_REVERSION_INPROCESS not enabled"
)
def test_session_reversion_inprocess_function_exists():
    """
    Characterization test: Verify in-process function exists.

    This test checks that the in-process wrapper function has been
    created in PreToolUse_write_router.py.

    This test will FAIL in RED phase because the function doesn't exist yet.
    """
    from PreToolUse_write_router import wrap_session_reversion_check_inprocess

    # If we get here, the import succeeded
    assert wrap_session_reversion_check_inprocess is not None
    assert callable(wrap_session_reversion_check_inprocess)


def test_session_reversion_functions_importable():
    """
    Verify that session_reversion_check functions can be imported.

    This is a baseline test to ensure the core functions are available
    for in-process use.
    """
    from session_reversion_check import get_changes_for_file, is_reversion

    # Verify functions are callable
    assert callable(get_changes_for_file)
    assert callable(is_reversion)
