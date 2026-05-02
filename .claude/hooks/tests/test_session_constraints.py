"""Tests for session_constraints.py.

Covers: correction detection, revocation, persistence, constraint prompt generation.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "__lib"))

from session_constraints import (
    detect_corrections,
    detect_revocations,
    save_constraints,
    load_constraints,
    constraints_active,
    build_constraint_prompt,
    _STATE_DIR,
    _session_file,
)


# ---------------------------------------------------------------------------
# Detection tests
# ---------------------------------------------------------------------------


def test_detect_english_only() -> None:
    assert "english_only" in detect_corrections("Please use English only from now on")


def test_detect_respond_in_english() -> None:
    assert "english_only" in detect_corrections("Respond in English please")


def test_detect_use_english() -> None:
    assert "english_only" in detect_corrections("Use English for all responses")


def test_detect_answer_directly() -> None:
    assert "direct_answer" in detect_corrections("Answer me directly, no preamble")


def test_detect_stop_doing() -> None:
    assert "stop_directive" in detect_corrections("Stop doing that weird formatting")


def test_no_false_positives() -> None:
    assert detect_corrections("What is the English word for this?") == []
    assert detect_corrections("How do I use the direct answer pattern?") == []


def test_detect_empty_input() -> None:
    assert detect_corrections("") == []
    assert detect_corrections("   ") == []


# ---------------------------------------------------------------------------
# Revocation tests
# ---------------------------------------------------------------------------


def test_revoke_english_only() -> None:
    assert "english_only" in detect_revocations("You can use Chinese now again")


def test_revoke_never_mind() -> None:
    assert "*" in detect_revocations("Never mind about the English only thing")


def test_no_false_revocations() -> None:
    assert detect_revocations("English only please") == []


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------


def test_save_and_load_constraints(tmp_path: Path) -> None:
    """Constraints persist to disk and load back correctly."""
    import session_constraints
    original_dir = session_constraints._STATE_DIR
    session_constraints._STATE_DIR = tmp_path
    try:
        save_constraints("test-session", ["english_only", "direct_answer"], [])
        active = constraints_active("test-session")
        assert "english_only" in active
        assert "direct_answer" in active
    finally:
        session_constraints._STATE_DIR = original_dir


def test_removal_persists(tmp_path: Path) -> None:
    """Removing a constraint deletes it from the active set."""
    import session_constraints
    original_dir = session_constraints._STATE_DIR
    session_constraints._STATE_DIR = tmp_path
    try:
        save_constraints("test-session", ["english_only", "direct_answer"], [])
        save_constraints("test-session", [], ["english_only"])
        active = constraints_active("test-session")
        assert "english_only" not in active
        assert "direct_answer" in active
    finally:
        session_constraints._STATE_DIR = original_dir


def test_full_revocation_clears_all(tmp_path: Path) -> None:
    """Revocation with '*' clears all constraints."""
    import session_constraints
    original_dir = session_constraints._STATE_DIR
    session_constraints._STATE_DIR = tmp_path
    try:
        save_constraints("test-session", ["english_only"], [])
        save_constraints("test-session", [], ["*"])
        active = constraints_active("test-session")
        assert active == []
        # File should be deleted
        assert not (tmp_path / "test-session.json").exists()
    finally:
        session_constraints._STATE_DIR = original_dir


def test_no_session_file_returns_empty(tmp_path: Path) -> None:
    """Missing session file returns empty constraints."""
    import session_constraints
    original_dir = session_constraints._STATE_DIR
    session_constraints._STATE_DIR = tmp_path
    try:
        active = constraints_active("nonexistent-session")
        assert active == []
    finally:
        session_constraints._STATE_DIR = original_dir


# ---------------------------------------------------------------------------
# Constraint prompt generation tests
# ---------------------------------------------------------------------------


def test_build_prompt_with_english_only(tmp_path: Path) -> None:
    """English-only constraint generates the right prompt fragment."""
    import session_constraints
    original_dir = session_constraints._STATE_DIR
    session_constraints._STATE_DIR = tmp_path
    try:
        save_constraints("test-session", ["english_only"], [])
        prompt = build_constraint_prompt("test-session")
        assert prompt is not None
        assert "English only" in prompt
        assert "SESSION CONSTRAINT" in prompt
    finally:
        session_constraints._STATE_DIR = original_dir


def test_build_prompt_with_direct_answer(tmp_path: Path) -> None:
    """Direct-answer constraint generates the right prompt fragment."""
    import session_constraints
    original_dir = session_constraints._STATE_DIR
    session_constraints._STATE_DIR = tmp_path
    try:
        save_constraints("test-session", ["direct_answer"], [])
        prompt = build_constraint_prompt("test-session")
        assert prompt is not None
        assert "first sentence" in prompt
    finally:
        session_constraints._STATE_DIR = original_dir


def test_build_prompt_returns_none_when_empty(tmp_path: Path) -> None:
    """No active constraints returns None."""
    import session_constraints
    original_dir = session_constraints._STATE_DIR
    session_constraints._STATE_DIR = tmp_path
    try:
        prompt = build_constraint_prompt("empty-session")
        assert prompt is None
    finally:
        session_constraints._STATE_DIR = original_dir


# ---------------------------------------------------------------------------
# English-only correction persists across turns
# ---------------------------------------------------------------------------


def test_english_only_persists_across_turns(tmp_path: Path) -> None:
    """User says 'English only' on turn 1; constraint is active on turn 2."""
    import session_constraints
    original_dir = session_constraints._STATE_DIR
    session_constraints._STATE_DIR = tmp_path
    try:
        # Turn 1: user correction detected
        corrections = detect_corrections("English only from now on")
        assert corrections == ["english_only"]
        save_constraints("test-session", corrections, [])

        # Turn 2: constraint still active
        prompt = build_constraint_prompt("test-session")
        assert prompt is not None
        assert "English only" in prompt
    finally:
        session_constraints._STATE_DIR = original_dir


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
