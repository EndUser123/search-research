"""Tests for question_extractor.py — S1.5 openquestions extraction."""

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

sys.path.insert(0, "P:/.claude/hooks")
from utils.question_extractor import (
    extract_pending_questions,
    extract_text_from_message,
    is_substantive_answer,
    has_context_pronoun,
)


def make_entry(msg_type: str, content: str, timestamp: str = "2026-05-05T10:00:00Z") -> dict:
    """Helper to create a transcript entry."""
    return {
        "type": msg_type,
        "message": {"content": content},
        "timestamp": timestamp,
    }


def make_transcript(entries: list[dict]) -> str:
    """Helper to create a JSONL transcript string."""
    return "\n".join(json.dumps(e) for e in entries)


class TestIsSubstantiveAnswer:
    """Test case 1: No questions → empty array."""

    def test_empty_text_returns_false(self):
        assert is_substantive_answer("") is False
        assert is_substantive_answer("   ") is False

    def test_short_text_returns_false(self):
        assert is_substantive_answer("Let me check.") is False
        assert is_substantive_answer("I need to look into it.") is False

    def test_meta_phrases_return_false(self):
        assert is_substantive_answer("Let me investigate this for you.") is False
        assert is_substantive_answer("I'll check the documentation.") is False
        assert is_substantive_answer("That's a good question, let me think...") is False

    def test_real_answer_returns_true(self):
        assert is_substantive_answer(
            "The users table has the following columns: id (integer, primary key), "
            "email (varchar), created_at (timestamp), and updated_at (timestamp)."
        ) is True
        assert is_substantive_answer(
            "Based on my analysis, the issue is caused by the missing import statement "
            "at line 42 of the auth middleware."
        ) is True


class TestHasContextPronoun:
    """Test context-dependent question detection."""

    def test_pronouns_detected(self):
        assert has_context_pronoun("Where is it defined?") is True
        assert has_context_pronoun("How does that work?") is True
        assert has_context_pronoun("What did they do?") is True

    def test_no_pronouns_returns_false(self):
        assert has_context_pronoun("What is the schema for users?") is False
        assert has_context_pronoun("How do I install this package?") is False


class TestExtractTextFromMessage:
    """Test message text extraction."""

    def test_string_content(self):
        msg = {"message": {"content": "Hello world"}}
        assert extract_text_from_message(msg) == "Hello world"

    def test_list_content(self):
        msg = {"message": {"content": [{"type": "text", "text": "Hello from list"}]}}
        assert extract_text_from_message(msg) == "Hello from list"

    def test_empty_content(self):
        msg = {"message": {"content": ""}}
        assert extract_text_from_message(msg) == ""


class TestNoQuestionsEmptyTranscript:
    """Test case 1: No questions → empty array."""

    def test_only_statements(self):
        transcript = make_transcript([
            make_entry("user", "Do the thing."),
            make_entry("assistant", "I'll do it now."),
            make_entry("user", "Thanks!"),
        ])
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "transcript.jsonl"
            path.write_text(transcript, encoding="utf-8")
            result = extract_pending_questions(path, max_questions=3)
            assert result == []

    def test_only_ellipsis(self):
        transcript = make_transcript([
            make_entry("user", "Not sure..."),
            make_entry("assistant", "Let me investigate."),
        ])
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "transcript.jsonl"
            path.write_text(transcript, encoding="utf-8")
            result = extract_pending_questions(path, max_questions=3)
            assert result == []


class TestUnansweredQuestion:
    """Test case 2: Unanswered question → captured."""

    def test_question_without_answer(self):
        transcript = make_transcript([
            make_entry("user", "What's the schema for users table?"),
        ])
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "transcript.jsonl"
            path.write_text(transcript, encoding="utf-8")
            result = extract_pending_questions(path, max_questions=3)
            assert len(result) == 1
            assert result[0]["question"] == "What's the schema for users table?"
            assert result[0]["context"] == ""

    def test_question_with_meta_response_still_pending(self):
        transcript = make_transcript([
            make_entry("user", "What's the schema for users table?"),
            make_entry("assistant", "Let me check the migrations..."),
        ])
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "transcript.jsonl"
            path.write_text(transcript, encoding="utf-8")
            result = extract_pending_questions(path, max_questions=3)
            # Meta response is not substantive, question still pending
            assert len(result) == 1
            assert "users table" in result[0]["question"]


class TestAnsweredQuestion:
    """Test case 3: Answered question → excluded."""

    def test_question_with_substantive_answer(self):
        transcript = make_transcript([
            make_entry("user", "What's the schema for users table?"),
            make_entry("assistant", (
                "The users table has these columns: id (integer, primary key), "
                "email (varchar unique), created_at (timestamp), and updated_at (timestamp)."
            )),
        ])
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "transcript.jsonl"
            path.write_text(transcript, encoding="utf-8")
            result = extract_pending_questions(path, max_questions=3)
            assert result == []  # Question was answered


class TestMultipleQuestions:
    """Test case 5: Multiple questions → top 3 recent."""

    def test_five_questions_two_answered(self):
        transcript = make_transcript([
            make_entry("user", "What's the schema?", timestamp="2026-05-05T10:00:00Z"),
            make_entry("assistant", "id, email, created_at."),  # Answered
            make_entry("user", "Where is it?", timestamp="2026-05-05T10:01:00Z"),
            make_entry("user", "How do I use it?", timestamp="2026-05-05T10:02:00Z"),
            make_entry("assistant", "Let me explain..."),  # Not substantive
            make_entry("user", "Can you show an example?", timestamp="2026-05-05T10:03:00Z"),
        ])
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "transcript.jsonl"
            path.write_text(transcript, encoding="utf-8")
            result = extract_pending_questions(path, max_questions=3)
            assert len(result) == 3  # 3 unanswered (meta doesn't count as answer)
            # Most recent last
            assert result[-1]["question"] == "Can you show an example?"

    def test_only_top_three_returned(self):
        transcript = make_transcript([
            make_entry("user", f"Question {i}?", timestamp=f"2026-05-05T10:{i:02d}:00Z")
            for i in range(6)  # 6 questions, no answers
        ])
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "transcript.jsonl"
            path.write_text(transcript, encoding="utf-8")
            result = extract_pending_questions(path, max_questions=3)
            assert len(result) == 3  # Capped at 3


class TestContextDependentQuestion:
    """Test case 6: Context-dependent → context captured."""

    def test_pronoun_gets_preceding_context(self):
        transcript = make_transcript([
            make_entry("assistant", "The auth middleware checks JWT tokens."),
            make_entry("user", "Where is it defined?", timestamp="2026-05-05T10:00:00Z"),
        ])
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "transcript.jsonl"
            path.write_text(transcript, encoding="utf-8")
            result = extract_pending_questions(path, max_questions=3)
            assert len(result) == 1
            assert result[0]["context"] == "The auth middleware checks JWT tokens."

    def test_standalone_question_no_context(self):
        transcript = make_transcript([
            make_entry("user", "What is the main function?", timestamp="2026-05-05T10:00:00Z"),
        ])
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "transcript.jsonl"
            path.write_text(transcript, encoding="utf-8")
            result = extract_pending_questions(path, max_questions=3)
            assert len(result) == 1
            assert result[0]["context"] == ""


class TestAssistantQuestionIgnored:
    """Edge case: Question in assistant message (rhetorical) → ignored."""

    def test_assistant_question_not_extracted(self):
        transcript = make_transcript([
            make_entry("assistant", "Should we use async here?"),
            make_entry("user", "Yes, let's do async."),
        ])
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "transcript.jsonl"
            path.write_text(transcript, encoding="utf-8")
            result = extract_pending_questions(path, max_questions=3)
            assert result == []  # No user questions


class TestLongQuestionTruncation:
    """Edge case: Very long question (>200 chars) → truncated."""

    def test_long_question_truncated(self):
        long_question = "What is the " + "X. " * 50 + "schema for users table?"
        transcript = make_transcript([
            make_entry("user", long_question),
        ])
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "transcript.jsonl"
            path.write_text(transcript, encoding="utf-8")
            result = extract_pending_questions(path, max_questions=3)
            assert len(result) == 1
            assert len(result[0]["question"]) <= 200


class TestMissingTranscript:
    """Edge case: Missing or invalid transcript path."""

    def test_none_path_returns_empty(self):
        result = extract_pending_questions(None, max_questions=3)
        assert result == []

    def test_nonexistent_path_returns_empty(self):
        result = extract_pending_questions("/nonexistent/path.jsonl", max_questions=3)
        assert result == []