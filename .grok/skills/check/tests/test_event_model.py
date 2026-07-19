"""Tests for ``event_model.py`` — frozen dataclasses and contract enums.

Evidence classification: CONTRACT_MODEL_TESTED

These tests verify the local dataclass model is internally consistent. They
do NOT verify live /check behavior (which would require a real Grok session
and packet consumption by a verifier subagent).
"""

import pytest

import event_model as m


def test_packet_schema_version_is_string():
    assert isinstance(m.PACKET_SCHEMA_VERSION, str)
    assert m.PACKET_SCHEMA_VERSION


def test_role_from_raw_known_types():
    assert m.Role.from_raw("system") is m.Role.SYSTEM
    assert m.Role.from_raw("user") is m.Role.USER
    assert m.Role.from_raw("assistant") is m.Role.ASSISTANT
    assert m.Role.from_raw("tool_result") is m.Role.TOOL_RESULT
    assert m.Role.from_raw("reasoning") is m.Role.REASONING


def test_role_from_raw_unknown_falls_back():
    assert m.Role.from_raw("bogus") is m.Role.UNKNOWN
    assert m.Role.from_raw(None) is m.Role.UNKNOWN
    assert m.Role.from_raw(123) is m.Role.UNKNOWN


def test_role_values_match_jsonl_literal_strings():
    """Role string values must match Grok's chat_history.jsonl `type` field."""
    expected = {"system", "user", "assistant", "tool_result", "reasoning", "unknown"}
    actual = {r.value for r in m.Role}
    assert expected <= actual


def test_source_status_values():
    expected = {"SOURCE_COMPLETE", "SOURCE_PARTIAL", "SOURCE_UNVERIFIED"}
    actual = {s.value for s in m.SourceStatus}
    assert actual == expected


def test_check_verdicts_and_severities_match_skill():
    """Mirrors of check/SKILL.md VERDICT and Issue sections."""
    assert set(m.CHECK_VERDICTS) == {"PASS", "FAIL"}
    assert set(m.CHECK_ISSUE_SEVERITIES) == {"bug", "gap", "regression", "suggestion"}


def test_toolcall_is_frozen():
    tc = m.ToolCall(id="c1", name="write", arguments={"x": 1}, arguments_raw='{"x":1}')
    with pytest.raises(Exception):
        tc.id = "c2"  # type: ignore[misc]


def test_event_is_frozen_and_defaults():
    ev = m.Event(index=0, role=m.Role.ASSISTANT, text="hi")
    with pytest.raises(Exception):
        ev.index = 1  # type: ignore[misc]
    assert ev.tool_calls == ()
    assert ev.tool_call_id is None
    assert ev.synthetic_reason is None
    assert ev.parse_warnings == ()


def test_parse_stats_reconciles_balanced():
    s = m.ParseStats(total_lines=10, parsed_events=9, skipped_malformed=1)
    assert s.reconciles() is True


def test_parse_stats_reconciles_unbalanced():
    s = m.ParseStats(total_lines=10, parsed_events=8, skipped_malformed=1)
    # 8 + 1 != 10 - 0
    assert s.reconciles() is False


def test_parse_stats_reconciles_with_blank():
    s = m.ParseStats(total_lines=10, parsed_events=7, skipped_blank=2, skipped_malformed=1)
    # 7 + 1 == 10 - 2
    assert s.reconciles() is True


def test_transcript_event_by_index_in_range():
    ev = m.Event(index=0, role=m.Role.SYSTEM, text="x")
    t = m.Transcript(
        events=(ev,),
        source_path="p",
        source_status=m.SourceStatus.COMPLETE,
        parse_stats=m.ParseStats(total_lines=1, parsed_events=1),
    )
    assert t.event_by_index(0) is ev
    assert t.event_by_index(1) is None
    assert t.event_by_index(-1) is None


def test_transcript_replace_preserves_others():
    ev = m.Event(index=0, role=m.Role.SYSTEM, text="x")
    t = m.Transcript(
        events=(ev,),
        source_path="p",
        source_status=m.SourceStatus.COMPLETE,
        parse_stats=m.ParseStats(total_lines=1, parsed_events=1),
        session_id=None,
    )
    t2 = t.replace(session_id="abc-123")
    assert t2.session_id == "abc-123"
    assert t.session_id is None  # original unchanged
    assert t2.events == t.events
    assert t2.source_path == "p"


def test_to_dict_roundtrip_keys():
    ev = m.Event(
        index=3,
        role=m.Role.ASSISTANT,
        text="hi",
        tool_calls=(m.ToolCall(id="c1", name="write", arguments={"a": 1}, arguments_raw="{}"),),
        model_id="grok-4.5",
        reasoning_effort="high",
        source_path="P:/x.jsonl",
        raw_line_number=42,
    )
    d = ev.to_dict()
    assert d["index"] == 3
    assert d["role"] == "assistant"
    assert d["text"] == "hi"
    assert d["tool_calls"][0]["id"] == "c1"
    assert d["model_id"] == "grok-4.5"
    assert d["source_path"] == "P:/x.jsonl"
    assert d["raw_line_number"] == 42


def test_toolcall_parse_error_field_exists():
    tc = m.ToolCall(id="c", name="x", arguments={}, arguments_raw="not json", parse_error="json_decode_error: foo")
    d = tc.to_dict()
    assert d["parse_error"].startswith("json_decode_error")
