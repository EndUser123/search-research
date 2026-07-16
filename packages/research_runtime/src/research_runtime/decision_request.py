"""Versioned, evidence-aware intake contract for a future design workflow.

This module validates the decision request only.  It does not route research,
select an option, emit an ADR, or execute a plan.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "decision-request.v1"
DECISION_TYPES = {"architecture", "technology_selection", "migration", "workflow", "operational_risk", "build_or_buy", "provider_strategy"}
CONSTRAINT_GROUPS = {"technical", "operational", "compatibility", "cost", "timeline", "reversibility"}
PRIORITY_FIELDS = {"reliability", "simplicity", "performance", "maintainability", "cost"}
TOP_LEVEL_FIELDS = {"schema_version", "request_id", "created_at", "decision_context", "constraints", "options", "priorities", "authority", "research_dependency"}


class DecisionRequestValidationError(ValueError):
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


def _strings(value: Any, path: str, errors: list[str], *, nonempty: bool = False) -> None:
    if not isinstance(value, list) or (nonempty and not value) or any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{path}: expected {'non-empty ' if nonempty else ''}array of strings")


def validate(request: Any) -> None:
    errors: list[str] = []
    if not isinstance(request, dict):
        raise DecisionRequestValidationError(["root: expected object"])
    unknown = set(request) - TOP_LEVEL_FIELDS
    errors.extend(f"root.{field}: unknown field" for field in sorted(unknown))
    _required(request, tuple(TOP_LEVEL_FIELDS), "root", errors)
    if request.get("schema_version") != SCHEMA_VERSION:
        errors.append("root.schema_version: expected decision-request.v1")
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", str(request.get("request_id", ""))):
        errors.append("root.request_id: expected UUID")
    _str(request.get("created_at"), "root.created_at", errors)

    context = request.get("decision_context")
    if not isinstance(context, dict):
        errors.append("root.decision_context: expected object")
    else:
        _required(context, ("objective", "desired_outcome", "decision_type", "scope"), "root.decision_context", errors)
        for field in ("objective", "desired_outcome", "scope"):
            _str(context.get(field), f"root.decision_context.{field}", errors)
        if context.get("decision_type") not in DECISION_TYPES:
            errors.append("root.decision_context.decision_type: invalid")

    constraints = request.get("constraints")
    if not isinstance(constraints, dict):
        errors.append("root.constraints: expected object")
    else:
        unknown_constraints = set(constraints) - CONSTRAINT_GROUPS
        errors.extend(f"root.constraints.{field}: unknown field" for field in sorted(unknown_constraints))
        for field in CONSTRAINT_GROUPS:
            if field not in constraints:
                errors.append(f"root.constraints.{field}: required; use [] when no constraint is known")
            else:
                _strings(constraints.get(field), f"root.constraints.{field}", errors)

    options = request.get("options")
    if not isinstance(options, dict):
        errors.append("root.options: expected object")
    else:
        _required(options, ("considered", "excluded", "alternatives"), "root.options", errors)
        for field in ("excluded", "alternatives"):
            _strings(options.get(field), f"root.options.{field}", errors)
        considered = options.get("considered")
        if not isinstance(considered, list) or not considered:
            errors.append("root.options.considered: expected non-empty array")
        else:
            ids: set[str] = set()
            for i, option in enumerate(considered):
                path = f"root.options.considered[{i}]"
                if not isinstance(option, dict):
                    errors.append(f"{path}: expected object")
                    continue
                _required(option, ("option_id", "label"), path, errors)
                _str(option.get("option_id"), f"{path}.option_id", errors)
                _str(option.get("label"), f"{path}.label", errors)
                if option.get("option_id") in ids:
                    errors.append(f"{path}.option_id: duplicate")
                ids.add(option.get("option_id"))

    priorities = request.get("priorities")
    if not isinstance(priorities, dict):
        errors.append("root.priorities: expected object")
    else:
        unknown_priorities = set(priorities) - PRIORITY_FIELDS
        errors.extend(f"root.priorities.{field}: unknown field" for field in sorted(unknown_priorities))
        for field in PRIORITY_FIELDS:
            _str(priorities.get(field), f"root.priorities.{field}", errors)

    authority = request.get("authority")
    if not isinstance(authority, dict):
        errors.append("root.authority: expected object")
    else:
        _required(authority, ("decision_owner", "approval_requirements", "irreversible_actions"), "root.authority", errors)
        _str(authority.get("decision_owner"), "root.authority.decision_owner", errors)
        _strings(authority.get("approval_requirements"), "root.authority.approval_requirements", errors)
        _strings(authority.get("irreversible_actions"), "root.authority.irreversible_actions", errors)

    dependency = request.get("research_dependency")
    if not isinstance(dependency, dict):
        errors.append("root.research_dependency: expected object")
    else:
        _required(dependency, ("required", "result_refs", "unresolved_evidence_acknowledged", "freshness_requirement"), "root.research_dependency", errors)
        if not isinstance(dependency.get("required"), bool):
            errors.append("root.research_dependency.required: expected boolean")
        refs = dependency.get("result_refs")
        if not isinstance(refs, list) or (dependency.get("required") is True and not refs):
            errors.append("root.research_dependency.result_refs: expected array; required research needs at least one reference")
        else:
            for i, ref in enumerate(refs):
                path = f"root.research_dependency.result_refs[{i}]"
                if not isinstance(ref, dict):
                    errors.append(f"{path}: expected object")
                    continue
                _required(ref, ("run_id", "artifact_sha256"), path, errors)
                if not re.fullmatch(r"[0-9a-fA-F-]{36}", str(ref.get("run_id", ""))):
                    errors.append(f"{path}.run_id: expected UUID")
                if not re.fullmatch(r"[0-9a-fA-F]{64}", str(ref.get("artifact_sha256", ""))):
                    errors.append(f"{path}.artifact_sha256: expected SHA-256")
        if not isinstance(dependency.get("unresolved_evidence_acknowledged"), bool):
            errors.append("root.research_dependency.unresolved_evidence_acknowledged: expected boolean")
        _str(dependency.get("freshness_requirement"), "root.research_dependency.freshness_requirement", errors)

    if errors:
        raise DecisionRequestValidationError(errors)


def write_request(path: str | Path, request: dict[str, Any]) -> None:
    validate(request)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(request, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
