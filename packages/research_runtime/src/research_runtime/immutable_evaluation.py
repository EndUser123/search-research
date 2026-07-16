"""Immutable run storage and comparison for bounded evaluation smoke runs.

This module owns provenance only. It does not select providers, generate
falsifiers, assess evidence, or alter reconciliation behavior.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).parents[4]
STATE_ROOT = ROOT / "tmp" / ".codex" / "state" / "immutable-evaluations"
LOST_HISTORICAL_ARTIFACT = "The historical Phase 2A artifact was overwritten and cannot be reconstructed."


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(manifest_path: Path, *, expected_sha256: str | None = None) -> dict[str, Any]:
    """Verify the manifest itself and every file hash it binds."""
    actual_manifest_hash = sha256_file(manifest_path)
    if expected_sha256 is not None and actual_manifest_hash != expected_sha256:
        raise ValueError("manifest_hash_mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_dir = manifest_path.parent
    for entry in manifest.get("files", []):
        path = run_dir / entry["path"]
        if not path.is_file() or path.stat().st_size != entry["size"] or sha256_file(path) != entry["sha256"]:
            raise ValueError("manifest_file_hash_mismatch")
    return manifest


def _git_head() -> str | None:
    try:
        return subprocess.check_output(("git", "-C", str(ROOT), "rev-parse", "HEAD"), text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _source_hashes() -> dict[str, str | None]:
    paths = (
        ROOT / "packages" / "research_runtime" / "src" / "research_runtime" / "phase1.py",
        ROOT / "packages" / "research_runtime" / "src" / "research_runtime" / "phase2a.py",
        ROOT / "packages" / "research_runtime" / "src" / "research_runtime" / "evaluate_phase2a.py",
        ROOT / "tests" / "research_run_v1" / "phase2a_corpus.json",
        ROOT / ".artifacts" / "research" / "legacy" / "phase1e-evaluation.json",
    )
    return {str(path.relative_to(ROOT)): sha256_file(path) if path.exists() else None for path in paths}


class ImmutableRunStore:
    """Reserve one run directory and permit each artifact path to be written once."""

    def __init__(self, run_id: str, *, root: Path = STATE_ROOT) -> None:
        self.run_id = run_id
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.run_dir = self.root / run_id
        self.run_dir.mkdir()

    def write_json(self, relative_path: str, value: Any) -> Path:
        path = self.run_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        return path

    def manifest(self, *, run_metadata: dict[str, Any]) -> tuple[Path, str]:
        run_path = self.write_json("run.json", run_metadata)
        entries: list[dict[str, Any]] = []
        for path in sorted(self.run_dir.rglob("*")):
            if path.is_file() and path.name != "manifest.json":
                entries.append({"path": path.relative_to(self.run_dir).as_posix(), "size": path.stat().st_size, "sha256": sha256_file(path)})
        manifest = {
            "schema": "research-run-v1.immutable-manifest",
            "run_id": self.run_id,
            "completed_at": _now(),
            "immutable": True,
            "files": entries,
        }
        manifest_path = self.write_json("manifest.json", manifest)
        return manifest_path, sha256_file(manifest_path)


def _summaries(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "case_id": record["case_id"],
        "action": record["reconciliation"]["revised_action"],
        "outcome": record["reconciliation"]["outcome"],
        "admitted_falsifiers": record["metrics"]["admitted_falsifier_count"],
        "rejected_falsifiers": record["metrics"]["rejected_falsifier_count"],
        "opened_sources": record["metrics"]["additional_source_open_count"],
        "source_open_failures": record["metrics"]["source_open_failures"],
        "elapsed_ms": record["metrics"]["total_run_time_ms"],
    } for record in records]


def build_comparison(*, baseline: dict[str, Any], candidate: dict[str, Any], baseline_manifest_hash: str, candidate_manifest_hash: str) -> dict[str, Any]:
    baseline_cases = {case["case_id"]: case for case in baseline["cases"]}
    candidate_cases = {case["case_id"]: case for case in candidate["cases"]}
    same_cases = set(baseline_cases) == set(candidate_cases)
    same_corpus = baseline["provenance"]["corpus_sha256"] == candidate["provenance"]["corpus_sha256"]
    same_policy = baseline["provenance"]["policy_sha256"] == candidate["provenance"]["policy_sha256"]
    same_provider_names = set(baseline["providers"]) == set(candidate["providers"])
    return {
        "schema": "research-run-v1.immutable-comparison",
        "comparison_id": f"cmp-{uuid.uuid4()}",
        "created_at": _now(),
        "immutable": True,
        "baseline_run_id": baseline["run_id"],
        "baseline_manifest_sha256": baseline_manifest_hash,
        "candidate_run_id": candidate["run_id"],
        "candidate_manifest_sha256": candidate_manifest_hash,
        "historical_context": {"lost_phase2a_artifact": True, "statement": LOST_HISTORICAL_ARTIFACT},
        "comparability": {
            "provider_set": "directly_comparable" if same_provider_names else "not_comparable",
            "corpus": "directly_comparable" if same_cases and same_corpus else "not_comparable",
            "policy": "directly_comparable" if same_policy else "not_comparable",
            "execution_conditions": "partially_comparable",
            "source_results": "partially_comparable",
            "reason": "Both prospective runs use the same implementation and corpus, but external search results, quota state, and timing are live and can vary.",
        },
        "cases": [{
            "case_id": case_id,
            "baseline": baseline_cases[case_id]["reconciliation"],
            "candidate": candidate_cases[case_id]["reconciliation"],
        } for case_id in sorted(baseline_cases.keys() & candidate_cases.keys())],
    }


def run_smoke() -> dict[str, Any]:
    """Run two prospective, isolated baseline/candidate evaluations."""
    from .brave_lane import observe_brave
    from .evaluate_phase1e import _load_brave_key
    from .evaluate_phase2a import CORPUS, _baseline_index, _measure_case
    from .mmx_state import observe_mmx

    cases = json.loads(CORPUS.read_text(encoding="utf-8"))
    selected = [case for case in cases if case["id"] in {"windows-lifecycle-defects", "official-source-comparison"}]
    baseline_index = _baseline_index()
    brave_key = _load_brave_key()
    records: list[dict[str, Any]] = []
    completed: list[tuple[dict[str, Any], str]] = []
    for label in ("baseline", "candidate"):
        run_id = f"phase2a-{label}-20260714-{uuid.uuid4().hex[:12]}"
        store = ImmutableRunStore(run_id)
        started = _now()
        mmx = observe_mmx(r"C:\Users\brsth\AppData\Roaming\npm\mmx.cmd")
        brave = observe_brave(api_key=brave_key)
        run_records = [_measure_case(case, baseline_index, mmx, brave, brave_key, store.run_dir / "evidence") for case in selected]
        run_payload = {
            "schema": "research-run-v1.immutable-run",
            "run_id": run_id,
            "run_label": label,
            "started_at": started,
            "completed_at": _now(),
            "immutable": True,
            "providers": {
                "mmx": {"readiness": mmx.readiness, "executable_path": mmx.executable_path, "version": mmx.executable_version, "quota": mmx.quota, "quota_attribution": "indeterminate_shared_account"},
                "brave": {"readiness": brave.readiness},
                "qmd": {"role": "local_context_only", "calls": len(run_records)},
            },
            "cases": run_records,
            "provenance": {
                "python_executable": sys.executable,
                "pid": os.getpid(),
                "git_head": _git_head(),
                "corpus_sha256": sha256_file(CORPUS),
                "policy_sha256": sha256_file(ROOT / "packages" / "research_runtime" / "src" / "research_runtime" / "phase2a.py"),
                "source_hashes": _source_hashes(),
                "historical_phase2a_artifact_reconstructable": False,
                "historical_phase2a_artifact_note": LOST_HISTORICAL_ARTIFACT,
            },
        }
        manifest_path, manifest_hash = store.manifest(run_metadata=run_payload)
        run_payload["manifest"] = {"path": str(manifest_path.relative_to(ROOT)), "sha256": manifest_hash}
        # run.json is already immutable; the manifest is the authoritative binding.
        records.append(run_payload)
        completed.append((run_payload, manifest_hash))
    baseline, baseline_hash = completed[0]
    candidate, candidate_hash = completed[1]
    comparison = build_comparison(baseline=baseline, candidate=candidate, baseline_manifest_hash=baseline_hash, candidate_manifest_hash=candidate_hash)
    comparison_store = ImmutableRunStore(comparison["comparison_id"])
    comparison_path = comparison_store.write_json("comparison.json", comparison)
    comparison["artifact_path"] = str(comparison_path.relative_to(ROOT))
    return {"baseline": baseline, "candidate": candidate, "comparison": comparison}


if __name__ == "__main__":
    result = run_smoke()
    print(json.dumps({"baseline": result["baseline"]["run_id"], "candidate": result["candidate"]["run_id"], "comparison": result["comparison"]["comparison_id"], "artifact": result["comparison"]["artifact_path"]}, indent=2))
