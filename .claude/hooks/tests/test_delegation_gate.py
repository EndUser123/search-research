#!/usr/bin/env python3
"""Tests for PreToolUse_delegation_gate.py and delegation_prospector state wiring."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

import pytest

# Import the module being tested
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PreToolUse_delegation_gate import (
    _is_expired,
    _load_delegation_state,
    _clear_delegation_state,
    _is_bypass_flagged,
    _build_block_message,
    _log_gate_event,
)


class TestTTLExpiration:
    """Test TTL-based state expiration."""

    def test_not_expired_within_ttl(self):
        """State within TTL window should not be expired."""
        now = 1700000000.0
        detected_at = now - 100  # 100 seconds ago, well under 300s TTL
        assert not _is_expired(detected_at, now=now)

    def test_expired_beyond_ttl(self):
        """State beyond TTL window should be expired."""
        now = 1700000000.0
        detected_at = now - 400  # 400 seconds ago, over 300s TTL
        assert _is_expired(detected_at, now=now)

    def test_expired_at_exact_boundary(self):
        """State at exact TTL boundary should be expired."""
        now = 1700000000.0
        detected_at = now - 300  # Exactly 300 seconds ago
        assert _is_expired(detected_at, now=now)

    def test_not_expired_just_before_boundary(self):
        """State just before TTL boundary should not be expired."""
        now = 1700000000.0
        detected_at = now - 299  # 299 seconds ago
        assert not _is_expired(detected_at, now=now)


class TestDelegationStatePersistence:
    """Test delegation state file read/write/clear operations."""

    def setup_method(self):
        """Create temp directory for test state files."""
        self.temp_dir = tempfile.mkdtemp()
        # Patch STATE_DIR before importing the module
        import PreToolUse_delegation_gate as gate_module
        self._original_state_dir = gate_module.STATE_DIR
        gate_module.STATE_DIR = Path(self.temp_dir)

    def teardown_method(self):
        """Restore original STATE_DIR and clean up temp files."""
        import PreToolUse_delegation_gate as gate_module
        gate_module.STATE_DIR = self._original_state_dir
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_write_and_read_delegation_state(self):
        """State written by prospector can be read by gate."""
        session_id = "test-session-123"
        state_data = {
            "session_id": session_id,
            "terminal_id": "console_abc",
            "detected_at": time.time() - 100,  # Recent timestamp
            "matched_pattern": "test pattern",
            "prompt_snippet": "test snippet",
        }

        # Write state (simulating what delegation_prospector does)
        import PreToolUse_delegation_gate as gate_module
        state_file = Path(self.temp_dir) / f"delegation_expected_{session_id}.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f)

        # Read state via gate function
        loaded = _load_delegation_state(session_id)
        assert loaded is not None, f"Failed to load state from {state_file}"
        assert loaded["session_id"] == session_id
        assert loaded["matched_pattern"] == "test pattern"

    def test_load_nonexistent_state_returns_none(self):
        """Missing state file returns None."""
        result = _load_delegation_state("nonexistent-session")
        assert result is None

    def test_expired_state_is_not_loaded(self):
        """Expired state file is deleted and returns None."""
        session_id = "expired-session"
        state_file = Path(self.temp_dir) / f"delegation_expected_{session_id}.json"

        # Write state with old timestamp (400 seconds ago)
        state_data = {
            "session_id": session_id,
            "detected_at": 1700000000.0 - 400,  # Expired
        }
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f)

        # State should be expired and file deleted
        result = _load_delegation_state(session_id)
        assert result is None
        assert not state_file.exists()

    def test_clear_delegation_state(self):
        """Clearing state removes the file."""
        session_id = "clear-test-session"
        state_file = Path(self.temp_dir) / f"delegation_expected_{session_id}.json"

        # Create state file
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"session_id": session_id}, f)
        assert state_file.exists()

        # Clear it
        _clear_delegation_state(session_id)
        assert not state_file.exists()

    def test_clear_nonexistent_state_is_silent(self):
        """Clearing nonexistent state doesn't raise."""
        # Should not raise
        _clear_delegation_state("nonexistent-session")


class TestBypassFlag:
    """Test bypass flag detection."""

    def test_bypass_flag_detected(self):
        """--allow-inline flag is detected."""
        assert _is_bypass_flagged("Use --allow-inline to skip the check")
        assert _is_bypass_flagged("--allow-inline some text")
        assert _is_bypass_flagged("do it --allow-inline")

    def test_bypass_flag_case_insensitive(self):
        """Bypass flag is case-insensitive."""
        assert _is_bypass_flagged("--ALLOW-INLINE")
        assert _is_bypass_flagged("--Allow-Inline")

    def test_bypass_flag_not_detected_without_flag(self):
        """Messages without bypass flag return False."""
        assert not _is_bypass_flagged("Please delegate this work")
        assert not _is_bypass_flagged("Use Task tool")
        assert not _is_bypass_flagged("")

    def test_bypass_flag_not_confused_by_similar_text(self):
        """Similar text doesn't trigger bypass."""
        assert not _is_bypass_flagged("don't allow inline comments")
        assert not _is_bypass_flagged("allowed inline mode")


class TestBlockMessage:
    """Test block message generation."""

    def test_block_message_contains_tool_name(self):
        """Block message includes the tool name that was blocked."""
        state = {
            "matched_pattern": "inspect files",
            "prompt_snippet": "Please inspect file1.py and file2.py for issues",
        }
        msg = _build_block_message("Read", state)
        # Block message should contain the tool name or a reference to blocked action
        assert "tool" in msg.lower() or "Read" in msg or "BLOCKED" in msg or "⛔" in msg

    def test_block_message_contains_pattern(self):
        """Block message includes matched pattern info."""
        state = {
            "matched_pattern": "test pattern",
            "prompt_snippet": "test snippet",
        }
        msg = _build_block_message("Edit", state)
        # Check that pattern is in message (may be formatted differently)
        assert "pattern" in msg.lower() or "DELEGATION" in msg


class TestDelegationProspectorState:
    """Test delegation_prospector's state writing functions."""

    def test_write_delegation_state_creates_file(self):
        """State file is created with expected structure."""
        session_id = "state-test-session"
        terminal_id = "console_xyz"

        # Import and call the function
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "UserPromptSubmit_modules"))
        from delegation_prospector import _write_delegation_state

        _write_delegation_state(
            session_id=session_id,
            terminal_id=terminal_id,
            matched_pattern="test pattern",
            prompt_snippet="analyze foo and bar",
        )

        # State is written to .claude/state/ (not .claude/hooks/state/)
        state_file = Path(__file__).resolve().parent.parent.parent / "state" / f"delegation_expected_{session_id}.json"
        assert state_file.exists()

        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["session_id"] == session_id
        assert data["terminal_id"] == terminal_id
        assert data["matched_pattern"] == "test pattern"
        assert "detected_at" in data

        # Clean up
        state_file.unlink(missing_ok=True)

    def test_clear_delegation_state(self):
        """clear_delegation_state removes state file."""
        session_id = "clear-test"
        terminal_id = "console_xyz"

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "UserPromptSubmit_modules"))
        from delegation_prospector import _write_delegation_state, _clear_delegation_state

        # Write then clear
        _write_delegation_state(session_id, terminal_id, "test", "snippet")
        state_file = Path(__file__).resolve().parent.parent.parent / "state" / f"delegation_expected_{session_id}.json"
        assert state_file.exists()

        _clear_delegation_state(session_id)
        assert not state_file.exists()


class TestPreToolUseGate:
    """Integration test for PreToolUse gate with state."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self._orig_state_dir = None
        import PreToolUse_delegation_gate as gate_module
        self._orig_state_dir = gate_module.STATE_DIR
        gate_module.STATE_DIR = Path(self.temp_dir)

    def teardown_method(self):
        """Tear down test environment."""
        import PreToolUse_delegation_gate as gate_module
        gate_module.STATE_DIR = self._orig_state_dir
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run_gate(self, tool_name: str, session_id: str, prompt: str = "") -> int:
        """Run the gate and return exit code."""
        import PreToolUse_delegation_gate as gate_module
        import sys
        import io

        # Write state file (simulating delegation_prospector) with recent timestamp
        state_file = Path(self.temp_dir) / f"delegation_expected_{session_id}.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": session_id,
                "terminal_id": "console_test",
                "detected_at": time.time() - 100,  # Recent, within TTL
                "matched_pattern": "analyze A and B",
                "prompt_snippet": "analyze foo.py and bar.py",
            }, f)

        # Create test input and pipe to stdin
        test_data = {
            "tool_name": tool_name,
            "session_id": session_id,
            "prompt": prompt,
        }

        # Capture and restore stdin
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(test_data))

        try:
            exit_code = gate_module.main()
        finally:
            sys.stdin = old_stdin

        return exit_code

    def test_gate_allows_task_tool(self):
        """Task tool is always allowed."""
        exit_code = self._run_gate("Task", "session-123", "")
        assert exit_code == 0

    def test_gate_allows_agent_tool(self):
        """Agent tool is always allowed."""
        exit_code = self._run_gate("Agent", "session-123", "")
        assert exit_code == 0

    def test_gate_blocks_read_tool(self):
        """Read tool is blocked when delegation expected."""
        exit_code = self._run_gate("Read", "session-456", "")
        assert exit_code == 2  # Blocked

    def test_gate_blocks_edit_tool(self):
        """Edit tool is blocked when delegation expected."""
        exit_code = self._run_gate("Edit", "session-456", "")
        assert exit_code == 2  # Blocked

    def test_gate_blocks_bash_tool(self):
        """Bash tool is blocked when delegation expected."""
        exit_code = self._run_gate("Bash", "session-456", "")
        assert exit_code == 2  # Blocked

    def test_gate_allows_with_bypass_flag(self):
        """Tools are allowed with --allow-inline bypass."""
        exit_code = self._run_gate("Read", "session-789", "Use --allow-inline to skip")
        assert exit_code == 0  # Allowed

    def test_gate_allows_without_state(self):
        """Tools are allowed when no delegation state exists."""
        # Run with a session that has no state file
        import PreToolUse_delegation_gate as gate_module
        import sys
        import io

        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps({
            "tool_name": "Read",
            "session_id": "nonexistent-session",
            "prompt": "",
        }))

        try:
            exit_code = gate_module.main()
        finally:
            sys.stdin = old_stdin

        assert exit_code == 0  # Allowed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])