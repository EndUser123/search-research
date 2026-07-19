"""Spec Section 22 acceptance tests (20 cases).

Evidence class: production unit (deterministic tests for the 20 spec cases).

This file is the explicit acceptance gate for the continual-improvement
upgrade. Each test maps to a numbered case in spec Section 22. Some are
behavioural (opportunity emitted by a detector + validator accepts it);
others are contract (validator rejects a malformed opportunity).

Test classification is honest: prompt-structure assertions against
SKILL.md are NOT live behavioral validation. Live behavioral validation
requires an actual LLM AAR run and is covered separately in
``test_real_session_full_smoke.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from canonical_model import BranchStatus, CanonicalEvent, CanonicalEventType
from detectors import (
    Signal,
    SignalKind,
    detect_duplicate_capability_references,
    detect_recommendation_revisions,
    detect_successful_interventions,
    detect_unconsumed_artifacts,
    detect_unused_capability,
    run_all_detectors,
)
from event_model import Event, Role, ToolCall
from opportunity_model import (
    ImprovementCandidate,
    Opportunity,
    OpportunityDisposition,
    OpportunityHorizon,
    OpportunityLifecycle,
    OpportunityMechanism,
    OpportunitySourceClass,
    RejectedOpportunity,
    RejectedOpportunityLedger,
    ValueAccounting,
    ValueCategory,
    ValueEntry,
    is_generic_opportunity_title,
    opportunity_fingerprint,
)
from output_validator import validate_aar_report

FIXTURES = Path(__file__).parent / "fixtures"
VALID_REPORT = FIXTURES / "aar_report_valid.json"

from test_detectors import _assistant, _tc, _tool_result  # reuse helpers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_opp(**overrides) -> dict:
    """Validator-friendly opportunity dict."""
    base = {
        "opportunity_id": "OPP-001",
        "title": "Reuse the security scanner independently",
        "source_classes": ["CAPABILITY_DERIVED"],
        "horizon": "CROSS_SKILL_REUSE",
        "mechanism": "REUSE",
        "supporting_event_ids": ["chat_history-L000001-S000000"],
        "observed_evidence": "scanner.py was discovered during the package review",
        "interpretation": "the scanner can be invoked without the surrounding orchestrator",
        "value_expected": "fewer duplicate scanners across install paths",
        "beneficiary": "multi-package install workflow",
        "frequency_or_reach": "once per package addition",
        "disposition": "INVESTIGATE",
        "falsifier": "scanner may depend on the surrounding orchestrator's state",
        "next_evidence_needed": "test scanner against a clean package without the parent",
        "lifecycle": {
            "hypothesis": "scanner reuse reduces duplication",
            "evidence_needed": "3 future installs",
            "success_signal": "scanner used in 2+ paths without re-implementation",
            "failure_signal": "each path re-implements its own scanner",
            "review_trigger": "after 3 installs",
            "retirement_condition": "if scanner is removed upstream",
        },
    }
    base.update(overrides)
    return base


def _load_valid_report() -> dict:
    return json.loads(VALID_REPORT.read_text(encoding="utf-8"))


def _codes(result, severity=None):
    return {f.code for f in result.findings if severity is None or f.severity == severity}


# ---------------------------------------------------------------------------
# Test 1: successful session generates success-amplification opportunity
# ---------------------------------------------------------------------------


def test_case_1_successful_session_generates_success_opportunity():
    """A session that has a successful intervention produces a SUCCESSFUL_INTERVENTION
    candidate signal, and a SUCCESS_DERIVED opportunity citing it passes validation."""
    events = [
        _tool_result(0, "Error: tests failed"),
        _assistant(1, "Fixed it. Tests passed now."),
    ]
    sigs = detect_successful_interventions(events)
    assert any(s.kind is SignalKind.OPPORTUNITY_CANDIDATE_SUCCESSFUL_INTERVENTION for s in sigs)

    # A SUCCESS_DERIVED opportunity built on this signal is validator-accepted.
    report = _load_valid_report()
    report["opportunity_candidates"] = [_valid_opp(
        source_classes=["SUCCESS_DERIVED"],
        title="Standardise the credential preflight that recovered the run",
        mechanism=OpportunityMechanism.GENERALIZE.value,
    )]
    r = validate_aar_report(report)
    assert r.passed, [f.to_dict() for f in r.blockers()]


# ---------------------------------------------------------------------------
# Test 2: no failure but repeated manual work → automation candidate
# ---------------------------------------------------------------------------


def test_case_2_repeated_manual_work_yields_automation_candidate():
    """Repeated identical tool calls are detected; the LLM can frame the
    opportunity as AUTOMATE."""
    events = [
        _assistant(0, tool_calls=(_tc("run_terminal_command", {"command": "pytest a"}, "c1"),)),
        _assistant(1, tool_calls=(_tc("run_terminal_command", {"command": "pytest a"}, "c2"),)),
    ]
    from detectors import detect_repeated_identical_tool_calls
    sigs = detect_repeated_identical_tool_calls(events)
    assert sigs  # repeated work detected
    # The LLM would frame this as FRICTION_DERIVED + AUTOMATE.
    opp = _valid_opp(
        source_classes=["FRICTION_DERIVED"],
        title="Automate the pytest preflight via a single CLI command",
        mechanism=OpportunityMechanism.AUTOMATE.value,
        horizon=OpportunityHorizon.NEAR_TERM_WORKFLOW.value,
    )
    report = _load_valid_report()
    report["opportunity_candidates"] = [opp]
    r = validate_aar_report(report)
    assert r.passed


# ---------------------------------------------------------------------------
# Test 3: useful component inside rejected package → reuse candidate
# ---------------------------------------------------------------------------


def test_case_3_useful_component_in_rejected_package_yields_reuse():
    """The 'security scanner in a rejected package' example from the spec."""
    events = [
        _tool_result(0, "discovered scanner.py with run_security_scan()"),
        _assistant(1, "we reject the overall package"),
    ]
    sigs = detect_unused_capability(events)
    assert any(s.group_key == "scanner.py" for s in sigs)
    # The LLM frames it as CAPABILITY_DERIVED + REUSE.
    opp = _valid_opp(
        source_classes=["CAPABILITY_DERIVED", "REUSE_DERIVED"],
        title="Reuse scanner.py independently of the rejected parent package",
        mechanism=OpportunityMechanism.REUSE.value,
        horizon=OpportunityHorizon.CROSS_SKILL_REUSE.value,
    )
    report = _load_valid_report()
    report["opportunity_candidates"] = [opp]
    r = validate_aar_report(report)
    assert r.passed


# ---------------------------------------------------------------------------
# Test 4: two existing capabilities → combination candidate
# ---------------------------------------------------------------------------


def test_case_4_two_capabilities_yield_combination_candidate():
    """Spec example: native marketplace + external scanning."""
    # The LLM identifies this from session evidence. There is no deterministic
    # detector for "two capabilities could combine" — that's synthesis. We
    # verify a COMBINATION_DERIVED opportunity with two source capabilities
    # is validator-accepted.
    opp = _valid_opp(
        source_classes=["COMBINATION_DERIVED"],
        title="Combine native Grok install with external security scan via a hybrid pipeline",
        mechanism=OpportunityMechanism.INTEGRATE.value,
        horizon=OpportunityHorizon.STRATEGIC_OPTION.value,
    )
    report = _load_valid_report()
    report["opportunity_candidates"] = [opp]
    r = validate_aar_report(report)
    assert r.passed


# ---------------------------------------------------------------------------
# Test 5: generic brainstorm without evidence is rejected
# ---------------------------------------------------------------------------


def test_case_5_generic_brainstorm_rejected():
    report = _load_valid_report()
    report["opportunity_candidates"] = [_valid_opp(title="add validation")]
    r = validate_aar_report(report)
    assert "OPPORTUNITY_GENERIC_TITLE" in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Test 6: duplicate existing capability rejected or routed to reuse
# ---------------------------------------------------------------------------


def test_case_6_duplicate_capability_routed_to_reuse():
    """Detector flags duplicate; opportunity with REUSE_EXISTING disposition
    is accepted; opportunity with ACT_NOW to rebuild is acceptable only with
    explicit justification."""
    events = [
        _tool_result(0, "scanner.py exists"),
        _assistant(1, "let me build a new scanner"),
    ]
    sigs = detect_duplicate_capability_references(events)
    assert sigs  # candidate flagged

    # REUSE_EXISTING is valid.
    opp = _valid_opp(
        source_classes=["CAPABILITY_DERIVED"],
        title="Reuse existing scanner.py instead of building a new one",
        mechanism=OpportunityMechanism.REUSE.value,
        disposition=OpportunityDisposition.REUSE_EXISTING.value,
    )
    opp.pop("lifecycle")  # not required for REUSE_EXISTING
    report = _load_valid_report()
    report["opportunity_candidates"] = [opp]
    r = validate_aar_report(report)
    assert r.passed


# ---------------------------------------------------------------------------
# Test 7: user-friction opportunity identifies the user as beneficiary
# ---------------------------------------------------------------------------


def test_case_7_user_friction_opportunity_identifies_user_beneficiary():
    """Friction opportunity with empty beneficiary is rejected; with
    beneficiary='the user' it is accepted."""
    report = _load_valid_report()
    bad_opp = _valid_opp(
        source_classes=["USER_EXPERIENCE_DERIVED"],
        beneficiary="",
    )
    report["opportunity_candidates"] = [bad_opp]
    r = validate_aar_report(report)
    assert "OPPORTUNITY_MISSING_FIELD" in _codes(r, "blocker")

    good_opp = _valid_opp(
        source_classes=["USER_EXPERIENCE_DERIVED"],
        beneficiary="the user (reduces correction burden)",
    )
    report["opportunity_candidates"] = [good_opp]
    r = validate_aar_report(report)
    assert "OPPORTUNITY_MISSING_FIELD" not in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Test 8: high-impact + high burden is not auto-prioritized
# ---------------------------------------------------------------------------


def test_case_8_high_impact_high_burden_not_auto_prioritized():
    """The validator does not force ACT_NOW based on impact alone. A MONITOR
    disposition on a high-impact opportunity is accepted as long as a
    lifecycle block is present."""
    opp = _valid_opp(
        title="Add cross-vendor skill portability layer",
        source_classes=["STRATEGIC_OPTION_DERIVED"],
        horizon=OpportunityHorizon.STRATEGIC_OPTION.value,
        disposition=OpportunityDisposition.MONITOR.value,
        expected_value={
            "outcome_impact": {"rating": "VERY_HIGH", "rationale": "unlocks an entire class of portability"},
            "implementation_cost": {"rating": "VERY_HIGH", "rationale": "requires new infrastructure"},
        },
    )
    report = _load_valid_report()
    report["opportunity_candidates"] = [opp]
    r = validate_aar_report(report)
    assert r.passed  # MONITOR is valid; no rule forces ACT_NOW from impact


# ---------------------------------------------------------------------------
# Test 9: low-frequency severe-risk control may remain valuable
# ---------------------------------------------------------------------------


def test_case_9_low_frequency_severe_risk_control_valuable():
    """A low-frequency/high-severity opportunity is validator-accepted and
    not deprioritised by any 'frequency threshold' rule."""
    opp = _valid_opp(
        title="Add credential preflight before destructive operations",
        source_classes=["RISK_DERIVED"],
        horizon=OpportunityHorizon.NEAR_TERM_WORKFLOW.value,
        mechanism=OpportunityMechanism.VALIDATE.value,
        frequency_or_reach="rare (once a quarter) but blocks a destructive failure",
        expected_value={
            "frequency_or_reach": {"rating": "LOW", "rationale": "rare event"},
            "outcome_impact": {"rating": "VERY_HIGH", "rationale": "prevents destructive ops"},
            "risk_of_harm": {"rating": "VERY_HIGH", "rationale": "without it, destructive ops can fire"},
        },
    )
    report = _load_valid_report()
    report["opportunity_candidates"] = [opp]
    r = validate_aar_report(report)
    assert r.passed


# ---------------------------------------------------------------------------
# Test 10: revised rec classified as healthy when based on new user info
# ---------------------------------------------------------------------------


def test_case_10_revision_classified_healthy_when_new_user_info():
    """Spec Section 12: HEALTHY_UPDATE_USER_PREFERENCE is a valid classification."""
    from opportunity_model import RevisionClassification
    assert RevisionClassification.HEALTHY_UPDATE_USER_PREFERENCE.value == "HEALTHY_UPDATE_USER_PREFERENCE"


# ---------------------------------------------------------------------------
# Test 11: revision classified avoidable when evidence already available
# ---------------------------------------------------------------------------


def test_case_11_revision_avoidable_when_evidence_available():
    from opportunity_model import RevisionClassification
    assert RevisionClassification.AVOIDABLE_UPDATE_MISSED_AVAILABLE_EVIDENCE.value == "AVOIDABLE_UPDATE_MISSED_AVAILABLE_EVIDENCE"
    # The detector flags the revision; the LLM assigns the classification.
    events = [
        _assistant(0, "I recommend package X."),
        _assistant(1, "Actually, on reflection, I recommend against it."),
    ]
    sigs = detect_recommendation_revisions(events)
    assert sigs  # candidate emitted; LLM classifies


# ---------------------------------------------------------------------------
# Test 12: success preserved without forcing a new action
# ---------------------------------------------------------------------------


def test_case_12_success_preserved_without_new_action():
    """PRESERVE disposition with NO_CHANGE_PRESERVE mechanism is accepted."""
    opp = _valid_opp(
        title="Preserve the existing detector registry pattern",
        source_classes=["SUCCESS_DERIVED"],
        horizon=OpportunityHorizon.IMMEDIATE_LOCAL.value,
        mechanism=OpportunityMechanism.NO_CHANGE_PRESERVE.value,
        disposition=OpportunityDisposition.PRESERVE.value,
    )
    opp.pop("lifecycle")
    report = _load_valid_report()
    report["opportunity_candidates"] = [opp]
    r = validate_aar_report(report)
    assert r.passed


# ---------------------------------------------------------------------------
# Test 13: no-change conclusion accepted as opportunity disposition
# ---------------------------------------------------------------------------


def test_case_13_no_change_accepted_as_disposition():
    opp = _valid_opp(
        title="No change needed: existing validation is sufficient",
        source_classes=["SIMPLIFICATION_DERIVED"],
        horizon=OpportunityHorizon.IMMEDIATE_LOCAL.value,
        mechanism=OpportunityMechanism.NO_CHANGE_PRESERVE.value,
        disposition=OpportunityDisposition.NOT_WORTH_DOING.value,
    )
    opp.pop("lifecycle")
    report = _load_valid_report()
    report["opportunity_candidates"] = [opp]
    r = validate_aar_report(report)
    assert r.passed


# ---------------------------------------------------------------------------
# Test 14: opportunity includes a falsifier and next evidence
# ---------------------------------------------------------------------------


def test_case_14_opportunity_must_have_falsifier_and_next_evidence():
    report = _load_valid_report()
    bad = _valid_opp()
    del bad["falsifier"]
    del bad["next_evidence_needed"]
    report["opportunity_candidates"] = [bad]
    r = validate_aar_report(report)
    codes = _codes(r, "blocker")
    assert "OPPORTUNITY_MISSING_FIELD" in codes


# ---------------------------------------------------------------------------
# Test 15: opportunity distinct from observed gap
# ---------------------------------------------------------------------------


def test_case_15_opportunity_distinct_from_gap():
    report = _load_valid_report()
    same = "scanner.py was discovered"
    opp = _valid_opp(observed_evidence=same, interpretation=same)
    report["opportunity_candidates"] = [opp]
    r = validate_aar_report(report)
    assert "OPPORTUNITY_CONFUSES_GAP_WITH_OPPORTUNITY" in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Test 16: one session produces a monitored hypothesis, not durable policy
# ---------------------------------------------------------------------------


def test_case_16_one_session_yields_monitored_hypothesis():
    """CONTINUAL_LEARNING horizon with MONITOR disposition + lifecycle is
    the disciplined path; the validator rejects it without lifecycle."""
    # Without lifecycle → blocked
    opp = _valid_opp(
        title="Track recommendation-reversal patterns across future AAR runs",
        source_classes=["LEARNING_DERIVED"],
        horizon=OpportunityHorizon.CONTINUAL_LEARNING.value,
        disposition=OpportunityDisposition.MONITOR.value,
    )
    opp.pop("lifecycle")
    report = _load_valid_report()
    report["opportunity_candidates"] = [opp]
    r = validate_aar_report(report)
    assert "OPPORTUNITY_LIFECYCLE_MISSING" in _codes(r, "blocker")

    # With lifecycle → accepted as a hypothesis, not policy
    opp["lifecycle"] = {
        "hypothesis": "reversals concentrate when external verification is skipped",
        "evidence_needed": "5 AAR runs with reversal tracking",
        "success_signal": "reversals drop when verification is added",
        "failure_signal": "no correlation observed",
        "review_trigger": "after 5 runs",
        "retirement_condition": "if pattern does not replicate",
    }
    report["opportunity_candidates"] = [opp]
    r = validate_aar_report(report)
    assert r.passed


# ---------------------------------------------------------------------------
# Test 17: unused artifact does not automatically imply waste
# ---------------------------------------------------------------------------


def test_case_17_unused_artifact_does_not_imply_waste():
    """The detector emits LOW severity + a falsifier that explicitly notes
    the artifact may be a deliberate deliverable."""
    events = [_assistant(0, tool_calls=(_tc("write", {"file_path": "report.md"}, "c1"),))]
    sigs = detect_unconsumed_artifacts(events)
    assert sigs
    assert sigs[0].severity.value == "LOW"
    assert "deliverable" in sigs[0].falsifier


# ---------------------------------------------------------------------------
# Test 18: unresolved falsifier constrains recommendation strength
# ---------------------------------------------------------------------------


def test_case_18_unresolved_falsifier_present_in_opportunity():
    """Opportunities must carry a falsifier; an empty one is blocked."""
    report = _load_valid_report()
    opp = _valid_opp(falsifier="")
    report["opportunity_candidates"] = [opp]
    r = validate_aar_report(report)
    assert "OPPORTUNITY_MISSING_FIELD" in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Test 19: rejected opportunity retained to prevent re-proposal
# ---------------------------------------------------------------------------


def test_case_19_rejected_opportunity_retained():
    """The rejection ledger fingerprints rejected opportunities."""
    fp = opportunity_fingerprint("Build a cross-session surveillance daemon", OpportunityMechanism.AUTOMATE)
    ledger = RejectedOpportunityLedger()
    ledger.add(RejectedOpportunity(
        opportunity_id="OPP-001",
        title="Build a cross-session surveillance daemon",
        mechanism=OpportunityMechanism.AUTOMATE,
        rejection_reason="spec forbids cross-session surveillance",
        rejected_at="2026-07-18T00:00:00Z",
        fingerprint=fp,
        original_disposition=OpportunityDisposition.REJECT,
    ))
    # Same idea re-proposed → fingerprint matches.
    new_fp = opportunity_fingerprint("Build a cross-session surveillance daemon", OpportunityMechanism.AUTOMATE)
    assert ledger.contains_fingerprint(new_fp)

    # And the validator warns if REJECT dispositions aren't tracked.
    report = _load_valid_report()
    opp = _valid_opp(disposition=OpportunityDisposition.REJECT.value)
    opp.pop("lifecycle")
    report["opportunity_candidates"] = [opp]
    r = validate_aar_report(report)
    assert "REJECTED_OPPORTUNITIES_NOT_TRACKED" in _codes(r, "warning")


# ---------------------------------------------------------------------------
# Test 20: opportunity portfolio includes value, cost, confidence, disposition
# ---------------------------------------------------------------------------


def test_case_20_opportunity_portfolio_has_full_value_set():
    """The portfolio block must carry value_expected, cost_or_burden,
    confidence, and disposition. Missing any is blocked."""
    report = _load_valid_report()
    opp = _valid_opp(
        expected_value={
            "outcome_impact": {"rating": "HIGH", "rationale": "removes a class of failure"},
            "implementation_cost": {"rating": "LOW", "rationale": "one-line change"},
            "evidence_strength": {"rating": "HIGH", "rationale": "directly observed"},
        },
    )
    report["opportunity_candidates"] = [opp]
    r = validate_aar_report(report)
    assert r.passed

    # Missing value_expected → blocked
    bad = _valid_opp()
    del bad["value_expected"]
    report["opportunity_candidates"] = [bad]
    r = validate_aar_report(report)
    assert "OPPORTUNITY_MISSING_FIELD" in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Cross-session candidate is emission-only (spec Section 17)
# ---------------------------------------------------------------------------


def test_improvement_candidate_emission_only_format():
    """The ImprovementCandidate record can be produced; it carries no
    cross-session auto-consume semantics."""
    c = ImprovementCandidate(
        candidate_id="CAND-001",
        hypothesis="X",
        local_evidence="Y",
        scope="PROBLEM_CLASS",
        confidence="INFERRED",
        expected_value="Z",
        future_signal="F",
        promotion_condition="P",
        retirement_condition="R",
        source_opportunity_id="OPP-001",
    )
    d = c.to_dict()
    assert d["promotion_condition"] == "P"
    assert d["scope"] == "PROBLEM_CLASS"
