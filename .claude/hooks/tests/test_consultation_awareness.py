#!/usr/bin/env python3
"""Tests for UserPromptSubmit_modules/consultation_awareness.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from UserPromptSubmit_modules.consultation_awareness import (
    _is_directive,
    _is_question_response,
    _near_match,
    _has_tool_calls,
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
            ("Hello?", True),
            ("", False),
        ],
    )
    def test_question_response_patterns(self, text: str, expected: bool):
        """Question response patterns match correctly."""
        assert _is_question_response(text) is expected


class TestNearMatch:
    """Tests for _near_match helper."""

    @pytest.mark.parametrize(
        "a,b,expected",
        [
            ("implement the feature", "implement the feature", True),
            ("implement the feature", "IMPLEMENT THE FEATURE", True),  # case insensitive
            ("implement the feature", "implement the feature ", True),  # trailing space
            ("implement the feature", "implement the", True),  # prefix match (valid near-match)
            ("hello world", "goodbye world", False),  # different
            ("start the process", "start the process now", True),  # prefix
            ("start the process now", "start the process", True),  # prefix reverse
            ("", "", False),  # both empty
            ("implement the feature", "", False),  # one empty
            ("", "implement the feature", False),
            # Length < 6 returns False even if identical
            ("abc", "abc", False),
            ("ab", "ab", False),
        ],
    )
    def test_near_match(self, a: str, b: str, expected: bool):
        """Near-match detection works for prefix/case variations."""
        assert _near_match(a, b) is expected


class TestHasToolCalls:
    """Tests for _has_tool_calls helper."""

    def test_tools_used_list(self):
        """tools_used list with entries returns True."""
        ctx = MagicMock()
        ctx.data = {"tools_used": ["Read", "Write"]}
        assert _has_tool_calls(ctx) is True

    def test_tools_used_empty(self):
        """Empty tools_used list returns False."""
        ctx = MagicMock()
        ctx.data = {"tools_used": []}
        assert _has_tool_calls(ctx) is False

    def test_tools_used_missing(self):
        """Missing tools_used key returns False."""
        ctx = MagicMock()
        ctx.data = {}
        assert _has_tool_calls(ctx) is False

    def test_toolUse_list(self):
        """toolUse list with entries returns True."""
        ctx = MagicMock()
        ctx.data = {"toolUse": [{"Name": "Read"}]}
        assert _has_tool_calls(ctx) is True

    def test_toolUse_empty(self):
        """Empty toolUse list returns False."""
        ctx = MagicMock()
        ctx.data = {"toolUse": []}
        assert _has_tool_calls(ctx) is False

    def test_tool_events_list(self):
        """tool_events list with entries returns True."""
        ctx = MagicMock()
        ctx.data = {"tool_events": [{"name": "Read"}]}
        assert _has_tool_calls(ctx) is True

    def test_tool_events_empty(self):
        """Empty tool_events list returns False."""
        ctx = MagicMock()
        ctx.data = {"tool_events": []}
        assert _has_tool_calls(ctx) is False

    def test_non_dict_data(self):
        """Non-dict data returns False."""
        ctx = MagicMock()
        ctx.data = "not a dict"
        assert _has_tool_calls(ctx) is False

    def test_none_data(self):
        """None data returns False."""
        ctx = MagicMock()
        ctx.data = None
        assert _has_tool_calls(ctx) is False
