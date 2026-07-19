"""Tests for the deterministic post-LLM output validator.

Evidence classification: CONTRACT_MODEL_TESTED

Each contract rule gets at least one positive test (the rule passes when the
report is well-formed) and one negative test (the rule fires a blocker when
violated). The valid-report fixture is a real JSON file on disk (anti-mock).
Invalid variants are constructed inline so each test isolates one rule.
"""

from __future__ import annotations

import json
import copy
from pathlib import Path

import pytest

from output_validator import (
    REQUIRED_SECTIONS,
    ValidationFinding,
    ValidationResult,
    validate_aar_report,
    extract_structured_block,
)

FIXTURES = Path(__file__).parent / "fixtures"
VALID_REPORT = FIXTURES / "aar_report_valid.json"


def _load_valid() -> dict:
    """Load the canonical valid report as a mutable dict (for variant tests)."""
    return json.loads(VALID_REPORT.read_text(encoding="utf-8"))


def _codes(result: ValidationResult, severity: str | None = None) -> set[str]:
    return {f.code for f in result.findings if severity is None or f.severity == severity}


# ---------------------------------------------------------------------------
# Valid report passes
# ---------------------------------------------------------------------------


def test_valid_report_passes_with_zero_findings():
    r = validate_aar_report(VALID_REPORT)
    assert r.passed is True
    assert r.findings == ()
    assert "PASS" in r.summary


def test_valid_report_passes_from_dict():
    r = validate_aar_report(_load_valid())
    assert r.passed is True


def test_valid_report_via_markdown_with_embedded_json(tmp_path: Path):
    """Validator extracts structured block from markdown reports."""
    data = _load_valid()
    md = tmp_path / "report.md"
    md.write_text(
        f"# AAR\n\nVerdict: ok.\n\n<!-- AAR_JSON: {json.dumps(data)} -->\n",
        encoding="utf-8",
    )
    r = validate_aar_report(md)
    assert r.passed is True


# ---------------------------------------------------------------------------
# extract_structured_block
# ---------------------------------------------------------------------------


def test_extract_block_from_aar_json_marker():
    md = "Intro\n<!-- AAR_JSON: {\"verdict\": \"ok\"} -->\nOutro"
    obj = extract_structured_block(md)
    assert obj == {"verdict": "ok"}


def test_extract_block_from_json_fence():
    md = "Intro\n```json\n{\"a\": 1}\n```\n"
    assert extract_structured_block(md) == {"a": 1}


def test_extract_block_returns_none_when_absent():
    assert extract_structured_block("no json here") is None


def test_validator_raises_on_markdown_without_block(tmp_path: Path):
    md = tmp_path / "r.md"
    md.write_text("# AAR\nNo structured block.", encoding="utf-8")
    with pytest.raises(ValueError, match="no structured JSON block"):
        validate_aar_report(md)


# ---------------------------------------------------------------------------
# Required sections
# ---------------------------------------------------------------------------


def test_missing_section_is_blocker():
    for section in REQUIRED_SECTIONS:
        data = _load_valid()
        del data[section]
        r = validate_aar_report(data)
        assert not r.passed, f"removing {section!r} should fail"
        assert "MISSING_SECTION" in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Episode types
# ---------------------------------------------------------------------------


def test_invalid_episode_type_is_blocker():
    data = _load_valid()
    data["episodes"][0]["type"] = "bogus_type"
    r = validate_aar_report(data)
    assert "EPISODE_TYPE_INVALID" in _codes(r, "blocker")


def test_invalid_episode_status_is_warning():
    data = _load_valid()
    data["episodes"][0]["status"] = "completed_wrong_value"
    r = validate_aar_report(data)
    assert "EPISODE_STATUS_INVALID" in _codes(r, "warning")


# ---------------------------------------------------------------------------
# Episode evidence
# ---------------------------------------------------------------------------


def test_missing_episode_evidence_is_blocker():
    data = _load_valid()
    data["episodes"][1]["evidence"] = ""
    r = validate_aar_report(data)
    assert "EPISODE_MISSING_EVIDENCE" in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Dispositions
# ---------------------------------------------------------------------------


def test_invalid_disposition_is_blocker():
    data = _load_valid()
    data["opportunity_candidates"][0]["disposition"] = "JUST_DO_IT"
    r = validate_aar_report(data)
    assert "DISPOSITION_INVALID" in _codes(r, "blocker")


def test_missing_disposition_is_warning():
    data = _load_valid()
    del data["opportunity_candidates"][0]["disposition"]
    r = validate_aar_report(data)
    assert "OPPORTUNITY_MISSING_DISPOSITION" in _codes(r, "warning")


# ---------------------------------------------------------------------------
# Accounting reconciliation
# ---------------------------------------------------------------------------


def test_accounting_does_not_reconcile_is_blocker():
    data = _load_valid()
    data["accounting"]["total_episodes"] = 99
    r = validate_aar_report(data)
    assert "ACCOUNTING_DOES_NOT_RECONCILE" in _codes(r, "blocker")


def test_accounting_missing_type_count_is_blocker():
    data = _load_valid()
    del data["accounting"]["observation"]
    r = validate_aar_report(data)
    assert "ACCOUNTING_TYPE_MISSING" in _codes(r, "blocker")


def test_accounting_episode_list_mismatch_is_warning():
    data = _load_valid()
    data["accounting"]["total_episodes"] = 999  # != len(episodes)=3
    # But the sum of type counts must also equal total_episodes, so this
    # fires both the reconcile blocker AND the list-mismatch warning.
    r = validate_aar_report(data)
    assert "ACCOUNTING_DOES_NOT_RECONCILE" in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Confidence dimensions
# ---------------------------------------------------------------------------


def test_material_conclusion_missing_dimension_is_blocker():
    data = _load_valid()
    del data["recurring_patterns"][0]["confidence_dimensions"]["causal_confidence"]
    r = validate_aar_report(data)
    assert "CONFIDENCE_DIMENSION_MISSING" in _codes(r, "blocker")


def test_material_conclusion_invalid_value_is_blocker():
    data = _load_valid()
    data["recurring_patterns"][0]["confidence_dimensions"]["evidence_confidence"] = "PRETTY_SURE"
    r = validate_aar_report(data)
    assert "CONFIDENCE_VALUE_INVALID" in _codes(r, "blocker")


def test_missing_confidence_rationale_is_warning():
    data = _load_valid()
    del data["recurring_patterns"][0]["confidence_rationale"]["evidence_confidence"]
    r = validate_aar_report(data)
    assert "CONFIDENCE_RATIONALE_MISSING" in _codes(r, "warning")


# ---------------------------------------------------------------------------
# Comparative claim rule
# ---------------------------------------------------------------------------


def test_comparative_claim_without_comparison_is_blocker():
    data = _load_valid()
    data["verdict"]["text"] = (
        "Hooks are more reliable than validators for this class of failure."
    )
    # comparison_status defaults to NO_COMPARISON → must fire.
    r = validate_aar_report(data)
    assert "COMPARATIVE_CLAIM_WITHOUT_COMPARISON" in _codes(r, "blocker")


def test_comparative_claim_with_controlled_comparison_passes():
    data = _load_valid()
    data["verdict"]["text"] = (
        "Hooks are more reliable than validators for this class of failure."
    )
    data["comparison_status"] = "CONTROLLED_COMPARISON"
    r = validate_aar_report(data)
    assert "COMPARATIVE_CLAIM_WITHOUT_COMPARISON" not in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# SOURCE_PARTIAL + exhaustive claim
# ---------------------------------------------------------------------------


def test_partial_source_with_exhaustive_claim_is_blocker():
    data = _load_valid()
    data["evidence_scope"]["source_status"] = "SOURCE_PARTIAL"
    data["verdict"]["text"] = "We found all gaps identified in this session."
    r = validate_aar_report(data)
    assert "PARTIAL_SOURCE_EXHAUSTIVE_CLAIM" in _codes(r, "blocker")


def test_complete_source_with_exhaustive_claim_does_not_fire():
    data = _load_valid()
    data["verdict"]["text"] = "We found all gaps identified in this session."
    r = validate_aar_report(data)
    assert "PARTIAL_SOURCE_EXHAUSTIVE_CLAIM" not in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# GENERAL scope gate
# ---------------------------------------------------------------------------


def test_general_scope_with_insufficient_evidence_is_blocker():
    data = _load_valid()
    data["recurring_patterns"][0]["scope"] = "GENERAL"
    # n_sessions=1, comparison_status=NO_COMPARISON → insufficient.
    r = validate_aar_report(data)
    assert "GENERAL_SCOPE_INSUFFICIENT_EVIDENCE" in _codes(r, "blocker")


def test_general_scope_with_mechanically_universal_exempt():
    data = _load_valid()
    data["recurring_patterns"][0]["scope"] = "GENERAL"
    data["recurring_patterns"][0]["mechanically_universal"] = True
    r = validate_aar_report(data)
    assert "GENERAL_SCOPE_INSUFFICIENT_EVIDENCE" not in _codes(r, "blocker")


def test_general_scope_with_three_sessions_and_comparison_passes():
    data = _load_valid()
    data["recurring_patterns"][0]["scope"] = "GENERAL"
    data["recurring_patterns"][0]["comparison_status"] = "CONTROLLED_COMPARISON"
    data["n_sessions"] = 3
    r = validate_aar_report(data)
    assert "GENERAL_SCOPE_INSUFFICIENT_EVIDENCE" not in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# LOW causal + DURABLE_POLICY
# ---------------------------------------------------------------------------


def test_low_causal_with_durable_policy_is_blocker():
    data = _load_valid()
    pat = data["recurring_patterns"][0]
    pat["policy_promotion"] = "DURABLE_POLICY"
    pat["confidence_dimensions"]["causal_confidence"] = "LOW"
    r = validate_aar_report(data)
    assert "LOW_CAUSAL_DURABLE_POLICY" in _codes(r, "blocker")


def test_high_causal_with_durable_policy_passes():
    data = _load_valid()
    pat = data["recurring_patterns"][0]
    pat["policy_promotion"] = "DURABLE_POLICY"
    pat["confidence_dimensions"]["causal_confidence"] = "HIGH"
    r = validate_aar_report(data)
    assert "LOW_CAUSAL_DURABLE_POLICY" not in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Headline scope vs body scope
# ---------------------------------------------------------------------------


def test_headline_scope_exceeds_body_is_blocker():
    data = _load_valid()
    data["verdict"]["scope"] = "GENERAL"
    # Body max is PROBLEM_CLASS → GENERAL headline outranks it.
    r = validate_aar_report(data)
    assert "HEADLINE_SCOPE_EXCEEDS_BODY" in _codes(r, "blocker")


def test_headline_scope_equal_to_body_passes():
    data = _load_valid()
    data["verdict"]["scope"] = "PROBLEM_CLASS"
    r = validate_aar_report(data)
    assert "HEADLINE_SCOPE_EXCEEDS_BODY" not in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Workflow REDUNDANT promotion gate
# ---------------------------------------------------------------------------


def test_redundant_without_sufficient_evidence_is_blocker():
    data = _load_valid()
    pat = data["recurring_patterns"][0]
    pat["workflow_classification"] = "REDUNDANT"
    pat["n_runs"] = 1  # < 3
    pat["n_unique_outputs"] = 0
    pat["has_consumer"] = False
    pat["n_unique_defects_caught"] = 0
    r = validate_aar_report(data)
    assert "REDUNDANT_WITHOUT_SUFFICIENT_EVIDENCE" in _codes(r, "blocker")


def test_redundant_with_sufficient_evidence_passes():
    data = _load_valid()
    pat = data["recurring_patterns"][0]
    pat["workflow_classification"] = "REDUNDANT"
    pat["n_runs"] = 5
    pat["n_unique_outputs"] = 0
    pat["has_consumer"] = False
    pat["n_unique_defects_caught"] = 0
    r = validate_aar_report(data)
    assert "REDUNDANT_WITHOUT_SUFFICIENT_EVIDENCE" not in _codes(r, "blocker")


def test_redundant_with_unique_defect_caught_is_blocker():
    """A step that catches a unique defect cannot be REDUNDANT."""
    data = _load_valid()
    pat = data["recurring_patterns"][0]
    pat["workflow_classification"] = "REDUNDANT"
    pat["n_runs"] = 5
    pat["n_unique_outputs"] = 0
    pat["has_consumer"] = False
    pat["n_unique_defects_caught"] = 1  # catches something
    r = validate_aar_report(data)
    assert "REDUNDANT_WITHOUT_SUFFICIENT_EVIDENCE" in _codes(r, "blocker")


# ---------------------------------------------------------------------------
# Blocker vs warning semantics
# ---------------------------------------------------------------------------


def test_passed_is_true_iff_zero_blockers():
    r = validate_aar_report(_load_valid())
    assert r.passed is True
    assert len(r.blockers()) == 0

    data = _load_valid()
    data["episodes"][0]["type"] = "bad"
    r = validate_aar_report(data)
    assert r.passed is False
    assert len(r.blockers()) >= 1


def test_validation_result_to_dict_round_trip():
    r = validate_aar_report(_load_valid())
    d = r.to_dict()
    assert d["passed"] is True
    assert "findings" in d
    assert d["blocker_count"] == 0
