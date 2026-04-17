#!/usr/bin/env python3
"""Tests for SessionStart_tldr.py — extract_last_user_message and last_user_message kwarg."""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Import the module under test
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
from SessionStart_tldr import extract_last_user_message, _format_tldr_output


class TestExtractLastUserMessage:
    """Unit tests for extract_last_user_message()."""

    def test_happy_path_returns_content(self) -> None:
        data = {"messages": [{"role": "user", "content": "hello"}]}
        result = extract_last_user_message(data)
        assert result == "hello"

    def test_empty_messages_returns_none(self) -> None:
        data = {"messages": []}
        result = extract_last_user_message(data)
        assert result is None

    def test_only_assistant_returns_none(self) -> None:
        data = {"messages": [{"role": "assistant", "content": "hi"}]}
        result = extract_last_user_message(data)
        assert result is None

    def test_malformed_messages_returns_none(self) -> None:
        data = {"messages": "not a list"}
        result = extract_last_user_message(data)
        assert result is None

    def test_missing_messages_key_returns_none(self) -> None:
        data: dict[str, Any] = {}
        result = extract_last_user_message(data)
        assert result is None

    def test_last_user_message_wins(self) -> None:
        data = {
            "messages": [
                {"role": "assistant", "content": "hello"},
                {"role": "user", "content": "second"},
                {"role": "assistant", "content": "third"},
                {"role": "user", "content": "last"},
            ]
        }
        result = extract_last_user_message(data)
        assert result == "last"

    def test_whitespace_content_is_preserved(self) -> None:
        data = {"messages": [{"role": "user", "content": "   hello   "}]}
        result = extract_last_user_message(data)
        assert result == "hello"

    def test_non_dict_message_skipped(self) -> None:
        data = {"messages": [{"role": "user", "content": "first"}, "not a dict", {"role": "user", "content": "last"}]}
        result = extract_last_user_message(data)
        assert result == "last"

    def test_missing_role_skipped(self) -> None:
        data = {"messages": [{"role": "user", "content": "first"}, {"content": "no role"}, {"role": "user", "content": "last"}]}
        result = extract_last_user_message(data)
        assert result == "last"

    def test_missing_content_field_returns_none(self) -> None:
        data = {"messages": [{"role": "user"}]}
        result = extract_last_user_message(data)
        assert result is None

    def test_non_string_content_returns_none(self) -> None:
        data = {"messages": [{"role": "user", "content": 123}]}
        result = extract_last_user_message(data)
        assert result is None


class TestFormatTldrOutputWithLastUserMessage:
    """Tests for _format_tldr_output() with last_user_message kwarg."""

    def test_last_user_message_field_appended(self) -> None:
        summary = textwrap.dedent("""\
            ## Last Session Summary
            **When:** 2026-04-16T21:56:37+00:00
            **Duration:** ~11m
            **Accomplished:** - (no activity)
            **Files changed:** - (none)
            """)
        result = _format_tldr_output(summary, last_user_message="what does skill-creator optimize?")
        assert "**Last user message:** what does skill-creator optimize?" in result

    def test_no_last_user_message_kwarg_backward_compat(self) -> None:
        summary = textwrap.dedent("""\
            ## Last Session Summary
            **When:** 2026-04-16T21:56:37+00:00
            **Duration:** ~11m
            """)
        result = _format_tldr_output(summary)
        assert "**Last user message:**" not in result

    def test_none_last_user_message_backward_compat(self) -> None:
        summary = textwrap.dedent("""\
            ## Last Session Summary
            **When:** 2026-04-16T21:56:37+00:00
            **Duration:** ~11m
            """)
        result = _format_tldr_output(summary, last_user_message=None)
        assert "**Last user message:**" not in result

    def test_empty_string_last_user_message_appended(self) -> None:
        """LOGIC-001 fix: empty string is not None, so field should appear."""
        summary = textwrap.dedent("""\
            ## Last Session Summary
            **When:** 2026-04-16T21:56:37+00:00
            **Duration:** ~11m
            """)
        result = _format_tldr_output(summary, last_user_message="")
        assert "**Last user message:**" in result

    def test_whitespace_only_last_user_message_appended(self) -> None:
        """LOGIC-001 fix: whitespace-only string is not None, so field should appear."""
        summary = textwrap.dedent("""\
            ## Last Session Summary
            **When:** 2026-04-16T21:56:37+00:00
            **Duration:** ~11m
            """)
        result = _format_tldr_output(summary, last_user_message="   ")
        assert "**Last user message:**" in result

    def test_field_position_at_end(self) -> None:
        summary = textwrap.dedent("""\
            ## Last Session Summary
            **When:** 2026-04-16T21:56:37+00:00
            **Duration:** ~11m
            **Open items:**
            - something
            """)
        result = _format_tldr_output(summary, last_user_message="what does skill-creator optimize?")
        lines = result.strip().splitlines()
        assert lines[-1] == "**Last user message:** what does skill-creator optimize?"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
