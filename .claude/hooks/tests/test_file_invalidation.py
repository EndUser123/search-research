from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evidence_store import is_file_invalidated, mark_file_invalidated


def test_mark_and_is_invalidated() -> None:
    """Mark a file and check it's invalidated."""
    path = str(Path(__file__).resolve())
    result = mark_file_invalidated(path)
    assert result is True
    assert is_file_invalidated(path) is True


def test_is_invalidated_false_for_clean_file() -> None:
    """File never marked should return False."""
    assert is_file_invalidated("P:/nonexistent/clean/file.txt") is False


def test_mark_invalidated_empty_path_returns_false() -> None:
    """Empty path should return False (fail open)."""
    assert mark_file_invalidated("") is False


def test_is_file_invalidated_empty_path_returns_false() -> None:
    """Empty path should return False (fail open)."""
    assert is_file_invalidated("") is False


def test_mark_file_invalidated_with_session() -> None:
    """Mark with session_id and terminal_id should succeed."""
    path = str(Path(__file__).resolve())
    result = mark_file_invalidated(path, session_id="test-session-123", terminal_id="console_test")
    assert result is True


def test_replacement_mark_overwrites() -> None:
    """Marking same file twice (replacement) should succeed."""
    path = str(Path(__file__).resolve())
    mark_file_invalidated(path, session_id="session-1")
    mark_file_invalidated(path, session_id="session-2")
    # Still invalidated (was replaced, not added)
    assert is_file_invalidated(path) is True


def test_invalidated_persists_across_calls() -> None:
    """Invalidation state should persist across multiple is_file_invalidated calls."""
    path = str(Path(__file__).resolve())
    mark_file_invalidated(path)
    # First check
    assert is_file_invalidated(path) is True
    # Second check (verifies persistence)
    assert is_file_invalidated(path) is True
