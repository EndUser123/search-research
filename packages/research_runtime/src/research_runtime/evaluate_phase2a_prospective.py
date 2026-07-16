"""Prospective provider-equivalent Phase 2A baseline/candidate evaluation."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from .assessment import EvidenceAssessment
from .brave_lane import execute_brave_search, observe_brave
from .evaluate_phase1 import _qmd_lane
from .evaluate_phase1e import _load_brave_key
from .evaluate_phase2a import _admission, _authority, _now, _run_falsifier
from .immutable_evaluation import ImmutableRunStore, LOST_HISTORICAL_ARTIFACT, _git_head, _source_hashes, build_comparison, canonical_json, sha256_bytes, sha256_file
from .mmx_state import observe_mmx
from .phase1 import LaneExecution, _source_id, execute_mmx_search, execute_parallel, open_source
from .phase2a import build_bounded_query, validate_phase2a_record
from .router import TaskSignals


ROOT = Path(__file__).parents[4]
CORPUS = ROOT / "tests" / "research_run_v1" / "phase2a_prospective_corpus.json"
MMX = r"C:\Users\brsth\AppData\Roaming\npm\mmx.cmd"


def _cases() -> list[dict[str, Any]]:
    return json.loads(CORPUS.read_text(encoding="utf-8"))


def _trigger(case: dict[str, Any]) -> dict[str, Any]:
    eligible = case["impact"] in {"medium", "high"} and case["reversibility"] in {"low", "medium"} and case["omission_sensitivity"] in {"medium", "high"}
    actual = eligible
    return {"expected": bool(case["trigger_expected"]), "produced": actual, "reason": "consequential decision with material omission risk" if actual else "low-impact reversible lookup or no trigger condition", "false_positive": actual and not case["trigger_expected"], "false_negative": bool(case["trigger_expected"]) and not actual, "depth": case.get("expected_depth", "light")}


def _serialize_result(item: Any) -> dict[str, Any]:
    return {"provider": item.provider, "lane_role": item.lane_role, "query": item.query, "result_id": item.result_id, "title": item.title, "url_or_source_ref": item.url_or_source_ref, "snippet": item.snippet, "published_at": item.published_at, "retrieved_at": item.retrieved_at, "result_type": item.result_type, "source_identity": item.source_identity, "provider_provenance": item.provider_provenance, "failure": item.failure}


def _affirmative(case: dict[str, Any], provider_state: dict[str, Any], brave_key: str | None, evidence_root: Path) -> dict[str, Any]:
    started = _now()
    qmd_start = __import__("time").perf_counter()
    qmd = _qmd_lane(case["affirmative_question"])
    qmd_ms = round((__import__("time").perf_counter() - qmd_start) * 1000, 1)
    signals = TaskSignals(needs_current_web=True, needs_independent_recall=True, as_of=_now())
    if case["affirmative_provider"] == "mmx":
        lane = execute_mmx_search(case["affirmative_question"], signals, provider_state, timeout_seconds=30)
    else:
        lane = execute_brave_search(case["affirmative_question"], provider_state, api_key=brave_key, timeout_seconds=15, max_results=5, role="IMPLEMENTATION_DISCOVERY")
    opened: list[dict[str, Any]] = []
    assessments: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = list(lane.failures)
    for result in lane.results[:2]:
        item = open_source(result, evidence_root / case["id"], timeout_seconds=10)
        if item.status == "failed":
            failures.append({"provider": result.provider, "source_id": _source_id(result.url_or_source_ref), "failure": item.failure})
            continue
        opened.append({"source_id": _source_id(result.url_or_source_ref), "provider": result.provider, "title": result.title, "url": result.url_or_source_ref, "body_path": item.body_path, "opened_at": item.opened_at, "retrieval_method": item.retrieval_method, "discovery_status": item.status})
        assessments.append({"claim_id": case["id"], "source_id": _source_id(result.url_or_source_ref), "source_location": result.url_or_source_ref, "relationship": "contextual_only", "authority": _authority(result.url_or_source_ref), "currency": "unknown", "assessment_method": "reference_case_criteria", "run_id": "prospective-baseline", "source_status": item.status, "limitations": [case["reference_criteria"]]})
    action = "continue_targeted_use" if opened else "require_more_evidence"
    record = {
        "case_id": case["id"], "claim_id": case["id"], "question": case["question"], "claim": case["claim"], "affirmative_query": lane.query, "affirmative_provider": case["affirmative_provider"], "providers_used": [lane.provider, "qmd"], "qmd_context": {"status": qmd.status, "candidate_count": len(qmd.results), "elapsed_ms": qmd_ms, "failures": list(qmd.failures)}, "normalized_results": [_serialize_result(item) for item in lane.results], "opened_sources": opened, "assessments": assessments, "source_failures": failures, "claim_status": "supported" if opened else "unverified", "final_action": action, "reconciliation": {"claim_id": case["id"], "original_action": action, "revised_action": action, "outcome": "survived" if opened else "required_more_evidence", "changed": False, "basis_falsifier_ids": [], "noisy_falsifier_ids": [], "false_contradiction_count": 0, "additional_evidence_required": not bool(opened), "limitation": case["reference_criteria"]}, "trigger": _trigger(case), "falsifiers": [], "timing": {"started_at": started, "finished_at": _now(), "elapsed_ms": round((__import__("time").perf_counter() - qmd_start) * 1000, 1)}, "reference_criteria": case["reference_criteria"]
    }
    return record


def _candidate_case(case: dict[str, Any], baseline_record: dict[str, Any], baseline_index: dict[tuple[str, str], dict[str, Any]], baseline_id: str, baseline_manifest_hash: str, mmx: Any, brave: Any, brave_key: str | None, evidence_root: Path) -> dict[str, Any]:
    trigger = _trigger(case)
    affirmative_ref = {"baseline_run_id": baseline_id, "baseline_manifest_sha256": baseline_manifest_hash, "baseline_case_sha256": sha256_bytes(canonical_json(baseline_record))}
    if not trigger["produced"]:
        return {**baseline_record, "run_variant": "candidate", "affirmative_reuse": {"baseline_case_id": case["id"], **affirmative_ref}, "disconfirmation": {"executed": False, "stop_reason": "trigger_not_produced"}, "trigger": trigger}
    from .evaluate_phase2a import _measure_case
    result = _measure_case(case, baseline_index, mmx, brave, brave_key, evidence_root)
    validate_phase2a_record(result)
    result["run_variant"] = "candidate"
    result["affirmative_reuse"] = {"baseline_case_id": case["id"], **affirmative_ref}
    result["trigger"] = trigger
    result["disconfirmation"] = {"executed": True, "stop_reason": "bounded_depth_reached_or_provider_results_exhausted", "depth": case["expected_depth"]}
    return result


def evaluate() -> dict[str, Any]:
    cases = _cases()
    if not 8 <= len(cases) <= 12:
        raise ValueError("prospective_case_count_out_of_bounds")
    key = _load_brave_key()
    # A unique evaluation namespace prevents collisions across terminals while
    # keeping the two paired run IDs deterministic within this evaluation.
    namespace = ImmutableRunStore(f"phase2a-prospective-evaluation-20260714-{__import__('uuid').uuid4().hex[:12]}")
    baseline_id = f"phase2a-prospective-baseline-20260714-{namespace.run_id.rsplit('-', 1)[-1]}"
    candidate_id = f"phase2a-prospective-candidate-20260714-{namespace.run_id.rsplit('-', 1)[-1]}"
    baseline_store = ImmutableRunStore(baseline_id, root=namespace.root / namespace.run_id)
    candidate_store = ImmutableRunStore(candidate_id, root=namespace.root / namespace.run_id)
    mmx_baseline = observe_mmx(MMX)
    brave_baseline = observe_brave(api_key=key)
    baseline_records = [_affirmative(case, mmx_baseline if case["affirmative_provider"] == "mmx" else brave_baseline, key, baseline_store.run_dir / "evidence") for case in cases]
    baseline_index = {(case["id"], case["baseline_mode"]): {"action": "usable_evidence" if record["claim_status"] == "supported" else "insufficient_evidence", "unique_useful_sources": len(record["opened_sources"]), "unique_authoritative_sources": sum(item["authority"] == "primary" for item in record["assessments"])} for case, record in zip(cases, baseline_records)}
    baseline_payload = {"schema": "research-run-v1.immutable-run", "run_id": baseline_id, "run_variant": "baseline", "evaluation_namespace": namespace.run_id, "providers": {"mmx": {"readiness": mmx_baseline.readiness, "executable_path": mmx_baseline.executable_path, "version": mmx_baseline.executable_version}, "brave": {"readiness": brave_baseline.readiness}, "qmd": {"role": "local_context_only", "calls": len(cases)}, "call_counts": {"mmx": sum(case["affirmative_provider"] == "mmx" for case in cases), "brave": sum(case["affirmative_provider"] == "brave" for case in cases)}}, "cases": baseline_records, "provenance": {"git_head": _git_head(), "corpus_sha256": sha256_file(CORPUS), "policy_sha256": sha256_file(ROOT / "tools" / "research_run_v1" / "phase2a.py"), "source_hashes": _source_hashes(), "historical_phase2a_artifact_reconstructable": False, "historical_phase2a_artifact_note": LOST_HISTORICAL_ARTIFACT, "baseline_contains_disconfirmation": False}}
    _, baseline_hash = baseline_store.manifest(run_metadata=baseline_payload)
    mmx_candidate = observe_mmx(MMX)
    brave_candidate = observe_brave(api_key=key)
    candidate_records = [_candidate_case(case, record, baseline_index, baseline_id, baseline_hash, mmx_candidate, brave_candidate, key, candidate_store.run_dir / "evidence") for case, record in zip(cases, baseline_records)]
    candidate_calls = [f for record in candidate_records if record.get("disconfirmation", {}).get("executed") for f in record.get("falsifiers", [])]
    candidate_payload = {"schema": "research-run-v1.immutable-run", "run_id": candidate_id, "run_variant": "candidate", "evaluation_namespace": namespace.run_id, "providers": {"mmx": {"readiness": mmx_candidate.readiness, "executable_path": mmx_candidate.executable_path, "version": mmx_candidate.executable_version}, "brave": {"readiness": brave_candidate.readiness}, "qmd": {"role": "local_context_only", "calls": sum(1 for record in candidate_records if record.get("disconfirmation", {}).get("executed"))}, "call_counts": {"mmx": sum(item["provider"] == "mmx" for item in candidate_calls), "brave": sum(item["provider"] == "brave" for item in candidate_calls)}}, "cases": candidate_records, "provenance": {"git_head": _git_head(), "corpus_sha256": sha256_file(CORPUS), "policy_sha256": sha256_file(ROOT / "tools" / "research_run_v1" / "phase2a.py"), "source_hashes": _source_hashes(), "historical_phase2a_artifact_reconstructable": False, "historical_phase2a_artifact_note": LOST_HISTORICAL_ARTIFACT, "affirmative_reused_from_baseline": True, "baseline_run_id": baseline_id}}
    _, candidate_hash = candidate_store.manifest(run_metadata=candidate_payload)
    comparison = build_comparison(baseline=baseline_payload, candidate=candidate_payload, baseline_manifest_hash=baseline_hash, candidate_manifest_hash=candidate_hash)
    comparison["evaluation_namespace"] = namespace.run_id
    comparison["trigger_summary"] = {"expected": sum(case["trigger_expected"] for case in cases), "produced": sum(_trigger(case)["produced"] for case in cases), "false_positives": sum(_trigger(case)["false_positive"] for case in cases), "false_negatives": sum(_trigger(case)["false_negative"] for case in cases)}
    comparison_path = namespace.write_json("comparison.json", comparison)
    return {"evaluation_namespace": namespace.run_id, "baseline": baseline_payload, "candidate": candidate_payload, "baseline_manifest_sha256": baseline_hash, "candidate_manifest_sha256": candidate_hash, "comparison": comparison, "comparison_path": str(comparison_path)}


if __name__ == "__main__":
    result = evaluate()
    print(json.dumps({"evaluation_namespace": result["evaluation_namespace"], "baseline_run_id": result["baseline"]["run_id"], "candidate_run_id": result["candidate"]["run_id"], "baseline_manifest_sha256": result["baseline_manifest_sha256"], "candidate_manifest_sha256": result["candidate_manifest_sha256"], "comparison_path": result["comparison_path"], "trigger_summary": result["comparison"]["trigger_summary"]}, indent=2))
