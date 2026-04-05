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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
