#!/usr/bin/env python3
"""
Tests for hook_feedback_summary module
"""

# Add __lib to path for imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))

import hook_feedback_summary


class TestFormatBlockingSummary:
    """Tests for format_blocking_summary() function."""

    def test_complete_block_result(self):
        """Test formatting with complete block_result dict."""
        block_result = {
            "blocking_hook": "authorization_gate",
            "reason": "Destructive command requires explicit authorization",
            "decision": "deny"
        }
        result = hook_feedback_summary.format_blocking_summary(block_result)

        assert "authorization_gate" in result
        assert "Destructive command requires explicit authorization" in result
        assert "BLOCKED" in result
        assert "💡" in result  # Guidance icon

    def test_missing_blocking_hook(self):
        """Test graceful handling when blocking_hook field is missing."""
        block_result = {
            "reason": "Some error occurred"
        }
        result = hook_feedback_summary.format_blocking_summary(block_result)

        assert "Unknown hook" in result
        assert "Some error occurred" in result

    def test_missing_reason(self):
        """Test graceful handling when reason field is missing."""
        block_result = {
            "blocking_hook": "tdd_gate"
        }
        result = hook_feedback_summary.format_blocking_summary(block_result)

        assert "tdd_gate" in result
        assert "blocked by hook policy" in result

    def test_empty_block_result(self):
        """Test graceful handling of completely empty dict."""
        block_result = {}
        result = hook_feedback_summary.format_blocking_summary(block_result)

        assert "Unknown hook" in result
        assert "blocked by hook policy" in result

    def test_authorization_gate_guidance(self):
        """Test specific guidance for authorization_gate."""
        block_result = {
            "blocking_hook": "authorization_gate",
            "reason": "Pattern: rm -rf"
        }
        result = hook_feedback_summary.format_blocking_summary(block_result)

        assert "proceed" in result.lower()
        assert "do it" in result.lower()

    def test_tdd_gate_guidance(self):
        """Test specific guidance for tdd_gate."""
        block_result = {
            "blocking_hook": "tdd_gate",
            "reason": "No tests found"
        }
        result = hook_feedback_summary.format_blocking_summary(block_result)

        assert "RED" in result
        assert "GREEN" in result
        assert "tests first" in result.lower()

    def test_planning_mode_guidance(self):
        """Test specific guidance for planning_mode_gate."""
        block_result = {
            "blocking_hook": "planning_mode_gate",
            "reason": "Complex change requires planning"
        }
        result = hook_feedback_summary.format_blocking_summary(block_result)

        assert "plan" in result.lower()
        assert "architecture" in result.lower()

    def test_unknown_hook_guidance(self):
        """Test default guidance for unknown hooks."""
        block_result = {
            "blocking_hook": "some_unknown_hook",
            "reason": "Blocked"
        }
        result = hook_feedback_summary.format_blocking_summary(block_result)

        # Should have default guidance
        assert "Review the hook requirements" in result

    def test_formatting_structure(self):
        """Test that output has proper visual structure."""
        block_result = {
            "blocking_hook": "authorization_gate",
            "reason": "Test"
        }
        result = hook_feedback_summary.format_blocking_summary(block_result)

        # Check for box drawing characters
        assert "╌" in result
        assert "╞" in result
        assert "│" in result
        assert "╘" in result
        assert "⛔" in result

    def test_multiple_block_results(self):
        """Test formatting multiple different block results."""
        hooks = ["authorization_gate", "tdd_gate", "directory_policy"]
        for hook in hooks:
            block_result = {
                "blocking_hook": hook,
                "reason": f"Blocked by {hook}"
            }
            result = hook_feedback_summary.format_blocking_summary(block_result)

            assert hook in result
            assert len(result) > 0
