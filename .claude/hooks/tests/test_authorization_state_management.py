#!/usr/bin/env python3
"""Test authorization gate state management for assistant response handling."""

import json
import os
import sys
import time
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

from PreToolUse_authorization_gate import (
    _get_state_file_path,
    _resolve_state_identifiers,
    check_authorization_state,
    cleanup_awaiting_state,
    write_awaiting_state,
)


def test_state_file_path_generation():
    """Test that state file paths include session and terminal IDs."""
    input_data = {"session_id": "test-session-123", "terminal_id": "test-terminal-456"}

    session_id, terminal_id = _resolve_state_identifiers(input_data)
    assert session_id == "test-session-123", f"Expected test-session-123, got {session_id}"
    assert terminal_id == "test-terminal-456", f"Expected test-terminal-456, got {terminal_id}"

    state_file = _get_state_file_path(session_id, terminal_id)
    assert "test-session-123" in str(state_file), f"Session ID not in path: {state_file}"
    assert "test-terminal-456" in str(state_file), f"Terminal ID not in path: {state_file}"

    print("✓ test_state_file_path_generation passed")


def test_write_and_check_state():
    """Test writing and checking authorization state."""
    input_data = {"session_id": "test-session-write", "terminal_id": "test-terminal-write"}
    command = "rm -rf test/path"

    # Clean up any existing state
    cleanup_awaiting_state(input_data)

    # Write state
    write_awaiting_state(input_data, command)

    # Check state exists
    state = check_authorization_state(input_data, command)
    assert state is not None, "State should exist after write"
    assert state.get("awaiting_response") == True, "State should be awaiting response"
    assert "rm -rf test/path" in state.get("command", ""), "Command should be in state"

    # Clean up
    cleanup_awaiting_state(input_data)

    # Verify cleanup
    state = check_authorization_state(input_data, command)
    assert state is None, "State should be None after cleanup"

    print("✓ test_write_and_check_state passed")


def test_state_ttl_expiration():
    """Test that state expires after TTL."""
    input_data = {"session_id": "test-session-ttl", "terminal_id": "test-terminal-ttl"}
    command = "rm -rf test/path"

    # Clean up any existing state
    cleanup_awaiting_state(input_data)

    # Write state
    write_awaiting_state(input_data, command)

    # Manually expire the state by modifying the file
    session_id, terminal_id = _resolve_state_identifiers(input_data)
    state_file = _get_state_file_path(session_id, terminal_id)

    state = json.loads(state_file.read_text())
    state["blocked_at"] = time.time() - 400  # 400 seconds ago (> 300 TTL)
    state_file.write_text(json.dumps(state))

    # Check state - should be expired and cleaned up
    state = check_authorization_state(input_data, command)
    assert state is None, "State should be None after expiration"
    assert not state_file.exists(), "State file should be deleted after expiration"

    print("✓ test_state_ttl_expiration passed")


def test_command_hash_mismatch():
    """Test that different commands don't share state."""
    input_data = {"session_id": "test-session-hash", "terminal_id": "test-terminal-hash"}
    command1 = "rm -rf path1"
    command2 = "rm -rf path2"

    # Clean up any existing state
    cleanup_awaiting_state(input_data)

    # Write state for command1
    write_awaiting_state(input_data, command1)

    # Check with command2 - should return None (different command)
    state = check_authorization_state(input_data, command2)
    assert state is None, "Different command should not match state"

    # Clean up
    cleanup_awaiting_state(input_data)

    print("✓ test_command_hash_mismatch passed")


def test_fallback_to_environment_variables():
    """Test fallback to environment variables for session/terminal IDs."""
    # Set environment variables
    old_session = os.environ.get("CLAUDE_SESSION_ID")
    old_terminal = os.environ.get("CLAUDE_TERMINAL_ID")

    os.environ["CLAUDE_SESSION_ID"] = "env-session-123"
    os.environ["CLAUDE_TERMINAL_ID"] = "env-terminal-456"

    input_data = {}  # No session_id/terminal_id in input_data

    try:
        session_id, terminal_id = _resolve_state_identifiers(input_data)
        assert session_id == "env-session-123", f"Expected env-session-123, got {session_id}"
        assert terminal_id == "env-terminal-456", f"Expected env-terminal-456, got {terminal_id}"

        print("✓ test_fallback_to_environment_variables passed")
    finally:
        # Restore environment
        if old_session:
            os.environ["CLAUDE_SESSION_ID"] = old_session
        else:
            os.environ.pop("CLAUDE_SESSION_ID", None)

        if old_terminal:
            os.environ["CLAUDE_TERMINAL_ID"] = old_terminal
        else:
            os.environ.pop("CLAUDE_TERMINAL_ID", None)


if __name__ == "__main__":
    print("Running authorization state management tests...")
    test_state_file_path_generation()
    test_write_and_check_state()
    test_state_ttl_expiration()
    test_command_hash_mismatch()
    test_fallback_to_environment_variables()
    print("\n✅ All tests passed!")
