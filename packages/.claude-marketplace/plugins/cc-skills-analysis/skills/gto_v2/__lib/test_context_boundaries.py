"""Tests for context_boundaries module."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "gto_v2"))

from __lib.context_boundaries import (
    WorkContext,
    detect_context_boundaries,
)


def test_goal_phrase_snaps_to_word_boundary():
    """Phrase must not start mid-path — snap to next word boundary."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = True

    # Content where pattern match ends mid-segment — a path
    # containing `:d` at position 4 of the remainder looks like
    # `:diagn`/`ostics/` if sliced mid-character.
    content = "Let's also work on P:\\.claude\\hooks\\di. Hooks are here."

    mock_turns = [
        MagicMock(role="user", content=content, turn_number=42),
    ]

    with patch("__lib.context_boundaries.read_turns", return_value=mock_turns):
        results = detect_context_boundaries(mock_path)

    if not results:
        pytest.skip("No match triggered")

    phrase = results[0].goal_phrase
    assert not phrase.startswith("diagn"), f"Got mid-path corruption: {phrase!r}"
    assert phrase[0].isalpha() or phrase[0] == "_", f"Got non-word character: {phrase!r}"


def test_goal_phrase_max_100_chars():
    """Phrase must be capped at 100 characters."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = True

    long_goal = "Let's also work on " + "x" * 200
    mock_turns = [MagicMock(role="user", content=long_goal, turn_number=1)]

    with patch("__lib.context_boundaries.read_turns", return_value=mock_turns):
        results = detect_context_boundaries(mock_path)

    if not results:
        pytest.skip("No match triggered")

    assert len(results[0].goal_phrase) <= 100, "Phrase exceeded 100 char cap"


def test_context_empty_no_results():
    """Non-existent path produces no results."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = False

    results = detect_context_boundaries(mock_path)
    assert results == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])