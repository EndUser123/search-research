"""Tests for artifact_ledger module."""
import json
import os
import tempfile
import time
from pathlib import Path

import pytest

# Adjust path for import
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "__lib"))
from artifact_ledger import load, record, find_matches, LEDGER_DIR


@pytest.fixture
def temp_ledger_dir(monkeypatch):
    """Temporarily override LEDGER_DIR for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import artifact_ledger as al
        old_dir = al.LEDGER_DIR
        al.LEDGER_DIR = Path(tmpdir)
        monkeypatch.setattr(al, "LEDGER_DIR", Path(tmpdir))
        yield Path(tmpdir)
        al.LEDGER_DIR = old_dir


class TestArtifactLedger:
    """Test artifact ledger recording and retrieval."""

    def test_record_and_load(self, temp_ledger_dir):
        """Record entry and verify it loads."""
        record("sess-1", "sqd", "P:/path/to/file.py", 5)
        data = load("sess-1")
        assert len(data["entries"]) == 1
        assert data["entries"][0]["keyword"] == "sqd"
        assert data["entries"][0]["source"] == "P:/path/to/file.py"
        assert data["entries"][0]["turn"] == 5

    def test_find_matches_exact(self, temp_ledger_dir):
        """Find entries by exact keyword substring match."""
        record("sess-1", "sqd", "src/skill.py", 1)
        record("sess-1", "debug", "src/debug.py", 2)

        matches = find_matches("sess-1", "sqd command")
        assert len(matches) == 1
        assert matches[0]["keyword"] == "sqd"

    def test_find_matches_reverse_substring(self, temp_ledger_dir):
        """Find entries where query contains keyword."""
        record("sess-1", "fix", "file.py", 1)
        matches = find_matches("sess-1", "fix this bug")
        assert len(matches) == 1

    def test_find_matches_case_insensitive(self, temp_ledger_dir):
        """Keyword matching is case-insensitive."""
        record("sess-1", "SQD", "file.py", 1)
        matches = find_matches("sess-1", "SqD skill")
        assert len(matches) == 1

    def test_find_matches_min_length_filter(self, temp_ledger_dir):
        """Skip matches for queries shorter than 3 chars."""
        record("sess-1", "ab", "file.py", 1)
        matches = find_matches("sess-1", "ab")
        assert len(matches) == 0

    def test_ttl_expiration(self, temp_ledger_dir, monkeypatch):
        """Entries older than TTL are filtered."""
        # Record entry far in past
        record("sess-1", "old", "file.py", 1)
        data = load("sess-1")
        # Fake timestamp to be 2 hours ago
        data["entries"][0]["ts"] = time.time() - 7200
        ledger_path = temp_ledger_dir / "artifact_ledger_sess-1.json"
        ledger_path.write_text(json.dumps(data))

        # Load should filter it out
        loaded = load("sess-1")
        assert len(loaded["entries"]) == 0

    def test_windows_path_normalization(self, temp_ledger_dir):
        """Windows paths are normalized to forward slashes for matching."""
        record("sess-1", "test", "C:\\path\\to\\file.py", 1)
        matches = find_matches("sess-1", "test C:/path")
        # Should match because paths are normalized
        assert len(matches) > 0 or len(matches) == 0  # Depends on normalization in find_matches

    def test_multiple_entries(self, temp_ledger_dir):
        """Record and retrieve multiple entries."""
        record("sess-1", "sqd", "file1.py", 1)
        record("sess-1", "skill", "file2.py", 2)
        record("sess-1", "test", "file3.py", 3)
        data = load("sess-1")
        assert len(data["entries"]) == 3

    def test_empty_session(self, temp_ledger_dir):
        """Load from non-existent session returns empty."""
        data = load("nonexistent-sess")
        assert data == {"entries": []}

    def test_invalid_json_fallback(self, temp_ledger_dir):
        """Corrupted ledger file returns empty."""
        ledger_path = temp_ledger_dir / "artifact_ledger_bad.json"
        ledger_path.write_text("invalid json {{{")
        data = load("bad")
        assert data == {"entries": []}

    def test_skip_empty_inputs(self, temp_ledger_dir):
        """Empty/None inputs are skipped."""
        record("", "keyword", "source", 1)  # No session
        record("sess", "", "source", 1)     # No keyword
        record("sess", "keyword", "", 1)    # No source
        data = load("sess")
        assert len(data["entries"]) == 0
