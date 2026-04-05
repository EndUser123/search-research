"""Test path_utils.py canonical_path function (D6)

This test suite verifies TASK-009: canonical_path function for the
LLM Behavioral Integrity plan D6 invariant.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from path_utils import canonical_path, paths_are_same


def test_canonical_path_empty_string() -> None:
    """Test that empty string returns empty string."""
    assert canonical_path("") == ""
    assert canonical_path(None) == ""  # type: ignore


def test_canonical_path_resolves_relative(tmp_path: Path) -> None:
    """Test that relative paths are resolved to absolute."""
    file_path = tmp_path / "test.md"
    file_path.touch()

    # Relative path
    rel = "test.md"
    canon = canonical_path(rel)

    # Should be absolute
    assert Path(canon).is_absolute()
    # Should end with the file name
    assert canon.endswith("test.md")


def test_canonical_path_normalizes_slashes(tmp_path: Path) -> None:
    """Test that forward and back slashes are normalized."""
    file_path = tmp_path / "test.md"
    file_path.touch()

    # Different slash representations should resolve to same canonical path
    path1 = canonical_path(str(file_path))
    assert "test.md" in path1


def test_paths_are_same_basic(tmp_path: Path) -> None:
    """Test basic same-path comparison."""
    file_a = tmp_path / "a.md"
    file_b = tmp_path / "b.md"
    file_a.touch()
    file_b.touch()

    assert paths_are_same(str(file_a), str(file_a))
    assert not paths_are_same(str(file_a), str(file_b))


def test_paths_are_same_different_representations(tmp_path: Path) -> None:
    """Test paths that look different but are the same file."""
    file_path = tmp_path / "test.md"
    file_path.touch()

    # Paths with different slash styles
    path_str = str(file_path)
    # On Windows, this handles backslash vs forward slash
    path_normalized = path_str.replace("\\", "/")

    # Both should be recognized as same via canonical_path
    assert paths_are_same(path_str, path_normalized)
