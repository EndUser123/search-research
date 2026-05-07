"""Tests for Stop_aggregator.py - hook aggregation, deduplication, and prioritization.

Covers:
- Classification: hook name → (root_issue, confidence)
- Deduplication: overlapping results collapsed
- Prioritization: blocks first, then top warns by priority
- Rendering: compact actionable messages with signals list
- Env var toggle: STOP_AGGREGATOR_ENABLED
- Shallow compliance: no messages returns empty string
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

from Stop_aggregator import (
    AggregatedIssue,
    RawHookResult,
    aggregate_and_render,
    aggregate_raw_messages,
    classify_result,
    render_aggregated,
)


# ---------------------------------------------------------------------------
# Hook classification tests
# ---------------------------------------------------------------------------

class TestClassifyResult:
    def test_high_confidence_hooks(self):
        assert classify_result("cited_content_guard", "warn") == ("fabricated_evidence", "high")
        assert classify_result("cross_validator", "warn") == ("fabricated_evidence", "high")
        assert classify_result("completion_verification_guard", "block") == ("missing_verification", "high")
        assert classify_result("deletion_verification_guard", "block") == ("destructive_risk", "high")
        assert classify_result("correction_acknowledgment", "warn") == ("empty_ack_after_correction", "high")
        assert classify_result("correction_followthrough", "warn") == ("empty_ack_after_correction", "high")
        assert classify_result("behavior_gates_agreement", "warn") == ("empty_ack_after_correction", "high")
        assert classify_result("behavior_gates_blacklist", "block") == ("destructive_risk", "high")
        assert classify_result("safety_gate", "block") == ("destructive_risk", "high")
        assert classify_result("command_execution_validator", "block") == ("destructive_risk", "high")
        assert classify_result("frameguard_stop", "block") == ("destructive_risk", "high")

    def test_medium_confidence_hooks(self):
        assert classify_result("hypothesis_as_fact_gate", "warn") == ("unsupported_causal_claim", "medium")
        assert classify_result("hypothesis_enforcement", "warn") == ("unsupported_causal_claim", "medium")
        assert classify_result("comparative_claim_guard", "warn") == ("unsupported_causal_claim", "medium")
        assert classify_result("diagnostic_analysis_quality", "warn") == ("diagnostic_analysis_incomplete", "medium")
        assert classify_result("lazy_workaround_gate", "warn") == ("lazy_closure", "medium")
        assert classify_result("epistemic_contract", "warn") == ("epistemic_format", "medium")
        assert classify_result("unverified_stance", "warn") == ("unsupported_causal_claim", "medium")
        assert classify_result("empirical_claims_gate", "warn") == ("missing_verification", "medium")
        assert classify_result("fix_verification_enforcer", "warn") == ("missing_verification", "medium")
        assert classify_result("architecture_evidence_gate", "warn") == ("unsupported_causal_claim", "medium")
        assert classify_result("assumption_audit", "warn") == ("unsupported_causal_claim", "medium")
        assert classify_result("speculation_gate", "warn") == ("unsupported_causal_claim", "medium")
        assert classify_result("recommendation_gate", "warn") == ("lazy_closure", "medium")
        assert classify_result("intent_artifact_alignment", "warn") == ("coverage_gap", "medium")
        assert classify_result("narrative_intent", "warn") == ("unsupported_causal_claim", "medium")
        assert classify_result("behavior_gates_guidance", "warn") == ("coverage_gap", "medium")
        assert classify_result("dependency_chain_guard", "warn") == ("unsupported_causal_claim", "medium")

    def test_low_confidence_hooks(self):
        assert classify_result("self_reflection", "warn") == ("other", "low")
        assert classify_result("referent_coverage", "warn") == ("coverage_gap", "low")
        assert classify_result("overconfidence_detector", "warn") == ("overconfidence", "low")
        assert classify_result("tool_sanity", "warn") == ("tool_usage_anomaly", "low")
        assert classify_result("advisory", "warn") == ("other", "low")
        assert classify_result("reflect_integration", "warn") == ("other", "low")
        assert classify_result("reasoning_quality_gate", "warn") == ("other", "low")
        assert classify_result("reasoning_enhanced", "warn") == ("other", "low")
        assert classify_result("optimality_check", "warn") == ("other", "low")
        assert classify_result("symptom_map", "warn") == ("other", "low")
        assert classify_result("negative_existence_guard", "warn") == ("unsupported_causal_claim", "low")
        assert classify_result("positive_existence_guard", "warn") == ("unsupported_causal_claim", "low")
        assert classify_result("perf_attribution_gate", "warn") == ("unsupported_causal_claim", "low")
        assert classify_result("drift_sentinel", "warn") == ("other", "low")
        assert classify_result("step_header_verifier", "warn") == ("other", "low")
        assert classify_result("rca_reflector", "warn") == ("other", "low")
        assert classify_result("rca_contract", "warn") == ("other", "low")
        assert classify_result("good_question_gate", "warn") == ("other", "low")
        assert classify_result("skill_question_marker", "warn") == ("other", "low")
        assert classify_result("ralph_loop", "warn") == ("other", "low")
        assert classify_result("autonomy_gate", "warn") == ("other", "low")
        assert classify_result("proposal_decision_scanner", "warn") == ("other", "low")
        assert classify_result("arch_gap_detection", "warn") == ("coverage_gap", "low")
        assert classify_result("tdd_refactor_gate", "warn") == ("other", "low")
        assert classify_result("task_completion_gate", "warn") == ("other", "low")
        assert classify_result("rsn_display_gate", "warn") == ("other", "low")
        assert classify_result("skill_first_stop_gate", "warn") == ("other", "low")
        assert classify_result("post_skill_prose_gate", "warn") == ("other", "low")
        assert classify_result("verification_enforcement", "warn") == ("missing_verification", "medium")
        assert classify_result("git_diff_reground", "warn") == ("other", "low")
        assert classify_result("skill_dir_correlation", "warn") == ("other", "low")
        assert classify_result("cks_correction_anchor", "warn") == ("other", "low")
        assert classify_result("consultation_loop_interrupt", "warn") == ("other", "low")

    def test_unknown_hook_defaults_to_other_medium(self):
        assert classify_result("unknown_hook", "warn") == ("other", "medium")
        assert classify_result("some_fictional_gate", "block") == ("other", "medium")

    def test_partial_match(self):
        # "Stop_diagnostic_analysis_quality_gate.py" → "diagnostic_analysis_quality"
        assert classify_result("Stop_diagnostic_analysis_quality_gate.py", "warn") == ("diagnostic_analysis_incomplete", "medium")


# ---------------------------------------------------------------------------
# Deduplication tests
# ---------------------------------------------------------------------------

class TestDeduplication:
    def test_identical_hooks_collapse(self):
        messages = [
            ("cited_content_guard", "warn", "fabricated evidence message"),
            ("cross_validator", "warn", "fabricated evidence message"),
        ]
        issues = aggregate_raw_messages(messages)
        assert len(issues) == 1
        assert "cited_content_guard" in issues[0].source_hooks
        assert "cross_validator" in issues[0].source_hooks

    def test_empty_ack_correction_collapse(self):
        messages = [
            ("correction_acknowledgment", "warn", "empty ack message"),
            ("correction_followthrough", "warn", "followthrough message"),
            ("behavior_gates_agreement", "warn", "agreement message"),
        ]
        issues = aggregate_raw_messages(messages)
        assert len(issues) == 1
        assert "empty_ack_after_correction" == issues[0].root_issue
        assert len(issues[0].source_hooks) == 3

    def test_different_root_issues_dont_collapse(self):
        messages = [
            ("cited_content_guard", "warn", "fabricated evidence message"),
            ("lazy_workaround_gate", "warn", "lazy workaround message"),
        ]
        issues = aggregate_raw_messages(messages)
        # lazy_workaround_gate → lazy_closure → collapse group "empty_ack_after_correction"
        # So fabricated_evidence and empty_ack_after_correction are different root issues
        root_issues = {i.root_issue for i in issues}
        assert "fabricated_evidence" in root_issues
        assert "empty_ack_after_correction" in root_issues

    def test_confidence_upgrade_on_higher_confidence_duplicate(self):
        messages = [
            ("tool_sanity", "warn", "low confidence message"),
            ("cited_content_guard", "warn", "high confidence fabricated evidence"),
        ]
        issues = aggregate_raw_messages(messages)
        fabricated = next(i for i in issues if i.root_issue == "fabricated_evidence")
        assert fabricated.confidence == "high"


# ---------------------------------------------------------------------------
# Prioritization tests
# ---------------------------------------------------------------------------

class TestPrioritization:
    def test_blocks_come_first(self):
        messages = [
            ("lazy_workaround_gate", "warn", "lazy closure warning"),
            ("safety_gate", "block", "destructive risk block"),
            ("diagnostic_analysis_quality", "warn", "diagnostic incomplete warning"),
        ]
        issues = aggregate_raw_messages(messages)
        assert issues[0].severity == "block"
        assert issues[0].root_issue == "destructive_risk"

    def test_warns_limited_to_max(self):
        messages = [
            ("lazy_workaround_gate", "warn", "lazy 1"),
            ("diagnostic_analysis_quality", "warn", "diagnostic 1"),
            ("narrative_intent", "warn", "narrative 1"),
            ("assumption_audit", "warn", "assumption 1"),
            ("epistemic_contract", "warn", "epistemic 1"),
        ]
        issues = aggregate_raw_messages(messages)
        warns = [i for i in issues if i.severity == "warn"]
        # _MAX_WARN_MESSAGES = 2
        assert len(warns) <= 2

    def test_info_suppressed_when_strong_issues_exist(self):
        messages = [
            ("safety_gate", "block", "destructive risk"),
            ("overconfidence_detector", "warn", "overconfidence"),
            ("tool_sanity", "info", "tool anomaly info"),
        ]
        issues = aggregate_raw_messages(messages)
        infos = [i for i in issues if i.severity == "info"]
        assert len(infos) == 0  # suppressed due to strong issues

    def test_info_allowed_when_no_strong_issues(self):
        messages = [
            ("tool_sanity", "info", "tool anomaly info"),
            ("self_reflection", "info", "self reflection info"),
        ]
        issues = aggregate_raw_messages(messages)
        infos = [i for i in issues if i.severity == "info"]
        assert len(infos) <= 1


# ---------------------------------------------------------------------------
# Rendering tests
# ---------------------------------------------------------------------------

class TestRendering:
    def test_renders_label_severity_nextstep_signals(self):
        messages = [
            ("cited_content_guard", "warn", "fabricated evidence detected"),
        ]
        result = aggregate_and_render(messages)
        assert "fabricated evidence" in result  # space, not underscore
        assert "warn" in result
        assert "Verify claims" in result  # next step
        assert "cited_content_guard" in result
        assert "Signals:" in result

    def test_renders_multiple_issues(self):
        messages = [
            ("cited_content_guard", "warn", "fabricated evidence detected"),
            ("lazy_workaround_gate", "warn", "lazy closure detected"),
        ]
        result = aggregate_and_render(messages)
        assert "fabricated evidence" in result  # space, not underscore
        # lazy_workaround_gate → lazy_closure → collapse group → "empty ack after correction"
        assert "empty ack after correction" in result

    def test_empty_messages_returns_empty(self):
        result = aggregate_and_render([])
        assert result == ""

    def test_signals_shows_hook_names(self):
        messages = [
            ("cited_content_guard", "warn", "msg1"),
            ("cross_validator", "warn", "msg2"),
        ]
        result = aggregate_and_render(messages)
        assert "cited_content_guard" in result
        assert "cross_validator" in result

    def test_signals_truncated_at_4_hooks(self):
        messages = [
            ("hook1", "warn", "msg"),
            ("hook2", "warn", "msg"),
            ("hook3", "warn", "msg"),
            ("hook4", "warn", "msg"),
            ("hook5", "warn", "msg"),
        ]
        result = aggregate_and_render(messages)
        assert "+1 more" in result or "hook1" in result


# ---------------------------------------------------------------------------
# Env var toggle tests
# ---------------------------------------------------------------------------

class TestEnvVarToggle:
    def test_enabled_by_default(self):
        os.environ.pop("STOP_AGGREGATOR_ENABLED", None)
        messages = [("cited_content_guard", "warn", "msg")]
        result = aggregate_and_render(messages)
        assert result != ""  # aggregation active

    def test_disabled_via_env_var(self):
        os.environ["STOP_AGGREGATOR_ENABLED"] = "false"
        try:
            messages = [
                ("cited_content_guard", "warn", "msg1"),
                ("cited_content_guard", "warn", "msg1"),  # duplicate
            ]
            result = aggregate_and_render(messages)
            # When disabled, just dedups without aggregation
            assert "msg1" in result
            # Should still be deduplicated but not aggregated
        finally:
            os.environ.pop("STOP_AGGREGATOR_ENABLED", None)

    def test_various_enabled_values(self):
        for val in ("1", "true", "yes", "on"):
            os.environ["STOP_AGGREGATOR_ENABLED"] = val
            try:
                messages = [("cited_content_guard", "warn", "msg")]
                result = aggregate_and_render(messages)
                assert result != ""  # aggregation active
            finally:
                os.environ.pop("STOP_AGGREGATOR_ENABLED", None)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_none_messages_handled(self):
        result = aggregate_and_render([])
        assert result == ""

    def test_all_blocks_sorted_by_priority(self):
        messages = [
            ("overconfidence_detector", "block", "overconfidence block"),  # unsupported_causal_claim
            ("safety_gate", "block", "destructive block"),  # destructive_risk
            ("cited_content_guard", "block", "fabricated block"),  # fabricated_evidence
        ]
        issues = aggregate_raw_messages(messages)
        blocks = [i for i in issues if i.severity == "block"]
        # destructive_risk should come first (priority 0)
        assert blocks[0].root_issue == "destructive_risk"

    def test_severity_mismatch_doesnt_collapse(self):
        messages = [
            ("cited_content_guard", "warn", "warn message"),
            ("cited_content_guard", "block", "block message"),
        ]
        issues = aggregate_raw_messages(messages)
        # Same root issue but different severity → different entries
        assert len(issues) == 2


# ---------------------------------------------------------------------------
# Integration: render_aggregated
# ---------------------------------------------------------------------------

class TestRenderAggregated:
    def test_renders_list_of_issues(self):
        issues = [
            AggregatedIssue(
                root_issue="fabricated_evidence",
                severity="warn",
                confidence="high",
                primary_message="fabricated evidence detected",
                next_step="Verify claims with evidence",
                source_hooks=["cited_content_guard", "cross_validator"],
            ),
            AggregatedIssue(
                root_issue="lazy_closure",
                severity="warn",
                confidence="medium",
                primary_message="lazy closure detected",
                next_step="Execute the actual fix",
                source_hooks=["lazy_workaround_gate"],
            ),
        ]
        result = render_aggregated(issues)
        assert "fabricated evidence" in result  # space, not underscore
        assert "lazy closure" in result  # space, not underscore
        assert "cited_content_guard" in result
        assert "lazy_workaround_gate" in result

    def test_empty_list_returns_empty(self):
        result = render_aggregated([])
        assert result == ""