#!/usr/bin/env python3
"""Tests for pretooluse_observability correlation_id in block events."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))

from pretooluse_observability import build_pretooluse_block_entry


class TestCorrelationIdInBlockEntry:
    def test_correlation_id_propagated(self) -> None:
        data = {"tool_name": "Write", "tool_input": {"file_path": "/test.py"}}
        entry = build_pretooluse_block_entry(
            data,
            blocking_hook="test_hook",
            reason="blocked",
            event_kind="blocked",
            correlation_id="corr-123",
        )
        assert entry["correlation_id"] == "corr-123"
        assert entry["schema"] == "pretooluse_block"

    def test_correlation_id_none_when_absent(self) -> None:
        data = {"tool_name": "Write", "tool_input": {"file_path": "/test.py"}}
        entry = build_pretooluse_block_entry(
            data,
            blocking_hook="test_hook",
            reason="blocked",
            event_kind="blocked",
        )
        assert entry["correlation_id"] is None

    def test_block_entry_has_required_fields(self) -> None:
        data = {"tool_name": "Edit", "tool_input": {"file_path": "/a.py"}}
        entry = build_pretooluse_block_entry(
            data,
            blocking_hook="deny_root_write",
            reason="root write blocked",
            event_kind="blocked",
            correlation_id="abc-def",
            active_turn_id="turn-1",
        )
        assert entry["tool_name"] == "Edit"
        assert entry["blocking_hook"] == "deny_root_write"
        assert entry["active_turn_id"] == "turn-1"
        assert entry["version"] == 2
        assert entry["event_id"]  # non-empty UUID

    def test_session_id_resolved_from_data(self) -> None:
        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "session": {"id": "sess-42"},
        }
        entry = build_pretooluse_block_entry(
            data,
            blocking_hook="bash_gate",
            reason="unsafe command",
            event_kind="blocked",
            correlation_id="c-1",
        )
        assert entry["session_id"] == "sess-42"
        assert entry["correlation_id"] == "c-1"
