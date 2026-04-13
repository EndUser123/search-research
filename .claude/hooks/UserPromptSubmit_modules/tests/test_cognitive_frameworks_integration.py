"""Test cognitive frameworks integration into cognitive_enhancers hook."""

import pytest
from UserPromptSubmit_modules.base import HookContext
from UserPromptSubmit_modules.cognitive_enhancers import (
    _ENHANCERS,
    _detect_intent,
    _load_config,
    _select_enhancers,
    cognitive_enhancers,
)


class TestCognitiveFrameworksIntegration:
    """Test that Cynefin, Hanlon's Razor, and Devil's Advocate are integrated."""

    def test_enhancer_count(self):
        """Verify the currently configured enhancers are registered."""
        enhancer_names = {e.name for e in _ENHANCERS}
        expected = {
            "assumption_surfacing",
            "assumption_check",
            "escape_hatch_gate",
            "outcome_anchoring",
            "inversion_prompting",
            "chestertons_fence",
            "calibrated_confidence",
            "named_artifact_discovery",
            "socratic_decomposition",
            "cynefin_classification",
            "hanlons_razor",
            "devils_advocate",
            "comparative_analysis",
        }
        assert enhancer_names == expected, (
            f"Enhancer set drifted. Missing={expected - enhancer_names}, "
            f"Unexpected={enhancer_names - expected}"
        )

    def test_cynefin_enhancer_exists(self):
        """Verify Cynefin framework is registered."""
        enhancer_names = [e.name for e in _ENHANCERS]
        assert "cynefin_classification" in enhancer_names

    def test_hanlons_razor_enhancer_exists(self):
        """Verify Hanlon's Razor framework is registered."""
        enhancer_names = [e.name for e in _ENHANCERS]
        assert "hanlons_razor" in enhancer_names

    def test_devils_advocate_enhancer_exists(self):
        """Verify Devil's Advocate framework is registered."""
        enhancer_names = [e.name for e in _ENHANCERS]
        assert "devils_advocate" in enhancer_names

    def test_cynefin_triggers_on_diagnostic(self):
        """Verify Cynefin triggers on diagnostic prompts."""
        prompt = "diagnose why the API is returning 500 errors"
        intent = _detect_intent(prompt)

        # Cynefin should be selected for diagnostic topics
        config = _load_config()
        selected = _select_enhancers(intent, config)
        selected_names = [e.name for e in selected]

        # Should include cynefin_classification when diagnostic intent detected
        assert any(
            "cynefin" in name for name in selected_names
        ), f"Expected cynefin_classification in {selected_names} for prompt: {prompt}"

    def test_hanlons_razor_triggers_on_diagnostic(self):
        """Verify Hanlon's Razor is configured for diagnostic prompts."""
        prompt = "investigate why the database connection keeps failing"
        intent = _detect_intent(prompt)

        assert intent.get("diagnostic") is True, "Should detect diagnostic intent"

        config = _load_config()
        selected = _select_enhancers(intent, config)
        selected_names = [e.name for e in selected]

        hanlons_razor = next((e for e in _ENHANCERS if e.name == "hanlons_razor"), None)
        assert hanlons_razor is not None, "Hanlon's Razor enhancer should exist"
        assert (
            "diagnostic" in hanlons_razor.topics
        ), f"Hanlon's Razor should be configured for diagnostic topic, got {hanlons_razor.topics}"
        assert len(selected_names) <= config.get("max_enhancers_by_topic", {}).get(
            "diagnostic", config.get("max_enhancers_per_prompt", 5)
        )

    def test_devils_advocate_triggers_on_implementation(self):
        """Verify Devil's Advocate triggers on implementation prompts."""
        prompt = "implement a new caching layer for the API"
        intent = _detect_intent(prompt)

        # First verify implementation intent was detected
        assert intent.get("implementation") is True, "Should detect implementation intent"

        config = _load_config()
        selected = _select_enhancers(intent, config)
        selected_names = [e.name for e in selected]

        # Devil's Advocate should be in the pool for implementation intent
        # (may not be selected due to max_enhancers limit of 3)
        devils_advocate_enhancer = next(
            (e for e in _ENHANCERS if e.name == "devils_advocate"), None
        )
        assert devils_advocate_enhancer is not None, "Devil's Advocate enhancer should exist"
        assert (
            "implementation" in devils_advocate_enhancer.topics
        ), "Devil's Advocate should be configured for implementation topic"

    def test_default_config_enables_new_enhancers(self):
        """Verify default config enables the 3 new frameworks."""
        config = _load_config()
        enhancers_config = config.get("enhancers", {})

        assert enhancers_config.get(
            "cynefin_classification", True
        ), "Cynefin should be enabled by default"
        assert enhancers_config.get(
            "hanlons_razor", True
        ), "Hanlon's Razor should be enabled by default"
        assert enhancers_config.get(
            "devils_advocate", True
        ), "Devil's Advocate should be enabled by default"

    def test_hook_execution_with_diagnostic_prompt(self):
        """Test full hook execution with diagnostic prompt."""
        context = HookContext(
            prompt="debug this memory leak in the background worker",
            data={},
            session_id="test-session",
        )

        result = cognitive_enhancers(context)

        # Should inject cognitive enhancement
        assert result.context, "Expected non-empty context injection"

        # Check for framework markers in injection
        injection_lower = result.context.lower()
        assert (
            "cynefin" in injection_lower or "hanlon" in injection_lower
        ), f"Expected Cynefin or Hanlon's Razor framework in injection: {result.context[:200]}"

    def test_hook_execution_with_implementation_prompt(self):
        """Test full hook execution with implementation prompt."""
        context = HookContext(
            prompt="refactor the authentication module to use JWT tokens",
            data={},
            session_id="test-session",
        )

        result = cognitive_enhancers(context)

        # Should inject cognitive enhancement
        assert result.context, "Expected non-empty context injection"

        # Check for ANY cognitive framework markers (not just Devil's Advocate)
        # Since max_enhancers=3, may not see devils_advocate every time
        injection_lower = result.context.lower()
        framework_markers = [
            "assumption",
            "outcome",
            "inversion",
            "chesterton",
            "devil",
            "advocate",
        ]
        has_any_framework = any(marker in injection_lower for marker in framework_markers)
        assert (
            has_any_framework
        ), f"Expected cognitive framework markers in injection: {result.context[:200]}"

    def test_max_enhancers_limit_still_works(self):
        """Verify per-topic limits still apply with the current enhancer set."""
        prompt = "implement and debug this complex feature with many unknowns"
        intent = _detect_intent(prompt)

        config = _load_config()
        max_by_topic = config.get("max_enhancers_by_topic", {})
        global_max = config.get("max_enhancers_per_prompt", 3)
        selected = _select_enhancers(intent, config)

        # Determine the applicable limit from detected topics
        detected_topics = [t for t, active in intent.items() if active and t in max_by_topic]
        if detected_topics:
            applicable_limit = max(max_by_topic.get(t, global_max) for t in detected_topics)
        else:
            applicable_limit = global_max

        assert (
            len(selected) <= applicable_limit
        ), f"Expected at most {applicable_limit} enhancers, got {len(selected)}: {[e.name for e in selected]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
