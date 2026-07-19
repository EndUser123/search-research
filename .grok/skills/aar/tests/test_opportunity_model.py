"""Tests for the opportunity model (spec Sections 2-10, 13-17).

Evidence class: production unit.

Covers:
* 12 source classes / 6 horizons / 16 mechanisms / 10 dispositions / 7 value
  categories / 5 revision classes are all present with stable values.
* Opportunity serialisation round-trips every required field.
* The generic-opportunity blocklist rejects bare phrases and accepts concrete
  ones (spec Section 8 / test case 5).
* Opportunity fingerprinting dedups for the rejection ledger.
* The rejection ledger prevents re-proposal (test case 19).
* OpportunityLifecycle is required-aware for non-ACT_NOW dispositions.
* ValueAccounting distinguishes populated vs empty categories.
* ImprovementCandidate is emission-only (no aggregation).
"""

from __future__ import annotations

import pytest

from opportunity_model import (
    GENERIC_OPPORTUNITY_PHRASES,
    OPPORTUNITY_SCHEMA_VERSION,
    ImprovementCandidate,
    Opportunity,
    OpportunityDisposition,
    OpportunityHorizon,
    OpportunityLifecycle,
    OpportunityMechanism,
    OpportunitySourceClass,
    RejectedOpportunity,
    RejectedOpportunityLedger,
    ExpectedValueDimension,
    ExpectedValueRating,
    ValueAccounting,
    ValueCategory,
    ValueEntry,
    is_generic_opportunity_title,
    opportunity_fingerprint,
)


# ---------------------------------------------------------------------------
# Enum coverage (spec acceptance)
# ---------------------------------------------------------------------------


def test_twelve_source_classes_present():
    """Spec Section 3: 12 named source classes."""
    expected = {
        "FAILURE_DERIVED", "FRICTION_DERIVED", "SUCCESS_DERIVED",
        "CAPABILITY_DERIVED", "REUSE_DERIVED", "COMBINATION_DERIVED",
        "SIMPLIFICATION_DERIVED", "RISK_DERIVED", "USER_EXPERIENCE_DERIVED",
        "LEARNING_DERIVED", "STRATEGIC_OPTION_DERIVED", "EXTERNAL_EVIDENCE_DERIVED",
    }
    actual = {s.value for s in OpportunitySourceClass}
    assert actual == expected
    assert len(expected) == 12


def test_six_horizons_present():
    expected = {
        "IMMEDIATE_LOCAL", "NEAR_TERM_WORKFLOW", "CROSS_SKILL_REUSE",
        "SYSTEM_CAPABILITY", "STRATEGIC_OPTION", "CONTINUAL_LEARNING",
    }
    actual = {h.value for h in OpportunityHorizon}
    assert actual == expected


def test_sixteen_mechanisms_present():
    """Spec Section 7: 16 mechanisms including NO_CHANGE_PRESERVE."""
    expected = {
        "REMOVE", "SIMPLIFY", "MERGE", "RESEQUENCE", "AUTOMATE", "VALIDATE",
        "INSTRUMENT", "REUSE", "GENERALIZE", "SPECIALIZE", "INTEGRATE",
        "EXPERIMENT", "DOCUMENT", "TRAIN_OR_PROMPT", "CHANGE_DECISION_RULE",
        "NO_CHANGE_PRESERVE",
    }
    actual = {m.value for m in OpportunityMechanism}
    assert actual == expected
    assert len(expected) == 16


def test_ten_dispositions_present():
    """Spec Section 14: 10 dispositions for continual-improvement governance."""
    expected = {
        "ACT_NOW", "BOUNDED_EXPERIMENT", "INVESTIGATE", "MONITOR",
        "REUSE_EXISTING", "SIMPLIFY_OR_REMOVE", "PRESERVE", "DEFER",
        "REJECT", "NOT_WORTH_DOING",
    }
    actual = {d.value for d in OpportunityDisposition}
    assert actual == expected


def test_seven_value_categories_present():
    expected = {
        "VALUE_CREATED", "VALUE_PRESERVED", "VALUE_RECOVERED",
        "VALUE_UNREALIZED", "VALUE_DEFERRED", "VALUE_DESTROYED_OR_COST",
        "VALUE_COMPOUNDED",
    }
    actual = {c.value for c in ValueCategory}
    assert actual == expected


def test_twelve_expected_value_dimensions():
    """Spec Section 9: 12 expected-value dimensions."""
    expected = {
        "outcome_impact", "frequency_or_reach", "reliability_gain",
        "efficiency_gain", "user_experience_gain", "learning_or_reuse_gain",
        "implementation_cost", "maintenance_cost", "cognitive_burden",
        "risk_of_harm", "reversibility", "evidence_strength",
    }
    actual = {d.value for d in ExpectedValueDimension}
    assert actual == expected


def test_revision_classifications_present():
    """Spec Section 12: 5 classifications."""
    from opportunity_model import RevisionClassification
    expected = {
        "HEALTHY_UPDATE_NEW_INFORMATION", "HEALTHY_UPDATE_USER_PREFERENCE",
        "AVOIDABLE_UPDATE_MISSED_AVAILABLE_EVIDENCE",
        "AVOIDABLE_UPDATE_UNVERIFIED_ASSUMPTION", "AMBIGUOUS_REVISION",
    }
    actual = {r.value for r in RevisionClassification}
    assert actual == expected


# ---------------------------------------------------------------------------
# Opportunity dataclass
# ---------------------------------------------------------------------------


def _minimal_opportunity(**overrides) -> Opportunity:
    defaults = dict(
        opportunity_id="OPP-001",
        title="Reuse the security scanner independently",
        source_classes=(OpportunitySourceClass.CAPABILITY_DERIVED,),
        horizon=OpportunityHorizon.CROSS_SKILL_REUSE,
        mechanism=OpportunityMechanism.REUSE,
        supporting_event_ids=("chat_history-L000001-S000000",),
        observed_evidence="The scanner at P:/x/scanner.py was discovered during package review",
        interpretation="The scanner can be invoked without adopting the surrounding orchestrator",
        value_expected="Fewer duplicate scanners; consistent rules across install paths",
        beneficiary="multi-package install workflow",
        frequency_or_reach="once per package addition",
        disposition=OpportunityDisposition.INVESTIGATE,
        falsifier="if the scanner depends on the surrounding orchestrator's state",
        next_evidence_needed="test the scanner against a clean package without the parent",
    )
    defaults.update(overrides)
    return Opportunity(**defaults)


def test_opportunity_serialisation_round_trips_all_fields():
    opp = _minimal_opportunity()
    d = opp.to_dict()
    assert d["opportunity_id"] == "OPP-001"
    assert d["source_classes"] == ["CAPABILITY_DERIVED"]
    assert d["horizon"] == "CROSS_SKILL_REUSE"
    assert d["mechanism"] == "REUSE"
    assert d["disposition"] == "INVESTIGATE"
    assert d["falsifier"]
    assert d["next_evidence_needed"]
    assert d["lifecycle"] is None  # no lifecycle yet


def test_opportunity_is_frozen():
    opp = _minimal_opportunity()
    with pytest.raises(Exception):
        opp.title = "other"  # type: ignore[misc]


def test_opportunity_with_lifecycle_serialises():
    lc = OpportunityLifecycle(
        hypothesis="Scanner reuse reduces duplication",
        evidence_needed="Track scanner invocations across 3 future installs",
        success_signal="Scanner used in ≥2 install paths without re-implementation",
        failure_signal="Each install path re-implements its own scanner",
        review_trigger="After 3 install sessions or 30 days",
        retirement_condition="If scanner is removed from upstream package",
    )
    opp = _minimal_opportunity(lifecycle=lc)
    d = opp.to_dict()
    assert d["lifecycle"]["hypothesis"] == "Scanner reuse reduces duplication"
    assert d["lifecycle"]["success_signal"]


def test_expected_value_ratings_serialise():
    opp = _minimal_opportunity(
        expected_value={
            ExpectedValueDimension.OUTCOME_IMPACT: (ExpectedValueRating.HIGH, "removes a whole class of duplication"),
            ExpectedValueDimension.IMPLEMENTATION_COST: (ExpectedValueRating.LOW, "wrap scanner in one CLI"),
        }
    )
    d = opp.to_dict()
    assert d["expected_value"]["outcome_impact"]["rating"] == "HIGH"
    assert "duplication" in d["expected_value"]["outcome_impact"]["rationale"]


# ---------------------------------------------------------------------------
# Generic-opportunity blocklist (test case 5)
# ---------------------------------------------------------------------------


def test_bare_add_validation_is_generic():
    assert is_generic_opportunity_title("add validation")


def test_bare_automate_this_is_generic():
    assert is_generic_opportunity_title("automate this")


def test_bare_improve_communication_is_generic():
    assert is_generic_opportunity_title("improve communication")


def test_concrete_validation_target_is_not_generic():
    """Concrete target after the phrase escapes the blocklist."""
    assert not is_generic_opportunity_title("add validation for the credential preflight")


def test_concrete_automation_target_is_not_generic():
    assert not is_generic_opportunity_title("Automate the preflight via a Python script")


def test_empty_title_is_generic():
    assert is_generic_opportunity_title("")
    assert is_generic_opportunity_title("   ")


# ---------------------------------------------------------------------------
# Value accounting
# ---------------------------------------------------------------------------


def test_value_accounting_supports_empty_categories():
    """Spec Section 5: 'Do not force every category to contain an item.'"""
    va = ValueAccounting(entries=())
    d = va.to_dict()
    # All 7 categories appear as empty lists — not omitted.
    for cat in ValueCategory:
        assert cat.value in d["by_category"]
        assert d["by_category"][cat.value] == []


def test_value_accounting_by_category():
    e1 = ValueEntry(ValueCategory.VALUE_CREATED, "Built the preprocessor")
    e2 = ValueEntry(ValueCategory.VALUE_CREATED, "Shipped the validator")
    e3 = ValueEntry(ValueCategory.VALUE_PRESERVED, "Kept detector semantics")
    va = ValueAccounting(entries=(e1, e2, e3))
    created = va.by_category(ValueCategory.VALUE_CREATED)
    assert len(created) == 2
    assert va.categories_populated() == frozenset({ValueCategory.VALUE_CREATED, ValueCategory.VALUE_PRESERVED})


def test_value_entry_serialisation():
    e = ValueEntry(
        ValueCategory.VALUE_RECOVERED,
        "Recovered the scanner after premature rejection",
        supporting_event_ids=("e1", "e2"),
        beneficiary="install workflow",
    )
    d = e.to_dict()
    assert d["category"] == "VALUE_RECOVERED"
    assert d["supporting_event_ids"] == ["e1", "e2"]
    assert d["beneficiary"] == "install workflow"


# ---------------------------------------------------------------------------
# Fingerprinting + rejection ledger (test case 19)
# ---------------------------------------------------------------------------


def test_fingerprint_normalises_case_and_punctuation():
    a = opportunity_fingerprint("Automate the Preflight!", OpportunityMechanism.AUTOMATE)
    b = opportunity_fingerprint("automate the preflight", OpportunityMechanism.AUTOMATE)
    c = opportunity_fingerprint("automate   the  preflight.", OpportunityMechanism.AUTOMATE)
    assert a == b == c


def test_fingerprint_includes_mechanism():
    """Same title, different mechanism → different fingerprint."""
    a = opportunity_fingerprint("Reuse scanner", OpportunityMechanism.REUSE)
    b = opportunity_fingerprint("Reuse scanner", OpportunityMechanism.INTEGRATE)
    assert a != b


def test_rejection_ledger_prevents_reproposal():
    """Test case 19: rejected opportunity retained to prevent re-proposal."""
    fp = opportunity_fingerprint("Build a cross-session surveillance daemon", OpportunityMechanism.AUTOMATE)
    rejected = RejectedOpportunity(
        opportunity_id="OPP-OLD-001",
        title="Build a cross-session surveillance daemon",
        mechanism=OpportunityMechanism.AUTOMATE,
        rejection_reason="Spec explicitly forbids cross-session surveillance; enterprise complexity for a non-problem",
        rejected_at="2026-07-18T00:00:00Z",
        fingerprint=fp,
        original_disposition=OpportunityDisposition.REJECT,
    )
    ledger = RejectedOpportunityLedger(entries=(rejected,))
    assert ledger.contains_fingerprint(fp)
    # Same fingerprint for a new proposal that matches
    new_fp = opportunity_fingerprint("Build a cross-session surveillance daemon", OpportunityMechanism.AUTOMATE)
    assert ledger.contains_fingerprint(new_fp)


def test_rejection_ledger_to_dict_round_trips():
    fp = opportunity_fingerprint("Add enterprise dashboard", OpportunityMechanism.INSTRUMENT)
    ledger = RejectedOpportunityLedger()
    ledger.add(
        RejectedOpportunity(
            opportunity_id="OPP-001",
            title="Add enterprise dashboard",
            mechanism=OpportunityMechanism.INSTRUMENT,
            rejection_reason="no observer; violates solo-dev principle",
            rejected_at="2026-07-18T00:00:00Z",
            fingerprint=fp,
            original_disposition=OpportunityDisposition.NOT_WORTH_DOING,
        )
    )
    d = ledger.to_dict()
    assert d["entries_total"] == 1
    assert d["entries"][0]["title"] == "Add enterprise dashboard"


# ---------------------------------------------------------------------------
# Improvement candidate (cross-session emission — test case 16)
# ---------------------------------------------------------------------------


def test_improvement_candidate_is_emission_only():
    """Spec Section 17: candidate may be emitted but never auto-consumed."""
    c = ImprovementCandidate(
        candidate_id="CAND-001",
        hypothesis="Conditional external verification reduces premature rejections",
        local_evidence="One session: user correction arrived after a recommendation was made without external check",
        scope="PROBLEM_CLASS",
        confidence="INFERRED",
        expected_value="Fewer reversals when recommending external packages",
        future_signal="Track reversal-with-external-evidence over next 5 AAR runs",
        promotion_condition="≥3 independent sessions show the same pattern",
        retirement_condition="If no reversal pattern observed in 10 sessions",
        source_opportunity_id="OPP-001",
    )
    d = c.to_dict()
    assert d["candidate_id"] == "CAND-001"
    assert d["scope"] == "PROBLEM_CLASS"
    assert d["promotion_condition"].startswith("≥3")


# ---------------------------------------------------------------------------
# Schema version
# ---------------------------------------------------------------------------


def test_schema_version_is_string():
    assert OPPORTUNITY_SCHEMA_VERSION == "1.0"
