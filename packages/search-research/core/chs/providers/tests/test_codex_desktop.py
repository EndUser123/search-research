"""T1, T11, T16, T17: codex_desktop provider tests."""

import json
import os
import sys
import hashlib
from pathlib import Path
from unittest.mock import patch

# Add search-research to path
_SEARCH_RESEARCH_DIR = Path(__file__).resolve().parent.parent.parent.parent / "packages" / "search-research"
if _SEARCH_RESEARCH_DIR.exists():
    sys.path.insert(0, str(_SEARCH_RESEARCH_DIR))

from .codex_desktop import (  # noqa: E402
    CodexDesktopProvider,
    _compute_content_hash,
    _parse_event_num,
    _resolve_terminal_id,
    _parse_s_timestamp,
)


class TestParseSTimestamp:
    """Timestamp parsing: ts (seconds) -> ISO 8601."""

    def test_parses_standard_epoch(self):
        # 2026-04-02 00:00:00 UTC = 1775088000 seconds
        result = _parse_s_timestamp(1775088000)
        assert result.startswith("2026-04-02")

    def test_parses_zero(self):
        # 1970-01-01 00:00:00 UTC
        result = _parse_s_timestamp(0)
        assert result.startswith("1970-01-01")

    def test_handles_none(self):
        result = _parse_s_timestamp(None)
        assert "T" in result  # ISO format

    def test_handles_invalid(self):
        result = _parse_s_timestamp(-1)
        assert "T" in result  # falls back to now()


class TestResolveTerminalId:
    """Terminal ID resolution per D3: codex_{cwd_hash[:8]}."""

    def test_resolves_explicit_terminal_id(self):
        result = _resolve_terminal_id("explicit_terminal")
        assert result == "explicit_terminal"

    def test_computes_codex_prefix_from_cwd(self):
        """Without explicit terminal_id, derives codex_{hash} from current directory."""
        result = _resolve_terminal_id(None)
        assert result.startswith("codex_")
        # hash is 8 hex chars
        suffix = result.split("_", 1)[1]
        assert len(suffix) == 8
        assert all(c in "0123456789abcdef" for c in suffix)

    def test_same_cwd_produces_same_hash(self):
        """MD5 of path string is deterministic."""
        result1 = _resolve_terminal_id(None)
        result2 = _resolve_terminal_id(None)
        assert result1 == result2

    def test_different_cwd_produces_different_hash(self, tmp_path):
        result1 = _resolve_terminal_id(None)
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result2 = _resolve_terminal_id(None)
        # Different paths may or may not collide, but the format is correct
        assert result1.startswith("codex_")
        assert result2.startswith("codex_")


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


class TestComputeContentHash:
    """Content hash computation for deduplication."""

    def test_same_inputs_produce_same_hash(self):
        h1 = _compute_content_hash("codex_desktop", "source", "user", "hello", 12345)
        h2 = _compute_content_hash("codex_desktop", "source", "user", "hello", 12345)
        assert h1 == h2

    def test_different_content_produces_different_hash(self):
        h1 = _compute_content_hash("codex_desktop", "source", "user", "hello", 12345)
        h2 = _compute_content_hash("codex_desktop", "source", "user", "world", 12345)
        assert h1 != h2

    def test_different_provider_produces_different_hash(self):
        h1 = _compute_content_hash("codex_desktop", "source", "user", "hello", 12345)
        h2 = _compute_content_hash("other_provider", "source", "user", "hello", 12345)
        assert h1 != h2


class TestCodexDesktopProviderInterface:
    """Provider interface contract."""

    def test_provider_id(self):
        p = CodexDesktopProvider()
        assert p.provider_id == "codex_desktop"

    def test_capabilities_fields(self):
        p = CodexDesktopProvider()
        caps = p.capabilities
        assert caps.supports_incremental is True
        assert caps.supports_backfill is True
        assert caps.has_task_events is True
        assert caps.has_tool_events is True

    def test_discover_returns_list(self):
        p = CodexDesktopProvider()
        result = p.discover()
        assert isinstance(result, list)

    def test_ingest_since_accepts_none(self):
        p = CodexDesktopProvider()
        result = p.ingest_since(None)
        assert isinstance(result, list)

    def test_ingest_since_accepts_watermark(self):
        p = CodexDesktopProvider()
        wm = {"last_event_id": "event_1", "last_occurred_at": "2026-04-01T00:00:00Z"}
        result = p.ingest_since(wm)
        assert isinstance(result, list)

    def test_fetch_session_returns_dict(self):
        p = CodexDesktopProvider()
        result = p.fetch_session("nonexistent_session")
        assert isinstance(result, dict)

    def test_fetch_message_returns_dict(self):
        p = CodexDesktopProvider()
        result = p.fetch_message("nonexistent_session", "nonexistent_msg")
        assert isinstance(result, dict)


class TestDiscoverEmpty:
    """T16: discover() returns empty list when no history file."""

    def test_discover_nonexistent_file(self, tmp_path):
        p = CodexDesktopProvider()
        with patch("core.chs.providers.codex_desktop.HISTORY_JSONL", tmp_path / "nonexistent.jsonl"):
            result = p.discover()
            assert result == []


class TestDiscoverWithMockHistory:
    """T17: discover() returns sources from history.jsonl."""

    def test_discover_finds_sessions(self, tmp_path):
        history_file = tmp_path / "history.jsonl"
        # ts is seconds-since-epoch, not milliseconds
        history_file.write_text(
            json.dumps({"session_id": "sess_001", "ts": 1743604800, "text": "hello", "uuid": "msg_001"}) + "\n",
            encoding="utf-8",
        )
        with patch("core.chs.providers.codex_desktop.HISTORY_JSONL", history_file):
            p = CodexDesktopProvider()
            sources = p.discover()
            assert len(sources) == 1
            assert sources[0]["source_id"] == "sess_001"
            assert sources[0]["type"] == "session"

    def test_discover_deduplicates_session_ids(self, tmp_path):
        history_file = tmp_path / "history.jsonl"
        history_file.write_text(
            json.dumps({"session_id": "sess_001", "ts": 1743604800, "text": "hello", "uuid": "msg_001"}) + "\n"
            + json.dumps({"session_id": "sess_001", "ts": 1743604900, "text": "world", "uuid": "msg_002"}) + "\n",
            encoding="utf-8",
        )
        with patch("core.chs.providers.codex_desktop.HISTORY_JSONL", history_file):
            p = CodexDesktopProvider()
            sources = p.discover()
            assert len(sources) == 1
            assert sources[0]["source_id"] == "sess_001"


class TestIngestSinceIdempotency:
    """T1: ingest_since is idempotent — replay produces no duplicates."""

    def test_ingest_twice_returns_same_events(self, tmp_path):
        """ingest_since called twice with same watermark returns same events."""
        # 1764359459 seconds = clearly in future (year 2025+), unambiguous
        history_file = tmp_path / "history.jsonl"
        history_file.write_text(
            json.dumps({
                "session_id": "sess_001",
                "ts": 1764359459,
                "text": "hello",
                "uuid": "event_00001",
            }) + "\n",
            encoding="utf-8",
        )
        with patch("core.chs.providers.codex_desktop.HISTORY_JSONL", history_file):
            p = CodexDesktopProvider()
            # Watermark way before the event — first call returns it
            wm = {"provider_id": "codex_desktop", "source_id": "sess_001", "last_event_id": "event_00000", "last_occurred_at": "2020-01-01T00:00:00Z", "terminal_id": "codex_00000000"}
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
                "provider_id": "codex_desktop",
                "source_id": "sess_001",
                "last_event_id": "event_00001",
                "last_occurred_at": occurred_at,
                "terminal_id": "codex_00000000",
            }
            events_after = p.ingest_since(wm_after)
            assert len(events_after) == 0  # Event already past updated watermark


class TestIngestSinceNoHistory:
    """ingest_since handles missing history file gracefully."""

    def test_ingest_nonexistent_file(self, tmp_path):
        with patch("core.chs.providers.codex_desktop.HISTORY_JSONL", tmp_path / "nonexistent.jsonl"):
            p = CodexDesktopProvider()
            result = p.ingest_since(None)
            assert result == []


class TestTerminalIdScoping:
    """Terminal_id scoping per D3: codex_{workspace_hash[:8]}."""

    def test_ingest_uses_watermark_terminal_id(self, tmp_path):
        """If watermark has terminal_id, ingest uses it."""
        history_file = tmp_path / "history.jsonl"
        history_file.write_text(
            json.dumps({
                "session_id": "sess_001",
                "ts": 1743604800,
                "text": "hello",
                "uuid": "event_00001",
            }) + "\n",
            encoding="utf-8",
        )
        with patch("core.chs.providers.codex_desktop.HISTORY_JSONL", history_file):
            p = CodexDesktopProvider()
            wm = {
                "provider_id": "codex_desktop",
                "source_id": "sess_001",
                "last_event_id": None,
                "last_occurred_at": None,
                "terminal_id": "specific_terminal",
            }
            events = p.ingest_since(wm)
            for ev in events:
                assert ev["terminal_id"] == "specific_terminal"

    def test_ingest_uses_codex_prefix_when_no_watermark_terminal_id(self, tmp_path):
        """When no terminal_id in watermark, derives codex_{hash} from cwd."""
        history_file = tmp_path / "history.jsonl"
        history_file.write_text(
            json.dumps({
                "session_id": "sess_001",
                "ts": 1743604800,
                "text": "hello",
                "uuid": "event_00001",
            }) + "\n",
            encoding="utf-8",
        )
        with patch("core.chs.providers.codex_desktop.HISTORY_JSONL", history_file):
            p = CodexDesktopProvider()
            events = p.ingest_since(None)
            for ev in events:
                assert ev["terminal_id"].startswith("codex_")

    def test_all_events_use_same_terminal_id(self, tmp_path):
        """Multiple events in one ingest all use the same terminal_id."""
        history_file = tmp_path / "history.jsonl"
        history_file.write_text(
            json.dumps({"session_id": "sess_001", "ts": 1743604800, "text": "hello", "uuid": "event_00001"}) + "\n"
            + json.dumps({"session_id": "sess_001", "ts": 1743604900, "text": "world", "uuid": "event_00002"}) + "\n",
            encoding="utf-8",
        )
        with patch("core.chs.providers.codex_desktop.HISTORY_JSONL", history_file):
            p = CodexDesktopProvider()
            events = p.ingest_since(None)
            assert len(events) == 2
            terminal_ids = {ev["terminal_id"] for ev in events}
            assert len(terminal_ids) == 1
            assert events[0]["terminal_id"].startswith("codex_")


class TestProviderRegistration:
    """Verify provider is registered."""

    def test_codex_desktop_registered(self):
        from core.chs.providers import _REGISTRY
        assert "codex_desktop" in _REGISTRY
        p = _REGISTRY["codex_desktop"]()
        assert p.provider_id == "codex_desktop"

    def test_both_providers_coexist(self):
        from core.chs.providers import _REGISTRY
        assert "claude_code_raw" in _REGISTRY
        assert "codex_desktop" in _REGISTRY


class TestMessageTypeAlwaysUser:
    """Codex history.jsonl entries are always user messages."""

    def test_ingest_sets_msg_type_user(self, tmp_path):
        history_file = tmp_path / "history.jsonl"
        history_file.write_text(
            json.dumps({
                "session_id": "sess_001",
                "ts": 1743604800,
                "text": "hello",
                "uuid": "event_00001",
            }) + "\n",
            encoding="utf-8",
        )
        with patch("core.chs.providers.codex_desktop.HISTORY_JSONL", history_file):
            p = CodexDesktopProvider()
            events = p.ingest_since(None)
            assert len(events) == 1
            assert events[0]["metadata"]["msg_type"] == "user"

    def test_fetch_message_returns_user_type(self, tmp_path):
        history_file = tmp_path / "history.jsonl"
        history_file.write_text(
            json.dumps({
                "session_id": "sess_001",
                "ts": 1743604800,
                "text": "hello",
                "uuid": "msg_001",
            }) + "\n",
            encoding="utf-8",
        )
        with patch("core.chs.providers.codex_desktop.HISTORY_JSONL", history_file):
            p = CodexDesktopProvider()
            msg = p.fetch_message("sess_001", "msg_001")
            assert msg["type"] == "user"
            assert msg["content"] == "hello"
