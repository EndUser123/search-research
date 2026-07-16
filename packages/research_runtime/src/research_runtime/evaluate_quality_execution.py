"""Bounded real A/B evaluation of quality-guided query execution.

This is an evaluation harness, not a change to the /all caller. Control uses
the original question. Candidate executes one supplemental query selected from
the deterministic quality plan. All provider calls use the existing
search-research:/all Phase 1 path.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

from .quality import plan_research_quality
from .router import TaskSignals

CASES = (
    ("repository-adoption", "Should we adopt a maintained repository for agentic coding workflows?", "adoption"),
    ("architecture-choice", "Which architecture should our provider-neutral research runner use?", "architecture"),
    ("implementation-comparison", "Compare implementation approaches for durable agentic task state.", "implementation"),
    ("official-lookup", "What does the official Python asyncio subprocess documentation guarantee about pipes?", "authority"),
    ("compatibility", "What Windows compatibility limits affect subprocess cleanup for coding workers?", "compatibility"),
    ("maintenance", "Is the selected agentic coding library actively maintained?", "maintenance"),
    ("local-external", "How should our workspace combine local QMD knowledge with external research?", "mixed"),
    ("insufficient-identity", "What is the authoritative backend model identity of this advisory worker?", "insufficient"),
    ("insufficient-authority", "Can this discovered source alone authorize a production decision?", "insufficient"),
    ("duplicate-docs", "Python asyncio subprocess documentation official current versions 3.14 3.12 3.9", "duplicates"),
    ("failure-modes", "What failure modes and cleanup risks affect agentic coding workers?", "failure"),
    ("repository-maintenance", "Which repository implementation is active, maintained, and compatible with Windows?", "repository"),
    ("local-architecture", "What prior workspace decisions describe our research router architecture?", "local"),
    ("evidence-sufficient-candidate", "The official source is already opened; confirm the documented pipe behavior.", "sufficient_candidate"),
    ("implementation-authority", "Find official implementation evidence for bounded Windows subprocess execution.", "mixed_authority"),
)


def signals_for(question: str, kind: str) -> TaskSignals:
    words = question.lower()
    roles: set[str] = set()
    if kind in {"adoption", "architecture", "implementation", "mixed", "mixed_authority"}:
        roles.add("IMPLEMENTATION_DISCOVERY")
    if kind in {"repository", "repository-maintenance"}:
        roles.add("REPOSITORY_PROJECT_DISCOVERY")
    if kind in {"maintenance", "repository-maintenance"}:
        roles.add("MAINTENANCE_STATUS")
    if kind == "compatibility" or "windows" in words:
        roles.add("COMPATIBILITY_RESEARCH")
    if kind in {"failure", "adoption", "architecture", "insufficient"}:
        roles.add("OMISSION_SENSITIVE_DISCOVERY")
    if kind in {"authority", "mixed_authority", "insufficient"} or "official" in words or "authoritative" in words:
        needs_authority = True
    else:
        needs_authority = False
    local = kind in {"local", "mixed", "architecture", "local-external"} or "workspace" in words or "our " in words
    conceptual = kind in {"adoption", "architecture", "implementation", "mixed", "failure"} or "compare" in words
    if conceptual:
        roles.add("CONCEPTUAL_RECALL")
    return TaskSignals(
        needs_local_context=local,
        needs_current_web=not local or kind not in {"local"},
        needs_independent_recall=not local or conceptual,
        needs_primary_source_verification=needs_authority,
        decision_impact="high" if kind in {"adoption", "architecture", "compatibility", "insufficient", "mixed_authority"} else "low",
        requested_roles=frozenset(roles),
        allow_parallel=local and bool(roles),
        parallel_trigger="distinct_complementary_roles" if local and roles else None,
    )


def _metrics(artifact: dict[str, Any]) -> dict[str, Any]:
    sources = artifact.get("sources", [])
    quality = artifact.get("quality", {})
    contribution = quality.get("source_contribution", {})
    opened = [s for s in sources if s.get("discovery_status") in {"opened", "anchor_confirmed", "verified"}]
    authority = [s for s in opened if s.get("source_type") == "primary"]
    return {
        "providers_used": [lane.get("provider") for lane in artifact.get("retrieval_lanes", [])],
        "sources_returned": len(sources),
        "sources_opened": len(opened),
        "useful_sources": contribution.get("unique_useful_sources", 0),
        "authority_sources": len(authority),
        "claim_status": [claim.get("status") for claim in artifact.get("claims", [])],
        "missing_evidence": quality.get("stopping", {}).get("missing_categories", []),
        "stop_reason": quality.get("stopping", {}).get("status", artifact.get("stop_reason")),
        "runtime_ms": artifact.get("integration_telemetry", {}).get("total_runtime_ms"),
        "failures": [failure for lane in artifact.get("retrieval_lanes", []) for failure in lane.get("failures", [])],
    }


def decision_changed(control: dict[str, Any], candidate: dict[str, Any]) -> bool:
    """A decision change means a changed stop/action, not a claim detail."""

    return control.get("stop_reason") != candidate.get("stop_reason")


async def _run_one(question: str, mode: str) -> tuple[dict[str, Any], str]:
    from skills.all.search_executor import execute_phase1_for_all
    _, artifact_path = await execute_phase1_for_all(question, mode="auto")
    path = Path(artifact_path)
    return json.loads(path.read_text(encoding="utf-8")), str(path)


async def evaluate() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for case_id, question, kind in CASES:
        signals = signals_for(question, kind)
        plan = plan_research_quality(question, signals)
        started = time.perf_counter()
        control, control_path = await _run_one(question, "control")
        control_elapsed = round((time.perf_counter() - started) * 1000, 1)
        supplemental = plan["targeted_queries"][1] if len(plan["targeted_queries"]) > 1 else plan["targeted_queries"][0]
        started = time.perf_counter()
        candidate, candidate_path = await _run_one(supplemental, "candidate")
        candidate_elapsed = round((time.perf_counter() - started) * 1000, 1)
        control_metrics = _metrics(control)
        candidate_metrics = _metrics(candidate)
        records.append({
            "task": question,
            "case_id": case_id,
            "mode": "control_vs_quality_candidate",
            "evidence_categories": plan["required_categories"],
            "queries_generated": plan["targeted_queries"],
            "queries_executed": {"control": [question], "candidate": [supplemental]},
            "control": {"artifact_path": control_path, **control_metrics, "elapsed_ms": control_elapsed},
            "candidate": {"artifact_path": candidate_path, **candidate_metrics, "elapsed_ms": candidate_elapsed},
            "decision_change": decision_changed(control_metrics, candidate_metrics),
            "claim_status_changed": control_metrics["claim_status"] != candidate_metrics["claim_status"],
            "delta": {
                "useful_sources": candidate_metrics["useful_sources"] - control_metrics["useful_sources"],
                "authority_sources": candidate_metrics["authority_sources"] - control_metrics["authority_sources"],
                "opened_sources": candidate_metrics["sources_opened"] - control_metrics["sources_opened"],
                "runtime_ms": candidate_elapsed - control_elapsed,
            },
            "review_required": True,
        })
    return {"schema": "research-quality-execution-evaluation.v1", "caller": "search-research:/all", "case_count": len(records), "records": records, "authorization": "evaluation_only"}


if __name__ == "__main__":
    print(json.dumps(asyncio.run(evaluate()), indent=2))
