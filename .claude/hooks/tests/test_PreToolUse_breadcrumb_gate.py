#!/usr/bin/env python3
"""
Tests for PreToolUse_breadcrumb_gate.py

Covers:
- _get_step_kind_from_tool() - tool to step kind mapping
- _get_expected_next_step() - workflow step progression
- _is_valid_progression() - step validation logic
- run() - hook entry point
"""

import sys
from pathlib import Path

import pytest

# Force hooks directory into path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from PreToolUse_breadcrumb_gate import (
    _get_expected_next_step,
    _get_step_kind_from_tool,
    _is_valid_progression,
    run,
)


class TestGetStepKindFromTool:
    """Tests for _get_step_kind_from_tool()"""

    def test_exact_matches(self):
        """Exact tool name matches return correct step kind."""
        assert _get_step_kind_from_tool("WebSearch") == "research"
        assert _get_step_kind_from_tool("Read") == "requirements"
        assert _get_step_kind_from_tool("Edit") == "tdd"
        assert _get_step_kind_from_tool("Write") == "tdd"
        assert _get_step_kind_from_tool("Bash") == "verification"
        assert _get_step_kind_from_tool("Skill") == "verification"
        assert _get_step_kind_from_tool("Agent") == "agent_coordination"
        assert _get_step_kind_from_tool("EnterPlanMode") == "planning"

    def test_prefix_matches(self):
        """Tools starting with known prefixes match correctly."""
        assert _get_step_kind_from_tool("mcp__tavily-mcp__tavily_search") == "research"
        assert _get_step_kind_from_tool("mcp__perplexity__perplexity_search") == "research"
        assert _get_step_kind_from_tool("mcp__exa__get_code_context_exa") == "research"

    def test_pattern_based_inference(self):
        """Pattern-based inference for unknown tools."""
        assert _get_step_kind_from_tool("MyCustomSearchTool") == "research"
        assert _get_step_kind_from_tool("FileReader") == "requirements"
        assert _get_step_kind_from_tool("CodeEditor") == "tdd"
        assert _get_step_kind_from_tool("TestRunner") == "verification"
        assert _get_step_kind_from_tool("SubAgent") == "agent_coordination"

    def test_unknown_tool_returns_none(self):
        """Unknown tools with no patterns return None."""
        assert _get_step_kind_from_tool("XYZUnknown") is None
        assert _get_step_kind_from_tool("") is None

    def test_case_sensitivity(self):
        """Pattern matching is case-insensitive, exact/prefi""x matching is case-sensitive."""
        # websearch: no exact match, but "search" in "websearch" → research (pattern match)
        assert _get_step_kind_from_tool("websearch") == "research"
        # EDIT: no exact match, but "edit" in "edit" → tdd (pattern match, case-insensitive)
        assert _get_step_kind_from_tool("EDIT") == "tdd"
        # XYZUnknown: no exact, no prefix, no pattern → None
        assert _get_step_kind_from_tool("XYZUnknown") is None


class TestGetExpectedNextStep:
    """Tests for _get_expected_next_step()"""

    def test_returns_first_incomplete_step(self):
        """Returns first step not in completed set."""
        trail = {
            "workflow_steps": [
                {"id": "step1", "kind": "research"},
                {"id": "step2", "kind": "requirements"},
                {"id": "step3", "kind": "tdd"},
            ],
            "completed_steps": ["step1"],
        }
        result = _get_expected_next_step(trail)
        assert result == {"id": "step2", "kind": "requirements"}

    def test_skips_optional_verification_steps(self):
        """Optional verification steps are skipped."""
        trail = {
            "workflow_steps": [
                {"id": "step1", "kind": "research"},
                {"id": "verify1", "kind": "verification", "optional": True},
                {"id": "step2", "kind": "tdd"},
            ],
            "completed_steps": ["step1"],
        }
        result = _get_expected_next_step(trail)
        assert result == {"id": "step2", "kind": "tdd"}

    def test_all_complete_returns_none(self):
        """Returns None when all steps are complete."""
        trail = {
            "workflow_steps": [
                {"id": "step1", "kind": "research"},
                {"id": "step2", "kind": "tdd"},
            ],
            "completed_steps": ["step1", "step2"],
        }
        result = _get_expected_next_step(trail)
        assert result is None

    def test_string_step_ids(self):
        """String step IDs are handled correctly."""
        trail = {
            "workflow_steps": ["step1", "step2", "step3"],
            "completed_steps": ["step1"],
        }
        result = _get_expected_next_step(trail)
        assert result == {"id": "step2", "kind": "execution"}

    def test_empty_workflow_steps(self):
        """Empty workflow_steps returns None."""
        trail = {"workflow_steps": [], "completed_steps": []}
        result = _get_expected_next_step(trail)
        assert result is None


class TestIsValidProgression:
    """Tests for _is_valid_progression()"""

    def test_same_kind_is_valid(self):
        """Tool kind matching expected step kind is valid."""
        step = {"id": "step1", "kind": "research"}
        assert _is_valid_progression("WebSearch", step) is True
        assert _is_valid_progression("mcp__tavily_search", step) is True

    def test_earlier_step_is_valid(self):
        """Going back to earlier step is valid (investigation)."""
        step = {"id": "step1", "kind": "tdd"}
        # research is before tdd in the order
        assert _is_valid_progression("WebSearch", step) is True

    def test_skipping_ahead_is_invalid(self):
        """Skipping to a later step is invalid."""
        step = {"id": "step1", "kind": "research"}
        # tdd comes after research
        assert _is_valid_progression("Edit", step) is False

    def test_unknown_tool_kind_is_valid(self):
        """Unknown tool kinds are allowed (fail open)."""
        step = {"id": "step1", "kind": "research"}
        assert _is_valid_progression("XYZUnknownTool", step) is True

    def test_unknown_step_kind_is_valid(self):
        """Unknown step kinds are allowed (fail open)."""
        step = {"id": "step1", "kind": "custom_kind"}
        assert _is_valid_progression("WebSearch", step) is True

    def test_step_ordering(self):
        """Correct ordering: research < requirements < tdd < verification."""
        research_step = {"id": "s1", "kind": "research"}
        req_step = {"id": "s2", "kind": "requirements"}
        tdd_step = {"id": "s3", "kind": "tdd"}
        verify_step = {"id": "s4", "kind": "verification"}

        # Can use research tools at research step
        assert _is_valid_progression("WebSearch", research_step) is True
        # Cannot use tdd tools at research step
        assert _is_valid_progression("Edit", research_step) is False
        # Cannot use requirements tools at research step (Read=requirements index 1 > research index 0)
        assert _is_valid_progression("Read", research_step) is False

        # Can use tdd tools at tdd step
        assert _is_valid_progression("Edit", tdd_step) is True
        # Cannot skip to verification
        assert _is_valid_progression("Bash", tdd_step) is False


class TestRun:
    """Tests for run() - hook entry point"""

    def test_disabled_returns_true(self, monkeypatch):
        """When ENABLED=False, always returns continue=True."""
        monkeypatch.setenv("BREADCRUMB_GATE_ENABLED", "false")
        # Re-import to pick up env change
        import importlib

        import PreToolUse_breadcrumb_gate

        importlib.reload(PreToolUse_breadcrumb_gate)

        result = PreToolUse_breadcrumb_gate.run({"tool_name": "Edit"})
        assert result == {"continue": True}

    def test_skill_tool_always_allowed(self):
        """Skill tool is always allowed (workflow initiation)."""
        result = run({"tool_name": "Skill", "tool_input": {}})
        assert result["continue"] is True

    def test_no_breadcrumb_trail_continues(self):
        """When no breadcrumb trail exists, tool is allowed."""
        result = run({"tool_name": "Edit", "tool_input": {}})
        assert result["continue"] is True

    def test_no_completed_steps_continues(self):
        """When no steps completed yet, first tool is allowed."""
        # This simulates having a trail but no completed steps
        # In practice, the hook would need a mock for get_breadcrumb_trail
        result = run({"tool_name": "WebSearch", "tool_input": {}})
        # Without a breadcrumb trail, continues
        assert result["continue"] is True

    def test_returns_correct_schema(self):
        """Always returns dict with 'continue' key."""
        result = run({"tool_name": "Bash", "tool_input": {}})
        assert isinstance(result, dict)
        assert "continue" in result
        assert isinstance(result["continue"], bool)


class TestIntegration:
    """Integration tests for the complete hook"""

    def test_all_mapped_tools_return_valid_schema(self):
        """All tools in TOOL_TO_STEP_KIND return valid schema."""
        tools = [
            "WebSearch",
            "mcp__tavily-mcp__tavily_search",
            "Read",
            "Glob",
            "Grep",
            "Edit",
            "Write",
            "Bash",
            "Skill",
            "AskUserQuestion",
            "EnterPlanMode",
            "Agent",
        ]
        for tool in tools:
            result = run({"tool_name": tool, "tool_input": {}})
            assert "continue" in result, f"{tool} missing 'continue' key"
            assert isinstance(result["continue"], bool), f"{tool} 'continue' is not bool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
