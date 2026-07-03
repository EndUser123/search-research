#!/usr/bin/env python3
"""Integration tests for post-skill prose response detection using real skills."""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import Stop  # Import once at module level


class TestPostSkillProseIntegration:
    """Integration tests using real skill data."""

    def test_code_skill_is_execution_skill(self):
        """Verify /code is detected as an execution skill."""
        # /code has 13 workflow_steps, should be execution skill
        assert Stop._is_execution_skill("code") is True

    def test_research_skill_is_execution_skill(self):
        """Verify /research is detected as an execution skill."""
        # /research has 7 workflow_steps, should be execution skill
        assert Stop._is_execution_skill("research") is True

    def test_arch_skill_is_execution_skill(self):
        """Verify /arch is detected as an execution skill."""
        # /arch has workflow_steps, should be execution skill
        assert Stop._is_execution_skill("arch") is True

    def test_nonexistent_skill_no_workflow_steps(self):
        """Verify non-existent skills return no workflow_steps (treated as knowledge)."""
        # Non-existent skills return empty list from _load_workflow_steps
        # Empty list = no workflow_steps = knowledge skill = allow prose
        # This is acceptable behavior - better to allow unknown skills than block them
        assert Stop._is_execution_skill("nonexistent_skill_xyz") is False

    def test_code_with_prose_response_blocked(self):
        """Integration test: /code invoked but AI responds with prose instead of tools."""
        # Simulate Stop hook input after AI called Skill("code") but responded with prose
        data = {
            "tool_calls": [{"name": "Skill"}],
            "tool_input": {"skill": "code"},
            "tools_used": [{"name": "Skill"}],  # Only Skill, no execution tools
        }

        result = Stop._check_post_skill_prose_response(data)

        # Should block because /code is execution skill but no execution tools used
        assert result is not None
        assert result["decision"] == "block"
        assert "E_POST_SKILL_PROSE_RESPONSE" in result["reason"]
        assert "WORKFLOW EXECUTION REQUIRED" in result["reason"]

    def test_code_with_bash_tool_allowed(self):
        """Integration test: /code invoked and AI uses Bash tool (correct behavior)."""
        # Simulate Stop hook input after AI called Skill("code") and used Bash
        data = {
            "tool_calls": [{"name": "Skill"}, {"name": "Bash"}],
            "tool_input": {"skill": "code"},
            "tools_used": [{"name": "Skill"}, {"name": "Bash"}],  # Skill + execution tool
        }

        result = Stop._check_post_skill_prose_response(data)

        # Should allow because execution tool (Bash) was used
        assert result is None

    def test_code_with_read_tool_allowed(self):
        """Integration test: /code invoked and AI uses Read tool (correct behavior)."""
        # Simulate Stop hook input after AI called Skill("code") and used Read
        data = {
            "tool_calls": [{"name": "Skill"}, {"name": "Read"}],
            "tool_input": {"skill": "code"},
            "tools_used": [{"name": "Skill"}, {"name": "Read"}],  # Skill + execution tool
        }

        result = Stop._check_post_skill_prose_response(data)

        # Should allow because execution tool (Read) was used
        assert result is None

    def test_research_with_prose_response_blocked(self):
        """Integration test: /research invoked but AI responds with prose."""
        # Simulate Stop hook input after AI called Skill("research") but responded with prose
        data = {
            "tool_calls": [{"name": "Skill"}],
            "tool_input": {"skill": "research"},
            "tools_used": [{"name": "Skill"}],  # Only Skill, no execution tools
        }

        result = Stop._check_post_skill_prose_response(data)

        # Should block because /research is execution skill but no execution tools used
        assert result is not None
        assert result["decision"] == "block"
        assert "E_POST_SKILL_PROSE_RESPONSE" in result["reason"]

    def test_research_with_web_search_blocks(self):
        """Integration test: /research invoked with WebSearch (blocks because WebSearch not in execution whitelist)."""
        # Note: WebSearch is NOT in the execution tool whitelist (Bash, Task, Write, Edit, Grep, Glob, Read)
        # So even though WebSearch was used, it still blocks because WebSearch is not a workflow execution tool
        data = {
            "tool_calls": [{"name": "Skill"}, {"name": "WebSearch"}],
            "tool_input": {"skill": "research"},
            "tools_used": [{"name": "Skill"}, {"name": "WebSearch"}],
        }

        result = Stop._check_post_skill_prose_response(data)

        # Should block because WebSearch is not an execution tool in the whitelist
        # The gate only recognizes Bash, Task, Write, Edit, Grep, Glob, Read as execution tools
        assert result is not None
        assert result["decision"] == "block"
        assert "E_POST_SKILL_PROSE_RESPONSE" in result["reason"]

    def test_no_skill_invoked_allowed(self):
        """Integration test: AI responds without invoking any skill (allowed)."""
        # Simulate Stop hook input without Skill tool
        data = {
            "tool_calls": [{"name": "Read"}],
            "tool_input": {"file_path": "test.txt"},
            "tools_used": [{"name": "Read"}],  # No Skill tool
        }

        result = Stop._check_post_skill_prose_response(data)

        # Should allow because no skill was invoked
        assert result is None

    def test_multiple_execution_tools_allowed(self):
        """Integration test: /code invoked with multiple execution tools."""
        # Simulate Stop hook input with multiple execution tools
        data = {
            "tool_calls": [
                {"name": "Skill"},
                {"name": "Read"},
                {"name": "Grep"},
                {"name": "Bash"},
            ],
            "tool_input": {"skill": "code"},
            "tools_used": [
                {"name": "Skill"},
                {"name": "Read"},
                {"name": "Grep"},
                {"name": "Bash"},
            ],
        }

        result = Stop._check_post_skill_prose_response(data)

        # Should allow because execution tools were used
        assert result is None

    def test_skill_name_extraction_from_dict(self):
        """Test skill name extraction from dict format tool_input."""
        data = {"tool_input": {"skill": "code"}}
        skill_name = Stop._extract_skill_name_from_data(data)
        assert skill_name == "code"

    def test_skill_name_extraction_from_xml(self):
        """Test skill name extraction from XML format tool_input."""
        data = {"tool_input": '<parameter name="skill">research</parameter>'}
        skill_name = Stop._extract_skill_name_from_data(data)
        assert skill_name == "research"

    def test_block_message_format(self):
        """Verify block message contains expected guidance."""
        data = {
            "tool_calls": [{"name": "Skill"}],
            "tool_input": {"skill": "code"},
            "tools_used": [{"name": "Skill"}],
        }

        result = Stop._check_post_skill_prose_response(data)

        # Verify block message structure
        assert result["decision"] == "block"
        assert "E_POST_SKILL_PROSE_RESPONSE" in result["reason"]
        assert "WORKFLOW EXECUTION REQUIRED" in result["reason"]
        assert "/code" in result["reason"]  # Skill name mentioned
        assert "workflow_steps" in result["reason"].lower()  # Guidance mentions workflow_steps
        assert "Bash" in result["reason"] or "Task" in result["reason"]  # Execution tools mentioned

    def test_all_execution_tools_recognized(self):
        """Verify all execution tools are properly recognized."""
        execution_tools = ["Bash", "Task", "Write", "Edit", "Grep", "Glob", "Read"]

        for tool in execution_tools:
            data = {
                "tool_calls": [{"name": "Skill"}, {"name": tool}],
                "tool_input": {"skill": "code"},
                "tools_used": [{"name": "Skill"}, {"name": tool}],
            }

            result = Stop._check_post_skill_prose_response(data)
            assert result is None, f"Tool {tool} should be recognized as execution tool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
