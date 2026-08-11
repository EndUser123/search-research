from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from research_runtime.evaluate_policy import evaluate  # noqa: E402


def test_phase1_role_policy_corpus_matches() -> None:
    results = evaluate()
    assert len(results) == 15
    for result in results:
        assert result["lanes"] == result["expected_lanes"], result
        assert result["stop_reason"] == result["expected_stop"], result
        assert result["human_escalation"] == result["expected_escalation"], result


def test_healthy_provider_roles_are_automatic_without_per_call_approval() -> None:
    results = {item["id"]: item for item in evaluate()}
    assert results["implementation-example"]["selection_modes"] == ["automatic"]
    assert results["broad-conceptual"]["selection_modes"] == ["automatic"]
    assert results["mixed-roles"]["selection_modes"] == ["automatic", "automatic"]


def test_policy_evaluator_is_provider_free() -> None:
    assert "subprocess" not in Path(ROOT / "packages/research_runtime/src/research_runtime/evaluate_policy.py").read_text(encoding="utf-8")
