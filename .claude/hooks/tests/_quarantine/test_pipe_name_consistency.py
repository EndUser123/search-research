#!/usr/bin/env python3
r"""
Test for pipe name consistency between hook and daemon.

This test verifies that hook and daemon use the same fallback pipe name:
- Hook uses: \\.\pipe\csf_semantic
- Daemon uses: \\.\pipe\csf_semantic

These MUST be identical for the semantic daemon system to work correctly.

Run with: pytest P:/.claude/hooks/tests/test_pipe_name_consistency.py -v
"""

import re
import sys
from pathlib import Path
from typing import Final

import pytest

# Expected fallback pipe name that both hook and daemon must use
EXPECTED_FALLBACK_PIPE: Final = r"\\.\pipe\csf_semantic"


def _get_hook_fallback_pipe_name() -> str:
    """
    Extract the hook's fallback pipe name from source code.

    Returns:
        The fallback pipe name used by the SessionStart_semantic_daemon hook.

    Raises:
        AssertionError: If fallback pipe name pattern cannot be found.
    """
    hooks_dir = Path("P:/.claude/hooks")
    if str(hooks_dir) not in sys.path:
        sys.path.insert(0, str(hooks_dir))

    hook_file = hooks_dir / "SessionStart_semantic_daemon.py"
    hook_content = hook_file.read_text()

    # Extract the fallback pipe name from the hook
    # Looking for: return r"\\.\pipe\csf_semantic"
    match = re.search(r'return r"(\\\\\.\\pipe\\[^"]+)"', hook_content)
    assert match, "Could not find fallback pipe name in hook"

    return match.group(1)


def _get_daemon_fallback_pipe_name() -> str:
    """
    Get the daemon's fallback pipe name from the daemon module.

    Returns:
        The PIPE_NAME constant used by the unified_semantic_daemon module.
    """
    csf_src_dir = Path("P:/__csf/src")
    if str(csf_src_dir) not in sys.path:
        sys.path.insert(0, str(csf_src_dir))

    # Import PIPE_NAME from daemon module
    from daemons.unified_semantic_daemon import PIPE_NAME
    return PIPE_NAME


def test_hook_fallback_pipe_name() -> None:
    """
    Characterization: Verify the hook's fallback pipe name.

    Given: The SessionStart_semantic_daemon hook
    When: Reading the _get_daemon_pipe_name function's fallback
    Then: Should return the hardcoded fallback pipe name

    Fixed behavior: Returns \\.\\pipe\\csf_semantic
    """
    hook_pipe_name = _get_hook_fallback_pipe_name()
    assert hook_pipe_name == EXPECTED_FALLBACK_PIPE, \
        f"Hook fallback pipe name is {hook_pipe_name}"


def test_daemon_fallback_pipe_name() -> None:
    """
    Characterization: Verify the daemon's fallback pipe name.

    Given: The unified_semantic_daemon module
    When: Reading the PIPE_NAME constant
    Then: Should return the fallback pipe name

    Current behavior: Returns \\.\\pipe\\csf_semantic
    """
    daemon_pipe_name = _get_daemon_fallback_pipe_name()
    assert daemon_pipe_name == EXPECTED_FALLBACK_PIPE, \
        f"Daemon PIPE_NAME is {daemon_pipe_name}"


def test_pipe_names_are_identical() -> None:
    """
    Test that hook and daemon fallback pipe names are identical.

    Given: The semantic daemon system
    When: Comparing hook's fallback pipe name with daemon's PIPE_NAME
    Then: They MUST be identical for the system to work

    FIXED: Both now use \\.\\pipe\\csf_semantic
    """
    hook_pipe_name = _get_hook_fallback_pipe_name()
    daemon_pipe_name = _get_daemon_fallback_pipe_name()

    # This assertion passes after the fix
    assert hook_pipe_name == daemon_pipe_name, \
        f"Pipe name mismatch! Hook uses '{hook_pipe_name}' but daemon uses '{daemon_pipe_name}'. " \
        f"These must be identical for the semantic daemon to work correctly."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
