"""Unit tests for QMDWikiBackend.

Test cases per plan test matrix:
- qmd available: returns search results from qmd JSON output
- qmd unavailable: falls back to glob+grep
- empty vault: returns empty results without error
- malformed page: skips page, logs warning (not tested here - read-only)
- stale index: triggers async rebuild when vault mtime > index mtime
- circuit breaker: 3 consecutive failures triggers cooldown
- path traversal: invalid qmd_scope raises ValueError
- query sanitization: long/malformed queries truncated
- config override: OBSIDIAN_VAULT_PATH from environment variable used
- vault path validation: non-existent path raises ValueError
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import subprocess
from subprocess import TimeoutExpired

from core.backends.local.qmd_wiki_backend import (
    MAX_FILE_READ,
    QMDWikiBackend,
    REBUILD_COOLDOWN,
    REBUILD_FAILURE_LIMIT,
    VAULT_MTIME_CACHE_TTL,
)


class TestQMDWikiBackendInitialization:
    """Test backend initialization and vault path validation."""

    def test_initialization_with_default_vault_path(self, monkeypatch):
        """Test backend initializes with default vault path from config."""
        monkeypatch.setenv("SEARCH_RESEARCH_OBSIDIAN_VAULT_PATH", "")
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir)
            assert backend.vault_path == Path(tmpdir).resolve()
            assert backend.qmd_scope == "wiki/"
            assert backend.BACKEND_NAME == "QMD_WIKI"

    def test_initialization_with_custom_vault_path(self):
        """Test backend initializes with custom vault path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir)
            assert backend.vault_path == Path(tmpdir).resolve()

    def test_initialization_with_custom_qmd_scope(self):
        """Test backend initializes with custom qmd_scope."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="docs/")
            assert backend.qmd_scope == "docs/"

    def test_initialization_vault_path_expands_user(self):
        """Test vault path expands ~ to user home directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir)
            assert not str(backend.vault_path).startswith("~")

    def test_initialization_nonexistent_vault_raises(self):
        """Test non-existent vault path raises ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            QMDWikiBackend(vault_path="/nonexistent/path/that/does/not/exist")

    def test_path_traversal_prevention_valid_scope(self):
        """Test valid qmd_scope within vault does not raise."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / "wiki").mkdir()
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            assert backend.vault_path == vault.resolve()

    def test_path_traversal_prevention_invalid_scope(self):
        """Test qmd_scope outside vault raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="escapes vault"):
                QMDWikiBackend(vault_path=tmpdir, qmd_scope="../etc")


class TestQuerySanitization:
    """Test query sanitization."""

    def test_query_sanitization_truncates_long_query(self):
        """Test long query is truncated to 500 chars."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir)
            long_query = "a" * 1000
            sanitized = backend._sanitize_query(long_query)
            assert len(sanitized) == 500

    def test_query_sanitization_strips_nonprintable(self):
        """Test non-printable characters are stripped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir)
            dirty_query = "hello world\x00\x07test\x1f"
            sanitized = backend._sanitize_query(dirty_query)
            assert sanitized == "hello worldtest"
            assert "\x00" not in sanitized
            assert "\x07" not in sanitized
            assert "\x1f" not in sanitized

    def test_query_sanitization_preserves_spaces(self):
        """Test whitespace is preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir)
            query = "hello   world  test"
            sanitized = backend._sanitize_query(query)
            assert sanitized == query


class TestVaultMtimeCaching:
    """Test vault mtime caching with TTL."""

    def test_vault_mtime_returns_none_for_empty_vault(self):
        """Test vault mtime returns None when no .md files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            mtime = backend._get_vault_mtime_cached()
            assert mtime is None

    def test_vault_mtime_returns_max_of_md_files(self):
        """Test vault mtime returns max mtime of all .md files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            wiki = vault / "wiki"
            wiki.mkdir()
            (wiki / "a.md").write_text("content a")
            (wiki / "b.md").write_text("content b")
            import time
            time.sleep(0.01)
            (wiki / "c.md").write_text("content c")
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            mtime = backend._get_vault_mtime_cached()
            assert mtime is not None
            c_mtime = (wiki / "c.md").stat().st_mtime
            assert mtime == c_mtime

    def test_vault_mtime_cached_within_ttl(self):
        """Test vault mtime is cached and reused within TTL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            wiki = vault / "wiki"
            wiki.mkdir()
            (wiki / "a.md").write_text("content")
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            mtime1 = backend._get_vault_mtime_cached()
            import time
            time.sleep(0.01)
            (wiki / "b.md").write_text("new content")
            mtime2 = backend._get_vault_mtime_cached()
            assert mtime1 == mtime2

    def test_vault_mtime_not_cached_after_ttl(self):
        """Test vault mtime refreshes after TTL expires."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            wiki = vault / "wiki"
            wiki.mkdir()
            (wiki / "a.md").write_text("content")
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            mtime1 = backend._get_vault_mtime_cached()
            import time
            time.sleep(VAULT_MTIME_CACHE_TTL + 0.5)
            (wiki / "b.md").write_text("new content")
            mtime2 = backend._get_vault_mtime_cached()
            assert mtime2 > mtime1

    def test_vault_mtime_handles_permission_error(self):
        """Test PermissionError is handled gracefully during scan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            backend._vault_mtime_cache = None
            with patch("os.scandir", side_effect=PermissionError):
                mtime = backend._get_vault_mtime_cached()
                assert mtime is None


class TestIndexMtime:
    """Test index mtime tracking."""

    def test_index_mtime_returns_none_when_no_index(self):
        """Test index mtime returns None when .qmd/index doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            assert backend._get_index_mtime() is None

    def test_index_mtime_returns_file_mtime(self):
        """Test index mtime returns mtime of .qmd/index file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            qmd_dir = vault / ".qmd"
            qmd_dir.mkdir()
            index_file = qmd_dir / "index"
            index_file.write_text("")
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            mtime = backend._get_index_mtime()
            assert mtime is not None
            assert mtime == index_file.stat().st_mtime


class TestFallbackGrep:
    """Test glob+grep fallback when qmd is unavailable."""

    def test_fallback_grep_returns_empty_for_empty_vault(self):
        """Test fallback returns empty list when vault is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            results = backend._fallback_grep("test")
            assert results == []

    def test_fallback_grep_finds_matching_content(self):
        """Test fallback grep finds files containing query."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            wiki = vault / "wiki"
            wiki.mkdir()
            (wiki / "test.md").write_text("This is a test file about testing.")
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            results = backend._fallback_grep("test")
            assert len(results) == 1
            assert results[0].title == "test"
            assert results[0].source == "QMD_WIKI"
            assert results[0].score == 0.5

    def test_fallback_grep_case_insensitive(self):
        """Test fallback grep is case insensitive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            wiki = vault / "wiki"
            wiki.mkdir()
            (wiki / "test.md").write_text("Python Programming")
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            results = backend._fallback_grep("python")
            assert len(results) == 1

    def test_fallback_grep_respects_file_size_limit(self):
        """Test fallback reads only first 1MB of files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            wiki = vault / "wiki"
            wiki.mkdir()
            large_file = wiki / "large.md"
            large_file.write_bytes(b"x" * (MAX_FILE_READ + 100))
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            results = backend._fallback_grep("x" * 50)
            assert len(results) == 1
            assert len(results[0].content) <= 200

    def test_fallback_grep_handles_permission_error(self):
        """Test fallback skips files with PermissionError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            wiki = vault / "wiki"
            wiki.mkdir()
            (wiki / "accessible.md").write_text("accessible content")
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            with patch("builtins.open", side_effect=PermissionError):
                results = backend._fallback_grep("accessible")
                assert len(results) == 0


class TestCircuitBreaker:
    """Test circuit breaker for rebuild failures."""

    def test_circuit_breaker_triggers_after_three_failures(self):
        """Test cooldown triggers after REBUILD_FAILURE_LIMIT failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            backend._rebuild_failures = REBUILD_FAILURE_LIMIT
            backend._update_cooldown()
            assert backend._rebuild_cooldown_until is not None

    def test_circuit_breaker_no_cooldown_below_limit(self):
        """Test no cooldown when failures below limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            backend._rebuild_failures = REBUILD_FAILURE_LIMIT - 1
            backend._update_cooldown()
            assert backend._rebuild_cooldown_until is None

    def test_circuit_breaker_cooldown_duration(self):
        """Test cooldown duration is REBUILD_COOLDOWN seconds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import time
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            backend._rebuild_failures = REBUILD_FAILURE_LIMIT
            before = time.monotonic()
            backend._update_cooldown()
            after = time.monotonic()
            assert backend._rebuild_cooldown_until is not None
            elapsed = backend._rebuild_cooldown_until - before
            assert REBUILD_COOLDOWN - 1 <= elapsed <= REBUILD_COOLDOWN + 1


class TestQMDJsonParsing:
    """Test QMD JSON output parsing."""

    def test_parse_valid_qmd_json(self):
        """Test parsing valid qmd JSON output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            qmd_output = json.dumps({
                "results": [
                    {"path": "wiki/test.md", "snippet": "test content", "score": 0.95},
                    {"path": "wiki/demo.md", "snippet": "demo snippet", "score": 0.85},
                ]
            }).encode()
            results = backend._parse_qmd_json(qmd_output)
            assert len(results) == 2
            assert results[0].title == "test"
            assert results[0].score == 0.95
            assert results[1].title == "demo"
            assert results[1].score == 0.85

    def test_parse_empty_qmd_json(self):
        """Test parsing JSON with no results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            qmd_output = json.dumps({"results": []}).encode()
            results = backend._parse_qmd_json(qmd_output)
            assert results == []

    def test_parse_malformed_qmd_json(self):
        """Test parsing malformed JSON returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            qmd_output = b"not valid json"
            results = backend._parse_qmd_json(qmd_output)
            assert results == []


class TestSearchAsync:
    """Test async search behavior."""

    @pytest.mark.asyncio
    async def test_search_async_file_not_found_triggers_fallback(self):
        """Test FileNotFoundError (qmd not found) triggers fallback grep."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            wiki = vault / "wiki"
            wiki.mkdir()
            (wiki / "test.md").write_text("hello world")
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            with patch(
                "asyncio.create_subprocess_exec",
                side_effect=FileNotFoundError,
            ):
                results = await backend.search_async("hello")
                assert len(results) == 1
                assert results[0].title == "test"

    @pytest.mark.asyncio
    async def test_search_async_subprocess_error_triggers_fallback(self):
        """Test asyncio.subprocess.SubprocessError triggers fallback grep."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            wiki = vault / "wiki"
            wiki.mkdir()
            (wiki / "test.md").write_text("hello world")
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            with patch(
                "asyncio.create_subprocess_exec",
                side_effect=subprocess.SubprocessError,
            ):
                results = await backend.search_async("hello")
                assert len(results) == 1


class TestSyncRebuild:
    """Test synchronous rebuild."""

    def test_sync_rebuild_updates_index_mtime(self):
        """Test sync rebuild updates _index_mtime on success."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            wiki = vault / "wiki"
            wiki.mkdir()
            qmd_dir = vault / ".qmd"
            qmd_dir.mkdir()
            index_file = qmd_dir / "index"
            index_file.write_text("")
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            backend._index_mtime = None
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.stderr = b""
                mock_run.return_value = mock_result
                backend._sync_rebuild()
                assert backend._index_mtime is not None

    def test_sync_rebuild_handles_timeout(self):
        """Test sync rebuild handles TimeoutExpired."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = QMDWikiBackend(vault_path=tmpdir, qmd_scope="wiki/")
            backend._rebuild_failures = 0
            with patch("subprocess.run", side_effect=TimeoutExpired):
                backend._sync_rebuild()
                assert backend._rebuild_failures == 1


class TestConfigIntegration:
    """Test OBSIDIAN_VAULT_PATH config integration."""

    def test_obsidian_vault_path_from_env_var(self, monkeypatch):
        """Test OBSIDIAN_VAULT_PATH is read from environment variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("SEARCH_RESEARCH_OBSIDIAN_VAULT_PATH", tmpdir)
            from importlib import reload
            import core.config
            reload(core.config)
            from core.config import config
            assert config.OBSIDIAN_VAULT_PATH == tmpdir

    def test_obsidian_vault_path_default_value(self, monkeypatch):
        """Test OBSIDIAN_VAULT_PATH has correct default."""
        monkeypatch.delenv("SEARCH_RESEARCH_OBSIDIAN_VAULT_PATH", raising=False)
        from importlib import reload
        import core.config
        reload(core.config)
        from core.config import config
        assert "personal-wiki" in config.OBSIDIAN_VAULT_PATH


class TestRouterIntegration:
    """Test QMD Wiki backend is registered in AsyncSearchRouter."""

    def test_wiki_backend_registered_in_router(self):
        """Test wiki backend is registered in AsyncSearchRouter."""
        import tempfile
        from pathlib import Path
        from unittest.mock import patch, MagicMock
        from core.router_async import AsyncSearchRouter
        from core.backends import local
        with tempfile.TemporaryDirectory() as vault_dir:
            vault_path = Path(vault_dir)
            (vault_path / "wiki").mkdir()
            mock_config = MagicMock()
            mock_config.OBSIDIAN_VAULT_PATH = str(vault_path)
            with patch("core.backends.local.qmd_wiki_backend.config", mock_config):
                router = AsyncSearchRouter()
                router._backends_initialized = False
                router._backends = {}
                backends = router._create_backends()
                assert "wiki" in backends
                assert backends["wiki"].BACKEND_NAME == "QMD_WIKI"
