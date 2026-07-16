"""Immutable, evidence-bound output contract for a future design workflow."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "decision-result.v1"
CONFIDENCE = {"high", "medium", "low", "insufficient"}
APPROVAL_STATES = {"not_required", "pending", "approved", "rejected"}
TOP_LEVEL_FIELDS = {"schema_version", "identity", "context", "decision", "alternatives", "tradeoffs", "evidence", "risks", "authority", "execution_boundary", "provenance"}


class DecisionResultValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _required(obj: dict[str, Any], fields: tuple[str, ...], path: str, errors: list[str]) -> None:
    for field in fields:
        if field not in obj:
            errors.append(f"{path}.{field}: required")


def _str(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected non-empty string")


def _strings(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{path}: expected array of strings")


def _hash(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", value):
        errors.append(f"{path}: expected SHA-256")


def _ref(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return
    _required(value, ("run_id", "artifact_sha256"), path, errors)
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", str(value.get("run_id", ""))):
        errors.append(f"{path}.run_id: expected UUID")
    _hash(value.get("artifact_sha256"), f"{path}.artifact_sha256", errors)


def _option(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return
    _required(value, ("option_id", "label"), path, errors)
    _str(value.get("option_id"), f"{path}.option_id", errors)
    _str(value.get("label"), f"{path}.label", errors)


def validate(result: Any) -> None:
    errors: list[str] = []
    if not isinstance(result, dict):
        raise DecisionResultValidationError(["root: expected object"])
    errors.extend(f"root.{field}: unknown field" for field in sorted(set(result) - TOP_LEVEL_FIELDS))
    _required(result, tuple(TOP_LEVEL_FIELDS), "root", errors)
    if result.get("schema_version") != SCHEMA_VERSION:
        errors.append("root.schema_version: expected decision-result.v1")

    identity = result.get("identity")
    if not isinstance(identity, dict):
        errors.append("root.identity: expected object")
    else:
        _required(identity, ("decision_id", "request_id", "request_sha256", "created_at"), "root.identity", errors)
        for field in ("decision_id", "request_id"):
            if not re.fullmatch(r"[0-9a-fA-F-]{36}", str(identity.get(field, ""))):
                errors.append(f"root.identity.{field}: expected UUID")
        _hash(identity.get("request_sha256"), "root.identity.request_sha256", errors)
        _str(identity.get("created_at"), "root.identity.created_at", errors)

    context = result.get("context")
    if not isinstance(context, dict):
        errors.append("root.context: expected object")
    else:
        _required(context, ("objective", "scope", "constraints"), "root.context", errors)
        _str(context.get("objective"), "root.context.objective", errors)
        _str(context.get("scope"), "root.context.scope", errors)
        if not isinstance(context.get("constraints"), dict):
            errors.append("root.context.constraints: expected object")

    decision = result.get("decision")
    if not isinstance(decision, dict):
        errors.append("root.decision: expected object")
    else:
        _required(decision, ("selected_option", "outcome", "rationale"), "root.decision", errors)
        _option(decision.get("selected_option"), "root.decision.selected_option", errors)
        _str(decision.get("outcome"), "root.decision.outcome", errors)
        _str(decision.get("rationale"), "root.decision.rationale", errors)

    alternatives = result.get("alternatives")
    if not isinstance(alternatives, dict):
        errors.append("root.alternatives: expected object")
    else:
        _required(alternatives, ("considered", "rejected", "rejection_reasons"), "root.alternatives", errors)
        considered = alternatives.get("considered")
        if not isinstance(considered, list) or not considered:
            errors.append("root.alternatives.considered: expected non-empty array")
        else:
            for i, option in enumerate(considered):
                _option(option, f"root.alternatives.considered[{i}]", errors)
        _strings(alternatives.get("rejected"), "root.alternatives.rejected", errors)
        reasons = alternatives.get("rejection_reasons")
        if not isinstance(reasons, list) or any(not isinstance(item, dict) for item in reasons):
            errors.append("root.alternatives.rejection_reasons: expected array of objects")
        else:
            for i, reason in enumerate(reasons):
                _required(reason, ("option_id", "reason"), f"root.alternatives.rejection_reasons[{i}]", errors)
                _str(reason.get("option_id"), f"root.alternatives.rejection_reasons[{i}].option_id", errors)
                _str(reason.get("reason"), f"root.alternatives.rejection_reasons[{i}].reason", errors)

    tradeoffs = result.get("tradeoffs")
    if not isinstance(tradeoffs, dict):
        errors.append("root.tradeoffs: expected object")
    else:
        for field in ("accepted", "rejected", "consequences"):
            _strings(tradeoffs.get(field), f"root.tradeoffs.{field}", errors)

    evidence = result.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("root.evidence: expected object")
    else:
        _required(evidence, ("research_result_refs", "supporting_claims", "conflicting_claims", "confidence", "unresolved_questions"), "root.evidence", errors)
        refs = evidence.get("research_result_refs")
        if not isinstance(refs, list) or not refs:
            errors.append("root.evidence.research_result_refs: expected non-empty array")
        else:
            for i, ref in enumerate(refs):
                _ref(ref, f"root.evidence.research_result_refs[{i}]", errors)
        for field in ("supporting_claims", "conflicting_claims", "unresolved_questions"):
            _strings(evidence.get(field), f"root.evidence.{field}", errors)
        if evidence.get("confidence") not in CONFIDENCE:
            errors.append("root.evidence.confidence: invalid")

    risks = result.get("risks")
    if not isinstance(risks, dict):
        errors.append("root.risks: expected object")
    else:
        for field in ("known", "mitigations", "accepted_risks"):
            _strings(risks.get(field), f"root.risks.{field}", errors)

    authority = result.get("authority")
    if not isinstance(authority, dict):
        errors.append("root.authority: expected object")
    else:
        _required(authority, ("decision_owner", "approvals", "approval_state"), "root.authority", errors)
        _str(authority.get("decision_owner"), "root.authority.decision_owner", errors)
        if not isinstance(authority.get("approvals"), list):
            errors.append("root.authority.approvals: expected array")
        if authority.get("approval_state") not in APPROVAL_STATES:
            errors.append("root.authority.approval_state: invalid")

    boundary = result.get("execution_boundary")
    if not isinstance(boundary, dict):
        errors.append("root.execution_boundary: expected object")
    else:
        _required(boundary, ("implementation_required", "planning_required", "blocked_items"), "root.execution_boundary", errors)
        for field in ("implementation_required", "planning_required"):
            if not isinstance(boundary.get(field), bool):
                errors.append(f"root.execution_boundary.{field}: expected boolean")
        _strings(boundary.get("blocked_items"), "root.execution_boundary.blocked_items", errors)

    provenance = result.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("root.provenance: expected object")
    else:
        _required(provenance, ("source_artifacts", "hashes"), "root.provenance", errors)
        artifacts = provenance.get("source_artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            errors.append("root.provenance.source_artifacts: expected non-empty array")
        else:
            for i, artifact in enumerate(artifacts):
                path = f"root.provenance.source_artifacts[{i}]"
                if not isinstance(artifact, dict):
                    errors.append(f"{path}: expected object")
                    continue
                _required(artifact, ("kind", "artifact_id", "sha256"), path, errors)
                _str(artifact.get("kind"), f"{path}.kind", errors)
                _str(artifact.get("artifact_id"), f"{path}.artifact_id", errors)
                _hash(artifact.get("sha256"), f"{path}.sha256", errors)
        hashes = provenance.get("hashes")
        if not isinstance(hashes, dict):
            errors.append("root.provenance.hashes: expected object")
        else:
            if hashes.get("request") != identity.get("request_sha256"):
                errors.append("root.provenance.hashes.request: must equal root.identity.request_sha256")
            evidence_refs = result.get("evidence", {}).get("research_result_refs", [])
            expected_research_hashes = [ref.get("artifact_sha256") for ref in evidence_refs if isinstance(ref, dict)]
            if hashes.get("research_results") != expected_research_hashes:
                errors.append("root.provenance.hashes.research_results: must equal evidence research hashes")
            source_hashes = {item.get("kind"): item.get("sha256") for item in provenance.get("source_artifacts", []) if isinstance(item, dict)}
            if source_hashes.get("decision_request", source_hashes.get("request")) != identity.get("request_sha256"):
                errors.append("root.provenance.source_artifacts: request hash mismatch")

    if errors:
        raise DecisionResultValidationError(errors)


def write_result(path: str | Path, result: dict[str, Any]) -> None:
    validate(result)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
