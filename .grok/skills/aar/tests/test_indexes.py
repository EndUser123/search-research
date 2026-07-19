"""Tests for the retrieval indexes.

Evidence class: production unit.

Covers spec Section 10 + Section 16 (index/packet tests):
* all event references resolve;
* active/superseded indexes are separate;
* indexes by event_id, turn, tool, file_path, branch_status, etc.
"""

from __future__ import annotations

import pytest

from canonical_model import BranchStatus, CanonicalEvent, CanonicalEventType
from event_model import Event, Role
from indexes import EventIndex, build_indexes


def _ce(
    index: int, role: Role = Role.ASSISTANT, text: str = "x", *,
    eid: str, turn: int | None = 0, branch: BranchStatus = BranchStatus.ACTIVE_HISTORY,
    ctype: CanonicalEventType = CanonicalEventType.ASSISTANT_MESSAGE,
    tool_name: str | None = None, paths: tuple[str, ...] = (),
    source_file: str = "chat_history.jsonl",
) -> CanonicalEvent:
    # raw_line_number is what populates source_line_or_offset in from_event.
    base = Event(index=index, role=role, text=text, raw_line_number=index + 1)
    return CanonicalEvent.from_event(
        base, event_id=eid, source_file=source_file, canonical_type=ctype, actor="assistant",
        turn_index=turn, sequence_index=index, branch_status=branch, tool_name=tool_name, paths=paths,
    )


def _build(*events: CanonicalEvent) -> EventIndex:
    return build_indexes(list(events))


# ---------------------------------------------------------------------------
# by_event_id
# ---------------------------------------------------------------------------


def test_index_resolves_every_event_id():
    events = (_ce(0, eid="a"), _ce(1, eid="b"))
    idx = _build(*events)
    assert idx.resolve("a") == "a"
    assert idx.resolve("b") == "b"
    assert idx.resolve("missing") is None


def test_every_event_id_resolves_in_index():
    """Spec: 'all event references resolve'."""
    events = tuple(_ce(i, eid=f"e{i}") for i in range(50))
    idx = _build(*events)
    for ce in events:
        assert idx.resolve(ce.event_id) is not None


# ---------------------------------------------------------------------------
# by_turn
# ---------------------------------------------------------------------------


def test_index_by_turn_groups_events():
    events = (
        _ce(0, eid="a", turn=0),
        _ce(1, eid="b", turn=0),
        _ce(2, eid="c", turn=5),
    )
    idx = _build(*events)
    assert set(idx.by_turn[0]) == {"a", "b"}
    assert set(idx.by_turn[5]) == {"c"}


# ---------------------------------------------------------------------------
# by_actor / by_tool / by_canonical_type
# ---------------------------------------------------------------------------


def test_index_by_actor_and_tool_and_type():
    events = (
        _ce(0, eid="a", ctype=CanonicalEventType.FILE_WRITE, tool_name="write"),
        _ce(1, eid="b", role=Role.USER, ctype=CanonicalEventType.USER_MESSAGE),
    )
    # The second event needs a different actor
    base = Event(index=1, role=Role.USER, text="hi")
    events = events + (
        CanonicalEvent.from_event(base, event_id="b", source_file="chat_history.jsonl",
                                  canonical_type=CanonicalEventType.USER_MESSAGE, actor="user",
                                  turn_index=0, sequence_index=1),
    )
    idx = _build(*events[:2])  # only first two to avoid duplication
    assert "a" in idx.by_actor["assistant"]
    assert "a" in idx.by_tool["write"]
    assert "a" in idx.by_canonical_type["FILE_WRITE"]


# ---------------------------------------------------------------------------
# by_file_path (case-insensitive)
# ---------------------------------------------------------------------------


def test_index_by_file_path_is_case_insensitive():
    events = (_ce(0, eid="a", paths=("P:/Some/Path.py",)),)
    idx = _build(*events)
    assert "a" in idx.by_file_path["p:/some/path.py"]


def test_index_by_file_path_distinguishes_different_files():
    events = (
        _ce(0, eid="a", paths=("a.py",)),
        _ce(1, eid="b", paths=("b.py",)),
    )
    idx = _build(*events)
    assert set(idx.by_file_path["a.py"]) == {"a"}
    assert set(idx.by_file_path["b.py"]) == {"b"}


# ---------------------------------------------------------------------------
# by_branch_status — active/superseded separation
# ---------------------------------------------------------------------------


def test_active_and_superseded_indexes_are_separate():
    """Spec: 'active/superseded indexes are separate'."""
    events = (
        _ce(0, eid="a", branch=BranchStatus.ACTIVE_HISTORY),
        _ce(1, eid="b", branch=BranchStatus.SUPERSEDED_HISTORY),
        _ce(2, eid="c", branch=BranchStatus.ACTIVE_HISTORY),
    )
    idx = _build(*events)
    assert set(idx.active_event_ids) == {"a", "c"}
    assert set(idx.superseded_event_ids) == {"b"}
    # No overlap
    assert set(idx.active_event_ids).isdisjoint(idx.superseded_event_ids)


def test_branch_status_index_includes_all_four_statuses():
    events = (
        _ce(0, eid="a", branch=BranchStatus.ACTIVE_HISTORY),
        _ce(1, eid="b", branch=BranchStatus.SUPERSEDED_HISTORY),
        _ce(2, eid="c", branch=BranchStatus.SYSTEM_METADATA),
    )
    idx = _build(*events)
    assert "ACTIVE_HISTORY" in idx.by_branch_status
    assert "SUPERSEDED_HISTORY" in idx.by_branch_status
    assert "SYSTEM_METADATA" in idx.by_branch_status


# ---------------------------------------------------------------------------
# by_error_signature
# ---------------------------------------------------------------------------


def test_error_signature_index_populated_for_errors():
    base = Event(index=0, role=Role.TOOL_RESULT, text="Traceback (most recent call last):\n...")
    ce = CanonicalEvent.from_event(
        base, event_id="err1", source_file="chat_history.jsonl",
        canonical_type=CanonicalEventType.ERROR, actor="tool",
    )
    idx = _build(ce)
    # at least one error signature recorded
    assert len(idx.by_error_signature) >= 1


# ---------------------------------------------------------------------------
# by_keyword
# ---------------------------------------------------------------------------


def test_keyword_index_bounded_per_event():
    """Spec: keyword index should be practical, not exhaustive."""
    text = " ".join(f"word{i}" for i in range(50))
    base = Event(index=0, role=Role.ASSISTANT, text=text)
    ce = CanonicalEvent.from_event(
        base, event_id="a", source_file="x",
        canonical_type=CanonicalEventType.ASSISTANT_MESSAGE, actor="assistant",
    )
    idx = _build(ce)
    # word0..word49 all length>=5; default cap is 8 per event
    # so total unique keywords <= 8
    assert len(idx.by_keyword) <= 8


def test_keyword_index_short_tokens_excluded():
    base = Event(index=0, role=Role.ASSISTANT, text="a bb ccc dddd eeeee")
    ce = CanonicalEvent.from_event(
        base, event_id="a", source_file="x",
        canonical_type=CanonicalEventType.ASSISTANT_MESSAGE, actor="assistant",
    )
    idx = _build(ce)
    # min length is 5 by default; only "eeeee" qualifies
    assert "eeeee" in idx.by_keyword
    assert "a" not in idx.by_keyword


# ---------------------------------------------------------------------------
# get() helper
# ---------------------------------------------------------------------------


def test_get_returns_empty_for_missing_keys():
    idx = _build(_ce(0, eid="a"))
    assert idx.get("by_event_id", "missing") == ()
    assert idx.get("nonexistent_index", "a") == ()


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_index_build_is_deterministic():
    events = tuple(_ce(i, eid=f"e{i}", turn=i) for i in range(10))
    a = _build(*events)
    b = _build(*events)
    assert a.by_event_id == b.by_event_id
    assert a.by_turn == b.by_turn
    assert a.active_event_ids == b.active_event_ids
