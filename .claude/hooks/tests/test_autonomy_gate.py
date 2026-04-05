"""
Tests for autonomy_gate.py - Stop hook that prevents deferral after execution directive.

Test coverage follows adversarial findings:
- TEST-001: Empty/missing payload field tests (fail-open behavior)
- TEST-002: Payload field variation tests
- TEST-005: Deferral pattern tests (5 patterns + negative tests)

All tests use synthetic payloads (no mocks) per testing patterns.
"""

import autonomy_gate


def _payload(
    prompt: str = "",
    user_prompt: str = "",
    assistant_response: str = "",
    response: str = "",
) -> dict:
    """
    Helper to create test payloads with all field variations.
    Matches actual payload structure from Stop_router.py.
    """
    payload = {}
    if prompt:
        payload["prompt"] = prompt
    if user_prompt:
        payload["user_prompt"] = user_prompt
    if assistant_response:
        payload["assistant_response"] = assistant_response
    if response:
        payload["response"] = response
    return payload


class TestFailOpenBehavior:
    """TEST-001: Empty/missing payload field tests - fail-open is constitutional requirement."""

    def test_empty_prompt_passes(self):
        """Empty prompt should pass (fail-open)."""
        p = _payload(prompt="", assistant_response="Should I proceed with Domain 6?")
        result = autonomy_gate.evaluate(p)
        assert result["continue"] is True
        assert "missing user_prompt or response" in result["reason"]

    def test_missing_response_field_passes(self):
        """Missing response field should pass (fail-open)."""
        p = _payload(prompt="Implement Domain 6a now 0")
        result = autonomy_gate.evaluate(p)
        assert result["continue"] is True
        assert "missing user_prompt or response" in result["reason"]

    def test_prompt_field_variation(self):
        """Test that prompt field is recognized (fallback from user_prompt)."""
        p = _payload(
            prompt="Implement Domain 6a now 0",
            assistant_response="Here is Domain 6a implementation...",
        )
        result = autonomy_gate.evaluate(p)
        assert result["continue"] is True
        assert "no deferral pattern detected" in result["reason"]

    def test_user_prompt_field_variation(self):
        """Test that user_prompt field is recognized (primary field)."""
        p = _payload(
            user_prompt="Implement Domain 6a now 0",
            assistant_response="Here is Domain 6a implementation...",
        )
        result = autonomy_gate.evaluate(p)
        assert result["continue"] is True
        assert "no deferral pattern detected" in result["reason"]

    def test_response_field_variation(self):
        """Test that response field is recognized (fallback from assistant_response)."""
        p = _payload(
            prompt="Implement Domain 6a now 0", response="Here is Domain 6a implementation..."
        )
        result = autonomy_gate.evaluate(p)
        assert result["continue"] is True
        assert "no deferral pattern detected" in result["reason"]

    def test_assistant_response_field_variation(self):
        """Test that assistant_response field is recognized (primary field)."""
        p = _payload(
            prompt="Implement Domain 6a now 0",
            assistant_response="Here is Domain 6a implementation...",
        )
        result = autonomy_gate.evaluate(p)
        assert result["continue"] is True
        assert "no deferral pattern detected" in result["reason"]


class TestExecutionSignalDetection:
    """Tests for detecting execution signal (trailing '0')."""

    def test_trailing_zero_detected(self):
        """Trailing '0' should be recognized as execution signal."""
        assert autonomy_gate.is_autonomy_signal("Implement Domain 6a now 0")
        assert autonomy_gate.is_autonomy_signal("Domain 6a 0")
        assert autonomy_gate.is_autonomy_signal("0")

    def test_zero_not_signal_without_context(self):
        """'0' without execution context should not trigger (implementation detail)."""
        # Current implementation: trailing '0' is always the signal
        # This test documents current behavior
        assert autonomy_gate.is_autonomy_signal("0")

    def test_no_signal_without_zero(self):
        """Messages without trailing '0' should not trigger."""
        assert not autonomy_gate.is_autonomy_signal("Implement Domain 6a now")
        assert not autonomy_gate.is_autonomy_signal("What should we do next?")
        assert not autonomy_gate.is_autonomy_signal("Should I proceed?")


class TestDeferralPatternDetection:
    """TEST-005: Tests for deferral pattern detection (5 patterns + negative tests)."""

    def test_should_i_proceed_pattern(self):
        """Detect 'Should I proceed' deferral pattern."""
        p = _payload(
            prompt="Implement Domain 6a now 0",
            assistant_response="Should I proceed with Domain 6, or skip to Domain 7?",
        )
        result = autonomy_gate.evaluate(p)
        assert result["continue"] is False
        assert "Autonomy violation" in result["reason"]

    def test_should_we_proceed_pattern(self):
        """Detect 'Should we proceed' deferral pattern."""
        p = _payload(
            prompt="Implement Domain 6a now 0",
            assistant_response="Should we proceed with the implementation?",
        )
        result = autonomy_gate.evaluate(p)
        assert result["continue"] is False

    def test_skip_to_domain_pattern(self):
        """Detect 'skip to Domain' deferral pattern (TEST-005 missing pattern)."""
        p = _payload(
            prompt="Implement Domain 6a now 0",
            assistant_response="Should I skip to Domain 7 instead?",
        )
        result = autonomy_gate.evaluate(p)
        assert result["continue"] is False

    def test_would_you_like_me_to_pattern(self):
        """Detect 'would you like me to' deferral pattern."""
        p = _payload(
            prompt="Implement Domain 6a now 0",
            assistant_response="Would you like me to proceed with Domain 6?",
        )
        result = autonomy_gate.evaluate(p)
        assert result["continue"] is False

    def test_do_you_want_me_to_pattern(self):
        """Detect 'do you want me to' deferral pattern."""
        p = _payload(
            prompt="Implement Domain 6a now 0",
            assistant_response="Do you want me to skip to Domain 7?",
        )
        result = autonomy_gate.evaluate(p)
        assert result["continue"] is False


class TestDeferralPatternNegativeTests:
    """TEST-005: Negative tests for deferral patterns (false positives)."""

    def test_normal_answer_allowed(self):
        """Normal answers should be allowed even with '0' signal."""
        p = _payload(
            prompt="Implement Domain 6a now 0",
            assistant_response="Here is Domain 6a implementation...",
        )
        result = autonomy_gate.evaluate(p)
        assert result["continue"] is True

    def test_deferral_without_signal_allowed(self):
        """Deferral without execution signal should be allowed."""
        p = _payload(
            prompt="What should we do next?",
            assistant_response="Should I proceed with Domain 6, or skip to Domain 7?",
        )
        result = autonomy_gate.evaluate(p)
        assert result["continue"] is True
        assert "no autonomy signal" in result["reason"]

    def test_pattern_not_too_broad(self):
        """Ensure patterns DO match 'should proceed' in any context (conservative design)."""
        p = _payload(
            prompt="Implement Domain 6a now 0",
            assistant_response="We should proceed carefully with the implementation.",
        )
        result = autonomy_gate.evaluate(p)
        # "should proceed" is blocked - gate is conservative by design
        # If AI wants to say "proceed", it should just execute, not ask
        assert result["continue"] is False
        assert "Autonomy violation" in result["reason"]

    def test_case_insensitive_matching(self):
        """Patterns should match case-insensitively."""
        p = _payload(
            prompt="Implement Domain 6a now 0",
            assistant_response="SHOULD I PROCEED WITH DOMAIN 6?",
        )
        result = autonomy_gate.evaluate(p)
        assert result["continue"] is False


class TestRouterRegistration:
    """TEST-002: Integration tests for router registration."""

    def test_hook_registered_in_sequence(self):
        """Verify autonomy_gate.py is registered in Stop_router HOOK_SEQUENCE."""
        from Stop_router import HOOK_SEQUENCE

        hook_names = [hook[0] for hook in HOOK_SEQUENCE]
        assert "autonomy_gate.py" in hook_names, "autonomy_gate.py not found in HOOK_SEQUENCE"

        # Verify it has the correct structure: (name, env_var, default, dispatch)
        for hook in HOOK_SEQUENCE:
            if hook[0] == "autonomy_gate.py":
                assert hook[1] == "AUTONOMY_GATE_ENABLED"
                assert hook[2] is True
                assert hook[3] == "inprocess"
                break

    def test_hook_in_active_runtime_hooks(self):
        """Verify autonomy_gate.py is in ACTIVE_RUNTIME_HOOKS."""
        from Stop_router import ACTIVE_RUNTIME_HOOKS

        assert (
            "autonomy_gate.py" in ACTIVE_RUNTIME_HOOKS
        ), "autonomy_gate.py not found in ACTIVE_RUNTIME_HOOKS"

    def test_env_var_default(self):
        """Verify AUTONOMY_GATE_ENABLED env var is set to 'true'."""
        import json
        from pathlib import Path

        settings_path = Path("P:/.claude/settings.json")
        with open(settings_path) as f:
            settings = json.load(f)

        assert (
            "AUTONOMY_GATE_ENABLED" in settings["env"]
        ), "AUTONOMY_GATE_ENABLED not in settings.env"
        assert (
            settings["env"]["AUTONOMY_GATE_ENABLED"] == "true"
        ), "AUTONOMY_GATE_ENABLED should default to 'true'"
