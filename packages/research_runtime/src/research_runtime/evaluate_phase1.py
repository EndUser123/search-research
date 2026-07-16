"""Measured Phase 1 comparison using MMX and the verified local QMD lane.

This is an evaluation harness, not a provider broker. It runs a fixed corpus
with explicit lane modes and emits metrics without changing routing policy.
"""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .mmx_state import MMXObservation, observe_mmx
from .phase1 import LaneExecution, NormalizedResult, execute_mmx_search, execute_parallel, open_source
from .router import TaskSignals


ROOT = Path(__file__).parents[4]
CORPUS = ROOT / "tests" / "research_run_v1" / "phase1_eval_corpus.json"
MMX = r"C:\Users\brsth\AppData\Roaming\npm\mmx.cmd"
QMD = r"C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\qmd.exe"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _qmd_lane(query: str) -> LaneExecution:
    started = _now()
    try:
        completed = subprocess.run([QMD, "query", query, "--collection", "wiki", "--limit", "5", "--format", "json"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45, check=False)
    except subprocess.TimeoutExpired:
        return LaneExecution("qmd", "qmd", "context_retrieval", query, "failed", started, _now(), failures=({"outcome": "timeout"},))
    if completed.returncode != 0:
        return LaneExecution("qmd", "qmd", "context_retrieval", query, "failed", started, _now(), failures=({"outcome": f"exit_code:{completed.returncode}"},))
    if completed.stdout.strip() == "No matching documents found":
        return LaneExecution("qmd", "qmd", "context_retrieval", query, "empty", started, _now())
    try:
        rows = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return LaneExecution("qmd", "qmd", "context_retrieval", query, "failed", started, _now(), failures=({"outcome": "malformed_json"},))
    results: list[NormalizedResult] = []
    seen: set[str] = set()
    for index, row in enumerate(rows if isinstance(rows, list) else []):
        if not isinstance(row, dict) or not isinstance(row.get("file"), str):
            continue
        source_ref = f"qmd://wiki/{row['file']}"
        if source_ref in seen:
            continue
        seen.add(source_ref)
        results.append(NormalizedResult("qmd", "context_retrieval", query, f"qmd-{index}-{row.get('docid', index)}", str(row.get("title") or row["file"]), source_ref, str(row.get("snippet") or ""), None, _now(), source_identity=source_ref))
    return LaneExecution("qmd", "qmd", "context_retrieval", query, "success" if results else "empty", started, _now(), results=tuple(results))


def _useful(result: NormalizedResult, root: Path) -> bool:
    if result.provider == "qmd":
        relative = result.url_or_source_ref.removeprefix("qmd://wiki/").removeprefix("wiki/")
        path = ROOT / ".data" / "wiki" / relative
        return path.is_file() and path.stat().st_size > 0
    opened = open_source(result, root / result.provider, timeout_seconds=15)
    return opened.status in {"opened", "anchor_confirmed"}


def _measure(mode: str, question: dict[str, str], observation: MMXObservation, root: Path) -> dict[str, Any]:
    query = question["query"]
    started = time.perf_counter()
    signals = TaskSignals(needs_current_web=True, needs_independent_recall=True, as_of=_now())
    lane_started = time.perf_counter()
    if mode == "mmx_only":
        lanes = (execute_mmx_search(query, signals, observation),)
    elif mode == "qmd_only":
        lanes = (_qmd_lane(query),)
    elif mode == "parallel":
        lanes = execute_parallel((("mmx", lambda: execute_mmx_search(query, signals, observation)), ("qmd", lambda: _qmd_lane(query))))
    else:
        raise ValueError(mode)
    lane_wall_time_ms = round((time.perf_counter() - lane_started) * 1000, 1)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    all_results = [result for lane in lanes for result in lane.results]
    identities = [result.source_identity or result.url_or_source_ref for result in all_results]
    unique = set(identities)
    source_started = time.perf_counter()
    useful_ids = {
        result.source_identity or result.url_or_source_ref
        for result in all_results[:5]
        if _useful(result, root)
    }
    source_open_time_ms = round((time.perf_counter() - source_started) * 1000, 1)
    failures = [failure for lane in lanes for failure in lane.failures]
    return {"question_id": question["id"], "mode": mode, "elapsed_ms": elapsed_ms, "lane_wall_time_ms": lane_wall_time_ms, "source_open_time_ms": source_open_time_ms, "assessment_time_ms": 0.0, "artifact_write_time_ms": 0.0, "total_run_time_ms": elapsed_ms, "providers_invoked": [lane.provider for lane in lanes if lane.status != "not_attempted"], "lane_statuses": {lane.lane_id: lane.status for lane in lanes}, "candidate_count": len(all_results), "unique_sources": len(unique), "duplicate_count": len(all_results) - len(unique), "useful_sources": len(useful_ids), "failures": failures, "action": "usable_evidence" if useful_ids else "incomplete"}


def evaluate() -> dict[str, Any]:
    cases = json.loads(CORPUS.read_text(encoding="utf-8"))
    observation = observe_mmx(MMX)
    root = ROOT / "tmp" / ".codex" / "state" / "phase1-evaluation-20260713"
    root.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for case in cases:
        if case["mode"] in {"mmx_only", "qmd_only", "parallel"}:
            records.append(_measure(case["mode"], case, observation, root))
        if case.get("compare_parallel"):
            baseline = records[-1]
            for mode in ("mmx_only", "qmd_only", "parallel"):
                if mode != case["mode"]:
                    records.append(_measure(mode, case, observation, root))
                    records[-1]["comparison_group"] = case["id"]
            baseline["comparison_group"] = case["id"]
    return {"schema": "research-run-v1.phase1-evaluation", "observed_at": _now(), "mmx_observation": {"readiness": observation.readiness, "version": observation.executable_version, "quota": observation.quota, "valid_until": observation.valid_until}, "cases": records}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
