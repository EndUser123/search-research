"""Pure Phase 1 role-policy corpus evaluator; it never invokes providers."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from .router import CapabilityRecord, TaskSignals, default_capabilities, recommend

ROOT = Path(__file__).parents[4]
CORPUS = ROOT / "tests" / "research_run_v1" / "phase1_policy_corpus.json"
OBSERVED = "2026-07-15T12:00:00Z"
VALID_UNTIL = "2026-07-16T12:00:00Z"


def _profile(name: str) -> tuple[CapabilityRecord, ...]:
    base = default_capabilities()
    healthy = dict(ready=True, readiness_observed_at=OBSERVED, readiness_valid_until=VALID_UNTIL, observation_method="policy-test", authenticated=True)
    if name == "healthy_shared_external":
        return tuple(replace(item, **healthy, quota_remaining_percent=80.0) if item.lane == "mmx" else replace(item, **healthy) if item.lane == "brave" else item for item in base)
    if name == "degraded_mmx_brave":
        return tuple(replace(item, **healthy, quota_remaining_percent=5.0) if item.lane == "mmx" else replace(item, **healthy) if item.lane == "brave" else item for item in base)
    raise ValueError(name)


def evaluate() -> list[dict[str, Any]]:
    cases = json.loads(CORPUS.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    for case in cases:
        raw = dict(case["signals"])
        raw["requested_roles"] = frozenset(raw.get("requested_roles", []))
        result = recommend(TaskSignals(**raw), _profile(case["profile"]))
        results.append({"id": case["id"], "lanes": [item.lane for item in result.recommendations], "selection_modes": [item.selection_mode for item in result.recommendations], "stop_reason": result.stop_reason, "human_escalation": result.human_escalation, "rejected": {item.lane: list(item.reasons) for item in result.rejected}, "expected_lanes": case["expected_lanes"], "expected_stop": case["expected_stop"], "expected_escalation": case["expected_escalation"]})
    return results


if __name__ == "__main__":
    print(json.dumps({"schema": "research-router-policy-evaluation.v1", "cases": evaluate()}, indent=2))
