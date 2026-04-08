"""T16: discover() empty return — discover() returns [] when no new sources.

Verifies: When the history file does not exist, discover() returns an empty list
without raising an error.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from core.chs.providers.claude_code_raw import ClaudeCodeRawProvider
from core.chs.providers.codex_desktop import CodexDesktopProvider
from core.chs.providers.claude_log import ClaudeLogProvider


@pytest.fixture
def nonexistent_history(tmp_path):
    """Path to a history file that does not exist."""
    return tmp_path / ".claude" / "nonexistent_history.jsonl"


class TestDiscoverEmpty:
    """T16: discover() empty return tests."""

    def test_claude_code_raw_discover_no_history_file(self, nonexistent_history):
        """discover() returns [] when history.jsonl does not exist."""
        provider = ClaudeCodeRawProvider()
        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", nonexistent_history):
            result = provider.discover()
            assert result == [], f"Expected [], got {result}"
            assert isinstance(result, list)

    def test_codex_desktop_discover_no_history_file(self, nonexistent_history):
        """discover() returns [] when .codex/history.jsonl does not exist."""
        provider = CodexDesktopProvider()
        nonexistent_codex = nonexistent_history.parent.parent / ".codex" / "history.jsonl"
        with patch("core.chs.providers.codex_desktop.HISTORY_JSONL", nonexistent_codex):
            result = provider.discover()
            assert result == [], f"Expected [], got {result}"

    def test_claude_log_discover_no_history_file(self, nonexistent_history):
        """discover() returns [] when claude-log.jsonl does not exist."""
        provider = ClaudeLogProvider()
        nonexistent_log = nonexistent_history.parent.parent / "claude-log.jsonl"
        with patch("core.chs.providers.claude_log.HISTORY_JSONL", nonexistent_log):
            result = provider.discover()
            assert result == [], f"Expected [], got {result}"

    def test_discover_returns_list_not_none(self, nonexistent_history):
        """discover() always returns a list, never None."""
        provider = ClaudeCodeRawProvider()
        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", nonexistent_history):
            result = provider.discover()
            assert result is not None
            assert isinstance(result, list)
