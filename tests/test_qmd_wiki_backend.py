"""Tests for QMDWikiBackend."""

import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add search_research package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from search_research.backends.local.qmd_wiki_backend import (
    QMDWikiBackend,
    MAX_FILE_READ,
    REBUILD_COOLDOWN,
    REBUILD_FAILURE_LIMIT,
    VAULT_MTIME_CACHE_TTL,
)


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault matching qmd's config structure.

    qmd config maps "wiki" → ".../personal-wiki/wiki" directly (no wiki/ subdir).
    Files go directly into the vault path, not a nested wiki/ subdirectory.
    """
    vault = tmp_path
    (vault / "entities").mkdir()
    (vault / "concepts").mkdir()
    (vault / "sources").mkdir()
    # Create some test pages at vault root level (matching qmd structure)
    (vault / "test-entity.md").write_text(
        "---\ntitle: Test Entity\ntags:\n  - test\ncreated: 2024-01-01\nsources: []\nsummary: A test entity.\n---\nTest content."
    )
    return tmp_path


class TestQMDWikiBackendConstruction:
    """Tests for QMDWikiBackend initialization."""

    def test_vault_existence_validation(self, tmp_path):
        """Constraint 8: Non-existent vault raises ValueError."""
        with pytest.raises(ValueError, match="Vault path does not exist"):
            QMDWikiBackend(vault_path=str(tmp_path / "nonexistent"))

    def test_path_traversal_prevention_absolute_escapes(self, temp_vault):
        """Constraint 3: Absolute path that escapes vault raises ValueError."""
        # Use absolute path that points outside vault
        parent = temp_vault.parent
        # This should fail because parent is outside vault
        with pytest.raises(ValueError, match="escapes vault directory"):
            QMDWikiBackend(vault_path=str(temp_vault), qmd_scope=str(parent / "evil"))

    def test_valid_qmd_scope_works(self, temp_vault):
        """Valid qmd_scope within vault works fine."""
        backend = QMDWikiBackend(vault_path=str(temp_vault), qmd_scope="wiki/")
        assert backend.qmd_scope == "wiki/"


class TestQuerySanitization:
    """Tests for query sanitization (Constraint 4)."""

    def test_query_length_limit(self, temp_vault):
        """Query is truncated to 500 characters."""
        backend = QMDWikiBackend(vault_path=str(temp_vault))
        long_query = "a" * 1000
        result = backend._sanitize_query(long_query)
        assert len(result) == 500

    def test_non_printable_stripped(self, temp_vault):
        """Non-printable characters are stripped."""
        backend = QMDWikiBackend(vault_path=str(temp_vault))
        query = "test\x00\x01\x02\x03query"
        result = backend._sanitize_query(query)
        assert "\x00" not in result
        assert "\x01" not in result

    def test_fts5_root_patch_in_place(self, temp_vault):
        """#1064: FTS5 escaping lives at the root in our forked qmd.build_fts5_query.

        Caller-side sanitize was removed; this asserts the install-site patch
        (cc-skills-utils/__lib/qmd_fts5_patch.patch) is actually applied.
        If this fails, qmd was reinstalled/upgraded and the patch was lost —
        re-apply from the .patch file.
        """
        from qmd.core.retrieval import build_fts5_query as f
        assert f("two-levers") == "two levers"
        assert f('foo*bar(baz)/"qux"') == "foo bar baz qux"
        result = f("café- naïve 你好 — Москва")
        assert "café" in result and "你好" in result and "Москва" in result
        assert "-" not in result


class TestVaultMtimeCache:
    """Tests for vault mtime caching (Constraint 11)."""

    def test_vault_mtime_returns_file_mtime(self, temp_vault):
        """Vault mtime returns the latest .md file mtime."""
        backend = QMDWikiBackend(vault_path=str(temp_vault))

        mtime = backend._get_vault_mtime_cached()
        assert mtime is not None
        # File exists in wiki/ so mtime should be set

    def test_empty_vault_returns_none(self, tmp_path):
        """Constraint 10: Empty vault returns None without error."""
        empty_vault = tmp_path / "empty"
        empty_vault.mkdir()
        # With qmd_scope="", _get_vault_mtime_cached() scans empty_vault directly
        backend = QMDWikiBackend(vault_path=str(empty_vault))
        result = backend._get_vault_mtime()
        assert result is None


class TestFallbackGrepLineNumber:
    """Tests for line_number capture in fallback grep."""

    def test_fallback_grep_returns_line_number(self, temp_vault):
        """Fallback grep captures line number of match."""
        # Frontmatter (3 lines: ---, title, ---) shifts content by 3
        # "Decision framework" is on content line 4 = file line 7
        test_file = temp_vault / "dalio-decisions.md"
        test_file.write_text("---\ntitle: Dalio Decisions\n---\nLine 1\nLine 2\nLine 3\nDecision framework here on line 4\nLine 5\n")

        backend = QMDWikiBackend(vault_path=str(temp_vault))
        results = backend._fallback_grep("Decision framework")

        assert len(results) >= 1
        result = results[0]
        assert result.line_number is not None
        assert result.line_number == 7  # frontmatter occupies lines 1-3
        assert result.file_path == str(test_file)

    def test_fallback_grep_line_number_multiple_matches(self, temp_vault):
        """When query appears on multiple lines, returns multiple results with correct line numbers."""
        test_file = temp_vault / "multi-match.md"
        # frontmatter (3 lines) shifts: "Alpha at line 3" → file line 4, "Alpha at line 5" → file line 6
        test_file.write_text("---\ntitle: Multi\n---\nAlpha at line 3\nBeta\nAlpha at line 5\nGamma\n")

        backend = QMDWikiBackend(vault_path=str(temp_vault))
        results = backend._fallback_grep("Alpha")

        assert len(results) == 2
        line_nums = {r.line_number for r in results}
        assert line_nums == {4, 6}  # frontmatter shifts by 3


class TestSearchBatch:
    """Tests for search_batch_async."""

    @pytest.mark.asyncio
    async def test_search_batch_runs_queries(self, temp_vault):
        """search_batch_async runs all queries and returns aggregated results."""
        backend = QMDWikiBackend(vault_path=str(temp_vault))
        queries = ["entity", "test", "content"]

        results = await backend.search_batch_async(queries, limit=5)

        # Should get results from fallback (qmd not available in test env)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_batch_deduplication(self, temp_vault):
        """Two queries returning same file → one result, higher score wins."""
        # Create two files with distinct content
        file1 = temp_vault / "alpha.md"
        file1.write_text("---\ntitle: Alpha\n---\nalpha content here")
        file2 = temp_vault / "beta.md"
        file2.write_text("---\ntitle: Beta\n---\nbeta content here")

        backend = QMDWikiBackend(vault_path=str(temp_vault))

        # Mock search_async to return same file with different scores
        async def mock_search(query, limit=10, **kwargs):
            from search_research.models import SearchResult
            return [
                SearchResult(
                    title="alpha",
                    content="alpha",
                    source="QMD_WIKI",
                    score=0.8 if query == "alpha" else 0.5,
                    file_path=str(file1),
                )
            ]

        with patch.object(backend, 'search_async', side_effect=mock_search):
            results = await backend.search_batch_async(["alpha", "alpha"], limit=5)

        # Same file appears twice via two queries, deduplicated to one
        file_paths = [r.file_path for r in results]
        assert file_paths.count(str(file1)) == 1


class TestFallbackGrep:
    """Tests for glob+grep fallback (Constraint 13)."""

    def test_fallback_finds_content(self, temp_vault):
        """Fallback grep finds content in wiki files."""
        backend = QMDWikiBackend(vault_path=str(temp_vault))
        results = backend._fallback_grep("entity")
        assert len(results) >= 1
        assert "entity" in results[0].content.lower() or "entity" in results[0].title.lower()

    def test_permission_error_handled(self, temp_vault):
        """Constraint 9: PermissionError is handled gracefully."""
        backend = QMDWikiBackend(vault_path=str(temp_vault))

        original_open = open
        def mock_open(*args, **kwargs):
            if str(temp_vault) in str(args[0]):
                raise PermissionError("Permission denied")
            return original_open(*args, **kwargs)

        with patch("builtins.open", side_effect=mock_open):
            results = backend._fallback_grep("test")
            assert results == []  # Should not crash, just skip


class TestCircuitBreaker:
    """Tests for rebuild circuit breaker (Constraint 7)."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_after_failures(self, temp_vault):
        """After REBUILD_FAILURE_LIMIT failures, cooldown is activated."""
        backend = QMDWikiBackend(vault_path=str(temp_vault))

        # Directly set failure count to trigger cooldown
        backend._rebuild_failures = REBUILD_FAILURE_LIMIT
        backend._update_cooldown()

        # Should be in cooldown
        assert backend._rebuild_cooldown_until is not None
        assert backend._rebuild_cooldown_until > time.monotonic()


class TestQMDJSONParsing:
    """Tests for QMD JSON output parsing."""

    def test_valid_qmd_json_parsed(self, temp_vault):
        """Valid qmd JSON output is correctly parsed."""
        backend = QMDWikiBackend(vault_path=str(temp_vault))

        qmd_output = json.dumps([
            {
                "file": "wiki/entities/test.md",
                "snippet": "Test snippet",
                "score": 0.95
            }
        ]).encode()

        results = backend._parse_qmd_json(qmd_output)
        assert len(results) == 1
        assert results[0].title == "test"
        assert results[0].content == "Test snippet"
        assert results[0].score == 0.95

    def test_qmd_json_parses_line_number_from_diff_notation(self, temp_vault):
        """qmd returns @@ -N,M @@ diff notation — line_number extracted."""
        backend = QMDWikiBackend(vault_path=str(temp_vault))

        qmd_output = json.dumps([
            {
                "file": "wiki/concepts/decisions.md",
                "snippet": "@@ -142,5 @@ (141 before, 300 after)\nDecision framework here",
                "score": 0.88,
                "title": "Dalio Decisions"
            }
        ]).encode()

        results = backend._parse_qmd_json(qmd_output)
        assert len(results) == 1
        assert results[0].line_number == 142

    def test_malformed_json_returns_empty(self, temp_vault):
        """Malformed JSON returns empty list."""
        backend = QMDWikiBackend(vault_path=str(temp_vault))
        results = backend._parse_qmd_json(b"not valid json")
        assert results == []

    def test_qmd_json_no_diff_notation_returns_none_line_number(self, temp_vault):
        """qmd snippet without @@ notation leaves line_number as None."""
        backend = QMDWikiBackend(vault_path=str(temp_vault))

        qmd_output = json.dumps([
            {
                "file": "wiki/entities/test.md",
                "snippet": "Plain snippet without line info",
                "score": 0.5
            }
        ]).encode()

        results = backend._parse_qmd_json(qmd_output)
        assert len(results) == 1
        assert results[0].line_number is None


class TestSyncRebuild:
    """Tests for sync rebuild (Constraint 1)."""

    def test_sync_rebuild_uses_subprocess_run(self, temp_vault):
        """Constraint 1: _sync_rebuild uses subprocess.run, not async."""
        backend = QMDWikiBackend(vault_path=str(temp_vault))

        with patch("search_research.backends.local.qmd_wiki_backend.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stderr=b"")
            backend._sync_rebuild()
            # Verify subprocess.run was called with sys.executable -m qmd update
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == sys.executable
            assert call_args[1] == "-m"
            assert call_args[2] == "qmd"
            assert "update" in call_args


class TestIndexMtimeTracking:
    """Tests for index mtime tracking (Constraints 5, 6)."""

    def test_index_mtime_tracks_qmd_index_file(self, temp_vault):
        """Constraint 5: _index_mtime tracks QMD index file mtime, not vault mtime."""
        backend = QMDWikiBackend(vault_path=str(temp_vault))

        # Create fake .qmd/index file
        qmd_dir = temp_vault / ".qmd"
        qmd_dir.mkdir()
        index_file = qmd_dir / "index"
        index_file.write_text("")

        mtime = backend._get_index_mtime()
        assert mtime is not None
        assert abs(mtime - index_file.stat().st_mtime) < 0.1

    def test_index_mtime_none_when_index_missing(self, temp_vault):
        """No .qmd/index file returns None."""
        backend = QMDWikiBackend(vault_path=str(temp_vault))
        assert backend._get_index_mtime() is None
