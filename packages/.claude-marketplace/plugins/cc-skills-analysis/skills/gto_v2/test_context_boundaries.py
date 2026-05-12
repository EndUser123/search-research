"""Tests for context_boundaries word-boundary snap fix."""
from __future__ import annotations

import re


def snap_to_word(remainder: str) -> str:
    """Snap start AND end of remainder to word boundaries, capped at ~100 chars."""
    r = re.search(r"\w", remainder)
    start_offset = r.start() if r else 0
    end_offset = start_offset + 100

    if end_offset < len(remainder):
        pre_end = remainder[start_offset:end_offset]
        # Find complete words in pre_end (word followed by non-word).
        candidates = []
        for m in re.finditer(r"\w+", pre_end):
            word_end = m.end()
            if word_end < len(pre_end):
                following = pre_end[word_end]
                if not following.isalnum() and following != "_":
                    candidates.append((m.start(), word_end))
        if candidates:
            # Snap to end of the last complete word before truncation
            end_offset = start_offset + candidates[-1][1]
        else:
            # No complete word — we're mid-word. Snap back to word start.
            last_match = None
            for m in re.finditer(r"\w+", pre_end):
                last_match = m
            if last_match and last_match.start() > 0:
                end_offset = start_offset + last_match.start()

    return remainder[start_offset:end_offset]


def test_snaps_start_to_word():
    """Start must not be mid-path — `:diagnostics` should snap past `:`."""
    remainder = ":diagnostics/P:/.claude/hooks"
    phrase = snap_to_word(remainder)
    assert phrase[0].isalpha() or phrase[0] == "_", f"Got: {phrase!r}"


def test_snaps_end_to_word():
    """End must not be mid-word — `diagnostics` should snap cleanly."""
    # "diagnostics" is at positions 1-12, followed by 90+ x's.
    # Cut at position 100 lands in the x's. "diagnostics" is complete in pre_end.
    remainder = " diagnostic" + "sthatisnotaword" + "x" * 200
    phrase = snap_to_word(remainder)
    assert not phrase.endswith("stic"), f"Got mid-word end: {phrase!r}"
    assert phrase.endswith("sthatisnotaword"), f"Expected full word: {phrase!r}"


def test_normal_content_unchanged():
    """Normal sentence snaps cleanly to full words."""
    remainder = " work on the hooks module."
    phrase = snap_to_word(remainder)
    assert phrase.startswith("work"), f"Got: {phrase!r}"
    assert phrase.endswith("module"), f"Got: {phrase!r}"


def test_empty_remainder():
    """Empty remainder must not crash."""
    assert snap_to_word("") == ""


def test_already_word_boundary():
    """Already clean start/end stays unchanged."""
    remainder = "work on the hooks module."
    phrase = snap_to_word(remainder)
    assert phrase.startswith("work")


def test_path_mid_segment():
    """.claude/hooks/SomeFile.py — end snaps to `SomeFile`."""
    remainder = ".claude/hooks/SomeFile.py and continue."
    phrase = snap_to_word(remainder)
    assert phrase.startswith("claude") or phrase.startswith("SomeFile")


def test_hooks_di_corruption():
    """The actual bug: path remainder snaps to word boundaries."""
    # After pattern match ends mid-segment, remainder starts mid-path
    remainder = "ostics/P:/.claude/hooks"
    phrase = snap_to_word(remainder)
    # Start must be a word char (snap past leading /)
    assert phrase[0].isalpha(), f"Got: {phrase!r}"
    # End should be clean (not mid-word)
    assert not phrase.endswith("ks"), f"Got mid-word end: {phrase!r}"
    assert phrase == "ostics/P:/.claude/hooks", f"Got: {phrase!r}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
