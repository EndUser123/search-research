"""Tests for runtime_ground_truth renderer.

Verifies Phase 2 verify bar:
  - parse: skips header + separator, handles `|` escape
  - render: stale entries show [STALE — reverify: ...], never silently trusted
  - budget: hard cap, never exceeds
  - session-scoped expiry (e.g. "next session start") is treated as always stale
  - malformed last_verified does not crash (treats as fresh)
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

import pytest

_PLUGIN_LIB = Path(
    "P:/packages/.claude-marketplace/plugins/cc-aca-session/__lib"
)
sys.path.insert(0, str(_PLUGIN_LIB))

import runtime_ground_truth as rgt  # noqa: E402


SAMPLE = """
# header junk

| fact | source | verification_command | last_verified | expiry_trigger |
|------|--------|----------------------|---------------|----------------|
| Foo path | src | `ls /foo` | 2026-07-01 | 30 d |
| Bar cmd | src | `cat /bar` | 2026-07-01 | calendar 2027-01 |
| Baz ses | src | `cmd` | 2026-07-01 | next session start |
| Quux  | src | `cmd` | not-a-date | 30 d |
"""


def test_parse_skips_header_and_separator():
    rows = rgt.parse_table(SAMPLE)
    assert len(rows) == 4
    assert rows[0]["fact"] == "Foo path"
    assert rows[0]["verification_command"] == "`ls /foo`"


def test_render_fresh_passes_through():
    out = rgt.render(
        [{"fact": "X", "source": "s", "verification_command": "c",
          "last_verified": "2026-07-07", "expiry_trigger": "30 d"}],
        today=datetime.date(2026, 7, 7),
    )
    assert "- X  [last_verified 2026-07-07]" in out
    assert "STALE" not in out


def test_render_stale_shows_reverify_command():
    out = rgt.render(
        [{"fact": "X", "source": "s", "verification_command": "ls /y",
          "last_verified": "2026-06-01", "expiry_trigger": "30 d"}],
        today=datetime.date(2026, 7, 7),
    )
    assert "[STALE — reverify: `ls /y`]" in out
    assert "X" in out  # fact still present, NOT dropped


def test_session_scoped_trigger_is_always_stale():
    out = rgt.render(
        [{"fact": "X", "source": "s", "verification_command": "cmd",
          "last_verified": "2026-07-07", "expiry_trigger": "next session start"}],
        today=datetime.date(2026, 7, 7),
    )
    assert "[STALE — reverify: `cmd`]" in out


def test_calendar_trigger_far_future_fresh():
    out = rgt.render(
        [{"fact": "X", "source": "s", "verification_command": "cmd",
          "last_verified": "2026-07-07", "expiry_trigger": "calendar 2027-01"}],
        today=datetime.date(2026, 7, 7),
    )
    assert "STALE" not in out


def test_budget_hard_cap():
    rows = [
        {"fact": f"Row {i} " + ("x" * 50), "source": "s",
         "verification_command": "c", "last_verified": "2026-07-07",
         "expiry_trigger": "30 d"}
        for i in range(20)
    ]
    out = rgt.render(rows, today=datetime.date(2026, 7, 7), budget_chars=400)
    assert len(out) <= 400


def test_malformed_date_treated_as_fresh():
    # Should not raise; fact should pass through (today's date used as fallback).
    out = rgt.render(
        [{"fact": "X", "source": "s", "verification_command": "c",
          "last_verified": "not-a-date", "expiry_trigger": "30 d"}],
        today=datetime.date(2026, 7, 7),
    )
    assert "- X  [last_verified not-a-date]" in out


def test_load_real_ground_truth_file():
    """End-to-end: parse the actual file shipped with the deliverable."""
    p = Path("P:/.claude/hooks/analysis/runtime-ground-truth.md")
    if not p.exists():
        pytest.skip("ground-truth file not present in this env")
    out = rgt.load_and_render(p, today=datetime.date(2026, 7, 7))
    assert "RUNTIME GROUND TRUTH" in out
    assert "P:/.data/evals/" in out
    assert "stop_blocks.jsonl" in out
    # The "Today is 2026-07-07" row has trigger "next session start" → ALWAYS
    # stale (re-verify every session). That's the intended Phase 2 behavior,
    # not a bug: session-scoped facts must be re-verified, never silently
    # trusted. So STALE IS in the output, and that's correct.
    assert "STALE" in out
    assert "Today is 2026-07-07" in out


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))