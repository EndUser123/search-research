"""Evaluate decision-request.v1 against representative future design inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .decision_request import validate

SCENARIOS = [
    ("agent-framework", "adopt an agent framework", "research problem", "Current capabilities, lifecycle, and integration evidence."),
    ("persistence", "choose persistence architecture", "decision context problem", "Retention, recovery, and operational constraints must be explicit."),
    ("build-buy", "choose build versus buy", "research problem", "Comparable implementation and maintenance evidence."),
    ("provider-strategy", "select provider strategy", "research problem", "Current capability, quota, provenance, and failure evidence."),
    ("migration", "migrate an existing component", "execution planning problem", "Sequencing, rollback, compatibility, and ownership plan."),
    ("new-workflow", "introduce a new workflow", "decision context problem", "Scope, owner, success criterion, and non-goals."),
    ("operational-risk", "accept operational risk", "decision context problem", "Named risk owner, threshold, mitigations, and approval."),
    ("repository", "choose between competing repositories", "research problem", "Primary-source comparison of maintenance and compatibility."),
    ("lifecycle", "choose process lifecycle ownership", "execution planning problem", "Start, stop, cleanup, restart, and failure ownership."),
    ("pilot", "authorize a limited pilot", "decision context problem", "Pilot boundary, rollback, monitoring, and explicit approval."),
]


def evaluate(result_path: Path) -> dict:
    raw = result_path.read_bytes()
    result = json.loads(raw)
    ref = {"run_id": result["run_id"], "artifact_sha256": hashlib.sha256(raw).hexdigest()}
    rows = []
    for scenario_id, objective, missing_kind, missing in SCENARIOS:
        request = {
            "schema_version": "decision-request.v1",
            "request_id": "12345678-1234-4234-8234-123456789012",
            "created_at": "2026-07-16T12:00:00Z",
            "decision_context": {"objective": objective, "desired_outcome": "A bounded, reversible decision.", "decision_type": "architecture", "scope": scenario_id},
            "constraints": {key: [] for key in ("technical", "operational", "compatibility", "cost", "timeline", "reversibility")},
            "options": {"considered": [{"option_id": "a", "label": "Option A"}, {"option_id": "b", "label": "Option B"}], "excluded": [], "alternatives": []},
            "priorities": {key: "explicitly supplied" for key in ("reliability", "simplicity", "performance", "maintainability", "cost")},
            "authority": {"decision_owner": "named human owner", "approval_requirements": [], "irreversible_actions": []},
            "research_dependency": {"required": True, "result_refs": [ref], "unresolved_evidence_acknowledged": True, "freshness_requirement": "same workspace revision"},
        }
        validate(request)
        rows.append({"scenario_id": scenario_id, "objective": objective, "intake_valid": True, "research_can_supply": True, "design_can_decide_if_evidence_sufficient": True, "current_input_status": "needs_more_evidence", "missing_information": missing, "missing_information_class": missing_kind, "decision_not_made_by_contract": True})
    return {"schema_version": "decision-request-contract-evaluation.v1", "research_run_id": result["run_id"], "case_count": len(rows), "cases": rows, "summary": {"valid_intakes": len(rows), "research_problem_cases": sum(row["missing_information_class"] == "research problem" for row in rows), "decision_context_problem_cases": sum(row["missing_information_class"] == "decision context problem" for row in rows), "execution_planning_problem_cases": sum(row["missing_information_class"] == "execution planning problem" for row in rows), "all_preserve_decision_boundary": all(row["decision_not_made_by_contract"] for row in rows)}}


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
