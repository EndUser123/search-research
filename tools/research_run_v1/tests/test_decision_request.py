from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from research_runtime.decision_request import (
    DecisionRequestValidationError,
    validate,
    write_request,
)


def request() -> dict:
    return {
        "schema_version": "decision-request.v1",
        "request_id": "12345678-1234-4234-8234-123456789012",
        "created_at": "2026-07-14T22:00:00Z",
        "decision_context": {
            "objective": "Choose a persistence approach.",
            "desired_outcome": "Durable state with bounded operational burden.",
            "decision_type": "architecture",
            "scope": "Investigation state storage only.",
        },
        "constraints": {key: [f"{key} constraint"] for key in ("technical", "operational", "compatibility", "cost", "timeline", "reversibility")},
        "options": {
            "considered": [{"option_id": "sqlite", "label": "SQLite"}, {"option_id": "files", "label": "Append-only files"}],
            "excluded": ["Managed database"],
            "alternatives": ["Do not persist"],
        },
        "priorities": {key: "high" if key in {"reliability", "simplicity"} else "medium" for key in ("reliability", "simplicity", "performance", "maintainability", "cost")},
        "authority": {
            "decision_owner": "workspace owner",
            "approval_requirements": ["Human approval before irreversible change"],
            "irreversible_actions": ["Schema migration requires rollback plan"],
        },
        "research_dependency": {
            "required": True,
            "result_refs": [{"run_id": "87654321-4321-4432-8432-210987654321", "artifact_sha256": "a" * 64}],
            "unresolved_evidence_acknowledged": True,
            "freshness_requirement": "Current for the selected workspace revision.",
        },
    }


def test_valid_request_round_trips() -> None:
    value = request()
    validate(value)
    assert json.loads(json.dumps(value)) == value


@pytest.mark.parametrize("field", ["decision_context", "constraints", "options", "priorities", "authority", "research_dependency"])
def test_required_sections_are_required(field: str) -> None:
    value = request()
    del value[field]
    with pytest.raises(DecisionRequestValidationError):
        validate(value)


def test_missing_constraints_are_rejected() -> None:
    value = request()
    del value["constraints"]["reversibility"]
    with pytest.raises(DecisionRequestValidationError):
        validate(value)


def test_research_reference_requires_run_identity_and_hash() -> None:
    value = request()
    value["research_dependency"]["result_refs"][0]["artifact_sha256"] = "not-bound"
    with pytest.raises(DecisionRequestValidationError):
        validate(value)


def test_research_artifact_decision_fields_are_not_accepted_as_intake() -> None:
    value = request()
    value["decision"] = "SQLite"
    with pytest.raises(DecisionRequestValidationError):
        validate(value)


def test_required_research_cannot_be_empty() -> None:
    value = request()
    value["research_dependency"]["result_refs"] = []
    with pytest.raises(DecisionRequestValidationError):
        validate(value)


def test_immutable_storage_does_not_overwrite(tmp_path: Path) -> None:
    value = request()
    target = tmp_path / "decision-request.json"
    write_request(target, value)
    original = target.read_bytes()
    with pytest.raises(FileExistsError):
        write_request(target, value)
    assert target.read_bytes() == original
