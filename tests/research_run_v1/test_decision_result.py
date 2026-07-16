from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from research_runtime.decision_result import (
    DecisionResultValidationError,
    validate,
    write_result,
)
from research_runtime.research_result import validate as validate_research_result


RUN_ID = "87654321-4321-4432-8432-210987654321"
REQUEST_ID = "12345678-1234-4234-8234-123456789012"
HASH = "a" * 64


def result() -> dict:
    return {
        "schema_version": "decision-result.v1",
        "identity": {"decision_id": "11111111-2222-4333-8444-555555555555", "request_id": REQUEST_ID, "request_sha256": "b" * 64, "created_at": "2026-07-14T22:30:00Z"},
        "context": {"objective": "Choose persistence.", "scope": "Investigation state.", "constraints": {"reversibility": ["Rollback required"]}},
        "decision": {"selected_option": {"option_id": "sqlite", "label": "SQLite"}, "outcome": "Select SQLite for the bounded first increment.", "rationale": "It meets the stated constraints with the smallest operational surface."},
        "alternatives": {"considered": [{"option_id": "sqlite", "label": "SQLite"}, {"option_id": "files", "label": "Append-only files"}], "rejected": ["files"], "rejection_reasons": [{"option_id": "files", "reason": "Weaker query ergonomics for the required access pattern."}]},
        "tradeoffs": {"accepted": ["Single-node storage"], "rejected": ["Distributed availability"], "consequences": ["A later migration may be needed if concurrency grows."]},
        "evidence": {"research_result_refs": [{"run_id": RUN_ID, "artifact_sha256": HASH}], "supporting_claims": ["claim-1"], "conflicting_claims": [], "confidence": "medium", "unresolved_questions": ["Concurrent writer limits require a later live test."]},
        "risks": {"known": ["Concurrency ceiling is not fully established."], "mitigations": ["Keep the first increment single-writer."], "accepted_risks": ["Bounded pilot risk"]},
        "authority": {"decision_owner": "workspace owner", "approvals": [{"approver": "workspace owner", "state": "pending"}], "approval_state": "pending"},
        "execution_boundary": {"implementation_required": True, "planning_required": True, "blocked_items": ["Define migration rollback before implementation."]},
        "provenance": {"source_artifacts": [{"kind": "decision_request", "artifact_id": REQUEST_ID, "sha256": "b" * 64}, {"kind": "research_result", "artifact_id": RUN_ID, "sha256": HASH}], "hashes": {"request": "b" * 64, "research_results": [HASH]}},
    }


def test_valid_result_round_trips() -> None:
    value = result()
    validate(value)
    assert json.loads(json.dumps(value)) == value


def test_request_and_research_hash_binding_is_required() -> None:
    value = result()
    value["identity"]["request_id"] = "bad"
    with pytest.raises(DecisionResultValidationError):
        validate(value)
    value = result()
    value["provenance"]["hashes"]["request"] = "c" * 64
    with pytest.raises(DecisionResultValidationError):
        validate(value)
    value = result()
    value["evidence"]["research_result_refs"][0]["artifact_sha256"] = "bad"
    with pytest.raises(DecisionResultValidationError):
        validate(value)


def test_rejected_alternatives_and_unresolved_evidence_are_required() -> None:
    value = result()
    del value["alternatives"]["rejection_reasons"]
    with pytest.raises(DecisionResultValidationError):
        validate(value)
    value = result()
    del value["evidence"]["unresolved_questions"]
    with pytest.raises(DecisionResultValidationError):
        validate(value)


def test_authority_and_execution_boundaries_are_required() -> None:
    value = result()
    value["authority"]["approval_state"] = "approved"
    assert validate(value) is None
    value = result()
    del value["execution_boundary"]["planning_required"]
    with pytest.raises(DecisionResultValidationError):
        validate(value)


def test_immutable_storage_does_not_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "decision-result.json"
    write_result(target, result())
    original = target.read_bytes()
    with pytest.raises(FileExistsError):
        write_result(target, result())
    assert target.read_bytes() == original


def test_research_result_rejects_decision_fields() -> None:
    fixture = Path(__file__).parent / "fixtures" / "valid.json"
    research = json.loads(fixture.read_text(encoding="utf-8"))
    research["decision"] = "not allowed"
    with pytest.raises(Exception):
        validate_research_result(research)
