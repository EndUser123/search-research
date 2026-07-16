from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from research_runtime.validator import ValidationError, validate, validate_file, write_run


FIXTURES = ROOT / "tests" / "research_run_v1" / "fixtures"


def test_valid_fixture() -> None:
    validate_file(FIXTURES / "valid.json")


def test_empty_lane_is_valid_and_explicit() -> None:
    validate_file(FIXTURES / "empty-lane.json")


def test_discovery_only_cannot_be_used_as_verified_claim_support() -> None:
    artifact = json.loads((FIXTURES / "valid.json").read_text(encoding="utf-8"))
    artifact["sources"][0]["discovery_status"] = "discovery_only"
    artifact["claims"][0]["status"] = "verified"
    with pytest.raises(ValidationError):
        validate(artifact)


def test_unknown_source_reference_is_rejected() -> None:
    artifact = json.loads((FIXTURES / "valid.json").read_text(encoding="utf-8"))
    artifact["claims"][0]["supporting_source_ids"] = ["missing"]
    with pytest.raises(ValidationError):
        validate(artifact)


def test_duplicate_write_does_not_overwrite(tmp_path: Path) -> None:
    artifact = json.loads((FIXTURES / "valid.json").read_text(encoding="utf-8"))
    target = tmp_path / "run.json"
    write_run(target, artifact)
    with pytest.raises(FileExistsError):
        write_run(target, artifact)


def _agy_artifact(tmp_path: Path, *, status: str = "success") -> dict:
    invocation_id = "11111111-2222-4333-8444-555555555555"
    evidence = tmp_path / invocation_id
    evidence.mkdir(parents=True)
    packet = evidence / "invocation-packet.json"
    packet.write_text(json.dumps({"invocation_id": invocation_id}), encoding="utf-8")
    paths = {}
    for name, content in {
        "metadata.json": "{}",
        "stdout.txt": "finding",
        "stderr.txt": "",
        "internal.log": "runtime",
        "findings.json": "[{\"candidate\": \"x\"}]" if status == "success" else "[]",
    }.items():
        path = evidence / name
        path.write_text(content, encoding="utf-8")
        paths[name.split(".")[0]] = str(path)
    return {
        "schema_version": "research-run.v1",
        "run_id": "99999999-8888-4777-8666-555555555555",
        "created_at": "2026-07-13T13:00:00Z",
        "research_question": "bounded agy test",
        "requested_decision": "evidence only",
        "authorization_level_sought": "evidence_gathering",
        "workspace": {"root": "P:/", "revision": "test"},
        "authority": {"producer": "test", "acquisition": "test", "serialization": "JSON", "storage": "test", "consumer": "test", "trust": "test", "scope": "run", "lifetime": "run", "collision": "fail", "failure": "record", "retention": "policy"},
        "runtime": {"role": "AGY_SEARCH_INDEPENDENT", "status": status, "authorization_supported": False, "backend_model_identity": "unproven", "invocation_id": invocation_id, "packet_path": str(packet), "packet_sha256": hashlib.sha256(packet.read_bytes()).hexdigest(), "metadata_path": paths["metadata"], "stdout_path": paths["stdout"], "stderr_path": paths["stderr"], "internal_log_path": paths["internal"], "findings_path": paths["findings"], "exit_code": 0 if status == "success" else 1, "timeout_triggered": False},
        "retrieval_lanes": [{"lane_id": "agy", "provider": "agy", "independence_group": "agy-advisory", "query": "test", "status": "success" if status == "success" else "failed", "started_at": "2026-07-13T13:00:00Z", "finished_at": "2026-07-13T13:00:01Z", "sources": ["s"] if status == "success" else [], "failures": [] if status == "success" else [{"outcome": "researcher_unavailable"}]}],
        "sources": [{"source_id": "s", "lane_id": "agy", "title": "test source", "url": "https://example.com", "source_type": "primary", "discovery_status": "verified", "retrieved_at": "2026-07-13T13:00:01Z", "retrieval_method": "test", "opened_at": "2026-07-13T13:00:01Z", "opened_by": "test", "verified_at": "2026-07-13T13:00:01Z", "verification_method": "test", "evidence_paths": [paths["stdout"]]}],
        "claims": [], "uncertainty": ["test"], "stop_reason": "test", "authorization_supported": False,
    }


def test_agy_success_requires_bound_nonempty_findings(tmp_path: Path) -> None:
    artifact = _agy_artifact(tmp_path)
    validate(artifact)
    artifact["runtime"]["findings_path"] = str(tmp_path / "missing" / "findings.json")
    with pytest.raises(ValidationError):
        validate(artifact)


def test_agy_rejects_empty_or_malformed_success_findings(tmp_path: Path) -> None:
    artifact = _agy_artifact(tmp_path)
    Path(artifact["runtime"]["findings_path"]).write_text("[]", encoding="utf-8")
    with pytest.raises(ValidationError):
        validate(artifact)
    artifact = _agy_artifact(tmp_path / "malformed")
    Path(artifact["runtime"]["findings_path"]).write_text("not-json", encoding="utf-8")
    with pytest.raises(ValidationError):
        validate(artifact)


def test_agy_rejects_timeout_and_missing_source_evidence(tmp_path: Path) -> None:
    artifact = _agy_artifact(tmp_path)
    artifact["runtime"]["timeout_triggered"] = True
    with pytest.raises(ValidationError):
        validate(artifact)
    artifact = _agy_artifact(tmp_path / "missing-source-evidence")
    artifact["sources"][0]["evidence_paths"] = [str(tmp_path / "missing-source-evidence" / "missing.txt")]
    with pytest.raises(ValidationError):
        validate(artifact)


def test_agy_rejects_authorization_overreach_and_packet_mismatch(tmp_path: Path) -> None:
    artifact = _agy_artifact(tmp_path)
    artifact["authorization_supported"] = True
    with pytest.raises(ValidationError):
        validate(artifact)
    artifact = _agy_artifact(tmp_path / "second")
    artifact["runtime"]["invocation_id"] = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
    with pytest.raises(ValidationError):
        validate(artifact)


def test_agy_failed_lane_cannot_support_verified_claim(tmp_path: Path) -> None:
    artifact = _agy_artifact(tmp_path, status="failed")
    artifact["sources"] = []
    artifact["claims"] = [{"claim_id": "bad", "text": "bad", "status": "verified", "supporting_source_ids": ["missing"], "contradicting_source_ids": [], "verification_method": "test", "falsifier": "test"}]
    with pytest.raises(ValidationError):
        validate(artifact)
