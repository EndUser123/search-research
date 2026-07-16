"""Prospective 20-task evaluation of Exa and DDG as restricted complements."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .brave_lane import execute_brave_search, observe_brave
from .external_lane import execute_external_search, observe_external
from .mmx_state import observe_mmx
from .phase1 import LaneExecution, execute_mmx_search, execute_parallel, open_source
from .router import TaskSignals

ROOT = Path(__file__).parents[4]
CORPUS = ROOT / "tests" / "research_run_v1" / "provider_diversity_corpus.json"
MMX = r"C:\Users\brsth\AppData\Roaming\npm\mmx.cmd"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _brave_key() -> str | None:
    if os.environ.get("BRAVE_API_KEY"):
        return os.environ["BRAVE_API_KEY"]
    try:
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if line.startswith("BRAVE_API_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'") or None
    except OSError:
        return None
    return None


def _useful(result: Any, status: str, case: dict[str, Any]) -> bool:
    if status not in {"opened", "anchor_confirmed"}:
        return False
    text = f"{result.title} {result.snippet} {result.url_or_source_ref}".lower()
    return sum(term.lower() in text for term in case["useful_terms"]) >= 2


def _identity(result: Any) -> str:
    parsed = urllib.parse.urlparse(result.url_or_source_ref)
    return f"{parsed.netloc.lower()}{parsed.path.rstrip('/').lower()}"


def _primary(result: Any, case: dict[str, Any]) -> bool:
    host = urllib.parse.urlparse(result.url_or_source_ref).netloc.lower()
    return any(host == domain or host.endswith("." + domain) for domain in case["primary_domains"])


def _provider_metrics(results: list[Any], opened: dict[str, str], case: dict[str, Any]) -> dict[str, Any]:
    identities = [_identity(result) for result in results]
    useful = {_identity(result) for result in results if _useful(result, opened.get(result.result_id, "discovery_only"), case)}
    claim_linked = {_identity(result) for result in results if _primary(result, case) and _useful(result, opened.get(result.result_id, "discovery_only"), case)}
    return {
        "sources_returned": len(results),
        "sources_opened": sum(opened.get(result.result_id) in {"opened", "anchor_confirmed"} for result in results),
        "unique_sources": len(set(identities)),
        "duplicate_sources": len(identities) - len(set(identities)),
        "useful_sources": len(useful),
        "claim_linked_sources": len(claim_linked),
    }


def _measure(case: dict[str, Any], mmx: Any, brave: Any, brave_key: str | None, external: Any, root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    signals = TaskSignals(needs_current_web=True, needs_independent_recall=True, as_of=_now())
    baseline_lanes = execute_parallel((
        ("mmx", lambda: execute_mmx_search(case["query"], signals, mmx)),
        ("brave", lambda: execute_brave_search(case["query"], brave, api_key=brave_key)),
    ), max_workers=2)
    baseline_opened: dict[str, str] = {}
    baseline_failures: list[dict[str, Any]] = []
    for lane in baseline_lanes:
        for result in lane.results[:2]:
            opened = open_source(result, root / "baseline" / case["id"], timeout_seconds=10)
            baseline_opened[result.result_id] = opened.status
            if opened.status == "failed":
                baseline_failures.append({"provider": result.provider, "outcome": opened.failure})
    candidate_lane = execute_external_search(case["query"], external)
    candidate_opened: dict[str, str] = {}
    candidate_failures = list(candidate_lane.failures)
    for result in candidate_lane.results[:2]:
        opened = open_source(result, root / "candidate" / case["id"], timeout_seconds=10)
        candidate_opened[result.result_id] = opened.status
        if opened.status == "failed":
            candidate_failures.append({"provider": result.provider, "outcome": opened.failure})
    baseline_results = [r for lane in baseline_lanes for r in lane.results]
    candidate_results = baseline_results + list(candidate_lane.results)
    baseline_useful = {_identity(r) for r in baseline_results if _useful(r, baseline_opened.get(r.result_id, "discovery_only"), case)}
    candidate_useful = {_identity(r) for r in candidate_results if _useful(r, baseline_opened.get(r.result_id, candidate_opened.get(r.result_id, "discovery_only")), case)}
    complement_useful = {_identity(r) for r in candidate_lane.results if _useful(r, candidate_opened.get(r.result_id, "discovery_only"), case)}
    candidate_primary = {_identity(r) for r in candidate_lane.results if _primary(r, case) and _useful(r, candidate_opened.get(r.result_id, "discovery_only"), case)}
    baseline_metrics = {lane.provider: _provider_metrics(list(lane.results), baseline_opened, case) for lane in baseline_lanes}
    candidate_metrics = _provider_metrics(list(candidate_lane.results), candidate_opened, case)
    return {
        "task_id": case["id"], "query": case["query"], "selected_provider": external.provider,
        "baseline": {"providers": [lane.provider for lane in baseline_lanes], "statuses": {lane.provider: lane.status for lane in baseline_lanes}, "metrics": baseline_metrics, "unique_useful_sources": len(baseline_useful), "failures": baseline_failures},
        "candidate": {"provider": external.provider, "status": candidate_lane.status, "metrics": candidate_metrics, "unique_useful_sources": len(candidate_useful), "complementary_unique_useful_sources": len(complement_useful), "claim_linked_sources": len(candidate_primary), "failures": candidate_failures},
        "decision_changed": bool(complement_useful), "missing_evidence_discovered": bool(candidate_primary - baseline_useful),
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
    }


def evaluate(output_root: Path | None = None) -> dict[str, Any]:
    cases = json.loads(CORPUS.read_text(encoding="utf-8"))
    mmx = observe_mmx(MMX)
    brave = observe_brave(api_key=_brave_key())
    root = output_root or (ROOT / "tmp" / ".codex" / "state" / f"provider-diversity-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
    root.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    observations: dict[str, Any] = {}
    for case in cases:
        provider = case["provider"]
        external = observe_external(provider)
        observations[provider] = external.__dict__
        records.append(_measure(case, mmx, brave, _brave_key(), external, root))
    artifact = {
        "schema": "research-run-v1.provider-diversity-evaluation",
        "observed_at": _now(), "corpus_size": len(cases),
        "baseline_policy": "bounded_parallel_existing_mmx_brave",
        "candidate_policy": "explicit_role_selected_exa_or_duckduckgo_plus_baseline",
        "automatic_routing_change": False,
        "mmx_observation": {"readiness": mmx.readiness, "quota": mmx.quota, "valid_until": mmx.valid_until},
        "brave_observation": {"readiness": brave.readiness, "authentication_state": brave.authentication_state, "valid_until": brave.valid_until},
        "external_observations": observations, "records": records,
        "summary": {
            "provider_counts": {p: sum(r["selected_provider"] == p for r in records) for p in sorted(observations)},
            "unique_complementary_useful_sources": sum(r["candidate"]["complementary_unique_useful_sources"] for r in records),
            "decision_changes": sum(r["decision_changed"] for r in records),
            "missing_evidence_discovered": sum(r["missing_evidence_discovered"] for r in records),
            "baseline_failures": sum(len(r["baseline"]["failures"]) for r in records),
            "candidate_failures": sum(len(r["candidate"]["failures"]) for r in records),
            "total_latency_ms": round(sum(r["latency_ms"] for r in records), 1),
            "provider_metrics": {
                provider: {
                    "queries": sum(1 for r in records if r["selected_provider"] == provider),
                    "sources_returned": sum(r["candidate"]["metrics"]["sources_returned"] for r in records if r["selected_provider"] == provider),
                    "sources_opened": sum(r["candidate"]["metrics"]["sources_opened"] for r in records if r["selected_provider"] == provider),
                    "unique_sources": sum(r["candidate"]["metrics"]["unique_sources"] for r in records if r["selected_provider"] == provider),
                    "duplicate_sources": sum(r["candidate"]["metrics"]["duplicate_sources"] for r in records if r["selected_provider"] == provider),
                    "useful_sources": sum(r["candidate"]["metrics"]["useful_sources"] for r in records if r["selected_provider"] == provider),
                    "claim_linked_sources": sum(r["candidate"]["metrics"]["claim_linked_sources"] for r in records if r["selected_provider"] == provider),
                    "decision_changes": sum(1 for r in records if r["selected_provider"] == provider and r["decision_changed"]),
                    "failures": sum(len(r["candidate"]["failures"]) for r in records if r["selected_provider"] == provider),
                    "latency_ms": round(sum(r["latency_ms"] for r in records if r["selected_provider"] == provider), 1),
                }
                for provider in sorted(observations)
            },
        },
    }
    out = root / "provider-diversity-evaluation.json"
    with out.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(artifact, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    artifact["artifact_path"] = str(out)
    return artifact


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
