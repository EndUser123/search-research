#!/usr/bin/env python3
"""Tests for pending_action_guard session mismatch behavior in UserPromptSubmit_router.py.

Feature: UserPromptSubmit_router.py should only inject for matching session.

Test case: When guard state exists but for different session_id, return None.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPendingActionGuardSessionMismatch:
    """Tests for pending_action_guard session mismatch behavior.

    CHARACTERIZATION TESTS: These tests CAPTURE CURRENT BEHAVIOR before refactoring.
    Run with: pytest P:/.claude/hooks/tests/test_pending_action_guard_session_mismatch.py -v
    """

    def test_block_context_injection_session_mismatch_terminal_id(
        self, tmp_path, monkeypatch
    ):
        """
        Test that block_context_injection returns None when terminal_id mismatch.

        Given: Guard state exists with scope_key="terminal_A|session_123"
        When: Data has terminal_id="terminal_B"
        Then: Function returns None (no injection)

        CHARACTERIZATION: Captures current behavior before refactoring.
        """
        # Arrange
        from UserPromptSubmit_router import run_pending_action_guard

        # Create mock state directory and file
        state_dir = tmp_path / ".state"
        state_dir.mkdir()

        # Create pending action state with terminal_A|session_123 scope
        guard_state = {
            "scope_key": "terminal_A|session_123",
            "pending_action": "value_check_assessment",
            "prohibited_actions": ["implement", "write", "create"],
            "timestamp": "2026-02-09T12:00:00+00:00",
            "expires_after_seconds": 300,
        }
        state_file = state_dir / "pending_action_context.json"
        state_file.write_text(json.dumps(guard_state), encoding="utf-8")

        # Enable the guard
        monkeypatch.setenv("PENDING_ACTION_GUARD_ENABLED", "true")

        # Mock HOOKS_DIR to use tmp_path
        with patch("UserPromptSubmit_router.HOOKS_DIR", tmp_path):
            # Create data with different terminal_id
            data = {
                "terminal_id": "terminal_B",  # Different from scope_key
                "session_id": "session_123",
            }
            prompt = "proceed"

            # Act
            result = run_pending_action_guard(data, prompt)

            # Assert - Characterization: Current behavior
            # Expected (after implementation): result should be None
            # Current behavior: Returns None (but for wrong reason - scope check not implemented)
            # The function currently returns None because it doesn't check scope_key at all
            assert result is None, (
                f"Expected None when terminal_id mismatch, got: {result}"
            )
            assert False, "TODO: Implement scope_key checking in run_pending_action_guard"

    def test_block_context_injection_session_mismatch_session_id(
        self, tmp_path, monkeypatch
    ):
        """
        Test that block_context_injection returns None when session_id mismatch.

        Given: Guard state exists with scope_key="terminal_A|session_123"
        When: Data has session_id="session_456"
        Then: Function returns None (no injection)

        CHARACTERIZATION: Captures current behavior before refactoring.
        """
        # Arrange
        from UserPromptSubmit_router import run_pending_action_guard

        # Create mock state directory and file
        state_dir = tmp_path / ".state"
        state_dir.mkdir()

        # Create pending action state with terminal_A|session_123 scope
        guard_state = {
            "scope_key": "terminal_A|session_123",
            "pending_action": "value_check_assessment",
            "prohibited_actions": ["implement", "write", "create"],
            "timestamp": "2026-02-09T12:00:00+00:00",
            "expires_after_seconds": 300,
        }
        state_file = state_dir / "pending_action_context.json"
        state_file.write_text(json.dumps(guard_state), encoding="utf-8")

        # Enable the guard
        monkeypatch.setenv("PENDING_ACTION_GUARD_ENABLED", "true")

        # Mock HOOKS_DIR to use tmp_path
        with patch("UserPromptSubmit_router.HOOKS_DIR", tmp_path):
            # Create data with different session_id
            data = {
                "terminal_id": "terminal_A",
                "session_id": "session_456",  # Different from scope_key
            }
            prompt = "proceed"

            # Act
            result = run_pending_action_guard(data, prompt)

            # Assert - Characterization: Current behavior
            # Expected (after implementation): result should be None
            # Current behavior: Returns None (but for wrong reason - scope check not implemented)
            assert result is None, (
                f"Expected None when session_id mismatch, got: {result}"
            )
            assert False, "TODO: Implement scope_key checking in run_pending_action_guard"

    def test_block_context_injection_matching_session_injects(
        self, tmp_path, monkeypatch
    ):
        """
        Test that block_context_injection injects when session matches.

        Given: Guard state exists with scope_key="terminal_A|session_123"
        When: Data has terminal_id="terminal_A" AND session_id="session_123"
        Then: Function returns injection context

        CHARACTERIZATION: Captures current behavior before refactoring.
        """
        # Arrange
        from UserPromptSubmit_router import run_pending_action_guard

        # Create mock state directory and file
        state_dir = tmp_path / ".state"
        state_dir.mkdir()

        # Create pending action state with terminal_A|session_123 scope
        guard_state = {
            "scope_key": "terminal_A|session_123",
            "pending_action": "value_check_assessment",
            "prohibited_actions": ["implement", "write", "create"],
            "timestamp": "2026-02-09T12:00:00+00:00",
            "expires_after_seconds": 300,
        }
        state_file = state_dir / "pending_action_context.json"
        state_file.write_text(json.dumps(guard_state), encoding="utf-8")

        # Enable the guard
        monkeypatch.setenv("PENDING_ACTION_GUARD_ENABLED", "true")

        # Mock HOOKS_DIR to use tmp_path
        with patch("UserPromptSubmit_router.HOOKS_DIR", tmp_path):
            # Create data with matching terminal_id and session_id
            data = {
                "terminal_id": "terminal_A",
                "session_id": "session_123",
            }
            prompt = "proceed"

            # Act
            result = run_pending_action_guard(data, prompt)

            # Assert - Characterization: Current behavior
            # Expected (after implementation): result should have injection
            # Current behavior: Returns None (scope check not implemented)
            assert result is None, (
                f"CHARACTERIZATION: Current behavior returned {result}. "
                "After implementation, should return injection context when session matches."
            )
            assert False, "TODO: Implement scope_key checking and return injection when session matches"
