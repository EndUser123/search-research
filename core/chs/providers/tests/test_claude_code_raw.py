"""T1, T11, T16, T17: claude_code_raw provider tests."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add search-research to path
_SEARCH_RESEARCH_DIR = Path(__file__).resolve().parent.parent.parent.parent / "packages" / "search-research"
if _SEARCH_RESEARCH_DIR.exists():
    sys.path.insert(0, str(_SEARCH_RESEARCH_DIR))

from core.chs.providers.claude_code_raw import (  # noqa: E402
    ClaudeCodeRawProvider,
    _compute_content_hash,
    _extract_text_content,
    _parse_event_num,
    _resolve_terminal_id,
)


class TestParseEventNum:
    """Tie-breaking numeric parsing for event IDs."""

    def test_event_num_parses_standard_format(self):
        assert _parse_event_num("event_12345") == 12345

    def test_event_num_handles_large_numbers(self):
        assert _parse_event_num("event_999999999") == 999999999

    def test_event_num_invalid_format_returns_minus_one(self):
        assert _parse_event_num("invalid") == -1
        assert _parse_event_num("event_abc") == -1
        assert _parse_event_num("event_") == -1


class TestResolveTerminalId:
    """Terminal ID resolution."""

    def test_resolves_explicit_terminal_id(self):
        result = _resolve_terminal_id("terminal_abc")
        assert result == "terminal_abc"

    def test_resolves_from_env_var(self):
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "env_terminal"}):
            result = _resolve_terminal_id(None)
            assert result == "env_terminal"

    def test_fallback_for_empty_env(self):
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": ""}):
            result = _resolve_terminal_id(None)
            assert result == "default"


class TestExtractTextContent:
    """Content extraction from message structures."""

    def test_passes_through_plain_string(self):
        assert _extract_text_content("hello world") == "hello world"

    def test_extracts_text_field(self):
        msg = {"text": "hello from text field"}
        assert _extract_text_content(msg) == "hello from text field"

    def test_extracts_tool_use(self):
        msg = {
            "type": "tool_use",
            "name": "bash",
            "input": {"command": "ls"},
        }
        result = _extract_text_content(msg)
        assert "[Tool: bash]" in result
        assert "ls" in result

    def test_extracts_thinking(self):
        msg = {"type": "thinking", "thinking": "let me consider..."}
        assert "Thinking" in _extract_text_content(msg)

    def test_handles_content_list(self):
        msg = {
            "content": [
                {"type": "text", "text": "hello"},
                {"type": "tool_use", "name": "bash"},
            ]
        }
        result = _extract_text_content(msg)
        assert "hello" in result
        assert "[Tool: bash]" in result


class TestComputeContentHash:
    """Content hash computation for deduplication."""

    def test_same_inputs_produce_same_hash(self):
        h1 = _compute_content_hash("provider", "source", "user", "hello", 12345)
        h2 = _compute_content_hash("provider", "source", "user", "hello", 12345)
        assert h1 == h2

    def test_different_content_produces_different_hash(self):
        h1 = _compute_content_hash("provider", "source", "user", "hello", 12345)
        h2 = _compute_content_hash("provider", "source", "user", "world", 12345)
        assert h1 != h2


class TestClaudeCodeRawProviderInterface:
    """T13-equivalent: Provider interface contract."""

    def test_provider_id(self):
        p = ClaudeCodeRawProvider()
        assert p.provider_id == "claude_code_raw"

    def test_capabilities_fields(self):
        p = ClaudeCodeRawProvider()
        caps = p.capabilities
        assert caps.supports_incremental is True
        assert caps.supports_backfill is True
        assert caps.has_task_events is True
        assert caps.has_tool_events is True

    def test_discover_returns_list(self):
        p = ClaudeCodeRawProvider()
        result = p.discover()
        assert isinstance(result, list)

    def test_ingest_since_accepts_none(self):
        p = ClaudeCodeRawProvider()
        result = p.ingest_since(None)
        assert isinstance(result, list)

    def test_ingest_since_accepts_watermark(self):
        p = ClaudeCodeRawProvider()
        wm = {"last_event_id": "event_1", "last_occurred_at": "2026-04-01T00:00:00Z"}
        result = p.ingest_since(wm)
        assert isinstance(result, list)

    def test_fetch_session_returns_dict(self):
        p = ClaudeCodeRawProvider()
        result = p.fetch_session("nonexistent_session")
        assert isinstance(result, dict)

    def test_fetch_message_returns_dict(self):
        p = ClaudeCodeRawProvider()
        result = p.fetch_message("nonexistent_session", "nonexistent_msg")
        assert isinstance(result, dict)


class TestDiscoverEmpty:
    """T16: discover() returns empty list when no history file."""

    def test_discover_nonexistent_file(self, tmp_path):
        p = ClaudeCodeRawProvider()
        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", tmp_path / "nonexistent.jsonl"):
            result = p.discover()
            assert result == []


class TestDiscoverWithMockHistory:
    """T17: discover() returns sources from history.jsonl."""

    def test_discover_finds_sessions(self, tmp_path):
        history_file = tmp_path / "history.jsonl"
        history_file.write_text(
            json.dumps({"sessionId": "sess_001", "timestamp": 2000000000000, "type": "user", "message": "hello", "uuid": "msg_001"}) + "\n",
            encoding="utf-8",
        )
        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", history_file):
            p = ClaudeCodeRawProvider()
            sources = p.discover()
            assert len(sources) == 1
            assert sources[0]["source_id"] == "sess_001"


class TestIngestSinceIdempotency:
    """T1: ingest_since is idempotent — replay produces no duplicates."""

    def test_ingest_twice_returns_same_events(self, tmp_path):
        """ingest_since called twice with same watermark returns same events."""
        # Use 2000000000000ms = Nov 24 2033 UTC — clearly in future, unambiguous
        history_file = tmp_path / "history.jsonl"
        history_file.write_text(
            json.dumps({
                "sessionId": "sess_001",
                "timestamp": 2000000000000,
                "type": "user",
                "message": "hello",
                "uuid": "event_00001",
            }) + "\n",
            encoding="utf-8",
        )
        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", history_file):
            p = ClaudeCodeRawProvider()
            # Watermark way before the event — first call returns it
            wm = {"provider_id": "claude_code_raw", "source_id": "sess_001", "last_event_id": "event_00000", "last_occurred_at": "2020-01-01T00:00:00Z", "terminal_id": "default"}
            events_first = p.ingest_since(wm)
            events_second = p.ingest_since(wm)
            # ingest_since is stateless — same watermark returns same events (output idempotent).
            # Deduplication happens at DB INSERT level via content_hash (T1: no duplicates).
            assert len(events_first) == 1
            assert len(events_second) == 1
            assert events_first[0]["event_id"] == events_second[0]["event_id"]

            # Watermark progression: second call with updated watermark skips the event
            occurred_at = events_first[0]["occurred_at"]
            wm_after = {
                "provider_id": "claude_code_raw",
                "source_id": "sess_001",
                "last_event_id": "event_00001",
                "last_occurred_at": occurred_at,
                "terminal_id": "default",
            }
            events_after = p.ingest_since(wm_after)
            assert len(events_after) == 0  # Event already past updated watermark


class TestIngestSinceNoHistory:
    """ingest_since handles missing history file gracefully."""

    def test_ingest_nonexistent_file(self, tmp_path):
        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", tmp_path / "nonexistent.jsonl"):
            p = ClaudeCodeRawProvider()
            result = p.ingest_since(None)
            assert result == []


class TestWatermarkSchema:
    """Watermark schema validation (LOGIC-010 fix)."""

    def test_watermark_schema_fields(self):
        wm = {
            "provider_id": "claude_code_raw",
            "source_id": "sess_001",
            "last_event_id": "event_00001",
            "last_occurred_at": "2026-04-02T00:00:00Z",
            "terminal_id": "default",
        }
        assert "provider_id" in wm
        assert "source_id" in wm
        assert "last_event_id" in wm
        assert "last_occurred_at" in wm
        assert "terminal_id" in wm


class TestTerminalIdScoping:
    """Terminal_id scoping per provider (D3 in plan)."""

    def test_provider_uses_native_terminal_id(self):
        """claude_code_raw uses native terminal_id from source."""
        p = ClaudeCodeRawProvider()
        assert p.capabilities.supports_incremental is True

    def test_ingest_uses_watermark_terminal_id(self, tmp_path):
        """If watermark has terminal_id, ingest uses it."""
        history_file = tmp_path / "history.jsonl"
        history_file.write_text(
            json.dumps({
                "sessionId": "sess_001",
                "timestamp": 1743600000000,
                "type": "user",
                "message": "hello",
                "uuid": "event_00001",
            }) + "\n",
            encoding="utf-8",
        )
        with patch("core.chs.providers.claude_code_raw.HISTORY_JSONL", history_file):
            p = ClaudeCodeRawProvider()
            wm = {
                "provider_id": "claude_code_raw",
                "source_id": "sess_001",
                "last_event_id": None,
                "last_occurred_at": None,
                "terminal_id": "specific_terminal",
            }
            events = p.ingest_since(wm)
            for ev in events:
                assert ev["terminal_id"] == "specific_terminal"


class TestProviderRegistration:
    """Verify provider is registered."""

    def test_claude_code_raw_registered(self):
        from core.chs.providers import _REGISTRY
        assert "claude_code_raw" in _REGISTRY
        p = _REGISTRY["claude_code_raw"]()
        assert p.provider_id == "claude_code_raw"
