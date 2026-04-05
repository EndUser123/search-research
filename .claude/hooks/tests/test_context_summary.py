#!/usr/bin/env python3
"""Tests for context_summary.py UserPromptSubmit hook."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(HOOKS_DIR / "UserPromptSubmit_modules"))

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.context_summary import (
    _extract_key_facts,
    _format_summary,
    _read_transcript,
    _should_trigger,
    context_summary_hook,
)


def test_should_trigger_with_slash_command():
    """Should not trigger for slash commands."""
    context = HookContext(
        prompt="/code test",
        data={"transcript_path": "test.jsonl"},
        session_id="test",
        terminal_id="test",
    )
    assert not _should_trigger(context)


def test_should_trigger_with_short_prompt():
    """Should not trigger for very short prompts."""
    context = HookContext(
        prompt="ok",
        data={"transcript_path": "test.jsonl"},
        session_id="test",
        terminal_id="test",
    )
    assert not _should_trigger(context)


def test_should_trigger_with_normal_prompt():
    """Should trigger for normal prompts with transcript."""
    context = HookContext(
        prompt="what was the decision we made earlier?",
        data={"transcript_path": "test.jsonl"},
        session_id="test",
        terminal_id="test",
    )
    assert _should_trigger(context)


def test_should_trigger_without_transcript():
    """Should not trigger when transcript path missing."""
    context = HookContext(
        prompt="what was the decision?",
        data={},
        session_id="test",
        terminal_id="test",
    )
    assert not _should_trigger(context)


def test_read_transcript_from_file():
    """Should read and parse turns from transcript file."""
    # Create temporary transcript file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        transcript_path = f.name
        # Write sample turns
        f.write(json.dumps({"role": "user", "content": "Let's use pytest for testing"}) + "\n")
        f.write(json.dumps({"role": "assistant", "content": "Good choice"}) + "\n")
        f.write(json.dumps({"role": "user", "content": "I prefer option A"}) + "\n")
        f.write(json.dumps({"role": "assistant", "content": "Noted"}) + "\n")
        f.write(json.dumps({"role": "user", "content": "Set timeout to 30 seconds"}) + "\n")

    try:
        turns = _read_transcript(transcript_path, max_turns=3)

        # Should return all 5 turns
        assert len(turns) == 5

        # Should be in reverse order (newest first)
        assert turns[0]["role"] == "user"
        assert "timeout" in turns[0]["content"]

        # Last turn should be oldest
        assert turns[-1]["role"] == "user"
        assert "pytest" in turns[-1]["content"]

    finally:
        # Cleanup
        os.unlink(transcript_path)


def test_read_transcript_missing_file():
    """Should return empty list for missing file."""
    turns = _read_transcript("nonexistent.jsonl")
    assert turns == []


def test_extract_key_facts_from_turns():
    """Should extract factual statements from turns."""
    turns = [
        {"role": "user", "content": "We'll use pytest for testing this module"},
        {"role": "assistant", "content": "Good choice"},
        {"role": "user", "content": "I prefer option A over option B"},
        {"role": "user", "content": "Set timeout to 30 seconds"},
        {"role": "user", "content": "This is required to work properly"},
    ]

    facts = _extract_key_facts(turns)

    # Should extract key facts
    assert len(facts) >= 3

    # Check for expected patterns
    fact_text = " ".join(facts).lower()
    assert "pytest" in fact_text or "use" in fact_text
    assert "option" in fact_text or "prefer" in fact_text
    assert "timeout" in fact_text or "set" in fact_text


def test_extract_key_facts_empty_turns():
    """Should return empty list for no turns."""
    facts = _extract_key_facts([])
    assert facts == []


def test_extract_key_facts_deduplicates():
    """Should deduplicate similar facts."""
    turns = [
        {"role": "user", "content": "We'll use pytest for testing"},
        {"role": "user", "content": "We'll use pytest for testing"},
        {"role": "user", "content": "We'll use pytest for testing"},
    ]

    facts = _extract_key_facts(turns)

    # Should deduplicate
    assert len(facts) <= 2


def test_format_summary_with_facts():
    """Should format facts as context injection."""
    facts = [
        "• Use pytest for testing",
        "• Set timeout to 30 seconds",
    ]

    summary = _format_summary(facts)

    assert "KEY FACTS FROM RECENT CONVERSATION" in summary
    assert "Use pytest for testing" in summary
    assert "Set timeout to 30 seconds" in summary


def test_format_summary_empty_facts():
    """Should return empty string for no facts."""
    summary = _format_summary([])
    assert summary == ""


def test_context_summary_hook_integration():
    """Integration test: full hook with mock transcript."""
    # Create temporary transcript
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        transcript_path = f.name
        f.write(json.dumps({"role": "user", "content": "We'll implement option 1"}) + "\n")
        f.write(json.dumps({"role": "assistant", "content": "OK"}) + "\n")
        f.write(json.dumps({"role": "user", "content": "Set timeout to 30 seconds"}) + "\n")

    try:
        context = HookContext(
            prompt="what did we decide?",
            data={"transcript_path": transcript_path},
            session_id="test",
            terminal_id="test",
        )

        result = context_summary_hook(context)

        # Should return HookResult with context
        assert isinstance(result, HookResult)
        assert result.context is not None
        assert "KEY FACTS FROM RECENT CONVERSATION" in result.context

    finally:
        os.unlink(transcript_path)


if __name__ == "__main__":
    # Run tests
    import pytest

    pytest.main([__file__, "-v"])
