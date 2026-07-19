"""Tests for the deterministic transcript parser.

Evidence classification: CONTRACT_MODEL_TESTED

The parser is fed a hand-crafted but realistic Grok ``chat_history.jsonl``
fixture plus several adversarial inputs. The fixture is a real file on disk
(anti-mock), covering every role, malformed JSON, synthetic user messages,
and a tool_call ↔ tool_result join.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from event_model import ParseStats, Role, SourceStatus, Transcript
from transcript_parser import (
    TranscriptParseError,
    classify_source,
    extract_session_id_from_path,
    parse_transcript,
    parse_transcript_lines,
)

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE = FIXTURES / "chat_history_sample.jsonl"


# ---------------------------------------------------------------------------
# Happy path: parse the realistic fixture
# ---------------------------------------------------------------------------


def test_parse_sample_fixture_returns_transcript():
    t = parse_transcript(SAMPLE)
    assert isinstance(t, Transcript)
    assert len(t.events) > 0
    assert t.source_path.endswith("chat_history_sample.jsonl")


def test_parse_sample_fixture_role_counts():
    t = parse_transcript(SAMPLE)
    by_role = t.parse_stats.by_role
    assert by_role["system"] == 1
    assert by_role["user"] == 3
    assert by_role["assistant"] == 8
    assert by_role["tool_result"] == 6
    assert by_role["reasoning"] == 1


def test_parse_sample_fixture_distinguishes_synthetic_user():
    """Synthetic user messages (compaction_meta) must be counted separately."""
    t = parse_transcript(SAMPLE)
    assert t.parse_stats.synthetic_user_messages == 1
    assert t.parse_stats.real_user_messages == 2


def test_parse_sample_fixture_has_timestamps_is_false():
    """Grok chat_history.jsonl carries no timestamps; parser must say so."""
    t = parse_transcript(SAMPLE)
    assert t.parse_stats.has_timestamps is False


def test_parse_sample_fixture_stats_reconcile():
    t = parse_transcript(SAMPLE)
    assert t.parse_stats.reconciles() is True


def test_parse_sample_fixture_orphan_count():
    """Fixture contains one tool_result with unknown tool_call_id."""
    t = parse_transcript(SAMPLE)
    assert t.parse_stats.tool_results_orphaned == 1
    assert any("unknown tool_call_id" in w for w in t.parse_stats.warnings)


def test_parse_sample_fixture_tool_arg_parse_error_count():
    """Fixture ends with a tool_call whose arguments are invalid JSON."""
    t = parse_transcript(SAMPLE)
    assert t.parse_stats.tool_calls_with_parse_error == 1


def test_parse_sample_source_status_complete():
    """No compaction/ dir → COMPLETE (fixture lives in tests/fixtures/)."""
    t = parse_transcript(SAMPLE)
    assert t.source_status is SourceStatus.COMPLETE


# ---------------------------------------------------------------------------
# Tool call argument parsing
# ---------------------------------------------------------------------------


def test_tool_call_arguments_parsed_as_dict():
    lines = [
        json.dumps(
            {
                "type": "assistant",
                "content": "x",
                "tool_calls": [
                    {"id": "c1", "name": "write", "arguments": '{"file_path":"a.py","content":"x"}'}
                ],
                "model_id": "grok-4.5",
            }
        )
    ]
    t = parse_transcript_lines(lines, source_status=SourceStatus.COMPLETE)
    ev = t.events[0]
    assert ev.tool_calls[0].arguments == {"file_path": "a.py", "content": "x"}
    assert ev.tool_calls[0].parse_error is None


def test_tool_call_arguments_parse_error_recorded():
    """Malformed JSON arguments must not crash the parser; error is recorded."""
    lines = [
        json.dumps(
            {
                "type": "assistant",
                "content": "x",
                "tool_calls": [{"id": "c1", "name": "write", "arguments": "{not valid"}],
                "model_id": "grok-4.5",
            }
        )
    ]
    t = parse_transcript_lines(lines, source_status=SourceStatus.COMPLETE)
    tc = t.events[0].tool_calls[0]
    assert tc.arguments == {}
    assert tc.parse_error is not None
    assert tc.arguments_raw == "{not valid"
    assert t.parse_stats.tool_calls_with_parse_error == 1


# ---------------------------------------------------------------------------
# Malformed input tolerance
# ---------------------------------------------------------------------------


def test_malformed_json_line_is_skipped_not_fatal():
    lines = ['{"type":"user","content":[{"type":"text","text":"hi"}]}', "this is not json", ""]
    t = parse_transcript_lines(lines, source_status=SourceStatus.COMPLETE)
    assert t.parse_stats.skipped_malformed == 1
    assert t.parse_stats.skipped_blank == 1
    assert len(t.events) == 1
    assert any("malformed JSON" in w for w in t.parse_stats.warnings)
    assert t.parse_stats.reconciles() is True


def test_non_object_json_root_is_skipped():
    lines = ['["a","b"]', "42", "null"]
    t = parse_transcript_lines(lines, source_status=SourceStatus.COMPLETE)
    assert t.parse_stats.skipped_malformed == 3
    assert len(t.events) == 0


def test_unknown_role_maps_to_unknown_with_warning():
    lines = [json.dumps({"type": "weird_new_role", "content": "x"})]
    t = parse_transcript_lines(lines, source_status=SourceStatus.COMPLETE)
    assert t.events[0].role is Role.UNKNOWN
    assert t.parse_stats.unknown_role_lines == 1
    assert "unknown role type" in t.events[0].parse_warnings[0]


# ---------------------------------------------------------------------------
# Text extraction across roles
# ---------------------------------------------------------------------------


def test_user_content_list_blocks_are_joined():
    lines = [
        json.dumps(
            {
                "type": "user",
                "content": [
                    {"type": "text", "text": "part 1"},
                    {"type": "text", "text": "part 2"},
                ],
            }
        )
    ]
    t = parse_transcript_lines(lines, source_status=SourceStatus.COMPLETE)
    assert t.events[0].text == "part 1\npart 2"


def test_assistant_content_is_plain_string():
    lines = [json.dumps({"type": "assistant", "content": "hello world", "model_id": "x"})]
    t = parse_transcript_lines(lines, source_status=SourceStatus.COMPLETE)
    assert t.events[0].text == "hello world"


def test_tool_result_content_joined():
    lines = [json.dumps({"type": "tool_result", "tool_call_id": "c1", "content": "output line"})]
    t = parse_transcript_lines(lines, source_status=SourceStatus.COMPLETE)
    assert t.events[0].text == "output line"
    assert t.events[0].tool_call_id == "c1"


# ---------------------------------------------------------------------------
# Source classification
# ---------------------------------------------------------------------------


def test_classify_source_unverified_for_empty_file(tmp_path: Path):
    p = tmp_path / "empty.jsonl"
    p.write_text("", encoding="utf-8")
    assert classify_source(p) is SourceStatus.UNVERIFIED


def test_classify_source_unverified_for_wrong_format(tmp_path: Path):
    """A file full of unrecognised types is UNVERIFIED."""
    p = tmp_path / "bad.jsonl"
    p.write_text(
        "\n".join(['{"type":"weird","content":"x"}'] * 5) + "\n",
        encoding="utf-8",
    )
    assert classify_source(p) is SourceStatus.UNVERIFIED


def test_classify_source_complete_for_real_grok_shaped_file(tmp_path: Path):
    p = tmp_path / "ok.jsonl"
    p.write_text(
        "\n".join(
            [
                json.dumps({"type": "system", "content": "sys"}),
                json.dumps({"type": "user", "content": [{"type": "text", "text": "hi"}]}),
                json.dumps({"type": "assistant", "content": "hello", "model_id": "x"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assert classify_source(p) is SourceStatus.COMPLETE


def test_classify_source_partial_when_compaction_dir_exists(tmp_path: Path):
    """A co-located compaction/ dir with segment files → SOURCE_PARTIAL."""
    p = tmp_path / "chat_history.jsonl"
    p.write_text(
        json.dumps({"type": "system", "content": "sys"}) + "\n", encoding="utf-8"
    )
    (tmp_path / "compaction").mkdir()
    (tmp_path / "compaction" / "segment_000.md").write_text("# compacted", encoding="utf-8")
    assert classify_source(p) is SourceStatus.PARTIAL


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def test_extract_session_id_from_grok_path():
    path = "C:/Users/x/.grok/sessions/P%3A%5C/019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe/chat_history.jsonl"
    assert (
        extract_session_id_from_path(path)
        == "019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe"
    )


def test_extract_session_id_returns_none_when_no_uuid():
    assert extract_session_id_from_path("C:/tmp/no-uuid-here.jsonl") is None


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_parse_missing_file_raises():
    with pytest.raises(TranscriptParseError):
        parse_transcript(Path("does/not/exist.jsonl"))


def test_parse_directory_raises():
    with pytest.raises(TranscriptParseError):
        parse_transcript(FIXTURES)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_parse_is_deterministic_across_runs():
    """Parsing the same file twice yields identical event indices and texts."""
    t1 = parse_transcript(SAMPLE)
    t2 = parse_transcript(SAMPLE)
    assert [e.index for e in t1.events] == [e.index for e in t2.events]
    assert [e.text for e in t1.events] == [e.text for e in t2.events]
    assert t1.parse_stats == t2.parse_stats
