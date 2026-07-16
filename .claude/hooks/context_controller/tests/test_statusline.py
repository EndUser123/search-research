"""Tests for session-bound, stateless statusline rendering."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from context_controller.statusline import render_status  # noqa: E402


def test_statusline_identity_is_bound_to_session_input() -> None:
    first = render_status(
        {
            "session_id": "session-alpha-12345678",
            "model": {"display_name": "M3"},
            "context_window": {"used_percentage": 20, "context_window_size": 1_000_000},
        }
    )
    second = render_status(
        {
            "session_id": "session-beta-87654321",
            "model": {"display_name": "M3"},
            "context_window": {"used_percentage": 80, "context_window_size": 1_000_000},
        }
    )
    assert "sid=12345678" in first
    assert "sid=87654321" in second
    assert first != second


def test_missing_context_is_unknown_not_stale() -> None:
    output = render_status({"session_id": "session-alpha-12345678", "model": {}})
    assert "sid=12345678" in output
    assert "ctx ?" in output
    assert "COMPACT NOW" not in output


def test_missing_session_identity_is_explicit() -> None:
    output = render_status(
        {"model": {"display_name": "M3"}, "context_window": {"used_percentage": 80}}
    )
    assert "sid=?" in output
