#!/usr/bin/env python3
"""Tests for StopHook_consultation_loop_interrupt.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add __lib/ to sys.path for the Stop hook module
_hooks_lib_dir = Path(__file__).resolve().parent.parent / "__lib"
if str(_hooks_lib_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_lib_dir))

from StopHook_consultation_loop_interrupt import (
    _is_directive,
    _is_question_response,
    _get_last_directive_and_questions,
    _load_state,
    _save_state,
    _extract_terminal_id,
    _extract_session_id,
    _extract_transcript,
    _STATE_DIR,
)


class TestIsDirective:
    """Tests for _is_directive helper."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("consider all the options", True),
            ("implement the feature", True),
            ("do it now", True),
            ("execute the plan", True),
            ("start the process", True),
            ("begin immediately", True),
            ("proceed with the implementation", True),
            ("save the file", True),
            ("write an entry", True),
            ("which should we choose", True),
            ("which has we implemented", True),
            ("which do we need", True),
            ("hello world", False),
            ("what is this", False),
            ("how does it work", False),
            ("", False),
        ],
    )
    def test_directive_patterns(self, text: str, expected: bool):
        """Directive patterns match correctly."""
        assert _is_directive(text) is expected


class TestIsQuestionResponse:
    """Tests for _is_question_response helper."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Which would you prefer?", True),
            ("Which do you think is best?", True),
            ("Which should I choose?", True),
            ("Which should we do?", True),
            ("Should I proceed?", True),
            ("Should we start?", True),
            ("I have a question?", True),  # ends with ?
            ("Is this correct", False),
            ("This is a statement.", False),
            ("Hello?", True),  # ends with ?
            ("", False),
        ],
    )
    def test_question_response_patterns(self, text: str, expected: bool):
        """Question response patterns match correctly."""
        assert _is_question_response(text) is expected


class TestGetLastDirectiveAndQuestions:
    """Tests for _get_last_directive_and_questions transcript scanner."""

    def test_no_directive(self):
        """No directive means zero question count."""
        transcript = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        directive, count = _get_last_directive_and_questions(transcript)
        assert directive is None
        assert count == 0

    def test_directive_then_question(self):
        """Directive followed by question increments counter."""
        transcript = [
            {"role": "user", "content": "consider all the options"},
            {"role": "assistant", "content": "Which would you prefer?"},
        ]
        directive, count = _get_last_directive_and_questions(transcript)
        assert directive == "consider all the options"
        assert count == 1

    def test_directive_then_two_questions(self):
        """Directive followed by two questions increments counter to 2."""
        transcript = [
            {"role": "user", "content": "implement the feature"},
            {"role": "assistant", "content": "Which should I prioritize first?"},
            {"role": "assistant", "content": "Should I start with the backend?"},
        ]
        directive, count = _get_last_directive_and_questions(transcript)
        assert directive == "implement the feature"
        assert count == 2

    def test_directive_then_non_question_resets(self):
        """Directive followed by non-question response resets counter."""
        transcript = [
            {"role": "user", "content": "do it now"},
            {"role": "assistant", "content": "Which would you prefer?"},
            {"role": "assistant", "content": "I'll proceed with option A."},
        ]
        directive, count = _get_last_directive_and_questions(transcript)
        assert directive is None
        assert count == 0

    def test_directive_repeat_during_question_sequence(self):
        """User repeats directive during question sequence — counter continues."""
        transcript = [
            {"role": "user", "content": "start the process"},
            {"role": "assistant", "content": "Which step would you like to begin with?"},
            {"role": "user", "content": "start the process"},
            {"role": "assistant", "content": "Should I begin with step one?"},
        ]
        directive, count = _get_last_directive_and_questions(transcript)
        assert directive == "start the process"
        assert count == 2

    def test_non_directive_user_after_questions_resets(self):
        """Non-directive user message after questions resets counter."""
        transcript = [
            {"role": "user", "content": "start the process"},
            {"role": "assistant", "content": "Which would you like?"},
            {"role": "user", "content": "actually let's try something else"},
        ]
        directive, count = _get_last_directive_and_questions(transcript)
        assert count == 0
        assert directive is None

    def test_mixed_content_list_format(self):
        """Transcript entries with list content are concatenated."""
        transcript = [
            {"role": "user", "content": "execute the plan"},
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "Which "}, {"type": "text", "text": "should I do?"}],
            },
        ]
        directive, count = _get_last_directive_and_questions(transcript)
        assert directive == "execute the plan"
        assert count == 1

    def test_empty_transcript(self):
        """Empty transcript returns None, 0."""
        directive, count = _get_last_directive_and_questions([])
        assert directive is None
        assert count == 0


class TestExtractHelpers:
    """Tests for extraction helpers."""

    def test_extract_terminal_id_from_data(self):
        """terminal_id extracted from data dict."""
        data = {"terminal_id": "console_abc123"}
        assert _extract_terminal_id(data) == "console_abc123"

    def test_extract_terminal_id_from_session(self):
        """terminal_id extracted from nested session dict."""
        data = {"session": {"terminal_id": "console_xyz"}}
        assert _extract_terminal_id(data) == "console_xyz"

    def test_extract_terminal_id_fallback(self):
        """Falls back to env var when not in data."""
        data = {}
        result = _extract_terminal_id(data)
        # Returns env value or empty string
        assert isinstance(result, str)

    def test_extract_session_id_from_data(self):
        """session_id extracted from data dict."""
        data = {"session_id": "sess_abc123"}
        assert _extract_session_id(data) == "sess_abc123"

    def test_extract_session_id_from_session_object(self):
        """session_id extracted from session object."""
        data = {"session": {"id": "sess_xyz"}}
        assert _extract_session_id(data) == "sess_xyz"

    def test_extract_transcript_from_data(self):
        """Transcript extracted from data.transcript."""
        transcript = [{"role": "user", "content": "hello"}]
        data = {"transcript": transcript}
        assert _extract_transcript(data) == transcript

    def test_extract_transcript_from_handoff(self):
        """Transcript extracted from handoff_envelope.transcript when transcript key missing."""
        transcript = [{"role": "user", "content": "hello"}]
        # handoff_envelope only checked when data.transcript is not a list
        # (Stop hook receives transcript directly, not via handoff_envelope)
        data = {"transcript": "not_a_list", "handoff_envelope": {"transcript": transcript}}
        assert _extract_transcript(data) == transcript

    def test_extract_transcript_empty(self):
        """Missing transcript returns empty list."""
        assert _extract_transcript({}) == []
        assert _extract_transcript({"transcript": "not_a_list"}) == []


class TestStateManagement:
    """Tests for state save/load (uses temp path)."""

    def test_save_and_load_state(self, tmp_path):
        """State round-trips through JSON file."""
        state_file = tmp_path / "test_state.json"
        state = {
            "consecutive_question_responses": 2,
            "in_question_sequence": True,
            "last_directive": "implement the feature",
            "injected_directives": ["implement the feature"],
        }
        _save_state(str(state_file), str(state_file), state)

        loaded = _load_state(str(state_file), str(state_file))
        assert loaded["consecutive_question_responses"] == 2
        assert loaded["last_directive"] == "implement the feature"
        assert "implement the feature" in loaded["injected_directives"]

    def test_load_state_missing_file_returns_defaults(self, tmp_path):
        """Missing state file returns default dict."""
        result = _load_state(str(tmp_path / "nonexistent.json"), "nonexistent")
        assert result["consecutive_question_responses"] == 0
        assert result["in_question_sequence"] is False
        assert result["last_directive"] is None
        assert result["injected_directives"] == []

    def test_save_state_creates_parent_dir(self):
        """State save creates parent directories in _STATE_DIR."""
        # _save_state uses _get_state_file which returns _STATE_DIR / f"consultation_loop_{terminal}_{session}.json"
        # It always writes to _STATE_DIR, not the passed path
        _save_state("abc", "xyz", {"consecutive_question_responses": 0})
        # Verify file was created at the actual state location
        state_file = _STATE_DIR / "consultation_loop_abc_xyz.json"
        assert state_file.exists(), f"Expected {state_file} to exist"

    def test_save_state_fails_open(self, tmp_path):
        """OSError on save is silently ignored (fail open)."""
        # Path that cannot be written to (directory)
        _save_state(str(tmp_path), str(tmp_path), {"consecutive_question_responses": 0})
        # Should not raise
