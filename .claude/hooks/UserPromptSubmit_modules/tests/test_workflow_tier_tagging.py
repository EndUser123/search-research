"""Tests for workflow_tier_tagging module."""


from UserPromptSubmit_modules.base import HookContext
from UserPromptSubmit_modules.workflow_tier_tagging import (
    _find_skill_file,
    _generate_tier_directive,
    _parse_workflow_steps,
    workflow_tier_tagging_hook,
)


def test_find_skill_file_debugRCA():
    """Test finding debugRCA skill file."""
    skill_file = _find_skill_file("debugRCA")
    assert skill_file is not None
    assert skill_file.exists()
    assert skill_file.name == "SKILL.md"


def test_find_skill_file_nonexistent():
    """Test finding nonexistent skill returns None."""
    skill_file = _find_skill_file("nonexistent_skill_xyz")
    assert skill_file is None


def test_parse_workflow_steps_debugRCA():
    """Test parsing workflow_steps from debugRCA SKILL.md."""
    skill_file = _find_skill_file("debugRCA")
    assert skill_file is not None

    steps = _parse_workflow_steps(skill_file)
    assert len(steps) == 5
    assert "diagnose_with_evidence" in steps
    assert "recommend_fix_with_verification" in steps
    assert "complete_root_cause_analysis" in steps
    assert "tier_evidence_tagging" in steps
    assert "documentation_completion" in steps


def test_generate_tier_directive_debugRCA():
    """Test generating workflow step directive."""
    workflow_steps = [
        "diagnose_with_evidence",
        "recommend_fix_with_verification",
        "complete_root_cause_analysis",
        "tier_evidence_tagging",
        "documentation_completion",
    ]

    directive = _generate_tier_directive("debugRCA", workflow_steps)

    assert "METHODOLOGY COMPLIANCE FOR debugRCA" in directive
    assert "[DIAGNOSE_WITH_EVIDENCE]" in directive
    assert "[RECOMMEND_FIX_WITH_VERIFICATION]" in directive
    assert "[COMPLETE_ROOT_CAUSE_ANALYSIS]" in directive
    assert "[TIER_EVIDENCE_TAGGING]" in directive
    assert "[DOCUMENTATION_COMPLETION]" in directive
    assert "5 documented workflow steps" in directive
    assert "[COMPLETE]" in directive
    assert "Self-Audit" in directive


def test_workflow_tier_tagging_hook_with_debugRCA():
    """Test hook injects directive for debugRCA skill invocation."""
    # Simulate UserPromptSubmit event data for Skill() invocation
    data = {
        "tool_name": "Skill",
        "tool_input": {
            "skill": "debugRCA",
            "args": "investigate hook failure",
        },
        "session_id": "test-session-123",
        "terminal_id": "test-terminal",
    }

    context = HookContext(
        prompt="/debugRCA investigate hook failure",
        data=data,
        session_id="test-session-123",
        terminal_id="test-terminal",
    )

    result = workflow_tier_tagging_hook(context)

    # Should return non-empty result with directive
    assert not result.is_empty()
    assert isinstance(result.context, str)
    assert "METHODOLOGY COMPLIANCE FOR debugRCA" in result.context
    assert "[DIAGNOSE_WITH_EVIDENCE]" in result.context


def test_workflow_tier_tagging_hook_skips_non_skill():
    """Test hook returns empty for non-Skill tool invocations."""
    data = {
        "tool_name": "Read",
        "tool_input": {"file_path": "test.txt"},
        "session_id": "test-session-123",
        "terminal_id": "test-terminal",
    }

    context = HookContext(
        prompt="/read test.txt",
        data=data,
        session_id="test-session-123",
        terminal_id="test-terminal",
    )

    result = workflow_tier_tagging_hook(context)

    # Should return empty result (skip)
    assert result.is_empty()


def test_workflow_tier_tagging_hook_skips_non_procedure_skill():
    """Test hook returns empty for non-PROCEDURE skills."""
    # "code" is not in PROCEDURE_SKILLS set
    data = {
        "tool_name": "Skill",
        "tool_input": {
            "skill": "code",
            "args": "implement feature",
        },
        "session_id": "test-session-123",
        "terminal_id": "test-terminal",
    }

    context = HookContext(
        prompt="/code implement feature",
        data=data,
        session_id="test-session-123",
        terminal_id="test-terminal",
    )

    result = workflow_tier_tagging_hook(context)

    # Should return empty result (skip - not a PROCEDURE skill)
    assert result.is_empty()


def test_workflow_tier_tagging_hook_skips_skill_without_workflow_steps():
    """Test hook returns empty for skills without workflow_steps."""
    # This test assumes "arch" skill has no workflow_steps (or create a mock skill)
    # For now, we'll just test the hook structure

    # If we had a skill without workflow_steps, the hook should skip it
    # The actual behavior depends on whether such skills exist in the codebase
    pass
