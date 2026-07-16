"""Evaluate the human-authored evidence-assessment reference corpus."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .assessment import ClaimRequirement, EvidenceAssessment, assess_claim


ROOT = Path(__file__).parents[4]
CORPUS = ROOT / "tests" / "research_run_v1" / "assessment_corpus.json"
REFERENCE_RUN = "reference-assessment-run"
ASSESSED_AT = "2026-07-15T12:00:00Z"


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    requirement = ClaimRequirement(frozenset(case["requirement"]["authorities"]), case["requirement"].get("current", False), case["requirement"].get("direct", False), frozenset(case["requirement"].get("methods", [])))
    assessments = tuple(EvidenceAssessment(claim_id=case["claim"], source_id=item["source_id"], source_identity=item.get("source_identity"), source_location=f"reference:{case['id']}", passage_or_anchor="human-authored reference basis", relationship=item["relationship"], authority=item["authority"], currency=item["currency"], assessment_method=item["assessment_method"], assessment_basis="human-authored reference assessment", assessed_at=ASSESSED_AT, limitations=tuple(item.get("limitations", [])), run_id=REFERENCE_RUN, source_status=item.get("source_status", "discovery_only")) for item in case["assessments"])
    result = assess_claim(case["claim"], assessments, requirement, expected_run_id=REFERENCE_RUN)
    return {"id": case["id"], "expected": case["expected"], "actual": result.status, "match": result.status == case["expected"], "rationale": list(result.rationale), "supporting_source_ids": list(result.supporting_source_ids), "contradicting_source_ids": list(result.contradicting_source_ids)}


def evaluate(path: Path = CORPUS) -> dict[str, Any]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    results = [evaluate_case(case) for case in cases]
    return {"schema": "research-run-v1.assessment-evaluation", "cases": results, "exact_matches": sum(item["match"] for item in results), "disagreements": [item for item in results if not item["match"]]}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
