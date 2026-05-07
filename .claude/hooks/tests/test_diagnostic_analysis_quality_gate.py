"""Tests for Stop_diagnostic_analysis_quality_gate.py.

Covers:
- Single-story diagnosis without alternatives → flagged
- Diagnosis with A vs B plus discriminating test → allowed
- Metric declared diagnostic without baseline → flagged
- Strong causal claim without mechanism trace but with uncertainty → allowed
- Implementation report → no-op (not a diagnostic turn)
- Shallow compliance → blocked
- Short responses → no-op
- Non-diagnostic responses → no-op
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure hooks directory is on sys.path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from Stop_diagnostic_analysis_quality_gate import (
    DiagnosticFinding,
    _check_baseline_comparison,
    _check_competing_hypotheses,
    _check_discriminating_test,
    _check_mechanism_trace,
    _is_diagnostic_turn,
    _is_shallow_compliance,
    analyze,
    run,
)


# ---------------------------------------------------------------------------
# Turn detection tests
# ---------------------------------------------------------------------------

class TestIsDiagnosticTurn:
    def test_short_response_is_not_diagnostic(self):
        assert _is_diagnostic_turn("The bug is caused by a missing import.") is False

    def test_implementation_report_is_not_diagnostic(self):
        text = (
            "Files modified:\n"
            "- Stop_router.py: added new hook registration\n"
            "- tests/test_foo.py: added 5 test cases\n\n"
            "All tests pass."
        )
        assert _is_diagnostic_turn(text) is False

    def test_status_summary_is_not_diagnostic(self):
        text = (
            "All 12 tests passed. The implementation is complete and verified. "
            "No regressions detected in the existing test suite."
        )
        assert _is_diagnostic_turn(text) is False

    def test_causal_plus_diagnostic_is_diagnostic(self):
        text = (
            "The root cause of this regression is that the idle_wait metric increased "
            "because the auth middleware now validates sessions on every request. "
            "This is why the latency doubled. The reason is that session validation "
            "was added in commit abc123 due to the security requirement."
        )
        assert _is_diagnostic_turn(text) is True

    def test_multiple_causal_phrases_is_diagnostic(self):
        text = (
            "Looking at what happened, the hook caused a timeout because the subprocess "
            "call leads to a deadlock. The result of this is that the entire pipeline "
            "stalls. We need to understand what caused the deadlock to occur when "
            "multiple terminals run simultaneously."
        )
        assert _is_diagnostic_turn(text) is True

    def test_pure_causal_without_diagnostic_intent_is_diagnostic(self):
        text = (
            "Because of the way Python imports work, modules are loaded once and cached. "
            "This causes the state to persist across calls. Due to this behavior, "
            "you need to call reload() to pick up changes. "
            "The result is that changes don't take effect until you reload."
        )
        # 4+ causal phrases trigger diagnostic mode even without explicit diagnostic words
        assert _is_diagnostic_turn(text) is True

    def test_factual_answer_not_diagnostic(self):
        text = (
            "The file is located at P:/.claude/hooks/Stop_router.py. "
            "It contains the HOOK_SEQUENCE list and ACTIVE_RUNTIME_HOOKS set. "
            "The router uses in-process dispatch for better performance."
        )
        assert _is_diagnostic_turn(text) is False


# ---------------------------------------------------------------------------
# Competing hypotheses tests
# ---------------------------------------------------------------------------

class TestCompetingHypotheses:
    def test_single_story_flagged(self):
        text = (
            "The idle_wait metric increased because the auth middleware now "
            "validates sessions on every request. This directly causes the "
            "latency to double since each validation takes 50ms."
        )
        result = _check_competing_hypotheses(text)
        assert result is not None
        assert "DIAGNOSTIC_SINGLE_STORY" in result

    def test_two_hypotheses_passes(self):
        text = (
            "Hypothesis A: The auth middleware validates sessions on every request, "
            "adding 50ms per call. "
            "Hypothesis B: The connection pool is exhausted, causing new connections "
            "to wait for available slots."
        )
        result = _check_competing_hypotheses(text)
        assert result is None

    def test_two_possible_causes_passes(self):
        text = (
            "There are two possible causes for this regression. First, the auth "
            "middleware could be adding latency. Alternatively, the connection pool "
            "might be exhausted under load."
        )
        result = _check_competing_hypotheses(text)
        assert result is None

    def test_overwhelming_evidence_passes(self):
        text = (
            "The root cause is definitively confirmed by the stack trace showing "
            "auth middleware at frame 3. This is the only possible explanation "
            "for the 50ms increase."
        )
        result = _check_competing_hypotheses(text)
        assert result is None

    def test_alternative_explanation_passes(self):
        text = (
            "The auth middleware adds latency, but another possibility is that "
            "the database connection pool is misconfigured."
        )
        result = _check_competing_hypotheses(text)
        assert result is None


# ---------------------------------------------------------------------------
# Discriminating test tests
# ---------------------------------------------------------------------------

class TestDiscriminatingTest:
    def test_no_falsification_flagged(self):
        text = (
            "The auth middleware is the cause. It adds 50ms to every request. "
            "Hypothesis A is the auth middleware, Hypothesis B is the connection pool."
        )
        result = _check_discriminating_test(text)
        assert result is not None
        assert "DIAGNOSTIC_NO_FALSIFICATION" in result

    def test_falsification_condition_passes(self):
        text = (
            "To distinguish auth middleware vs connection pool: if run04 has elevated "
            "idle_wait but normal query time, that supports the auth hypothesis. "
            "If query time is also elevated, that supports the pool hypothesis."
        )
        result = _check_discriminating_test(text)
        assert result is None

    def test_would_be_wrong_if_passes(self):
        text = (
            "Hypothesis A: auth middleware. Hypothesis B: connection pool. "
            "This would be wrong if removing the auth middleware doesn't fix the latency."
        )
        result = _check_discriminating_test(text)
        assert result is None

    def test_check_whether_passes(self):
        text = (
            "Two possibilities: auth middleware or connection pool. "
            "We can check whether the latency disappears "
            "when we bypass auth."
        )
        result = _check_discriminating_test(text)
        assert result is None


# ---------------------------------------------------------------------------
# Baseline comparison tests
# ---------------------------------------------------------------------------

class TestBaselineComparison:
    def test_metric_without_baseline_flagged(self):
        text = (
            "The idle_wait metric is 150ms, which is a direct auth signal. "
            "This elevated wait time proves the auth middleware is blocking requests."
        )
        result = _check_baseline_comparison(text)
        assert result is not None
        assert "DIAGNOSTIC_NO_BASELINE" in result

    def test_metric_with_baseline_passes(self):
        text = (
            "The idle_wait metric is 150ms, compared to a baseline of 30ms in v1 "
            "without auth. The 5x increase supports the auth middleware hypothesis."
        )
        result = _check_baseline_comparison(text)
        assert result is None

    def test_metric_with_prior_run_passes(self):
        text = (
            "Latency is 200ms. The prior run without this change was 40ms. "
            "This 5x regression is due to the new middleware."
        )
        result = _check_baseline_comparison(text)
        assert result is None

    def test_no_metric_claims_skips_check(self):
        text = (
            "The root cause is that the hook reloads sessions on every request. "
            "Hypothesis A: session reload. Hypothesis B: stale cache."
        )
        result = _check_baseline_comparison(text)
        assert result is None

    def test_control_case_passes(self):
        text = (
            "Latency is 150ms in the test case, compared to 30ms in the control case "
            "without the auth middleware."
        )
        result = _check_baseline_comparison(text)
        assert result is None


# ---------------------------------------------------------------------------
# Mechanism trace tests
# ---------------------------------------------------------------------------

class TestMechanismTrace:
    def test_strong_causal_without_trace_flagged(self):
        text = (
            "This gate is why the behavior changed. The hook refreshes sessions "
            "on every request, causing the observed latency increase."
        )
        result = _check_mechanism_trace(text)
        assert result is not None
        assert "DIAGNOSTIC_NO_MECHANISM_TRACE" in result

    def test_causal_with_file_reference_passes(self):
        text = (
            "This gate is why the behavior changed. Looking at auth_middleware.py:47, "
            "the validate_session() call happens on every request, adding 50ms."
        )
        result = _check_mechanism_trace(text)
        assert result is None

    def test_causal_with_uncertainty_passes(self):
        text = (
            "This gate is why the behavior changed. The mechanism is unclear — "
            "the hook might be refreshing sessions, but I haven't verified this yet."
        )
        result = _check_mechanism_trace(text)
        assert result is None

    def test_no_strong_causal_skips_check(self):
        text = (
            "The latency might be caused by auth middleware or connection pool issues. "
            "We need to investigate further to determine the root cause."
        )
        result = _check_mechanism_trace(text)
        assert result is None


# ---------------------------------------------------------------------------
# Shallow compliance tests
# ---------------------------------------------------------------------------

class TestShallowCompliance:
    def test_thin_hypotheses_flagged(self):
        text = (
            "Possible causes:\n"
            "- Auth issue\n"
            "- Cache problem\n"
            "- Config bug\n\n"
            "The root cause is likely the auth middleware."
        )
        result = _is_shallow_compliance(text)
        assert result is not None
        assert "DIAGNOSTIC_SHALLOW_COMPLIANCE" in result

    def test_substantive_hypotheses_passes(self):
        text = (
            "Possible causes:\n"
            "- Auth middleware validates sessions on every request, adding 50ms latency per call\n"
            "- Connection pool is exhausted under load, causing new connections to wait for available slots\n"
            "- The cache invalidation trigger runs too frequently, causing unnecessary reloads\n\n"
            "The evidence points to the auth middleware."
        )
        result = _is_shallow_compliance(text)
        assert result is None

    def test_no_hypothesis_header_skips(self):
        text = (
            "Hypothesis A: The auth middleware is the cause because it adds 50ms. "
            "Hypothesis B: The connection pool is exhausted under high concurrency."
        )
        result = _is_shallow_compliance(text)
        assert result is None


# ---------------------------------------------------------------------------
# Integration: analyze() and run()
# ---------------------------------------------------------------------------

class TestAnalyze:
    def test_good_diagnosis_passes(self):
        text = (
            "Root cause analysis of the latency regression:\n\n"
            "Hypothesis A: Auth middleware validates sessions on every request (auth_middleware.py:47), "
            "adding 50ms per call.\n"
            "Hypothesis B: Connection pool exhausted under load, causing wait times.\n\n"
            "To distinguish: if run04 shows elevated idle_wait but normal query_time, "
            "that supports A. If both are elevated, supports B.\n\n"
            "idle_wait is 150ms vs baseline of 30ms in v1 without auth. "
            "The 5x increase is consistent with hypothesis A."
        )
        findings = analyze(text)
        assert len(findings) == 0

    def test_single_story_diagnosis_flagged(self):
        text = (
            "The root cause of this regression is that the auth middleware now "
            "validates sessions on every request. This is why the latency doubled "
            "from 30ms to 150ms. The middleware was added in commit abc and causes "
            "every request to wait for session validation."
        )
        findings = analyze(text)
        # Should flag: no competing hypotheses, no falsification, no baseline
        assert any(f.check == "competing_hypotheses" for f in findings)
        assert any(f.check == "discriminating_test" for f in findings)

    def test_implementation_report_not_analyzed(self):
        text = (
            "Files created:\n"
            "- Stop_diagnostic_analysis_quality_gate.py: new gate module\n"
            "- tests/test_diagnostic_quality.py: test suite\n\n"
            "All 12 tests pass. The gate is wired into Stop_router.py."
        )
        findings = analyze(text)
        assert len(findings) == 0


class TestRun:
    def test_disabled_returns_none(self):
        os.environ["DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED"] = "false"
        try:
            result = run({"response": "root cause is X because of Y"})
            assert result is None
        finally:
            os.environ.pop("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED", None)

    def test_warn_mode_returns_warn(self):
        os.environ["DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED"] = "true"
        os.environ["DIAGNOSTIC_ANALYSIS_QUALITY_GATE_MODE"] = "warn"
        try:
            text = (
                "Investigating the root cause of this performance regression. "
                "The idle_wait metric increased because the auth middleware now "
                "validates sessions on every request. This is why the latency "
                "doubled. The reason for this regression is that session validation "
                "was added due to the security requirement. The result is that "
                "every request pays a 50ms penalty due to the validation overhead."
            )
            result = run({"response": text})
            assert result is not None
            assert result.get("decision") == "warn"
        finally:
            os.environ.pop("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED", None)
            os.environ.pop("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_MODE", None)

    def test_block_mode_blocks_warn_findings(self):
        os.environ["DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED"] = "true"
        os.environ["DIAGNOSTIC_ANALYSIS_QUALITY_GATE_MODE"] = "block"
        try:
            text = (
                "Investigating the root cause of this performance regression. "
                "The idle_wait metric increased because the auth middleware now "
                "validates sessions on every request. This is why the latency "
                "doubled. The reason for this regression is that session validation "
                "was added due to the security requirement. The result is that "
                "every request pays a 50ms penalty due to the validation overhead."
            )
            result = run({"response": text})
            assert result is not None
            assert result.get("decision") == "block"
        finally:
            os.environ.pop("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED", None)
            os.environ.pop("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_MODE", None)

    def test_shallow_compliance_always_blocks(self):
        os.environ["DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED"] = "true"
        os.environ["DIAGNOSTIC_ANALYSIS_QUALITY_GATE_MODE"] = "warn"
        try:
            text = (
                "Root cause analysis of the regression:\n\n"
                "Possible causes:\n"
                "- Auth issue\n"
                "- Cache bug\n\n"
                "The reason is the auth middleware causing this regression "
                "because it was added last week due to security requirements. "
                "This is why the behavior changed. The result is that latency "
                "increased due to the extra validation on every request."
            )
            result = run({"response": text})
            assert result is not None
            assert result.get("decision") == "block"
            assert "SHALLOW_COMPLIANCE" in result.get("reason", "")
        finally:
            os.environ.pop("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED", None)
            os.environ.pop("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_MODE", None)

    def test_empty_response_returns_none(self):
        result = run({"response": ""})
        assert result is None

    def test_non_diagnostic_returns_none(self):
        result = run({
            "response": "I updated the file and all tests pass. Implementation is complete."
        })
        assert result is None
