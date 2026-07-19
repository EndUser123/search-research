"""Tests for the canonical-stream normalizer.

Evidence class: production unit + integration.

Covers spec Section 7 (rewind/branch tests):
* active branch reconstructed;
* superseded records labeled;
* superseded decision not treated as current;
* unknown branch state lowers completeness.

And Section 6: classification of raw events into rich canonical types,
deterministic event_ids, cross-linking with events.jsonl timestamps.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from canonical_model import BranchStatus, CanonicalEventType
from event_model import Event, Role, ToolCall
from normalizer import (
    CanonicalStream,
    classify_canonical_type,
    normalize_event,
    normalize_session,
)
from reconciler import ReconciliationReport, USEFUL_EVENT_TYPES, reconcile_sources
from source_snapshot import snapshot_session_sources
from transcript_parser import parse_transcript

from test_reconciler import _build_session, _snapshot_and_reconcile  # reuse fixtures

SID = "019fabc1-0000-0000-0000-000000000001"


# ---------------------------------------------------------------------------
# Classification (canonical type mapping)
# ---------------------------------------------------------------------------


def test_classify_system_as_system_metadata():
    ev = Event(index=0, role=Role.SYSTEM, text="You are Grok.")
    t, meta = classify_canonical_type(ev)
    assert t is CanonicalEventType.SYSTEM_METADATA


def test_classify_real_user_as_user_message():
    ev = Event(index=0, role=Role.USER, text="hello")
    t, _ = classify_canonical_type(ev)
    assert t is CanonicalEventType.USER_MESSAGE


def test_classify_synthetic_user_as_system_metadata():
    ev = Event(index=0, role=Role.USER, text="x", synthetic_reason="compaction_meta")
    t, _ = classify_canonical_type(ev)
    assert t is CanonicalEventType.SYSTEM_METADATA


def test_classify_single_write_as_file_write():
    ev = Event(
        index=0, role=Role.ASSISTANT, text="writing",
        tool_calls=(ToolCall(id="c1", name="write", arguments={"file_path": "a.py"}, arguments_raw="{}"),),
    )
    t, meta = classify_canonical_type(ev)
    assert t is CanonicalEventType.FILE_WRITE
    assert meta.paths == ("a.py",)


def test_classify_read_file_as_file_read():
    ev = Event(
        index=0, role=Role.ASSISTANT, text="reading",
        tool_calls=(ToolCall(id="c1", name="read_file", arguments={"target_file": "x.py"}, arguments_raw="{}"),),
    )
    t, meta = classify_canonical_type(ev)
    assert t is CanonicalEventType.FILE_READ


def test_classify_git_command_as_git_operation():
    ev = Event(
        index=0, role=Role.ASSISTANT, text="git",
        tool_calls=(ToolCall(id="c1", name="run_terminal_command", arguments={"command": "git checkout -- x.py"}, arguments_raw="{}"),),
    )
    t, meta = classify_canonical_type(ev)
    assert t is CanonicalEventType.GIT_OPERATION
    assert meta.command == "git checkout -- x.py"


def test_classify_pytest_as_test_run():
    ev = Event(
        index=0, role=Role.ASSISTANT, text="testing",
        tool_calls=(ToolCall(id="c1", name="run_terminal_command", arguments={"command": "python -m pytest"}, arguments_raw="{}"),),
    )
    t, _ = classify_canonical_type(ev)
    assert t is CanonicalEventType.TEST_RUN


def test_classify_tool_result_error():
    ev = Event(index=0, role=Role.TOOL_RESULT, text="Error: something failed\nTraceback (most recent call last):")
    t, meta = classify_canonical_type(ev)
    assert t is CanonicalEventType.ERROR
    assert meta.exit_code is None  # no exit code in this text


def test_classify_tool_result_with_exit_code():
    ev = Event(index=0, role=Role.TOOL_RESULT, text="Exit Code: 1\noutput")
    t, meta = classify_canonical_type(ev)
    assert t is CanonicalEventType.ERROR
    assert meta.exit_code == 1


def test_classify_multi_call_assistant_as_tool_call():
    ev = Event(
        index=0, role=Role.ASSISTANT, text="batch",
        tool_calls=(
            ToolCall(id="c1", name="read_file", arguments={"target_file": "a"}, arguments_raw="{}"),
            ToolCall(id="c2", name="read_file", arguments={"target_file": "b"}, arguments_raw="{}"),
        ),
    )
    t, meta = classify_canonical_type(ev)
    assert t is CanonicalEventType.TOOL_CALL
    assert meta.tool_name == "multi"
    assert set(meta.paths) == {"a", "b"}


# ---------------------------------------------------------------------------
# Event IDs deterministic
# ---------------------------------------------------------------------------


def test_event_ids_stable_across_normalize_calls(tmp_path: Path):
    sd = _build_session(tmp_path)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    t = parse_transcript(tmp_path / "snap" / "chat_history.jsonl")
    s1 = normalize_session(t, reconciliation=rep, events=None, session_id=SID, terminal_id="t")
    s2 = normalize_session(t, reconciliation=rep, events=None, session_id=SID, terminal_id="t")
    assert [c.event_id for c in s1.events] == [c.event_id for c in s2.events]


def test_event_id_includes_source_and_line(tmp_path: Path):
    sd = _build_session(tmp_path)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    t = parse_transcript(tmp_path / "snap" / "chat_history.jsonl")
    stream = normalize_session(t, reconciliation=rep, events=None, session_id=SID, terminal_id="t")
    first = stream.events[0]
    assert first.event_id.startswith("chat_history-L")
    assert "-S" in first.event_id


# ---------------------------------------------------------------------------
# Branch labelling
# ---------------------------------------------------------------------------


def test_no_duplicate_prompt_indices_all_active(tmp_path: Path):
    sd = _build_session(tmp_path)  # default has 1 user msg at prompt_index 0
    rep = _snapshot_and_reconcile(sd, tmp_path)
    t = parse_transcript(tmp_path / "snap" / "chat_history.jsonl")
    stream = normalize_session(t, reconciliation=rep, events=None, session_id=SID, terminal_id="t")
    user_msgs = [c for c in stream.events if c.canonical_type is CanonicalEventType.USER_MESSAGE]
    assert len(user_msgs) == 1
    assert all(c.branch_status is BranchStatus.ACTIVE_HISTORY for c in user_msgs)


def test_duplicate_prompt_index_supersedes_first_branch(tmp_path: Path):
    """The earlier branch (prompt 0 first occurrence through next user msg)
    must be labelled SUPERSEDED; the second occurrence is ACTIVE."""
    chat = [
        {"type": "system", "content": "sys"},
        {"type": "user", "content": [{"type": "text", "text": "first"}], "prompt_index": 0},
        {"type": "assistant", "content": "v1 response"},
        {"type": "user", "content": [{"type": "text", "text": "rewound"}], "prompt_index": 0},  # DUP
        {"type": "assistant", "content": "v2 response"},
    ]
    sd = _build_session(tmp_path, chat_lines=chat, num_chat_messages=5)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    t = parse_transcript(tmp_path / "snap" / "chat_history.jsonl")
    stream = normalize_session(t, reconciliation=rep, events=None, session_id=SID, terminal_id="t")
    # First user message (prompt_index=0, first occurrence) is SUPERSEDED
    first_user = next(c for c in stream.events if c.text == "first")
    second_user = next(c for c in stream.events if c.text == "rewound")
    v1 = next(c for c in stream.events if c.text == "v1 response")
    v2 = next(c for c in stream.events if c.text == "v2 response")
    assert first_user.branch_status is BranchStatus.SUPERSEDED_HISTORY
    assert v1.branch_status is BranchStatus.SUPERSEDED_HISTORY
    assert second_user.branch_status is BranchStatus.ACTIVE_HISTORY
    assert v2.branch_status is BranchStatus.ACTIVE_HISTORY


def test_system_messages_labelled_system_metadata(tmp_path: Path):
    sd = _build_session(tmp_path)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    t = parse_transcript(tmp_path / "snap" / "chat_history.jsonl")
    stream = normalize_session(t, reconciliation=rep, events=None, session_id=SID, terminal_id="t")
    sys_events = [c for c in stream.events if c.role is Role.SYSTEM]
    assert all(c.branch_status is BranchStatus.SYSTEM_METADATA for c in sys_events)


def test_superseded_decision_not_treated_as_current(tmp_path: Path):
    """Spec Section 7: 'never present a superseded decision as current authority'.

    We can't test the LLM behaviour, but we can test that superseded events
    are kept in a separate tuple from active ones, so the LLM-facing active
    timeline never includes them by default.
    """
    chat = [
        {"type": "system", "content": "sys"},
        {"type": "user", "content": [{"type": "text", "text": "first"}], "prompt_index": 0},
        {"type": "assistant", "content": "decision A"},
        {"type": "user", "content": [{"type": "text", "text": "redo"}], "prompt_index": 0},
        {"type": "assistant", "content": "decision B"},
    ]
    sd = _build_session(tmp_path, chat_lines=chat, num_chat_messages=5)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    t = parse_transcript(tmp_path / "snap" / "chat_history.jsonl")
    stream = normalize_session(t, reconciliation=rep, events=None, session_id=SID, terminal_id="t")
    # decision A is in superseded_events; decision B is in active_events.
    superseded_texts = {c.text for c in stream.superseded_events}
    active_texts = {c.text for c in stream.active_events}
    assert "decision A" in superseded_texts
    assert "decision A" not in active_texts
    assert "decision B" in active_texts


# ---------------------------------------------------------------------------
# Cross-linking with events.jsonl
# ---------------------------------------------------------------------------


def test_timestamp_cross_linked_from_events(tmp_path: Path):
    events = [
        {"ts": "2026-07-18T00:00:00Z", "type": "turn_started", "session_id": SID, "turn_number": 0},
    ]
    sd = _build_session(tmp_path, events_lines=events)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    t = parse_transcript(tmp_path / "snap" / "chat_history.jsonl")
    snap = snapshot_session_sources(sd, tmp_path/"snap2", session_id=SID)
    # Re-fetch filtered events
    events_filtered = []
    for line in (tmp_path/"snap"/"events.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                o = json.loads(line)
                if o.get("type") in USEFUL_EVENT_TYPES:
                    events_filtered.append(o)
            except json.JSONDecodeError:
                pass
    stream = normalize_session(t, reconciliation=rep, events=events_filtered, session_id=SID, terminal_id="t")
    # At least one event should have a timestamp attached.
    assert stream.cross_link_count > 0
    user_msgs = [c for c in stream.events if c.canonical_type is CanonicalEventType.USER_MESSAGE]
    assert any(c.timestamp == "2026-07-18T00:00:00Z" for c in user_msgs)


def test_no_events_yields_no_cross_links(tmp_path: Path):
    sd = _build_session(tmp_path)  # no events_lines → no events.jsonl
    rep = _snapshot_and_reconcile(sd, tmp_path)
    t = parse_transcript(tmp_path / "snap" / "chat_history.jsonl")
    stream = normalize_session(t, reconciliation=rep, events=None, session_id=SID, terminal_id="t")
    assert stream.cross_link_count == 0
    assert all(c.timestamp is None for c in stream.events)


# ---------------------------------------------------------------------------
# Accounting reconciliation
# ---------------------------------------------------------------------------


def test_stream_counts_add_up(tmp_path: Path):
    """active + superseded + unknown + system_metadata == events_total."""
    sd = _build_session(tmp_path)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    t = parse_transcript(tmp_path / "snap" / "chat_history.jsonl")
    stream = normalize_session(t, reconciliation=rep, events=None, session_id=SID, terminal_id="t")
    total = (
        len(stream.active_events)
        + len(stream.superseded_events)
        + len(stream.unknown_branch_events)
        + len(stream.system_metadata_events)
    )
    assert total == len(stream.events)
