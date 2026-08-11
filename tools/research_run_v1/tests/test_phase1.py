from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from research_runtime.mmx_state import MMXObservation  # noqa: E402
from research_runtime.phase1 import (  # noqa: E402
    LaneExecution,
    NormalizedResult,
    build_artifact,
    execute_mmx_search,
    execute_parallel,
    normalize_mmx_results,
    open_source,
)
from research_runtime.router import TaskSignals  # noqa: E402
from research_runtime.validator import validate  # noqa: E402


NOW = "2026-07-13T13:00:00Z"


def healthy_observation() -> MMXObservation:
    return MMXObservation(
        provider="mmx", observed_at=NOW, valid_until="2026-07-13T13:05:00Z", executable_path="C:\\mmx.cmd", executable_version="mmx 1.0.16", capability_check="available", authentication_state="authenticated", quota={"interval_remaining_percent": 93, "weekly_remaining_percent": 100}, quota_interpretation="reported", readiness="ready", observation_method="test", command_results=(),
    )


def healthy_runner(command: tuple[str, ...], timeout: int) -> subprocess.CompletedProcess[str]:
    assert command[1:3] == ("search", "query")
    return subprocess.CompletedProcess(command, 0, json.dumps({"organic": [{"title": "Python docs", "link": "https://docs.python.org/3/library/pathlib.html", "snippet": "Object-oriented filesystem paths.", "date": ""}]}), "")


def test_router_rejection_prevents_provider_invocation() -> None:
    calls: list[tuple[str, ...]] = []

    def runner(command: tuple[str, ...], timeout: int) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        raise AssertionError("rejected provider was invoked")

    observation = healthy_observation()
    result = execute_mmx_search("pathlib", TaskSignals(needs_current_web=True, evidence_sufficient=True), observation, runner=runner)

    assert result.status == "not_attempted"
    assert not calls


def test_stale_state_does_not_reach_execution() -> None:
    stale = MMXObservation(
        provider="mmx", observed_at="2026-07-13T12:00:00Z", valid_until="2026-07-13T12:01:00Z", executable_path="C:\\mmx.cmd", executable_version="mmx 1.0.16", capability_check="available", authentication_state="authenticated", quota={"interval_remaining_percent": 93, "weekly_remaining_percent": 100}, quota_interpretation="reported", readiness="ready", observation_method="test", command_results=(),
    )
    calls: list[tuple[str, ...]] = []

    def runner(command: tuple[str, ...], timeout: int) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        raise AssertionError("stale provider was invoked")

    result = execute_mmx_search("pathlib", TaskSignals(needs_current_web=True), stale, runner=runner)

    assert result.status == "not_attempted"
    assert not calls


def test_healthy_mmx_reaches_execution_and_normalizes_duplicates() -> None:
    result = execute_mmx_search("pathlib", TaskSignals(needs_current_web=True, needs_independent_recall=True, as_of=NOW), healthy_observation(), runner=healthy_runner)

    assert result.status == "success"
    assert len(result.results) == 1
    assert result.results[0].result_type == "discovery_candidate"
    assert result.results[0].provider == "mmx"

    normalized = normalize_mmx_results("pathlib", {"organic": [{"title": "A", "link": "https://example.com/x/", "snippet": ""}, {"title": "A duplicate", "link": "https://example.com/x", "snippet": "other"}]})
    assert len(normalized) == 1


def test_one_failure_does_not_hide_success_and_parallel_wave_is_bounded() -> None:
    def success() -> LaneExecution:
        return LaneExecution("mmx", "mmx", "discovery", "q", "success", NOW, NOW, results=(NormalizedResult("mmx", "discovery", "q", "r", "A", "https://example.com", "s", None, NOW),))

    def failure() -> LaneExecution:
        return LaneExecution("local", "local-qmd", "context_retrieval", "q", "failed", NOW, NOW, failures=({"outcome": "unavailable"},))

    results = execute_parallel((("mmx", success), ("local", failure)))
    assert [item.lane_id for item in results] == ["local", "mmx"]
    assert next(item for item in results if item.lane_id == "local").failures
    assert next(item for item in results if item.lane_id == "mmx").results


def test_opened_primary_source_is_distinguishable_and_verifiable(tmp_path: Path) -> None:
    result = NormalizedResult("mmx", "discovery", "q", "r", "Python docs", "https://docs.python.org/3/library/pathlib.html", "snippet", None, NOW)

    opened = open_source(result, tmp_path, opener=lambda url, timeout: (200, "text/html", b"Object-oriented filesystem paths."), verification_text="Object-oriented filesystem paths")

    assert opened.status == "anchor_confirmed"
    assert opened.body_path and Path(opened.body_path).is_file()
    lane = LaneExecution("mmx", "mmx", "discovery", "q", "success", NOW, NOW, results=(result,))
    artifact = build_artifact(run_id="33333333-4444-4555-8666-777777777777", question="q", requested_decision="d", workspace_revision="test", lanes=(lane,), opened=(opened,), observation=healthy_observation(), output_path=tmp_path / "research-run.json")
    validate(artifact)
    assert artifact["assessments"][0]["assessment_method"] == "deterministic_anchor_only"
    assert artifact["claims"][0]["status"] == "supported"
    telemetry = artifact["runtime"]["provider_state"]["quota_telemetry"]
    assert telemetry["quota_scope"] == "shared_account"
    assert telemetry["quota_delta_attributable_to_current_run"] is False
    assert telemetry["current_run_top_level_calls"] == 1


def test_failed_source_opening_remains_discovery_only_and_artifact_validates(tmp_path: Path) -> None:
    result = NormalizedResult("mmx", "discovery", "q", "r", "Candidate", "https://example.com", "snippet", None, NOW)
    lane = LaneExecution("mmx", "mmx", "discovery", "q", "success", NOW, NOW, results=(result,))
    opened = open_source(result, tmp_path / "sources", opener=lambda url, timeout: (503, "text/html", b""))
    artifact = build_artifact(run_id="11111111-2222-4333-8444-555555555555", question="q", requested_decision="d", workspace_revision="test", lanes=(lane,), opened=(opened,), observation=healthy_observation(), output_path=tmp_path / "research-run.json")

    validate(artifact)
    assert artifact["sources"][0]["discovery_status"] == "discovery_only"
    assert artifact["authorization_supported"] is False


def test_artifact_has_no_secret_material_and_reserved_disconfirmation_is_not_executed(tmp_path: Path) -> None:
    artifact = build_artifact(run_id="22222222-3333-4444-8555-666666666666", question="q", requested_decision="d", workspace_revision="test", lanes=(), opened=(), observation=healthy_observation(), output_path=tmp_path / "research-run.json")
    serialized = json.dumps(artifact)
    assert "api_key" not in serialized.lower()
    assert "disconfirmation" not in serialized.lower()
    # No implicit lane exists: an empty explicit wave performs no invocation.
    assert execute_parallel(()) == ()
