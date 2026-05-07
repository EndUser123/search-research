#!/usr/bin/env python3
"""Tests for Stop_semantic_critic.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Setup bf_agent path before importing Stop_semantic_critic
_TOOLS_MCP = Path("P:/tools/mcp")
if str(_TOOLS_MCP) not in sys.path:
    sys.path.insert(0, str(_TOOLS_MCP))

import pytest
from Stop_semantic_critic import (
    _is_diagnostic_scope,
    _is_non_substantive,
    parse_semantic_critic_response,
    SemanticCriticResult,
    call_semantic_critic_via_bifrost,
    _session_key,
    _build_critic_user_message,
    CRITIC_SYSTEM_PROMPT,
    CRITIC_PROMPTS,
    _detect_critic_profile,
    REMEDIATION_TEMPLATES,
    _build_remediation_message,
)


# =============================================================================
# parse_semantic_critic_response — pure parsing unit tests
# =============================================================================


class TestParseSemanticCriticResponse:
    """Unit tests for the pure JSON parsing helper."""

    def test_clean_json(self):
        result = parse_semantic_critic_response('{"ok": true, "reason": "looks good"}')
        assert result is not None
        assert result.ok is True
        assert result.reason == "looks good"

    def test_clean_json_false(self):
        result = parse_semantic_critic_response(
            '{"ok": false, "reason": "missing alternatives"}'
        )
        assert result is not None
        assert result.ok is False
        assert result.reason == "missing alternatives"

    def test_json_with_newlines_and_whitespace(self):
        result = parse_semantic_critic_response(
            '  \n  {"ok": true, "reason": "  well reasoned  "}\n\n  '
        )
        assert result is not None
        assert result.ok is True
        assert result.reason == "  well reasoned  "

    def test_json_in_json_fence(self):
        text = '```json\n{"ok": true, "reason": "adequate"}\n```'
        result = parse_semantic_critic_response(text)
        assert result is not None
        assert result.ok is True
        assert result.reason == "adequate"

    def test_json_in_plain_fence(self):
        text = '```\n{"ok": false, "reason": "too shallow"}\n```'
        result = parse_semantic_critic_response(text)
        assert result is not None
        assert result.ok is False
        assert result.reason == "too shallow"

    def test_json_in_fence_with_language_tag(self):
        text = '```json\n{"ok": true, "reason": "mechanism trace present"}\n```'
        result = parse_semantic_critic_response(text)
        assert result is not None
        assert result.ok is True

    def test_json_in_multiline_fence(self):
        text = '```\n{"ok": true, "reason": "covers alternatives"}\n```'
        result = parse_semantic_critic_response(text)
        assert result is not None
        assert result.ok is True

    def test_json_prose_no_fence(self):
        result = parse_semantic_critic_response(
            "The response is adequate. The analysis covers the root cause."
        )
        assert result is None

    def test_non_json_random_text(self):
        result = parse_semantic_critic_response("This is not JSON at all")
        assert result is None

    def test_malformed_json(self):
        result = parse_semantic_critic_response('{"ok": true, "reason": missing}')
        assert result is None

    def test_missing_ok_key(self):
        result = parse_semantic_critic_response('{"reason": "no ok field"}')
        assert result is None

    def test_missing_reason_key(self):
        result = parse_semantic_critic_response('{"ok": true}')
        assert result is None

    def test_ok_is_int_not_bool(self):
        result = parse_semantic_critic_response('{"ok": 1, "reason": "test"}')
        assert result is None

    def test_ok_is_string_not_bool(self):
        result = parse_semantic_critic_response('{"ok": "true", "reason": "test"}')
        assert result is None

    def test_reason_is_int_not_string(self):
        result = parse_semantic_critic_response('{"ok": true, "reason": 42}')
        assert result is None

    def test_reason_is_empty_string(self):
        # Empty reason is technically valid schema but unusual — allow it
        result = parse_semantic_critic_response('{"ok": true, "reason": ""}')
        assert result is not None
        assert result.ok is True
        assert result.reason == ""

    def test_extra_fields_allowed(self):
        result = parse_semantic_critic_response(
            '{"ok": true, "reason": "ok", "extra": "ignored"}'
        )
        assert result is not None
        assert result.ok is True

    def test_nested_json_object(self):
        result = parse_semantic_critic_response('{"ok": true, "reason": "nested"}')
        assert result is not None
        assert result.ok is True

    def test_empty_string_input(self):
        result = parse_semantic_critic_response("")
        assert result is None

    def test_whitespace_only_input(self):
        result = parse_semantic_critic_response("   \n\n  ")
        assert result is None

    def test_fence_only_empty(self):
        result = parse_semantic_critic_response("```\n\n```")
        assert result is None

    def test_reason_unicode(self):
        result = parse_semantic_critic_response(
            '{"ok": true, "reason": "covers \\u00e9v\\u00e9ryth\\u00e9ing"}'
        )
        assert result is not None
        assert result.ok is True


# =============================================================================
# _is_diagnostic_scope — scope detection tests (preserved from before)
# =============================================================================


class TestIsDiagnosticScope:
    """Test diagnostic scope detection."""

    def test_short_response_excluded(self):
        short = "The bug is in the race condition."
        assert len(short.split()) < 50
        assert _is_diagnostic_scope("why did this fail?", short) is False

    def test_diagnosis_explicit_prompt(self):
        long = "The error occurs because of a race condition in the connection pool. " * 5
        assert len(long.split()) > 50
        result = _is_diagnostic_scope("why did the connection fail?", long)
        assert result is True

    def test_root_cause_prompt(self):
        long = (
            "The issue is related to deadlock detection. " * 5
            + "This happens when multiple threads acquire locks in different orders."
        ) * 2
        assert len(long.split()) > 50
        result = _is_diagnostic_scope("what is the root cause?", long)
        assert result is True

    def test_investigation_prompt(self):
        long = (
            "The pattern suggests memory leak in the garbage collector. " * 3
            + "Memory grows linearly over time. The investigation reveals the root cause."
        ) * 2
        assert len(long.split()) > 50
        result = _is_diagnostic_scope("investigate the memory issue", long)
        assert result is True

    def test_troubleshoot_prompt(self):
        long = (
            "The system crashes under high load. " * 4
            + "The thread pool becomes saturated. This is the cause of the failure."
        ) * 2
        assert len(long.split()) > 50
        result = _is_diagnostic_scope("troubleshoot this crash", long)
        assert result is True

    def test_explain_why_prompt(self):
        long = (
            "The crash happens at line 42. " * 3
            + "The stack trace shows a null pointer exception. The root cause is a null reference."
        ) * 2
        assert len(long.split()) > 50
        result = _is_diagnostic_scope("what is the reason for the crash", long)
        assert result is True

    def test_no_diagnostic_keywords(self):
        long = "The file contains 1000 lines of code. The function is called " * 10
        assert len(long.split()) > 50
        result = _is_diagnostic_scope("what does this file do?", long)
        assert result is False

    def test_ambiguous_prompt_with_mechanism(self):
        long = (
            "The race condition happens when threads access shared state without synchronization. "
            * 3
            + "This led to intermittent failures."
        ) * 2
        assert len(long.split()) > 50
        result = _is_diagnostic_scope("describe this code", long)
        # Has "led to" (causal keyword) and mechanism terms
        assert result is True

    def test_chinese_diagnostic(self):
        long = "诊断 分析 问题 原因 和 机制 。 " * 30
        assert len(long.split()) > 50
        result = _is_diagnostic_scope("分析 问题 根源", long)
        assert result is True


# =============================================================================
# _is_non_substantive — non-substantive detection tests (preserved)
# =============================================================================


class TestIsNonSubstantive:
    """Test non-substantive detection (fallback version in Stop_semantic_critic)."""

    def test_greeting(self):
        result = _is_non_substantive("Hello! What are we working on today?")
        assert result is True

    def test_short_ack(self):
        result = _is_non_substantive("Got it, thanks!")
        assert result is True

    def test_empty(self):
        result = _is_non_substantive("")
        assert result is False  # conservative: empty not clearly phatic

    def test_analytical(self):
        result = _is_non_substantive(
            "The root cause is a race condition in the thread pool when "
            "multiple threads try to acquire the same lock simultaneously."
        )
        assert result is False

    def test_with_because(self):
        result = _is_non_substantive("This fails because the config is missing.")
        assert result is False

    def test_with_should(self):
        result = _is_non_substantive("You should add validation before processing.")
        assert result is False


# =============================================================================
# Helpers — unit tests
# =============================================================================


class TestHelpers:
    """Unit tests for helper functions."""

    def test_session_key_from_session_id(self):
        data = {"session_id": "abc123", "terminal_id": "term456"}
        assert _session_key(data) == "abc123"

    def test_session_key_from_terminal_id(self):
        data = {"terminal_id": "term456"}
        assert _session_key(data) == "term456"

    def test_session_key_fallback(self):
        data = {}
        key = _session_key(data)
        assert isinstance(key, str)
        assert len(key) > 0

    def test_build_critic_user_message_format(self):
        msg = _build_critic_user_message(
            "Why did it fail?", "It failed because X."
        )
        assert "<<<USER_PROMPT" in msg
        assert "Why did it fail?" in msg
        assert "<<<ASSISTANT_RESPONSE" in msg
        assert "It failed because X." in msg

    def test_critic_system_prompt_present(self):
        assert len(CRITIC_SYSTEM_PROMPT) > 100
        assert "semantic quality critic" in CRITIC_SYSTEM_PROMPT
        assert '{"ok": true, "reason": "short reason"}' in CRITIC_SYSTEM_PROMPT


# =============================================================================
# SemanticCriticResult — dataclass unit tests
# =============================================================================


class TestSemanticCriticResult:
    """Test the result dataclass."""

    def test_ok_true(self):
        r = SemanticCriticResult(ok=True, reason="adequate")
        assert r.ok is True
        assert r.reason == "adequate"

    def test_ok_false(self):
        r = SemanticCriticResult(ok=False, reason="missing alternatives")
        assert r.ok is False
        assert r.reason == "missing alternatives"


# =============================================================================
# Integration-like tests — mock Bifrost via monkeypatch
# =============================================================================


class TestSemanticCriticWithMockedBifrost:
    """Integration-like tests using mocked Bifrost responses."""

    def test_shallow_answer_gets_false(self, monkeypatch):
        """A shallow diagnostic answer should be vetoed."""
        import Stop_semantic_critic as mod

        def fake_bifrost_call(model, prompt, correlation_id, compare_id, system=None):
            return {
                "ok": True,
                "model": model,
                "text": '{"ok": false, "reason": "Answer lacks mechanism trace and alternatives"}',
                "status": "ok",
                "error_type": "",
                "ttfb_ms": 100,
                "total_ms": 500,
            }

        monkeypatch.setattr(mod, "bifrost_call", fake_bifrost_call)

        result = call_semantic_critic_via_bifrost(
            original_user_prompt="Why did the connection fail?",
            assistant_response=(
                "The connection failed. This is a networking issue caused by the server "
                "being down. Try restarting the service. "
            )
            * 10,  # Make it > 50 words
            session_key="test-session",
        )

        assert result is not None
        assert result.ok is False
        assert "mechanism trace" in result.reason.lower() or "alternatives" in result.reason.lower()

    def test_robust_answer_gets_true(self, monkeypatch):
        """A robust diagnostic answer should pass."""
        import Stop_semantic_critic as mod

        def fake_bifrost_call(model, prompt, correlation_id, compare_id, system=None):
            return {
                "ok": True,
                "model": model,
                "text": '{"ok": true, "reason": "Adequate mechanism trace and alternatives present."}',
                "status": "ok",
                "error_type": "",
                "ttfb_ms": 100,
                "total_ms": 500,
            }

        monkeypatch.setattr(mod, "bifrost_call", fake_bifrost_call)

        result = call_semantic_critic_via_bifrost(
            original_user_prompt="Why did the connection fail?",
            assistant_response=(
                "The connection failed because the authentication token expired after 24 hours. "
                "This caused the server to reject the request with a 401 error. "
                "Alternative causes include network timeout, wrong API endpoint, or revoked credentials. "
                "You can verify the token expiration by checking the JWT claims at jwt.io. "
                "The fix is to refresh the token before making API calls."
            )
            * 5,
            session_key="test-session",
        )

        assert result is not None
        assert result.ok is True

    def test_bifrost_timeout_returns_none(self, monkeypatch):
        """Timeout should return None (fail open)."""
        import Stop_semantic_critic as mod

        def fake_bifrost_call(model, prompt, correlation_id, compare_id, system=None):
            return {
                "ok": False,
                "model": model,
                "text": "",
                "status": "timeout",
                "error_type": "Timeout",
                "ttfb_ms": 9000,
                "total_ms": 9000,
            }

        monkeypatch.setattr(mod, "bifrost_call", fake_bifrost_call)

        result = call_semantic_critic_via_bifrost(
            original_user_prompt="Why did it fail?",
            assistant_response="It failed because X. " * 10,
            session_key="test-session",
        )

        assert result is None

    def test_bifrost_returns_non_json_returns_none(self, monkeypatch):
        """Non-JSON response should return None (fail open)."""
        import Stop_semantic_critic as mod

        def fake_bifrost_call(model, prompt, correlation_id, compare_id, system=None):
            return {
                "ok": True,
                "model": model,
                "text": "The response is quite good.",
                "status": "ok",
                "error_type": "",
                "ttfb_ms": 100,
                "total_ms": 400,
            }

        monkeypatch.setattr(mod, "bifrost_call", fake_bifrost_call)

        result = call_semantic_critic_via_bifrost(
            original_user_prompt="Explain the bug",
            assistant_response="The bug occurs when X and Y. " * 10,
            session_key="test-session",
        )

        assert result is None


# =============================================================================
# Full hook run() — integration tests with mocked Bifrost
# =============================================================================


class TestStopSemanticCriticRun:
    """Test the full run() function with mocked Bifrost."""

    def test_early_exit_empty_response(self):
        from Stop_semantic_critic import run

        result = run({"session_id": "s", "user_prompt": "x", "response": ""})
        assert result is None

    def test_early_exit_short_response(self):
        from Stop_semantic_critic import run

        result = run({"session_id": "s", "user_prompt": "x", "response": "Short."})
        assert result is None

    def test_early_exit_non_substantive(self):
        from Stop_semantic_critic import run

        result = run(
            {
                "session_id": "s",
                "user_prompt": "hi",
                "response": "Hello! Ready when you are.",
            }
        )
        assert result is None

    def test_early_exit_non_diagnostic(self):
        from Stop_semantic_critic import run

        result = run(
            {
                "session_id": "s",
                "user_prompt": "What is the weather?",
                "response": "The weather is sunny today with a high of 75 degrees. " * 5,
            }
        )
        assert result is None

    def test_run_with_ok_verdict_allows(self, monkeypatch):
        """Ok=true verdict should return None (allow)."""
        import Stop_semantic_critic as mod

        def fake_bifrost_call(model, prompt, correlation_id, compare_id, system=None):
            return {
                "ok": True,
                "model": model,
                "text": '{"ok": true, "reason": "Adequate"}',
                "status": "ok",
                "error_type": "",
                "ttfb_ms": 100,
                "total_ms": 400,
            }

        monkeypatch.setattr(mod, "bifrost_call", fake_bifrost_call)

        # Clear per-session cap between tests
        mod._INVOCATION_COUNTS.clear()

        result = mod.run(
            {
                "session_id": "cap-test",
                "user_prompt": "Why did the connection fail?",
                "response": (
                    "The connection failed because the authentication token expired. "
                    "Alternative causes include network timeout, wrong endpoint, or revoked credentials. "
                    "You can verify by checking the JWT claims. The fix is to refresh the token."
                )
                * 5,
            }
        )
        assert result is None

    def test_run_with_false_verdict_injects_advisory(self, monkeypatch):
        """Ok=false verdict should return allow+systemMessage advisory."""
        import Stop_semantic_critic as mod

        def fake_bifrost_call(model, prompt, correlation_id, compare_id, system=None):
            return {
                "ok": True,
                "model": model,
                "text": '{"ok": false, "reason": "No mechanism trace provided."}',
                "status": "ok",
                "error_type": "",
                "ttfb_ms": 100,
                "total_ms": 400,
            }

        monkeypatch.setattr(mod, "bifrost_call", fake_bifrost_call)

        mod._INVOCATION_COUNTS.clear()

        result = mod.run(
            {
                "session_id": "veto-test",
                "user_prompt": "Why did the connection fail?",
                "response": (
                    "The connection failed. This is a networking issue caused by the server "
                    "being down. Try restarting the service."
                )
                * 5,
            }
        )
        assert result is not None
        assert result.get("allow") is True
        assert "Missing issue: No mechanism trace provided." in result.get("systemMessage", "")


# =============================================================================
# Cap enforcement
# =============================================================================


class TestCapEnforcement:
    """Test per-session invocation cap."""

    def test_cap_limits_calls(self, monkeypatch):
        import Stop_semantic_critic as mod

        call_count = [0]

        def fake_bifrost_call(model, prompt, correlation_id, compare_id, system=None):
            call_count[0] += 1
            return {
                "ok": True,
                "model": model,
                "text": '{"ok": false, "reason": "shallow"}',
                "status": "ok",
                "error_type": "",
                "ttfb_ms": 100,
                "total_ms": 400,
            }

        monkeypatch.setattr(mod, "bifrost_call", fake_bifrost_call)
        mod._INVOCATION_COUNTS.clear()
        original_cap = mod.SEMANTIC_CRITIC_CAP
        mod.SEMANTIC_CRITIC_CAP = 3

        diagnostic_response = (
            "The connection failed because of a timeout in the authentication flow. "
            "This is a known issue when the server is under load. "
            "Alternative explanations include network latency, DNS resolution failure, "
            "or an expired certificate. You should verify the server status and check logs."
        ) * 5

        session = "cap-test-session"
        for i in range(5):
            result = mod.run(
                {
                    "session_id": session,
                    "user_prompt": "Why did the connection fail?",
                    "response": diagnostic_response,
                }
            )

        assert call_count[0] == 3, f"Expected 3 calls, got {call_count[0]}"

        mod.SEMANTIC_CRITIC_CAP = original_cap


# =============================================================================
# Module import
# =============================================================================


class TestModuleImport:
    """Test that the module can be imported and run is callable."""

    def test_module_import(self):
        from Stop_semantic_critic import run

        assert callable(run)


# =============================================================================
# Critic profile routing
# =============================================================================


class TestDetectCriticProfile:
    """Test deterministic profile selection."""

    def test_software_rca_two_signals(self):
        assert _detect_critic_profile(
            "Why did the API return 401 after deploy?",
            "The deploy broke auth. Roll back.",
        ) == "software_rca"

    def test_software_rca_incident(self):
        assert _detect_critic_profile(
            "Root cause the production incident",
            "Thread pool deadlock in the connection handler.",
        ) == "software_rca"

    def test_software_rca_latency_and_auth(self):
        # Two signals: latency + auth
        assert _detect_critic_profile(
            "Why is latency high after login was added?",
            "Synchronous profile hydration is blocking the auth flow.",
        ) == "software_rca"

    def test_software_rca_stack_trace(self):
        # Two signals: crash (prompt) + exception (response has "Exception")
        assert _detect_critic_profile(
            "Debug this crash",
            "NullPointerException at line 42 in UserService.java. Check for null references.",
        ) == "software_rca"

    def test_evaluative_recommendation(self):
        assert _detect_critic_profile(
            "Which database should we use?",
            "Postgres is best. Use Postgres.",
        ) == "evaluative_recommendation"

    def test_evaluative_compare(self):
        assert _detect_critic_profile(
            "Compare React vs Vue for our project",
            "React is better because of the ecosystem.",
        ) == "evaluative_recommendation"

    def test_evaluative_best(self):
        assert _detect_critic_profile(
            "What is the best approach?",
            "Option A is better because of X and Y.",
        ) == "evaluative_recommendation"

    def test_fallback_general_diagnostic(self):
        # No software signals, no evaluative signals
        assert _detect_critic_profile(
            "Why did the economy slow down?",
            "Lower consumer spending and higher interest rates slowed economic growth.",
        ) == "general_diagnostic"

    def test_fallback_nominal(self):
        # Only one software signal (crash), needs >=2 for software_rca
        # Use words unlikely to match any signal list
        assert _detect_critic_profile(
            "What is the reason for the crash?",
            "The system shutdown unexpectedly during startup.",
        ) == "general_diagnostic"

    def test_evaluative_tradeoff(self):
        assert _detect_critic_profile(
            "What are the tradeoffs?",
            "Microservices give you independence but add operational overhead.",
        ) == "evaluative_recommendation"

    def test_evaluative_priority(self):
        assert _detect_critic_profile(
            "Which feature should we prioritize?",
            "Feature A has higher impact and lower effort.",
        ) == "evaluative_recommendation"

    def test_short_rca_phrase_routes_to_software_rca(self):
        # "root cause" alone is enough — phrase signal overrides signal_count
        assert _detect_critic_profile(
            "Root cause the outage",
            "Unknown at this time.",
        ) == "software_rca"

    def test_short_technical_prompt_with_two_signals(self):
        # Short prompt: "bug" (in prompt) + "exception" (response has NullPointerException)
        assert _detect_critic_profile(
            "Why is the API returning a 500 error?",
            "NullPointerException in the handler. Add a null check.",
        ) == "software_rca"

    def test_short_non_technical_prompt_one_signal(self):
        # Only one software signal (crash), no phrase signal — should NOT route to software_rca
        assert _detect_critic_profile(
            "Why did the system crash?",
            "The server was overloaded and had to shut down.",
        ) == "general_diagnostic"

    def test_short_bug_report_routes_to_software_rca(self):
        # "bug" is a software signal; response adds a second signal via "exception"
        assert _detect_critic_profile(
            "There's a bug in the auth module",
            "It throws a NullPointerException when the token is None.",
        ) == "software_rca"

    def test_short_stacktrace_with_one_prompt_signal(self):
        # Prompt has "crash"; response has stack trace language
        assert _detect_critic_profile(
            "My app keeps crashing",
            "java.lang.OutOfMemoryError: Java heap space",
        ) == "software_rca"


class TestCriticPrompts:
    """Test that all profiles exist and have expected structure."""

    def test_all_three_profiles_present(self):
        assert set(CRITIC_PROMPTS.keys()) == {
            "software_rca",
            "general_diagnostic",
            "evaluative_recommendation",
        }

    def test_software_rca_has_examples(self):
        assert "Example 1" in CRITIC_PROMPTS["software_rca"]
        assert "Example 4" in CRITIC_PROMPTS["software_rca"]

    def test_evaluative_has_examples(self):
        assert "Example 1" in CRITIC_PROMPTS["evaluative_recommendation"]
        assert "Example 4" in CRITIC_PROMPTS["evaluative_recommendation"]

    def test_general_diagnostic_has_examples(self):
        assert "Example 1" in CRITIC_PROMPTS["general_diagnostic"]
        assert "Example 3" in CRITIC_PROMPTS["general_diagnostic"]

    def test_backwards_compatible_alias(self):
        # CRITIC_SYSTEM_PROMPT must resolve to general_diagnostic
        assert CRITIC_SYSTEM_PROMPT == CRITIC_PROMPTS["general_diagnostic"]


class TestRemediationTemplates:
    """Test profile-specific remediation templates."""

    def test_all_three_profiles_have_remediation(self):
        assert set(REMEDIATION_TEMPLATES.keys()) == {
            "software_rca",
            "general_diagnostic",
            "evaluative_recommendation",
        }

    def test_remediation_not_empty(self):
        for profile, template in REMEDIATION_TEMPLATES.items():
            assert len(template) > 10, f"Remediation for {profile} is too short"

    def test_build_remediation_software_rca(self):
        msg = _build_remediation_message("software_rca", "missing test")
        assert "conclusion" in msg.lower()
        assert "verification" in msg.lower()
        assert "missing test" in msg

    def test_build_remediation_general_diagnostic(self):
        msg = _build_remediation_message("general_diagnostic", "premature absence")
        # Must contain the new absence-check language
        assert "missing" in msg.lower() or "unavailable" in msg.lower()
        assert "evidence" in msg.lower() or "checked" in msg.lower()
        assert "premature absence" in msg

    def test_build_remediation_evaluative_recommendation(self):
        msg = _build_remediation_message("evaluative_recommendation", "no criteria")
        assert "criteria" in msg.lower() or "tradeoff" in msg.lower()
        assert "no criteria" in msg

    def test_build_remediation_unknown_profile(self):
        # Unknown profile should fall back gracefully
        msg = _build_remediation_message("unknown", "some reason")
        assert "some reason" in msg

    def test_run_uses_profile_specific_remediation(self, monkeypatch):
        """run() should use profile-specific remediation on software_rca failures."""
        import Stop_semantic_critic as mod

        def fake_bifrost_call(model, prompt, correlation_id, compare_id, system=None):
            return {
                "ok": True,
                "model": model,
                "text": '{"ok": false, "reason": "Missing mechanism trace."}',
                "status": "ok",
                "error_type": "",
                "ttfb_ms": 100,
                "total_ms": 400,
            }

        monkeypatch.setattr(mod, "bifrost_call", fake_bifrost_call)
        mod._INVOCATION_COUNTS.clear()

        result = mod.run(
            {
                "session_id": "remediation-test",
                "user_prompt": "Why did the connection fail?",
                "response": (
                    "The service crashed. The deploy probably broke auth. "
                    "You should check the logs and restart the service."
                )
                * 5,
            }
        )
        assert result is not None
        assert result.get("allow") is True
        system_msg = result.get("systemMessage", "")
        # Should contain software_rca-specific remediation
        assert "conclusion" in system_msg.lower() or "verification" in system_msg.lower()
        assert "Missing mechanism trace" in system_msg


class TestSoftwareRcaPromptExamples:
    """Verify software_rca prompt has required examples from the revised spec."""

    def test_has_example_3_auto_commit(self):
        # Example 3 must reference auto-commit / env var / test bypass scenario
        assert "auto-commit" in CRITIC_PROMPTS["software_rca"].lower() or "env var" in CRITIC_PROMPTS["software_rca"].lower()

    def test_has_example_4_shruggy_answer(self):
        # Example 4 must show the "probably not, unverified" failure mode
        assert "probably not" in CRITIC_PROMPTS["software_rca"].lower() or "unverified" in CRITIC_PROMPTS["software_rca"].lower()

    def test_has_strongest_conclusion_criterion(self):
        prompt = CRITIC_PROMPTS["software_rca"]
        assert (
            "strongest justified" in prompt.lower()
            or "best-effort" in prompt.lower()
            or "interim conclusion" in prompt.lower()
        )

    def test_example_4_returns_false(self):
        # The Example 4 answer should trigger ok=false
        prompt = CRITIC_PROMPTS["software_rca"]
        # Verify the example format: "Probably not. It's unverified. You'd need to test it." -> ok=false
        assert 'Output: {"ok": false' in prompt or 'ok: false' in prompt


class TestAbsenceConclusionCriterion:
    """Verify absence-check criterion is present in all applicable profiles."""

    def test_general_diagnostic_has_absence_criterion(self):
        prompt = CRITIC_PROMPTS["general_diagnostic"]
        assert "prematurely conclude" in prompt.lower()
        assert "missing" in prompt.lower() and ("unavailable" in prompt.lower() or "impossible" in prompt.lower())
        assert "evidence source" in prompt.lower()

    def test_software_rca_has_absence_criterion(self):
        prompt = CRITIC_PROMPTS["software_rca"]
        assert "prematurely conclude" in prompt.lower()
        assert "missing" in prompt.lower() and ("unavailable" in prompt.lower() or "impossible" in prompt.lower())
        assert "evidence source" in prompt.lower()

    def test_evaluative_has_absence_criterion(self):
        prompt = CRITIC_PROMPTS["evaluative_recommendation"]
        assert "prematurely conclude" in prompt.lower()
        assert "missing" in prompt.lower() and ("unavailable" in prompt.lower() or "impossible" in prompt.lower())
        assert "evidence source" in prompt.lower()

    def test_general_diagnostic_has_absence_examples(self):
        prompt = CRITIC_PROMPTS["general_diagnostic"]
        # Must have both failure and pass examples for absence conclusion
        assert "Example 4" in prompt
        assert "Example 5" in prompt
        assert "No, there is no API key" in prompt  # failure example
        assert "I have not checked" in prompt        # pass example

    def test_absence_premature_conclusion_flagged(self, monkeypatch):
        """Answer that says 'X is missing' without checking sources should get ok=false."""
        import Stop_semantic_critic as mod

        def fake_bifrost_call(model, prompt, correlation_id, compare_id, system=None):
            # Inject a response that says "no key available" without checking
            return {
                "ok": True,
                "model": model,
                "text": '{"ok": false, "reason": "Missing evidence check; did not search known config locations or state they were unchecked."}',
                "status": "ok",
                "error_type": "",
                "ttfb_ms": 100,
                "total_ms": 400,
            }

        monkeypatch.setattr(mod, "bifrost_call", fake_bifrost_call)
        mod._INVOCATION_COUNTS.clear()

        result = mod.run({
            "session_id": "absence-test",
            "user_prompt": "Why is the minimax provider failing because of missing credentials?",
            "response": (
                "No API key is configured for minimax. The provider cannot be used without "
                "credentials, so the feature cannot be enabled in the current setup. "
                "You would need to obtain a valid API key from the minimax provider and add it "
                "to your configuration before the provider can be used for any operations. "
                "Please check the provider documentation for setup instructions and credential "
                "requirements to understand what steps are needed to get started."
            ),
        })

        assert result is not None
        assert result.get("allow") is True
        # Remediation must reference absence-check
        assert "missing" in result["systemMessage"].lower() or "unavailable" in result["systemMessage"].lower()
        assert "checked" in result["systemMessage"].lower() or "evidence" in result["systemMessage"].lower()

    def test_absence_with_explicit_uncertainty_passes(self, monkeypatch):
        """Answer that explicitly says sources were not checked should get ok=true."""
        import Stop_semantic_critic as mod

        def fake_bifrost_call(model, prompt, correlation_id, compare_id, system=None):
            # Inject a response that says "I haven't checked, so I don't know"
            return {
                "ok": True,
                "model": model,
                "text": '{"ok": true, "reason": "Adequate."}',
                "status": "ok",
                "error_type": "",
                "ttfb_ms": 100,
                "total_ms": 400,
            }

        monkeypatch.setattr(mod, "bifrost_call", fake_bifrost_call)
        mod._INVOCATION_COUNTS.clear()

        result = mod.run({
            "session_id": "absence-uncertain-test",
            "user_prompt": "Is there a minimax API key?",
            "response": (
                "I have not checked P:/.env or ~/.pi/agent/auth.json, so I cannot confirm "
                "whether a minimax key is available. I can verify those locations if needed."
            ),
        })

        # ok=true -> run() returns None (allow without advisory)
        assert result is None


class TestGeneralDiagnosticRemediationUpdated:
    """Verify general_diagnostic remediation uses the absence-check template."""

    def test_new_absence_template(self):
        """general_diagnostic remediation must contain absence-check language."""
        import Stop_semantic_critic as mod

        msg = mod._build_remediation_message("general_diagnostic", "no key found")
        assert "missing" in msg.lower() or "unavailable" in msg.lower()
        assert "checked" in msg.lower() or "evidence" in msg.lower()
        assert "no key found" in msg

    def test_spec_divergence_clause_present(self):
        """general_diagnostic remediation must include spec-alignment clause."""
        import Stop_semantic_critic as mod

        msg = mod._build_remediation_message("general_diagnostic", "silent pivot")
        assert "hook phase" in msg.lower() or "constraints" in msg.lower()
        assert "confirm" in msg.lower()
        assert "silently" in msg.lower()


class TestSpecAlignmentCriterion:
    """Verify spec-alignment criterion is present in all applicable profiles."""

    def test_general_diagnostic_has_spec_alignment_criterion(self):
        prompt = CRITIC_PROMPTS["general_diagnostic"]
        assert "hook phase" in prompt.lower() or "explicit user constraint" in prompt.lower()
        assert "confirm" in prompt.lower()

    def test_software_rca_has_spec_alignment_criterion(self):
        prompt = CRITIC_PROMPTS["software_rca"]
        assert "hook phase" in prompt.lower() or "explicit user constraint" in prompt.lower()
        assert "confirm" in prompt.lower()

    def test_evaluative_has_spec_alignment_criterion(self):
        prompt = CRITIC_PROMPTS["evaluative_recommendation"]
        assert "hook phase" in prompt.lower() or "explicit user constraint" in prompt.lower()
        assert "confirm" in prompt.lower()

    def test_general_diagnostic_has_spec_alignment_examples(self):
        prompt = CRITIC_PROMPTS["general_diagnostic"]
        assert "Example 6" in prompt
        assert "Example 7" in prompt
        assert "UserPromptSubmit" in prompt   # failure example
        assert "PreToolUse" in prompt          # failure example
        assert "you asked for" in prompt.lower()  # pass example

    def test_software_rca_has_spec_alignment_examples(self):
        prompt = CRITIC_PROMPTS["software_rca"]
        assert "Example 5" in prompt
        assert "Example 6" in prompt
        assert "PreToolUse" in prompt or "Stop hook" in prompt

    def test_silent_phase_change_flagged(self, monkeypatch):
        """Answer that silently changes requested phase should get ok=false."""
        import Stop_semantic_critic as mod

        def fake_bifrost_call(model, prompt, correlation_id, compare_id, system=None):
            return {
                "ok": True,
                "model": model,
                "text": '{"ok": false, "reason": "Used UserPromptSubmit instead of the requested PreToolUse phase without stating the change."}',
                "status": "ok",
                "error_type": "",
                "ttfb_ms": 100,
                "total_ms": 400,
            }

        monkeypatch.setattr(mod, "bifrost_call", fake_bifrost_call)
        mod._INVOCATION_COUNTS.clear()

        result = mod.run({
            "session_id": "spec-align-test",
            "user_prompt": "Why is the language guard blocking English input in tools?",
            "response": (
                "The UserPromptSubmit hook you asked for is working correctly. "
                "It scans messages before tool execution and blocks content that does not appear "
                "to be English. This is expected behavior for a content filter. "
                "If you want different thresholds or allowlists, those can be adjusted."
            ),
        })

        assert result is not None
        assert result.get("allow") is True
        # Remediation must reference hook phase / confirmation
        assert "confirm" in result["systemMessage"].lower() or "constraints" in result["systemMessage"].lower()

    def test_explicit_proposal_not_penalized(self, monkeypatch):
        """Answer that explicitly proposes a different approach should get ok=true."""
        import Stop_semantic_critic as mod

        def fake_bifrost_call(model, prompt, correlation_id, compare_id, system=None):
            return {
                "ok": True,
                "model": model,
                "text": '{"ok": true, "reason": "Adequate."}',
                "status": "ok",
                "error_type": "",
                "ttfb_ms": 100,
                "total_ms": 400,
            }

        monkeypatch.setattr(mod, "bifrost_call", fake_bifrost_call)
        mod._INVOCATION_COUNTS.clear()

        result = mod.run({
            "session_id": "spec-align-pass-test",
            "user_prompt": "Why is the language guard blocking English input in tools?",
            "response": (
                "You asked for a PreToolUse hook, but a UserPromptSubmit hook is a better fit "
                "here because language filtering is a generation-time concern, not a tool "
                "execution concern. PreToolUse runs after tool selection but before execution, "
                "which means it would still scan non-text tools unnecessarily. UserPromptSubmit "
                "catches it earlier and avoids that overhead. Would you like to switch to "
                "UserPromptSubmit, or stick with PreToolUse?"
            ),
        })

        # ok=true -> run() returns None
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])