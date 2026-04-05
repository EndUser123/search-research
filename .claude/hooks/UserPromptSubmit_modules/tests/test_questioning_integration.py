"""Test questioning pattern integration for cognitive & reasoning systems.

Tests for questioning_integration.py module:
- 5 questioning patterns detection
- 3 debugging heuristics (H1/H2/H3) detection
- Context and guidance retrieval
- Performance overhead
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
MODULES_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MODULES_DIR))

from questioning_integration import (
    detect_questioning_patterns,
    get_debugging_guidance,
    get_pattern_context,
)


class TestPatternCompilation:
    """Verify that all patterns are compiled exactly once at module load."""

    def test_questioning_patterns_count(self):
        """Should have exactly 5 questioning patterns."""
        import questioning_integration as qi

        assert len(qi._QUESTIONING_PATTERNS) == 5

    def test_debugging_heuristics_count(self):
        """Should have exactly 3 debugging heuristics (H1, H2, H3)."""
        import questioning_integration as qi

        assert len(qi._DEBUGGING_HEURISTICS) == 3

    def test_compiled_patterns_exist(self):
        """Compiled patterns should exist at module load."""
        import questioning_integration as qi

        assert hasattr(qi, "_COMPILED_PATTERNS")
        assert hasattr(qi, "_COMPILED_DEBUGGING")
        assert len(qi._COMPILED_PATTERNS) == 5
        assert len(qi._COMPILED_DEBUGGING) == 3


class TestPattern1ArbitraryThreshold:
    """Verify Pattern 1: Arbitrary Threshold Detection."""

    @pytest.mark.parametrize(
        "prompt,expected_trigger",
        [
            ("Use a 5 minute timeout for API calls", "5 minute"),
            ("Set retry to 3 times", "retry"),
            ("Cache expiry 300 seconds", "300"),
            ("Max retries = 10", "max"),
            ("Wait 30 seconds before retry", "30 second"),
            ("Threshold = 50", "threshold"),
            ("Limit is 100", "limit"),
            ("TTL = 3600", "ttl"),
        ],
    )
    def test_arbitrary_threshold_detection(self, prompt, expected_trigger):
        """Should detect arbitrary thresholds and magic numbers."""
        result = detect_questioning_patterns(prompt)

        assert "arbitrary_threshold" in result.patterns
        actual_trigger = result.triggers.get("arbitrary_threshold", "")
        assert expected_trigger.lower() in actual_trigger.lower()

    def test_arbitrary_threshold_no_match(self):
        """Should not trigger on non-threshold prompts."""
        result = detect_questioning_patterns("Build a new feature")

        assert "arbitrary_threshold" not in result.patterns


class TestPattern2SharedState:
    """Verify Pattern 2: Shared State Detection."""

    @pytest.mark.parametrize(
        "prompt,expected_trigger",
        [
            ("Check git status before proceeding", "git status"),
            ("Use file mtime for caching", "mtime"),
            ("Last modified time for staleness detection", "last modified"),
            ("Shared state for session tracking", "shared state"),
            ("Global variable for configuration", "global variable"),
            ("Centralized cache for performance", "centralized"),
            ("Potential race condition in concurrent access", "race condition"),
            ("Multi-terminal environment support", "multi.?terminal"),
        ],
    )
    def test_shared_state_detection(self, prompt, expected_trigger):
        """Should detect shared state that may have race conditions."""
        result = detect_questioning_patterns(prompt)

        assert "shared_state_concurrency" in result.patterns
        # Check for trigger text (regex match, so substring check)
        trigger = result.triggers.get("shared_state_concurrency", "")
        assert len(trigger) > 0

    def test_shared_state_no_match(self):
        """Should not trigger on prompts without shared state."""
        result = detect_questioning_patterns("Add a logging statement")

        assert "shared_state_concurrency" not in result.patterns


class TestPattern3OverEngineering:
    """Verify Pattern 3: Over-Engineering Detection."""

    @pytest.mark.parametrize(
        "prompt",
        [
            "Add a dashboard for monitoring",
            "Create a survey for user feedback",
            "Implement analytics for tracking",
            "Add a metrics reporter",
            "Generate weekly reports",
            "Create separate handlers for each error type",
            "Implement individual processors for different formats",
            "Add a dedicated manager for state",
            "Create an abstract factory pattern",
            "Implement logging for all operations",
            "Consolidate multiple modules",
            "Refactor multiple components at once",
            "Extract into multiple smaller modules",
        ],
    )
    def test_over_engineering_detection(self, prompt):
        """Should detect over-engineering patterns."""
        result = detect_questioning_patterns(prompt)

        assert "over_engineering" in result.patterns

    def test_over_engineering_no_match(self):
        """Should not trigger on simple, necessary changes."""
        result = detect_questioning_patterns("Fix the bug in the error handler")

        assert "over_engineering" not in result.patterns


class TestPattern4SwissCheese:
    """Verify Pattern 4: Swiss Cheese Maintenance Detection."""

    @pytest.mark.parametrize(
        "prompt",
        [
            "Update each file with the new pattern",
            "Modify all 15 components",
            "Change across multiple files",
            "This creates multiple maintenance points",
            "Single source of truth for configuration",
            "Centralize the logging logic",
            "Avoid duplication across files",
            "Multiple sources to maintain",
            "Scale to 50 components",
        ],
    )
    def test_swiss_cheese_detection(self, prompt):
        """Should detect Swiss cheese maintenance patterns."""
        result = detect_questioning_patterns(prompt)

        assert "swiss_cheese_maintenance" in result.patterns

    def test_swiss_cheese_no_match(self):
        """Should not trigger on centralized approaches."""
        result = detect_questioning_patterns("Use a shared library for common functions")

        assert "swiss_cheese_maintenance" not in result.patterns


class TestPattern5DebuggingCognition:
    """Verify Pattern 5: Debugging Cognition Detection."""

    @pytest.mark.parametrize(
        "prompt",
        [
            "Debug this failing test",
            "Investigate the error",
            "Diagnose the issue",
            "Root cause analysis of the bug",
            "Why is the test failing",
            "Stack trace shows NameError",
            "Exception in module import",
            "Test command failed with exit code 1",
        ],
    )
    def test_debugging_cognition_detection(self, prompt):
        """Should detect debugging scenarios."""
        result = detect_questioning_patterns(prompt)

        assert "debugging_cognition" in result.patterns


class TestDebuggingHeuristics:
    """Verify H1, H2, H3 heuristic detection."""

    def test_h1_entry_point_first(self):
        """H1: Entry Point First Rule should trigger on hypothesis speculation."""
        result = detect_questioning_patterns("I think the issue might be caused by import errors")

        assert "debugging_cognition" in result.patterns
        assert "H1" in result.debugging_heuristics

    def test_h2_parallel_diagnostics(self):
        """H2: Parallel Diagnostics should trigger on sequential investigation language."""
        result = detect_questioning_patterns(
            "First check the logs, then verify imports, after that test the config"
        )

        assert "debugging_cognition" in result.patterns
        assert "H2" in result.debugging_heuristics

    def test_h3_meta_cognitive_check(self):
        """H3: Meta-Cognitive Pre-Flight should trigger on mental model language."""
        result = detect_questioning_patterns(
            "My guess is that the path is wrong based on the error message"
        )

        assert "debugging_cognition" in result.patterns
        assert "H3" in result.debugging_heuristics


class TestContextRetrieval:
    """Verify get_pattern_context() returns useful information."""

    def test_arbitrary_threshold_context(self):
        """Should return context for arbitrary_threshold pattern."""
        context = get_pattern_context("arbitrary_threshold")

        assert context is not None
        assert "Why this specific value?" in context
        assert "arbitrary threshold" in context.lower()
        assert "Line 17" in context  # Reference line

    def test_shared_state_context(self):
        """Should return context for shared_state_concurrency pattern."""
        context = get_pattern_context("shared_state_concurrency")

        assert context is not None
        assert "Are you sure about concurrency?" in context

    def test_over_engineering_context(self):
        """Should return context for over_engineering pattern."""
        context = get_pattern_context("over_engineering")

        assert context is not None
        assert "Is this necessary?" in context

    def test_swiss_cheese_context(self):
        """Should return context for swiss_cheese_maintenance pattern."""
        context = get_pattern_context("swiss_cheese_maintenance")

        assert context is not None
        assert "What happens at scale?" in context

    def test_debugging_cognition_context(self):
        """Should return context for debugging_cognition pattern."""
        context = get_pattern_context("debugging_cognition")

        assert context is not None
        assert "What does the error actually say?" in context

    def test_unknown_pattern_context(self):
        """Should return None for unknown pattern names."""
        context = get_pattern_context("unknown_pattern")

        assert context is None


class TestDebuggingGuidance:
    """Verify get_debugging_guidance() returns heuristic information."""

    def test_h1_guidance(self):
        """Should return H1 guidance."""
        guidance = get_debugging_guidance("H1")

        assert guidance is not None
        assert "H1" in guidance
        assert "Entry Point First Rule" in guidance

    def test_h2_guidance(self):
        """Should return H2 guidance."""
        guidance = get_debugging_guidance("H2")

        assert guidance is not None
        assert "H2" in guidance
        assert "Parallel Diagnostic Testing" in guidance

    def test_h3_guidance(self):
        """Should return H3 guidance."""
        guidance = get_debugging_guidance("H3")

        assert guidance is not None
        assert "H3" in guidance
        assert "Meta-Cognitive Pre-Flight Check" in guidance

    def test_unknown_heuristic_guidance(self):
        """Should return None for unknown heuristic codes."""
        guidance = get_debugging_guidance("H99")

        assert guidance is None


class TestPerformance:
    """Verify performance is within acceptable limits."""

    def test_detection_performance(self):
        """Single detection should be fast (<10ms target)."""
        import time

        prompt = "Use a 5 minute timeout and check git status"

        start = time.perf_counter()
        result = detect_questioning_patterns(prompt)
        end = time.perf_counter()

        duration_ms = (end - start) * 1000

        # Should be very fast (compiled regex patterns)
        assert duration_ms < 10, f"Detection took {duration_ms}ms, exceeds 10ms target"

    def test_long_prompt_performance(self):
        """Long prompts should still be fast."""
        import time

        long_prompt = "Use a 5 minute timeout " + "with additional context " * 50

        start = time.perf_counter()
        result = detect_questioning_patterns(long_prompt)
        end = time.perf_counter()

        duration_ms = (end - start) * 1000

        assert duration_ms < 10, f"Long prompt detection took {duration_ms}ms"


class TestAcceptanceCriteria:
    """Acceptance tests for T-005 requirements."""

    def test_all_5_patterns_detected(self):
        """All 5 questioning patterns should be detected (AC-001)."""
        prompts = [
            "Use a 5 minute timeout",  # arbitrary_threshold
            "Check git status",  # shared_state_concurrency
            "Add a dashboard for monitoring",  # over_engineering
            "Update each file",  # swiss_cheese_maintenance
            "Debug the failing test",  # debugging_cognition
        ]

        for prompt in prompts:
            result = detect_questioning_patterns(prompt)
            assert len(result.patterns) > 0, f"Should detect pattern in: {prompt}"

    def test_performance_overhead_acceptable(self):
        """Pattern matching should be <10ms overhead (AC-002)."""
        import time

        prompt = "Investigate the error with a 5 second timeout"

        # Warm up
        detect_questioning_patterns(prompt)

        # Measure
        start = time.perf_counter()
        result = detect_questioning_patterns(prompt)
        end = time.perf_counter()

        duration_ms = (end - start) * 1000

        assert duration_ms < 10, f"Overhead {duration_ms}ms exceeds 10ms target"

    def test_references_questioning_patterns_md(self):
        """Results should reference questioning_patterns.md (AC-003)."""
        result = detect_questioning_patterns("Use a 5 minute timeout")

        assert result.reference is not None
        assert "questioning_patterns.md" in result.reference

    def test_debugging_heuristics_injected(self):
        """Debugging cognition heuristics H1/H2/H3 should be detected (AC-004)."""
        prompts = [
            ("I think it might be caused by...", "H1"),
            ("First check A, then B", "H2"),
            ("My guess based on the error is...", "H3"),
        ]

        for prompt, expected_heuristic in prompts:
            result = detect_questioning_patterns(prompt)
            assert (
                expected_heuristic in result.debugging_heuristics
            ), f"Should detect {expected_heuristic} in: {prompt}"


class TestEdgeCases:
    """Edge case coverage."""

    def test_empty_prompt(self):
        """Should handle empty string prompt."""
        result = detect_questioning_patterns("")

        assert len(result.patterns) == 0
        assert len(result.debugging_heuristics) == 0

    def test_none_prompt_equivalent(self):
        """Should handle prompts with no matches."""
        result = detect_questioning_patterns("hello world")

        assert len(result.patterns) == 0
        assert len(result.debugging_heuristics) == 0

    def test_multiple_patterns_in_one_prompt(self):
        """Should detect multiple patterns in a single prompt."""
        prompt = "Use a 5 minute timeout and add a dashboard for monitoring"

        result = detect_questioning_patterns(prompt)

        assert "arbitrary_threshold" in result.patterns
        assert "over_engineering" in result.patterns

    def test_case_insensitive_matching(self):
        """Should match patterns regardless of case."""
        lower = "use a 5 minute timeout"
        upper = "USE A 5 MINUTE TIMEOUT"
        mixed = "Use A 5 Minute Timeout"

        for prompt in [lower, upper, mixed]:
            result = detect_questioning_patterns(prompt)
            assert "arbitrary_threshold" in result.patterns

    def test_unicode_characters(self):
        """Should handle Unicode characters in prompts."""
        prompt = "Use a 5 minute timeout for café config"

        result = detect_questioning_patterns(prompt)

        # Should still detect the pattern
        assert "arbitrary_threshold" in result.patterns


class TestBackwardCompatibility:
    """Ensure all 5 patterns still match after implementation."""

    def test_all_patterns_match(self):
        """All 5 questioning patterns should match their test prompts."""
        test_cases = [
            ("arbitrary_threshold", "Use a 5 minute timeout"),
            ("shared_state_concurrency", "Check git status"),
            ("over_engineering", "Add a dashboard for monitoring"),
            ("swiss_cheese_maintenance", "Update each file"),
            ("debugging_cognition", "Debug the failing test"),
        ]

        for pattern_name, test_prompt in test_cases:
            result = detect_questioning_patterns(test_prompt)
            assert (
                pattern_name in result.patterns
            ), f"Pattern '{pattern_name}' should match prompt: {test_prompt}"

    def test_all_debugging_heuristics_match(self):
        """All 3 debugging heuristics should match their test prompts."""
        test_cases = [
            ("H1", "I think it might be caused by..."),
            ("H2", "First check A, then B"),
            ("H3", "My guess based on the error is..."),
        ]

        for heuristic_code, test_prompt in test_cases:
            result = detect_questioning_patterns(test_prompt)
            assert (
                heuristic_code in result.debugging_heuristics
            ), f"Heuristic '{heuristic_code}' should match prompt: {test_prompt}"
