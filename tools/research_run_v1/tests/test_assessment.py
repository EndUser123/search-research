from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from research_runtime.assessment import ClaimRequirement, EvidenceAssessment, assess_claim  # noqa: E402
from research_runtime.evaluate_assessment import evaluate  # noqa: E402


def assessment(**overrides: object) -> EvidenceAssessment:
    values: dict[str, object] = {
        "claim_id": "c",
        "source_id": "s",
        "source_location": "P:/repo/file.py:10",
        "passage_or_anchor": "relevant passage",
        "relationship": "directly_supports",
        "authority": "primary",
        "currency": "current",
        "assessment_method": "caller_supplied",
        "assessment_basis": "direct inspection",
        "assessed_at": "2026-07-13T13:00:00Z",
        "run_id": "run-1",
        "source_status": "verified",
    }
    values.update(overrides)
    return EvidenceAssessment(**values)


def test_reference_corpus_matches_all_human_authored_outcomes() -> None:
    result = evaluate()

    assert len(result["cases"]) == 15
    assert result["exact_matches"] == 15
    assert result["disagreements"] == []


def test_anchor_match_does_not_imply_support() -> None:
    result = assess_claim("c", [assessment(assessment_method="deterministic_anchor_only", source_status="anchor_confirmed")], ClaimRequirement(frozenset({"primary"}), require_direct_support=True), expected_run_id="run-1")

    assert result.status == "supported"
    assert "advisory_or_anchor_only" in result.rationale


def test_opened_source_does_not_imply_support() -> None:
    result = assess_claim("c", [assessment(relationship="contextual_only", source_status="opened")], expected_run_id="run-1")

    assert result.status == "unverified"


def test_relationships_remain_distinct() -> None:
    for relationship, expected in (("directly_supports", "verified"), ("partially_supports", "supported"), ("contradicts", "contradicted"), ("contextual_only", "unverified"), ("insufficient", "unverified")):
        result = assess_claim("c", [assessment(relationship=relationship)], ClaimRequirement(frozenset({"primary"}), require_direct_support=True), expected_run_id="run-1")
        assert result.status == expected


def test_stale_primary_cannot_verify_current_claim() -> None:
    result = assess_claim("c", [assessment(currency="stale")], ClaimRequirement(frozenset({"primary"}), require_current=True), expected_run_id="run-1")

    assert result.status == "supported"


def test_model_assisted_assessment_is_advisory() -> None:
    result = assess_claim("c", [assessment(assessment_method="model_assisted")], ClaimRequirement(frozenset({"primary"}), require_direct_support=True), expected_run_id="run-1")

    assert result.status == "supported"
    assert "advisory_or_anchor_only" in result.rationale


def test_duplicate_underlying_sources_do_not_multiply_evidence() -> None:
    result = assess_claim("c", [assessment(source_id="s1", source_identity="same"), assessment(source_id="s2", source_identity="same", relationship="contextual_only")], ClaimRequirement(frozenset({"primary"}), require_direct_support=True), expected_run_id="run-1")

    assert result.status == "verified"
    assert result.supporting_source_ids == ("s1",)


def test_foreign_run_is_not_consumed() -> None:
    result = assess_claim("c", [assessment(run_id="foreign")], expected_run_id="run-1")

    assert result.status == "unverified"
