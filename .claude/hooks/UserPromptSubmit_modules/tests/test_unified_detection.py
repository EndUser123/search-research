"""Test unified detection engine for cognitive & reasoning systems.

Tests for single-pass pattern matching that consolidates:
- 9 cognitive frameworks (cognitive_enhancers.py)
- 4 reasoning modes (reasoning_mode_selector.py)
- 7 think profiles (think_trigger.py)
"""

from __future__ import annotations

# Import the module we're testing
import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
MODULES_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(MODULES_DIR))

from unified_detection import (
    detect_prompt,
)


class TestPatternCompilation:
    """Verify that all patterns are compiled exactly once at module load."""

    def test_cognitive_framework_patterns_compiled(self):
        """Cognitive framework regex patterns should be compiled at module load."""
        import unified_detection as ud

        # Check that compiled patterns exist
        assert hasattr(ud, "_COMPILED_PATTERNS")
        assert isinstance(ud._COMPILED_PATTERNS, dict)

        # Verify cognitive framework patterns exist
        # (We'll check specific patterns in regression tests)
        assert len(ud._COMPILED_PATTERNS) > 0

    def test_reasoning_mode_patterns_compiled(self):
        """Reasoning mode keyword patterns should be compiled at module load."""
        import unified_detection as ud

        # Should have reasoning mode patterns
        assert "sequential" in str(ud._COMPILED_PATTERNS).lower()

    def test_think_trigger_patterns_compiled(self):
        """Think trigger strong/weak patterns should be compiled at module load."""
        import unified_detection as ud

        # Should have think trigger patterns
        assert "debug_rca" in str(ud._COMPILED_PATTERNS).lower()


class TestCognitiveFrameworksRegression:
    """Verify all 9 cognitive frameworks still match after consolidation.

    Frameworks:
    1. assumption_surfacing
    2. outcome_anchoring
    3. inversion_prompting
    4. chestertons_fence
    5. calibrated_confidence
    6. socratic_decomposition
    7. cynefin_classification
    8. hanlons_razor
    9. devils_advocate
    """

    @pytest.mark.parametrize(
        "prompt,expected_frameworks",
        [
            # Implementation prompts
            (
                "Implement a new feature to add user authentication",
                ["assumption_surfacing", "outcome_anchoring", "inversion_prompting"],
            ),
            (
                "Refactor the database layer to use async patterns",
                ["assumption_surfacing", "chestertons_fence"],
            ),
            (
                "Create a new endpoint for handling file uploads",
                ["assumption_surfacing", "outcome_anchoring"],
            ),
            # Diagnostic prompts
            ("Debug why the test keeps failing intermittently", ["calibrated_confidence"]),
            (
                "Investigate the root cause of the memory leak",
                ["calibrated_confidence", "hanlons_razor"],
            ),
            ("Figure out why the API is returning 500 errors", ["calibrated_confidence"]),
            # Architecture prompts
            (
                "Design a system for handling real-time notifications",
                ["assumption_surfacing", "chestertons_fence"],
            ),
            (
                "Should we use Redis or Memcached for caching?",
                ["assumption_surfacing", "devils_advocate"],
            ),
            # Vague prompts (trigger socratic_decomposition)
            ("How should I build this system?", ["socratic_decomposition"]),
        ],
    )
    def test_framework_detection(self, prompt, expected_frameworks):
        """All cognitive frameworks should match their prompts."""
        result = detect_prompt(prompt)

        # Check that expected frameworks are detected
        for framework in expected_frameworks:
            assert (
                framework in result.matched_frameworks
            ), f"Framework '{framework}' should match prompt: {prompt}"

    def test_framework_implementation_intent(self):
        """Implementation intent should trigger appropriate frameworks."""
        result = detect_prompt("Build a new authentication system")

        # Should trigger implementation frameworks
        assert "assumption_surfacing" in result.matched_frameworks
        assert "outcome_anchoring" in result.matched_frameworks
        assert "inversion_prompting" in result.matched_frameworks

    def test_framework_diagnostic_intent(self):
        """Diagnostic intent should trigger appropriate frameworks."""
        result = detect_prompt("Debug why the test is failing")

        # Should trigger diagnostic frameworks
        assert "calibrated_confidence" in result.matched_frameworks

    def test_framework_no_match(self):
        """Prompts with no intent should return no matches."""
        result = detect_prompt("hello world")

        assert len(result.matched_frameworks) == 0
        assert len(result.matched_modes) == 0
        assert len(result.matched_profiles) == 0


class TestReasoningModesRegression:
    """Verify all 4 reasoning modes still match after consolidation.

    Modes:
    1. sequential
    2. multi_agent
    3. graph
    4. two_stage
    """

    @pytest.mark.parametrize(
        "prompt,expected_mode",
        [
            # Sequential mode (step-by-step)
            ("Implement this feature step by step", "sequential"),
            ("Create a function that does X, then test it", "sequential"),
            ("Build the API endpoint, then wire it to the frontend", "sequential"),
            # Multi-agent mode (multiple perspectives)
            ("Evaluate this approach from multiple perspectives", "multi_agent"),
            ("What are the pros and cons of this design?", "multi_agent"),
            ("Get opinions from different stakeholders", "multi_agent"),
            # Graph mode (branching exploration)
            ("Explore different implementation options", "graph"),
            ("What are the alternative approaches?", "graph"),
            ("Consider multiple paths forward", "graph"),
            # Two-stage mode (reasoning then implementation)
            ("Analyze the problem, then implement the solution", "two_stage"),
            ("Think first, then code", "two_stage"),
            ("Plan the approach, then execute", "two_stage"),
        ],
    )
    def test_reasoning_mode_detection(self, prompt, expected_mode):
        """All reasoning modes should match their prompts."""
        result = detect_prompt(prompt)

        # Check that expected mode is detected
        assert (
            expected_mode in result.matched_modes
        ), f"Mode '{expected_mode}' should match prompt: {prompt}"

    def test_mode_no_match(self):
        """Prompts without reasoning keywords should not match modes."""
        result = detect_prompt("hello world")

        assert len(result.matched_modes) == 0


class TestThinkTriggerRegression:
    """Verify all 7 think profiles still match after consolidation.

    Profiles:
    1. debug_rca
    2. tradeoff_decision
    3. architecture
    4. pre_commit_risk
    5. security_review
    6. performance_analysis
    7. multi_file_refactor
    """

    @pytest.mark.parametrize(
        "prompt,expected_profile",
        [
            # Debug RCA
            ("Debug why the test keeps failing intermittently", "debug_rca"),
            ("Root cause analysis needed", "debug_rca"),
            ("Investigate the intermittent bug", "debug_rca"),
            # Tradeoff decision
            ("Should we use Redis or Memcached?", "tradeoff_decision"),
            ("Pick between option A or option B", "tradeoff_decision"),
            ("Pros and cons of this approach", "tradeoff_decision"),
            # Architecture
            ("Should we split into microservices?", "architecture"),
            ("Design the system architecture", "architecture"),
            ("What are the service boundaries?", "architecture"),
            # Pre-commit risk
            ("About to deploy to production", "pre_commit_risk"),
            ("Pushing to main branch", "pre_commit_risk"),
            ("Shipping this feature to production", "pre_commit_risk"),
            # Security review
            ("SQL injection vulnerability detected", "security_review"),
            ("XSS attack vector", "security_review"),
            ("Security audit needed", "security_review"),
            # Performance analysis
            ("Why is this query slow?", "performance_analysis"),
            ("Investigate performance bottleneck", "performance_analysis"),
            ("Optimize this slow endpoint", "performance_analysis"),
            # Multi-file refactor
            ("Refactor this across multiple files", "multi_file_refactor"),
            ("Restructure across the codebase", "multi_file_refactor"),
            ("Split into multiple modules", "multi_file_refactor"),
        ],
    )
    def test_think_profile_detection(self, prompt, expected_profile):
        """All think profiles should match their prompts."""
        result = detect_prompt(prompt)

        # Check that expected profile is detected
        assert (
            expected_profile in result.matched_profiles
        ), f"Profile '{expected_profile}' should match prompt: {prompt}"

    def test_profile_no_match(self):
        """Prompts without think keywords should not match profiles."""
        result = detect_prompt("hello world")

        assert len(result.matched_profiles) == 0


class TestIntentClassification:
    """Verify intent classification works correctly."""

    def test_implementation_intent(self):
        """Implementation prompts should classify as 'implementation'."""
        result = detect_prompt("Implement a new feature")

        assert result.intent_classification == "implementation"

    def test_diagnostic_intent(self):
        """Diagnostic prompts should classify as 'diagnostic'."""
        result = detect_prompt("Debug why this is failing")

        assert result.intent_classification == "diagnostic"

    def test_no_intent(self):
        """Vague prompts without clear intent should return None."""
        result = detect_prompt("hello world")

        assert result.intent_classification is None


class TestSynergyDetection:
    """Verify synergy detection between frameworks and modes."""

    def test_assumption_surfacing_with_sequential(self):
        """assumption_surfacing + sequential is a valid synergy."""
        result = detect_prompt("Implement this feature step by step while surfacing assumptions")

        # Should detect both
        assert "assumption_surfacing" in result.matched_frameworks
        assert "sequential" in result.matched_modes

        # Should detect synergy
        synergy_found = any(
            s.get("framework") == "assumption_surfacing" and s.get("mode") == "sequential"
            for s in result.synergy_candidates
        )
        assert synergy_found, "assumption_surfacing + sequential synergy should be detected"

    def test_socratic_decomposition_with_multi_agent(self):
        """socratic_decomposition + multi_agent is a valid synergy."""
        result = detect_prompt("Break this down and evaluate from multiple perspectives")

        # Should detect both
        assert "socratic_decomposition" in result.matched_frameworks
        assert "multi_agent" in result.matched_modes

        # Should detect synergy
        synergy_found = any(
            s.get("framework") == "socratic_decomposition" and s.get("mode") == "multi_agent"
            for s in result.synergy_candidates
        )
        assert synergy_found, "socratic_decomposition + multi_agent synergy should be detected"


class TestPerformance:
    """Verify performance is within acceptable limits."""

    def test_single_pass_performance(self):
        """Single detection pass should be fast (<60ms)."""
        import time

        prompt = "Implement a feature with debugging and architecture considerations"

        # Time detection
        start = time.perf_counter()
        result = detect_prompt(prompt)
        end = time.perf_counter()

        duration_ms = (end - start) * 1000

        # Should be very fast (baseline was 0.11ms mean)
        assert duration_ms < 60, f"Detection took {duration_ms}ms, exceeds 60ms threshold"
        # Internal timing should be populated and should not exceed wall-clock timing.
        # Wall-clock includes Python call overhead and test harness noise, so it can be
        # modestly higher than the detector's internal measurement.
        assert result.timing_ms > 0, "timing_ms should be set"
        assert (
            result.timing_ms <= duration_ms + 1.0
        ), f"timing_ms ({result.timing_ms}ms) should not materially exceed wall-clock duration ({duration_ms}ms)"

    def test_long_prompt_performance(self):
        """Long prompts should still be fast."""
        import time

        # 1000 character prompt
        long_prompt = "Implement a feature " + "with detailed requirements " * 50

        start = time.perf_counter()
        result = detect_prompt(long_prompt)
        end = time.perf_counter()

        duration_ms = (end - start) * 1000

        assert (
            duration_ms < 60
        ), f"Long prompt detection took {duration_ms}ms, exceeds 60ms threshold"


class TestBackwardCompatibility:
    """Ensure all existing patterns still match after consolidation."""

    def test_all_frameworks_match(self):
        """All 9 cognitive frameworks should still detect their prompts."""
        frameworks_to_test = [
            ("assumption_surfacing", "implement the feature"),
            ("outcome_anchoring", "what should this do"),
            ("inversion_prompting", "what could break this"),
            ("chestertons_fence", "modify existing code"),
            ("calibrated_confidence", "debug this issue"),
            ("socratic_decomposition", "build a system"),
            ("cynefin_classification", "investigate the problem"),
            ("hanlons_razor", "why is this failing"),
            ("devils_advocate", "evaluate this proposal"),
        ]

        for framework, test_prompt in frameworks_to_test:
            result = detect_prompt(test_prompt)
            assert (
                framework in result.matched_frameworks
            ), f"Framework '{framework}' should match prompt: {test_prompt}"

    def test_all_modes_match(self):
        """All 4 reasoning modes should still detect their prompts."""
        modes_to_test = [
            ("sequential", "do this step by step"),
            ("multi_agent", "get multiple opinions"),
            ("graph", "explore alternatives"),
            ("two_stage", "analyze then implement"),
        ]

        for mode, test_prompt in modes_to_test:
            result = detect_prompt(test_prompt)
            assert mode in result.matched_modes, f"Mode '{mode}' should match prompt: {test_prompt}"

    def test_all_profiles_match(self):
        """All 7 think profiles should still detect their prompts."""
        profiles_to_test = [
            ("debug_rca", "debug the intermittent failure"),
            ("tradeoff_decision", "choose between A and B"),
            ("architecture", "design the system"),
            ("pre_commit_risk", "before deploying to production"),
            ("security_review", "fix the security vulnerability"),
            ("performance_analysis", "optimize the slow query"),
            ("multi_file_refactor", "restructure across files"),
        ]

        for profile, test_prompt in profiles_to_test:
            result = detect_prompt(test_prompt)
            assert (
                profile in result.matched_profiles
            ), f"Profile '{profile}' should match prompt: {test_prompt}"
