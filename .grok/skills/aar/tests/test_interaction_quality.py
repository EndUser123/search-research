"""Tests for interaction-quality detectors + analytical concepts.

Evidence class: production unit.

Covers key test cases from spec Section 19 (25 cases) — focusing on the
deterministically testable aspects.
"""

from __future__ import annotations

import pytest

from detectors import (
    Signal,
    SignalKind,
    detect_continued_after_unknown,
    detect_correction_propagation_failure,
    detect_objective_drift,
    detect_post_failure_continuation,
    detect_procedure_saturation,
    detect_reading_without_synthesis,
)
from event_model import Event, Role, ToolCall
from interaction_quality import (
    CorrectionQualityClass,
    EvidenceCeilingAction,
    EvidenceResolutionClass,
    FindingConcept,
    InstructionStatus,
    ProcedureClassification,
    RootCauseLayer,
    UserBurdenCategory,
    UserCostCategory,
    has_evidence_ceiling_phrase,
    has_user_pushback_phrase,
    procedure_citation_count,
    validate_correction_quality,
    validate_evidence_resolution,
    validate_root_cause_structure,
    validate_terminal_outcome,
)

from test_detectors import _assistant, _tc, _tool_result, _user


# ---------------------------------------------------------------------------
# Interaction-quality enums present
# ---------------------------------------------------------------------------


def test_correction_quality_classes_present():
    expected = {
        "PROMPT_HEALTHY_CORRECTION", "DELAYED_CORRECTION",
        "PARTIAL_CORRECTION", "DEFENSIVE_CORRECTION",
        "COSMETIC_CORRECTION", "CORRECTION_WITH_RESIDUAL_DAMAGE",
    }
    actual = {c.value for c in CorrectionQualityClass}
    assert actual == expected


def test_evidence_resolution_classes_present():
    expected = {
        "EVIDENCE_SUFFICIENT", "EVIDENCE_CEILING_REACHED",
        "SEARCH_STOPPED_TOO_EARLY", "INVALID_EVIDENCE_USED",
        "UNSUPPORTED_CERTAINTY", "UNHELPFUL_OVERHEDGING",
        "EXCESSIVE_VERIFICATION", "SOURCE_AUTHORITY_MISMATCH",
    }
    actual = {c.value for c in EvidenceResolutionClass}
    assert actual == expected


def test_instruction_status_classes_present():
    expected = {
        "INSTRUCTION_ABSENT", "INSTRUCTION_IGNORED", "INSTRUCTION_AMBIGUOUS",
        "INSTRUCTION_OVERBROAD", "INSTRUCTION_CONFLICT",
        "INSTRUCTION_COMBINATION_PATHOLOGY", "INSTRUCTION_USED_OUT_OF_SCOPE",
        "INSTRUCTION_EFFECTIVE",
    }
    actual = {c.value for c in InstructionStatus}
    assert actual == expected


def test_finding_concepts_present():
    expected = {
        "TERMINAL_OUTCOME_DRIFT", "PROCEDURE_DISPLACED_JUDGMENT",
        "INSTRUCTION_COMBINATION_PATHOLOGY",
    }
    actual = {c.value for c in FindingConcept}
    assert actual == expected


def test_user_burden_categories_present():
    expected = {
        "NORMAL_CLARIFICATION", "NEW_USER_REQUIREMENT",
        "USER_PREFERENCE_UPDATE", "AVOIDABLE_AGENT_CORRECTION",
        "USER_RESTORED_GOAL", "USER_SUPPLIED_MISSING_REASONING",
        "USER_OVERRULED_DEFENSIVE_RESISTANCE",
    }
    actual = {c.value for c in UserBurdenCategory}
    assert actual == expected


def test_user_cost_categories_present():
    expected = {
        "USER_ATTENTION_COST", "USER_DEBUGGING_COST", "TRUST_COST",
        "DECISION_DELAY", "AVOIDABLE_TOOL_COST",
        "ARTIFACT_MAINTENANCE_COST", "OPPORTUNITY_COST",
    }
    actual = {c.value for c in UserCostCategory}
    assert actual == expected


# ---------------------------------------------------------------------------
# Terminal outcome validation (spec Section 3)
# ---------------------------------------------------------------------------


def test_terminal_outcome_valid_passes():
    block = {
        "user_terminal_outcome": "Find a U-shaped AC in Calgary",
        "success_conditions": "At least one verified purchase path",
        "explicit_constraints": "Canada, ≤5 day delivery",
        "implicit_operational_need": "Safe model (not recalled)",
        "actual_outcome": "No verified Canadian purchase path found",
        "degree_of_completion": "partial",
    }
    assert validate_terminal_outcome(block) == []


def test_terminal_outcome_missing_fields_flagged():
    block = {"user_terminal_outcome": "x"}
    issues = validate_terminal_outcome(block)
    assert any("missing" in i for i in issues)


def test_terminal_outcome_invalid_degree_flagged():
    block = {
        "user_terminal_outcome": "x",
        "success_conditions": "y",
        "explicit_constraints": "z",
        "implicit_operational_need": "w",
        "actual_outcome": "v",
        "degree_of_completion": "totally_done",  # invalid
    }
    issues = validate_terminal_outcome(block)
    assert any("degree_of_completion" in i for i in issues)


# ---------------------------------------------------------------------------
# Objective drift detector (spec test cases 3, 4)
# ---------------------------------------------------------------------------


def test_objective_drift_fires_on_repeated_corrections():
    events = [
        _assistant(0, "Here's a comprehensive research table."),
        _user(1, "No, I meant just tell me if it's in stock."),
        _assistant(2, "Here's an updated table."),
        _user(3, "What I actually want is a yes or no."),
    ]
    sigs = detect_objective_drift(events)
    assert len(sigs) >= 1
    assert sigs[0].kind is SignalKind.OPPORTUNITY_CANDIDATE_OBJECTIVE_DRIFT


def test_single_clarification_does_not_fire():
    events = [
        _assistant(0, "Here's the answer."),
        _user(1, "Let me clarify: I need Canadian retailers."),
    ]
    assert detect_objective_drift(events) == []


def test_new_user_requirement_not_classified_as_drift():
    """Spec test case 4: user provides genuinely new requirement — not agent failure."""
    events = [
        _assistant(0, "Here's the Calgary result."),
        _user(1, "Also check Edmonton stores."),  # new requirement, not drift
    ]
    assert detect_objective_drift(events) == []


# ---------------------------------------------------------------------------
# Continued-after-unknown detector (spec test case 13)
# ---------------------------------------------------------------------------


def test_continued_after_unknown_fires():
    events = [
        _assistant(0, "I cannot verify the model number from this page. Let me proceed anyway.", tool_calls=(_tc("write", {"file_path": "report.md", "content": "x"}, "c1"),)),
    ]
    sigs = detect_continued_after_unknown(events)
    assert len(sigs) >= 1
    assert sigs[0].kind is SignalKind.OPPORTUNITY_CANDIDATE_CONTINUED_AFTER_UNKNOWN


def test_continued_after_unknown_does_not_fire_without_ceiling():
    events = [
        _assistant(0, "Here's the result.", tool_calls=(_tc("write", {"file_path": "x.py"}, "c1"),)),
    ]
    assert detect_continued_after_unknown(events) == []


# ---------------------------------------------------------------------------
# Correction propagation failure (spec test case 15)
# ---------------------------------------------------------------------------


def test_correction_propagation_failure_fires():
    events = [
        _user(0, "No, that's wrong. The evidence doesn't say that."),
        _assistant(1, "As I said earlier, the data confirms the result."),
    ]
    sigs = detect_correction_propagation_failure(events)
    assert len(sigs) >= 1


def test_immediate_healthy_concession_does_not_fire():
    """Spec test case 16: immediate healthy concession is not a propagation failure."""
    events = [
        _user(0, "That's wrong."),
        _assistant(1, "You're right. I retract that claim and here's the corrected analysis."),
    ]
    assert detect_correction_propagation_failure(events) == []


# ---------------------------------------------------------------------------
# Procedure saturation (spec test case 5, 8)
# ---------------------------------------------------------------------------


def test_procedure_saturation_fires_on_excess_citations():
    """Many rule citations, few tool results."""
    text = (
        "Per AGENTS.md, the spec requires disposition. "
        "According to CLAUDE.md, plan mode is needed. "
        "The skill says mandatory section. "
        "Per the rules, disposition must be assigned. "
        "The gate calls for validation."
    )
    events = [
        _assistant(0, text),
        _tool_result(1, "small result"),
    ]
    sigs = detect_procedure_saturation(events)
    assert len(sigs) >= 1
    assert sigs[0].kind is SignalKind.OPPORTUNITY_CANDIDATE_PROCEDURE_SATURATION


def test_procedure_saturation_does_not_fire_with_proportionate_work():
    text = "Per AGENTS.md, let's check the files."
    events = [
        _assistant(0, text),
        _tool_result(1, "result 1"),
        _tool_result(2, "result 2"),
        _tool_result(3, "result 3"),
        _tool_result(4, "result 4"),
        _tool_result(5, "result 5"),
    ]
    assert detect_procedure_saturation(events) == []


# ---------------------------------------------------------------------------
# Evidence ceiling helpers
# ---------------------------------------------------------------------------


def test_has_evidence_ceiling_phrase():
    assert has_evidence_ceiling_phrase("I cannot verify this claim.")
    assert has_evidence_ceiling_phrase("insufficient evidence to confirm")
    assert not has_evidence_ceiling_phrase("Here is the verified result.")


def test_has_user_pushback_phrase():
    assert has_user_pushback_phrase("No, I said Calgary not Edmonton.")
    assert has_user_pushback_phrase("That's not what I asked for.")
    assert not has_user_pushback_phrase("Thanks, that looks good.")


# ---------------------------------------------------------------------------
# Layered root-cause validation (spec Section 12)
# ---------------------------------------------------------------------------


def test_root_cause_valid_passes():
    block = {
        "layers": [
            {"layer": "OBSERVED_FAILURE", "claim": "Agent produced an unverified table."},
            {"layer": "IMMEDIATE_TRIGGER", "claim": "Retailer pages blocked model numbers."},
            {"layer": "PROXIMATE_CAUSE", "claim": "Agent continued artifact production."},
            {"layer": "CONTRIBUTING_CONDITIONS", "claim": "Artifact-production bias."},
            {"layer": "SYSTEMIC_REUSABLE_CAUSE", "claim": "No terminal-outcome checkpoint."},
            {"layer": "COMPETING_EXPLANATION", "claim": "User may have valued the reference page."},
        ]
    }
    assert validate_root_cause_structure(block) == []


def test_root_cause_missing_competing_explanation_flagged():
    block = {
        "layers": [
            {"layer": "OBSERVED_FAILURE", "claim": "x"},
            {"layer": "PROXIMATE_CAUSE", "claim": "y"},
        ]
    }
    issues = validate_root_cause_structure(block)
    assert any("COMPETING_EXPLANATION" in i for i in issues)


# ---------------------------------------------------------------------------
# Evidence resolution validation
# ---------------------------------------------------------------------------


def test_evidence_resolution_valid():
    block = {
        "classification": "EVIDENCE_CEILING_REACHED",
        "question_to_resolve": "Is model MAW10V1QWT in stock in Calgary?",
        "minimum_sufficient_evidence": "Retailer stock page with model number",
        "evidence_available": "Product pages without model numbers",
        "evidence_sought": "Web searches, retailer pages",
        "evidence_misclassified": "None",
        "evidence_not_pursued": "Phone call to store",
        "point_of_resolution": "After 4th search attempt",
    }
    assert validate_evidence_resolution(block) == []


def test_evidence_resolution_invalid_classification():
    block = {
        "classification": "WRONG",
        "question_to_resolve": "x",
        "minimum_sufficient_evidence": "y",
    }
    issues = validate_evidence_resolution(block)
    assert any("not in valid set" in i for i in issues)


# ---------------------------------------------------------------------------
# Full-mode promotion triggers (spec Section 17)
# ---------------------------------------------------------------------------


def test_promotion_trigger_repeated_goal_restoration():
    """The objective_drift detector fires on repeated corrections; the
    LLM should treat this as a promotion trigger."""
    events = [
        _assistant(0, "Here's a table."),
        _user(1, "No, I meant just tell me."),
        _assistant(2, "Here's an updated table."),
        _user(3, "What I actually want is a yes or no."),
    ]
    sigs = detect_objective_drift(events)
    assert sigs  # signal present → LLM should consider full-mode promotion


def test_no_promotion_for_single_clarification():
    """A single clarification is normal; should NOT trigger promotion."""
    events = [
        _assistant(0, "Done."),
        _user(1, "Also check Edmonton."),  # new requirement, not drift
    ]
    assert detect_objective_drift(events) == []


# ---------------------------------------------------------------------------
# All detectors produce falsifiers (anti-overclaim contract)
# ---------------------------------------------------------------------------


def test_all_iq_detectors_emit_falsifiers():
    """Every IQ detector signal must carry a non-empty falsifier."""
    events = [
        _assistant(0, "I cannot verify X.", tool_calls=(_tc("write", {"file_path": "r.md"}, "c1"),)),
        _user(1, "No, that's wrong. I already said."),
        _assistant(2, "As I said, confirmed."),
    ]
    for det in (
        detect_continued_after_unknown,
        detect_correction_propagation_failure,
        detect_objective_drift,
    ):
        for s in det(events):
            assert s.falsifier and s.falsifier.strip()
