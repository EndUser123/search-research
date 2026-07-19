"""Tests for the Textual-based ornith-monitor dashboard.

These tests verify the DATA-GATHERING layer (read_snapshot, _update_metrics,
metric parsing) produces the same results as the original ctypes-based
dashboard. The rendering layer (Textual widgets) is framework-managed and
not unit-tested here.
"""
from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT = Path(__file__).with_name("ornith-monitor-textual.py")
SPEC = importlib.util.spec_from_file_location("ornith_monitor_textual", SCRIPT)
assert SPEC and SPEC.loader
monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(monitor)


def test_read_snapshot_returns_expected_fields():
    """read_snapshot should return all fields the dashboard needs."""
    # Use a non-existent endpoint so we get a BROKEN state (no network dependency)
    snapshot = monitor.read_snapshot(
        "http://127.0.0.1:99999",  # nothing listening
        Path("P:/.claude/state/local-model-state.json"),
        Path("P:/tmp/test-metrics.json"),
        "http://127.0.0.1:99999",  # CCR also unreachable
    )
    required_fields = [
        "model", "state", "slot", "task", "activity",
        "prompt_total", "prompt_processed", "prompt_progress",
        "decoded", "remaining", "metrics", "ccr_metrics",
        "gpu", "temperature", "vram", "context",
        "started", "checked",
    ]
    for field in required_fields:
        assert field in snapshot, f"Missing field: {field}"
    assert snapshot["state"] in ("LOADED", "BROKEN", "UNKNOWN")


def test_update_metrics_counts_task_transition_once(tmp_path):
    """_update_metrics should count a task transition exactly once."""
    metrics_file = tmp_path / "metrics.json"
    first = monitor._update_metrics(metrics_file, False, None, 0, 0, 0)
    second = monitor._update_metrics(metrics_file, True, "task-1", 100, 10, 5)
    assert second["requests"] == 1
    third = monitor._update_metrics(metrics_file, True, "task-1", 100, 20, 10)
    assert third["requests"] == 1, "Same task should not count again"


def test_update_metrics_counts_busy_transition_without_task_id(tmp_path):
    """_update_metrics should count a busy transition even without task id."""
    metrics_file = tmp_path / "metrics.json"
    monitor._update_metrics(metrics_file, False, None, 0, 0, 0)
    result = monitor._update_metrics(metrics_file, True, None, 100, 10, 5)
    assert result["requests"] == 1


def test_read_llama_metrics_parses_authoritative_counters():
    """Metric parser should extract llama.cpp Prometheus counters."""
    # Mock _get_text to return a known metrics string
    original = monitor._get_text
    monitor._get_text = lambda url: (
        "llamacpp:prompt_tokens_total 12345\n"
        "llamacpp:tokens_predicted_total 6789\n"
        "llamacpp:prompt_tokens_seconds 55.5\n"
        "llamacpp:predicted_tokens_seconds 42.3\n"
        "llamacpp:requests_processing 1\n"
        "llamacpp:requests_deferred 2\n"
    )
    try:
        result = monitor._read_llama_metrics("http://fake")
        assert result is not None
        assert result["prompt_tokens_processed"] == 12345.0
        assert result["generated_tokens"] == 6789.0
        assert result["prompt_tps"] == 55.5
        assert result["generation_tps"] == 42.3
        assert result["requests_processing"] == 1.0
        assert result["requests_deferred"] == 2.0
    finally:
        monitor._get_text = original


def test_read_ccr_metrics_parses_bounded_request_counters():
    """CCR metric parser should extract request lifecycle counters."""
    original = monitor._get_text
    monitor._get_text = lambda url: (
        "ccr_requests_in_flight 2\n"
        "ccr_requests_completed_total 100\n"
        "ccr_requests_failed_total 5\n"
        "ccr_requests_cancelled_total 1\n"
        "ccr_requests_rejected_total 3\n"
        "ccr_fallbacks_total 2\n"
        "ccr_quota_failures_total 1\n"
        "ccr_provider_attempts_total 110\n"
    )
    try:
        result = monitor._read_ccr_metrics("http://fake")
        assert result is not None
        assert result["in_flight"] == 2.0
        assert result["completed"] == 100.0
        assert result["failed"] == 5.0
        assert result["cancelled"] == 1.0
        assert result["rejected"] == 3.0
        assert result["fallbacks"] == 2.0
        assert result["quota_failures"] == 1.0
    finally:
        monitor._get_text = original


def test_format_uptime_formats_correctly():
    """Uptime formatting should produce HH:MM:SS or Nd HH:MM:SS."""
    now = datetime(2026, 7, 19, 12, 0, 0)
    assert monitor._format_uptime(now - timedelta(seconds=65), now) == "00:01:05"
    assert monitor._format_uptime(now - timedelta(hours=3, minutes=23, seconds=12), now) == "03:23:12"
    assert monitor._format_uptime(None, now) == "n/a"


def test_as_int_clamps_negative_to_zero():
    """_as_int should never return a negative value."""
    assert monitor._as_int(-5) == 0
    assert monitor._as_int(0) == 0
    assert monitor._as_int(42) == 42
    assert monitor._as_int(None) == 0
    assert monitor._as_int("not a number") == 0


def test_textual_dashboard_class_importable():
    """The Textual dashboard class should be importable and subclass App."""
    assert hasattr(monitor, "OrnithDashboard")
    from textual.app import App
    assert issubclass(monitor.OrnithDashboard, App)
