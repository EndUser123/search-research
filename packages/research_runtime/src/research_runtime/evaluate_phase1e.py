"""Phase 1E live comparison: MMX versus one bounded Brave discovery lane.

The corpus uses evaluator-supplied lexical relevance rules.  It does not infer
claim truth, and search snippets remain discovery-only until a source is opened.
Only three cases run the genuinely concurrent wave to bound MMX consumption;
all ten cases run each lane alone for direct comparison.
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .brave_lane import BraveObservation, execute_brave_search, observe_brave
from .mmx_state import MMXObservation, observe_mmx
from .phase1 import LaneExecution, NormalizedResult, execute_mmx_search, execute_parallel, open_source
from .router import TaskSignals


ROOT = Path(__file__).parents[4]
CORPUS = ROOT / "tests" / "research_run_v1" / "phase1e_eval_corpus.json"
MMX = r"C:\Users\brsth\AppData\Roaming\npm\mmx.cmd"
BRAVE_KEY_NAME = "BRAVE_API_KEY"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_brave_key() -> str | None:
    value = os.environ.get(BRAVE_KEY_NAME)
    if value:
        return value
    env_path = ROOT / ".env"
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{BRAVE_KEY_NAME}="):
                value = line.split("=", 1)[1].strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                    value = value[1:-1]
                return value or None
    except OSError:
        return None
    return None


def _underlying_identity(result: NormalizedResult) -> str:
    parsed = urllib.parse.urlparse(result.url_or_source_ref)
    host = parsed.netloc.lower()
    path = parsed.path.rstrip("/").lower()
    if host == "github.com":
        parts = [part for part in path.split("/") if part]
        if len(parts) >= 2:
            return f"github:{parts[0]}/{parts[1]}"
    return f"url:{host}{path}"


def _is_primary(result: NormalizedResult, case: dict[str, Any]) -> bool:
    host = urllib.parse.urlparse(result.url_or_source_ref).netloc.lower()
    return any(host == domain or host.endswith("." + domain) for domain in case["primary_domains"])


def _is_useful(result: NormalizedResult, opened_status: str, case: dict[str, Any]) -> bool:
    if opened_status not in {"opened", "anchor_confirmed"}:
        return False
    text = f"{result.title} {result.snippet} {result.url_or_source_ref}".lower()
    return sum(term.lower() in text for term in case["useful_terms"]) >= 2


def _is_contradictory(result: NormalizedResult, case: dict[str, Any]) -> bool:
    text = f"{result.title} {result.snippet}".lower()
    return any(term.lower() in text for term in case["contradiction_terms"])


def _lane_run(mode: str, query: str, mmx: MMXObservation, brave: BraveObservation, brave_key: str | None) -> tuple[tuple[LaneExecution, ...], dict[str, float], float]:
    signals = TaskSignals(needs_current_web=True, needs_independent_recall=True, as_of=_now())
    lane_times: dict[str, float] = {}

    def timed(name: str, callback):
        started = time.perf_counter()
        try:
            return callback()
        finally:
            lane_times[name] = round((time.perf_counter() - started) * 1000, 1)

    wave_started = time.perf_counter()
    if mode == "mmx_only":
        lanes = (timed("mmx", lambda: execute_mmx_search(query, signals, mmx)),)
    elif mode == "brave_only":
        lanes = (timed("brave", lambda: execute_brave_search(query, brave, api_key=brave_key)),)
    elif mode == "parallel":
        lanes = execute_parallel((
            ("mmx", lambda: timed("mmx", lambda: execute_mmx_search(query, signals, mmx))),
            ("brave", lambda: timed("brave", lambda: execute_brave_search(query, brave, api_key=brave_key))),
        ))
    else:
        raise ValueError(mode)
    return lanes, lane_times, round((time.perf_counter() - wave_started) * 1000, 1)


def _measure(case: dict[str, Any], mode: str, mmx: MMXObservation, brave: BraveObservation, brave_key: str | None, root: Path) -> dict[str, Any]:
    total_started = time.perf_counter()
    lanes, lane_times, wave_ms = _lane_run(mode, case["query"], mmx, brave, brave_key)
    all_results = [result for lane in lanes for result in lane.results]
    canonical_ids = [result.source_identity or result.url_or_source_ref.rstrip("/").lower() for result in all_results]
    underlying_ids = [_underlying_identity(result) for result in all_results]
    source_start = time.perf_counter()
    opened_by_result: dict[str, str] = {}
    opening_failures: list[dict[str, Any]] = []
    for result in all_results[:6]:
        opened = open_source(result, root / mode, timeout_seconds=10)
        opened_by_result[result.result_id] = opened.status
        if opened.status == "failed":
            opening_failures.append({"result_id": result.result_id, "provider": result.provider, "outcome": opened.failure})
    source_open_ms = round((time.perf_counter() - source_start) * 1000, 1)
    assessment_start = time.perf_counter()
    unique_canonical = set(canonical_ids)
    useful_underlying = {_underlying_identity(result) for result in all_results if _is_useful(result, opened_by_result.get(result.result_id, "discovery_only"), case)}
    authoritative_underlying = {_underlying_identity(result) for result in all_results if _is_useful(result, opened_by_result.get(result.result_id, "discovery_only"), case) and _is_primary(result, case)}
    contradictory = {_underlying_identity(result) for result in all_results if _is_contradictory(result, case)}
    duplicate_canonical = len(all_results) - len(unique_canonical)
    duplicate_underlying = len(all_results) - len(set(underlying_ids)) - duplicate_canonical
    direct_support = len(authoritative_underlying)
    partial_support = len(useful_underlying - authoritative_underlying)
    insufficient = len(all_results) - len(useful_underlying)
    assessment_ms = round((time.perf_counter() - assessment_start) * 1000, 1)
    details = [{"provider": result.provider, "title": result.title, "url": result.url_or_source_ref, "status": opened_by_result.get(result.result_id, "discovery_only"), "underlying_source": _underlying_identity(result), "useful": _is_useful(result, opened_by_result.get(result.result_id, "discovery_only"), case), "authoritative": _is_primary(result, case), "contradictory": _is_contradictory(result, case)} for result in all_results]
    total_ms = round((time.perf_counter() - total_started) * 1000, 1)
    return {
        "question_id": case["id"], "mode": mode, "query": case["query"],
        "mmx_lane_wall_time_ms": lane_times.get("mmx", 0.0), "complementary_lane_wall_time_ms": lane_times.get("brave", 0.0),
        "parallel_wave_wall_time_ms": wave_ms if mode == "parallel" else 0.0, "source_open_time_ms": source_open_ms,
        "assessment_time_ms": assessment_ms, "artifact_write_time_ms": 0.0, "total_run_time_ms": total_ms,
        "candidate_count": len(all_results), "canonical_duplicate_count": duplicate_canonical, "same_underlying_source_duplicate_count": max(0, duplicate_underlying),
        "unique_useful_sources": len(useful_underlying), "unique_authoritative_sources": len(authoritative_underlying),
        "opened_primary_sources": sum(1 for result in all_results if _is_primary(result, case) and opened_by_result.get(result.result_id) in {"opened", "anchor_confirmed"}),
        "directly_supporting_sources": direct_support, "partially_supporting_sources": partial_support, "contradictory_sources": len(contradictory), "insufficient_sources": max(0, insufficient),
        "source_opening_failures": opening_failures, "lane_failures": [failure for lane in lanes for failure in lane.failures],
        "action": "usable_evidence" if useful_underlying else "insufficient_evidence", "sources": details,
    }


def evaluate() -> dict[str, Any]:
    cases = json.loads(CORPUS.read_text(encoding="utf-8"))
    mmx = observe_mmx(MMX)
    brave_key = _load_brave_key()
    brave = observe_brave(api_key=brave_key)
    root = ROOT / "tmp" / ".codex" / "state" / "phase1e-evaluation-20260713"
    root.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for index, case in enumerate(cases):
        records.append(_measure(case, "mmx_only", mmx, brave, brave_key, root))
        records.append(_measure(case, "brave_only", mmx, brave, brave_key, root))
        if index in {0, 4, 9}:
            records.append(_measure(case, "parallel", mmx, brave, brave_key, root))
    artifact = {"schema": "research-run-v1.phase1e-evaluation", "phase": "1E", "observed_at": _now(), "corpus_size": len(cases), "selected_complementary_lane": "brave", "reference_assessment": "evaluator_supplied_lexical_relevance_and_authority_rules_in_phase1e_eval_corpus.json", "mmx_observation": {"readiness": mmx.readiness, "version": mmx.executable_version, "quota": mmx.quota, "valid_until": mmx.valid_until}, "brave_observation": {"readiness": brave.readiness, "authentication_state": brave.authentication_state, "observation_method": brave.observation_method, "valid_until": brave.valid_until, "quota": brave.quota}, "records": records}
    write_start = time.perf_counter()
    out = root / "phase1e-evaluation.json"
    artifact["artifact_write_time_ms"] = 0.0
    out.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
    artifact["artifact_write_time_ms"] = round((time.perf_counter() - write_start) * 1000, 1)
    out.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
    return artifact


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
