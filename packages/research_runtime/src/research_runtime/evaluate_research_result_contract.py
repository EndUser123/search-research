"""Evaluate the research-result.v1 boundary against representative design inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .research_result import build_research_result, validate, write_result

CASES = [
    ("agent-framework", "Choose an agent framework for bounded orchestration."),
    ("persistence", "Choose persistence for investigation state across sessions."),
    ("provider", "Choose whether to adopt a new research provider."),
    ("retrieval", "Choose local-only, web-only, or combined retrieval."),
    ("lifecycle", "Choose process lifecycle and cleanup ownership."),
    ("migration", "Choose a migration strategy for the research artifact schema."),
    ("build-buy", "Choose build versus buy for source opening and extraction."),
    ("security", "Choose credential and workspace isolation boundaries."),
    ("performance", "Choose a latency and quota budget for research runs."),
    ("production", "Choose whether the research workflow is ready for limited pilot."),
]


def evaluate(result: dict) -> dict:
    validate(result)
    rows = []
    for case_id, question in CASES:
        has_context = bool(result["context"]["research_question"] and result["context"]["requested_decision"])
        has_provenance = bool(result["provenance"]["sources"] or result["provenance"]["lanes"])
        unresolved = bool(result["unresolved_questions"])
        decision_separation = result["authorization"]["research_may_decide"] is False and not result["options"]
        rows.append({
            "case_id": case_id,
            "input": question,
            "context_available": has_context,
            "provenance_available": has_provenance,
            "unresolved_evidence_explicit": unresolved,
            "decision_separation_preserved": decision_separation,
            "handoff_status": "needs_more_evidence_or_downstream_options" if unresolved or not result["options"] else "ready_for_downstream_assessment",
            "action_change": "downstream consumer must gather/define missing evidence and options before deciding",
        })
    return {
        "schema_version": "research-result-contract-evaluation.v1",
        "result_run_id": result["run_id"],
        "case_count": len(rows),
        "cases": rows,
        "summary": {
            "context_preserved": all(row["context_available"] for row in rows),
            "provenance_preserved": all(row["provenance_available"] for row in rows),
            "claim_decision_separation_preserved": all(row["decision_separation_preserved"] for row in rows),
            "cases_requiring_more_evidence": sum(row["handoff_status"] != "ready_for_downstream_assessment" for row in rows),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    raw = args.artifact.read_bytes()
    artifact = json.loads(raw)
    result = build_research_result(artifact, artifact_sha256=hashlib.sha256(raw).hexdigest())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result_path = args.output_dir / "research-result.json"
    write_result(result_path, result)
    evaluation = evaluate(result)
    (args.output_dir / "contract-evaluation.json").write_text(json.dumps(evaluation, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(result_path), "evaluation": str(args.output_dir / 'contract-evaluation.json'), "summary": evaluation["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
