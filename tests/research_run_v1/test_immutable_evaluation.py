from __future__ import annotations

import json
import sys

import pytest

from research_runtime.immutable_evaluation import ImmutableRunStore, build_comparison, verify_manifest


def _run(run_id: str) -> dict:
    return {
        "run_id": run_id,
        "cases": [{"case_id": "c", "reconciliation": {"outcome": "survived", "changed": False}}],
        "providers": {"mmx": {}, "brave": {}, "qmd": {}},
        "provenance": {"corpus_sha256": "same", "policy_sha256": "same"},
    }


def test_run_store_is_exclusive_and_manifest_hashes_files(tmp_path):
    store = ImmutableRunStore("run-a", root=tmp_path)
    store.write_json("evidence/result.json", {"query": "bounded"})
    manifest_path, manifest_hash = store.manifest(run_metadata={"run_id": "run-a", "immutable": True})
    assert manifest_path.exists()
    assert len(manifest_hash) == 64
    with pytest.raises(FileExistsError):
        ImmutableRunStore("run-a", root=tmp_path)
    with pytest.raises(FileExistsError):
        store.write_json("evidence/result.json", {"query": "overwrite"})
    manifest = verify_manifest(manifest_path, expected_sha256=manifest_hash)
    assert manifest["immutable"] is True
    (store.run_dir / "evidence" / "result.json").write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="manifest_file_hash_mismatch"):
        verify_manifest(manifest_path, expected_sha256=manifest_hash)


def test_comparison_binds_runs_and_marks_live_conditions_partial():
    comparison = build_comparison(baseline=_run("baseline"), candidate=_run("candidate"), baseline_manifest_hash="a" * 64, candidate_manifest_hash="b" * 64)
    assert comparison["baseline_run_id"] == "baseline"
    assert comparison["candidate_manifest_sha256"] == "b" * 64
    assert comparison["comparability"]["corpus"] == "directly_comparable"
    assert comparison["comparability"]["execution_conditions"] == "partially_comparable"
    assert comparison["historical_context"]["lost_phase2a_artifact"] is True
