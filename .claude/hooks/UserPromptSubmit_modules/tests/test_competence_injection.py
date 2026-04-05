"""Tests for competence_injector.py - Competence template injection.

Tests for:
- Research skill loaded → template injected with research guidance
- Analysis skill loaded → template injected with analysis questions
- Meta skill loaded → no template injected (HookResult.empty())
- No skill loaded → no template injected
- Cleanup: clear_state() after each test

Phase 2, Step 2.3 of Competence Layer implementation.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))


class TestCompetenceInjectorModuleExists:
    """Test module structure and imports."""

    def test_competence_injector_module_exists(self):
        """Module should be importable."""
        from UserPromptSubmit import competence_injector
        assert competence_injector is not None

    def test_competence_injector_has_hook_function(self):
        """Should have the main hook function."""
        from UserPromptSubmit import competence_injector
        assert hasattr(competence_injector, 'competence_injector_hook')
        assert callable(competence_injector.competence_injector_hook)


def create_mock_state(skill_name: str) -> dict:
    """Create a mock skill execution state dict."""
    return {
        "skill": skill_name.lower(),
        "loaded_at": 1234567890.0,
        "required_tools": ["Bash", "Task"],
        "pattern": "",
        "output_markers": [],
        "required_pattern": "",
        "hint": "",
        "intent_enabled": False,
        "tools_used": [],
        "commands_run": [],
        "execution_satisfied": False,
        "allowed_first_tools": [],
        "first_tool_validated": False,
    }


def run_with_state(state, prompt="/research test"):
    """Run the hook with a mocked state."""
    from UserPromptSubmit import competence_injector
    from UserPromptSubmit.base import HookContext

    # Patch at the module level, not the fully qualified path
    with patch.object(competence_injector, 'read_pending_state', return_value=state):
        context = HookContext(
            prompt=prompt,
            data={},
            session_id="test-session",
            terminal_id="test-terminal",
        )

        return competence_injector.process_skill_load(context)


class TestResearchSkillInjection:
    """Tests for research skill template injection."""

    def test_research_skill_injects_template(self):
        """Research skill should inject template with 'COMPETENCE GUIDANCE FOR RESEARCH TASKS'."""
        state = create_mock_state("research")
        result = run_with_state(state)

        assert result is not None
        assert result.context is not None
        assert "COMPETENCE GUIDANCE FOR RESEARCH" in result.context
        assert "Core Question" in result.context
        assert "What is true?" in result.context

    def test_research_template_has_lifecycle_steps(self):
        """Research template should include 5-step lifecycle."""
        state = create_mock_state("research")
        # Use a longer prompt (>15 chars) to avoid trivial prompt detection
        result = run_with_state(state, prompt="/research investigate the causes of")

        assert result.context is not None
        assert "5-Step Lifecycle" in result.context
        assert "Understand" in result.context
        assert "Enhance" in result.context
        assert "Execute" in result.context
        assert "Audit" in result.context


class TestAnalysisSkillInjection:
    """Tests for analysis skill template injection."""

    def test_analysis_skill_injects_template(self):
        """Analysis skill (debugrca) should inject template with analysis guidance."""
        state = create_mock_state("debugrca")
        result = run_with_state(state)

        assert result is not None
        assert result.context is not None
        assert "COMPETENCE GUIDANCE FOR ANALYSIS" in result.context

    def test_analysis_template_has_core_question(self):
        """Analysis template should have 'What does this mean?' as core question."""
        state = create_mock_state("debugrca")
        result = run_with_state(state)

        assert result.context is not None
        assert "What does this mean?" in result.context


class TestMetaSkillHandling:
    """Tests for meta skill handling (no template injected)."""

    def test_meta_ask_skill_no_template(self):
        """'ask' skill (meta) should return empty result."""
        state = create_mock_state("ask")
        result = run_with_state(state)

        # Meta skills return empty
        assert result is not None
        assert result.is_empty() or not result.context

    def test_meta_search_skill_no_template(self):
        """'search' skill (meta) should return empty result."""
        state = create_mock_state("search")
        result = run_with_state(state)

        assert result is not None
        assert result.is_empty() or not result.context


class TestNoSkillLoaded:
    """Tests for when no skill is loaded."""

    def test_no_skill_loaded_returns_empty(self):
        """No skill loaded (None state) should return empty result."""
        result = run_with_state(None)

        assert result is not None
        assert result.is_empty()

    def test_empty_state_returns_empty(self):
        """Empty state dict should return empty result."""
        result = run_with_state({})

        assert result is not None
        assert result.is_empty()


class TestEscapeHatch:
    """Tests for escape hatch in injected template."""

    def test_escape_hatch_in_research_template(self):
        """Template should include escape hatch note."""
        state = create_mock_state("research")
        result = run_with_state(state)

        assert result.context is not None
        assert "template is guidance" in result.context.lower()
        assert "mismatch" in result.context.lower()


class TestTokenEstimation:
    """Tests for token estimation in injected content."""

    def test_token_estimate_non_zero(self):
        """Template injection should have non-zero token estimate."""
        state = create_mock_state("research")
        result = run_with_state(state)

        if not result.is_empty():
            assert result.tokens > 0
            # Should be reasonable (not exceeding context limits)
            assert result.tokens < 10000  # Sanity check


class TestRegistryIntegration:
    """Tests for hook registration in registry."""

    def test_competence_injector_registered(self):
        """Hook should be registered in global registry."""
        from UserPromptSubmit.registry import HOOK_PRIORITY, HOOKS

        # Hook name should be in registry
        assert "competence_injector" in HOOKS or "competence_injector" in HOOK_PRIORITY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
