from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from research_runtime.mmx_state import observe_mmx  # noqa: E402
from research_runtime.router import TaskSignals, recommend  # noqa: E402


NOW = datetime(2026, 7, 13, 13, 0, tzinfo=timezone.utc)
MMX = r"C:\Users\brsth\AppData\Roaming\npm\mmx.cmd"


def _quota(interval: object = 93, weekly: object = 100) -> str:
    interval = "null" if interval is None else interval
    weekly = "null" if weekly is None else weekly
    return '{"model_remains":[{"model_name":"general","start_time":1,"end_time":2,"current_interval_remaining_percent":%s,"current_weekly_remaining_percent":%s}],"base_resp":{"status_code":0}}' % (interval, weekly)


def _runner(outputs: dict[str, str], exit_codes: dict[str, int] | None = None):
    exit_codes = exit_codes or {}

    def run(command: tuple[str, ...], timeout: int) -> subprocess.CompletedProcess[str]:
        key = " ".join(command[1:3]) if len(command) > 2 else command[1]
        return subprocess.CompletedProcess(command, exit_codes.get(key, 0), outputs.get(key, ""), "")

    return run


def _healthy_runner():
    return _runner({"--version": "mmx 1.0.16\n", "auth status": '{"method":"api-key","source":"config.json","key":"sk-c...a5z8"}', "quota show": _quota()})


def test_healthy_observation_is_fresh_and_router_ready_without_persisting_credentials() -> None:
    observation = observe_mmx(MMX, now=NOW, runner=_healthy_runner())

    assert observation.readiness == "ready"
    assert observation.executable_version == "mmx 1.0.16"
    assert observation.quota["interval_remaining_percent"] == 93
    assert observation.to_capability().ready
    assert all("key" not in str(item).lower() for item in observation.command_results)


def test_missing_executable_is_unavailable() -> None:
    observation = observe_mmx("C:\\does-not-exist\\mmx.cmd", now=NOW)

    assert observation.readiness == "unavailable"
    assert observation.errors == ("executable_missing",)


def test_changed_version_shape_is_not_ready() -> None:
    runner = _runner({"--version": "MiniMax CLI\n", "auth status": '{"method":"api-key","source":"config.json"}', "quota show": _quota()})

    observation = observe_mmx(MMX, now=NOW, runner=runner)

    assert observation.readiness == "unknown"
    assert "version_shape_unsupported" in observation.errors


def test_unauthenticated_response_is_not_ready() -> None:
    runner = _runner({"--version": "mmx 1.0.16\n", "auth status": '{"authenticated":false}', "quota show": _quota()})

    observation = observe_mmx(MMX, now=NOW, runner=runner)

    assert observation.readiness == "unknown"
    assert "authentication_not_established" in observation.errors


def test_malformed_quota_is_degraded_and_not_router_ready() -> None:
    runner = _runner({"--version": "mmx 1.0.16\n", "auth status": '{"method":"api-key","source":"config.json"}', "quota show": "not-json"})

    observation = observe_mmx(MMX, now=NOW, runner=runner)

    assert observation.readiness == "degraded"
    assert "quota:malformed_json" in observation.errors
    assert not observation.to_capability().ready


def test_missing_and_contradictory_quota_values_are_rejected() -> None:
    missing = _runner({"--version": "mmx 1.0.16\n", "auth status": '{"method":"api-key","source":"config.json"}', "quota show": _quota(None, 100)})
    contradictory = _runner({"--version": "mmx 1.0.16\n", "auth status": '{"method":"api-key","source":"config.json"}', "quota show": '{"model_remains":[{"model_name":"general","start_time":1,"end_time":2,"current_interval_remaining_percent":50,"current_weekly_remaining_percent":100,"current_interval_total_count":100,"current_interval_usage_count":120}]}'})

    missing_observation = observe_mmx(MMX, now=NOW, runner=missing)
    contradictory_observation = observe_mmx(MMX, now=NOW, runner=contradictory)

    assert missing_observation.readiness == "degraded"
    assert "quota:quota_interval_percent_invalid" in missing_observation.errors
    assert contradictory_observation.readiness == "degraded"
    assert "quota:quota_interval_counts_contradictory" in contradictory_observation.errors


def test_nonzero_quota_status_is_not_treated_as_success() -> None:
    runner = _runner({"--version": "mmx 1.0.16\n", "auth status": '{"method":"api-key","source":"config.json"}', "quota show": '{"model_remains":[],"base_resp":{"status_code":1001}}'})

    observation = observe_mmx(MMX, now=NOW, runner=runner)

    assert observation.readiness == "degraded"
    assert "quota:quota_status_code:1001" in observation.errors


def test_quota_command_failure_and_timeout_are_visible() -> None:
    failed = _runner({"--version": "mmx 1.0.16\n", "auth status": '{"method":"api-key","source":"config.json"}', "quota show": ""}, {"quota show": 1})
    timed_out = _runner({"--version": "mmx 1.0.16\n", "auth status": '{"method":"api-key","source":"config.json"}', "quota show": ""})

    def timeout_runner(command: tuple[str, ...], timeout: int) -> subprocess.CompletedProcess[str]:
        if command[1:3] == ("quota", "show"):
            raise subprocess.TimeoutExpired(command, timeout)
        return _healthy_runner()(command, timeout)

    failed_observation = observe_mmx(MMX, now=NOW, runner=failed)
    timeout_observation = observe_mmx(MMX, now=NOW, runner=timeout_runner)

    assert "quota:exit_code:1" in failed_observation.errors
    assert "quota:timeout" in timeout_observation.errors


def test_below_reserve_is_preserved_for_the_router() -> None:
    runner = _runner({"--version": "mmx 1.0.16\n", "auth status": '{"method":"api-key","source":"config.json"}', "quota show": _quota(5, 100)})

    observation = observe_mmx(MMX, now=NOW, runner=runner)
    capability = observation.to_capability()

    assert observation.readiness == "ready"
    assert capability.quota_remaining_percent == 5
    result = recommend(TaskSignals(needs_current_web=True, needs_independent_recall=True), (capability,))
    assert not result.recommendations
    assert "quota_below_reserve" in result.rejected[0].reasons


def test_shared_quota_is_not_attributed_to_this_run() -> None:
    observation = observe_mmx(MMX, now=NOW, runner=_healthy_runner())
    telemetry = observation.quota_telemetry(
        current_run_top_level_calls=3,
        shared_quota_before={"interval_remaining_percent": 80},
        shared_quota_after={"interval_remaining_percent": 70},
    )

    assert telemetry["quota_scope"] == "shared_account"
    assert telemetry["concurrent_consumers_possible"] is True
    assert telemetry["current_run_top_level_calls"] == 3
    assert telemetry["quota_delta_attributable_to_current_run"] is False
    assert telemetry["quota_delta_interpretation"] == "indeterminate_concurrent_usage"
