from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from research_runtime.research_result import (
    ResearchResultValidationError,
    build_research_result,
    validate,
    write_result,
)
from research_runtime.validator import validate as validate_run

ROOT = Path(__file__).parents[2]
FIXTURE = ROOT / "tests" / "research_run_v1" / "fixtures" / "valid.json"


def _artifact() -> dict:
    artifact = json.loads(FIXTURE.read_text(encoding="utf-8"))
    validate_run(artifact)
    return artifact


def test_projection_serializes_and_round_trips() -> None:
    artifact = _artifact()
    result = build_research_result(artifact, artifact_sha256="a" * 64)
    validate(result)
    assert json.loads(json.dumps(result)) == result
    assert result["source_schema_version"] == "research-run.v1"


def test_provenance_and_claim_identity_are_preserved() -> None:
    artifact = _artifact()
    result = build_research_result(artifact, artifact_sha256="b" * 64)
    assert result["run_id"] == artifact["run_id"]
    assert result["provenance"]["artifact_sha256"] == "b" * 64
    assert [s["source_id"] for s in result["provenance"]["sources"]] == [s["source_id"] for s in artifact["sources"]]
    assert [f["claim_id"] for f in result["findings"]] == [c["claim_id"] for c in artifact["claims"]]


def test_claims_do_not_become_a_decision() -> None:
    result = build_research_result(_artifact())
    assert "decision" not in result
    assert "chosen_option" not in result
    assert result["options"] == []
    assert result["authorization"]["research_may_decide"] is False


def test_unresolved_evidence_is_preserved() -> None:
    artifact = _artifact()
    artifact["claims"] = []
    artifact["uncertainty"] = ["primary source not opened"]
    result = build_research_result(artifact)
    assert "primary source not opened" in result["unresolved_questions"]
    assert any("No claim-specific" in item for item in result["unresolved_questions"])


def test_schema_rejects_decision_and_missing_provenance() -> None:
    result = build_research_result(_artifact())
    bad = copy.deepcopy(result)
    bad["decision"] = "choose A"
    with pytest.raises(ResearchResultValidationError):
        validate(bad)
    bad = copy.deepcopy(result)
    del bad["provenance"]["sources"]
    with pytest.raises(ResearchResultValidationError):
        validate(bad)


def test_backward_compatible_with_existing_run_fixture() -> None:
    result = build_research_result(_artifact())
    validate(result)
    assert result["options"] == []
    assert result["context"]["assumptions"] == []


def test_result_storage_is_immutable(tmp_path: Path) -> None:
    result = build_research_result(_artifact())
    target = tmp_path / "research-result.json"
    write_result(target, result)
    original = target.read_bytes()
    with pytest.raises(FileExistsError):
        write_result(target, result)
    assert target.read_bytes() == original
