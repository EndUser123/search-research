from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from research_runtime.evaluate_evidence_aware_routing import evaluate


def test_evidence_aware_corpus_has_25_cases_and_no_unnecessary_candidate_lanes():
    result = evaluate()
    assert result["corpus_size"] == 25
    assert result["summary"]["minimum_sufficient_cases"] == 25
    assert result["summary"]["unnecessary_lane_executions"] == 0


def test_evidence_aware_routing_promotes_exa_but_keeps_ddg_conditional():
    records = {item["id"]: item for item in evaluate()["records"]}
    assert records["semantic-memory"]["candidate_lanes"] == ["exa"]
    assert records["semantic-implementation"]["candidate_lanes"] == ["brave", "exa"]
    assert records["ddg-omission"]["candidate_lanes"] == ["duckduckgo"]
    assert records["concept-options"]["candidate_lanes"] == ["mmx"]
