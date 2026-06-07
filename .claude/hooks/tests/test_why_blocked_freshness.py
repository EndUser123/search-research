#!/usr/bin/env python3
"""Tests for why_blocked.py freshness signalling (_age + STALE threshold).

Covers the bug that wasted two turns: a stale prior block read as the current
"Blocked by hook". _age must flag old/unparseable rows so the banner fires.
"""
from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "why_blocked.py"
_spec = importlib.util.spec_from_file_location("why_blocked", _SCRIPT)
wb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wb)

NOW = datetime(2026, 6, 7, 4, 0, 0, tzinfo=timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def test_fresh_block_is_not_stale():
    secs, human = wb._age(_iso(NOW - timedelta(seconds=8)), NOW)
    assert secs <= wb.STALE_THRESHOLD_SEC
    assert "ago" in human or human == "just now"


def test_old_block_exceeds_threshold():
    secs, _ = wb._age(_iso(NOW - timedelta(hours=12)), NOW)
    assert secs > wb.STALE_THRESHOLD_SEC


def test_boundary_just_under_threshold_is_fresh():
    secs, _ = wb._age(_iso(NOW - timedelta(seconds=wb.STALE_THRESHOLD_SEC - 1)), NOW)
    assert secs <= wb.STALE_THRESHOLD_SEC


def test_unparseable_timestamp_treated_as_stale():
    secs, human = wb._age("not-a-timestamp", NOW)
    assert secs == float("inf")
    assert human == "unknown age"
    assert secs > wb.STALE_THRESHOLD_SEC


def test_naive_timestamp_assumed_utc():
    secs, _ = wb._age("2026-06-07T03:59:00", NOW)
    assert secs == pytest.approx(60, abs=2)


def test_future_timestamp_clamped_to_just_now():
    secs, human = wb._age(_iso(NOW + timedelta(seconds=30)), NOW)
    assert secs == 0.0
    assert human == "just now"


def test_human_format_hours():
    _, human = wb._age(_iso(NOW - timedelta(hours=2, minutes=5)), NOW)
    assert human == "2h05m ago"


def test_human_format_minutes():
    _, human = wb._age(_iso(NOW - timedelta(minutes=20)), NOW)
    assert human == "20m ago"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
