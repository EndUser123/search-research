from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).parents[2]
PLUGIN = ROOT / "packages" / ".claude-marketplace" / "plugins" / "search-research"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PLUGIN))

from research_runtime.phase1 import run_phase1  # noqa: E402
from research_runtime.router import TaskSignals  # noqa: E402
from skills.all.search_executor import _phase1_task_signals, execute_phase1_for_all  # noqa: E402


def test_all_signal_translation_keeps_consequential_work_non_adversarial():
    ordinary = _phase1_task_signals("research production readiness", "auto")
    explicit = _phase1_task_signals("research production readiness and red-team this", "auto")

    assert ordinary.needs_adversarial_review is False
    assert explicit.needs_adversarial_review is True
    assert ordinary.decision_impact == "high"


def test_phase1_writes_run_scoped_artifact_and_preserves_qmd_failure(tmp_path: Path):
    artifact, artifact_path = run_phase1(
        question="workspace context smoke",
        query="workspace context smoke",
        requested_decision="research_evidence",
        workspace_revision="test-revision",
        caller="search-research:/all",
        signals=TaskSignals(
            needs_local_context=True,
            authorization_level="evidence_gathering",
            as_of="2026-07-14T00:00:00Z",
        ),
        output_root=tmp_path,
        qmd_path=str(tmp_path / "missing-qmd.exe"),
        wiki_root=tmp_path / "wiki",
    )

    assert artifact_path == tmp_path / artifact["run_id"] / "research-run.json"
    assert artifact_path.is_file()
    assert artifact["caller"] == "search-research:/all"
    assert artifact["authority"]["scope"] == f"run:{artifact['run_id']}"
    assert artifact["retrieval_lanes"][0]["failures"]
    assert artifact["phase2a"] == {"requested": False, "executed": False, "activation": "explicit_only"}
    json.loads(artifact_path.read_text(encoding="utf-8"))


def test_explicit_challenge_reuses_manual_phase2a_runner(tmp_path: Path):
    called: list[str] = []
    artifact, _ = run_phase1(
        question="challenge this conclusion",
        query="challenge this conclusion",
        requested_decision="research_evidence",
        workspace_revision="test-revision",
        caller="search-research:/all",
        signals=TaskSignals(
            needs_adversarial_review=True,
            authorization_level="evidence_gathering",
            as_of="2026-07-14T00:00:00Z",
        ),
        output_root=tmp_path,
        manual_disconfirmation_runner=lambda: called.append("phase2a") or {"schema": "research-run-v1.phase2a-evaluation"},
    )

    assert called == ["phase2a"]
    assert artifact["phase2a"] == {"requested": True, "executed": True, "activation": "explicit_only", "result_schema": "research-run-v1.phase2a-evaluation"}


def test_all_consumes_exact_returned_artifact_path(monkeypatch, tmp_path: Path):
    expected = tmp_path / "exact" / "research-run.json"

    def fake_run(*, question, query, requested_decision, workspace_revision, caller, signals, caller_run_id):
        return ({
            "sources": [{"title": "opened", "snippet": "evidence", "provider": "qmd", "url": "qmd://wiki/a.md", "source_id": "s1", "discovery_status": "opened"}],
            "runtime": {"status": "success", "provider_state": {"errors": []}},
            "retrieval_lanes": [],
        }, expected)

    monkeypatch.setattr("research_runtime.phase1.run_phase1", fake_run)
    results, path = asyncio.run(execute_phase1_for_all("workspace context", "local-only"))

    assert path == str(expected)
    assert results[0].metadata["artifact_path"] == str(expected)
    assert "newest" not in Path(PLUGIN / "skills" / "all" / "search_executor.py").read_text(encoding="utf-8").lower()


def test_mixed_requirements_compose_local_and_external_lanes(tmp_path: Path):
    artifact, _ = run_phase1(
        question="mixed",
        query="mixed",
        requested_decision="research_evidence",
        workspace_revision="test-revision",
        caller="search-research:/all",
        signals=TaskSignals(
            needs_current_web=True,
            needs_local_context=True,
            requested_roles=frozenset({"IMPLEMENTATION_DISCOVERY"}),
            allow_parallel=True,
            parallel_trigger="distinct_complementary_roles",
            authorization_level="evidence_gathering",
            as_of="2026-07-14T00:00:00Z",
        ),
        output_root=tmp_path,
        mmx_observation=None,
        brave_observation=None,
    )

    assert artifact["routing"]["stop_reason"] == "bounded_parallel_wave"
    assert artifact["routing"]["required_capabilities"] == [
        "evidence_assessment",
        "external_discovery",
        "implementation_discovery",
        "local_context",
        "source_opening",
    ]
    assert set(artifact["routing"]["recommendations"]) == {"local", "brave"}
    assert artifact["routing"]["execution_wave"] == "bounded_parallel"
