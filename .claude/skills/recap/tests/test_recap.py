#!/usr/bin/env python3
"""Tests for recap skill — covering all identified edge cases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from recap import (
    _extract_content,
    _extract_semantic_content,
    _is_transcript_file,
    _summarize_session,
    extract_sessions_from_transcript,
    format_recap,
    load_transcript_entries,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def transcript_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for transcript files."""
    d = tmp_path / "transcripts"
    d.mkdir()
    return d


def make_transcript(transcript_dir: Path, *entries: dict) -> Path:
    """Write entries to a .jsonl file and return the path."""
    path = transcript_dir / "test.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    return path


# =============================================================================
# _is_transcript_file tests (PERF-003)
# =============================================================================


class TestIsTranscriptFile:
    def test_finds_user_type(self, transcript_dir: Path) -> None:
        path = make_transcript(
            transcript_dir,
            {"type": "user", "content": "Hello"},
        )
        assert _is_transcript_file(path) is True

    def test_finds_assistant_type(self, transcript_dir: Path) -> None:
        path = make_transcript(
            transcript_dir,
            {"type": "assistant", "content": "Hi there"},
        )
        assert _is_transcript_file(path) is True

    def test_rejects_non_transcript(self, transcript_dir: Path) -> None:
        path = make_transcript(transcript_dir, {"type": "metadata", "key": "value"})
        assert _is_transcript_file(path) is False

    def test_empty_file(self, transcript_dir: Path) -> None:
        path = transcript_dir / "empty.jsonl"
        path.touch()
        assert _is_transcript_file(path) is False

    def test_finds_user_after_metadata_lines(self, transcript_dir: Path) -> None:
        """Transcript with metadata before user/assistant content (issue: 20-line limit)."""
        entries = [{"type": "header", "version": "1"}] * 50
        entries.append({"type": "user", "content": "Hello"})
        path = make_transcript(transcript_dir, *entries)
        # Should find user content even though it appears after line 20
        assert _is_transcript_file(path) is True

    def test_finds_user_at_line_199(self, transcript_dir: Path) -> None:
        """User content at line 199 should be found (200-line limit)."""
        entries = [{"type": "header", "line": i} for i in range(199)]
        entries.append({"type": "user", "content": "Hello"})
        path = make_transcript(transcript_dir, *entries)
        assert _is_transcript_file(path) is True

    def test_rejects_when_user_after_line_200(self, transcript_dir: Path) -> None:
        """User content after line 200 is not found (limit is inclusive)."""
        entries = [{"type": "header", "line": i} for i in range(200)]
        entries.append({"type": "user", "content": "Hello"})
        path = make_transcript(transcript_dir, *entries)
        assert _is_transcript_file(path) is False


# =============================================================================
# _extract_content tests — empty list and tool_result filtering (QUAL-002, QUAL-004)
# =============================================================================


class TestExtractContent:
    def test_string_content(self) -> None:
        entry = {"type": "user", "content": "Hello world"}
        assert _extract_content(entry) == "Hello world"

    def test_nested_message_content(self) -> None:
        entry = {"type": "user", "message": {"role": "user", "content": "Nested"}}
        assert _extract_content(entry) == "Nested"

    def test_content_list_with_text(self) -> None:
        entry = {
            "type": "user",
            "content": [{"type": "text", "text": "List content"}],
        }
        assert _extract_content(entry) == "List content"

    def test_empty_list_returns_empty_string(self) -> None:
        """Empty list content should return '' not '[]' (QUAL-002 fix)."""
        entry = {"type": "user", "content": []}
        assert _extract_content(entry) == ""

    def test_none_content_fallback_to_nested(self) -> None:
        entry = {"type": "user", "content": None, "message": {"content": "Fallback"}}
        assert _extract_content(entry) == "Fallback"

    def test_none_content_no_fallback(self) -> None:
        entry = {"type": "user", "content": None}
        assert _extract_content(entry) == ""

    def test_tool_result_block_filtered(self) -> None:
        """tool_result blocks should be skipped (QUAL-004 fix)."""
        entry = {
            "type": "user",
            "content": [
                {"type": "tool_result", "text": "File created: foo.py"},
                {"type": "text", "text": "User intent"},
            ],
        }
        assert _extract_content(entry) == "User intent"

    def test_all_tool_result_blocks_skipped(self) -> None:
        """Entry with only tool_result blocks should return ''."""
        entry = {
            "type": "user",
            "content": [
                {"type": "tool_result", "text": "output1"},
                {"type": "tool_result", "text": "output2"},
            ],
        }
        # All blocks are tool_result → should return ''
        assert _extract_content(entry) == ""

    def test_mixed_content_text_then_tool_result(self) -> None:
        """Mixed content should extract from text block, skipping tool_result."""
        entry = {
            "type": "user",
            "content": [
                {"type": "text", "text": "User said hello"},
                {"type": "tool_result", "text": "Some output"},
            ],
        }
        assert _extract_content(entry) == "User said hello"


# =============================================================================
# _extract_semantic_content tests — regex pattern matching
# =============================================================================


class TestExtractSemanticContent:
    def test_extracts_problem_pattern(self) -> None:
        entries = [
            {"type": "user", "content": "The bug is in the loop."},
            {"type": "assistant", "content": "**Problem:** The loop runs forever."},
        ]
        result = _extract_semantic_content(entries)
        assert len(result["problems"]) >= 1

    def test_extracts_fix_pattern(self) -> None:
        entries = [
            {"type": "assistant", "content": "**What was the fix?** Added base case."},
        ]
        result = _extract_semantic_content(entries)
        assert len(result["fixes"]) >= 1

    def test_extracts_action_pattern(self) -> None:
        entries = [
            {
                "type": "assistant",
                "content": "**What did we do?** Refactored the function.",
            },
        ]
        result = _extract_semantic_content(entries)
        assert len(result["actions"]) >= 1

    def test_extracts_decision_pattern(self) -> None:
        entries = [
            {"type": "assistant", "content": "**Decision:** Use iterative approach."},
        ]
        result = _extract_semantic_content(entries)
        assert len(result["decisions"]) >= 1

    def test_extracts_outcome_pattern(self) -> None:
        entries = [
            {
                "type": "assistant",
                "content": "**Outcome:** Task completed successfully.",
            },
        ]
        result = _extract_semantic_content(entries)
        assert len(result["outcomes"]) >= 1

    def test_deduplicates_results(self) -> None:
        entries = [
            {
                "type": "assistant",
                "content": "**Problem:** Bug 1.\n**Problem:** Bug 1.",
            },
        ]
        result = _extract_semantic_content(entries)
        # Should deduplicate — note: `.` is a lookahead boundary, not in capture
        assert result["problems"].count("Bug 1") == 1


# =============================================================================
# Session extraction tests
# =============================================================================


class TestExtractSessions:
    def test_single_session(self) -> None:
        entries = [
            {"type": "user", "content": "Hi", "sessionId": "s1"},
            {"type": "assistant", "content": "Hello", "sessionId": "s1"},
        ]
        sessions = extract_sessions_from_transcript(entries)
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "s1"

    def test_session_boundary(self) -> None:
        entries = [
            {"type": "user", "content": "Hi", "sessionId": "s1"},
            {"type": "assistant", "content": "Hello", "sessionId": "s1"},
            {"type": "user", "content": "New", "sessionId": "s2"},
            {"type": "assistant", "content": "OK", "sessionId": "s2"},
        ]
        sessions = extract_sessions_from_transcript(entries)
        assert len(sessions) == 2
        assert sessions[0]["session_id"] == "s1"
        assert sessions[1]["session_id"] == "s2"

    def test_missing_sessionid_all_in_one_session(self) -> None:
        """Missing sessionId means all entries in one session (F7 behavior)."""
        entries = [
            {"type": "user", "content": "Hi"},  # no sessionId
            {"type": "assistant", "content": "Hello"},
        ]
        sessions = extract_sessions_from_transcript(entries)
        assert len(sessions) == 1

    def test_session_message_counts(self) -> None:
        entries = [
            {"type": "user", "content": "Hi", "sessionId": "s1"},
            {"type": "user", "content": "Again", "sessionId": "s1"},
            {"type": "assistant", "content": "Hello", "sessionId": "s1"},
        ]
        sessions = extract_sessions_from_transcript(entries)
        assert sessions[0]["user_message_count"] == 2
        assert sessions[0]["assistant_message_count"] == 1


# =============================================================================
# _summarize_session tests
# =============================================================================


class TestSummarizeSession:
    def test_last_goal_from_string_content(self) -> None:
        entries = [
            {"type": "assistant", "content": "Hello", "sessionId": "s1"},
            {"type": "user", "content": "Fix the login bug", "sessionId": "s1"},
        ]
        result = _summarize_session(entries, "s1")
        assert "Fix the login bug" in result["last_goal"]

    def test_last_goal_from_list_content(self) -> None:
        entries = [
            {"type": "assistant", "content": "Hello", "sessionId": "s1"},
            {
                "type": "user",
                "content": [{"type": "text", "text": "Refactor the parser"}],
                "sessionId": "s1",
            },
        ]
        result = _summarize_session(entries, "s1")
        assert "Refactor the parser" in result["last_goal"]

    def test_tool_result_only_entries_skipped_for_goal(self) -> None:
        """Entries that are only tool_result output should not become last_goal."""
        entries = [
            {"type": "user", "content": "Fix the bug", "sessionId": "s1"},
            {
                "type": "user",
                "content": [{"type": "tool_result", "text": "file.py edited"}],
                "sessionId": "s1",
            },
        ]
        result = _summarize_session(entries, "s1")
        # Should NOT pick up tool_result as goal
        assert result["last_goal"] != "file.py edited"

    def test_entry_count(self) -> None:
        entries = [
            {"type": "user", "content": "Hi", "sessionId": "s1"},
            {"type": "assistant", "content": "Hello", "sessionId": "s1"},
            {"type": "user", "content": "Again", "sessionId": "s1"},
        ]
        result = _summarize_session(entries, "s1")
        assert result["entry_count"] == 3


# =============================================================================
# load_transcript_entries tests
# =============================================================================


class TestLoadTranscriptEntries:
    def test_loads_valid_jsonl(self, transcript_dir: Path) -> None:
        path = make_transcript(
            transcript_dir,
            {"type": "user", "content": "Hello"},
            {"type": "assistant", "content": "Hi"},
        )
        entries = load_transcript_entries(str(path))
        assert len(entries) == 2

    def test_nonexistent_path_returns_empty(self) -> None:
        entries = load_transcript_entries("/nonexistent/path.jsonl")
        assert entries == []

    def test_handles_empty_lines(self, transcript_dir: Path) -> None:
        path = transcript_dir / "empty_lines.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"type": "user", "content": "Hello"}\n\n')
            f.write('{"type": "assistant", "content": "Hi"}\n')
        entries = load_transcript_entries(str(path))
        assert len(entries) == 2


# =============================================================================
# format_recap tests
# =============================================================================


class TestFormatRecap:
    def test_format_recap_empty_sessions(self) -> None:
        result = format_recap([], "term_abc", brief=False)
        assert "No session history found" in result

    def test_format_recap_brief(self) -> None:
        sessions = [
            {
                "session_id": "s1",
                "entry_count": 5,
                "user_message_count": 2,
                "assistant_message_count": 3,
                "last_goal": "Fix the bug",
                "problem": None,
                "fix": None,
                "action": None,
                "problems": [],
                "fixes": [],
                "actions": [],
                "decisions": [],
                "outcomes": [],
            }
        ]
        result = format_recap(sessions, "term_abc", brief=True)
        assert "Last session in this terminal" in result
        assert "Fix the bug" in result

    def test_format_recap_with_problem_fix_action(self) -> None:
        sessions = [
            {
                "session_id": "s1",
                "entry_count": 5,
                "user_message_count": 2,
                "assistant_message_count": 3,
                "last_goal": "Fix the bug",
                "problem": "Loop runs forever",
                "fix": "Added base case",
                "action": "Edited loop.py",
                "problems": ["Loop runs forever"],
                "fixes": ["Added base case"],
                "actions": ["Edited loop.py"],
                "decisions": [],
                "outcomes": [],
            }
        ]
        result = format_recap(sessions, "term_abc", brief=False)
        assert "Loop runs forever" in result
        assert "Added base case" in result
        assert "Edited loop.py" in result


# =============================================================================
# Integration tests
# =============================================================================


class TestIntegration:
    def test_full_pipeline_with_real_transcript(self, transcript_dir: Path) -> None:
        """End-to-end: write transcript -> load -> extract sessions -> format."""
        path = make_transcript(
            transcript_dir,
            {
                "type": "user",
                "content": "Fix the authentication bug",
                "sessionId": "sess_abc123",
            },
            {
                "type": "assistant",
                "content": "**Problem:** Token not validated.\n**What was the fix?** Added token check.",
                "sessionId": "sess_abc123",
            },
        )

        entries = load_transcript_entries(str(path))
        assert len(entries) == 2

        sessions = extract_sessions_from_transcript(entries)
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "sess_abc123"
        assert sessions[0]["user_message_count"] == 1
        assert sessions[0]["assistant_message_count"] == 1

        recap = format_recap(sessions, "term_test", brief=False)
        assert "sess_abc123" in recap
        assert "Token not validated" in recap or "Added token check" in recap

    def test_pipeline_with_empty_list_content(self, transcript_dir: Path) -> None:
        """Empty list content should not appear as '[]' in goal (QUAL-002)."""
        path = make_transcript(
            transcript_dir,
            {
                "type": "user",
                "content": [],
                "sessionId": "sess_empty",
            },
        )

        entries = load_transcript_entries(str(path))
        sessions = extract_sessions_from_transcript(entries)
        result = format_recap(sessions, "term_test", brief=False)
        # Should NOT contain '[]' as goal content
        assert "[]" not in result or "No session history" in result
