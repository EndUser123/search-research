"""Tests for ``transcript_parser.py``.

Evidence classification: CONTRACT_MODEL_TESTED + fixture-grounded

Uses both a synthetic 23-line fixture (tests/fixture_sample.jsonl) and
inline dict records to exercise edge cases (malformed JSON, unknown role,
orphaned tool_result, list-vs-string content, reasoning.summary).
"""

import json
from pathlib import Path

import pytest

import transcript_parser as tp
import event_model as m

FIXTURE = Path(__file__).parent / "fixture_sample.jsonl"


# ---------------------------------------------------------------------------
# extract_session_id
# ---------------------------------------------------------------------------


def test_extract_session_id_from_grok_path():
    p = "C:/Users/u/.grok/sessions/P%3A%5C/019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe/chat_history.jsonl"
    assert tp.extract_session_id(p) == "019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe"


def test_extract_session_id_returns_none_for_non_session_path():
    assert tp.extract_session_id("P:/tmp/some.jsonl") is None
    assert tp.extract_session_id("") is None
    assert tp.extract_session_id("P:/foo/not-a-uuid/bar.jsonl") is None


# ---------------------------------------------------------------------------
# infer_source_status
# ---------------------------------------------------------------------------


def test_infer_source_status_unverified_for_empty():
    assert tp.infer_source_status("", 0, 0) is m.SourceStatus.UNVERIFIED
    assert tp.infer_source_status("p", 0, 0) is m.SourceStatus.UNVERIFIED


def test_infer_source_status_partial_when_malformed():
    assert tp.infer_source_status("p", 100, 1, parsed_events=99) is m.SourceStatus.PARTIAL


def test_infer_source_status_complete_when_clean():
    assert tp.infer_source_status("p", 100, 0, parsed_events=100) is m.SourceStatus.COMPLETE


def test_infer_source_status_unverified_when_no_events_parsed():
    """All-blank input must yield UNVERIFIED, not COMPLETE.

    Regression guard for /review Finding 1: a file containing only blank
    lines previously produced SOURCE_COMPLETE with zero events parsed.
    """
    # 50 lines, all blank, 0 parsed, 0 malformed → UNVERIFIED (not COMPLETE).
    assert tp.infer_source_status("p", total_lines=50, skipped_malformed=0, parsed_events=0) is m.SourceStatus.UNVERIFIED
    # Sanity: same input with events parsed → COMPLETE
    assert tp.infer_source_status("p", total_lines=50, skipped_malformed=0, parsed_events=10) is m.SourceStatus.COMPLETE


def test_all_blank_jsonl_yields_unverified_status():
    """End-to-end: a file of only blank lines must yield SOURCE_UNVERIFIED."""
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for _ in range(5):
            f.write("   \n")
        path = f.name
    try:
        t = tp.parse_file(path)
        assert t.parse_stats.parsed_events == 0
        assert t.parse_stats.skipped_blank == 5
        assert t.source_status is m.SourceStatus.UNVERIFIED
    finally:
        Path(path).unlink()


# ---------------------------------------------------------------------------
# Fixture parse — full pipeline
# ---------------------------------------------------------------------------


def test_fixture_parses_all_lines():
    t = tp.parse_file(FIXTURE)
    s = t.parse_stats
    assert s.total_lines > 0
    assert s.reconciles() is True
    assert s.skipped_malformed == 0
    assert s.skipped_blank == 0
    assert s.parsed_events == s.total_lines


def test_fixture_source_status_complete():
    t = tp.parse_file(FIXTURE)
    assert t.source_status is m.SourceStatus.COMPLETE


def test_fixture_session_id_extracted():
    # The fixture path has no UUID parent, so session_id is None.
    t = tp.parse_file(FIXTURE)
    assert t.session_id is None


def test_fixture_role_counts_match_jsonl_types():
    t = tp.parse_file(FIXTURE)
    by_role = t.parse_stats.by_role
    assert by_role.get("system", 0) >= 1
    assert by_role.get("user", 0) >= 2
    assert by_role.get("assistant", 0) >= 1
    assert by_role.get("tool_result", 0) >= 1
    assert by_role.get("reasoning", 0) >= 1


def test_fixture_synthetic_vs_real_user_split():
    t = tp.parse_file(FIXTURE)
    # The fixture has exactly one <user_info> injection and one <user_query>.
    assert t.parse_stats.synthetic_user_messages == 1
    assert t.parse_stats.real_user_messages == 1


def test_fixture_has_no_timestamps():
    t = tp.parse_file(FIXTURE)
    assert t.parse_stats.has_timestamps is False


# ---------------------------------------------------------------------------
# Content shape — string vs list of blocks
# ---------------------------------------------------------------------------


def test_user_content_as_list_of_blocks_is_coerced():
    records = [
        {"type": "user", "content": [{"type": "text", "text": "hello"}, {"type": "text", "text": " world"}]},
    ]
    t = tp.parse_jsonl(records, source_path="inline")
    assert len(t.events) == 1
    assert t.events[0].text == "hello world"
    assert t.events[0].role is m.Role.USER


def test_user_content_as_string_passthrough():
    records = [{"type": "user", "content": "plain string"}]
    t = tp.parse_jsonl(records, source_path="inline")
    assert t.events[0].text == "plain string"


def test_assistant_text_present_even_with_tool_calls():
    records = [
        {"type": "assistant", "content": "thinking", "tool_calls": [
            {"id": "c1", "name": "write", "arguments": '{"file_path":"a"}'}
        ]},
    ]
    t = tp.parse_jsonl(records, source_path="inline")
    ev = t.events[0]
    assert ev.text == "thinking"
    assert len(ev.tool_calls) == 1
    assert ev.tool_calls[0].name == "write"


# ---------------------------------------------------------------------------
# Reasoning records — use summary, not content
# ---------------------------------------------------------------------------


def test_reasoning_uses_summary_for_text():
    records = [{"type": "reasoning", "id": "r1", "summary": "planning step", "encrypted_content": "", "status": "completed"}]
    t = tp.parse_jsonl(records, source_path="inline")
    ev = t.events[0]
    assert ev.role is m.Role.REASONING
    assert ev.text == "planning step"
    assert ev.reasoning_status == "completed"


def test_reasoning_without_status_field_handled():
    records = [{"type": "reasoning", "id": "r1", "summary": "x", "encrypted_content": ""}]
    t = tp.parse_jsonl(records, source_path="inline")
    assert t.events[0].reasoning_status is None


# ---------------------------------------------------------------------------
# Tool-call argument parsing
# ---------------------------------------------------------------------------


def test_tool_call_arguments_json_string_parsed_to_dict():
    records = [
        {"type": "assistant", "content": "", "tool_calls": [
            {"id": "c1", "name": "write", "arguments": '{"file_path": "P:/a.py", "content": "x"}'}
        ]},
    ]
    t = tp.parse_jsonl(records, source_path="inline")
    tc = t.events[0].tool_calls[0]
    assert tc.arguments == {"file_path": "P:/a.py", "content": "x"}
    assert tc.parse_error is None


def test_tool_call_arguments_malformed_records_error():
    records = [
        {"type": "assistant", "content": "", "tool_calls": [
            {"id": "c1", "name": "write", "arguments": "not json{"}
        ]},
    ]
    t = tp.parse_jsonl(records, source_path="inline")
    tc = t.events[0].tool_calls[0]
    assert tc.arguments == {}
    assert tc.parse_error is not None
    assert "json_decode_error" in tc.parse_error
    assert t.parse_stats.tool_calls_with_parse_error == 1


def test_tool_call_arguments_dict_passthrough():
    """Defensive: some pre-decoded inputs already have a dict."""
    records = [
        {"type": "assistant", "content": "", "tool_calls": [
            {"id": "c1", "name": "write", "arguments": {"file_path": "a"}}
        ]},
    ]
    t = tp.parse_jsonl(records, source_path="inline")
    tc = t.events[0].tool_calls[0]
    assert tc.arguments == {"file_path": "a"}
    assert tc.parse_error is None


def test_tool_call_arguments_non_object_json_flagged():
    """JSON that parses to a list/scalar must be flagged, not silently wrapped.

    Regression guard for /review Finding 2: previously, non-dict JSON args
    were stored under {"__value__": parsed} with parse_error=None, causing
    detectors to silently see empty arguments with no failure hint.
    """
    records = [
        {"type": "assistant", "content": "", "tool_calls": [
            {"id": "c1", "name": "grep", "arguments": '["a.py", "b.py"]'}
        ]},
    ]
    t = tp.parse_jsonl(records, source_path="inline")
    tc = t.events[0].tool_calls[0]
    # Arguments must be empty dict (not the silent __value__ wrap).
    assert tc.arguments == {}
    # Parse error must be present and identify the type mismatch.
    assert tc.parse_error is not None
    assert "arguments_not_object" in tc.parse_error
    assert "list" in tc.parse_error
    # Stats must reflect the parse error.
    assert t.parse_stats.tool_calls_with_parse_error == 1
    # Original raw is preserved so a reviewer can see what the model emitted.
    assert tc.arguments_raw == '["a.py", "b.py"]'


# ---------------------------------------------------------------------------
# Synthetic detection
# ---------------------------------------------------------------------------


def test_user_query_is_real_not_synthetic():
    records = [{"type": "user", "content": "<user_query>fix the bug</user_query>"}]
    t = tp.parse_jsonl(records, source_path="inline")
    assert t.events[0].synthetic_reason is None
    assert t.parse_stats.real_user_messages == 1


def test_system_reminder_injection_marked_synthetic():
    records = [{"type": "user", "content": "<system-reminder>rules</system-reminder>"}]
    t = tp.parse_jsonl(records, source_path="inline")
    assert t.events[0].synthetic_reason is not None
    assert t.parse_stats.synthetic_user_messages == 1


def test_synthetic_reason_tag_is_clean_string():
    """The tag must be a stable human-readable name, not a regex-source hack.

    Regression guard: the old implementation derived the tag by string-
    manipulating the compiled pattern, producing nonsense like
    ``"system>$*$"`` for the ``<system>\\s*$`` pattern.
    """
    records = [
        {"type": "user", "content": "<system-reminder>x</system-reminder>"},
        {"type": "user", "content": "<user_info>y</user_info>"},
        {"type": "user", "content": "<git_status>z</git_status>"},
        {"type": "user", "content": "<system>\n"},
    ]
    t = tp.parse_jsonl(records, source_path="inline")
    tags = [ev.synthetic_reason for ev in t.events]
    assert tags == ["system-reminder", "user_info", "git_status", "system"]


def test_user_query_quoting_system_reminder_is_real():
    """A real prompt that quotes a system-reminder should still be REAL."""
    records = [{"type": "user", "content": "<user_query>the agent said <system-reminder>foo</system-reminder> in output</user_query>"}]
    t = tp.parse_jsonl(records, source_path="inline")
    assert t.events[0].synthetic_reason is None


# ---------------------------------------------------------------------------
# Orphaned tool_results
# ---------------------------------------------------------------------------


def test_orphaned_tool_result_counted():
    records = [
        {"type": "tool_result", "tool_call_id": "nope", "content": "x"},
    ]
    t = tp.parse_jsonl(records, source_path="inline")
    assert t.parse_stats.tool_results_orphaned == 1
    assert t.events[0].role is m.Role.TOOL_RESULT


def test_tool_result_with_matching_call_not_orphaned():
    records = [
        {"type": "assistant", "content": "", "tool_calls": [{"id": "c1", "name": "write", "arguments": "{}"}]},
        {"type": "tool_result", "tool_call_id": "c1", "content": "ok"},
    ]
    t = tp.parse_jsonl(records, source_path="inline")
    assert t.parse_stats.tool_results_orphaned == 0


# ---------------------------------------------------------------------------
# Malformed lines / unknown roles
# ---------------------------------------------------------------------------


def test_malformed_json_line_counted_not_raised():
    raw_lines = [
        json.dumps({"type": "system", "content": "ok"}),
        "this is not json{",
        json.dumps({"type": "user", "content": "<user_query>x</user_query>"}),
    ]
    t = tp.parse_jsonl(raw_lines, source_path="inline")
    assert t.parse_stats.skipped_malformed == 1
    assert t.parse_stats.parsed_events == 2
    assert t.parse_stats.reconciles() is True
    assert t.source_status is m.SourceStatus.PARTIAL
    assert any("json decode error" in w for w in t.parse_stats.warnings)


def test_blank_lines_skipped():
    raw_lines = [json.dumps({"type": "system", "content": "x"}), "", "   ", json.dumps({"type": "user", "content": "<user_query>y</user_query>"})]
    t = tp.parse_jsonl(raw_lines, source_path="inline")
    assert t.parse_stats.skipped_blank == 2


def test_unknown_record_type_counted_as_unknown_role():
    records = [{"type": "walrus", "content": "x"}]
    t = tp.parse_jsonl(records, source_path="inline")
    assert t.parse_stats.unknown_role_lines == 1
    assert t.events[0].role is m.Role.UNKNOWN
    assert any("unknown_record_type" in w for w in t.events[0].parse_warnings)


def test_parse_jsonl_never_raises_on_bad_input():
    """Mixed garbage + valid records yields a partial transcript, no raise."""
    mixed = [
        None,
        42,
        {"type": "system", "content": "x"},
        "garbage",
        {"type": "user", "content": "<user_query>y</user_query>"},
    ]
    t = tp.parse_jsonl(mixed, source_path="inline")
    assert t.parse_stats.reconciles() is True
