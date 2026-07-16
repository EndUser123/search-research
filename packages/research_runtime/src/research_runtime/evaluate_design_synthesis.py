"""Evaluate decision synthesis against representative scenarios.

Tests the complete chain:
  decision-request.v1 + research-result.v1 -> decision-result.v1
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .decision_request import validate as validate_request
from .decision_result import validate as validate_decision
from .design import synthesize
from .research_result import validate as validate_research_result

SCENARIOS = [
    ("agent-framework", "choose an agent framework", "research gap"),
    ("persistence", "choose persistence architecture", "research gap"),
    ("build-buy", "choose build vs buy", "research gap"),
    ("provider-strategy", "select provider strategy", "research gap"),
    ("migration", "migrate a component", "research gap"),
    ("repositories", "choose between repositories", "research gap"),
    ("operational-risk", "accept operational risk", "decision-context gap"),
    ("defer", "defer a decision due to insufficient evidence", "research gap"),
]

RESEARCH_HASH = "a" * 64


def _run_id(scenario_id: str) -> str:
    """Produce a valid UUID from a scenario_id."""
    # Map each char to a hex digit (0-9, a-f)
    hex_vals = [hex(ord(c))[2:][-1] for c in scenario_id[:6]]
    suffix = "".join(hex_vals).ljust(12, "0")[:12]
    return f"87654321-4321-4432-8432-{suffix}"


def _request(scenario_id: str, research_hash: str) -> dict[str, Any]:
    return {
        "schema_version": "decision-request.v1",
        "request_id": "12345678-1234-4234-8234-123456789012",
        "created_at": "2026-07-16T12:00:00Z",
        "decision_context": {
            "objective": f"Make a decision: {scenario_id.replace('-', ' ')}",
            "desired_outcome": "An explicit, reversible outcome.",
            "decision_type": "architecture",
            "scope": scenario_id,
        },
        "constraints": {key: [] for key in ("technical", "operational", "compatibility", "cost", "timeline", "reversibility")},
        "options": {
            "considered": [{"option_id": "a", "label": "Option A"}, {"option_id": "b", "label": "Option B"}],
            "excluded": [], "alternatives": [],
        },
        "priorities": {key: "high" if key in {"reliability", "simplicity"} else "medium" for key in ("reliability", "simplicity", "performance", "maintainability", "cost")},
        "authority": {
            "decision_owner": "named owner",
            "approval_requirements": ["Review before implementation"],
            "irreversible_actions": [],
        },
        "research_dependency": {
            "required": True,
            "result_refs": [{"run_id": _run_id(scenario_id), "artifact_sha256": research_hash}],
            "unresolved_evidence_acknowledged": True,
            "freshness_requirement": "same revision",
        },
    }


def _research_result(scenario_id: str, *, has_evidence: bool = True) -> dict[str, Any]:
    run_id = _run_id(scenario_id)
    if has_evidence:
        findings = [
            {"claim_id": "claim-a", "statement": f"Evidence supports Option A for {scenario_id}.", "status": "verified", "confidence": "high", "supporting_source_ids": ["src-1"], "contradicting_source_ids": [], "assessment_ids": ["ass-1"], "limitations": []},
            {"claim_id": "claim-b", "statement": f"Option B faces compatibility issues for {scenario_id}.", "status": "contradicted", "confidence": "medium", "supporting_source_ids": [], "contradicting_source_ids": ["src-2"], "assessment_ids": ["ass-2"], "limitations": ["Limited data"]},
        ]
        unresolved: list[str] = []
    else:
        findings = [
            {"claim_id": "claim-a", "statement": f"Insufficient evidence for any option in {scenario_id}.", "status": "unverified", "confidence": "low", "supporting_source_ids": [], "contradicting_source_ids": [], "assessment_ids": [], "limitations": ["No sources opened"]},
        ]
        unresolved = [f"Primary evidence for {scenario_id} is still missing."]

    base = {
        "schema_version": "research-result.v1",
        "source_schema_version": "research-run.v1",
        "run_id": run_id,
        "created_at": "2026-07-16T12:00:00Z",
        "context": {"research_question": f"Research for {scenario_id}", "requested_decision": scenario_id, "scope": [], "constraints": [], "assumptions": []},
        "evidence_requirements": {"required_capabilities": [], "fulfilled_capabilities": [], "unresolved": []},
        "findings": findings,
        "options": [],
        "risks": [{"statement": f"Uncertainty for {scenario_id}", "kind": "uncertainty"}],
        "unresolved_questions": unresolved,
        "provenance": {"run_id": run_id, "artifact_sha256": RESEARCH_HASH, "workspace_revision": "7d8e103", "sources": [], "assessments": [], "lanes": [], "failures": []},
        "stopping": {"status": "quality_stop", "reason": "Sufficient evidence gathered.", "runtime_ms": None},
        "authorization": {"decision_authority": "downstream_consumer", "research_may_recommend": True, "research_may_decide": False, "authorization_supported": True},
    }
    validate_research_result(base)
    return base


def evaluate(research_result_path: Path | None = None) -> dict[str, Any]:
    rows = []
    for scenario_id, objective, missing_kind in SCENARIOS:
        req = _request(scenario_id, RESEARCH_HASH)
        validate_request(req)
        is_deferred = scenario_id == "defer"
        request_sha256 = hashlib.sha256(json.dumps(req, sort_keys=True).encode()).hexdigest()
        rr = _research_result(scenario_id, has_evidence=not is_deferred)
        result = synthesize(req, [rr], request_sha256=request_sha256)
        validate_decision(result)
        rows.append({
            "scenario_id": scenario_id,
            "request_valid": True,
            "research_reference_valid": bool(result["evidence"]["research_result_refs"]),
            "decision_valid": True,
            "uncertainty_preserved": bool(result["evidence"]["unresolved_questions"]) or bool(result["evidence"]["confidence"] != "high"),
            "rejected_alternatives_retained": bool(result["alternatives"]["rejected"]) and bool(result["alternatives"]["rejection_reasons"]),
            "provenance_intact": result["provenance"]["hashes"]["request"] == request_sha256,
            "execution_not_claimed": result["execution_boundary"]["implementation_required"] is not None,
            "missing_information_class": missing_kind,
        })
    passed = sum(
        1 for row in rows
        if all(row[key] for key in ("request_valid", "research_reference_valid", "decision_valid", "uncertainty_preserved", "rejected_alternatives_retained", "provenance_intact", "execution_not_claimed"))
    )
    return {
        "schema_version": "design-synthesis-evaluation.v1",
        "case_count": len(rows),
        "cases": rows,
        "summary": {
            "passed": passed,
            "total": len(rows),
            "research_gap": sum(1 for row in rows if row["missing_information_class"] == "research gap"),
            "decision_context_gap": sum(1 for row in rows if row["missing_information_class"] == "decision-context gap"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evaluation = evaluate(None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evaluation, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evaluation["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
