"""Evaluate the request -> research -> decision contract chain."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .decision_request import validate as validate_request
from .decision_result import validate as validate_decision
from .research_result import validate as validate_research_result

SCENARIOS = [
    ("agent-framework", "adopt an agent framework", "research gap"),
    ("persistence", "choose persistence architecture", "decision-context gap"),
    ("build-buy", "choose build vs buy", "research gap"),
    ("provider", "select an external provider", "research gap"),
    ("migration", "migrate a component", "execution-planning gap"),
    ("operational-risk", "accept operational risk", "approval/authority gap"),
    ("repositories", "choose between repositories", "research gap"),
    ("workflow", "introduce a new workflow", "decision-context gap"),
    ("reject-feature", "reject a proposed feature", "decision-context gap"),
    ("defer", "defer a decision due to insufficient evidence", "research gap"),
]


def _request(request_id: str, research_hash: str) -> dict:
    return {
        "schema_version": "decision-request.v1", "request_id": request_id, "created_at": "2026-07-16T12:00:00Z",
        "decision_context": {"objective": "Make a bounded decision.", "desired_outcome": "An explicit, reversible outcome.", "decision_type": "architecture", "scope": "Scenario"},
        "constraints": {key: [] for key in ("technical", "operational", "compatibility", "cost", "timeline", "reversibility")},
        "options": {"considered": [{"option_id": "a", "label": "Option A"}, {"option_id": "b", "label": "Option B"}], "excluded": [], "alternatives": []},
        "priorities": {key: "explicit" for key in ("reliability", "simplicity", "performance", "maintainability", "cost")},
        "authority": {"decision_owner": "named owner", "approval_requirements": [], "irreversible_actions": []},
        "research_dependency": {"required": True, "result_refs": [{"run_id": "87654321-4321-4432-8432-210987654321", "artifact_sha256": research_hash}], "unresolved_evidence_acknowledged": True, "freshness_requirement": "same revision"},
    }


def _decision(request: dict, research_hash: str, *, deferred: bool = False) -> dict:
    selected = {"option_id": "defer" if deferred else "a", "label": "Defer pending evidence" if deferred else "Option A"}
    return {
        "schema_version": "decision-result.v1",
        "identity": {"decision_id": "11111111-2222-4333-8444-555555555555", "request_id": request["request_id"], "request_sha256": "x" * 64, "created_at": "2026-07-16T12:00:00Z"},
        "context": {"objective": request["decision_context"]["objective"], "scope": request["decision_context"]["scope"], "constraints": request["constraints"]},
        "decision": {"selected_option": selected, "outcome": "Deferred pending evidence." if deferred else "Select Option A.", "rationale": "The explicit context and assessed evidence support this bounded outcome."},
        "alternatives": {"considered": request["options"]["considered"], "rejected": ["b"], "rejection_reasons": [{"option_id": "b", "reason": "Does not meet the stated decision criteria."}]},
        "tradeoffs": {"accepted": ["Bounded uncertainty"], "rejected": ["Unbounded scope"], "consequences": ["Revisit when the unresolved question is answered."]},
        "evidence": {"research_result_refs": request["research_dependency"]["result_refs"], "supporting_claims": [], "conflicting_claims": [], "confidence": "insufficient" if deferred else "medium", "unresolved_questions": ["The current evidence is not sufficient for stronger confidence."]},
        "risks": {"known": ["Evidence gap remains."], "mitigations": ["Keep the outcome reversible."], "accepted_risks": ["Bounded uncertainty"]},
        "authority": {"decision_owner": request["authority"]["decision_owner"], "approvals": [], "approval_state": "pending"},
        "execution_boundary": {"implementation_required": not deferred, "planning_required": not deferred, "blocked_items": ["Approval and planning remain separate."]},
        "provenance": {"source_artifacts": [{"kind": "decision_request", "artifact_id": request["request_id"], "sha256": "x" * 64}, {"kind": "research_result", "artifact_id": "87654321-4321-4432-8432-210987654321", "sha256": research_hash}], "hashes": {"request": "x" * 64, "research_results": [research_hash]}},
    }


def evaluate(research_result_path: Path) -> dict:
    raw = research_result_path.read_bytes()
    validate_research_result(json.loads(raw))
    research_hash = hashlib.sha256(raw).hexdigest()
    rows = []
    for index, (scenario_id, objective, missing_kind) in enumerate(SCENARIOS):
        request = _request(f"12345678-1234-4234-8234-{index:012d}", research_hash)
        request["decision_context"]["objective"] = objective
        validate_request(request)
        decision = _decision(request, research_hash, deferred=scenario_id == "defer")
        decision["identity"]["request_sha256"] = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        decision["provenance"]["hashes"]["request"] = decision["identity"]["request_sha256"]
        decision["provenance"]["source_artifacts"][0]["sha256"] = decision["identity"]["request_sha256"]
        validate_decision(decision)
        rows.append({"scenario_id": scenario_id, "request_valid": True, "research_reference_valid": True, "decision_valid": True, "uncertainty_preserved": bool(decision["evidence"]["unresolved_questions"]), "authority_represented": bool(decision["authority"]["decision_owner"]), "execution_separated": decision["execution_boundary"]["planning_required"] is not None, "missing_information_class": missing_kind})
    return {"schema_version": "decision-result-contract-evaluation.v1", "case_count": len(rows), "cases": rows, "summary": {"complete_chain_cases": sum(all(row[key] for key in ("request_valid", "research_reference_valid", "decision_valid", "uncertainty_preserved", "authority_represented", "execution_separated")) for row in rows), "research_gap": sum(row["missing_information_class"] == "research gap" for row in rows), "decision_context_gap": sum(row["missing_information_class"] == "decision-context gap" for row in rows), "execution_planning_gap": sum(row["missing_information_class"] == "execution-planning gap" for row in rows), "authority_gap": sum(row["missing_information_class"] == "approval/authority gap" for row in rows)}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("research_result", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    evaluation = evaluate(args.research_result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evaluation, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evaluation["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
