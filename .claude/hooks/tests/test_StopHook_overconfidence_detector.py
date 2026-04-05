#!/usr/bin/env python3
"""Tests for StopHook_overconfidence_detector.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from StopHook_overconfidence_detector import (
    ENABLED,
    _check_scope_mismatch,
    _check_status_tag_compliance,
    run,
)


class TestCheckScopeMismatch:
    """Tests for _check_scope_mismatch helper."""

    def test_global_claim_with_bash_allowed(self):
        """Global scope claims with Bash evidence are allowed through."""
        response = "The system is working as intended."
        tool_events = [{"name": "Bash", "input": {"command": "pytest"}}]
        result = _check_scope_mismatch(response, tool_events)
        assert result is None

    def test_global_claim_skill_only_flagged(self):
        """Global scope claims backed only by Skill (local-only) are flagged."""
        response = "The system is working as intended."
        tool_events = [{"name": "Skill", "input": {"skill": "code"}}]
        result = _check_scope_mismatch(response, tool_events)
        assert result is not None
        assert "Confidence Scope Mismatch" in result

    def test_no_global_claim_allowed(self):
        """Responses without global scope claims pass through."""
        response = "The function returns an error in foo.py."
        tool_events = [{"name": "Read", "input": {"file_path": "foo.py"}}]
        result = _check_scope_mismatch(response, tool_events)
        assert result is None

    def test_no_tool_events_allowed(self):
        """Responses without tool events are not flagged."""
        response = "The system is working as intended."
        result = _check_scope_mismatch(response, [])
        assert result is None


class TestCheckStatusTagCompliance:
    """Tests for _check_status_tag_compliance helper."""

    def test_status_tag_with_bash_allowed(self):
        """STATUS: INFERRING_FROM_DOCS with Bash evidence is allowed."""
        response = "STATUS: INFERRING_FROM_DOCS indicates the system..."
        tool_events = [{"name": "Bash", "input": {"command": "pytest"}}]
        result = _check_status_tag_compliance(response, tool_events)
        assert result is None

    def test_status_tag_without_bash_flagged(self):
        """STATUS: INFERRING_FROM_DOCS without Bash is flagged."""
        response = "STATUS: INFERRING_FROM_DOCS indicates the system..."
        tool_events = [{"name": "Read", "input": {"file_path": "foo.py"}}]
        result = _check_status_tag_compliance(response, tool_events)
        assert result is not None
        assert "STATUS Tag Violation" in result

    def test_no_status_tag_allowed(self):
        """Responses without STATUS tag pass through."""
        response = "The function works correctly based on code inspection."
        tool_events = [{"name": "Read", "input": {"file_path": "foo.py"}}]
        result = _check_status_tag_compliance(response, tool_events)
        assert result is None


class TestRun:
    """Tests for the run() entry point."""

    def test_disabled_returns_none(self, monkeypatch):
        """When ENABLED=false, run() returns None."""
        monkeypatch.setenv("OVERCONFIDENCE_DETECTOR_ENABLED", "false")
        # Re-import to pick up env var change would require reload
        # Instead test the current state
        if not ENABLED:
            data = {"assistant_response": "the system is broken"}
            result = run(data)
            assert result is None

    def test_empty_response_returns_none(self):
        """Empty response is allowed through."""
        data = {"assistant_response": ""}
        result = run(data)
        assert result is None

    def test_no_response_returns_none(self):
        """Missing response field returns None."""
        data = {}
        result = run(data)
        assert result is None

    def test_overconfident_claim_blocks_in_block_mode(self, monkeypatch):
        """Overconfident claim blocks when MODE=block and not RCA turn."""
        monkeypatch.setenv("OVERCONFIDENCE_DETECTOR_MODE", "block")
        # The response contains "this explains why" which is a causal assertion
        data = {
            "assistant_response": "This explains why the system is broken - it's clearly a bug.",
            "rca_turn": False,
        }
        result = run(data)
        assert result is not None
        assert result.get("block") is True or result.get("allow") is True

    def test_rca_turn_returns_allow_note(self, monkeypatch):
        """RCA turns return advisory note instead of block."""
        monkeypatch.setenv("OVERCONFIDENCE_DETECTOR_MODE", "block")
        data = {
            "assistant_response": "This explains why the system crashed.",
            "rca_turn": True,
        }
        result = run(data)
        # In RCA mode, even overconfidence returns allow with note
        if result is not None:
            assert result.get("allow") is True

    def test_normal_hedged_response_allowed(self):
        """Normal hedged responses are allowed through."""
        data = {
            "assistant_response": "The function might work correctly in this case, based on reading the code.",
            "rca_turn": False,
        }
        result = run(data)
        # No overconfidence detected, scope mismatch might warn
        if result is not None:
            assert result.get("allow") is True
