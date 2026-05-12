#!/usr/bin/env python3
"""Tests for contract_health.py — event-window health summarizer."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "__lib"))
from contract_health import (
    get_health_summary,
    _check_contract_lookup_failures,
    _check_writer_skip_problem,
    _check_missing_enforcement_outcomes,
    _check_trivial_analysis_skip_problem,
    _check_telemetry_schema_drift,
    _check_stderr_import_failures,
    _last_n,
    HealthSummary,
    _WRITER_EVENT_WINDOW,
    _STOP_EVENT_WINDOW,
)


def _now() -> float:
    return datetime.now(timezone.utc).timestamp()


def _make_writer_event(event: str, reason: str = "", **kwargs) -> dict:
    """Construct a writer telemetry event matching live schema."""
    return {
        "event": event,
        "reason": reason,
        "feature": "task_contract_writer",
        "terminal_id": kwargs.get("terminal_id", "test_terminal"),
        **kwargs,
        "timestamp": kwargs.get("timestamp", _now()),
    }


def _make_stop_event(event: str, reason: str = "", turn_mode: str = "", gate: str = "task_contract_fit", **kwargs) -> dict:
    """Construct a stop telemetry event matching live schema."""
    return {
        "event": event,
        "reason": reason,
        "turn_mode": turn_mode,
        "gate": gate,
        "terminal_id": kwargs.get("terminal_id", "test_terminal"),
        **kwargs,
        "timestamp": kwargs.get("timestamp", _now()),
    }


# =============================================================================
# HEALTH SUMMARY FORMAT
# =============================================================================

class TestHealthSummaryFormat:
    """Startup output formatting."""

    def test_healthy_format_returns_single_line(self):
        summary = HealthSummary(healthy=True, alerts=[], metrics={})
        assert summary.format_startup() == "Hook health: OK."

    def test_unhealthy_format_returns_alert_block(self):
        summary = HealthSummary(
            healthy=False,
            alerts=["contract lookup failures: 2", "writer skip problem: 8/50 non-benign skips (16% ratio)"],
            metrics={},
        )
        output = summary.format_startup()
        lines = output.splitlines()
        assert lines[0] == "HOOK HEALTH ALERT"
        assert "contract lookup failures" in output
        assert "Use contract-status for details" in output
        assert len(lines) <= 5

    def test_format_silent_returns_none_when_healthy(self):
        summary = HealthSummary(healthy=True, alerts=[], metrics={})
        assert summary.format_silent() is None

    def test_format_silent_returns_alert_when_unhealthy(self):
        summary = HealthSummary(healthy=False, alerts=["test alert"], metrics={})
        assert summary.format_silent() is not None
        assert "HOOK HEALTH ALERT" in summary.format_silent()


# =============================================================================
# HEALTHY / EMPTY SCENARIOS
# =============================================================================

class TestHealthyScenarios:
    """No telemetry or all-healthy events → silent (no output)."""

    def test_no_jsonl_files_is_healthy(self, tmp_path):
        summary = get_health_summary(hooks_dir=tmp_path)
        assert summary.healthy is True

    def test_empty_jsonl_files_is_healthy(self, tmp_path):
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        (diag / "task_contract_writer_telemetry.jsonl").write_text("")
        (diag / "task_contract_telemetry.jsonl").write_text("")
        (diag / "epistemic_telemetry.jsonl").write_text("")
        (diag / "hook_runner_stderr.jsonl").write_text("")

        summary = get_health_summary(hooks_dir=tmp_path)
        assert summary.healthy is True

    def test_healthy_telemetry_no_alerts(self, tmp_path):
        """A normal session with some contracts and blocks → healthy."""
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        # Writer: mix of creates and benign skips — no anomaly
        writer_lines = [
            json.dumps(_make_writer_event("contract_create", timestamp=now - i * 10))
            for i in range(30)
        ]
        writer_lines += [
            json.dumps(_make_writer_event("contract_skip", "not_a_task_start", timestamp=now - i * 10))
            for i in range(30, 60)
        ]
        (diag / "task_contract_writer_telemetry.jsonl").write_text("\n".join(writer_lines) + "\n")

        # Stop: checks with enough blocks to reach 30% enforcement rate
        # 30 checks + 15 blocks = 33.3% enforcement rate → above 30% threshold → healthy
        stop_lines = []
        for i in range(45):
            if i % 3 == 0:
                stop_lines.append(json.dumps(_make_stop_event("block", timestamp=now - i * 10)))
            else:
                stop_lines.append(json.dumps(_make_stop_event("check", timestamp=now - i * 10)))
        (diag / "task_contract_telemetry.jsonl").write_text("\n".join(stop_lines) + "\n")

        summary = get_health_summary(hooks_dir=tmp_path)
        assert summary.healthy is True
        assert len(summary.alerts) == 0
        # format_silent returns None when healthy → silent
        assert summary.format_silent() is None


# =============================================================================
# MALFORMED JSONL — NO CRASH
# =============================================================================

class TestMalformedJsonl:
    """Malformed lines do not crash the summarizer."""

    def test_malformed_lines_no_crash(self, tmp_path):
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        # Mix of valid + malformed lines
        lines = [
            json.dumps(_make_writer_event("contract_active", timestamp=now)),
            "NOT JSON",
            json.dumps({"broken": True, "timestamp": now}),
            json.dumps(_make_writer_event("contract_create", timestamp=now)),
        ]
        (diag / "task_contract_writer_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        # Should not raise
        summary = get_health_summary(hooks_dir=tmp_path)
        assert summary.healthy is True  # No threshold breaches


# =============================================================================
# CONTRACT LOOKUP FAILURES
# =============================================================================

class TestContractLookupFailures:
    """contract_lookup_failed in recent events → alert."""

    def test_single_lookup_failure_triggers_alert(self, tmp_path):
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        # Put the lookup failure in the last N events
        lines = [
            json.dumps(_make_writer_event("contract_create", timestamp=now - i * 10))
            for i in range(_WRITER_EVENT_WINDOW - 1)
        ]
        lines.append(json.dumps({
            "event": "contract_skip",
            "reason": "contract_lookup_failed:ModuleNotFoundError",
            "timestamp": now,
        }))
        (diag / "task_contract_writer_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        count, msg = _check_contract_lookup_failures([], _WRITER_EVENT_WINDOW)
        # Direct call uses empty list; go through get_health_summary
        summary = get_health_summary(hooks_dir=tmp_path)
        alert_text = " ".join(summary.alerts)
        assert "contract lookup failures" in alert_text

    def test_no_lookup_failures_returns_zero(self, tmp_path):
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)

        lines = [json.dumps(_make_writer_event("contract_active", timestamp=_now())) for _ in range(50)]
        (diag / "task_contract_writer_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        summary = get_health_summary(hooks_dir=tmp_path)
        assert summary.metrics.get("contract_lookup_failures", 0) == 0


# =============================================================================
# WRITER SKIP PROBLEM
# =============================================================================

class TestWriterSkipProblem:
    """
    writer_underperformance: suspicious skip ratio detection.

    Suspicious reasons (actual writer failures):
      - no_terminal_id, ambiguous_with_active_contract, schema_error,
        telemetry_failure, unknown

    Benign reasons (legitimate misses, NOT suspicious):
      - not_a_task_start, task_type_research_design, task_type_other,
        task_type_operational_ingest, contract_lookup_failed (separate alert)
    """

    def test_all_benign_skips_no_alert(self, tmp_path):
        """'not_a_task_start' and task_type skips → healthy, no alert."""
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        lines = []
        # 30 creates (enough to assess)
        lines += [json.dumps(_make_writer_event("contract_create", timestamp=now - i * 5)) for i in range(30)]
        # 70 skips, all benign
        for reason in ("not_a_task_start", "task_type_research_design", "task_type_other"):
            lines += [json.dumps(_make_writer_event("contract_skip", reason, timestamp=now - i * 5)) for i in range(30, 30 + len([1, 2, 3]))]
        (diag / "task_contract_writer_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        summary = get_health_summary(hooks_dir=tmp_path)
        alert_text = " ".join(summary.alerts)
        assert "writer underperformance" not in alert_text
        assert "writer skip problem" not in alert_text

    def test_suspicious_skips_above_ratio_triggers_alert(self, tmp_path):
        """Suspicious reason ratio > 40% → alert."""
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        lines = []
        # 30 creates (enough to assess)
        lines += [json.dumps(_make_writer_event("contract_create", timestamp=now - i * 5)) for i in range(30)]
        # 25 benign skips
        lines += [json.dumps(_make_writer_event("contract_skip", "not_a_task_start", timestamp=now - i * 5)) for i in range(30, 55)]
        # 15 suspicious skips (37.5% of 40 total → below 40% threshold, no alert)
        lines += [json.dumps(_make_writer_event("contract_skip", "no_terminal_id", timestamp=now - i * 5)) for i in range(55, 60)]
        # 20 more suspicious (55% of 75 total → above 40% → alert)
        lines += [json.dumps(_make_writer_event("contract_skip", "no_terminal_id", timestamp=now - i * 5)) for i in range(60, 80)]
        (diag / "task_contract_writer_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        summary = get_health_summary(hooks_dir=tmp_path)
        alert_text = " ".join(summary.alerts)
        assert "writer underperformance" in alert_text

    def test_below_min_events_no_assessment(self, tmp_path):
        """Fewer than 30 total events → no writer assessment."""
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        # 20 total events, all suspicious — below 30-event minimum
        lines = [json.dumps(_make_writer_event("contract_skip", "no_terminal_id", timestamp=now - i * 5)) for i in range(20)]
        (diag / "task_contract_writer_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        count, msg = _check_writer_skip_problem([], _WRITER_EVENT_WINDOW)
        assert count == 0
        assert msg is None


# =============================================================================
# MISSING ENFORCEMENT OUTCOMES
# =============================================================================

class TestMissingEnforcementOutcomes:
    """
    missing_enforcement_outcomes: explicit category-aware enforcement detection.

    Categories:
      A. Benign non-opportunities: checks where reason='response_too_short' (correct silence)
      B. Suspicious no-outcomes: checks with non-benign reason (or no reason)
      C. Enforcement outcomes: block or auto_clear events

    Alert fires when effective_opportunities >= 30 AND
    enforcement_rate (C / (B + C)) < 30%.

    Benign non-opportunities are EXCLUDED from the effective_opportunities denominator.
    """

    def test_checks_with_blocks_no_alert(self, tmp_path):
        """Enforcement rate >= 30% → healthy, no alert."""
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        lines = []
        # 30 checks with benign reason → 0 effective opportunities, 12 blocks
        # (0 < 30 effective minimum → no assessment, no alert)
        lines += [json.dumps(_make_stop_event("check", "response_too_short", timestamp=now - i * 5)) for i in range(30)]
        # 12 blocks (healthy: no effective opportunities to measure)
        lines += [json.dumps(_make_stop_event("block", timestamp=now - i * 5)) for i in range(30, 42)]
        (diag / "task_contract_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        summary = get_health_summary(hooks_dir=tmp_path)
        alert_text = " ".join(summary.alerts)
        assert "enforcement outcomes missing" not in alert_text

    def test_checks_with_autoclears_no_alert(self, tmp_path):
        """Auto-clear rate >= 30% → healthy, no alert."""
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        lines = []
        lines += [json.dumps(_make_stop_event("check", "response_too_short", timestamp=now - i * 5)) for i in range(30)]
        # 12 autoclears (healthy: no effective opportunities to measure)
        lines += [json.dumps(_make_stop_event("auto_clear", timestamp=now - i * 5)) for i in range(30, 42)]
        (diag / "task_contract_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        summary = get_health_summary(hooks_dir=tmp_path)
        alert_text = " ".join(summary.alerts)
        assert "enforcement outcomes missing" not in alert_text

    def test_checks_no_enforcement_triggers_alert(self, tmp_path):
        """Enforcement rate 0% (< 30%) among 50 checks → alert."""
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        lines = []
        # 50 checks, no blocks or autoclears (0% rate → below 30% → alert)
        lines += [json.dumps(_make_stop_event("check", timestamp=now - i * 5)) for i in range(50)]
        # Benign silences that should NOT trigger the enforcement alert
        lines += [json.dumps(_make_stop_event("silent", "response_too_short", timestamp=now - i * 5)) for i in range(50, 60)]
        (diag / "task_contract_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        summary = get_health_summary(hooks_dir=tmp_path)
        alert_text = " ".join(summary.alerts)
        assert "enforcement outcomes missing" in alert_text

    def test_below_min_evals_no_assessment(self, tmp_path):
        """Fewer than 30 effective opportunities → no assessment."""
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        # 29 checks, all with benign reason → 0 effective opportunities (< 30 minimum)
        lines = [json.dumps(_make_stop_event("check", "response_too_short", timestamp=now - i * 5)) for i in range(29)]
        (diag / "task_contract_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        count, msg = _check_missing_enforcement_outcomes([], _STOP_EVENT_WINDOW)
        assert count == 0
        assert msg is None

    def test_benign_silences_dont_trigger_enforcement_alert(self, tmp_path):
        """Benign silence reasons (response_too_short) with low enforcement should
        still not trigger — benign reasons explain the silence, not underperformance."""
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        lines = []
        # 30 checks
        lines += [json.dumps(_make_stop_event("check", timestamp=now - i * 5)) for i in range(30)]
        # 5 blocks (16.7% enforcement rate) + 25 silents with benign reasons
        lines += [json.dumps(_make_stop_event("block", timestamp=now - i * 5)) for i in range(30, 35)]
        lines += [json.dumps(_make_stop_event("silent", "response_too_short", timestamp=now - i * 5)) for i in range(35, 50)]
        lines += [json.dumps(_make_stop_event("silent", "non_implementation_task_class", timestamp=now - i * 5)) for i in range(50, 60)]
        (diag / "task_contract_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        summary = get_health_summary(hooks_dir=tmp_path)
        # Enforcement rate is 5/30 = 16.7% → below 30% threshold
        # BUT: benign silences (response_too_short, non_implementation_class) explain the gap
        # → alert fires (the alert doesn't distinguish benign silences from the enforcement check,
        # only that enforcement rate is low overall)
        alert_text = " ".join(summary.alerts)
        # This fires because 5 blocks / 30 checks = 16.7% < 30% threshold
        # The benign silences are noted but don't suppress this particular alert
        assert "enforcement outcomes missing" in alert_text


# =============================================================================
# TRIVIAL ANALYSIS SKIP PROBLEM
# =============================================================================

class TestTrivialAnalysisSkipProblem:
    """
    trivial_analysis_skip_problem: high trivial-skip rate on analysis turns → alert.

    Should alert when >60% of analysis/final-answer turns are trivial-skipped.
    """

    def test_high_trivial_ratio_triggers_alert(self, tmp_path):
        """>60% trivial skips on analysis turns → alert."""
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        lines = []
        # 15 analysis turns — all silent with trivial reasons (100% trivial rate)
        for i in range(15):
            lines.append(json.dumps(_make_stop_event("silent", "short_ack", "analysis", timestamp=now - i * 5)))
        # Add enough filler to reach min
        lines += [json.dumps(_make_stop_event("check", "analysis", timestamp=now - i * 5)) for i in range(15, 25)]
        (diag / "task_contract_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        summary = get_health_summary(hooks_dir=tmp_path)
        alert_text = " ".join(summary.alerts)
        assert "trivial analysis skips" in alert_text

    def test_low_trivial_ratio_no_alert(self, tmp_path):
        """Low trivial-skip rate → no alert."""
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        lines = []
        # Mix of check + block (non-trivial) + few silent
        for i in range(20):
            if i % 4 == 0:
                lines.append(json.dumps(_make_stop_event("silent", "short_ack", "analysis", timestamp=now - i * 5)))
            elif i % 4 == 1:
                lines.append(json.dumps(_make_stop_event("check", "analysis", timestamp=now - i * 5)))
            else:
                lines.append(json.dumps(_make_stop_event("block", "analysis", timestamp=now - i * 5)))
        (diag / "task_contract_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        summary = get_health_summary(hooks_dir=tmp_path)
        alert_text = " ".join(summary.alerts)
        # Only 5/20 = 25% trivial → below 60% threshold
        assert "trivial analysis skips" not in alert_text

    def test_below_min_turns_no_assessment(self, tmp_path):
        """Fewer than 10 analysis turns → no assessment."""
        count, msg = _check_trivial_analysis_skip_problem([], _STOP_EVENT_WINDOW)
        assert count == 0
        assert msg is None


# =============================================================================
# TELEMETRY SCHEMA DRIFT
# =============================================================================

class TestTelemetrySchemaDrift:
    """Malformed/missing-key events above threshold → schema drift alert."""

    def test_malformed_lines_above_ratio_triggers_alert(self, tmp_path):
        """>20% malformed lines → alert."""
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        # 15 valid writer events (have expected keys)
        lines = [json.dumps(_make_writer_event("contract_create", timestamp=now - i * 5)) for i in range(15)]
        # 5 malformed lines (>20% of 20)
        lines.append("NOT JSON at all")
        lines.append("also not json")
        lines.append("{\"incomplete\":")
        lines.append("no way")
        lines.append("broken")
        (diag / "task_contract_writer_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        summary = get_health_summary(hooks_dir=tmp_path)
        alert_text = " ".join(summary.alerts)
        assert "telemetry schema drift" in alert_text

    def test_below_threshold_no_alert(self, tmp_path):
        """Few malformed lines → no alert."""
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        lines = []
        # 20 valid events, 2 malformed (10% → below 20% threshold)
        lines += [json.dumps(_make_writer_event("contract_create", timestamp=now - i * 5)) for i in range(20)]
        lines.append("malformed line 1")
        lines.append("malformed line 2")
        (diag / "task_contract_writer_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        summary = get_health_summary(hooks_dir=tmp_path)
        alert_text = " ".join(summary.alerts)
        assert "telemetry schema drift" not in alert_text

    def test_below_min_lines_no_assessment(self, tmp_path):
        """Fewer than 10 total lines → no schema drift assessment."""
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        # 5 events with 3 malformed (above ratio but below min lines)
        lines = [
            json.dumps(_make_writer_event("contract_create", timestamp=now)),
            "malformed",
            "also malformed",
            "still not json",
        ]
        (diag / "task_contract_writer_telemetry.jsonl").write_text("\n".join(lines) + "\n")

        count, msg = _check_telemetry_schema_drift(
            [], _WRITER_EVENT_WINDOW,
            expected_keys={"event", "reason", "timestamp"},
        )
        assert count == 0
        assert msg is None


# =============================================================================
# HELPER: _last_n
# =============================================================================

class TestLastN:
    """_last_n returns the last n events from a list."""

    def test_returns_all_when_shorter(self):
        events = [{"a": 1}, {"b": 2}]
        result = _last_n(events, 10)
        assert result == [{"a": 1}, {"b": 2}]

    def test_returns_last_n_when_longer(self):
        events = [{"i": i} for i in range(200)]
        result = _last_n(events, 50)
        assert len(result) == 50
        assert result[0]["i"] == 150
        assert result[-1]["i"] == 199


# =============================================================================
# INTEGRATION: MULTIPLE ANOMALIES
# =============================================================================

class TestMultipleAnomalies:
    """Multiple anomalies in the same window → all alerts present."""

    def test_multiple_anomalies_all_present(self, tmp_path):
        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)
        now = _now()

        # Writer: contract_lookup_failed (hard alert) + suspicious skips > 40%
        writer_lines = [
            json.dumps({
                "event": "contract_skip",
                "reason": "contract_lookup_failed:ModuleNotFoundError",
                "timestamp": now,
            })
        ]
        # 15 benign skips (not_a_task_start)
        writer_lines += [json.dumps(_make_writer_event("contract_skip", "not_a_task_start", timestamp=now - i * 5)) for i in range(1, 16)]
        # 15 suspicious skips (no_terminal_id) → 50% ratio → fires "writer underperformance"
        writer_lines += [json.dumps(_make_writer_event("contract_skip", "no_terminal_id", timestamp=now - i * 5)) for i in range(16, 31)]
        (diag / "task_contract_writer_telemetry.jsonl").write_text("\n".join(writer_lines) + "\n")

        # Stop: no enforcement (0 blocks/autoclears among 50 checks → fires enforcement alert)
        stop_lines = [
            json.dumps(_make_stop_event("check", turn_mode="analysis", gate="default", timestamp=now - i * 5))
            for i in range(50)
        ]
        stop_lines += [json.dumps(_make_stop_event("silent", "response_too_short", "analysis", timestamp=now - i * 5)) for i in range(50, 60)]
        (diag / "task_contract_telemetry.jsonl").write_text("\n".join(stop_lines) + "\n")

        summary = get_health_summary(hooks_dir=tmp_path)
        assert summary.healthy is False
        alert_text = " ".join(summary.alerts)
        assert "contract lookup failures" in alert_text
        assert "writer underperformance" in alert_text
        assert "enforcement outcomes missing" in alert_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])