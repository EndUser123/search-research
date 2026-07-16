"""Bounded, non-search MMX runtime-state observation.

This module performs only executable/version, authentication-status, and quota
checks. It never invokes an MMX research command and does not persist output.
Callers may translate the returned observation into the pure router's
``CapabilityRecord``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from .router import CapabilityRecord


MMX_LANE = "mmx"
DEFAULT_VALIDITY_SECONDS = 300
CommandRunner = Callable[[Sequence[str], int], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class MMXObservation:
    provider: str
    observed_at: str
    valid_until: str
    executable_path: str | None
    executable_version: str | None
    capability_check: str
    authentication_state: str
    quota: dict[str, Any] | None
    quota_interpretation: str
    readiness: str
    observation_method: str
    errors: tuple[str, ...] = ()
    scope: str = "account-token-plan-model-group"
    command_results: tuple[dict[str, Any], ...] = ()
    quota_scope: str = "shared_account"
    concurrent_consumers_possible: bool = True
    quota_delta_attributable_to_current_run: bool = False
    current_run_top_level_calls: int = 0

    @property
    def ready(self) -> bool:
        return self.readiness == "ready"

    def to_capability(self) -> CapabilityRecord:
        """Return a router record without copying secret-bearing CLI output."""

        remaining = None
        if self.quota:
            remaining = min(
                self.quota["interval_remaining_percent"],
                self.quota["weekly_remaining_percent"],
            )
        return CapabilityRecord(
            lane=MMX_LANE,
            role="SEARCH_DISCOVERY",
            independence_group="external_search",
            capabilities=frozenset({"external_discovery", "current_web", "independent_recall", "broad_discovery", "conceptual_discovery", "candidate_generation"}),
            ready=self.ready,
            authenticated=self.authentication_state == "authenticated",
            automatic=True,
            authority="advisory",
            quota_remaining_percent=remaining,
            readiness_observed_at=self.observed_at,
            readiness_valid_until=self.valid_until,
            observation_method=self.observation_method,
            recent_anomaly=bool(self.errors) or self.readiness != "ready",
            recent_verified_value=self.executable_version,
            supported_roles=frozenset({
                "BROAD_EXTERNAL_DISCOVERY", "CONCEPTUAL_RECALL",
                "EXPLORATORY_RESEARCH", "CANDIDATE_GENERATION", "GENERAL_WEB_RESEARCH",
            }),
        )

    def quota_telemetry(
        self,
        *,
        current_run_top_level_calls: int = 0,
        shared_quota_before: dict[str, Any] | None = None,
        shared_quota_after: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return truthful shared-quota metadata without attributing deltas.

        Before/after observations are retained for visibility only. Other
        terminals may consume the same account between observations, so this
        adapter never computes or labels a per-run quota cost.
        """
        return {
            "quota_scope": self.quota_scope,
            "concurrent_consumers_possible": self.concurrent_consumers_possible,
            "quota_delta_attributable_to_current_run": False,
            "current_run_top_level_calls": current_run_top_level_calls,
            "shared_quota_before": shared_quota_before,
            "shared_quota_after": shared_quota_after,
            "quota_delta_interpretation": "indeterminate_concurrent_usage",
        }


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _default_runner(command: Sequence[str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        shell=False,
    )


def _resolve_executable(executable: str | None) -> str | None:
    if executable:
        path = Path(executable)
        return str(path.resolve()) if path.exists() else None
    return shutil.which("mmx.cmd") or shutil.which("mmx.exe") or shutil.which("mmx")


def _json_result(result: subprocess.CompletedProcess[str]) -> tuple[dict[str, Any] | None, str | None]:
    try:
        parsed = json.loads(result.stdout)
    except (TypeError, json.JSONDecodeError):
        return None, "malformed_json"
    if not isinstance(parsed, dict):
        return None, "malformed_json_shape"
    return parsed, None


def _result_meta(command: Sequence[str], started: datetime, ended: datetime, result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "command": " ".join(command),
        "started_at": _iso(started),
        "ended_at": _iso(ended),
        "exit_code": result.returncode,
        "stdout_bytes": len(result.stdout.encode("utf-8", "replace")),
        "stderr_bytes": len(result.stderr.encode("utf-8", "replace")),
    }


def _run(command: Sequence[str], timeout: int, runner: CommandRunner, started: datetime) -> tuple[subprocess.CompletedProcess[str] | None, dict[str, Any], str | None]:
    try:
        result = runner(command, timeout)
    except subprocess.TimeoutExpired:
        ended = _now()
        return None, {"command": " ".join(command), "started_at": _iso(started), "ended_at": _iso(ended), "exit_code": None, "timeout": True}, "timeout"
    except OSError as exc:
        ended = _now()
        return None, {"command": " ".join(command), "started_at": _iso(started), "ended_at": _iso(ended), "exit_code": None}, f"execution_error:{type(exc).__name__}"
    ended = _now()
    return result, _result_meta(command, started, ended, result), None if result.returncode == 0 else f"exit_code:{result.returncode}"


def _quota(parsed: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    rows = parsed.get("model_remains")
    if not isinstance(rows, list) or not rows:
        return None, "quota_missing_model_remains"
    intervals: list[float] = []
    weekly: list[float] = []
    groups: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            return None, "quota_row_invalid"
        i = row.get("current_interval_remaining_percent")
        w = row.get("current_weekly_remaining_percent")
        if not isinstance(i, (int, float)) or isinstance(i, bool) or not 0 <= i <= 100:
            return None, "quota_interval_percent_invalid"
        if not isinstance(w, (int, float)) or isinstance(w, bool) or not 0 <= w <= 100:
            return None, "quota_weekly_percent_invalid"
        interval_total = row.get("current_interval_total_count")
        interval_usage = row.get("current_interval_usage_count")
        weekly_total = row.get("current_weekly_total_count")
        weekly_usage = row.get("current_weekly_usage_count")
        for total, usage, label in (
            (interval_total, interval_usage, "interval"),
            (weekly_total, weekly_usage, "weekly"),
        ):
            if total is not None or usage is not None:
                if not isinstance(total, (int, float)) or not isinstance(usage, (int, float)) or usage < 0 or total < 0 or usage > total:
                    return None, f"quota_{label}_counts_contradictory"
        intervals.append(float(i))
        weekly.append(float(w))
        groups.append(str(row.get("model_name", "unknown")))
    if len(set(intervals)) > 1 and len(set(weekly)) > 1:
        interpretation = "conservative_minimum_across_model_groups"
    else:
        interpretation = "reported_model_group_values"
    return {
        "interval_remaining_percent": min(intervals),
        "weekly_remaining_percent": min(weekly),
        "model_groups": groups,
        "reset_or_window_fields_present": all(
            isinstance(row, dict) and row.get("start_time") is not None and row.get("end_time") is not None
            for row in rows
        ),
    }, interpretation


def observe_mmx(
    executable: str | None = None,
    *,
    timeout_seconds: int = 15,
    validity_seconds: int = DEFAULT_VALIDITY_SECONDS,
    now: datetime | None = None,
    runner: CommandRunner = _default_runner,
) -> MMXObservation:
    """Observe MMX without research execution or persistent caching."""

    observed = now or _now()
    valid_until = observed + timedelta(seconds=validity_seconds)
    path = _resolve_executable(executable)
    errors: list[str] = []
    results: list[dict[str, Any]] = []
    if not path:
        return MMXObservation(
            provider="mmx",
            observed_at=_iso(observed),
            valid_until=_iso(valid_until),
            executable_path=None,
            executable_version=None,
            capability_check="unavailable",
            authentication_state="unknown",
            quota=None,
            quota_interpretation="unavailable",
            readiness="unavailable",
            observation_method="mmx-state-v1",
            errors=("executable_missing",),
            command_results=(),
        )

    version_command = (path, "--version")
    started = _now()
    version_result, meta, error = _run(version_command, timeout_seconds, runner, started)
    results.append(meta)
    version = version_result.stdout.strip() if version_result and not error else None
    if error or not version or not version.lower().startswith("mmx "):
        errors.append(error or "version_shape_unsupported")

    auth_command = (path, "auth", "status", "--output", "json", "--quiet")
    started = _now()
    auth_result, meta, error = _run(auth_command, timeout_seconds, runner, started)
    results.append(meta)
    auth, auth_error = _json_result(auth_result) if auth_result and not error else (None, error)
    authenticated = bool(auth and auth.get("method") and auth.get("source"))
    if auth_error:
        errors.append(f"authentication:{auth_error}")
    elif not authenticated:
        errors.append("authentication_not_established")

    quota_command = (path, "quota", "show", "--output", "json", "--quiet")
    started = _now()
    quota_result, meta, error = _run(quota_command, timeout_seconds, runner, started)
    results.append(meta)
    quota_json, quota_error = _json_result(quota_result) if quota_result and not error else (None, error)
    if quota_json and quota_json.get("base_resp", {}).get("status_code", 0) != 0:
        quota_value, quota_interpretation = None, "quota_status_not_success"
        quota_error = f"quota_status_code:{quota_json.get('base_resp', {}).get('status_code')}"
    else:
        quota_value, quota_interpretation = _quota(quota_json) if quota_json else (None, "unavailable")
    if quota_error:
        errors.append(f"quota:{quota_error}")
    elif quota_value is None:
        errors.append(f"quota:{quota_interpretation}")

    readiness = "ready" if not errors and authenticated and quota_value else "unknown"
    if any(item.startswith("authentication:exit_code:401") for item in errors):
        readiness = "unavailable"
    if any(item.startswith("quota:") for item in errors) and authenticated:
        readiness = "degraded"
    return MMXObservation(
        "mmx", _iso(observed), _iso(valid_until), path, version, "available", "authenticated" if authenticated else "unknown",
        quota_value, quota_interpretation, readiness, "mmx-state-v1", tuple(errors), command_results=tuple(results),
    )
