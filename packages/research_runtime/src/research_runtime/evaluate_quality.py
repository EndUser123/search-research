"""Evaluate research-quality planning against a fixed agentic-coding corpus."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Support direct script execution by adding src to sys.path
_SRC = Path(__file__).parents[1]  # .../research_runtime/src/
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from research_runtime.quality import plan_research_quality
from research_runtime.router import TaskSignals


def evaluate(corpus_path: Path) -> dict[str, Any]:
    cases = json.loads(corpus_path.read_text(encoding="utf-8"))
    records = []
    for case in cases:
        signals = TaskSignals(
            decision_impact=case["impact"],
            needs_local_context="local" in case["categories"],
            needs_primary_source_verification="authority" in case["categories"],
            requested_roles=frozenset({
                "IMPLEMENTATION_DISCOVERY" if "implementation" in case["categories"] else "CONCEPTUAL_RECALL",
                *({"MAINTENANCE_STATUS"} if "maintenance" in case["categories"] else set()),
                *({"COMPATIBILITY_RESEARCH"} if "compatibility" in case["categories"] else set()),
                *({"OMISSION_SENSITIVE_DISCOVERY"} if "failure" in case["categories"] else set()),
            }),
        )
        plan = plan_research_quality(case["question"], signals)
        expected = set(case["categories"])
        planned = set(plan["required_categories"])
        records.append({
            "id": case["id"],
            "expected_categories": case["categories"],
            "planned_categories": plan["required_categories"],
            "category_recall": round(len(expected & planned) / len(expected), 3),
            "targeted_query_count": len(plan["targeted_queries"]),
            "inverse_search": plan["inverse_search"],
        })
    return {
        "schema": "research-quality-evaluation.v1",
        "corpus_size": len(records),
        "category_recall_mean": round(sum(r["category_recall"] for r in records) / len(records), 3),
        "inverse_planned_cases": sum(r["inverse_search"]["eligible"] for r in records),
        "bounded_query_cases": sum(r["targeted_query_count"] <= 4 for r in records),
        "records": records,
        "authorization": "evaluation_only; no provider invocation or routing change",
    }


if __name__ == "__main__":
    corpus = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tests/research_run_v1/research_quality_corpus.json"
    print(json.dumps(evaluate(corpus), indent=2))
