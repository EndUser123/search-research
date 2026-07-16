"""Bounded Phase 2A affirmative-versus-disconfirmation evaluation.

Affirmative-only results are the completed Phase 1E records. The experiment
adds two specific falsifier searches per case, one through MMX and one through
Brave, while QMD supplies local prior-context evidence. No model generates or
assesses claims; evaluator-supplied terms are required for every falsifier.
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .assessment import EvidenceAssessment, assess_claim
from .brave_lane import execute_brave_search, observe_brave
from .evaluate_phase1 import _qmd_lane
from .evaluate_phase1e import _load_brave_key
from .mmx_state import observe_mmx
from .phase1 import LaneExecution, _iso, _source_id, execute_mmx_search, execute_parallel, open_source
from .phase2a import admit_falsifier, build_bounded_query, validate_phase2a_record
from .router import TaskSignals


ROOT = Path(__file__).parents[4]
CORPUS = ROOT / "tests" / "research_run_v1" / "phase2a_corpus.json"
AFFIRMATIVE = ROOT / "tmp" / ".codex" / "state" / "phase1e-evaluation-20260713" / "phase1e-evaluation.json"
MMX = r"C:\Users\brsth\AppData\Roaming\npm\mmx.cmd"
RUN_ID = "phase2a-20260713"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _host(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower()


def _authority(url: str) -> str:
    host = _host(url)
    return "primary" if host == "github.com" or host.endswith(".github.com") or host.endswith("python.org") or host.endswith("microsoft.com") else "secondary"


def _terms(text: str, values: list[str]) -> int:
    lowered = text.lower()
    return sum(1 for value in values if value.lower() in lowered)


def _baseline_index() -> dict[tuple[str, str], dict[str, Any]]:
    artifact = json.loads(AFFIRMATIVE.read_text(encoding="utf-8"))
    return {(item["question_id"], item["mode"]): item for item in artifact["records"]}


def _run_falsifier(falsifier: dict[str, Any], mmx_observation, brave_observation, brave_key: str | None) -> LaneExecution:
    query = build_bounded_query(falsifier)
    signals = TaskSignals(needs_current_web=True, needs_independent_recall=True, as_of=_now())
    if falsifier["provider"] == "mmx":
        return execute_mmx_search(query, signals, mmx_observation, timeout_seconds=30)
    return execute_brave_search(query, brave_observation, api_key=brave_key, timeout_seconds=15, max_results=5, role="IMPLEMENTATION_DISCOVERY")


def _admission(case: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    admitted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    prior: list[dict[str, Any]] = []
    for item in case["falsifiers"]:
        normalized = {**item, "claim_id": item.get("claim_id", case["id"])}
        ok, reasons = admit_falsifier(normalized, claim_id=case["id"], prior=tuple(prior))
        record = {**normalized, "admitted": ok, "rejection_reasons": list(reasons)}
        (admitted if ok else rejected).append(record)
        if ok:
            prior.append(normalized)
    return admitted, rejected


def _assess_falsifier(case: dict[str, Any], falsifier: dict[str, Any], lane: LaneExecution, root: Path) -> dict[str, Any]:
    opened: list[dict[str, Any]] = []
    source_failures: list[dict[str, Any]] = []
    source_results = list(lane.results[:2])
    for result in source_results:
        source_start = time.perf_counter()
        opened_item = open_source(result, root / case["id"] / falsifier["falsifier_id"], timeout_seconds=10)
        if opened_item.status == "failed":
            source_failures.append({"source_id": _source_id(result.url_or_source_ref), "provider": result.provider, "failure": opened_item.failure, "opened_at": opened_item.opened_at, "retrieval_method": opened_item.retrieval_method})
            continue
        body = ""
        if opened_item.body_path:
            try:
                body = Path(opened_item.body_path).read_text(encoding="utf-8", errors="replace")
            except OSError:
                body = ""
        text = f"{result.title} {result.snippet} {body}"
        evidence_hits = _terms(text, falsifier["evidence_terms"])
        anchor_hits = _terms(text, falsifier["anchor_terms"])
        contradiction_hits = _terms(text, falsifier["contradiction_terms"])
        direct_contradiction = anchor_hits >= 1 and evidence_hits >= 2 and contradiction_hits >= 1
        false_contradiction = contradiction_hits >= 1 and not direct_contradiction
        relationship = "contradicts" if direct_contradiction else "contextual_only" if anchor_hits >= 1 and evidence_hits >= 2 else "insufficient"
        source_id = _source_id(result.url_or_source_ref)
        assessment = EvidenceAssessment(
            claim_id=case["id"], source_id=source_id, source_identity=result.source_identity,
            source_location=result.url_or_source_ref, passage_or_anchor=(body[:240] or result.snippet or result.title),
            relationship=relationship, authority=_authority(result.url_or_source_ref), currency="unknown",
            assessment_method="reference_evaluator", assessment_basis="Evaluator-supplied falsifier terms matched against opened source text.",
            assessed_at=_now(), limitations=("Keyword match is bounded evidence, not general truth assessment.",), run_id=RUN_ID, source_status=opened_item.status,
        )
        opened.append({
            "source_id": source_id, "provider": result.provider, "title": result.title, "url": result.url_or_source_ref,
            "discovery_status": opened_item.status, "body_path": opened_item.body_path, "opened_at": opened_item.opened_at, "retrieval_method": opened_item.retrieval_method, "anchor_hits": anchor_hits, "evidence_hits": evidence_hits, "contradiction_hits": contradiction_hits,
            "direct_contradiction": direct_contradiction, "false_contradiction": false_contradiction,
            "assessment": {"relationship": assessment.relationship, "authority": assessment.authority, "currency": assessment.currency, "assessment_method": assessment.assessment_method, "source_location": assessment.source_location, "passage_or_anchor": assessment.passage_or_anchor},
        })
    if lane.failures:
        source_failures.extend({"provider": lane.provider, "failure": item} for item in lane.failures)
    direct = any(item["direct_contradiction"] for item in opened)
    false_count = sum(1 for item in opened if item["false_contradiction"])
    outcome = "tested" if direct or opened else "no_evidence" if not source_failures else "source_open_failed"
    if false_count and not direct:
        outcome = "noisy"
    return {
        "falsifier_id": falsifier["falsifier_id"], "claim_id": case["id"], "provider": falsifier["provider"], "query": lane.query, "requested_query": falsifier["query"], "statement": falsifier["statement"],
        "decision_relevance": falsifier["decision_relevance"], "applicable": True, "specificity": "decision_specific", "generic": False,
        "evidence_terms": falsifier["evidence_terms"], "anchor_terms": falsifier["anchor_terms"], "contradiction_terms": falsifier["contradiction_terms"], "effect": falsifier["effect"],
        "lane_status": lane.status, "lane_started_at": lane.started_at, "lane_finished_at": lane.finished_at, "normalized_results": [{"provider": item.provider, "lane_role": item.lane_role, "query": item.query, "result_id": item.result_id, "title": item.title, "url_or_source_ref": item.url_or_source_ref, "snippet": item.snippet, "published_at": item.published_at, "retrieved_at": item.retrieved_at, "result_type": item.result_type, "source_identity": item.source_identity, "provider_provenance": item.provider_provenance, "failure": item.failure} for item in lane.results], "lane_failures": list(lane.failures), "opened_sources": opened, "source_open_failures": source_failures, "outcome": outcome,
        "source_open_count": len(opened), "false_contradiction_count": false_count,
    }


def _action_for(outcome: str, original: str) -> str:
    return {
        "survived": original, "narrowed_scope": "narrow_scope_to_supported_case", "reduced_confidence": "continue_only_with_primary_verification",
        "added_tests_or_guardrails": "continue_with_explicit_guardrail", "reduced_authorization": "do_not_authorize_broader_use",
        "required_more_evidence": "gather_more_evidence", "rejected_conclusion": "reject_conclusion",
    }[outcome]


def _reconcile(case: dict[str, Any], baseline: dict[str, Any], falsifiers: list[dict[str, Any]], claim_status: str) -> dict[str, Any]:
    direct = [item for item in falsifiers if any(source["direct_contradiction"] for source in item["opened_sources"])]
    noisy = [item for item in falsifiers if item["outcome"] == "noisy"]
    tested = [item for item in falsifiers if item["outcome"] == "tested"]
    if direct:
        effects = [item["effect"] for item in direct]
        outcome = "reduced_confidence"
        for candidate in ("rejected_conclusion", "reduced_authorization", "narrowed_scope", "added_tests_or_guardrails", "reduced_confidence"):
            if candidate in effects:
                outcome = candidate
                break
    elif not tested:
        outcome = "required_more_evidence"
    else:
        outcome = "survived"
    original_action = "continue_targeted_use" if baseline["action"] == "usable_evidence" else "require_more_evidence"
    revised_action = _action_for(outcome, original_action)
    return {
        "claim_id": case["id"], "original_action": original_action, "revised_action": revised_action, "outcome": outcome,
        "changed": revised_action != original_action, "claim_status_before": "supported" if baseline["action"] == "usable_evidence" else "unverified",
        "claim_status_after": "contradicted" if claim_status == "contradicted" else "supported" if tested else "unverified",
        "basis_falsifier_ids": [item["falsifier_id"] for item in direct], "noisy_falsifier_ids": [item["falsifier_id"] for item in noisy],
        "false_contradiction_count": sum(item["false_contradiction_count"] for item in falsifiers), "additional_evidence_required": outcome == "required_more_evidence",
        "limitation": "Two bounded falsifier queries and up to two opened sources per falsifier; absence of contradiction is not proof of truth.",
    }


def _measure_case(case: dict[str, Any], baseline_index: dict[tuple[str, str], dict[str, Any]], mmx_observation, brave_observation, brave_key: str | None, root: Path) -> dict[str, Any]:
    total_start = time.perf_counter()
    baseline = baseline_index[(case["id"], case["baseline_mode"])]
    qmd_start = time.perf_counter()
    qmd = _qmd_lane(case["affirmative_question"])
    qmd_ms = round((time.perf_counter() - qmd_start) * 1000, 1)
    admitted, rejected = _admission(case)
    disconfirm_start = time.perf_counter()
    def run_bound_falsifier(item: dict[str, Any]) -> LaneExecution:
        lane = _run_falsifier(item, mmx_observation, brave_observation, brave_key)
        return replace(lane, lane_id=item["falsifier_id"])

    falsifier_lanes = execute_parallel(tuple((item["falsifier_id"], lambda item=item: run_bound_falsifier(item)) for item in admitted))
    disconfirm_ms = round((time.perf_counter() - disconfirm_start) * 1000, 1)
    lane_by_id = {lane.lane_id: lane for lane in falsifier_lanes}
    source_start = time.perf_counter()
    falsifier_results = [_assess_falsifier(case, item, lane_by_id[item["falsifier_id"]], root) for item in admitted]
    source_open_ms = round((time.perf_counter() - source_start) * 1000, 1)
    assessments: list[EvidenceAssessment] = []
    for item in falsifier_results:
        for source in item["opened_sources"]:
            assessments.append(EvidenceAssessment(
                claim_id=case["id"], source_id=source["source_id"], source_identity=source["url"].rstrip("/").lower(), source_location=source["url"],
                passage_or_anchor=source["assessment"]["passage_or_anchor"], relationship=source["assessment"]["relationship"], authority=source["assessment"]["authority"], currency="unknown",
                assessment_method="reference_evaluator", assessment_basis="Phase 2A falsifier evidence rule", assessed_at=_now(), limitations=("Bounded keyword assessment.",), run_id=RUN_ID, source_status=source["discovery_status"],
            ))
    assessment_start = time.perf_counter()
    claim_assessment = assess_claim(case["id"], assessments, expected_run_id=RUN_ID)
    reconciliation = _reconcile(case, baseline, falsifier_results, claim_assessment.status)
    assessment_ms = round((time.perf_counter() - assessment_start) * 1000, 1)
    result = {
        "case_id": case["id"], "claim_id": case["id"], "claim": case["claim"], "affirmative_action": "continue_targeted_use" if baseline["action"] == "usable_evidence" else "require_more_evidence", "affirmative_only": {"mode": case["baseline_mode"], "action": baseline["action"], "useful_sources": baseline["unique_useful_sources"], "authoritative_sources": baseline["unique_authoritative_sources"]},
        "qmd_context": {"status": qmd.status, "candidate_count": len(qmd.results), "lane_failures": list(qmd.failures), "elapsed_ms": qmd_ms},
        "disconfirmation_action": "bounded_falsifier_search", "falsifiers": falsifier_results, "rejected_falsifiers": rejected,
        "assessments": [{"claim_id": item.claim_id, "source_id": item.source_id, "source_location": item.source_location, "passage_or_anchor": item.passage_or_anchor, "relationship": item.relationship, "authority": item.authority, "currency": item.currency, "assessment_method": item.assessment_method, "run_id": item.run_id, "source_status": item.source_status} for item in assessments],
        "claim_assessment": {"status": claim_assessment.status, "supporting_source_ids": list(claim_assessment.supporting_source_ids), "contradicting_source_ids": list(claim_assessment.contradicting_source_ids), "rationale": list(claim_assessment.rationale)},
        "reconciliation": reconciliation,
        "metrics": {"disconfirmation_search_wall_time_ms": disconfirm_ms, "qmd_context_time_ms": qmd_ms, "additional_source_open_time_ms": source_open_ms, "assessment_time_ms": assessment_ms, "additional_source_open_count": sum(item["source_open_count"] for item in falsifier_results), "source_open_failures": sum(len(item["source_open_failures"]) for item in falsifier_results), "lane_failures": sum(1 for item in falsifier_results if item["lane_status"] == "failed"), "noisy_falsifiers": len([item for item in falsifier_results if item["outcome"] == "noisy"]), "false_contradictions": sum(item["false_contradiction_count"] for item in falsifier_results), "admitted_falsifier_count": len(admitted), "rejected_falsifier_count": len(rejected), "total_run_time_ms": round((time.perf_counter() - total_start) * 1000, 1)},
    }
    validate_phase2a_record(result)
    return result


def evaluate() -> dict[str, Any]:
    cases = json.loads(CORPUS.read_text(encoding="utf-8"))
    baseline_index = _baseline_index()
    before = observe_mmx(MMX)
    brave_key = _load_brave_key()
    brave = observe_brave(api_key=brave_key)
    root = ROOT / "tmp" / ".codex" / "state" / "phase2a-evaluation-20260713"
    root.mkdir(parents=True, exist_ok=True)
    records = [_measure_case(case, baseline_index, before, brave, brave_key, root) for case in cases]
    after = observe_mmx(MMX)
    artifact = {
        "schema": "research-run-v1.phase2a-evaluation", "run_id": RUN_ID, "observed_at": _now(), "case_count": len(records), "cases": records,
        "providers": {"mmx": {"readiness_before": before.readiness, "readiness_after": after.readiness, "quota_before": before.quota, "quota_after": after.quota, "quota_scope": before.quota_scope, "concurrent_consumers_possible": True, "quota_delta_attributable_to_current_run": False, "quota_delta_interpretation": "indeterminate_concurrent_usage", "known_top_level_falsifier_calls": sum(1 for case in records for item in case["falsifiers"] if item["provider"] == "mmx")}, "brave": {"readiness": brave.readiness, "known_top_level_falsifier_calls": sum(1 for case in records for item in case["falsifiers"] if item["provider"] == "brave")}, "qmd": {"role": "local_context_only", "known_calls": len(cases)}},
    }
    artifact["aggregate"] = {"survived": sum(item["reconciliation"]["outcome"] == "survived" for item in records), "changed": sum(item["reconciliation"]["changed"] for item in records), "rejected_conclusions": sum(item["reconciliation"]["outcome"] == "rejected_conclusion" for item in records), "narrowed_scope": sum(item["reconciliation"]["outcome"] == "narrowed_scope" for item in records), "reduced_confidence": sum(item["reconciliation"]["outcome"] == "reduced_confidence" for item in records), "added_guardrails": sum(item["reconciliation"]["outcome"] == "added_tests_or_guardrails" for item in records), "reduced_authorization": sum(item["reconciliation"]["outcome"] == "reduced_authorization" for item in records), "required_more_evidence": sum(item["reconciliation"]["outcome"] == "required_more_evidence" for item in records), "noisy_falsifiers": sum(item["metrics"]["noisy_falsifiers"] for item in records), "false_contradictions": sum(item["metrics"]["false_contradictions"] for item in records), "additional_source_open_count": sum(item["metrics"]["additional_source_open_count"] for item in records), "additional_source_open_failures": sum(item["metrics"]["source_open_failures"] for item in records), "additional_source_open_time_ms": round(sum(item["metrics"]["additional_source_open_time_ms"] for item in records), 1), "disconfirmation_search_time_ms": round(sum(item["metrics"]["disconfirmation_search_wall_time_ms"] for item in records), 1), "total_time_ms": round(sum(item["metrics"]["total_run_time_ms"] for item in records), 1)}
    out = root / "phase2a-evaluation.json"
    out.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
    return artifact


if __name__ == "__main__":
    result = evaluate()
    print(json.dumps({"artifact": "P:/tmp/.codex/state/phase2a-evaluation-20260713/phase2a-evaluation.json", "aggregate": result["aggregate"], "mmx": result["providers"]["mmx"]}, indent=2))
