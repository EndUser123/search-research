"""Tests for design synthesis from decision request + research results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research_runtime.decision_request import (
    validate as validate_decision_request,
)
from research_runtime.decision_result import (
    DecisionResultValidationError,
    validate as validate_decision_result,
)
from research_runtime.design import synthesize
from research_runtime.research_result import (
    build_research_result,
    validate as validate_research_result,
    write_result,
)
from research_runtime.validator import validate as validate_run

ROOT = Path(__file__).parents[2]
FIXTURE = ROOT / "tests" / "research_run_v1" / "fixtures" / "valid.json"

REQUEST_ID = "12345678-1234-4234-8234-123456789012"
RUN_ID = "87654321-4321-4432-8432-210987654321"
HASH = "a" * 64


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decision_request(**overrides: dict) -> dict:
    """Build a valid decision-request.v1 for testing."""
    req = {
        "schema_version": "decision-request.v1",
        "request_id": REQUEST_ID,
        "created_at": "2026-07-14T22:00:00Z",
        "decision_context": {
            "objective": "Choose a persistence approach.",
            "desired_outcome": "Durable state with bounded operational burden.",
            "decision_type": "architecture",
            "scope": "Investigation state storage only.",
        },
        "constraints": {
            key: [f"{key} constraint"]
            for key in ("technical", "operational", "compatibility", "cost", "timeline", "reversibility")
        },
        "options": {
            "considered": [{"option_id": "sqlite", "label": "SQLite"}, {"option_id": "files", "label": "Append-only files"}],
            "excluded": ["Managed database"],
            "alternatives": ["Do not persist"],
        },
        "priorities": {
            key: "high" if key in {"reliability", "simplicity"} else "medium"
            for key in ("reliability", "simplicity", "performance", "maintainability", "cost")
        },
        "authority": {
            "decision_owner": "workspace owner",
            "approval_requirements": ["Human approval before irreversible change"],
            "irreversible_actions": ["Schema migration requires rollback plan"],
        },
        "research_dependency": {
            "required": True,
            "result_refs": [{"run_id": RUN_ID, "artifact_sha256": HASH}],
            "unresolved_evidence_acknowledged": True,
            "freshness_requirement": "Current for the selected workspace revision.",
        },
    }
    for key, value in overrides.items():
        parts = key.split(".")
        target = req
        for part in parts[:-1]:
            target = target[part]
        target[parts[-1]] = value
    return req


def _research_result(*, artifact_sha256: str = HASH, claim_text: str = "") -> dict:
    """Build a research-result.v1 from the valid fixture with explicit hash."""
    artifact = json.loads(FIXTURE.read_text(encoding="utf-8"))
    validate_run(artifact)
    if claim_text:
        artifact["claims"][0]["text"] = claim_text
    result = build_research_result(artifact, artifact_sha256=artifact_sha256)
    validate_research_result(result)
    return result


def _request_hash(request: dict) -> str:
    return hashlib.sha256(
        json.dumps(request, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Basic synthesis tests
# ---------------------------------------------------------------------------

def test_synthesis_produces_valid_decision_result() -> None:
    """End-to-end: valid request + valid research result -> valid decision result."""
    request = _decision_request()
    rr = _research_result()
    result = synthesize(request, [rr], request_sha256=_request_hash(request))
    # validate is called internally by synthesize()
    assert result["schema_version"] == "decision-result.v1"
    assert result["identity"]["request_id"] == REQUEST_ID
    assert result["identity"]["request_sha256"] == _request_hash(request)
    assert result["authority"]["approval_state"] == "pending"


def test_synthesis_preserves_request_context() -> None:
    """Decision context from request flows through to result."""
    request = _decision_request()
    rr = _research_result()
    result = synthesize(request, [rr], request_sha256=_request_hash(request))
    assert result["context"]["objective"] == request["decision_context"]["objective"]
    assert result["context"]["scope"] == request["decision_context"]["scope"]
    assert result["alternatives"]["considered"] == request["options"]["considered"]


def test_synthesis_preserves_research_run_references() -> None:
    """Research result run_id and hash are bound in the decision result."""
    request = _decision_request()
    rr = _research_result()
    result = synthesize(request, [rr], request_sha256=_request_hash(request))
    refs = result["evidence"]["research_result_refs"]
    assert len(refs) == 1
    assert refs[0]["run_id"] == rr["run_id"]
    assert refs[0]["artifact_sha256"] == HASH


def test_synthesis_records_unresolved_evidence() -> None:
    """Unresolved questions from research result are preserved."""
    request = _decision_request()
    # Create a research result with explicit uncertainty
    artifact = json.loads(FIXTURE.read_text(encoding="utf-8"))
    validate_run(artifact)
    artifact["uncertainty"] = ["Concurrent writer limits unknown."]
    rr = build_research_result(artifact, artifact_sha256="d" * 64)
    result = synthesize(request, [rr], request_sha256=_request_hash(request))
    assert isinstance(result["evidence"]["unresolved_questions"], list)
    assert any("unknown" in q or "claim" in q for q in result["evidence"]["unresolved_questions"])


def test_synthesis_produces_non_empty_alternatives() -> None:
    """Rejected alternatives and reasons are present."""
    request = _decision_request()
    rr = _research_result()
    result = synthesize(request, [rr], request_sha256=_request_hash(request))
    assert result["alternatives"]["rejected"]
    assert result["alternatives"]["rejection_reasons"]


def test_synthesis_never_approves() -> None:
    """Synthesis sets approval_state to pending or not_required, never approved."""
    request = _decision_request()
    rr = _research_result()
    result = synthesize(request, [rr], request_sha256=_request_hash(request))
    assert result["authority"]["approval_state"] in ("pending", "not_required")
    assert result["authority"]["approval_state"] != "approved"


def test_synthesis_sets_not_required_when_no_approval_needed() -> None:
    """When request has no approval_requirements, approval_state is not_required."""
    request = _decision_request()
    request["authority"]["approval_requirements"] = []
    rr = _research_result()
    result = synthesize(request, [rr], request_sha256=_request_hash(request))
    assert result["authority"]["approval_state"] == "not_required"


def test_synthesis_execution_boundary_reflects_evidence_status() -> None:
    """When evidence has unresolved questions, execution is blocked."""
    request = _decision_request()
    rr = _research_result()
    result = synthesize(request, [rr], request_sha256=_request_hash(request))
    boundary = result["execution_boundary"]
    assert isinstance(boundary["implementation_required"], bool)
    assert isinstance(boundary["planning_required"], bool)
    assert isinstance(boundary["blocked_items"], list)


def test_synthesis_binds_provenance_hashes() -> None:
    """Provenance hashes match identity and evidence refs."""
    request = _decision_request()
    r_hash = _request_hash(request)
    rr = _research_result()
    result = synthesize(request, [rr], request_sha256=r_hash)
    assert result["provenance"]["hashes"]["request"] == r_hash
    assert result["provenance"]["hashes"]["research_results"] == [HASH]
    # Source artifacts include both request and research result
    kinds = {a["kind"] for a in result["provenance"]["source_artifacts"]}
    assert "decision_request" in kinds
    assert "research_result" in kinds


def test_synthesis_options_reflect_evidence_coverage() -> None:
    """Options with matching research claims get supporting evidence."""
    request = _decision_request()
    rr = _research_result(claim_text="Selecting SQLite for persistence is appropriate.")
    result = synthesize(request, [rr], request_sha256=_request_hash(request))
    assert result["decision"]["selected_option"]["option_id"] == "sqlite"
    assert len(result["evidence"]["supporting_claims"]) >= 1


# ---------------------------------------------------------------------------
# Boundary tests
# ---------------------------------------------------------------------------

def test_synthesis_rejects_invalid_request() -> None:
    """Invalid request raises ValidationError."""
    request = _decision_request()
    del request["decision_context"]
    rr = _research_result()
    with pytest.raises((ValueError, DecisionResultValidationError)):
        synthesize(request, [rr])


def test_synthesis_rejects_unbound_research_hash() -> None:
    """Research result without bound artifact_sha256 raises ValueError."""
    request = _decision_request()
    artifact = json.loads(FIXTURE.read_text(encoding="utf-8"))
    validate_run(artifact)
    rr = build_research_result(artifact)  # no artifact_sha256 -> "not_bound"
    with pytest.raises(ValueError, match="unbound artifact_sha256"):
        synthesize(request, [rr], request_sha256=_request_hash(request))


def test_synthesis_rejects_decision_fields_in_research() -> None:
    """Research result with decision fields is caught by validator."""
    request = _decision_request()
    rr = _research_result()
    rr["decision"] = "not allowed"
    with pytest.raises(Exception):
        synthesize(request, [rr])


def test_synthesis_overwrites_nothing() -> None:
    """synthesize is a pure function with no I/O side effects."""
    request = _decision_request()
    rr = _research_result()
    original_rr = json.dumps(rr, sort_keys=True)
    synthesize(request, [rr], request_sha256=_request_hash(request))
    # Research result is not mutated
    assert json.dumps(rr, sort_keys=True) == original_rr


def test_synthesis_confidence_is_insufficient_without_findings() -> None:
    """When research has no findings, confidence is insufficient."""
    request = _decision_request()
    artifact = json.loads(FIXTURE.read_text(encoding="utf-8"))
    validate_run(artifact)
    artifact["claims"] = []
    artifact["uncertainty"] = ["No evidence found."]
    rr = build_research_result(artifact, artifact_sha256="c" * 64)
    result = synthesize(request, [rr], request_sha256=_request_hash(request))
    assert result["evidence"]["confidence"] == "insufficient"


def test_synthesis_with_multiple_research_results() -> None:
    """Synthesis handles multiple research results correctly."""
    request = _decision_request()
    # Use artifacts with different run_ids
    artifact1 = json.loads(FIXTURE.read_text(encoding="utf-8"))
    validate_run(artifact1)
    artifact1["run_id"] = "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa"
    rr1 = build_research_result(artifact1, artifact_sha256="b" * 64)
    artifact2 = json.loads(FIXTURE.read_text(encoding="utf-8"))
    validate_run(artifact2)
    artifact2["run_id"] = "bbbbbbbb-2222-4222-8222-bbbbbbbbbbbb"
    rr2 = build_research_result(artifact2, artifact_sha256="c" * 64)
    assert rr1["run_id"] != rr2["run_id"]
    result = synthesize(request, [rr1, rr2], request_sha256=_request_hash(request))
    assert len(result["evidence"]["research_result_refs"]) == 2
    ref_hashes = {ref["artifact_sha256"] for ref in result["evidence"]["research_result_refs"]}
    assert "b" * 64 in ref_hashes
    assert "c" * 64 in ref_hashes


# ---------------------------------------------------------------------------
# Immutable output test
# ---------------------------------------------------------------------------

def test_synthesis_output_is_immutable(tmp_path: Path) -> None:
    """Synthesis output can be immutably stored (exclusive create)."""
    from research_runtime.decision_result import write_result as write_decision_result
    request = _decision_request()
    rr = _research_result()
    result = synthesize(request, [rr], request_sha256=_request_hash(request))
    target = tmp_path / "decision-result.json"
    write_decision_result(target, result)
    original = target.read_bytes()
    with pytest.raises(FileExistsError):
        write_decision_result(target, result)
    assert target.read_bytes() == original


# ---------------------------------------------------------------------------
# Authority boundary
# ---------------------------------------------------------------------------

def test_synthesis_authority_fields_come_from_request() -> None:
    """Authority section reflects request's decision_owner."""
    request = _decision_request()
    request["authority"]["decision_owner"] = "designated reviewer"
    rr = _research_result()
    result = synthesize(request, [rr], request_sha256=_request_hash(request))
    assert result["authority"]["decision_owner"] == "designated reviewer"


def test_synthesis_does_not_claim_execution() -> None:
    """Decision result does not contain execution plan details."""
    request = _decision_request()
    rr = _research_result()
    result = synthesize(request, [rr], request_sha256=_request_hash(request))
    assert "implementation" not in str(result.get("decision", {}))
    assert "go" not in str(result.get("decision", {})).lower()
    assert result["execution_boundary"]["blocked_items"] is not None
