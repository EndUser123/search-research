"""Tests for the opportunity-schema validator extensions.

Evidence class: production unit.

Covers spec test cases 5, 7, 14, 15, 19, 20 (validator-facing aspects):

* generic brainstorm without evidence is rejected (test 5);
* user-friction opportunity identifies the user as beneficiary (test 7);
* opportunity includes a falsifier and next evidence (test 14);
* opportunity is distinct from the observed gap (test 15);
* rejected opportunity is tracked to prevent re-proposal (test 19);
* opportunity portfolio includes value, cost, confidence, and disposition (test 20).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from output_validator import validate_aar_report

FIXTURES = Path(__file__).parent / "fixtures"
VALID_REPORT = FIXTURES / "aar_report_valid.json"


def _load_valid() -> dict:
    return json.loads(VALID_REPORT.read_text(encoding="utf-8"))


def _codes(result, severity=None) -> set[str]:
    return {f.code for f in result.findings if severity is None or f.severity == severity}


def _valid_opportunity(**overrides) -> dict:
    """Return a single opportunity that satisfies the new schema."""
    base = {
        "opportunity_id": "OPP-001",
        "title": "Reuse the security scanner from the rejected package",
        "source_classes": ["CAPABILITY_DERIVED"],
        "horizon": "CROSS_SKILL_REUSE",
        "mechanism": "REUSE",
        "supporting_event_ids": ["chat_history-L000001-S000000"],
        "observed_evidence": "scanner.py was discovered during the package review",
        "interpretation": "the scanner can be invoked independently of the surrounding orchestrator",
        "value_expected": "fewer duplicate scanners across install paths",
        "beneficiary": "multi-package install workflow",
        "frequency_or_reach": "once per package addition",
        "disposition": "INVESTIGATE",
        "falsifier": "scanner may depend on the surrounding orchestrator's state",
        "next_evidence_needed": "test scanner against a clean package without the parent",
        "lifecycle": {
            "hypothesis": "scanner reuse reduces duplication",
            "evidence_needed": "track reuse across 3 future installs",
            "success_signal": "scanner used in 2+ paths without re-implementation",
            "failure_signal": "each path re-implements its own scanner",
            "review_trigger": "after 3 installs",
            "retirement_condition": "if scanner is removed upstream",
        },
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Generic-opportunity blocklist (test case 5)
# ---------------------------------------------------------------------------


def test_generic_opportunity_title_rejected():
    data = _load_valid()
    data["opportunity_candidates"] = [_valid_opportunity(title="add validation")]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_GENERIC_TITLE" in _codes(r, "blocker")


def test_concrete_opportunity_title_accepted():
    data = _load_valid()
    data["opportunity_candidates"] = [_valid_opportunity(title="Add validation for the credential preflight")]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_GENERIC_TITLE" not in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Required fields (test case 14)
# ---------------------------------------------------------------------------


def test_opportunity_missing_falsifier_is_blocker():
    data = _load_valid()
    opp = _valid_opportunity()
    del opp["falsifier"]
    data["opportunity_candidates"] = [opp]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_MISSING_FIELD" in _codes(r, "blocker")


def test_opportunity_missing_next_evidence_is_blocker():
    data = _load_valid()
    opp = _valid_opportunity()
    del opp["next_evidence_needed"]
    data["opportunity_candidates"] = [opp]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_MISSING_FIELD" in _codes(r, "blocker")


def test_opportunity_missing_beneficiary_is_blocker():
    data = _load_valid()
    opp = _valid_opportunity()
    del opp["beneficiary"]
    data["opportunity_candidates"] = [opp]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_MISSING_FIELD" in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Opportunity ≠ gap (test case 15)
# ---------------------------------------------------------------------------


def test_opportunity_confuses_gap_with_opportunity_is_blocker():
    """If observed_evidence and interpretation are identical, the report is
    jumping from symptom to solution without an interpretation step."""
    data = _load_valid()
    same_text = "scanner.py was discovered during the review"
    opp = _valid_opportunity(observed_evidence=same_text, interpretation=same_text)
    data["opportunity_candidates"] = [opp]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_CONFUSES_GAP_WITH_OPPORTUNITY" in _codes(r, "blocker")


def test_opportunity_distinct_observation_and_interpretation_accepted():
    data = _load_valid()
    data["opportunity_candidates"] = [_valid_opportunity()]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_CONFUSES_GAP_WITH_OPPORTUNITY" not in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Enum validity
# ---------------------------------------------------------------------------


def test_invalid_source_class_is_blocker():
    data = _load_valid()
    opp = _valid_opportunity(source_classes=["NOT_A_REAL_CLASS"])
    data["opportunity_candidates"] = [opp]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_SOURCE_CLASS_INVALID" in _codes(r, "blocker")


def test_invalid_horizon_is_blocker():
    data = _load_valid()
    opp = _valid_opportunity(horizon="NEVER")
    data["opportunity_candidates"] = [opp]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_HORIZON_INVALID" in _codes(r, "blocker")


def test_invalid_mechanism_is_blocker():
    data = _load_valid()
    opp = _valid_opportunity(mechanism="MAGIC")
    data["opportunity_candidates"] = [opp]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_MECHANISM_INVALID" in _codes(r, "blocker")


def test_invalid_disposition_is_blocker():
    data = _load_valid()
    opp = _valid_opportunity(disposition="JUST_DO_IT")
    data["opportunity_candidates"] = [opp]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_DISPOSITION_INVALID" in _codes(r, "blocker")


def test_new_disposition_simply_or_remove_accepted():
    """Spec Section 14 added SIMPLIFY_OR_REMOVE — must be valid."""
    data = _load_valid()
    opp = _valid_opportunity(disposition="SIMPLIFY_OR_REMOVE")
    opp.pop("lifecycle")  # not required for this disposition
    data["opportunity_candidates"] = [opp]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_DISPOSITION_INVALID" not in _codes(r, "blocker")
    assert "OPPORTUNITY_LIFECYCLE_MISSING" not in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Lifecycle requirement (test case 16: monitored hypothesis not durable policy)
# ---------------------------------------------------------------------------


def test_monitor_disposition_requires_lifecycle():
    data = _load_valid()
    opp = _valid_opportunity(disposition="MONITOR")
    opp.pop("lifecycle")
    data["opportunity_candidates"] = [opp]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_LIFECYCLE_MISSING" in _codes(r, "blocker")


def test_monitor_lifecycle_must_have_success_and_failure_signals():
    data = _load_valid()
    opp = _valid_opportunity(disposition="MONITOR")
    opp["lifecycle"] = {"hypothesis": "x", "success_signal": "", "failure_signal": "", "retirement_condition": ""}
    data["opportunity_candidates"] = [opp]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_LIFECYCLE_INCOMPLETE" in _codes(r, "blocker")


def test_act_now_does_not_require_lifecycle():
    data = _load_valid()
    opp = _valid_opportunity(disposition="ACT_NOW")
    opp.pop("lifecycle")
    data["opportunity_candidates"] = [opp]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_LIFECYCLE_MISSING" not in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Value accounting
# ---------------------------------------------------------------------------


def test_value_accounting_unknown_category_is_warning():
    data = _load_valid()
    data["value_accounting"] = {"NOT_A_CATEGORY": [{"description": "x"}]}
    r = validate_aar_report(data)
    assert "VALUE_CATEGORY_UNKNOWN" in _codes(r, "warning")


def test_value_accounting_entry_needs_description():
    data = _load_valid()
    data["value_accounting"] = {"VALUE_CREATED": [{"description": ""}]}
    r = validate_aar_report(data)
    assert "VALUE_ENTRY_MISSING_DESCRIPTION" in _codes(r, "warning")


def test_value_accounting_all_seven_categories_can_be_empty():
    """Spec: 'Do not force every category to contain an item.'"""
    data = _load_valid()
    data["value_accounting"] = {cat: [] for cat in (
        "VALUE_CREATED", "VALUE_PRESERVED", "VALUE_RECOVERED",
        "VALUE_UNREALIZED", "VALUE_DEFERRED", "VALUE_DESTROYED_OR_COST",
        "VALUE_COMPOUNDED",
    )}
    r = validate_aar_report(data)
    # No warnings: empty lists are valid.
    assert "VALUE_ENTRY_MISSING_DESCRIPTION" not in _codes(r, "warning")


# ---------------------------------------------------------------------------
# Portfolio / inflation / rejected tracking (test cases 19, 20)
# ---------------------------------------------------------------------------


def test_rejected_opportunities_should_be_tracked():
    """Test case 19: rejected opportunity retained to prevent re-proposal."""
    data = _load_valid()
    opp = _valid_opportunity(opportunity_id="OPP-REJ", disposition="REJECT")
    opp.pop("lifecycle")
    data["opportunity_candidates"] = [opp]
    # No rejected_opportunities ledger provided
    r = validate_aar_report(data)
    assert "REJECTED_OPPORTUNITIES_NOT_TRACKED" in _codes(r, "warning")


def test_rejected_opportunities_ledger_satisfies_warning():
    data = _load_valid()
    opp = _valid_opportunity(opportunity_id="OPP-REJ", disposition="REJECT")
    opp.pop("lifecycle")
    data["opportunity_candidates"] = [opp]
    data["rejected_opportunities"] = [{
        "opportunity_id": "OPP-REJ",
        "title": opp["title"],
        "rejection_reason": "duplicate",
    }]
    r = validate_aar_report(data)
    assert "REJECTED_OPPORTUNITIES_NOT_TRACKED" not in _codes(r, "warning")


def test_opportunity_inflation_warning_at_30_plus():
    """Spec Section 15: avoid speculative opportunity inflation."""
    data = _load_valid()
    opps = []
    for i in range(31):
        o = _valid_opportunity(opportunity_id=f"OPP-{i:03d}", disposition="ACT_NOW")
        o.pop("lifecycle")
        opps.append(o)
    data["opportunity_candidates"] = opps
    r = validate_aar_report(data)
    assert "OPPORTUNITY_INFLATION" in _codes(r, "warning")


# ---------------------------------------------------------------------------
# Beneficiary check (test case 7)
# ---------------------------------------------------------------------------


def test_friction_opportunity_with_empty_beneficiary_blocked():
    """Test case 7: friction opportunity must identify the beneficiary."""
    data = _load_valid()
    opp = _valid_opportunity(
        source_classes=["USER_EXPERIENCE_DERIVED"],
        beneficiary="",
    )
    data["opportunity_candidates"] = [opp]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_MISSING_FIELD" in _codes(r, "blocker")


def test_friction_opportunity_with_user_beneficiary_accepted():
    data = _load_valid()
    opp = _valid_opportunity(
        source_classes=["USER_EXPERIENCE_DERIVED"],
        beneficiary="the user (reduces correction burden)",
    )
    data["opportunity_candidates"] = [opp]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_MISSING_FIELD" not in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Valid full report still passes
# ---------------------------------------------------------------------------


def test_valid_report_fixture_still_passes_with_opportunity_schema():
    r = validate_aar_report(_load_valid())
    assert r.passed, f"valid fixture should pass: {r.summary}"
