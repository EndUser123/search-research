"""Small Phase 1 execution slice for one bounded MMX research run.

The router remains pure. This module owns only the integration boundary for a
run: state acquisition, one bounded MMX search, normalization, explicit source
opening, and exclusive research-run.v1 emission.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from .mmx_state import MMXObservation, observe_mmx
from .router import TaskSignals, recommend
from .router import CapabilityRecord
from .quality import analyze_artifact
from .validator import write_run

MAX_SOURCE_BYTES = 2_000_000

def _iso(value: datetime | None = None) -> str:
    return (value or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _source_id(url: str, provider: str | None = None) -> str:
    """Return a stable source identity that remains unique across lanes."""

    identity = f"{provider or 'unknown'}\0{url}"
    return "src-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]


def _canonical_url(url: str) -> str:
    return url.strip().rstrip("/").lower()


@dataclass(frozen=True)
class NormalizedResult:
    provider: str
    lane_role: str
    query: str
    result_id: str
    title: str
    url_or_source_ref: str
    snippet: str
    published_at: str | None
    retrieved_at: str
    result_type: str = "discovery_candidate"
    source_identity: str | None = None
    provider_provenance: dict[str, Any] | None = None
    failure: str | None = None


@dataclass(frozen=True)
class OpenedSource:
    result: NormalizedResult
    status: str
    opened_at: str
    retrieval_method: str
    body_path: str | None = None
    verification_note: str | None = None
    failure: str | None = None


@dataclass(frozen=True)
class LaneExecution:
    lane_id: str
    provider: str
    role: str
    query: str
    status: str
    started_at: str
    finished_at: str
    results: tuple[NormalizedResult, ...] = ()
    failures: tuple[dict[str, Any], ...] = ()


def _mmx_command(path: str, query: str) -> tuple[str, ...]:
    return (path, "search", "query", "--q", query, "--output", "json", "--quiet")


def _run_command(command: Sequence[str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout_seconds, check=False, shell=False)


def normalize_mmx_results(query: str, payload: dict[str, Any], retrieved_at: str | None = None) -> tuple[NormalizedResult, ...]:
    """Convert only MMX's documented organic result fields into candidates."""

    retrieved = retrieved_at or _iso()
    organic = payload.get("organic")
    if not isinstance(organic, list):
        raise ValueError("mmx_result_shape_missing_organic")
    results: list[NormalizedResult] = []
    seen: set[str] = set()
    for index, item in enumerate(organic):
        if not isinstance(item, dict) or not isinstance(item.get("link"), str) or not item["link"].strip():
            continue
        url = item["link"].strip()
        identity = _canonical_url(url)
        if identity in seen:
            continue
        seen.add(identity)
        results.append(
            NormalizedResult(
                provider="mmx",
                lane_role="discovery",
                query=query,
                result_id=f"mmx-{index}-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:16]}",
                title=str(item.get("title") or "Untitled"),
                url_or_source_ref=url,
                snippet=str(item.get("snippet") or ""),
                published_at=str(item["date"]) if item.get("date") else None,
                retrieved_at=retrieved,
                source_identity=identity,
                provider_provenance={"cli": "mmx search query", "response_field": "organic", "result_index": index},
            )
        )
    return tuple(results)


def execute_mmx_search(
    query: str,
    signals: TaskSignals,
    observation: MMXObservation,
    *,
    timeout_seconds: int = 30,
    runner: Callable[[Sequence[str], int], subprocess.CompletedProcess[str]] = _run_command,
) -> LaneExecution:
    """Run MMX only after the pure router recommends it; never retry."""

    started = _iso()
    capability = observation.to_capability()
    decision = recommend(
        signals,
        (capability,),
    )
    if not decision.recommendations:
        return LaneExecution(
            "mmx", "mmx", "discovery", query, "not_attempted", started, _iso(),
            failures=({"outcome": "router_rejected", "reasons": list(decision.rejected[0].reasons) if decision.rejected else [decision.stop_reason]},),
        )
    if not observation.executable_path:
        return LaneExecution("mmx", "mmx", "discovery", query, "failed", started, _iso(), failures=({"outcome": "executable_missing"},))
    command = _mmx_command(observation.executable_path, query)
    try:
        completed = runner(command, timeout_seconds)
    except subprocess.TimeoutExpired:
        return LaneExecution("mmx", "mmx", "discovery", query, "failed", started, _iso(), failures=({"outcome": "timeout"},))
    except OSError as exc:
        return LaneExecution("mmx", "mmx", "discovery", query, "failed", started, _iso(), failures=({"outcome": f"execution_error:{type(exc).__name__}"},))
    if completed.returncode != 0:
        return LaneExecution("mmx", "mmx", "discovery", query, "failed", started, _iso(), failures=({"outcome": f"exit_code:{completed.returncode}"},))
    try:
        payload = json.loads(completed.stdout)
        results = normalize_mmx_results(query, payload)
    except (json.JSONDecodeError, ValueError) as exc:
        return LaneExecution("mmx", "mmx", "discovery", query, "failed", started, _iso(), failures=({"outcome": str(exc)},))
    status = "success" if results else "empty"
    return LaneExecution("mmx", "mmx", "discovery", query, status, started, _iso(), results=results)


def execute_parallel(lanes: Iterable[tuple[str, Callable[[], LaneExecution]]], max_workers: int = 2) -> tuple[LaneExecution, ...]:
    """Execute an explicit bounded wave and preserve each lane's failure."""

    entries = list(lanes)
    if not entries:
        return ()
    with ThreadPoolExecutor(max_workers=min(max_workers, len(entries))) as pool:
        futures = {pool.submit(callback): lane_id for lane_id, callback in entries}
        completed: list[LaneExecution] = []
        for future in as_completed(futures):
            lane_id = futures[future]
            try:
                completed.append(future.result())
            except Exception as exc:  # preserve lane failure; do not replace it
                now = _iso()
                completed.append(LaneExecution(lane_id, lane_id, "explicit", "", "failed", now, now, failures=({"outcome": f"worker_error:{type(exc).__name__}"},)))
    return tuple(sorted(completed, key=lambda item: item.lane_id))


def open_source(
    result: NormalizedResult,
    evidence_dir: Path,
    *,
    timeout_seconds: int = 20,
    opener: Callable[[str, int], tuple[int, str, bytes]] | None = None,
    verification_text: str | None = None,
) -> OpenedSource:
    """Open one explicit candidate and optionally confirm one supplied anchor."""

    opened_at = _iso()
    if not result.url_or_source_ref.startswith(("https://", "http://")):
        return OpenedSource(result, "failed", opened_at, "direct-http", failure="unsupported_url_scheme")
    try:
        if opener:
            status, content_type, body = opener(result.url_or_source_ref, timeout_seconds)
        else:
            request = urllib.request.Request(result.url_or_source_ref, headers={"User-Agent": "research-run-v1/phase1"})
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                status, content_type, body = response.status, response.headers.get("Content-Type", ""), response.read(MAX_SOURCE_BYTES)
        if status < 200 or status >= 400:
            return OpenedSource(result, "failed", opened_at, "direct-http", failure=f"http_status:{status}")
        evidence_dir.mkdir(parents=True, exist_ok=True)
        body_path = evidence_dir / f"{result.result_id}.source"
        body_path.write_bytes(body)
        if verification_text and verification_text.lower().encode("utf-8") in body.lower():
            return OpenedSource(result, "anchor_confirmed", opened_at, f"direct-http:{content_type or 'unknown'}", str(body_path), verification_text)
        return OpenedSource(result, "opened", opened_at, f"direct-http:{content_type or 'unknown'}", str(body_path))
    except (OSError, TimeoutError) as exc:
        return OpenedSource(result, "failed", opened_at, "direct-http", failure=f"open_error:{type(exc).__name__}")


def build_artifact(
    *,
    run_id: str,
    question: str,
    requested_decision: str,
    workspace_revision: str,
    lanes: Sequence[LaneExecution],
    opened: Sequence[OpenedSource],
    observation: MMXObservation,
    output_path: Path,
    caller: str = "manual",
    assess_authority_candidates: bool = False,
) -> dict[str, Any]:
    source_entries: list[dict[str, Any]] = []
    for result in [item for lane in lanes for item in lane.results]:
        opened_item = next((item for item in opened if item.result.result_id == result.result_id), None)
        status = opened_item.status if opened_item and opened_item.status != "failed" else "discovery_only"
        source: dict[str, Any] = {
            "source_id": _source_id(result.url_or_source_ref, result.provider),
            "lane_id": next(lane.lane_id for lane in lanes if result in lane.results),
            "provider": result.provider,
            "title": result.title,
            "url": result.url_or_source_ref,
            "snippet": result.snippet,
            "source_type": "primary" if "python.org" in result.url_or_source_ref or "github.com" in result.url_or_source_ref else "discovered-web",
            "discovery_status": status,
            "retrieved_at": result.retrieved_at,
            "retrieval_method": "mmx search query" if result.provider == "mmx" else f"{result.provider} bounded discovery request",
        }
        if result.provider_provenance:
            source["provider_provenance"] = result.provider_provenance
        if result.published_at:
            source["publication_date"] = result.published_at
        if opened_item and status in {"opened", "anchor_confirmed", "verified"}:
            source.update({"opened_at": opened_item.opened_at, "opened_by": opened_item.retrieval_method})
        if opened_item and status == "anchor_confirmed":
            source.update({"anchor_at": opened_item.opened_at, "anchor_text": opened_item.verification_note or "", "anchor_method": "case-insensitive byte substring match"})
        source_entries.append(source)
    claims: list[dict[str, Any]] = []
    assessments: list[dict[str, Any]] = []
    anchored_sources = [item for item in source_entries if item["discovery_status"] == "anchor_confirmed"]
    if anchored_sources:
        source = anchored_sources[0]
        claim_id = "anchor-confirmed-source"
        claims.append({"claim_id": claim_id, "text": "The selected primary source was opened and contained the supplied anchor text.", "status": "supported", "supporting_source_ids": [source["source_id"]], "contradicting_source_ids": [], "verification_method": "direct source opening with explicit anchor match", "falsifier": "The source no longer contains the inspected anchor text."})
        assessments.append({"claim_id": claim_id, "source_id": source["source_id"], "source_location": source["url"], "passage_or_anchor": source.get("anchor_text", ""), "relationship": "directly_supports", "authority": source["source_type"] if source["source_type"] in {"primary", "secondary", "runtime"} else "unknown", "currency": "unknown", "assessment_method": "deterministic_anchor_only", "assessment_basis": "The opened body contained the caller-supplied anchor; this does not assess the broader research claim.", "assessed_at": source["anchor_at"], "limitations": ["Anchor confirmation is not general verification."], "run_id": run_id})
    elif assess_authority_candidates:
        candidates = [item for item in source_entries if item["discovery_status"] in {"opened", "anchor_confirmed", "verified"}]
        if candidates:
            source = next((item for item in candidates if item["source_type"] == "primary"), candidates[0])
            claim_id = "authority-candidate-source"
            from .assessment import EvidenceAssessment, assess_claim
            assessment = EvidenceAssessment(
                claim_id=claim_id,
                source_id=source["source_id"],
                source_location=source["url"],
                passage_or_anchor=source["url"],
                relationship="contextual_only",
                authority=source["source_type"] if source["source_type"] in {"primary", "secondary", "runtime"} else "unknown",
                currency="unknown",
                assessment_method="caller_supplied",
                assessment_basis="The source was opened as an authority candidate; source identity does not establish support for the requested authority claim.",
                assessed_at=source.get("opened_at", _iso()),
                limitations=("Authority remains unverified until a claim-specific anchor or assessment is supplied.",),
                run_id=run_id,
                source_status=source["discovery_status"],
            )
            claim_assessment = assess_claim(claim_id, (assessment,), expected_run_id=run_id)
            claims.append({"claim_id": claim_id, "text": "The opened source is an authority candidate; authority has not been established.", "status": claim_assessment.status, "supporting_source_ids": list(claim_assessment.supporting_source_ids), "contradicting_source_ids": list(claim_assessment.contradicting_source_ids), "verification_method": "evidence assessment after source opening", "falsifier": "A claim-specific assessment establishes that the opened source is not authoritative for the requested question."})
            assessments.append({"claim_id": assessment.claim_id, "source_id": assessment.source_id, "source_location": assessment.source_location, "passage_or_anchor": assessment.passage_or_anchor, "relationship": assessment.relationship, "authority": assessment.authority, "currency": assessment.currency, "assessment_method": assessment.assessment_method, "assessment_basis": assessment.assessment_basis, "assessed_at": assessment.assessed_at, "limitations": list(assessment.limitations), "run_id": assessment.run_id})
    failures = [failure for lane in lanes for failure in lane.failures]
    stop_reason = "opened_anchor_confirmed_primary_source" if anchored_sources else "discovery_complete_without_anchor_confirmed_primary_source"
    if failures:
        stop_reason += "; failures_recorded"
    mmx_top_level_calls = sum(1 for lane in lanes if lane.provider == "mmx" and lane.status != "not_attempted")
    quota_telemetry = observation.quota_telemetry(current_run_top_level_calls=mmx_top_level_calls) if hasattr(observation, "quota_telemetry") else {
        "quota_scope": "unknown",
        "concurrent_consumers_possible": True,
        "quota_delta_attributable_to_current_run": False,
        "current_run_top_level_calls": mmx_top_level_calls,
        "shared_quota_before": None,
        "shared_quota_after": None,
        "quota_delta_interpretation": "indeterminate_concurrent_usage",
    }
    return {
        "schema": "research-run.v1",
        "schema_version": "research-run.v1",
        "run_id": run_id,
        "created_at": _iso(),
        "research_question": question,
        "requested_decision": requested_decision,
        "authorization_level_sought": "evidence_gathering",
        "workspace": {"root": "P:/", "revision": workspace_revision},
        "authority": {"producer": "research_run_v1.phase1", "acquisition": "router recommendation, bounded lane execution, explicit source opening", "serialization": "research-run.v1 JSON", "storage": str(output_path.parent), "consumer": "human or validating agent", "trust": "validator plus source inspection", "scope": f"run:{run_id}", "lifetime": "run-scoped immutable artifact", "collision": "exclusive create fails", "failure": "preserve failed or incomplete lane", "retention": "caller-managed run-scoped retention", "caller": caller},
        "caller": caller,
        "runtime": {"phase": "1", "provider_state": {"readiness": observation.readiness, "observed_at": observation.observed_at, "valid_until": observation.valid_until, "quota": observation.quota, "errors": list(observation.errors), "quota_telemetry": quota_telemetry}, "status": "success" if anchored_sources else "incomplete"},
        "retrieval_lanes": [{"lane_id": lane.lane_id, "provider": lane.provider, "independence_group": lane.provider, "query": lane.query, "status": lane.status, "started_at": lane.started_at, "finished_at": lane.finished_at, "sources": [_source_id(result.url_or_source_ref, result.provider) for result in lane.results], "failures": list(lane.failures)} for lane in lanes],
        "sources": source_entries,
        "claims": claims,
        "assessments": assessments,
        "uncertainty": ["MMX discovery results are candidates until opened."] if not anchored_sources else ["Anchor confirmation is not general source or claim verification."],
        "stop_reason": stop_reason,
        "authorization_supported": bool(anchored_sources),
    }


def run_mmx_phase1(
    question: str,
    query: str,
    requested_decision: str,
    *,
    workspace_revision: str,
    verification_text: str | None = None,
    observation: MMXObservation | None = None,
    output_root: Path = Path("P:/.artifacts/research/runs"),
) -> tuple[dict[str, Any], Path]:
    """Run one bounded MMX flow and write one exclusive run artifact."""

    run_id = str(uuid.uuid4())
    run_dir = output_root / run_id
    artifact_path = run_dir / "research-run.json"
    state = observation or observe_mmx()
    signals = TaskSignals(needs_current_web=True, needs_independent_recall=True, as_of=_iso())
    lane = execute_mmx_search(query, signals, state)
    opened: list[OpenedSource] = []
    if lane.results:
        candidates = sorted(lane.results, key=lambda item: (0 if "python.org" in item.url_or_source_ref else 1, item.result_id))
        opened.append(open_source(candidates[0], run_dir / "sources", verification_text=verification_text))
    artifact = build_artifact(run_id=run_id, question=question, requested_decision=requested_decision, workspace_revision=workspace_revision, lanes=(lane,), opened=tuple(opened), observation=state, output_path=artifact_path)
    artifact["quality"] = analyze_artifact(question, signals, artifact)
    write_run(artifact_path, artifact)
    return artifact, artifact_path


def _qmd_lane(query: str, *, qmd_path: str, wiki_root: Path, timeout_seconds: int = 30) -> LaneExecution:
    """Execute the existing local QMD lane without external fallback."""
    started = _iso()
    try:
        completed = _run_command((qmd_path, "query", query, "--collection", "wiki", "--limit", "5", "--format", "json"), timeout_seconds)
    except subprocess.TimeoutExpired:
        return LaneExecution("qmd", "qmd", "local_context", query, "failed", started, _iso(), failures=({"outcome": "timeout"},))
    except OSError as exc:
        return LaneExecution("qmd", "qmd", "local_context", query, "failed", started, _iso(), failures=({"outcome": f"execution_error:{type(exc).__name__}"},))
    if completed.returncode != 0:
        return LaneExecution("qmd", "qmd", "local_context", query, "failed", started, _iso(), failures=({"outcome": f"exit_code:{completed.returncode}"},))
    if completed.stdout.strip() == "No matching documents found":
        return LaneExecution("qmd", "qmd", "local_context", query, "empty", started, _iso())
    try:
        rows = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return LaneExecution("qmd", "qmd", "local_context", query, "failed", started, _iso(), failures=({"outcome": "malformed_json"},))
    results: list[NormalizedResult] = []
    for index, row in enumerate(rows if isinstance(rows, list) else []):
        if not isinstance(row, dict) or not isinstance(row.get("file"), str):
            continue
        relative = Path(row["file"])
        if relative.parts and relative.parts[0].lower() == "wiki":
            relative = Path(*relative.parts[1:])
        try:
            source_path = (wiki_root / relative).resolve()
            source_path.relative_to(wiki_root.resolve())
        except (OSError, ValueError):
            continue
        source_ref = f"qmd://wiki/{relative.as_posix()}"
        results.append(NormalizedResult("qmd", "local_context", query, f"qmd-{index}-{row.get('docid', index)}", str(row.get("title") or relative), source_ref, str(row.get("snippet") or ""), None, _iso(), source_identity=str(source_path)))
    return LaneExecution("qmd", "qmd", "local_context", query, "success" if results else "empty", started, _iso(), results=tuple(results))


def _open_qmd_source(result: NormalizedResult, evidence_dir: Path, wiki_root: Path) -> OpenedSource:
    opened_at = _iso()
    if result.provider != "qmd" or not result.source_identity:
        return OpenedSource(result, "failed", opened_at, "local-file", failure="invalid_qmd_source_identity")
    try:
        source_path = Path(result.source_identity).resolve()
        source_path.relative_to(wiki_root.resolve())
        body = source_path.read_bytes()[:MAX_SOURCE_BYTES]
        if not body:
            return OpenedSource(result, "failed", opened_at, "local-file", failure="empty_source")
        evidence_dir.mkdir(parents=True, exist_ok=True)
        body_path = evidence_dir / f"{result.result_id}.source"
        body_path.write_bytes(body)
        return OpenedSource(result, "opened", opened_at, "local-file", str(body_path))
    except (OSError, ValueError) as exc:
        return OpenedSource(result, "failed", opened_at, "local-file", failure=f"open_error:{type(exc).__name__}")


def run_phase1(
    question: str,
    query: str,
    requested_decision: str,
    *,
    workspace_revision: str,
    caller: str,
    signals: TaskSignals,
    output_root: Path = Path("P:/.artifacts/research/runs"),
    mmx_observation: MMXObservation | None = None,
    brave_observation: BraveObservation | None = None,
    qmd_path: str = r"C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\qmd.exe",
    wiki_root: Path = Path("P:/.data/wiki"),
    manual_disconfirmation_runner: Callable[[], dict[str, Any]] | None = None,
    caller_run_id: str | None = None,
) -> tuple[dict[str, Any], Path]:
    """Run one router-selected Phase 1 wave and emit its exact artifact path."""
    total_started = time.perf_counter()
    from .brave_lane import BraveObservation, execute_brave_search, observe_brave
    run_id = str(uuid.uuid4())
    run_dir = output_root / run_id
    artifact_path = run_dir / "research-run.json"
    mmx_state = mmx_observation
    if mmx_state is None and signals.needs_current_web:
        mmx_state = observe_mmx()
    if mmx_state is None:
        now = _iso()
        mmx_state = MMXObservation("mmx", now, now, None, None, "not_requested", "unknown", None, "not_requested", "unavailable", "phase1-not-requested")
    brave_state = brave_observation
    if brave_state is None and signals.needs_current_web:
        brave_state = observe_brave()
    if brave_state is None:
        now = _iso()
        brave_state = BraveObservation("brave", now, now, "not_requested", "unavailable", "phase1-not-requested")
    capabilities = [mmx_state.to_capability(), brave_state.to_capability()]
    external_observations: dict[str, Any] = {}
    external_providers: set[str] = set()
    if "SEMANTIC_EXTERNAL_DISCOVERY" in signals.requested_roles or signals.explicit_lane == "exa":
        external_providers.add("exa")
    if signals.explicit_lane == "duckduckgo" or signals.conditional_lane_trigger:
        external_providers.add("duckduckgo")
    if external_providers:
        from .external_lane import observe_external
        for provider in sorted(external_providers):
            external_observations[provider] = observe_external(provider)
            capabilities.append(external_observations[provider].to_capability())
    if signals.needs_local_context:
        capabilities.insert(0, CapabilityRecord("local", "LOCAL_INSPECTION", "local", frozenset({"local_context", "primary_source_verification", "deep_source_inspection", "extraction"}), ready=True, authenticated=True, automatic=True, authority="local", observation_method="phase1-local"))
    decision = recommend(signals, capabilities)
    def execute_selected(selected: Any) -> LaneExecution:
        if selected.lane == "mmx":
            return execute_mmx_search(query, signals, mmx_state)
        if selected.lane == "brave":
            brave_roles = signals.requested_roles & {
                "IMPLEMENTATION_DISCOVERY", "AUTHORITATIVE_SOURCE_DISCOVERY",
                "REPOSITORY_PROJECT_DISCOVERY", "MAINTENANCE_STATUS",
                "COMPATIBILITY_RESEARCH", "OMISSION_SENSITIVE_DISCOVERY",
            }
            role = sorted(brave_roles)[0] if brave_roles else "IMPLEMENTATION_DISCOVERY"
            return execute_brave_search(query, brave_state, role=role)
        if selected.lane == "local":
            return _qmd_lane(query, qmd_path=qmd_path, wiki_root=wiki_root)
        if selected.lane in {"exa", "duckduckgo"}:
            from .external_lane import execute_external_search
            return execute_external_search(query, external_observations[selected.lane])
        return LaneExecution(selected.lane, selected.lane, "unsupported", query, "not_attempted", _iso(), _iso(), failures=({"outcome": "unsupported_selected_lane"},))

    selections = tuple(decision.recommendations)
    if len(selections) > 1:
        lanes = list(execute_parallel(tuple((item.lane, lambda item=item: execute_selected(item)) for item in selections), max_workers=3))
    else:
        lanes = [execute_selected(selections[0])] if selections else []
    if not lanes:
        lanes = [LaneExecution("router", "router", "policy", query, "not_attempted", _iso(), _iso(), failures=({"outcome": decision.stop_reason},))]
    opened: list[OpenedSource] = []
    for lane in lanes:
        for result in lane.results[:2]:
            if result.provider == "qmd":
                opened.append(_open_qmd_source(result, run_dir / "sources" / lane.lane_id, wiki_root))
            else:
                opened.append(open_source(result, run_dir / "sources" / lane.lane_id, timeout_seconds=15))
    artifact = build_artifact(run_id=run_id, question=question, requested_decision=requested_decision, workspace_revision=workspace_revision, lanes=tuple(lanes), opened=tuple(opened), observation=mmx_state, output_path=artifact_path, caller=caller, assess_authority_candidates=signals.needs_primary_source_verification)
    artifact["quality"] = analyze_artifact(question, signals, artifact)
    artifact["routing"] = {
        "required_capabilities": list(decision.required_capabilities),
        "capability_satisfaction": decision.capability_satisfaction or {},
        "recommendations": [item.lane for item in decision.recommendations],
        "rejected": {item.lane: list(item.reasons) for item in decision.rejected},
        "execution_wave": "bounded_parallel" if len(decision.recommendations) > 1 else "single_lane",
        "stop_reason": decision.stop_reason,
        "lane_decision": [
            {
                "required_capability": capability,
                "selected_lane": list(decision.capability_satisfaction.get(capability, ())),
                "rejected_lanes": {item.lane: list(item.reasons) for item in decision.rejected if capability in item.satisfies or item.lane in {"exa", "duckduckgo"}},
                "rejection_reason": next((reason for item in decision.rejected for reason in item.reasons if capability in item.satisfies), None),
                "evidence_gap": artifact["quality"]["stopping"]["missing_categories"],
                "evidence_obtained": artifact["quality"]["source_contribution"],
                "stop_reason": decision.stop_reason,
            }
            for capability in decision.required_capabilities
        ],
    }
    phase2a_result: dict[str, Any] | None = None
    if signals.needs_adversarial_review:
        # The caller must supply the explicit challenge signal.  Reuse the
        # stabilized evaluator; do not infer this from impact or routing.
        runner = manual_disconfirmation_runner
        if runner is None:
            from .evaluate_phase2a import evaluate
            runner = evaluate
        phase2a_result = runner()
    artifact["phase2a"] = {"requested": signals.needs_adversarial_review, "executed": bool(phase2a_result is not None), "activation": "explicit_only"}
    if phase2a_result is not None:
        artifact["phase2a"]["result_schema"] = phase2a_result.get("schema")
    failures = [failure for lane in lanes for failure in lane.failures]
    signal_values = {}
    for name in signals.__dataclass_fields__:
        value = getattr(signals, name)
        signal_values[name] = sorted(value) if isinstance(value, (frozenset, set, tuple)) else value
    artifact["integration_telemetry"] = {
        "caller": caller,
        "caller_run_id": caller_run_id or run_id,
        "research_run_id": run_id,
        "task_signals": signal_values,
        "required_capabilities": list(decision.required_capabilities),
        "capability_satisfaction": decision.capability_satisfaction or {},
        "selected_lanes": [item.lane for item in decision.recommendations],
        "executed_lanes": [lane.lane_id for lane in lanes if lane.status != "not_attempted"],
        "provider_outcomes": {lane.provider: lane.status for lane in lanes},
        "sources_opened": sum(item.status in {"opened", "anchor_confirmed", "verified"} for item in opened),
        "claim_statuses": {claim.get("claim_id"): claim.get("status") for claim in artifact.get("claims", [])},
        "stop_reason": decision.stop_reason,
        "quality_stop_status": artifact["quality"]["stopping"]["status"],
        "quality_missing_categories": artifact["quality"]["stopping"]["missing_categories"],
        "unique_useful_sources": artifact["quality"]["source_contribution"]["unique_useful_sources"],
        "phase2a_requested": signals.needs_adversarial_review,
        "phase2a_executed": phase2a_result is not None,
        "total_runtime_ms": round((time.perf_counter() - total_started) * 1000, 1),
        "failure_class": (
            "routing_policy_failure"
            if decision.stop_reason == "no_eligible_lane"
            else "provider_or_lane_failure"
            if failures
            else None
        ),
    }
    write_run(artifact_path, artifact)
    return artifact, artifact_path
