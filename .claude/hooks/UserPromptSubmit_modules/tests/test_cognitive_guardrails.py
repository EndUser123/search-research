"""
Tests for cognitive_guardrails module

Covers:
- Design intent detection (all three patterns)
- Non-design queries (negative cases)
- Edge cases (empty, None, truncated input)
- Environment variable gating
- Hook registration
- Input length limit
"""

import os
import pytest
from UserPromptSubmit_modules.cognitive_guardrails import (
    COGNITIVE_GUARDRAILS_ENABLED,
    COGNITIVE_GUARDRAILS_INJECTION,
    DESIGN_INTENT_PATTERNS,
    MAX_QUERY_LENGTH,
    cognitive_guardrails,
    process_prompt,
)
from UserPromptSubmit_modules.base import HookContext
from UserPromptSubmit_modules.registry import HOOKS, HOOK_PRIORITY


class TestDesignIntentDetection:
    """Test detection of design/implementation intent patterns."""

    def test_action_verbs_with_implementation_objects(self):
        """Action verbs + implementation objects should trigger guardrails."""
        design_prompts = [
            "we need to build a hook that detects X",
            "let's implement a new feature for the system",
            "design a skill to handle Y",
            "create a module package for the CLI",
            "architect a service for data processing",
            "develop a command to automate this",
            "add a function to calculate metrics",
            "make a class for user management",
        ]
        for prompt in design_prompts:
            result = process_prompt({"prompt": prompt})
            assert result.get("additionalContext") == COGNITIVE_GUARDRAILS_INJECTION, f"Should trigger: {prompt}"

    def test_planning_approach_framing(self):
        """Planning/approach framing should trigger guardrails."""
        planning_prompts = [
            "how should we implement this feature",
            "how should we design the solution",
            "we need to create a new workflow",
            "we need to implement the data pipeline",
            "how should I build this hook",
            "what's the best way to approach the problem",  # Ends with "approach"
            "we need to add a new function",  # Ends with "add"
        ]
        for prompt in planning_prompts:
            result = process_prompt({"prompt": prompt})
            assert result.get("additionalContext") == COGNITIVE_GUARDRAILS_INJECTION, f"Should trigger: {prompt}"

    def test_explicit_skill_invocations(self):
        """Explicit design skill invocations should trigger guardrails."""
        skill_prompts = [
            "/arch some architecture task",
            "/code fix the bug in router.py",
            "/planning create implementation plan",
            "/adf analyze this system",
            "/prd write requirements document",
            "/tdd implement the feature",
            "/feature-dev design the component",
        ]
        for prompt in skill_prompts:
            result = process_prompt({"prompt": prompt})
            assert result.get("additionalContext") == COGNITIVE_GUARDRAILS_INJECTION, f"Should trigger: {prompt}"


class TestNegativeCases:
    """Test that non-design queries do NOT trigger guardrails."""

    def test_non_design_queries(self):
        """Simple queries without design intent should not trigger."""
        non_design_prompts = [
            "what does frameguard_classifier.py do",
            "list all hooks in the registry",
            "show me the hook configuration",
            "how do I run pytest",
            "what is the current directory",
            "explain the regex pattern",
            "read the file at line 42",
        ]
        for prompt in non_design_prompts:
            result = process_prompt({"prompt": prompt})
            assert result.get("additionalContext") is None, f"Should NOT trigger: {prompt}"

    def test_code_analysis_without_design_intent(self):
        """Code analysis without implementation intent should not trigger."""
        analysis_prompts = [
            "analyze the cognitive_guardrails function",
            "review the regex patterns in the hook",
            "check the hook priority settings",
            "examine the env var configuration",
        ]
        for prompt in analysis_prompts:
            result = process_prompt({"prompt": prompt})
            assert result.get("additionalContext") is None, f"Should NOT trigger: {prompt}"

    def test_general_questions(self):
        """General questions should not trigger."""
        general_prompts = [
            "what is the weather today",
            "tell me a joke",
            "how are you doing",
            "what time is it",
            "who are you",
        ]
        for prompt in general_prompts:
            result = process_prompt({"prompt": prompt})
            assert result.get("additionalContext") is None, f"Should NOT trigger: {prompt}"


class TestEdgeCases:
    """Test edge cases for input handling."""

    def test_empty_input(self):
        """Empty input should not trigger."""
        result = process_prompt({"prompt": ""})
        assert result.get("additionalContext") is None

    def test_none_prompt_field(self):
        """None prompt field should not crash (str(None) = 'None')."""
        result = process_prompt({"prompt": None, "message": None})
        # 'None' string doesn't match any pattern, so no trigger
        assert result.get("additionalContext") is None

    def test_input_truncation(self):
        """Input exceeding MAX_QUERY_LENGTH should be truncated."""
        # Create input longer than MAX_QUERY_LENGTH
        long_input = "design a " + "feature " * 1000  # Much longer than 10000 chars
        result = process_prompt({"prompt": long_input})
        # Should still trigger (truncated input still contains "design a feature")
        assert result.get("additionalContext") == COGNITIVE_GUARDRAILS_INJECTION

    def test_exact_length_limit(self):
        """Input with trigger BEFORE limit should still trigger."""
        # Place "design a hook" early (before any truncation could occur)
        prefix = "design a hook and " + "x" * 50  # ~65 chars
        suffix = "y" * (MAX_QUERY_LENGTH - len(prefix))  # Fill to just under limit
        exact_length_input = prefix + suffix
        result = process_prompt({"prompt": exact_length_input})
        assert result.get("additionalContext") == COGNITIVE_GUARDRAILS_INJECTION

    def test_case_insensitive_matching(self):
        """Patterns should be case-insensitive (?i flag)."""
        case_variants = [
            "DESIGN A HOOK",
            "Design a Hook",
            "design A hook",
            "DESIGN a hook",
        ]
        for prompt in case_variants:
            result = process_prompt({"prompt": prompt})
            assert result.get("additionalContext") == COGNITIVE_GUARDRAILS_INJECTION

    def test_whitespace_variations(self):
        """Patterns should handle various whitespace (except LF at word boundaries)."""
        # NOTE: \b word boundary doesn't work after \n (LF) character
        # CR (\r) alone works, but \r\n (CRLF) and \n (LF) break the word boundary
        whitespace_variants = [
            "design  a hook",      # multiple spaces
            "design   a   hook",   # even more spaces
            "design\t a hook",     # tab character
            "design\r hook",       # CR only (works)
        ]
        for prompt in whitespace_variants:
            result = process_prompt({"prompt": prompt})
            assert result.get("additionalContext") == COGNITIVE_GUARDRAILS_INJECTION


class TestEnvironmentVariableGating:
    """Test COGNITIVE_GUARDRAILS_ENABLED environment variable."""

    def test_enabled_by_default(self):
        """Hook should be enabled by default (true)."""
        assert COGNITIVE_GUARDRAILS_ENABLED is True

    def test_env_var_disables_hook(self):
        """When env var is false, hook should not trigger."""
        # Save original value
        original = os.environ.get("COGNITIVE_GUARDRAILS_ENABLED")

        try:
            os.environ["COGNITIVE_GUARDRAILS_ENABLED"] = "false"
            # Re-import to pick up new env var
            import importlib
            import UserPromptSubmit_modules.cognitive_guardrails as cg_module
            importlib.reload(cg_module)

            result = cg_module.process_prompt({"prompt": "design a hook"})
            assert result.get("additionalContext") is None, "Should be disabled"
        finally:
            # Restore original value
            if original is not None:
                os.environ["COGNITIVE_GUARDRAILS_ENABLED"] = original
            else:
                os.environ.pop("COGNITIVE_GUARDRAILS_ENABLED", None)

    def test_env_var_case_insensitive(self):
        """Env var should be case-insensitive (TRUE, True, true)."""
        # Save original value
        original = os.environ.get("COGNITIVE_GUARDRAILS_ENABLED")

        try:
            for variant in ["TRUE", "True", "true", "TrUe"]:
                os.environ["COGNITIVE_GUARDRAILS_ENABLED"] = variant
                # Re-import to pick up new env var
                import importlib
                import UserPromptSubmit_modules.cognitive_guardrails as cg_module
                importlib.reload(cg_module)

                assert cg_module.COGNITIVE_GUARDRAILS_ENABLED is True, f"Variant {variant} should enable"
        finally:
            # Restore original value
            if original is not None:
                os.environ["COGNITIVE_GUARDRAILS_ENABLED"] = original


class TestHookRegistration:
    """Test hook registration and priority."""

    def test_hook_registered(self):
        """Hook should be registered in the HOOKS dict."""
        assert "cognitive_guardrails" in HOOKS, "Hook should be registered"

    def test_hook_priority(self):
        """Hook should have priority 2.0."""
        assert HOOK_PRIORITY.get("cognitive_guardrails") == 2.0, "Priority should be 2.0"

    def test_hook_function_exists(self):
        """Hook function should be callable."""
        assert callable(HOOKS["cognitive_guardrails"]), "Hook should be callable"


class TestPatternsPrecompiled:
    """Test that regex patterns are precompiled at module load."""

    def test_patterns_are_compiled(self):
        """All DESIGN_INTENT_PATTERNS should be compiled regex objects."""
        for pattern in DESIGN_INTENT_PATTERNS:
            assert hasattr(pattern, "pattern"), f"Pattern should be compiled: {pattern}"
            assert hasattr(pattern, "search"), f"Pattern should have search method: {pattern}"


class TestLegacyCompatibility:
    """Test legacy process_prompt function for direct invocation."""

    def test_legacy_entry_point_with_dict(self):
        """Legacy entry point should work with dict input."""
        data = {"prompt": "design a hook"}
        result = process_prompt(data)
        assert result.get("additionalContext") == COGNITIVE_GUARDRAILS_INJECTION

    def test_legacy_entry_point_with_message(self):
        """Legacy entry point should work with message field."""
        data = {"message": "implement a feature"}
        result = process_prompt(data)
        assert result.get("additionalContext") == COGNITIVE_GUARDRAILS_INJECTION

    def test_legacy_entry_point_empty_input(self):
        """Legacy entry point with empty input should return empty dict."""
        result = process_prompt({})
        assert result == {}


class TestReDoSProtection:
    """Test that patterns are safe from ReDoS attacks."""

    def test_pattern_has_quantifier_limit(self):
        """Pattern 1 should use {0,50}? quantifier (not larger ranges)."""
        # Only pattern 1 (action verbs + objects) needs the quantifier
        # Patterns 2 and 3 have different structures (specific phrases, skill invocations)
        pattern = DESIGN_INTENT_PATTERNS[0]
        pattern_str = pattern.pattern
        assert ".{0,50}?" in pattern_str, f"Pattern 1 should use {{0,50}}?: {pattern_str}"

    def test_lazy_quantifier_prevents_backtracking(self):
        """Lazy quantifier should prevent catastrophic backtracking."""
        # Pattern with word boundaries and lazy quantifier
        tricky_input = "\\b" + "a" * 49 + "\\b" + "hook"
        result = process_prompt({"prompt": tricky_input})
        # Should complete without hanging (pattern doesn't match because \b\a\b is invalid)
        assert result.get("additionalContext") is None


class TestInjectionContent:
    """Test that the injected content contains expected text."""

    def test_injection_contains_discovery_mandate(self):
        """Injection should contain DISCOVERY MANDATE."""
        result = process_prompt({"prompt": "design a hook"})
        injection = result.get("additionalContext", "")
        assert "DISCOVERY MANDATE" in injection
        assert "Search for existing implementations first" in injection

    def test_injection_contains_generalization_check(self):
        """Injection should contain GENERALIZATION CHECK."""
        result = process_prompt({"prompt": "design a hook"})
        injection = result.get("additionalContext", "")
        assert "GENERALIZATION CHECK" in injection
        assert "problem CLASS" in injection or "problem class" in injection
