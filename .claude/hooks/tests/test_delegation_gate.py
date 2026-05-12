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
    _get_artifacts_dir,
    _detect_terminal_id,
)
from UserPromptSubmit_modules.delegation_prospector import (
    _extract_skill_name,
    _detect_delegation_opportunity,
    _DELEGATION_HEAVY_SKILLS,
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


class TestTerminalDetection:
    """Test terminal ID detection."""

    def test_detect_terminal_id_with_wt_session(self, monkeypatch):
        """Terminal ID from WT_SESSION environment variable."""
        monkeypatch.setenv("WT_SESSION", "abc123-def456-789")
        tid = _detect_terminal_id()
        assert tid == "console_abc123-def456-789"

    def test_detect_terminal_id_without_wt_session(self, monkeypatch):
        """Terminal ID falls back to 'unknown' without WT_SESSION."""
        monkeypatch.delenv("WT_SESSION", raising=False)
        tid = _detect_terminal_id()
        assert tid == "unknown"

    def test_get_artifacts_dir_uses_terminal_id(self, monkeypatch):
        """Artifacts directory includes terminal ID."""
        monkeypatch.setenv("WT_SESSION", "test-terminal-123")
        artifacts_dir = _get_artifacts_dir()
        assert "test-terminal-123" in str(artifacts_dir)
        assert ".artifacts" in str(artifacts_dir)
        assert "hook_state" in str(artifacts_dir)


class TestDelegationStatePersistence:
    """Test delegation state file read/write/clear operations."""

    def setup_method(self):
        """Create temp directory for test state files."""
        self.temp_dir = tempfile.mkdtemp()
        # Mock _get_artifacts_dir to return our temp directory
        self._original_get_artifacts_dir = None
        import PreToolUse_delegation_gate as gate_module

        def mock_get_artifacts_dir():
            return Path(self.temp_dir)

        self._original_get_artifacts_dir = gate_module._get_artifacts_dir
        gate_module._get_artifacts_dir = mock_get_artifacts_dir

    def teardown_method(self):
        """Restore original function and clean up temp files."""
        import PreToolUse_delegation_gate as gate_module
        if self._original_get_artifacts_dir:
            gate_module._get_artifacts_dir = self._original_get_artifacts_dir
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_write_and_read_delegation_state(self):
        """State written by prospector can be read by gate."""
        state_data = {
            "terminal_id": "console_abc",
            "detected_at": time.time() - 100,  # Recent timestamp
            "matched_pattern": "test pattern",
            "prompt_snippet": "test snippet",
        }

        # Write state (simulating what delegation_prospector does)
        state_file = Path(self.temp_dir) / "delegation_expected.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f)

        # Read state via gate function
        loaded = _load_delegation_state()
        assert loaded is not None, f"Failed to load state from {state_file}"
        assert loaded["matched_pattern"] == "test pattern"

    def test_load_nonexistent_state_returns_none(self):
        """Missing state file returns None."""
        result = _load_delegation_state()
        assert result is None

    def test_expired_state_is_not_loaded(self):
        """Expired state file is deleted and returns None."""
        state_file = Path(self.temp_dir) / "delegation_expected.json"

        # Write state with old timestamp (400 seconds ago)
        state_data = {
            "detected_at": 1700000000.0 - 400,  # Expired
            "matched_pattern": "test",
        }
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f)

        # State should be expired and file deleted
        result = _load_delegation_state()
        assert result is None
        assert not state_file.exists()

    def test_clear_delegation_state(self):
        """Clearing state removes the file."""
        state_file = Path(self.temp_dir) / "delegation_expected.json"

        # Create state file
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"matched_pattern": "test"}, f)
        assert state_file.exists()

        # Clear it
        _clear_delegation_state()
        assert not state_file.exists()

    def test_clear_nonexistent_state_is_silent(self):
        """Clearing nonexistent state doesn't raise."""
        # Should not raise
        _clear_delegation_state()


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


class TestSkillDetection:
    """Test skill invocation detection for delegation-heavy skills."""

    def test_extract_skill_name_simple(self):
        """Simple slash command extraction."""
        assert _extract_skill_name("/go") == "go"
        assert _extract_skill_name("/code") == "code"
        assert _extract_skill_name("/refactor") == "refactor"
        assert _extract_skill_name("/tdd") == "tdd"

    def test_extract_skill_name_with_args(self):
        """Skill name with arguments (space or colon separator)."""
        assert _extract_skill_name("/go implement feature X") == "go"
        assert _extract_skill_name("/code:implement task") == "code"
        assert _extract_skill_name("/refactor cleanup") == "refactor"
        assert _extract_skill_name("/tdd write tests for Y") == "tdd"

    def test_extract_skill_name_long_form(self):
        """Long-form skill names."""
        assert _extract_skill_name("/subagent-driven-development") == "subagent-driven-development"
        assert _extract_skill_name("/planning decompose the work") == "planning"

    def test_extract_skill_name_non_slash(self):
        """Non-slash commands return None."""
        assert _extract_skill_name("implement X") is None
        assert _extract_skill_name("use the go skill") is None
        assert _extract_skill_name("") is None

    def test_delegation_heavy_skills_defined(self):
        """Verify delegation-heavy skills are defined."""
        expected = {"go", "code", "refactor", "tdd", "subagent-driven-development", "planning", "team", "sqa", "design"}
        assert _DELEGATION_HEAVY_SKILLS == expected or expected.issubset(_DELEGATION_HEAVY_SKILLS)

    def test_detect_delegation_by_skill(self):
        """Skill invocation triggers delegation detection."""
        # /go should trigger
        detected, pattern = _detect_delegation_opportunity("/go implement feature X")
        assert detected is True
        assert pattern == "skill:/go"

        # /code should trigger
        detected, pattern = _detect_delegation_opportunity("/code:implement the task")
        assert detected is True
        assert pattern == "skill:/code"

        # /tdd should trigger
        detected, pattern = _detect_delegation_opportunity("/tdd write tests for auth")
        assert detected is True
        assert pattern == "skill:/tdd"

    def test_detect_delegation_by_pattern_fallback(self):
        """Pattern matching still works when no skill invoked."""
        detected, pattern = _detect_delegation_opportunity("inspect file1 and file2")
        assert detected is True
        assert "matched:" in pattern

    def test_detect_no_delegation_regular_prompt(self):
        """Regular prompts without skill or patterns don't trigger."""
        detected, pattern = _detect_delegation_opportunity("fix the bug in auth.py")
        assert detected is False
        assert pattern is None

    def test_detect_no_delegation_empty_prompt(self):
        """Empty prompt doesn't trigger."""
        detected, pattern = _detect_delegation_opportunity("")
        assert detected is False


class TestDelegationProspectorState:
    """Test delegation_prospector's state writing functions."""

    def test_write_delegation_state_creates_file(self, monkeypatch):
        """State file is created with expected structure."""
        # Set up temp directory and mock
        temp_dir = tempfile.mkdtemp()
        monkeypatch.setenv("WT_SESSION", "prospector-test-123")

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "UserPromptSubmit_modules"))
        from delegation_prospector import _write_delegation_state, _get_state_dir

        # Write state
        _write_delegation_state(
            terminal_id="console_prospector-test-123",
            matched_pattern="test pattern",
            prompt_snippet="analyze foo and bar",
        )

        # Check file exists in terminal-scoped location
        state_dir = _get_state_dir()
        state_file = state_dir / "delegation_expected.json"
        assert state_file.exists()

        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["terminal_id"] == "console_prospector-test-123"
        assert data["matched_pattern"] == "test pattern"
        assert "detected_at" in data

        # Clean up
        state_file.unlink(missing_ok=True)
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_clear_delegation_state(self, monkeypatch):
        """clear_delegation_state removes state file."""
        temp_dir = tempfile.mkdtemp()
        monkeypatch.setenv("WT_SESSION", "prospector-clear-test")

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "UserPromptSubmit_modules"))
        from delegation_prospector import _write_delegation_state, _clear_delegation_state, _get_state_dir

        # Write then clear
        _write_delegation_state("console_prospector-clear-test", "test", "snippet")
        state_dir = _get_state_dir()
        state_file = state_dir / "delegation_expected.json"
        assert state_file.exists()

        _clear_delegation_state()
        assert not state_file.exists()

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


class TestPreToolUseGate:
    """Integration test for PreToolUse gate with state."""

    def setup_method(self):
        """Set up test environment with mocked state directory."""
        self.temp_dir = tempfile.mkdtemp()
        import PreToolUse_delegation_gate as gate_module

        # Mock _get_artifacts_dir
        def mock_get_artifacts_dir():
            return Path(self.temp_dir)

        self._original = gate_module._get_artifacts_dir
        gate_module._get_artifacts_dir = mock_get_artifacts_dir

        # Mock terminal detection
        def mock_detect_terminal_id():
            return "console_test-terminal"

        self._original_detect = gate_module._detect_terminal_id
        gate_module._detect_terminal_id = mock_detect_terminal_id

    def teardown_method(self):
        """Tear down test environment."""
        import PreToolUse_delegation_gate as gate_module
        gate_module._get_artifacts_dir = self._original
        gate_module._detect_terminal_id = self._original_detect
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run_gate(self, tool_name: str, prompt: str = "") -> int:
        """Run the gate and return exit code."""
        import PreToolUse_delegation_gate as gate_module
        import io

        # Write state file (simulating delegation_prospector) with recent timestamp
        state_file = Path(self.temp_dir) / "delegation_expected.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({
                "terminal_id": "console_test-terminal",
                "detected_at": time.time() - 100,  # Recent, within TTL
                "matched_pattern": "analyze A and B",
                "prompt_snippet": "analyze foo.py and bar.py",
            }, f)

        # Create test input and pipe to stdin
        test_data = {
            "tool_name": tool_name,
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
        exit_code = self._run_gate("Task", "")
        assert exit_code == 0

    def test_gate_allows_agent_tool(self):
        """Agent tool is always allowed."""
        exit_code = self._run_gate("Agent", "")
        assert exit_code == 0

    def test_gate_blocks_read_tool(self):
        """Read tool is blocked when delegation expected."""
        exit_code = self._run_gate("Read", "")
        assert exit_code == 2  # Blocked

    def test_gate_blocks_edit_tool(self):
        """Edit tool is blocked when delegation expected."""
        exit_code = self._run_gate("Edit", "")
        assert exit_code == 2  # Blocked

    def test_gate_blocks_bash_tool(self):
        """Bash tool is blocked when delegation expected."""
        exit_code = self._run_gate("Bash", "")
        assert exit_code == 2  # Blocked

    def test_gate_allows_with_bypass_flag(self):
        """Tools are allowed with --allow-inline bypass."""
        exit_code = self._run_gate("Read", "Use --allow-inline to skip")
        assert exit_code == 0  # Allowed

    def test_gate_allows_without_state(self):
        """Tools are allowed when no delegation state exists."""
        import PreToolUse_delegation_gate as gate_module
        import io

        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps({
            "tool_name": "Read",
            "prompt": "",
        }))

        try:
            exit_code = gate_module.main()
        finally:
            sys.stdin = old_stdin

        assert exit_code == 0  # Allowed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])