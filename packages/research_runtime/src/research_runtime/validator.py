"""Validate and safely persist research-run.v1 JSON artifacts.

This module deliberately has no provider or harness dependencies. Producers may
be Codex, OpenCode, a CLI, or a human following the documented contract.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "research-run.v1"
AUTH_LEVELS = {"none", "evidence_gathering", "implementation", "pilot", "production"}
LANE_STATUSES = {"success", "empty", "failed", "not_attempted"}
DISCOVERY = {"discovery_only", "opened", "anchor_confirmed", "verified"}
CLAIM_STATUSES = {"verified", "supported", "contradicted", "unverified"}
ASSESSMENT_RELATIONSHIPS = {"directly_supports", "partially_supports", "contradicts", "contextual_only", "insufficient"}
ASSESSMENT_AUTHORITIES = {"primary", "secondary", "runtime", "unknown"}
ASSESSMENT_CURRENCIES = {"current", "possibly_stale", "stale", "unknown"}
ASSESSMENT_METHODS = {"caller_supplied", "reference_evaluator", "model_assisted", "deterministic_anchor_only"}
AGY_ROLES = {"AGY_SEARCH_INDEPENDENT", "AGY_SEARCH_DEEP", "AGY_SEARCH_ADVERSARIAL"}
SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_ -]?key|access[_ -]?token|authorization|bearer|cookie)\s*[:=]"),
    re.compile(r"(?i)\b(?:sk-|tvly-|exa_|pplx-|ghp_|xai-)[A-Za-z0-9_-]{8,}"),
)


class ValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _required(obj: dict[str, Any], names: tuple[str, ...], path: str, errors: list[str]) -> None:
    for name in names:
        if name not in obj:
            errors.append(f"{path}.{name}: required")


def _iso(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{path}: expected ISO-8601 string")
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{path}: invalid ISO-8601 timestamp")


def _str(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected non-empty string")


def _source(source: Any, path: str, lane_ids: set[str], errors: list[str]) -> None:
    if not isinstance(source, dict):
        errors.append(f"{path}: expected object")
        return
    _required(source, ("source_id", "title", "url", "source_type", "discovery_status", "retrieved_at", "retrieval_method"), path, errors)
    _str(source.get("source_id"), f"{path}.source_id", errors)
    _str(source.get("title"), f"{path}.title", errors)
    _str(source.get("url"), f"{path}.url", errors)
    _str(source.get("source_type"), f"{path}.source_type", errors)
    if source.get("discovery_status") not in DISCOVERY:
        errors.append(f"{path}.discovery_status: invalid")
    _iso(source.get("retrieved_at"), f"{path}.retrieved_at", errors)
    _str(source.get("retrieval_method"), f"{path}.retrieval_method", errors)
    if source.get("discovery_status") in {"opened", "anchor_confirmed", "verified"}:
        _required(source, ("opened_at", "opened_by"), path, errors)
        _iso(source.get("opened_at"), f"{path}.opened_at", errors)
        _str(source.get("opened_by"), f"{path}.opened_by", errors)
    if source.get("discovery_status") == "anchor_confirmed":
        _required(source, ("anchor_at", "anchor_text", "anchor_method"), path, errors)
        _iso(source.get("anchor_at"), f"{path}.anchor_at", errors)
        _str(source.get("anchor_text"), f"{path}.anchor_text", errors)
        _str(source.get("anchor_method"), f"{path}.anchor_method", errors)
    if source.get("discovery_status") == "verified":
        _required(source, ("verified_at", "verification_method"), path, errors)
        _iso(source.get("verified_at"), f"{path}.verified_at", errors)
        _str(source.get("verification_method"), f"{path}.verification_method", errors)
    if source.get("lane_id") not in lane_ids:
        errors.append(f"{path}.lane_id: unknown lane")


def _assessment(assessment: Any, path: str, claim_ids: set[str], source_ids: set[str], errors: list[str]) -> None:
    if not isinstance(assessment, dict):
        errors.append(f"{path}: expected object")
        return
    _required(assessment, ("claim_id", "source_id", "source_location", "passage_or_anchor", "relationship", "authority", "currency", "assessment_method", "assessment_basis", "assessed_at", "limitations", "run_id"), path, errors)
    if assessment.get("claim_id") not in claim_ids:
        errors.append(f"{path}.claim_id: unknown claim")
    if assessment.get("source_id") not in source_ids:
        errors.append(f"{path}.source_id: unknown source")
    for field in ("source_location", "passage_or_anchor", "assessment_basis", "run_id"):
        _str(assessment.get(field), f"{path}.{field}", errors)
    if assessment.get("relationship") not in ASSESSMENT_RELATIONSHIPS:
        errors.append(f"{path}.relationship: invalid")
    if assessment.get("authority") not in ASSESSMENT_AUTHORITIES:
        errors.append(f"{path}.authority: invalid")
    if assessment.get("currency") not in ASSESSMENT_CURRENCIES:
        errors.append(f"{path}.currency: invalid")
    if assessment.get("assessment_method") not in ASSESSMENT_METHODS:
        errors.append(f"{path}.assessment_method: invalid")
    _iso(assessment.get("assessed_at"), f"{path}.assessed_at", errors)
    if not isinstance(assessment.get("limitations"), list) or any(not isinstance(item, str) or not item.strip() for item in assessment.get("limitations", [])):
        errors.append(f"{path}.limitations: expected array of strings")


def _existing_evidence_paths(value: Any, path: str, invocation_id: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{path}: expected non-empty evidence path array")
        return
    for i, raw_path in enumerate(value):
        item_path = f"{path}[{i}]"
        _str(raw_path, item_path, errors)
        if not isinstance(raw_path, str):
            continue
        normalized = raw_path.replace("\\", "/")
        if invocation_id not in normalized:
            errors.append(f"{item_path}: must contain invocation ID")
        if not Path(raw_path).is_file():
            errors.append(f"{item_path}: evidence file does not exist")


def _existing_evidence_path(value: Any, path: str, invocation_id: str, errors: list[str]) -> None:
    _str(value, path, errors)
    if not isinstance(value, str):
        return
    if invocation_id not in value.replace("\\", "/"):
        errors.append(f"{path}: must contain invocation ID")
    if not Path(value).is_file():
        errors.append(f"{path}: evidence file does not exist")


def _validate_agy_runtime(artifact: dict[str, Any], lane_ids: set[str], errors: list[str]) -> None:
    runtime = artifact.get("runtime")
    if not isinstance(runtime, dict) or runtime.get("role") not in AGY_ROLES:
        return
    invocation_id = runtime.get("invocation_id")
    if not isinstance(invocation_id, str) or not invocation_id:
        errors.append("root.runtime.invocation_id: required for advisory agy runs")
        return
    if runtime.get("status") not in {"success", "empty", "failed", "researcher_unavailable"}:
        errors.append("root.runtime.status: invalid advisory agy status")
    if runtime.get("authorization_supported") is not False or artifact.get("authorization_supported") is not False:
        errors.append("root.runtime: advisory agy runs cannot authorize broader execution")
    if artifact.get("authorization_level_sought") not in {"none", "evidence_gathering"}:
        errors.append("root.authorization_level_sought: agy may seek evidence_gathering only")
    if runtime.get("backend_model_identity") not in {None, "unproven", "unavailable"}:
        errors.append("root.runtime.backend_model_identity: authoritative identity is unavailable")
    for field in ("packet_path", "metadata_path", "stdout_path", "stderr_path", "internal_log_path", "findings_path"):
        _existing_evidence_path(runtime.get(field), f"root.runtime.{field}", invocation_id, errors)
    packet_path = runtime.get("packet_path")
    if isinstance(packet_path, str) and Path(packet_path).is_file():
        try:
            packet = json.loads(Path(packet_path).read_text(encoding="utf-8"))
            if packet.get("invocation_id") != invocation_id:
                errors.append("root.runtime.packet_path: packet invocation ID mismatch")
            expected_hash = runtime.get("packet_sha256")
            if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
                errors.append("root.runtime.packet_sha256: required SHA-256 hash")
            elif __import__("hashlib").sha256(Path(packet_path).read_bytes()).hexdigest().lower() != expected_hash.lower():
                errors.append("root.runtime.packet_sha256: packet hash mismatch")
        except (OSError, json.JSONDecodeError):
            errors.append("root.runtime.packet_path: unreadable JSON packet")
    if runtime.get("status") == "success":
        if runtime.get("exit_code") != 0:
            errors.append("root.runtime.exit_code: successful agy run requires zero exit code")
        if runtime.get("timeout_triggered") is not False:
            errors.append("root.runtime.timeout_triggered: successful agy run cannot time out")
        findings_path = runtime.get("findings_path")
        if isinstance(findings_path, str) and Path(findings_path).is_file():
            try:
                findings = json.loads(Path(findings_path).read_text(encoding="utf-8"))
                if not isinstance(findings, list) or not findings:
                    errors.append("root.runtime.findings_path: successful agy run requires non-empty findings")
            except (OSError, json.JSONDecodeError):
                errors.append("root.runtime.findings_path: invalid JSON findings")
    agy_lane_ids = {
        lane.get("lane_id")
        for lane in artifact.get("retrieval_lanes", [])
        if isinstance(lane, dict) and lane.get("provider") == "agy"
    }
    for i, source in enumerate(artifact.get("sources", [])):
        if isinstance(source, dict) and source.get("lane_id") in agy_lane_ids and source.get("discovery_status") in {"opened", "verified"}:
            _existing_evidence_paths(source.get("evidence_paths"), f"root.sources[{i}].evidence_paths", invocation_id, errors)
    agy_lanes = [lane for lane in artifact.get("retrieval_lanes", []) if isinstance(lane, dict) and lane.get("provider") == "agy"]
    if not agy_lanes:
        errors.append("root.retrieval_lanes: advisory agy run requires an agy lane")
    if runtime.get("status") == "success" and any(lane.get("status") != "success" for lane in agy_lanes):
        errors.append("root.runtime.status: successful agy run cannot hide a failed or unavailable lane")
    if runtime.get("status") in {"failed", "researcher_unavailable"} and not any(lane.get("status") in {"failed", "not_attempted"} for lane in agy_lanes):
        errors.append("root.retrieval_lanes: failed agy runtime must remain visible as a failed lane")
    for i, claim in enumerate(artifact.get("claims", [])):
        if not isinstance(claim, dict) or claim.get("status") != "verified":
            continue
        supporting = set(claim.get("supporting_source_ids", []))
        agy_source_ids = {
            source.get("source_id")
            for source in artifact.get("sources", [])
            if isinstance(source, dict) and source.get("lane_id") in agy_lane_ids
        }
        if supporting & agy_source_ids and runtime.get("status") != "success":
            errors.append(f"root.claims[{i}]: failed agy invocation cannot support a verified claim")


def validate(artifact: Any) -> None:
    errors: list[str] = []
    if not isinstance(artifact, dict):
        raise ValidationError(["root: expected object"])
    _required(artifact, ("schema_version", "run_id", "created_at", "research_question", "requested_decision", "authorization_level_sought", "workspace", "authority", "runtime", "retrieval_lanes", "sources", "claims", "uncertainty", "stop_reason", "authorization_supported"), "root", errors)
    if artifact.get("schema_version") != SCHEMA_VERSION:
        errors.append("root.schema_version: expected research-run.v1")
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", str(artifact.get("run_id", ""))):
        errors.append("root.run_id: expected UUID")
    _iso(artifact.get("created_at"), "root.created_at", errors)
    for field in ("research_question", "requested_decision", "stop_reason"):
        _str(artifact.get(field), f"root.{field}", errors)
    if artifact.get("authorization_level_sought") not in AUTH_LEVELS:
        errors.append("root.authorization_level_sought: invalid")
    if not isinstance(artifact.get("authorization_supported"), bool):
        errors.append("root.authorization_supported: expected boolean")
    for container in ("workspace", "authority", "runtime"):
        if not isinstance(artifact.get(container), dict):
            errors.append(f"root.{container}: expected object")
    authority = artifact.get("authority", {})
    if isinstance(authority, dict):
        _required(authority, ("producer", "acquisition", "serialization", "storage", "consumer", "trust", "scope", "lifetime", "collision", "failure", "retention"), "root.authority", errors)
    lanes = artifact.get("retrieval_lanes")
    lane_ids: set[str] = set()
    if not isinstance(lanes, list) or not lanes:
        errors.append("root.retrieval_lanes: expected non-empty array")
        lanes = []
    for i, lane in enumerate(lanes):
        path = f"root.retrieval_lanes[{i}]"
        if not isinstance(lane, dict):
            errors.append(f"{path}: expected object")
            continue
        _required(lane, ("lane_id", "provider", "independence_group", "query", "status", "started_at", "finished_at", "sources", "failures"), path, errors)
        lane_id = lane.get("lane_id")
        if not isinstance(lane_id, str) or not lane_id:
            errors.append(f"{path}.lane_id: expected non-empty string")
        elif lane_id in lane_ids:
            errors.append(f"{path}.lane_id: duplicate")
        else:
            lane_ids.add(lane_id)
        for field in ("provider", "independence_group", "query"):
            _str(lane.get(field), f"{path}.{field}", errors)
        if lane.get("status") not in LANE_STATUSES:
            errors.append(f"{path}.status: invalid")
        _iso(lane.get("started_at"), f"{path}.started_at", errors)
        _iso(lane.get("finished_at"), f"{path}.finished_at", errors)
        if not isinstance(lane.get("sources"), list):
            errors.append(f"{path}.sources: expected array")
        if not isinstance(lane.get("failures"), list):
            errors.append(f"{path}.failures: expected array")
    sources = artifact.get("sources")
    source_ids: set[str] = set()
    if not isinstance(sources, list):
        errors.append("root.sources: expected array")
        sources = []
    for i, source in enumerate(sources):
        before = len(errors)
        _source(source, f"root.sources[{i}]", lane_ids, errors)
        if isinstance(source, dict) and isinstance(source.get("source_id"), str):
            if source["source_id"] in source_ids:
                errors.append(f"root.sources[{i}].source_id: duplicate")
            source_ids.add(source["source_id"])
    claims = artifact.get("claims")
    claim_ids: set[str] = set()
    if not isinstance(claims, list):
        errors.append("root.claims: expected array")
        claims = []
    for i, claim in enumerate(claims):
        path = f"root.claims[{i}]"
        if not isinstance(claim, dict):
            errors.append(f"{path}: expected object")
            continue
        _required(claim, ("claim_id", "text", "status", "supporting_source_ids", "contradicting_source_ids", "verification_method", "falsifier"), path, errors)
        cid = claim.get("claim_id")
        if not isinstance(cid, str) or not cid:
            errors.append(f"{path}.claim_id: expected non-empty string")
        elif cid in claim_ids:
            errors.append(f"{path}.claim_id: duplicate")
        else:
            claim_ids.add(cid)
        _str(claim.get("text"), f"{path}.text", errors)
        if claim.get("status") not in CLAIM_STATUSES:
            errors.append(f"{path}.status: invalid")
        for field in ("supporting_source_ids", "contradicting_source_ids"):
            refs = claim.get(field)
            if not isinstance(refs, list):
                errors.append(f"{path}.{field}: expected array")
            else:
                for ref in refs:
                    if ref not in source_ids:
                        errors.append(f"{path}.{field}: unknown source {ref}")
        _str(claim.get("verification_method"), f"{path}.verification_method", errors)
        _str(claim.get("falsifier"), f"{path}.falsifier", errors)
        if claim.get("status") == "verified" and not claim.get("supporting_source_ids"):
            errors.append(f"{path}: verified claim requires supporting source")
        if claim.get("status") == "verified":
            verified_ids = {
                source.get("source_id")
                for source in sources
                if isinstance(source, dict) and source.get("discovery_status") == "verified"
            }
            if not any(ref in verified_ids for ref in claim.get("supporting_source_ids", [])):
                errors.append(f"{path}: verified claim requires an opened and verified supporting source")
    assessments = artifact.get("assessments", [])
    if not isinstance(assessments, list):
        errors.append("root.assessments: expected array")
    else:
        for i, assessment in enumerate(assessments):
            _assessment(assessment, f"root.assessments[{i}]", claim_ids, source_ids, errors)
    uncertainty = artifact.get("uncertainty")
    if not isinstance(uncertainty, list) or any(not isinstance(item, str) or not item.strip() for item in uncertainty):
        errors.append("root.uncertainty: expected array of strings")
    _validate_agy_runtime(artifact, lane_ids, errors)
    serialized = json.dumps(artifact, ensure_ascii=False)
    if any(pattern.search(serialized) for pattern in SECRET_PATTERNS):
        errors.append("root: secret-like material is not allowed")
    if errors:
        raise ValidationError(errors)


def validate_file(path: str | Path) -> None:
    target = Path(path)
    try:
        artifact = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError([f"{target}: cannot read JSON: {exc}"]) from exc
    validate(artifact)


def write_run(path: str | Path, artifact: dict[str, Any]) -> None:
    validate(artifact)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(artifact, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
