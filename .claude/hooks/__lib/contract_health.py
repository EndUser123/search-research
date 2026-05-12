#!/usr/bin/env python3
"""
Contract/hook system health summarizer — event-first model.

Refactored from 24h rolling window to event-window-based anomaly detection.
Time is only a weak freshness guard, not the primary filter.

Schema observations (from telemetry inspection 2026-05-11):
  - writer:  event, reason, feature, task_type, task_class, prompt_preview
  - stop:    event, gate, reason, turn_mode, contract_present
  - epistemic: gate, decision, mode, has_format_issues, issue_count
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# === Event-window configuration (primary filter) ===
_WRITER_EVENT_WINDOW = 100   # events per telemetry stream
_STOP_EVENT_WINDOW = 100
_EPISTEMIC_EVENT_WINDOW = 100
_STDERR_EVENT_WINDOW = 50   # hook_runner_stderr.jsonl

# Weak freshness guard: if no events in > N seconds, skip that stream
_FRESHNESS_THRESHOLD_SECONDS = float(
    os.environ.get("CONTRACT_HEALTH_FRESHNESS_SECONDS", "86400")
)

# === Anomaly thresholds ===
_LOOKUP_FAILURE_THRESHOLD = 1   # any recent event → alert

# Writer anomaly: suspicious skip ratio (non-benign skips / total skips)
# Only counts actual writer failures, not legitimate task-type misses.
# "not_a_task_start" is benign (exploratory chatter). Task-type skips are
# legitimate misses on valid task categories. Only failures like "no_terminal_id"
# and "ambiguous_with_active_contract" count as suspicious.
_WRITER_SUSPICIOUS_RATIO = 0.40  # alert if suspicious skips >40% of total skips
_WRITER_MIN_EVENTS_FOR_ASSESSMENT = 30  # don't assess below this

# Stop enforcement anomaly: combined block+autoclear rate
# Healthy usage has many benign silences (response_too_short, non_implementation_class).
# Only alert when checks exist but enforcement is nearly absent.
_STOP_ENFORCEMENT_RATIO = 0.30  # alert if enforcement rate < 30%
_STOP_ENFORCEMENT_MIN_CHECKS = 30  # minimum check events needed for this anomaly

# Explicit benign silence reasons — these are correct behavior, NOT enforcement failures.
# The response was legitimately short/not-a-delivery and the gate correctly stayed silent.
# Do NOT count these in the real-opportunities denominator.
_STOP_BENIGN_SILENCE_REASONS: frozenset[str] = frozenset({
    "response_too_short",
    "non_implementation_task_class",
})

# Trivial analysis skip: analysis/final-answer turns trivial-skipped
_TRIVIAL_ANALYSIS_RATIO = 0.60    # alert if >60% of analysis turns are trivial-skipped
_TRIVIAL_MIN_TURNS = 10           # minimum analysis/final-answer turns needed

# Schema drift
_SCHEMA_DRIFT_RATIO = 0.20        # alert if >20% of lines malformed or missing expected keys
_SCHEMA_DRIFT_MIN_LINES = 10      # minimum total lines needed for this check

# Suspicious skip reasons — actual writer failures, NOT legitimate task misses.
# These are hard-coded at module load to keep the check deterministic.
_WRITER_SUSPICIOUS_REASONS: frozenset[str] = frozenset({
    "no_terminal_id",
    "ambiguous_with_active_contract",
    "schema_error",
    "telemetry_failure",
    "unknown",
})


# === Data structures ===

@dataclass
class HealthSummary:
    healthy: bool
    alerts: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    def format_startup(self) -> str:
        """Compact unhealthy output: 1 header + N alert lines + 1 footer."""
        if self.healthy:
            return "Hook health: OK."
        lines = ["HOOK HEALTH ALERT"]
        for alert in self.alerts:
            lines.append(f"  {alert}")
        lines.append("")
        lines.append("Use contract-status for details")
        return "\n".join(lines)

    def format_silent(self) -> str | None:
        """Returns None when healthy (silent), alert text when unhealthy."""
        if self.healthy:
            return None  # Silent
        return self.format_startup()


# === File reading ===

def _load_jsonl(path: Path) -> list[dict]:
    """Load JSONL, skip malformed lines. Returns empty list if file missing."""
    if not path.exists():
        return []
    events = []
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    events.append({"_malformed": line})
    except (OSError, IOError):
        pass
    return events


def _last_n(events: list[dict], n: int) -> list[dict]:
    """Return the last n events from the list."""
    return events[-n:] if len(events) >= n else events


def _stale_timestamp(ts: float, cutoff: float) -> bool:
    """Return True if timestamp is older than cutoff (weak freshness guard)."""
    return ts < cutoff


# === Anomaly detectors ===

def _check_contract_lookup_failures(events: list[dict], window_n: int) -> tuple[int, str | None]:
    """Check for contract_lookup_failed in recent events (event-window, time as weak guard)."""
    recent = _last_n(events, window_n)
    if not recent:
        return 0, None

    cutoff = datetime.now(timezone.utc).timestamp() - _FRESHNESS_THRESHOLD_SECONDS

    count = 0
    for e in recent:
        ts = e.get("timestamp", 0)
        if ts > 0 and _stale_timestamp(ts, cutoff):
            continue
        reason = e.get("reason", "")
        if "contract_lookup_failed" in str(reason):
            count += 1

    if count >= _LOOKUP_FAILURE_THRESHOLD:
        return count, f"contract lookup failures: {count}"

    return 0, None


def _check_stderr_import_failures(events: list[dict], window_n: int) -> tuple[int, str | None]:
    """Check hook_runner_stderr.jsonl for contract module import failures."""
    recent = _last_n(events, window_n)
    if not recent:
        return 0, None

    count = 0
    for e in recent:
        # Malformed entries
        if "_malformed" in e:
            continue
        msg = e.get("error_text", "") or e.get("message", "") or str(e)
        if "task_contract" in msg.lower() and ("import" in msg.lower() or "module" in msg.lower()):
            count += 1

    if count > 0:
        return count, f"task_contract import failures: {count}"

    return 0, None


def _check_writer_skip_problem(events: list[dict], window_n: int) -> tuple[int, str | None]:
    """
    writer_underperformance: suspicious skip ratio detection.

    Suspicious skips are actual writer failures, NOT legitimate task misses:
      - 'no_terminal_id' — writer could not identify the session/terminal
      - 'ambiguous_with_active_contract' — active contract in flight, skip is correct
      - 'schema_error', 'telemetry_failure' — writer infrastructure failure
      - 'unknown' or empty without any feature signal — malformed event

    NOT suspicious (benign):
      - 'not_a_task_start' — exploratory/casual chat, correctly skipped
      - 'task_type_research_design', 'task_type_other', 'task_type_operational_ingest' —
        legitimate task-type misses on valid categories
      - 'contract_lookup_failed' — separate hard alert, handled by _check_contract_lookup_failures

    Alert triggers when:
      - total events >= _WRITER_MIN_EVENTS_FOR_ASSESSMENT
      - suspicious skip ratio > _WRITER_SUSPICIOUS_RATIO (40%)
    """
    recent = _last_n(events, window_n)
    if len(recent) < _WRITER_MIN_EVENTS_FOR_ASSESSMENT:
        return 0, None

    skips = [e for e in recent if e.get("event") == "contract_skip"]
    total_skips = len(skips)
    if total_skips == 0:
        return 0, None

    suspicious_skips = [e for e in skips if e.get("reason", "") in _WRITER_SUSPICIOUS_REASONS]
    suspicious_count = len(suspicious_skips)

    ratio = suspicious_count / total_skips if total_skips > 0 else 0

    if ratio > _WRITER_SUSPICIOUS_RATIO:
        return suspicious_count, (
            f"writer underperformance: {suspicious_count} suspicious skips / {total_skips} total "
            f"({ratio:.0%} ratio)"
        )

    return 0, None


@dataclass
class StopEnforcementSummary:
    """Explicit category-aware stop enforcement model."""

    # A. Benign non-opportunities: checks where silence is correct behavior
    benign_non_opportunity_count: int = 0

    # B. Suspicious no-outcomes: checks where silence means an opportunity was missed
    suspicious_no_outcome_count: int = 0

    # C. Actual enforcement outcomes
    enforcement_outcomes: int = 0

    @property
    def effective_opportunities(self) -> int:
        """B + C: real enforcement opportunities (not benign non-opportunities)."""
        return self.suspicious_no_outcome_count + self.enforcement_outcomes

    @property
    def enforcement_rate(self) -> float:
        """C / (B + C): fraction of real opportunities that produced an outcome."""
        denom = self.effective_opportunities
        return self.enforcement_outcomes / denom if denom > 0 else 0.0


def _check_missing_enforcement_outcomes(events: list[dict], window_n: int) -> tuple[int, str | None]:
    """
    missing_enforcement_outcomes: explicit category-aware enforcement detection.

    Categories:
      A. Benign non-opportunities — checks where the output was legitimately short
         (reason='response_too_short'); gate correctly stayed silent, not an enforcement fail
      B. Suspicious no-outcomes — checks where gate should have acted but produced neither
         block nor auto_clear nor benign silence
      C. Enforcement outcomes — block or auto_clear events

    Alert triggers when:
      - effective_opportunities >= _STOP_ENFORCEMENT_MIN_CHECKS (B + C >= 30)
      - enforcement_rate (C / (B + C)) < _STOP_ENFORCEMENT_RATIO (30%)

    This replaces the raw (blocks+clears)/checks ratio with a model that explicitly
    excludes benign non-opportunities from the denominator.
    """
    recent = _last_n(events, window_n)

    checks = [e for e in recent if e.get("event") == "check"]
    blocks = [e for e in recent if e.get("event") == "block"]
    autoclears = [e for e in recent if e.get("event") in ("auto_clear", "autoclear")]

    enforcement_outcomes = len(blocks) + len(autoclears)

    benign = 0
    suspicious = 0
    for e in checks:
        reason = e.get("reason", "")
        if reason in _STOP_BENIGN_SILENCE_REASONS:
            benign += 1
        else:
            suspicious += 1

    summary = StopEnforcementSummary(
        benign_non_opportunity_count=benign,
        suspicious_no_outcome_count=suspicious,
        enforcement_outcomes=enforcement_outcomes,
    )

    effective = summary.effective_opportunities
    if effective < _STOP_ENFORCEMENT_MIN_CHECKS:
        return 0, None

    rate = summary.enforcement_rate
    if rate < _STOP_ENFORCEMENT_RATIO:
        return summary.enforcement_outcomes, (
            f"enforcement outcomes missing: {summary.enforcement_outcomes} blocks+clears / "
            f"{effective} effective opportunities ({rate:.0%} enforcement rate, "
            f"{summary.suspicious_no_outcome_count} missed)"
        )

    return 0, None


def _check_trivial_analysis_skip_problem(events: list[dict], window_n: int) -> tuple[int, str | None]:
    """
    trivial_analysis_skip_problem: detect over-softening on analysis/final-answer turns.

    Looks at stop telemetry for 'silent' events on analysis/final-answer turns where
    the reason is a trivial pattern (short_ack, bare_numeric, smoke_test, etc.).

    Alert triggers when:
      - analysis/final-answer turns >= _TRIVIAL_MIN_TURNS
      - trivial-skip ratio > _TRIVIAL_ANALYSIS_RATIO
    """
    recent = _last_n(events, window_n)
    if len(recent) < _TRIVIAL_MIN_TURNS:
        return 0, None

    # Count analysis/final-answer turns
    analysis_turns = []
    for e in recent:
        # Stop telemetry: 'turn_mode' field
        turn_mode = e.get("turn_mode", "")
        if turn_mode in ("analysis", "final-answer", "query"):
            analysis_turns.append(e)

    if len(analysis_turns) < _TRIVIAL_MIN_TURNS:
        return 0, None

    # Identify trivial skips: silent with trivial reason
    trivial_reasons = {
        "short_ack", "bare_numeric", "smoke_test", "control_mode",
        "response_too_short", "not_trivial",
    }
    trivial_skips = [
        e for e in analysis_turns
        if e.get("event") == "silent" and e.get("reason", "") in trivial_reasons
    ]

    total_analysis = len(analysis_turns)
    trivial_count = len(trivial_skips)
    ratio = trivial_count / total_analysis if total_analysis > 0 else 0

    if ratio > _TRIVIAL_ANALYSIS_RATIO:
        return trivial_count, (
            f"trivial analysis skips: {trivial_count}/{total_analysis} analysis turns "
            f"({ratio:.0%} trivial rate)"
        )

    return 0, None


def _check_telemetry_schema_drift(
    events: list[dict],
    window_n: int,
    expected_keys: set[str],
) -> tuple[int, str | None]:
    """
    telemetry_schema_drift: detect when significant fraction of events are malformed
    or missing expected fields (indicates telemetry format changed).

    Alert triggers when:
      - total valid events in window >= _SCHEMA_DRIFT_MIN_LINES
      - malformed OR missing-expected-key ratio > _SCHEMA_DRIFT_RATIO
    """
    recent = _last_n(events, window_n)
    total = len(recent)
    if total < _SCHEMA_DRIFT_MIN_LINES:
        return 0, None

    bad = 0
    for e in recent:
        if "_malformed" in e:
            bad += 1
            continue
        # Check for missing expected fields
        if not expected_keys.issubset(e.keys()):
            bad += 1

    ratio = bad / total if total > 0 else 0
    if ratio > _SCHEMA_DRIFT_RATIO:
        return bad, f"telemetry schema drift: {bad}/{total} events malformed/unknown ({ratio:.0%})"

    return 0, None


# === Public API ===

def get_health_summary(
    *,
    hooks_dir: Path | None = None,
    writer_window: int = _WRITER_EVENT_WINDOW,
    stop_window: int = _STOP_EVENT_WINDOW,
    epistemic_window: int = _EPISTEMIC_EVENT_WINDOW,
    stderr_window: int = _STDERR_EVENT_WINDOW,
) -> HealthSummary:
    """
    Compute health summary using event-window-based anomaly detection.

    Time is only a weak freshness guard (skip events older than 24h).
    The primary filter is the last N events per telemetry stream.

    Args:
        hooks_dir: Path to hooks directory (default: same dir as this module)
        *_window: number of recent events to analyze per stream

    Returns:
        HealthSummary with healthy bool, alerts list, and metrics dict.
        Always returns a valid summary — never raises.
    """
    if hooks_dir is None:
        hooks_dir = Path(__file__).resolve().parent.parent

    diag_dir = hooks_dir / "logs" / "diagnostics"
    writer_log = diag_dir / "task_contract_writer_telemetry.jsonl"
    stop_log = diag_dir / "task_contract_telemetry.jsonl"
    epistemic_log = diag_dir / "epistemic_telemetry.jsonl"
    stderr_log = diag_dir / "hook_runner_stderr.jsonl"

    alerts: list[str] = []
    metrics: dict = {}

    try:
        # ── Writer telemetry ───────────────────────────────────────────────
        writer_events = _load_jsonl(writer_log)
        recent_writer = _last_n(writer_events, writer_window)

        # Schema: event, reason, feature, task_type, task_class, prompt_preview, timestamp
        # contract_lookup_failed may appear as 'reason' on skip events
        count, msg = _check_contract_lookup_failures(writer_events, writer_window)
        if msg:
            alerts.append(msg)
        metrics["contract_lookup_failures"] = count

        count, msg = _check_writer_skip_problem(writer_events, writer_window)
        if msg:
            alerts.append(msg)
        metrics["writer_skip_problem"] = count

        # ── Stop telemetry ─────────────────────────────────────────────────
        stop_events = _load_jsonl(stop_log)
        recent_stop = _last_n(stop_events, stop_window)

        count, msg = _check_missing_enforcement_outcomes(stop_events, stop_window)
        if msg:
            alerts.append(msg)
        metrics["missing_enforcement_outcomes"] = count

        count, msg = _check_trivial_analysis_skip_problem(stop_events, stop_window)
        if msg:
            alerts.append(msg)
        metrics["trivial_analysis_skip_problem"] = count

        # ── Stderr telemetry ───────────────────────────────────────────────
        stderr_events = _load_jsonl(stderr_log)
        count, msg = _check_stderr_import_failures(stderr_events, stderr_window)
        if msg:
            alerts.append(msg)
        metrics["stderr_import_failures"] = count

        # ── Schema drift detection (per stream) ─────────────────────────────
        # Writer expected keys: only universally-present fields (from live inspection 2026-05-11)
        count, msg = _check_telemetry_schema_drift(
            writer_events, writer_window,
            expected_keys={"event", "feature", "terminal_id", "timestamp"},
        )
        if msg:
            alerts.append(msg)
        metrics["writer_schema_drift"] = count

        # Stop expected keys: only universally-present fields
        count, msg = _check_telemetry_schema_drift(
            stop_events, stop_window,
            expected_keys={"event", "gate", "terminal_id", "timestamp"},
        )
        if msg:
            alerts.append(msg)
        metrics["stop_schema_drift"] = count

    except Exception:
        # Fail open — any error means we don't know, so no alerts
        pass

    return HealthSummary(healthy=len(alerts) == 0, alerts=alerts, metrics=metrics)


if __name__ == "__main__":
    summary = get_health_summary()
    silent = summary.format_silent()
    if silent:
        print(silent)
    # else: silent healthy — no output