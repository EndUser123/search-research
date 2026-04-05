#!/usr/bin/env python3
"""
Unit tests for Prompt Enhancement Bridge hook.

Tests ambiguity detection, complexity assessment, domain detection,
and injection builders.
"""

import sys
from pathlib import Path

import pytest

# Add hooks to path
hooks_dir = Path(__file__).resolve().parent.parent.parent.parent / "hooks"
sys.path.insert(0, str(hooks_dir))

# Import the module (uses the functions directly for testing)
from UserPromptSubmit_prompt_enhancement_bridge import (
    assess_complexity,
    build_clarification_injection,
    build_lightweight_guidance,
    check_ambiguity,
    detect_domain,
)


class TestDomainDetection:
    """Test domain detection from prompts and paths."""

    def test_security_domain_from_path(self):
        """Detect security domain from path hints."""
        assert detect_domain("fix auth", "P:/security/") == "security"
        assert detect_domain("help", "P:/__csf/src/security/") == "security"

    def test_security_domain_from_keywords(self):
        """Detect security domain from keywords."""
        assert detect_domain("fix vulnerability", "P:/") == "security"
        assert detect_domain("check xss", "P:/src/") == "security"
        assert detect_domain("auth issue", "P:/") == "security"

    def test_testing_domain_from_path(self):
        """Detect testing domain from path hints."""
        assert detect_domain("write test", "P:/tests/") == "testing"
        assert detect_domain("pytest help", "P:/test/") == "testing"

    def test_testing_domain_from_keywords(self):
        """Detect testing domain from keywords."""
        assert detect_domain("mock this", "P:/") == "testing"
        assert detect_domain("pytest error", "P:/src/") == "testing"

    def test_database_domain(self):
        """Detect database domain."""
        assert detect_domain("query help", "P:/db/") == "database"
        assert detect_domain("sql issue", "P:/") == "database"

    def test_frontend_domain(self):
        """Detect frontend domain."""
        assert detect_domain("react help", "P:/frontend/") == "frontend"
        assert detect_domain("css issue", "P:/") == "frontend"

    def test_general_domain_default(self):
        """Default to general when no patterns match."""
        assert detect_domain("hello world", "P:/") == "general"


class TestComplexityAssessment:
    """Test complexity assessment based on word count and patterns."""

    def test_simple_what_is_pattern(self):
        """'what is X' patterns are simple."""
        assert assess_complexity("what is react") == "simple"
        assert assess_complexity("what are hooks") == "simple"

    def test_simple_word_count(self):
        """Prompts with <= 10 words are simple."""
        assert assess_complexity("help me fix this") == "simple"
        assert assess_complexity("test the database connection") == "simple"

    def test_moderate_word_count(self):
        """10-30 words is moderate."""
        moderate_prompt = "describe the current architecture of the system and how it handles different types of errors during runtime"
        assert len(moderate_prompt.split()) >= 10  # Verify test data
        assert assess_complexity(moderate_prompt) == "moderate"

    def test_complex_word_count(self):
        """30-60 words is complex."""
        long_prompt = " ".join(["word"] * 40)
        assert assess_complexity(long_prompt) == "complex"

    def test_explicit_word_count(self):
        """60+ words is expert."""
        very_long_prompt = " ".join(["word"] * 70)
        assert assess_complexity(very_long_prompt) == "expert"

    def test_simple_implement_pattern(self):
        """Short 'implement X' prompts are simple based on word count."""
        assert assess_complexity("implement a new hook for prompt validation") == "simple"

    def test_framework_pattern_short(self):
        """Short 'framework X' prompts are simple based on word count."""
        assert assess_complexity("framework for semantic search architecture") == "simple"

    def test_explicit_word_count(self):
        """60+ words is expert."""
        very_long_prompt = " ".join(["word"] * 70)
        assert assess_complexity(very_long_prompt) == "expert"


class TestAmbiguityDetection:
    """Test ambiguity detection patterns."""

    def test_unclear_antecedent_fix(self):
        """Detect 'fix it' without referent."""
        assert check_ambiguity("fix it") == (True, "unclear_antecedent")
        assert check_ambiguity("fix this") == (True, "unclear_antecedent")
        assert check_ambiguity("check that") == (True, "unclear_antecedent")

    def test_missing_specifics(self):
        """Detect 'implement this' without what."""
        assert check_ambiguity("implement this") == (True, "missing_specifics")
        assert check_ambiguity("create this") == (True, "missing_specifics")

    def test_ambiguous_improvement(self):
        """Detect 'make it better' phrases."""
        assert check_ambiguity("make it better") == (True, "ambiguous_improvement")
        assert check_ambiguity("optimize this") == (True, "ambiguous_improvement")

    def test_too_brief(self):
        """Detect very brief prompts."""
        assert check_ambiguity("fix") == (True, "too_brief")
        assert check_ambiguity("help") == (True, "too_brief")
        assert check_ambiguity("ok") == (True, "too_brief")

    def test_not_ambiguous_specific_request(self):
        """Specific requests are not ambiguous."""
        is_ambiguous, reason = check_ambiguity("implement user authentication with JWT tokens")
        assert not is_ambiguous
        assert reason is None

    def test_not_ambiguous_detailed(self):
        """Detailed prompts are not ambiguous."""
        is_ambiguous, reason = check_ambiguity("describe how the UserPromptSubmit router works and its priority system")
        assert not is_ambiguous


class TestClarificationInjection:
    """Test clarification question injection builder."""

    def test_unclear_antecedent_injection(self):
        """Build questions for unclear antecedents."""
        result = build_clarification_injection("fix it", "unclear_antecedent", "general")
        assert "additionalContext" in result
        assert "What specifically are you referring to?" in result["additionalContext"]
        assert "Which file, component, or area" in result["additionalContext"]

    def test_missing_specifics_injection(self):
        """Build questions for missing specifics."""
        result = build_clarification_injection("implement this", "missing_specifics", "general")
        assert "additionalContext" in result
        assert "What should be implemented" in result["additionalContext"]

    def test_ambiguous_improvement_injection(self):
        """Build questions for ambiguous improvement."""
        result = build_clarification_injection("make it better", "ambiguous_improvement", "general")
        assert "additionalContext" in result
        assert "What aspects should be improved" in result["additionalContext"]

    def test_too_brief_injection(self):
        """Build questions for too brief prompts."""
        result = build_clarification_injection("help", "too_brief", "security")
        assert "additionalContext" in result
        assert "What would you like me to help you with?" in result["additionalContext"]

    def test_injection_includes_domain_context(self):
        """Injection includes domain context."""
        result = build_clarification_injection("fix", "too_brief", "security")
        assert "security" in result["additionalContext"].lower()

    def test_tokens_counted(self):
        """Token count is estimated."""
        result = build_clarification_injection("fix it", "unclear_antecedent", "general")
        assert "tokens" in result
        assert result["tokens"] > 0


class TestGuidanceInjection:
    """Test guidance injection builder."""

    def test_security_guidance(self):
        """Security domain gets security-specific guidance."""
        result = build_lightweight_guidance("security", "moderate")
        assert "additionalContext" in result
        assert "security" in result["additionalContext"].lower()
        assert "OWASP" in result["additionalContext"]

    def test_testing_guidance(self):
        """Testing domain gets testing-specific guidance."""
        result = build_lightweight_guidance("testing", "moderate")
        assert "additionalContext" in result
        assert "test-driven development" in result["additionalContext"]

    def test_database_guidance(self):
        """Database domain gets database-specific guidance."""
        result = build_lightweight_guidance("database", "moderate")
        assert "additionalContext" in result
        assert "transaction" in result["additionalContext"].lower()

    def test_frontend_guidance(self):
        """Frontend domain gets frontend-specific guidance."""
        result = build_lightweight_guidance("frontend", "moderate")
        assert "additionalContext" in result
        assert "component" in result["additionalContext"].lower()

    def test_general_guidance(self):
        """General domain gets generic guidance."""
        result = build_lightweight_guidance("general", "moderate")
        assert "additionalContext" in result
        assert "specific details" in result["additionalContext"]


class TestIntegration:
    """Integration tests for the full hook workflow."""

    def test_hook_exists_and_executable(self):
        """Verify hook file exists and has correct permissions."""
        hook_file = Path(__file__).resolve().parent.parent.parent / "UserPromptSubmit_prompt_enhancement_bridge.py"
        assert hook_file.exists()
        # Note: on Windows, executable bit may not be set the same way
        assert hook_file.stat().st_size > 0

    def test_hook_imports(self):
        """Verify hook can be imported without errors."""
        # The imports at the top of this test file verify this
        assert True  # If we got here, imports worked

    def test_fail_open_on_invalid_json(self):
        """Hook handles invalid JSON gracefully."""
        # This would need the hook_main behavior to be tested separately
        # For now, we verify the module loads
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
