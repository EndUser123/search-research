"""Unit tests for prompt_templates module.

Tests prompt building, solo-dev constraints, and task-specific templates.
"""

from prompt_templates import PROMPT_TEMPLATES, SOLO_DEV_CONSTRAINTS, build_prompt
from task_classifier import TaskType


class TestPromptBuilding:
    """Test prompt building functionality."""

    def test_build_prompt_without_context(self):
        """Test prompt building without context."""
        prompt = build_prompt("explain recursion", TaskType.GENERAL, context=None)
        assert "explain recursion" in prompt
        assert SOLO_DEV_CONSTRAINTS in prompt

    def test_build_prompt_with_context(self):
        """Test prompt building with context."""
        context = "This is file content"
        prompt = build_prompt("explain", TaskType.GENERAL, context=context)
        assert "This is file content" in prompt
        assert "--- Context ---" in prompt

    def test_build_prompt_returns_string(self):
        """Test build_prompt always returns a string."""
        prompt = build_prompt("test", TaskType.GENERAL)
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestSoloDevConstraints:
    """Test solo-dev constraints are present in all prompts."""

    def test_general_has_solo_dev_constraints(self):
        """Test general prompt includes solo-dev constraints."""
        prompt = build_prompt("test", TaskType.GENERAL)
        assert "Solo Development Environment" in prompt
        assert "NO team assignments" in prompt

    def test_code_review_has_solo_dev_constraints(self):
        """Test code review prompt includes solo-dev constraints."""
        prompt = build_prompt("test", TaskType.CODE_REVIEW)
        assert SOLO_DEV_CONSTRAINTS in prompt

    def test_all_task_types_have_constraints(self):
        """Test all task types include solo-dev constraints."""
        for task_type in TaskType:
            prompt = build_prompt("test query", task_type)
            assert SOLO_DEV_CONSTRAINTS in prompt
            assert "Single developer" in prompt


class TestTaskSpecificTemplates:
    """Test task-specific prompt templates."""

    def test_code_review_template_exists(self):
        """Test CODE_REVIEW template exists and has expected content."""
        assert TaskType.CODE_REVIEW in PROMPT_TEMPLATES
        template = PROMPT_TEMPLATES[TaskType.CODE_REVIEW]
        assert "CODE REVIEW" in template
        assert "Security vulnerabilities" in template

    def test_planning_template_exists(self):
        """Test PLANNING template exists and has expected content."""
        assert TaskType.PLANNING in PROMPT_TEMPLATES
        template = PROMPT_TEMPLATES[TaskType.PLANNING]
        assert "IMPLEMENTATION PLAN" in template
        assert "phased approach" in template

    def test_brainstorm_template_exists(self):
        """Test BRAINSTORM template exists and has expected content."""
        assert TaskType.BRAINSTORM in PROMPT_TEMPLATES
        template = PROMPT_TEMPLATES[TaskType.BRAINSTORM]
        assert "BRAINSTORMING" in template
        assert "pros and cons" in template

    def test_research_template_exists(self):
        """Test RESEARCH template exists and has expected content."""
        assert TaskType.RESEARCH in PROMPT_TEMPLATES
        template = PROMPT_TEMPLATES[TaskType.RESEARCH]
        assert "RESEARCH" in template
        assert "References" in template

    def test_debug_template_exists(self):
        """Test DEBUG template exists and has expected content."""
        assert TaskType.DEBUG in PROMPT_TEMPLATES
        template = PROMPT_TEMPLATES[TaskType.DEBUG]
        assert "DEBUGGING" in template
        assert "Root cause" in template

    def test_refactor_template_exists(self):
        """Test REFACTOR template exists and has expected content."""
        assert TaskType.REFACTOR in PROMPT_TEMPLATES
        template = PROMPT_TEMPLATES[TaskType.REFACTOR]
        assert "REFACTORING" in template
        assert "Code quality" in template

    def test_general_template_exists(self):
        """Test GENERAL template exists."""
        assert TaskType.GENERAL in PROMPT_TEMPLATES
        template = PROMPT_TEMPLATES[TaskType.GENERAL]
        assert len(template) > 0


class TestPromptContent:
    """Test prompt content quality and structure."""

    def test_code_review_prompt_mentions_security(self):
        """Test code review prompt mentions security."""
        prompt = build_prompt("review this", TaskType.CODE_REVIEW)
        assert "Security" in prompt or "security" in prompt.lower()

    def test_planning_prompt_mentions_phases(self):
        """Test planning prompt mentions phases."""
        prompt = build_prompt("create a plan", TaskType.PLANNING)
        assert "Phase" in prompt

    def test_debug_prompt_mentions_diagnosis(self):
        """Test debug prompt mentions diagnosis."""
        prompt = build_prompt("debug this", TaskType.DEBUG)
        assert "Diagnosis" in prompt or "diagnosis" in prompt.lower()

    def test_refactor_prompt_mentions_risk(self):
        """Test refactor prompt mentions risk."""
        prompt = build_prompt("refactor this", TaskType.REFACTOR)
        assert "risk" in prompt.lower()

    def test_all_prompts_have_question_section(self):
        """Test all prompts include the user's question."""
        test_query = "analyze this code"
        for task_type in TaskType:
            prompt = build_prompt(test_query, task_type)
            assert test_query in prompt or "Question:" in prompt


class TestPromptOutputFormat:
    """Test prompt output format and structure."""

    def test_code_review_output_format(self):
        """Test code review prompt has expected output format."""
        prompt = build_prompt("test", TaskType.CODE_REVIEW)
        assert "Critical Issues" in prompt
        assert "Important Issues" in prompt

    def test_planning_output_format(self):
        """Test planning prompt has expected output format."""
        prompt = build_prompt("test", TaskType.PLANNING)
        assert "Phase 1:" in prompt

    def test_brainstorm_output_format(self):
        """Test brainstorm prompt has expected output format."""
        prompt = build_prompt("test", TaskType.BRAINSTORM)
        assert "Idea 1:" in prompt or "idea" in prompt.lower()

    def test_debug_output_format(self):
        """Test debug prompt has expected output format."""
        prompt = build_prompt("test", TaskType.DEBUG)
        assert "Diagnosis" in prompt or "Fix Options" in prompt

    def test_refactor_output_format(self):
        """Test refactor prompt has expected output format."""
        prompt = build_prompt("test", TaskType.REFACTOR)
        assert "Issues Found" in prompt or "Refactoring Plan" in prompt


class TestEdgeCases:
    """Test edge cases in prompt building."""

    def test_empty_query(self):
        """Test prompt building with empty query."""
        prompt = build_prompt("", TaskType.GENERAL)
        assert len(prompt) > 0  # Should still build a prompt

    def test_very_long_query(self):
        """Test prompt building with very long query."""
        long_query = "test " * 1000
        prompt = build_prompt(long_query, TaskType.GENERAL)
        assert long_query in prompt
        assert SOLO_DEV_CONSTRAINTS in prompt

    def test_query_with_newlines(self):
        """Test prompt building preserves newlines in query."""
        query_with_newlines = "line1\nline2\nline3"
        prompt = build_prompt(query_with_newlines, TaskType.GENERAL)
        assert "line1" in prompt
        assert "line2" in prompt

    def test_context_with_special_chars(self):
        """Test prompt building handles special characters in context."""
        context = "Code with <html> & 'quotes'"
        prompt = build_prompt("test", TaskType.GENERAL, context=context)
        assert context in prompt


class TestSoloDevConstraintsContent:
    """Test solo-dev constraints have expected content."""

    def test_constraints_mention_single_developer(self):
        """Test constraints mention single developer."""
        assert "Single developer" in SOLO_DEV_CONSTRAINTS
        assert "NO team" in SOLO_DEV_CONSTRAINTS

    def test_constraints_prefer_simple_solutions(self):
        """Test constraints prefer simple solutions."""
        assert "SIMPLE solutions" in SOLO_DEV_CONSTRAINTS
        assert "JSON > databases" in SOLO_DEV_CONSTRAINTS

    def test_constraints_avoid_over_engineering(self):
        """Test constraints avoid over-engineering."""
        assert "Avoid over-engineering" in SOLO_DEV_CONSTRAINTS
        assert "single user" in SOLO_DEV_CONSTRAINTS
