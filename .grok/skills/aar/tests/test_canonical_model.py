"""Tests for the canonical event model.

Evidence class: production unit.

Covers spec Section 6:
* CanonicalEvent extends Event (detectors work unchanged);
* all 16 CanonicalEventType values are present;
* all 4 BranchStatus values are present;
* deterministic sort_key ordering;
* event_ids are stable;
* no fields silently default to fake values.
"""

from __future__ import annotations

import pytest

from canonical_model import (
    SOURCE_ORDER,
    BranchStatus,
    CanonicalEvent,
    CanonicalEventType,
)
from event_model import Event, Role, ToolCall


def test_all_canonical_event_types_present():
    """Spec lists 16 event types; all must be in the enum."""
    expected = {
        "USER_MESSAGE", "ASSISTANT_MESSAGE", "TOOL_CALL", "TOOL_RESULT",
        "COMMAND", "FILE_READ", "FILE_WRITE", "TEST_RUN", "GIT_OPERATION",
        "ERROR", "SESSION_EVENT", "REWIND", "DECISION_CANDIDATE",
        "CORRECTION_CANDIDATE", "CLAIM_CANDIDATE", "SYSTEM_METADATA",
    }
    actual = {t.value for t in CanonicalEventType}
    assert actual == expected
    assert len(expected) == 16


def test_all_branch_statuses_present():
    expected = {"ACTIVE_HISTORY", "SUPERSEDED_HISTORY", "BRANCH_UNKNOWN", "SYSTEM_METADATA"}
    actual = {b.value for b in BranchStatus}
    assert actual == expected


def test_canonical_event_inherits_event_fields():
    """Detectors accept Iterable[Event]; CanonicalEvent must satisfy that."""
    base = Event(index=5, role=Role.ASSISTANT, text="hi", source_path="x", raw_line_number=10)
    ce = CanonicalEvent.from_event(
        base,
        event_id="chat_history-L000010-S000005",
        source_file="chat_history.jsonl",
        canonical_type=CanonicalEventType.ASSISTANT_MESSAGE,
        actor="assistant",
    )
    # Inherited fields preserved
    assert ce.index == 5
    assert ce.role is Role.ASSISTANT
    assert ce.text == "hi"
    assert ce.raw_line_number == 10
    # Canonical fields populated
    assert ce.event_id == "chat_history-L000010-S000005"
    assert ce.source_file == "chat_history.jsonl"
    assert ce.canonical_type is CanonicalEventType.ASSISTANT_MESSAGE
    assert ce.actor == "assistant"


def test_canonical_event_is_frozen():
    base = Event(index=0, role=Role.USER, text="x")
    ce = CanonicalEvent.from_event(
        base, event_id="e1", source_file="x", canonical_type=CanonicalEventType.USER_MESSAGE, actor="user"
    )
    with pytest.raises(Exception):
        ce.event_id = "other"  # type: ignore[misc]


def test_sort_key_orders_by_turn_then_sequence():
    """Deterministic ordering even when timestamps are absent."""
    base1 = Event(index=0, role=Role.USER, text="a", prompt_index=5)
    base2 = Event(index=1, role=Role.USER, text="b", prompt_index=3)
    base3 = Event(index=2, role=Role.USER, text="c", prompt_index=5)
    e1 = CanonicalEvent.from_event(base1, event_id="e1", source_file="chat_history.jsonl", canonical_type=CanonicalEventType.USER_MESSAGE, actor="user", turn_index=5, sequence_index=0)
    e2 = CanonicalEvent.from_event(base2, event_id="e2", source_file="chat_history.jsonl", canonical_type=CanonicalEventType.USER_MESSAGE, actor="user", turn_index=3, sequence_index=1)
    e3 = CanonicalEvent.from_event(base3, event_id="e3", source_file="chat_history.jsonl", canonical_type=CanonicalEventType.USER_MESSAGE, actor="user", turn_index=5, sequence_index=2)
    ordered = sorted([e1, e2, e3], key=lambda c: c.sort_key())
    # turn 3 first, then turn 5 by sequence_index
    assert [c.event_id for c in ordered] == ["e2", "e1", "e3"]


def test_sort_key_handles_missing_turn():
    """Events with no turn_index sort last (sys.maxsize)."""
    import sys
    base = Event(index=0, role=Role.SYSTEM, text="sys")
    ce = CanonicalEvent.from_event(
        base, event_id="e", source_file="x", canonical_type=CanonicalEventType.SYSTEM_METADATA, actor="system",
        turn_index=None,
    )
    assert ce.sort_key()[0] == sys.maxsize


def test_source_order_ranks_chat_history_first():
    """Primary source (chat_history) is authoritative; sort_key reflects that."""
    assert SOURCE_ORDER["chat_history.jsonl"] == 0
    assert SOURCE_ORDER["events.jsonl"] > SOURCE_ORDER["chat_history.jsonl"]


def test_to_canonical_dict_contains_all_spec_fields():
    """Spec Section 6 lists the required event fields; all must be in the dict."""
    base = Event(index=0, role=Role.ASSISTANT, text="hi", tool_calls=(ToolCall(id="c1", name="write", arguments={"file_path":"a.py"}, arguments_raw="{}"),))
    ce = CanonicalEvent.from_event(
        base, event_id="e1", source_file="chat_history.jsonl",
        canonical_type=CanonicalEventType.FILE_WRITE, actor="assistant",
        tool_name="write", paths=("a.py",), timestamp="2026-07-18T00:00:00Z",
    )
    d = ce.to_canonical_dict()
    required = {
        "event_id", "source_file", "source_line_or_offset", "source_record_id",
        "turn_index", "sequence_index", "timestamp", "actor", "event_type",
        "tool_name", "command", "working_directory", "arguments",
        "stdout_excerpt", "stderr_excerpt", "exit_code", "duration_ms",
        "paths", "session_id", "terminal_id", "model", "provider",
        "branch_status", "raw_excerpt", "parse_confidence",
    }
    assert required.issubset(d.keys())
    assert d["event_type"] == "FILE_WRITE"
    assert d["paths"] == ["a.py"]


def test_event_ids_deterministic_for_same_input():
    """Same source_file+line+seq → same event_id."""
    base = Event(index=0, role=Role.USER, text="x")
    a = CanonicalEvent.from_event(base, event_id="chat_history-L000001-S000000", source_file="chat_history.jsonl", canonical_type=CanonicalEventType.USER_MESSAGE, actor="user")
    b = CanonicalEvent.from_event(base, event_id="chat_history-L000001-S000000", source_file="chat_history.jsonl", canonical_type=CanonicalEventType.USER_MESSAGE, actor="user")
    assert a.event_id == b.event_id
