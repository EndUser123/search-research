"""
Tests for abstraction_clarity_gate module

Covers:
- Ambiguous question detection
- Clarity pattern overrides
- Skip patterns
- Edge cases
"""

import pytest
from UserPromptSubmit_modules.abstraction_clarity_gate import (
    AMBIGUOUS_PATTERNS,
    CLARITY_PATTERNS,
    SKIP_PATTERNS,
    _is_ambiguous_question,
    process_prompt,
)
from UserPromptSubmit_modules.base import HookContext


class TestAmbiguousDetection:
    """Test detection of ambiguous questions."""

    def test_process_improvement_questions(self):
        """Process improvement questions should be flagged."""
        ambiguous_prompts = [
            "how can we make the process better",
            "what can I do to improve the workflow",
            "how should we approach this",
            "how can you make the results better",
        ]
        for prompt in ambiguous_prompts:
            assert _is_ambiguous_question(prompt), f"Should flag: {prompt}"

    def test_meta_analysis_questions(self):
        """Meta-analysis questions should be flagged."""
        ambiguous_prompts = [
            "analyze the problems",
            "what were the main issues",
            "what's broken with our system",
        ]
        for prompt in ambiguous_prompts:
            assert _is_ambiguous_question(prompt), f"Should flag: {prompt}"

    def test_optimal_solution_questions(self):
        """Optimal solution questions should be flagged."""
        ambiguous_prompts = [
            "what's the optimal solution",
            "how should we solve this",
            "what is the best approach",
        ]
        for prompt in ambiguous_prompts:
            assert _is_ambiguous_question(prompt), f"Should flag: {prompt}"


class TestClarityOverrides:
    """Test that clarity patterns prevent false positives."""

    def test_technical_level_clarity(self):
        """Technical indicators should override ambiguity."""
        clear_prompts = [
            "how can we make the process better by editing the files",
            "what's broken in the code",
            "optimize the function performance",
        ]
        for prompt in clear_prompts:
            assert not _is_ambiguous_question(prompt), f"Should NOT flag: {prompt}"

    def test_process_level_clarity(self):
        """Process indicators should override ambiguity."""
        clear_prompts = [
            "how should our workflow handle this decision",
            "what approach pattern should we use",
        ]
        for prompt in clear_prompts:
            assert not _is_ambiguous_question(prompt), f"Should NOT flag: {prompt}"

    def test_principle_level_clarity(self):
        """Principle indicators should override ambiguity."""
        clear_prompts = [
            "why does this keep happening",
            "what principle makes this work",
            "what's the underlying issue with the system",
        ]
        for prompt in clear_prompts:
            assert not _is_ambiguous_question(prompt), f"Should NOT flag: {prompt}"


class TestSkipPatterns:
    """Test that skip patterns work correctly."""

    def test_slash_commands_skipped(self):
        """Slash commands should be skipped."""
        assert not _is_ambiguous_question("/search query")
        assert not _is_ambiguous_question("/code implement feature")

    def test_short_prompts_skipped(self):
        """Short prompts should be skipped."""
        assert not _is_ambiguous_question("how can we")
        assert not _is_ambiguous_question("what's the best")

    def test_acceptances_skipped(self):
        """Acceptance responses should be skipped."""
        assert not _is_ambiguous_question("yes, that works")
        assert not _is_ambiguous_question("ok proceed")

    def test_simple_requests_skipped(self):
        """Simple requests should be skipped."""
        assert not _is_ambiguous_question("show me the files")
        assert not _is_ambiguous_question("find the bug")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_prompt(self):
        """Empty prompt should not be flagged."""
        assert not _is_ambiguous_question("")

    def test_whitespace_only(self):
        """Whitespace-only prompt should not be flagged."""
        assert not _is_ambiguous_question("   ")

    def test_case_insensitive(self):
        """Detection should be case-insensitive."""
        assert _is_ambiguous_question("HOW CAN WE MAKE THE PROCESS BETTER")
        assert _is_ambiguous_question("What's The Optimal Solution")

    def test_multiple_patterns(self):
        """Prompt matching multiple ambiguous patterns should be flagged."""
        assert _is_ambiguous_question("how can we make the process better and solve this")

    def test_subtle_clarity(self):
        """Subtle clarity indicators should work."""
        assert not _is_ambiguous_question("how can we refactor the code to make it better")
        assert not _is_ambiguous_question("what's the best pattern for this workflow")


class TestProcessPrompt:
    """Test the main hook function."""

    def test_returns_result_for_ambiguous(self):
        """Should return HookResult with clarification for ambiguous prompts."""
        ctx = HookContext(
            prompt="how can we make the process better",
            data={},
        )
        result = process_prompt(ctx)

        # Should inject clarification context
        assert not result.is_empty()
        assert "ABSTRACTION LEVEL" in result.context
        assert "Technical Level" in result.context
        assert "Process Level" in result.context
        assert "Principle Level" in result.context

    def test_returns_none_for_clear(self):
        """Should return empty HookResult for clear prompts."""
        ctx = HookContext(
            prompt="edit the file to fix the bug",
            data={},
        )
        result = process_prompt(ctx)

        # Should not inject anything
        assert result.is_empty()


class TestPatternCoverage:
    """Verify all patterns are syntactically valid."""

    def test_ambiguous_patterns_compile(self):
        """All ambiguous patterns should compile successfully."""
        import re
        for pattern in AMBIGUOUS_PATTERNS:
            try:
                re.compile(pattern, re.IGNORECASE)
            except Exception as e:
                pytest.fail(f"Ambiguous pattern failed to compile: {pattern}\nError: {e}")

    def test_clarity_patterns_compile(self):
        """All clarity patterns should compile successfully."""
        import re
        for pattern in CLARITY_PATTERNS:
            try:
                re.compile(pattern, re.IGNORECASE)
            except Exception as e:
                pytest.fail(f"Clarity pattern failed to compile: {pattern}\nError: {e}")

    def test_skip_patterns_compile(self):
        """All skip patterns should compile successfully."""
        import re
        for pattern in SKIP_PATTERNS:
            try:
                re.compile(pattern, re.IGNORECASE)
            except Exception as e:
                pytest.fail(f"Skip pattern failed to compile: {pattern}\nError: {e}")


class TestIntegration:
    """Verify module is properly integrated into registry system."""

    def test_hook_registered_in_registry(self):
        """Hook should be registered in HOOKS dict when module is imported."""
        # Import the module (simulates what registry.py does)
        import importlib

        from UserPromptSubmit_modules import registry
        module = importlib.import_module("UserPromptSubmit_modules.abstraction_clarity_gate")

        # Check it was registered
        assert "abstraction_clarity_gate" in registry.HOOKS, \
            "Hook not found in registry.HOOKS after import"

    def test_hook_has_correct_priority(self):
        """Hook should have priority 9.5 (early execution)."""
        from UserPromptSubmit_modules import registry

        priority = registry.HOOK_PRIORITY.get("abstraction_clarity_gate")
        assert priority == 9.5, f"Expected priority 9.5, got {priority}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
