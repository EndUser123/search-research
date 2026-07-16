"""Pure 25-task baseline/candidate evaluation for evidence-aware routing."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .router import CapabilityRecord, TaskSignals, default_capabilities, recommend

ROOT = Path(__file__).parents[4]
CORPUS = ROOT / "tests" / "research_run_v1" / "evidence_aware_routing_corpus.json"


def _healthy(item: CapabilityRecord, *, promoted_exa: bool, conditional_ddg: bool) -> CapabilityRecord:
    now = datetime.now(timezone.utc)
    kwargs: dict[str, Any] = {
        "ready": item.lane in {"local", "mmx", "brave", "exa", "duckduckgo"},
        "authenticated": item.lane in {"local", "mmx", "brave", "exa", "duckduckgo"},
        "readiness_observed_at": now.isoformat(),
        "readiness_valid_until": (now + timedelta(hours=1)).isoformat(),
        "observation_method": "evidence-aware-routing-evaluation",
    }
    if item.lane == "exa":
        kwargs.update(automatic=promoted_exa, circuit="CLOSED" if promoted_exa else "RESTRICTED")
    if item.lane == "duckduckgo":
        kwargs.update(automatic=False, circuit="RESTRICTED")
    return replace(item, **kwargs)


def _profile(candidate: bool, signals: TaskSignals) -> tuple[CapabilityRecord, ...]:
    trigger = bool(signals.conditional_lane_trigger)
    return tuple(
        _healthy(item, promoted_exa=candidate, conditional_ddg=candidate and trigger)
        for item in default_capabilities()
        if item.lane not in {"agy", "notebooklm", "native_web"}
        and (item.lane != "duckduckgo" or candidate and trigger)
    )


def evaluate() -> dict[str, Any]:
    cases = json.loads(CORPUS.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    for case in cases:
        raw = dict(case["signals"])
        raw["requested_roles"] = frozenset(raw.get("requested_roles", []))
        signals = TaskSignals(**raw)
        baseline = recommend(signals, _profile(False, signals))
        candidate = recommend(signals, _profile(True, signals))
        records.append({
            "id": case["id"], "query": case["query"],
            "baseline_lanes": [item.lane for item in baseline.recommendations],
            "candidate_lanes": [item.lane for item in candidate.recommendations],
            "baseline_calls": len(baseline.recommendations), "candidate_calls": len(candidate.recommendations),
            "candidate_selection_modes": [item.selection_mode for item in candidate.recommendations],
            "candidate_rejection_reasons": {item.lane: list(item.reasons) for item in candidate.rejected},
            "required_capabilities": list(candidate.required_capabilities),
            "capability_satisfaction": candidate.capability_satisfaction or {},
            "baseline_stop": baseline.stop_reason, "candidate_stop": candidate.stop_reason,
            "lane_set_changed": [item.lane for item in baseline.recommendations] != [item.lane for item in candidate.recommendations],
            "minimum_sufficient": candidate.stop_reason in {"single_best_eligible_lane", "bounded_parallel_wave", "evidence_already_sufficient"},
            "ddg_trigger": signals.conditional_lane_trigger,
        })
    return {
        "schema": "research-run-v1.evidence-aware-routing-evaluation",
        "corpus_size": len(records),
        "baseline_policy": "current_healthy_mmx_brave_with_exa_ddg_unpromoted",
        "candidate_policy": "promoted_exa_semantic_plus_triggered_ddg",
        "automatic_routing_change": True,
        "records": records,
        "summary": {
            "baseline_provider_calls": sum(item["baseline_calls"] for item in records),
            "candidate_provider_calls": sum(item["candidate_calls"] for item in records),
            "lane_set_changes": sum(item["lane_set_changed"] for item in records),
            "minimum_sufficient_cases": sum(item["minimum_sufficient"] for item in records),
            "unnecessary_lane_executions": sum(max(0, item["candidate_calls"] - len(item["required_capabilities"])) for item in records),
            "exa_semantic_selections": sum("exa" in item["candidate_lanes"] for item in records if "semantic_external_discovery" in item["required_capabilities"]),
            "ddg_conditional_selections": sum("duckduckgo" in item["candidate_lanes"] for item in records),
        },
    }


def write_evaluation(output: Path | None = None) -> Path:
    target = output or (ROOT / "tmp" / ".codex" / "state" / f"evidence-aware-routing-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
    target.mkdir(parents=True, exist_ok=True)
    path = target / "evaluation.json"
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump({"observed_at": datetime.now(timezone.utc).isoformat(), **evaluate()}, handle, indent=2)
        handle.write("\n")
    return path


if __name__ == "__main__":
    print(json.dumps({"artifact_path": str(write_evaluation()), **evaluate()}, indent=2))
