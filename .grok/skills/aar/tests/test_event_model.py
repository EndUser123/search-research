"""Tests for the event_model primitives.

Evidence classification: CONTRACT_MODEL_TESTED

These tests verify the typed primitives (Role, ToolCall, Event, ParseStats,
Transcript) are internally consistent: immutability, enum mapping, accounting
reconciliation, and serialisation round-trips.
"""

from __future__ import annotations

import pytest

from event_model import (
    ALLOWED_DISPOSITIONS,
    ALLOWED_EPISODE_TYPES,
    CONFIDENCE_LEVELS,
    Event,
    ParseStats,
    PACKET_SCHEMA_VERSION,
    Role,
    SourceStatus,
    ToolCall,
    Transcript,
)


# ---------------------------------------------------------------------------
# Role enum
# ---------------------------------------------------------------------------


def test_role_from_raw_recognised():
    assert Role.from_raw("system") is Role.SYSTEM
    assert Role.from_raw("user") is Role.USER
    assert Role.from_raw("assistant") is Role.ASSISTANT
    assert Role.from_raw("reasoning") is Role.REASONING
    assert Role.from_raw("tool_result") is Role.TOOL_RESULT


def test_role_from_raw_unknown_falls_back():
    assert Role.from_raw("not_a_role") is Role.UNKNOWN
    assert Role.from_raw(None) is Role.UNKNOWN
    assert Role.from_raw(123) is Role.UNKNOWN
    assert Role.from_raw("") is Role.UNKNOWN


def test_role_values_match_grok_strings():
    """Role values are the literal strings in chat_history.jsonl."""
    assert Role.SYSTEM.value == "system"
    assert Role.TOOL_RESULT.value == "tool_result"


# ---------------------------------------------------------------------------
# Contract enum coverage (mirrors SKILL.md)
# ---------------------------------------------------------------------------


def test_all_eight_episode_types_present():
    assert len(ALLOWED_EPISODE_TYPES) == 8
    for t in (
        "validated_success",
        "resolved_incident",
        "open_defect",
        "process_weakness",
        "pending_decision",
        "opportunity_candidate",
        "observation",
        "unknown",
    ):
        assert t in ALLOWED_EPISODE_TYPES


def test_all_eight_dispositions_present():
    assert len(ALLOWED_DISPOSITIONS) == 8
    for d in ("ACT_NOW", "INVESTIGATE", "MONITOR", "PRESERVE", "DEFER", "BLOCKED", "NOT_WORTH_DOING", "NO_CHANGE"):
        assert d in ALLOWED_DISPOSITIONS


def test_confidence_levels_include_unknown():
    """UNKNOWN must be a valid confidence level (never force certainty)."""
    assert "UNKNOWN" in CONFIDENCE_LEVELS
    assert "VERY_HIGH" in CONFIDENCE_LEVELS


def test_source_status_values_match_skill():
    assert SourceStatus.COMPLETE.value == "SOURCE_COMPLETE"
    assert SourceStatus.PARTIAL.value == "SOURCE_PARTIAL"
    assert SourceStatus.UNVERIFIED.value == "SOURCE_UNVERIFIED"


# ---------------------------------------------------------------------------
# ToolCall / Event immutability
# ---------------------------------------------------------------------------


def test_tool_call_is_frozen():
    tc = ToolCall(id="c1", name="read_file", arguments={"path": "x"}, arguments_raw='{"path":"x"}')
    with pytest.raises(Exception):
        tc.name = "other"  # type: ignore[misc]


def test_event_is_frozen():
    ev = Event(index=0, role=Role.ASSISTANT, text="hi")
    with pytest.raises(Exception):
        ev.text = "mutated"  # type: ignore[misc]


def test_event_to_dict_round_trips_keys():
    ev = Event(
        index=3,
        role=Role.ASSISTANT,
        text="hello",
        tool_calls=(ToolCall(id="c1", name="write", arguments={"file_path": "a.py"}, arguments_raw="{}"),),
        model_id="grok-4.5",
        source_path="C:/path/file.jsonl",
        raw_line_number=42,
    )
    d = ev.to_dict()
    assert d["index"] == 3
    assert d["role"] == "assistant"
    assert d["text"] == "hello"
    assert d["tool_calls"][0]["name"] == "write"
    assert d["model_id"] == "grok-4.5"
    assert d["raw_line_number"] == 42
    assert d["source_path"] == "C:/path/file.jsonl"


# ---------------------------------------------------------------------------
# ParseStats reconciliation
# ---------------------------------------------------------------------------


def test_parse_stats_reconciles_when_consistent():
    stats = ParseStats(
        total_lines=10,
        parsed_events=8,
        skipped_blank=1,
        skipped_malformed=1,
    )
    assert stats.reconciles() is True


def test_parse_stats_does_not_reconcile_when_drift():
    stats = ParseStats(total_lines=10, parsed_events=5, skipped_malformed=1, skipped_blank=1)
    assert stats.reconciles() is False


def test_parse_stats_to_dict_contains_honest_accounting_fields():
    """ParseStats must surface data-quality flags, not hide them."""
    stats = ParseStats(
        total_lines=100,
        parsed_events=98,
        skipped_malformed=2,
        tool_results_orphaned=3,
        tool_calls_with_parse_error=1,
        has_timestamps=False,
    )
    d = stats.to_dict()
    assert d["skipped_malformed"] == 2
    assert d["tool_results_orphaned"] == 3
    assert d["tool_calls_with_parse_error"] == 1
    assert d["has_timestamps"] is False


# ---------------------------------------------------------------------------
# Transcript
# ---------------------------------------------------------------------------


def test_transcript_event_by_index_in_range():
    ev = Event(index=0, role=Role.SYSTEM, text="sys")
    t = Transcript(
        events=(ev,),
        source_path="x",
        source_status=SourceStatus.COMPLETE,
        parse_stats=ParseStats(),
    )
    assert t.event_by_index(0) is ev


def test_transcript_event_by_index_out_of_range_returns_none():
    t = Transcript(
        events=(Event(index=0, role=Role.SYSTEM, text="sys"),),
        source_path="x",
        source_status=SourceStatus.COMPLETE,
        parse_stats=ParseStats(),
    )
    assert t.event_by_index(5) is None
    assert t.event_by_index(-1) is None


def test_transcript_is_frozen():
    t = Transcript(
        events=(),
        source_path="x",
        source_status=SourceStatus.COMPLETE,
        parse_stats=ParseStats(),
    )
    with pytest.raises(Exception):
        t.source_path = "other"  # type: ignore[misc]


def test_packet_schema_version_is_string():
    """Consumers must be able to refuse unknown schema versions."""
    assert isinstance(PACKET_SCHEMA_VERSION, str)
    assert PACKET_SCHEMA_VERSION == "1.0"
