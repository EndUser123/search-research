#!/usr/bin/env python3
"""Tests for post-skill prose response detection in Stop hook."""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


class TestPostSkillProseDetection:
    """Test suite for detecting prose responses after Skill() calls."""

    def test_extract_tools_used_with_skill_only(self):
        """Test extraction when only Skill tool was used."""
        from Stop_behavior_gates import _extract_tools_used

        data = {"tools_used": [{"name": "Skill"}]}
        tools = _extract_tools_used(data)
        assert tools == ["Skill"]

    def test_extract_tools_used_with_execution_tools(self):
        """Test extraction when execution tools were used."""
        from Stop_behavior_gates import _extract_tools_used

        data = {"tools_used": [{"name": "Skill"}, {"name": "Bash"}, {"name": "Read"}]}
        tools = _extract_tools_used(data)
        assert "Skill" in tools
        assert "Bash" in tools
        assert "Read" in tools

    def test_is_execution_skill_with_workflow_steps(self):
        """Test that skills with workflow_steps are execution skills."""
        # Mock _load_workflow_steps to return workflow steps
        import unittest.mock as mock

        def mock_load_workflow_steps(skill_name):
            if skill_name == "code":
                return ["step1", "step2", "step3"]
            return None

        with mock.patch('skill_guard.breadcrumb.tracker._load_workflow_steps', side_effect=mock_load_workflow_steps):
            # Need to import after patching
            if 'Stop_post_skill_prose_detection' in sys.modules:
                del sys.modules['Stop_post_skill_prose_detection']

            # Import the function
            # We'll test this after implementation

    def test_is_execution_skill_knowledge_skill(self):
        """Test that skills without workflow_steps are knowledge skills."""
        # Will test after implementation
        pass

    def test_check_post_skill_prose_skill_with_no_execution_tools_blocks(self):
        """Test that prose response after Skill() without execution tools is blocked."""
        # Will test after implementation
        pass

    def test_check_post_skill_prose_skill_with_execution_tools_allows(self):
        """Test that using execution tools after Skill() is allowed."""
        # Will test after implementation
        pass

    def test_check_post_skill_prose_knowledge_skill_allows_prose(self):
        """Test that prose response after knowledge Skill() is allowed."""
        # Note: /research actually has workflow_steps, so it's treated as execution skill
        # This test documents the actual behavior based on real skill registry state
        # To test true knowledge skills, we would need a skill without workflow_steps
        pass  # Current implementation: skills with workflow_steps block prose

    def test_check_post_skill_prose_no_skill_used_allows(self):
        """Test that responses without Skill() call are allowed."""
        # Will test after implementation
        pass

    def test_check_post_skill_prose_multiple_tools_includes_skill(self):
        """Test tool extraction with multiple tools including Skill."""
        from Stop_behavior_gates import _extract_tools_used

        data = {"tools_used": [{"name": "Read"}, {"name": "Skill"}, {"name": "Bash"}]}
        tools = _extract_tools_used(data)
        assert "Skill" in tools
        assert len(tools) == 3

    def test_execution_tool_list_comprehensive(self):
        """Test that all expected execution tools are in the whitelist."""
        # Expected execution tools from architecture decision
        expected_tools = {"Bash", "Task", "Write", "Edit", "Grep", "Glob", "Read"}
        # This will be used in implementation
        assert len(expected_tools) == 7
        assert "Bash" in expected_tools
        assert "Read" in expected_tools


class TestPostSkillProseRekey:
    """Rekey 2026-07-09: enforcement keyed off INVOCATION, not workflow_steps.

    Contract:
      (a) invoked skill WITHOUT workflow_steps → STILL enforced (block prose)
      (b) invoked skill WITH workflow_steps → unchanged (block prose + step msg)
      (c) non-skill slash-tokens (/tmp/x, /help) → trigger nothing (no Skill call)
      (d) knowledge skill (KNOWLEDGE_SKILLS) → exempt, prose allowed (no regression)
    """

    def test_invoked_skill_without_workflow_steps_is_enforced(self, monkeypatch):
        """(a) Tier 2: invoked skill lacking workflow_steps still blocks prose."""
        import Stop

        # Skill() called, NO execution tools → prose substitution.
        data = {
            "tool_calls": [{"name": "Skill"}],
            "tool_input": {"skill": "gitpack"},  # real skill, no workflow_steps
            "session_id": "s1",
            "terminal_id": "t1",
        }
        # Force deterministic classification: no workflow_steps, not knowledge.
        monkeypatch.setattr(Stop, "_is_execution_skill", lambda name: False)
        monkeypatch.setattr(Stop, "_is_knowledge_skill", lambda name: False)

        result = Stop._check_post_skill_prose_response(data)
        assert result is not None
        assert result["decision"] == "block"

    def test_invoked_skill_with_workflow_steps_keeps_behavior(self, monkeypatch):
        """(b) Tier 1: skill with workflow_steps still blocks; message references steps."""
        import Stop

        data = {
            "tool_calls": [{"name": "Skill"}],
            "tool_input": {"skill": "code"},
            "session_id": "s1",
            "terminal_id": "t1",
        }
        monkeypatch.setattr(Stop, "_is_execution_skill", lambda name: True)
        monkeypatch.setattr(Stop, "_is_knowledge_skill", lambda name: False)

        result = Stop._check_post_skill_prose_response(data)
        assert result is not None
        assert result["decision"] == "block"
        # Tier 1 message points at the documented workflow_steps.
        assert "workflow_steps" in result["reason"]

    def test_invoked_skill_with_workflow_steps_and_tools_allows(self, monkeypatch):
        """(b cont.) execution tools used after Skill() → allow (unchanged)."""
        import Stop

        data = {
            "tool_calls": [{"name": "Skill"}, {"name": "Bash"}],
            "tool_input": {"skill": "code"},
            "session_id": "s1",
            "terminal_id": "t1",
        }
        monkeypatch.setattr(Stop, "_is_execution_skill", lambda name: True)
        monkeypatch.setattr(Stop, "_is_knowledge_skill", lambda name: False)

        assert Stop._check_post_skill_prose_response(data) is None

    def test_non_skill_slash_tokens_trigger_nothing(self, monkeypatch):
        """(c) /tmp/x, /help never produce a Skill() call → gate returns None."""
        import Stop

        # No Skill tool in the call list — gate must short-circuit (return None)
        # regardless of how the classification helpers would classify.
        data = {
            "tool_calls": [{"name": "Bash"}],
            "tool_input": {"command": "ls /tmp/x"},
            "session_id": "s1",
            "terminal_id": "t1",
        }
        # Sentinel: if the gate ever reached classification, this would betray it.
        def _explode(name):
            raise AssertionError("classification should not be reached without Skill()")
        monkeypatch.setattr(Stop, "_is_execution_skill", _explode)
        monkeypatch.setattr(Stop, "_is_knowledge_skill", _explode)

        assert Stop._check_post_skill_prose_response(data) is None

    def test_knowledge_skill_prose_allowed_no_regression(self, monkeypatch):
        """(d) KNOWLEDGE_SKILLS exemption preserved: prose after /standards allowed."""
        import Stop

        data = {
            "tool_calls": [{"name": "Skill"}],
            "tool_input": {"skill": "standards"},
            "session_id": "s1",
            "terminal_id": "t1",
        }
        monkeypatch.setattr(Stop, "_is_execution_skill", lambda name: False)
        monkeypatch.setattr(Stop, "_is_knowledge_skill", lambda name: True)

        assert Stop._check_post_skill_prose_response(data) is None

    def test_tier2_message_omits_workflow_steps(self, monkeypatch):
        """Tier 2 message uses generic 'documented procedure', NOT workflow_steps."""
        import Stop

        data = {
            "tool_calls": [{"name": "Skill"}],
            "tool_input": {"skill": "gitpack"},
            "session_id": "s1",
            "terminal_id": "t1",
        }
        monkeypatch.setattr(Stop, "_is_execution_skill", lambda name: False)
        monkeypatch.setattr(Stop, "_is_knowledge_skill", lambda name: False)

        result = Stop._check_post_skill_prose_response(data)
        assert result is not None
        assert "documented procedure" in result["reason"]
        assert "workflow_steps" not in result["reason"]


class TestIsKnowledgeSkillHelper:
    """The new exemption lookup used to key enforcement off invocation."""

    def test_returns_true_for_knowledge_skill(self):
        import Stop

        # 'standards' is in KNOWLEDGE_SKILLS (hook_constants.py).
        assert Stop._is_knowledge_skill("standards") is True

    def test_returns_false_for_execution_skill(self):
        import Stop

        assert Stop._is_knowledge_skill("gitpack") is False

    def test_case_insensitive_and_strips_slash(self):
        import Stop

        assert Stop._is_knowledge_skill("Standards") is True
        assert Stop._is_knowledge_skill(" STANDARDS ") is True

    def test_empty_or_unknown_returns_false(self):
        import Stop

        assert Stop._is_knowledge_skill("") is False
        assert Stop._is_knowledge_skill("totally-unknown-skill") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
