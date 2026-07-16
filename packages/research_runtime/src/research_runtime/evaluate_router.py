"""Evaluate the bounded provider-neutral router corpus without provider calls."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from .router import CapabilityRecord, TaskSignals, default_capabilities, recommend


ROOT = Path(__file__).parents[4]
CORPUS = ROOT / "tests" / "research_run_v1" / "router_corpus.json"
OBSERVED = "2026-07-15T12:00:00Z"
VALID_UNTIL = "2026-07-16T12:00:00Z"


def _replace_lane(capabilities: tuple[CapabilityRecord, ...], lane: str, **changes: Any) -> tuple[CapabilityRecord, ...]:
    return tuple(replace(item, **changes) if item.lane == lane else item for item in capabilities)


def capabilities_for(profile: str) -> tuple[CapabilityRecord, ...]:
    base = default_capabilities()
    healthy = dict(ready=True, readiness_observed_at=OBSERVED, readiness_valid_until=VALID_UNTIL, observation_method="bounded-readiness-record", authenticated=True)
    if profile == "healthy_mmx":
        return _replace_lane(base, "mmx", **healthy, quota_remaining_percent=80.0)
    if profile == "healthy_notebooklm":
        return _replace_lane(base, "notebooklm", **healthy, automatic=True)
    if profile == "healthy_agy":
        return _replace_lane(base, "agy", **healthy, accepted_roles=frozenset({"AGY_SEARCH_INDEPENDENT", "AGY_SEARCH_DEEP", "AGY_SEARCH_ADVERSARIAL"}))
    if profile == "healthy_mmx_only":
        return (replace(next(item for item in base if item.lane == "mmx"), **healthy, quota_remaining_percent=80.0),)
    if profile == "degraded_mmx_only":
        return (replace(next(item for item in base if item.lane == "mmx"), **healthy, quota_remaining_percent=5.0),)
    if profile == "stale_mmx":
        stale = dict(healthy, readiness_valid_until="2026-07-15T12:00:00Z", quota_remaining_percent=80.0)
        return (replace(next(item for item in base if item.lane == "mmx"), **stale),)
    return base


def signals_for(raw: dict[str, Any]) -> TaskSignals:
    values = dict(raw)
    for field in ("attempted_lanes", "failed_lanes", "requested_roles"):
        values[field] = frozenset(values.get(field, []))
    return TaskSignals(**values)


def load_cases(path: Path = CORPUS) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    result = recommend(signals_for(case["signals"]), capabilities_for(case["profile"]))
    rejected = {item.lane: item.reasons for item in result.rejected}
    return {
        "id": case["id"],
        "description": case["description"],
        "baseline_policy": case["baseline_policy"],
        "prior_router": case["prior_router"],
        "refined_router": result.recommendations[0].lane if result.recommendations else None,
        "rejected": {lane: list(reasons) for lane, reasons in rejected.items()},
        "human_escalation": result.human_escalation,
        "escalation_reasons": list(result.escalation_reasons),
        "stop_reason": result.stop_reason,
        "expected_lane": case["expected_lane"],
        "expected_escalation": case["expected_escalation"],
        "expected_stop": case["stop"],
        "required_rejection": case.get("required_rejection"),
    }


def evaluate(path: Path = CORPUS) -> list[dict[str, Any]]:
    return [evaluate_case(case) for case in load_cases(path)]


def main() -> int:
    results = evaluate()
    print(json.dumps({"schema": "research-router-evaluation.v1", "cases": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
