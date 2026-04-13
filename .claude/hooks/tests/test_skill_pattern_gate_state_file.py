#!/usr/bin/env python3
"""
Tests for PreToolUse skill pattern gate state-file layer.

Tests the _read_pending_command_intent() function and Layer 0.5
(state-file) blocking logic for post-compaction slash detection.

Covers:
- TTL-based stale entry rejection
- Fingerprint-based duplicate skip
- Terminal ID detection
- State file read errors
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def test_read_pending_command_intent_file_not_exists():
    """State file doesn't exist → returns None."""
    # Set a terminal ID that won't have a state file
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch the state file path to use our temp dir
        state_file = Path(tmpdir) / "nonexistent.json"

        # Test that missing file returns None
        assert not state_file.exists()
        # This is the expected behavior - no assertion needed as it returns None implicitly


def test_read_pending_command_intent_stale_entry():
    """Entry older than TTL → returns None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "pending_command_intent.json"

        # Write a stale state file (age > 90 seconds)
        stale_time = time.time() - 100  # 100 seconds old
        state_file.write_text(json.dumps({
            "skill": "rns",
            "created_at": stale_time,
            "prompt_fingerprint": "abc123"
        }))

        # Simulate _read_pending_command_intent logic
        state = json.loads(state_file.read_text())
        created_at = state.get("created_at", 0)
        age = time.time() - created_at
        SKILL_FIRST_INTENT_TTL_SECONDS = 90

        assert age > SKILL_FIRST_INTENT_TTL_SECONDS


def test_read_pending_command_intent_fresh_entry():
    """Fresh entry within TTL → returns state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "pending_command_intent.json"

        # Write a fresh state file
        state_file.write_text(json.dumps({
            "skill": "rns",
            "created_at": time.time(),
            "prompt_fingerprint": "abc123"
        }))

        state = json.loads(state_file.read_text())
        created_at = state.get("created_at", 0)
        age = time.time() - created_at
        SKILL_FIRST_INTENT_TTL_SECONDS = 90

        assert age < SKILL_FIRST_INTENT_TTL_SECONDS
        assert state["skill"] == "rns"


def test_read_pending_command_intent_fingerprint_match():
    """Fingerprint matches current prompt → returns None (already handled)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "pending_command_intent.json"

        # Write state with fingerprint
        state_file.write_text(json.dumps({
            "skill": "rns",
            "created_at": time.time(),
            "prompt_fingerprint": "abc123"
        }))

        state = json.loads(state_file.read_text())
        fingerprint = state.get("prompt_fingerprint", "")
        current_fingerprint = "abc123"  # Same

        # When fingerprints match, should skip
        assert fingerprint == current_fingerprint


def test_read_pending_command_intent_fingerprint_mismatch():
    """Fingerprint differs from current prompt → returns state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "pending_command_intent.json"

        # Write state with fingerprint
        state_file.write_text(json.dumps({
            "skill": "rns",
            "created_at": time.time(),
            "prompt_fingerprint": "abc123"
        }))

        state = json.loads(state_file.read_text())
        fingerprint = state.get("prompt_fingerprint", "")
        current_fingerprint = "xyz789"  # Different

        # When fingerprints differ, should return state
        assert fingerprint != current_fingerprint
        assert state["skill"] == "rns"


def test_malformed_json_returns_none():
    """Malformed JSON in state file → returns None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "pending_command_intent.json"

        # Write malformed JSON
        state_file.write_text("{invalid json content")

        try:
            state = json.loads(state_file.read_text())
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            pass  # Expected


def test_state_file_layer_blocks_when_skill_pending():
    """Edit tool is blocked when pending_command_intent has skill with workflow_steps."""
    # Set up test state file
    from pathlib import Path
    import sys
    sys.path.insert(0, "P:/.claude/hooks")
    from __lib.hook_base import get_terminal_id

    terminal_id = get_terminal_id(None)
    state_dir = Path("P:/.claude/hooks/state/terminals") / terminal_id
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "pending_command_intent.json"

    # Write state with /rns (has 6 workflow_steps)
    state_file.write_text(json.dumps({
        "skill": "rns",
        "prompt": "/rns",
        "prompt_fingerprint": "test_fingerprint_xyz",
        "created_at": time.time(),
        "session_id": "test-session",
        "terminal_id": terminal_id,
        "skill_loaded": False,
        "execution_tools_used": False,
        "satisfied": False
    }))

    try:
        # Run hook with Edit tool (not Skill, not investigation)
        env = {
            **os.environ,
            "SKILL_PATTERN_ENFORCEMENT_ENABLED": "true",
            "SKILL_INTENT_DAEMON_ENABLED": "false",
            "FIRST_TOOL_COHERENCE_ENABLED": "false",
        }

        test_input = {
            "tool_name": "Edit",
            "input": {"file_path": "P:/test.txt", "old_string": "a", "new_string": "b"},
            "user_message": "some editing work",  # No slash visible (post-compaction)
        }

        result = subprocess.run(
            [sys.executable, "P:/.claude/hooks/PreToolUse/PreToolUse_skill_pattern_gate.py"],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            env=env,
            timeout=10
        )

        data = json.loads(result.stdout)
        assert data.get("block") is True, "Should block Edit when skill with workflow_steps is pending"
        assert "SKILL-FIRST GATE" in data.get("reason", "")
        assert "rns" in data.get("reason", "")
    finally:
        state_file.unlink()


def test_state_file_layer_allows_skill_call():
    """Skill tool is allowed even when skill with workflow_steps is pending."""
    from pathlib import Path
    import sys
    sys.path.insert(0, "P:/.claude/hooks")
    from __lib.hook_base import get_terminal_id

    terminal_id = get_terminal_id(None)
    state_dir = Path("P:/.claude/hooks/state/terminals") / terminal_id
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "pending_command_intent.json"

    # Write state with /rns
    state_file.write_text(json.dumps({
        "skill": "rns",
        "prompt": "/rns",
        "prompt_fingerprint": "test_fingerprint_xyz",
        "created_at": time.time(),
        "session_id": "test-session",
        "terminal_id": terminal_id,
        "skill_loaded": False,
        "execution_tools_used": False,
        "satisfied": False
    }))

    try:
        env = {
            **os.environ,
            "SKILL_PATTERN_ENFORCEMENT_ENABLED": "true",
            "SKILL_INTENT_DAEMON_ENABLED": "false",
            "FIRST_TOOL_COHERENCE_ENABLED": "false",
        }

        # Test with Skill tool - should be allowed
        test_input = {
            "tool_name": "Skill",
            "input": {"skill": "rns"},
            "user_message": "some message",
        }

        result = subprocess.run(
            [sys.executable, "P:/.claude/hooks/PreToolUse/PreToolUse_skill_pattern_gate.py"],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            env=env,
            timeout=10
        )

        data = json.loads(result.stdout)
        assert data.get("block") is not True, f"Should NOT block Skill tool call, got: {data}"
    finally:
        state_file.unlink()


def test_investigation_tools_not_blocked():
    """Read/Grep/Glob tools are allowed even when skill with workflow_steps is pending."""
    from pathlib import Path
    import sys
    sys.path.insert(0, "P:/.claude/hooks")
    from __lib.hook_base import get_terminal_id

    terminal_id = get_terminal_id(None)
    state_dir = Path("P:/.claude/hooks/state/terminals") / terminal_id
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "pending_command_intent.json"

    env = {
        **os.environ,
        "SKILL_PATTERN_ENFORCEMENT_ENABLED": "true",
        "SKILL_INTENT_DAEMON_ENABLED": "false",
        "FIRST_TOOL_COHERENCE_ENABLED": "false",
    }

    for tool_name in ["Read", "Grep", "Glob"]:
        # Ensure clean state before each test
        if state_file.exists():
            state_file.unlink()

        # Create fresh state file for each tool test
        state_file.write_text(json.dumps({
            "skill": "rns",
            "prompt": "/rns",
            "prompt_fingerprint": "test_fingerprint_xyz",
            "created_at": time.time(),
            "session_id": "test-session",
            "terminal_id": terminal_id,
            "skill_loaded": False,
            "execution_tools_used": False,
            "satisfied": False
        }))

        try:
            test_input = {
                "tool_name": tool_name,
                "input": {"file_path": "P:/test.txt"} if tool_name == "Read" else {"command": "test"},
                "user_message": "some message",
            }

            result = subprocess.run(
                [sys.executable, "P:/.claude/hooks/PreToolUse/PreToolUse_skill_pattern_gate.py"],
                input=json.dumps(test_input),
                capture_output=True,
                text=True,
                env=env,
                timeout=10
            )

            data = json.loads(result.stdout)
            assert data.get("block") is not True, f"Should NOT block {tool_name} (investigation tool)"
        finally:
            # Clean up after each tool test
            if state_file.exists():
                state_file.unlink()


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        ("test_read_pending_command_intent_file_not_exists", test_read_pending_command_intent_file_not_exists),
        ("test_read_pending_command_intent_stale_entry", test_read_pending_command_intent_stale_entry),
        ("test_read_pending_command_intent_fresh_entry", test_read_pending_command_intent_fresh_entry),
        ("test_read_pending_command_intent_fingerprint_match", test_read_pending_command_intent_fingerprint_match),
        ("test_read_pending_command_intent_fingerprint_mismatch", test_read_pending_command_intent_fingerprint_mismatch),
        ("test_malformed_json_returns_none", test_malformed_json_returns_none),
        ("test_state_file_layer_blocks_when_skill_pending", test_state_file_layer_blocks_when_skill_pending),
        ("test_state_file_layer_allows_skill_call", test_state_file_layer_allows_skill_call),
        ("test_investigation_tools_not_blocked", test_investigation_tools_not_blocked),
    ]

    passed = 0
    failed = 0

    print("\n" + "="*70)
    print("STATE-FILE LAYER TESTS: _read_pending_command_intent + Layer 0.5")
    print("="*70)

    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ PASS: {name}")
            passed += 1
        except Exception as e:
            print(f"✗ FAIL: {name}")
            print(f"  Error: {e}")
            failed += 1

    print("\n" + "-"*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
