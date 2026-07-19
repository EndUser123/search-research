"""Tests for the bounded context selector.

Evidence class: production unit.

Covers spec Section 14 + Section 16 (context-selection accounting reconciles):
* events_total / events_sent_initially / events_retrieved_later recorded;
* initial context is bounded (does not include all events);
* targeted retrieval via event_ids works;
* unknown event_ids are counted but do not raise.
"""

from __future__ import annotations

import pytest

from canonical_model import BranchStatus, CanonicalEvent, CanonicalEventType
from context_selector import (
    ContextSelection,
    DEFAULT_MAX_TOTAL_EVENTS,
    select_by_event_ids,
    select_initial_context,
)
from detectors import Signal, SignalKind, SignalSeverity
from event_model import Event, Role
from indexes import build_indexes


def _ce(
    index: int, *, eid: str, role: Role = Role.ASSISTANT, text: str = "x",
    turn: int | None = 0, ctype: CanonicalEventType = CanonicalEventType.ASSISTANT_MESSAGE,
    branch: BranchStatus = BranchStatus.ACTIVE_HISTORY,
) -> CanonicalEvent:
    base = Event(index=index, role=role, text=text)
    return CanonicalEvent.from_event(
        base, event_id=eid, source_file="chat_history.jsonl",
        canonical_type=ctype, actor="assistant",
        turn_index=turn, sequence_index=index, branch_status=branch,
    )


def _sig(indices: tuple[int, ...], *, kind: SignalKind = SignalKind.EMPTY_TOOL_RESULT,
         severity: SignalSeverity = SignalSeverity.MEDIUM, detail: str = "x") -> Signal:
    return Signal(
        kind=kind, event_indices=indices, detail=detail, severity=severity,
        detector="test", falsifier="test falsifier",
    )


# ---------------------------------------------------------------------------
# Initial selection — bounded
# ---------------------------------------------------------------------------


def test_initial_context_does_not_include_all_events():
    """Spec: 'Do not include all normalized events by default.'"""
    events = [_ce(i, eid=f"e{i}") for i in range(500)]
    signals = [_sig((0,), detail=f"sig{i}") for i in range(5)]
    idx = build_indexes(events)
    sel = select_initial_context(
        manifest_summary={}, events=events, signals=signals, indexes=idx,
        snapshot_cutoff="2026-07-18T00:00:00Z",
    )
    assert sel.accounting["events_total"] == 500
    assert sel.accounting["events_sent_initially"] <= DEFAULT_MAX_TOTAL_EVENTS
    assert sel.accounting["events_sent_initially"] < 500


def test_initial_context_records_accounting():
    events = [_ce(i, eid=f"e{i}") for i in range(50)]
    signals = [_sig((0,))]
    idx = build_indexes(events)
    sel = select_initial_context(
        manifest_summary={"snapshot_cutoff": "x"}, events=events, signals=signals,
        indexes=idx, snapshot_cutoff="2026-07-18T00:00:00Z",
    )
    assert sel.accounting["events_total"] == 50
    assert sel.accounting["events_sent_initially"] >= 1
    assert sel.accounting["events_retrieved_later"] == 0
    assert "selection_reason" in sel.accounting
    assert isinstance(sel.accounting["selection_reason"], str)


def test_initial_context_includes_top_signals_by_severity():
    """HIGH severity signals come before LOW severity ones."""
    events = [_ce(i, eid=f"e{i}") for i in range(10)]
    low_sig = _sig((0,), severity=SignalSeverity.LOW, detail="low")
    high_sig = _sig((1,), severity=SignalSeverity.HIGH, detail="high")
    idx = build_indexes(events)
    sel = select_initial_context(
        manifest_summary={}, events=events, signals=[low_sig, high_sig],
        indexes=idx, max_signals=2,
    )
    # High should appear before low in the signals list
    kinds_details = [s["detail"] for s in sel.signals]
    assert kinds_details.index("high") < kinds_details.index("low")


def test_initial_context_caps_signals_at_max():
    events = [_ce(i, eid=f"e{i}") for i in range(100)]
    signals = [_sig((i,), detail=f"s{i}") for i in range(50)]
    idx = build_indexes(events)
    sel = select_initial_context(
        manifest_summary={}, events=events, signals=signals, indexes=idx,
        max_signals=10,
    )
    assert len(sel.signals) == 10


# ---------------------------------------------------------------------------
# Targeted retrieval
# ---------------------------------------------------------------------------


def test_targeted_retrieval_adds_events():
    events = [_ce(i, eid=f"e{i}") for i in range(20)]
    sel = select_initial_context(
        manifest_summary={}, events=events, signals=[], indexes=build_indexes(events),
    )
    initial_count = sel.accounting["events_sent_initially"]
    sel2 = select_by_event_ids(sel, ["e15", "e16", "e17"], events)
    assert sel2.accounting["events_sent_initially"] == initial_count
    assert sel2.accounting["events_retrieved_later"] >= 1


def test_targeted_retrieval_counts_unknown_ids():
    events = [_ce(i, eid=f"e{i}") for i in range(5)]
    sel = select_initial_context(
        manifest_summary={}, events=events, signals=[], indexes=build_indexes(events),
    )
    sel2 = select_by_event_ids(sel, ["e0", "does_not_exist"], events)
    assert sel2.accounting["unknown_event_ids_requested"] == 1


def test_targeted_retrieval_dedupes_existing_events():
    events = [_ce(i, eid=f"e{i}") for i in range(5)]
    signals = [_sig((0,))]
    sel = select_initial_context(
        manifest_summary={}, events=events, signals=signals, indexes=build_indexes(events),
    )
    # e0 was already included via the signal; retrieving it again should not duplicate.
    sel2 = select_by_event_ids(sel, ["e0"], events)
    ids = [e["event_id"] for e in sel2.events]
    assert ids.count("e0") == 1


# ---------------------------------------------------------------------------
# System metadata excluded
# ---------------------------------------------------------------------------


def test_system_metadata_events_excluded_from_cited():
    base = Event(index=0, role=Role.SYSTEM, text="system msg")
    sys_event = CanonicalEvent.from_event(
        base, event_id="sys1", source_file="chat_history.jsonl",
        canonical_type=CanonicalEventType.SYSTEM_METADATA, actor="system",
        branch_status=BranchStatus.SYSTEM_METADATA,
    )
    sig = _sig((0,))
    idx = build_indexes([sys_event])
    sel = select_initial_context(
        manifest_summary={}, events=[sys_event], signals=[sig], indexes=idx,
    )
    cited_ids = {e["event_id"] for e in sel.events}
    assert "sys1" not in cited_ids


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_selection_is_deterministic():
    events = [_ce(i, eid=f"e{i}") for i in range(30)]
    signals = [_sig((i,)) for i in range(5)]
    idx = build_indexes(events)
    a = select_initial_context(manifest_summary={}, events=events, signals=signals, indexes=idx)
    b = select_initial_context(manifest_summary={}, events=events, signals=signals, indexes=idx)
    assert [s["detail"] for s in a.signals] == [s["detail"] for s in b.signals]
    assert [e["event_id"] for e in a.events] == [e["event_id"] for e in b.events]
