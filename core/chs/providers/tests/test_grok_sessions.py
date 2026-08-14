"""Tests for the GrokSessionsProvider."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

_PKG_ROOT = Path(__file__).resolve().parents[5]
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from core.chs.providers.grok_sessions import GrokSessionsProvider
from core.chs.providers.base import ProviderCapabilities


class TestGrokSessionsProviderInterface:
    """Verify GrokSessionsProvider satisfies the Provider protocol."""

    def test_provider_id(self):
        p = GrokSessionsProvider()
        assert p.provider_id == "grok_sessions"

    def test_capabilities_type(self):
        p = GrokSessionsProvider()
        assert isinstance(p.capabilities, ProviderCapabilities)

    def test_capabilities_values(self):
        p = GrokSessionsProvider()
        assert p.capabilities.supports_incremental is True
        assert p.capabilities.supports_backfill is True
        assert p.capabilities.has_task_events is True
        assert p.capabilities.has_tool_events is True

    def test_has_discover(self):
        p = GrokSessionsProvider()
        assert callable(getattr(p, "discover", None))

    def test_has_ingest_since(self):
        p = GrokSessionsProvider()
        assert callable(getattr(p, "ingest_since", None))

    def test_has_fetch_session(self):
        p = GrokSessionsProvider()
        assert callable(getattr(p, "fetch_session", None))

    def test_has_fetch_message(self):
        p = GrokSessionsProvider()
        assert callable(getattr(p, "fetch_message", None))

    def test_discover_returns_list(self):
        p = GrokSessionsProvider()
        result = p.discover()
        assert isinstance(result, list)

    @patch("core.chs.providers.grok_sessions._discover_session_files", return_value=[])
    def test_ingest_since_returns_list(self, mock_discover):
        p = GrokSessionsProvider()
        result = p.ingest_since(None)
        assert isinstance(result, list)

    @patch("core.chs.providers.grok_sessions._discover_session_files", return_value=[])
    def test_fetch_session_nonexistent_returns_empty(self, mock_discover):
        p = GrokSessionsProvider()
        result = p.fetch_session("nonexistent")
        assert isinstance(result, dict)
        assert result == {}

    @patch("core.chs.providers.grok_sessions._discover_session_files", return_value=[])
    def test_fetch_message_nonexistent_returns_empty(self, mock_discover):
        p = GrokSessionsProvider()
        result = p.fetch_message("nonexistent", "nonexistent_0")
        assert isinstance(result, dict)


class TestGrokFormatParsing:
    """Test extraction of text from Grok message format."""

    def test_extract_string_content(self):
        from core.chs.providers.grok_sessions import _extract_text_content
        obj = {"type": "system", "content": "You are Grok"}
        assert _extract_text_content(obj) == "You are Grok"

    def test_extract_list_content(self):
        from core.chs.providers.grok_sessions import _extract_text_content
        obj = {"type": "user", "content": [{"type": "text", "text": "Hello world"}]}
        assert _extract_text_content(obj) == "Hello world"

    def test_extract_multiple_blocks(self):
        from core.chs.providers.grok_sessions import _extract_text_content
        obj = {"type": "assistant", "content": [
            {"type": "text", "text": "Part 1"},
            {"type": "text", "text": "Part 2"},
        ]}
        result = _extract_text_content(obj)
        assert "Part 1" in result
        assert "Part 2" in result

    def test_extract_missing_content_uses_summary(self):
        from core.chs.providers.grok_sessions import _extract_text_content
        obj = {"type": "reasoning", "summary": "Thinking about X"}
        assert "[Reasoning]" in _extract_text_content(obj)

    def test_format_tool_calls_present(self):
        from core.chs.providers.grok_sessions import _format_tool_calls
        obj = {"tool_calls": [{"name": "read_file", "arguments": "{\"path\": \"/foo\"}"}]}
        result = _format_tool_calls(obj)
        assert "[Tool: read_file]" in result

    def test_format_tool_calls_none(self):
        from core.chs.providers.grok_sessions import _format_tool_calls
        assert _format_tool_calls({}) is None

    def test_format_tool_calls_truncates_long_args(self):
        from core.chs.providers.grok_sessions import _format_tool_calls
        long_args = "x" * 300
        obj = {"tool_calls": [{"name": "write", "arguments": long_args}]}
        result = _format_tool_calls(obj)
        assert "..." in result

    def test_role_map_skips_reasoning(self):
        from core.chs.providers.grok_sessions import _ROLE_MAP
        assert _ROLE_MAP.get("reasoning") is None
        assert _ROLE_MAP.get("user") == "user"
        assert _ROLE_MAP.get("assistant") == "assistant"
        assert _ROLE_MAP.get("tool_result") == "tool"
        assert _ROLE_MAP.get("system") == "system"


class TestContentHash:
    """Test content hash stability."""

    def test_hash_stable(self):
        from core.chs.providers.grok_sessions import _compute_content_hash
        h1 = _compute_content_hash("grok_sessions", "sess1", "user", "hello", 1)
        h2 = _compute_content_hash("grok_sessions", "sess1", "user", "hello", 1)
        assert h1 == h2

    def test_hash_differs_by_line(self):
        from core.chs.providers.grok_sessions import _compute_content_hash
        h1 = _compute_content_hash("grok_sessions", "sess1", "user", "hello", 1)
        h2 = _compute_content_hash("grok_sessions", "sess1", "user", "hello", 2)
        assert h1 != h2

    def test_hash_differs_by_content(self):
        from core.chs.providers.grok_sessions import _compute_content_hash
        h1 = _compute_content_hash("grok_sessions", "sess1", "user", "hello", 1)
        h2 = _compute_content_hash("grok_sessions", "sess1", "user", "world", 1)
        assert h1 != h2


class TestSessionDirParsing:
    """Test Grok session directory path parsing."""

    def test_session_dir_to_source(self):
        from core.chs.providers.grok_sessions import _session_dir_to_source
        d = Path("/fake/.grok/sessions/P%3A%5C/019ffbf4-6734-77a3-bec3-ef4ae502814e")
        result = _session_dir_to_source(d)
        assert result["source_id"] == "019ffbf4-6734-77a3-bec3-ef4ae502814e"
        assert "P:" in result["cwd"]
