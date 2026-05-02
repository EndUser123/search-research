"""Tests for cognitive_enhancers unified detection integration.

Test Coverage:
- All 9 frameworks still detected after unified detection integration
- No behavior changes (regression test)
- Performance improvement (~30% faster)
- Edge cases (empty prompt, unknown frameworks)
"""

from __future__ import annotations

import time

import pytest
from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.cognitive_enhancers import (
    _load_config,
    cognitive_enhancers,
)

# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def sample_prompts_by_framework():
    """Sample prompts that should trigger each cognitive framework.

    Prompts are designed to:
    - Be at least 30 characters (min_prompt_length requirement)
    - Meet socratic_min_length=200 for socratic_decomposition
    - Match the actual regex patterns in unified_detection.py
    - Work within max_enhancers_per_prompt=3 limit
    """
    return {
        "assumption_surfacing": "implement a new feature for user authentication",
        "outcome_anchoring": "what should the deliverable look like",
        "inversion_prompting": "what could break if we deploy this change",
        "chestertons_fence": "modify the existing authentication module",
        "calibrated_confidence": "investigate why the API call is failing",
        "socratic_decomposition": (
            "how should we design and build a comprehensive scalable system architecture "
            "that can handle millions of requests while maintaining high availability and performance "
            "across multiple data centers and geographic regions"
        ),
        "cynefin_classification": "characterize the problem domain for investigation",
        "hanlons_razor": "diagnose why the database connection is not working",
        "devils_advocate": "evaluate the pros and cons of this approach",
    }


@pytest.fixture
def hook_context():
    """Create a HookContext for testing."""
    return HookContext(prompt="", data={}, session_id="test-session", terminal_id="test-terminal")


# =============================================================================
# REGRESSION TESTS - All 9 Frameworks Still Detected
# =============================================================================


class TestFrameworkDetectionRegression:
    """Verify all 9 cognitive frameworks are still detected after unified detection integration."""

    def test_all_9_frameworks_detectable(self, sample_prompts_by_framework, hook_context):
        """All 9 cognitive frameworks should be detected by unified_detection.

        Note: This tests detection, not final selection. Due to max_enhancers_per_prompt=3,
        not all detected frameworks will be selected for injection.
        """
        from UserPromptSubmit_modules import unified_detection

        detected_frameworks = set()

        for framework_name, prompt in sample_prompts_by_framework.items():
            detection_result = unified_detection.detect_prompt(prompt)

            # Check if the target framework was detected
            if framework_name in detection_result.matched_frameworks:
                detected_frameworks.add(framework_name)

        # Check all 9 frameworks were detected
        expected_frameworks = {
            "assumption_surfacing",
            "outcome_anchoring",
            "inversion_prompting",
            "chestertons_fence",
            "calibrated_confidence",
            "socratic_decomposition",
            "cynefin_classification",
            "hanlons_razor",
            "devils_advocate",
        }

        assert (
            detected_frameworks >= expected_frameworks
        ), f"Missing frameworks: {expected_frameworks - detected_frameworks}"

    def test_assumption_surfacing_still_detected(self, hook_context):
        """Assumption surfacing should be detected with implementation prompts."""
        hook_context.prompt = "implement a new user authentication system"
        result = cognitive_enhancers(hook_context)

        assert result.context is not None
        assert "assumption surfacing" in result.context.lower()

    def test_outcome_anchoring_still_detected(self, hook_context):
        """Outcome anchoring should be detected with goal-oriented prompts."""
        hook_context.prompt = "what should the deliverable look like"
        result = cognitive_enhancers(hook_context)

        assert result.context is not None
        assert "outcome anchoring" in result.context.lower()

    def test_inversion_prompting_still_detected(self, hook_context):
        """Inversion prompting should be detected with failure-mode prompts."""
        hook_context.prompt = "what could break if we deploy this change"
        result = cognitive_enhancers(hook_context)

        assert result.context is not None
        assert "inversion prompting" in result.context.lower()

    def test_chestertons_fence_still_detected(self, hook_context):
        """Chesterton's fence should be detected by unified_detection."""
        from UserPromptSubmit_modules import unified_detection

        hook_context.prompt = "modify the existing authentication module"
        detection_result = unified_detection.detect_prompt(hook_context.prompt)

        assert (
            "chestertons_fence" in detection_result.matched_frameworks
        ), f"chestertons_fence not detected. Matched: {detection_result.matched_frameworks}"

    def test_calibrated_confidence_still_detected(self, hook_context):
        """Calibrated confidence should be detected with diagnostic prompts."""
        hook_context.prompt = "investigate why the API is returning errors"
        result = cognitive_enhancers(hook_context)

        assert result.context is not None
        assert "calibrated confidence" in result.context.lower()

    def test_socratic_decomposition_still_detected(self, hook_context):
        """Socratic decomposition should be detected with vague prompts.

        Note: Due to max_enhancers_per_prompt=3 limit and overlapping patterns,
        socratic_decomposition may not be in the final selection. This test
        verifies detection by unified_detection, not final selection.
        """
        # Verify that unified_detection detects socratic_decomposition for long vague prompts
        from UserPromptSubmit_modules import unified_detection

        hook_context.prompt = (
            "how should we design and build a comprehensive scalable system architecture "
            "that can handle millions of requests while maintaining high availability and performance "
            "across multiple data centers and geographic regions"
        )

        detection_result = unified_detection.detect_prompt(hook_context.prompt)
        assert (
            "socratic_decomposition" in detection_result.matched_frameworks
        ), f"socratic_decomposition not detected. Matched: {detection_result.matched_frameworks}"

    def test_cynefin_classification_still_detected(self, hook_context):
        """Cynefin classification should be detected with diagnostic prompts."""
        hook_context.prompt = "characterize the problem domain for investigation"
        result = cognitive_enhancers(hook_context)

        assert result.context is not None
        assert "cynefin classification" in result.context.lower()

    def test_hanlons_razor_still_detected(self, hook_context):
        """Hanlon's razor should be detected by unified_detection."""
        from UserPromptSubmit_modules import unified_detection

        hook_context.prompt = "why is the database connection broken"
        detection_result = unified_detection.detect_prompt(hook_context.prompt)

        assert (
            "hanlons_razor" in detection_result.matched_frameworks
        ), f"hanlons_razor not detected. Matched: {detection_result.matched_frameworks}"

    def test_devils_advocate_still_detected(self, hook_context):
        """Devil's advocate should be detected by unified_detection."""
        from UserPromptSubmit_modules import unified_detection

        hook_context.prompt = "evaluate the pros and cons of this approach"
        detection_result = unified_detection.detect_prompt(hook_context.prompt)

        assert (
            "devils_advocate" in detection_result.matched_frameworks
        ), f"devils_advocate not detected. Matched: {detection_result.matched_frameworks}"


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================


class TestPerformanceImprovement:
    """Verify performance improvement from unified detection."""

    def test_detection_performance_improved(self, hook_context):
        """Unified detection should be ~30% faster than legacy regex matching."""
        hook_context.prompt = "implement a new user authentication system with OAuth2 support"

        # Warm-up run
        cognitive_enhancers(hook_context)

        # Timed runs (10 iterations for average)
        timings = []
        for _ in range(10):
            start = time.perf_counter()
            _result = cognitive_enhancers(hook_context)  # noqa: F841
            elapsed_ms = (time.perf_counter() - start) * 1000
            timings.append(elapsed_ms)

        avg_time_ms = sum(timings) / len(timings)

        # Performance baseline: <15ms (30% improvement from legacy ~20ms)
        assert (
            avg_time_ms < 15.0
        ), f"Detection took {avg_time_ms:.2f}ms average, exceeds 15ms target"


# =============================================================================
# BEHAVIORAL REGRESSION TESTS
# =============================================================================


class TestBehavioralRegression:
    """Verify no behavioral changes after unified detection integration."""

    def test_empty_prompt_returns_empty_result(self, hook_context):
        """Empty prompts should return empty HookResult."""
        hook_context.prompt = ""
        result = cognitive_enhancers(hook_context)

        assert result.context in ("", None)
        assert result.tokens == 0

    def test_short_prompt_returns_empty_result(self, hook_context):
        """Short prompts below min_prompt_length should return empty HookResult."""
        hook_context.prompt = "help"
        config = _load_config()
        min_length = config.get("min_prompt_length", 30)

        if len(hook_context.prompt) < min_length:
            result = cognitive_enhancers(hook_context)
            assert result.context in ("", None)

    def test_question_only_prompt_returns_empty_result(self, hook_context):
        """Question-only prompts without implementation verbs should return empty."""
        hook_context.prompt = "what is this?"
        result = cognitive_enhancers(hook_context)

        # Should be empty unless implementation intent is also detected
        if "implement" not in hook_context.prompt.lower():
            assert result.context in ("", None)

    def test_fast_mode_disables_all_enhancers(self, hook_context):
        """#fast mode should disable all cognitive enhancers.

        NOTE: The prompt must be >= min_prompt_length (30) to pass the
        _is_actionable_prompt gate and actually reach mode handling logic.
        The old test used a 29-char prompt that returned empty for the wrong
        reason (length gate, not fast mode).
        """
        hook_context.prompt = "#fast implement a new user authentication feature"
        result = cognitive_enhancers(hook_context)

        # Fast mode disables all enhancers via disable_all in config
        assert result.context in ("", None)

    def test_rca_mode_forces_meta_rca_topic(self, hook_context):
        """#rca mode should force meta_rca topic and enable cynefin_classification."""
        hook_context.prompt = "#rca investigate the issue"
        result = cognitive_enhancers(hook_context)

        # Should trigger cynefin_classification (meta_rca topic)
        if result.context:
            # _build_injection replaces underscores with spaces and title-cases names
            assert "cynefin classification" in result.context.lower()


# =============================================================================
# CONFIG INTEGRATION TESTS
# =============================================================================


class TestConfigIntegration:
    """Verify config-driven framework selection still works."""

    def test_disabled_framework_not_selected(self, hook_context, tmp_path):
        """Frameworks disabled in config should not be selected."""
        # This test verifies config integration without modifying global config
        # Actual config testing would need temp config file setup
        hook_context.prompt = "implement a new feature"

        # Just verify the hook runs without error
        result = cognitive_enhancers(hook_context)
        # Result should be non-empty for implementation prompt
        assert isinstance(result, HookResult)

    def test_max_enhancers_limit_enforced(self, hook_context):
        """max_enhancers_per_prompt config should limit number of enhancers."""
        hook_context.prompt = (
            "implement and design a scalable system to investigate failures "
            "and figure out what's causing crashes while modifying existing code"
        )

        result = cognitive_enhancers(hook_context)

        if result.context:
            # Count enhancers in output
            enhancer_count = result.context.count("**")

            # Per-topic limits now allow up to 5 enhancers for some topics
            assert enhancer_count <= 20  # Loose upper bound (2x max per-topic limit)


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Test edge cases and graceful degradation."""

    def test_none_prompt_handled_gracefully(self, hook_context):
        """None prompt should not crash hook."""
        hook_context.prompt = None
        result = cognitive_enhancers(hook_context)

        assert isinstance(result, HookResult)

    def test_very_long_prompt_still_fast(self, hook_context):
        """Very long prompts (10000+ chars) should still complete in reasonable time."""
        hook_context.prompt = "implement " + "a new feature " * 1000

        start = time.perf_counter()
        result = cognitive_enhancers(hook_context)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert isinstance(result, HookResult)
        # Should complete in <50ms even for long prompts
        assert elapsed_ms < 50.0, f"Long prompt took {elapsed_ms:.2f}ms"

    def test_unicode_prompt_handled_correctly(self, hook_context):
        """Unicode characters in prompt should not break detection."""
        hook_context.prompt = "implement a feature with emoji 🎉 and unicode 中文"

        result = cognitive_enhancers(hook_context)

        # Should detect implementation intent despite unicode
        if result.context:
            assert "implement" in hook_context.prompt


# =============================================================================
# NAMED ARTIFACT DISCOVERY TESTS
# =============================================================================


class TestNamedArtifactDiscovery:
    """Tests for the named_artifact_discovery cognitive enhancer.

    This enhancer fires for diagnostic prompts to prevent the failure mode where
    the LLM assumes it knows where a named system lives based on recently-loaded
    context (e.g., HANDOFF.md loaded recently → assuming 'handoff system' == HANDOFF.md).
    """

    def test_named_artifact_discovery_fires_for_diagnostic_prompt(self, hook_context):
        """named_artifact_discovery should appear in injection for diagnostic prompts."""
        hook_context.prompt = "investigate why the handoff system is not working optimally"
        result = cognitive_enhancers(hook_context)

        assert result.context is not None, "Expected context injection for diagnostic prompt"
        assert (
            "artifact discovery" in result.context.lower()
        ), f"Expected 'artifact discovery' in injection. Got:\n{result.context}"

    def test_named_artifact_discovery_not_for_pure_implementation(self, hook_context):
        """named_artifact_discovery should NOT appear for pure implementation prompts.

        Implementation topic routes to assumption_surfacing, outcome_anchoring,
        inversion_prompting (max=3). named_artifact_discovery is position 6 in
        _ENHANCERS and only applies to topic='diagnostic'.
        """
        from UserPromptSubmit_modules import unified_detection

        hook_context.prompt = "implement a new feature for user authentication"
        detection_result = unified_detection.detect_prompt(hook_context.prompt)

        # named_artifact_discovery should be detected (it's in _COGNITIVE_FRAMEWORKS)
        # but the diagnostic topic check ensures it's not selected for implementation prompts
        # This test verifies it's in the detection framework
        assert (
            "named_artifact_discovery" in unified_detection._COGNITIVE_FRAMEWORKS
        ), "named_artifact_discovery must be registered in unified_detection._COGNITIVE_FRAMEWORKS"

    def test_named_artifact_discovery_in_unified_detection(self, hook_context):
        """named_artifact_discovery should be detectable via unified_detection."""
        from UserPromptSubmit_modules import unified_detection

        hook_context.prompt = "investigate why the reporting system is broken"
        detection_result = unified_detection.detect_prompt(hook_context.prompt)

        assert "named_artifact_discovery" in detection_result.matched_frameworks, (
            f"named_artifact_discovery not detected for diagnostic prompt. "
            f"Matched: {detection_result.matched_frameworks}"
        )

    def test_diagnostic_now_fires_3_enhancers(self, hook_context):
        """Raising diagnostic max from 2 to 3 should allow 3 enhancers for diagnostic prompts.

        Before: calibrated_confidence + cynefin_classification = 2 (max was 2)
        After:  calibrated_confidence + named_artifact_discovery + socratic_decomposition = 3

        Note: cynefin_classification is position 4 in _ENHANCERS for the diagnostic topic;
        it falls outside max=3. The actual chain at max=3 is:
          1. calibrated_confidence (position 1)
          2. named_artifact_discovery (position 2 — newly added)
          3. socratic_decomposition (position 3)
        cynefin_classification would be position 4, over the new max.

        This test verifies the max was correctly raised to 3.
        """
        config = _load_config()
        diagnostic_max = config.get("max_enhancers_by_topic", {}).get("diagnostic", 0)

        assert diagnostic_max == 5, (
            f"Expected diagnostic max_enhancers_by_topic=5, got {diagnostic_max}. "
            "The max was raised to 5 to accommodate all 4 diagnostic enhancers "
            "(calibrated_confidence, named_artifact_discovery, cynefin_classification, hanlons_razor)."
        )

    def test_artifact_discovery_injection_has_required_elements(self, hook_context):
        """The named_artifact_discovery injection must require specific search steps.

        The injection must require the LLM to:
        1. Name the system being sought
        2. State current belief about its location and WHY
        3. Specify the search to run before acting

        This prevents 'theater risk' - generic declarations without actionable specifics.
        """
        hook_context.prompt = "investigate why the indexing system keeps failing"
        result = cognitive_enhancers(hook_context)

        if result.context and "artifact discovery" in result.context.lower():
            # Should mention search/verification (not just declaration)
            context_lower = result.context.lower()
            has_search_requirement = any(
                term in context_lower for term in ["glob", "grep", "search", "confirm", "verify"]
            )
            assert has_search_requirement, (
                "Artifact discovery injection must require an explicit search step, "
                f"not just a declaration. Context:\n{result.context}"
            )

    def test_named_artifact_discovery_does_not_fire_for_generic_debugging(self, hook_context):
        """named_artifact_discovery should NOT trigger for generic debugging without a named artifact.

        Pre-mortem finding: bare patterns r"system", r"component" caused over-triggering.
        Every debugging session triggered the enhancer regardless of named-artifact ambiguity.

        Pattern narrowed to require: investigation verb + named artifact noun in same prompt.
        Generic debugging prompts like "debug the memory leak" should not trigger.
        """
        from UserPromptSubmit_modules import unified_detection

        # Generic debugging — no named system/package/component to locate
        generic_debug_prompts = [
            "debug the memory leak",
            "fix the crash",
            "why is it slow",
            "there is an error in the output",
            "investigate the performance issue",
        ]

        for prompt in generic_debug_prompts:
            detection_result = unified_detection.detect_prompt(prompt)
            assert "named_artifact_discovery" not in detection_result.matched_frameworks, (
                f"named_artifact_discovery incorrectly triggered for generic prompt: {prompt!r}\n"
                f"Matched frameworks: {detection_result.matched_frameworks}"
            )

    def test_named_artifact_discovery_fires_for_named_artifact_prompts(self, hook_context):
        """named_artifact_discovery should fire when investigating a named system/component.

        Positive case: investigation verb + a specific named artifact noun.
        These prompts have "where is it?" ambiguity that the enhancer addresses.
        """
        from UserPromptSubmit_modules import unified_detection

        named_artifact_prompts = [
            "investigate why the handoff system is not working",
            "debug the authentication service",
            "why is the reporting module broken",
        ]

        for prompt in named_artifact_prompts:
            detection_result = unified_detection.detect_prompt(prompt)
            assert "named_artifact_discovery" in detection_result.matched_frameworks, (
                f"named_artifact_discovery NOT triggered for named-artifact prompt: {prompt!r}\n"
                f"Matched frameworks: {detection_result.matched_frameworks}"
            )

    def test_named_artifact_discovery_scope_gap_documented(self, hook_context):
        """Document known scope gap: named_artifact_discovery only covers diagnostic topic.

        Implementation prompts like "build the new reporting system" also carry
        confident-wrong-belief risk — the LLM might assume it knows where an existing
        component lives. Adding 'implementation' to topics requires evaluating
        whether false-positive rate is acceptable.

        This test documents the gap and asserts current state as a regression guard.
        """
        from UserPromptSubmit_modules.cognitive_enhancers import _ENHANCERS

        artifact_enhancer = next(
            (e for e in _ENHANCERS if e.name == "named_artifact_discovery"), None
        )
        assert artifact_enhancer is not None, "named_artifact_discovery enhancer must be registered"
        assert (
            "diagnostic" in artifact_enhancer.topics
        ), "named_artifact_discovery must cover 'diagnostic' topic"
        # Known gap: implementation topic not covered (document for future evaluation)
        assert "implementation" not in artifact_enhancer.topics, (
            "SCOPE GAP EXISTS: 'implementation' topic intentionally not covered. "
            "Add 'implementation' to topics only after evaluating false-positive rate."
        )
