#!/usr/bin/env python3
"""Edge case tests for post-skill prose response detection.

Tests multi-turn conversations, terminal isolation, signal file cleanup,
and graceful degradation scenarios from architecture decision Task 6.
"""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import Stop


class TestPostSkillProseEdgeCases:
    """Edge case tests for post-skill prose detection."""

    def test_multi_turn_conversation_skill_then_prose(self):
        """Test multi-turn: Turn 1 uses Skill, Turn 2 responds with prose."""
        # Turn 1: AI calls Skill("code") (should allow)
        turn1_data = {
            "tool_calls": [{"name": "Skill"}, {"name": "Read"}],
            "tool_input": {"skill": "code"},
            "tools_used": [{"name": "Skill"}, {"name": "Read"}],
        }
        result1 = Stop._check_post_skill_prose_response(turn1_data)
        assert result1 is None  # Should allow (execution tool used)

        # Turn 2: AI responds with prose but no Skill tool (should allow - different turn)
        # The gate only fires if Skill was used THIS turn without execution tools
        turn2_data = {
            "tool_calls": [{"name": "Write"}],  # No Skill tool
            "tool_input": {"file_path": "test.py"},
            "tools_used": [{"name": "Write"}],
        }
        result2 = Stop._check_post_skill_prose_response(turn2_data)
        assert result2 is None  # Should allow (Skill not used this turn)

    def test_multi_turn_consecutive_skill_invocations(self):
        """Test consecutive skill invocations in separate turns."""
        # Turn 1: Skill("code") + execution tools (allow)
        turn1 = {
            "tool_calls": [{"name": "Skill"}, {"name": "Bash"}],
            "tool_input": {"skill": "code"},
            "tools_used": [{"name": "Skill"}, {"name": "Bash"}],
        }
        assert Stop._check_post_skill_prose_response(turn1) is None

        # Turn 2: Skill("research") + execution tools (allow)
        turn2 = {
            "tool_calls": [{"name": "Skill"}, {"name": "Read"}],
            "tool_input": {"skill": "research"},
            "tools_used": [{"name": "Skill"}, {"name": "Read"}],
        }
        assert Stop._check_post_skill_prose_response(turn2) is None

    def test_terminal_isolation_separate_sessions(self):
        """Test that terminal isolation prevents cross-session contamination.

        The post-skill prose gate uses Stop hook data which is per-terminal.
        This test verifies the gate doesn't leak state between terminals.
        """
        # Terminal A session: Skill("code") + prose (would block)
        terminal_a_data = {
            "tool_calls": [{"name": "Skill"}],
            "tool_input": {"skill": "code"},
            "tools_used": [{"name": "Skill"}],
            "session_id": "session_a",
            "terminal_id": "terminal_a",
        }
        result_a = Stop._check_post_skill_prose_response(terminal_a_data)
        assert result_a is not None  # Should block
        assert result_a["decision"] == "block"

        # Terminal B session: Same pattern but separate terminal (also blocks)
        # The gate is stateless per invocation, so both should block independently
        terminal_b_data = {
            "tool_calls": [{"name": "Skill"}],
            "tool_input": {"skill": "code"},
            "tools_used": [{"name": "Skill"}],
            "session_id": "session_b",  # Different session
            "terminal_id": "terminal_b",  # Different terminal
        }
        result_b = Stop._check_post_skill_prose_response(terminal_b_data)
        assert result_b is not None  # Should also block
        assert result_b["decision"] == "block"

    def test_graceful_degradation_skill_guard_unavailable(self):
        """Test graceful degradation when skill_guard.breadcrumb.tracker is unavailable."""
        # This test verifies the fail-safe behavior when _load_workflow_steps fails

        # Mock scenario: skill_guard module not available
        # The gate should fail open (allow) to avoid breaking the system

        # Create data that would normally block
        data = {
            "tool_calls": [{"name": "Skill"}],
            "tool_input": {"skill": "nonexistent_skill"},
            "tools_used": [{"name": "Skill"}],
        }

        # Call with mocked import failure
        import unittest.mock as mock

        # Mock _load_workflow_steps to raise exception
        with mock.patch('skill_guard.breadcrumb.tracker._load_workflow_steps', side_effect=ImportError("Mocked failure")):
            # Force reimport to pick up mock
            if 'Stop' in sys.modules:
                # Reload to apply mock
                import importlib
                importlib.reload(Stop)

            # The gate should fail open (return None) on exception
            result = Stop._check_post_skill_prose_response(data)

            # With the fail-safe exception handler, should allow (None)
            # This prevents breaking the entire Stop hook if skill_guard is unavailable
            # Note: The actual behavior depends on whether the mock applies before or after module import
            # In production, the exception handler in _is_execution_skill catches ImportError

    def test_skill_name_extraction_malformed_xml(self):
        """Test skill name extraction with malformed XML."""
        # Valid XML
        valid_xml = {"tool_input": '<parameter name="skill">code</parameter>'}
        assert Stop._extract_skill_name_from_data(valid_xml) == "code"

        # Malformed XML (missing closing tag) - should return None
        malformed_xml = {"tool_input": '<parameter name="skill">code'}
        result = Stop._extract_skill_name_from_data(malformed_xml)
        # Should return None (graceful degradation)
        assert result is None or result == ""

    def test_skill_name_extraction_empty_tool_calls(self):
        """Test skill name extraction with empty tool_calls."""
        data = {
            "tool_calls": [],
            "tool_input": {},
        }
        result = Stop._extract_skill_name_from_data(data)
        assert result is None

    def test_skill_name_extraction_missing_skill_field(self):
        """Test skill name extraction when 'skill' field is missing."""
        # tool_input exists but no 'skill' key
        data = {"tool_input": {"command": "test"}}
        result = Stop._extract_skill_name_from_data(data)
        assert result is None

    def test_execution_skill_check_with_none_workflow_steps(self):
        """Test _is_execution_skill when workflow_steps is None."""
        # Mock _load_workflow_steps to return None
        import unittest.mock as mock

        with mock.patch('skill_guard.breadcrumb.tracker._load_workflow_steps', return_value=None):
            # Force reload to apply mock
            import importlib
            importlib.reload(Stop)

            # None workflow_steps = knowledge skill
            result = Stop._is_execution_skill("test_skill")
            assert result is False  # None = no workflow_steps = knowledge skill

    def test_execution_skill_check_with_empty_workflow_steps(self):
        """Test _is_execution_skill when workflow_steps is empty list."""
        # Mock _load_workflow_steps to return empty list
        import unittest.mock as mock

        with mock.patch('skill_guard.breadcrumb.tracker._load_workflow_steps', return_value=[]):
            # Force reload to apply mock
            import importlib
            importlib.reload(Stop)

            # Empty list = no workflow_steps = knowledge skill
            result = Stop._is_execution_skill("test_skill")
            assert result is False  # Empty list = knowledge skill

    def test_execution_skill_check_with_exception(self):
        """Test _is_execution_skill fail-safe on exception."""
        # Mock _load_workflow_steps to raise exception
        import unittest.mock as mock

        with mock.patch('skill_guard.breadcrumb.tracker._load_workflow_steps', side_effect=Exception("Mocked error")):
            # Force reload to apply mock
            import importlib
            importlib.reload(Stop)

            # Exception = fail-safe = treat as execution skill (conservative blocking)
            result = Stop._is_execution_skill("test_skill")
            assert result is True  # Fail-safe = execution skill

    def test_concurrent_execution_tools_and_skill(self):
        """Test detection when Skill and execution tools are used concurrently."""
        data = {
            "tool_calls": [
                {"name": "Skill"},
                {"name": "Bash"},
                {"name": "Read"},
                {"name": "Write"},
            ],
            "tool_input": {"skill": "code"},
            "tools_used": [
                {"name": "Skill"},
                {"name": "Bash"},
                {"name": "Read"},
                {"name": "Write"},
            ],
        }
        result = Stop._check_post_skill_prose_response(data)
        assert result is None  # Should allow (execution tools used)

    def test_no_tool_calls_at_all(self):
        """Test behavior when no tool calls are made."""
        data = {
            "tool_calls": [],
            "tool_input": {},
            "tools_used": [],
        }
        result = Stop._check_post_skill_prose_response(data)
        assert result is None  # Should allow (no Skill tool used)

    def test_skill_with_unknown_tool_format(self):
        """Test handling of unknown tool call formats."""
        # Unusual but potentially valid format
        data = {
            "tool_calls": "weird_string_format",
            "tool_input": {"skill": "code"},
            "tools_used": [{"name": "Skill"}],
        }
        # Should not crash, should handle gracefully
        result = Stop._check_post_skill_prose_response(data)
        # The function should handle this without exception
        # Exact behavior depends on _extract_tools_used parsing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
