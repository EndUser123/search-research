"""Consumer-facing, evidence-only projection of a validated research run.

``research-run.v1`` is the execution record.  ``research-result.v1`` is a
small immutable handoff for a future decision workflow.  It deliberately does
not contain a chosen option or decision authority.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .validator import ValidationError, validate as validate_run

SCHEMA_VERSION = "research-result.v1"


class ResearchResultValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _str(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected non-empty string")


def _list(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{path}: expected array")


def validate(result: Any) -> None:
    errors: list[str] = []
    if not isinstance(result, dict):
        raise ResearchResultValidationError(["root: expected object"])
    required = (
        "schema_version", "run_id", "source_schema_version", "created_at",
        "context", "evidence_requirements", "findings", "options", "risks",
        "unresolved_questions", "provenance", "stopping", "authorization",
    )
    for field in required:
        if field not in result:
            errors.append(f"root.{field}: required")
    if result.get("schema_version") != SCHEMA_VERSION:
        errors.append("root.schema_version: expected research-result.v1")
    if result.get("source_schema_version") != "research-run.v1":
        errors.append("root.source_schema_version: expected research-run.v1")
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", str(result.get("run_id", ""))):
        errors.append("root.run_id: expected UUID")
    _str(result.get("created_at"), "root.created_at", errors)
    context = result.get("context")
    if not isinstance(context, dict):
        errors.append("root.context: expected object")
    else:
        for field in ("research_question", "requested_decision"):
            _str(context.get(field), f"root.context.{field}", errors)
        for field in ("scope", "constraints", "assumptions"):
            _list(context.get(field), f"root.context.{field}", errors)
    requirements = result.get("evidence_requirements")
    if not isinstance(requirements, dict):
        errors.append("root.evidence_requirements: expected object")
    else:
        for field in ("required_capabilities", "fulfilled_capabilities", "unresolved"):
            _list(requirements.get(field), f"root.evidence_requirements.{field}", errors)
    for field in ("findings", "options", "risks", "unresolved_questions"):
        _list(result.get(field), f"root.{field}", errors)
    findings = result.get("findings", [])
    finding_ids: set[str] = set()
    if isinstance(findings, list):
        for i, finding in enumerate(findings):
            path = f"root.findings[{i}]"
            if not isinstance(finding, dict):
                errors.append(f"{path}: expected object")
                continue
            for field in ("claim_id", "statement", "status", "confidence"):
                _str(finding.get(field), f"{path}.{field}", errors)
            cid = finding.get("claim_id")
            if isinstance(cid, str):
                if cid in finding_ids:
                    errors.append(f"{path}.claim_id: duplicate")
                finding_ids.add(cid)
            for field in ("supporting_source_ids", "contradicting_source_ids", "assessment_ids", "limitations"):
                _list(finding.get(field), f"{path}.{field}", errors)
    provenance = result.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("root.provenance: expected object")
    else:
        for field in ("run_id", "artifact_sha256", "workspace_revision"):
            _str(provenance.get(field), f"root.provenance.{field}", errors)
        for field in ("sources", "assessments", "lanes", "failures"):
            _list(provenance.get(field), f"root.provenance.{field}", errors)
        if provenance.get("run_id") != result.get("run_id"):
            errors.append("root.provenance.run_id: must equal root.run_id")
    stopping = result.get("stopping")
    if not isinstance(stopping, dict):
        errors.append("root.stopping: expected object")
    else:
        _str(stopping.get("reason"), "root.stopping.reason", errors)
        _str(stopping.get("status"), "root.stopping.status", errors)
    authorization = result.get("authorization")
    if not isinstance(authorization, dict):
        errors.append("root.authorization: expected object")
    else:
        if authorization.get("research_may_decide") is not False:
            errors.append("root.authorization.research_may_decide: must be false")
        if authorization.get("decision_authority") != "downstream_consumer":
            errors.append("root.authorization.decision_authority: invalid")
    if "decision" in result or "chosen_option" in result:
        errors.append("root: decision fields are not permitted")
    if errors:
        raise ResearchResultValidationError(errors)


def build_research_result(artifact: dict[str, Any], *, artifact_sha256: str = "") -> dict[str, Any]:
    """Project an existing validated run without inventing options or claims."""
    validate_run(artifact)
    quality = artifact.get("quality", {}) if isinstance(artifact.get("quality"), dict) else {}
    plan = quality.get("plan", {}) if isinstance(quality.get("plan"), dict) else {}
    stopping = quality.get("stopping", {}) if isinstance(quality.get("stopping"), dict) else {}
    routing = artifact.get("routing", {}) if isinstance(artifact.get("routing"), dict) else {}
    task = artifact.get("integration_telemetry", {}).get("task_signals", {})
    if not isinstance(task, dict):
        task = {}
    findings = []
    for claim in artifact.get("claims", []):
        findings.append({
            "claim_id": claim["claim_id"], "statement": claim["text"],
            "status": claim["status"],
            "confidence": "high" if claim["status"] == "verified" else "bounded",
            "supporting_source_ids": list(claim["supporting_source_ids"]),
            "contradicting_source_ids": list(claim["contradicting_source_ids"]),
            "assessment_ids": [a.get("assessment_id", f"assessment-{i}") for i, a in enumerate(artifact.get("assessments", [])) if a.get("claim_id") == claim["claim_id"]],
            "limitations": list(claim.get("limitations", [])) if isinstance(claim.get("limitations"), list) else [claim["falsifier"]],
        })
    unresolved = list(artifact.get("uncertainty", []))
    unresolved.extend(stopping.get("missing_categories", []))
    if not artifact.get("claims"):
        unresolved.append("No claim-specific finding was established by this run.")
    return {
        "schema_version": SCHEMA_VERSION, "source_schema_version": "research-run.v1",
        "run_id": artifact["run_id"], "created_at": artifact["created_at"],
        "context": {
            "research_question": artifact["research_question"],
            "requested_decision": artifact["requested_decision"],
            "scope": ["This result contains only evidence gathered by this run."],
            "constraints": [f"authorization_level_sought={artifact['authorization_level_sought']}"],
            "assumptions": [],
        },
        "evidence_requirements": {
            "required_capabilities": list(routing.get("required_capabilities", plan.get("required_categories", []))),
            "fulfilled_capabilities": sorted({cap for caps in routing.get("capability_satisfaction", {}).values() for cap in caps}) if isinstance(routing.get("capability_satisfaction"), dict) else [],
            "unresolved": unresolved,
        },
        "findings": findings,
        "options": [],
        "risks": [{"statement": item, "kind": "uncertainty"} for item in unresolved],
        "unresolved_questions": unresolved,
        "provenance": {
            "run_id": artifact["run_id"], "artifact_sha256": artifact_sha256 or "not_bound",
            "workspace_revision": artifact.get("workspace", {}).get("revision", "unknown"),
            "sources": artifact.get("sources", []), "assessments": artifact.get("assessments", []),
            "lanes": artifact.get("retrieval_lanes", []),
            "failures": [failure for lane in artifact.get("retrieval_lanes", []) for failure in lane.get("failures", [])],
        },
        "stopping": {"status": stopping.get("status", "unknown"), "reason": artifact["stop_reason"],
                     "runtime_ms": artifact.get("integration_telemetry", {}).get("total_runtime_ms")},
        "authorization": {"decision_authority": "downstream_consumer", "research_may_recommend": True,
                          "research_may_decide": False, "authorization_supported": artifact["authorization_supported"]},
    }


def write_result(path: str | Path, result: dict[str, Any]) -> None:
    validate(result)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
