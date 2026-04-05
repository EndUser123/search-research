#!/usr/bin/env python3
"""
Unit tests for tdd/phase_transition_logger.py

Tests:
- Phase transition logging with evidence binding
- Evidence hash computation
- Transition history retrieval
- Transition sequence validation
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


def test_compute_evidence_hash_returns_consistent_hash():
    """Test that same inputs produce same hash."""
    from tdd.phase_transition_logger import compute_evidence_hash

    hash1 = compute_evidence_hash("impl.py", "test output", "impl content")
    hash2 = compute_evidence_hash("impl.py", "test output", "impl content")

    assert hash1 == hash2
    assert len(hash1) == 16  # Short hash


def test_compute_evidence_hash_different_for_different_inputs():
    """Test that different inputs produce different hashes."""
    from tdd.phase_transition_logger import compute_evidence_hash

    hash1 = compute_evidence_hash("impl.py", "test output 1")
    hash2 = compute_evidence_hash("impl.py", "test output 2")

    assert hash1 != hash2


def test_log_phase_transition_creates_record():
    """Test that log_phase_transition creates a PhaseTransition record."""
    from tdd.phase_transition_logger import log_phase_transition

    transition = log_phase_transition(
        from_phase="red",
        to_phase="green",
        impl_path="impl.py",
        session_id="test_session",
        terminal_id="test_terminal",
    )

    assert transition.from_phase == "red"
    assert transition.to_phase == "green"
    assert transition.impl_path == "impl.py"
    assert transition.session_id == "test_session"
    assert transition.terminal_id == "test_terminal"
    assert len(transition.evidence_hash) == 16
    assert transition.timestamp  # Non-empty


def test_log_phase_transition_writes_evidence_file():
    """Test that evidence file is written when evidence_dir provided."""
    from tdd.phase_transition_logger import log_phase_transition

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_dir = Path(tmpdir) / "evidence"
        impl_path = Path(tmpdir) / "impl.py"
        impl_path.write_text("def foo(): return 1")

        transition = log_phase_transition(
            from_phase="red",
            to_phase="green",
            impl_path=str(impl_path),
            evidence_dir=evidence_dir,
            test_output="All tests pass",
        )

        # Check evidence file was created
        assert (evidence_dir / "tdd95").exists()
        evidence_files = list((evidence_dir / "tdd95").rglob("*.json"))
        assert len(evidence_files) == 1


def test_log_phase_transition_handles_enum_phases():
    """Test that enum phases are handled correctly."""
    from tdd.phase_transition_logger import log_phase_transition

    class MockPhase:
        def __init__(self, value):
            self.value = value

    transition = log_phase_transition(
        from_phase=MockPhase("RED"),
        to_phase=MockPhase("GREEN"),
        impl_path="impl.py",
    )

    assert transition.from_phase == "red"
    assert transition.to_phase == "green"


def test_get_transition_history_returns_empty_for_no_evidence():
    """Test that empty list returned when no evidence exists."""
    from tdd.phase_transition_logger import get_transition_history

    with tempfile.TemporaryDirectory() as tmpdir:
        history = get_transition_history("impl.py", Path(tmpdir))
        assert history == []


def test_get_transition_history_returns_transitions():
    """Test that transition history is retrieved correctly."""
    from tdd.phase_transition_logger import get_transition_history, log_phase_transition

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_dir = Path(tmpdir) / "evidence"
        impl_path = Path(tmpdir) / "impl.py"
        impl_path.write_text("def foo(): return 1")

        # Log two transitions
        log_phase_transition(
            from_phase="none",
            to_phase="red",
            impl_path=str(impl_path),
            evidence_dir=evidence_dir,
        )
        log_phase_transition(
            from_phase="red",
            to_phase="green",
            impl_path=str(impl_path),
            evidence_dir=evidence_dir,
        )

        # Get history
        history = get_transition_history(str(impl_path), evidence_dir)

        assert len(history) == 2
        # Newest first
        assert history[0].to_phase == "green"
        assert history[1].to_phase == "red"


def test_validate_transition_sequence_accepts_valid_sequence():
    """Test that valid TDD sequence is accepted."""
    from tdd.phase_transition_logger import PhaseTransition, validate_transition_sequence

    transitions = [
        PhaseTransition("none", "red", "impl.py", "", ""),
        PhaseTransition("red", "green", "impl.py", "", ""),
        PhaseTransition("green", "refactor", "impl.py", "", ""),
        PhaseTransition("refactor", "complete", "impl.py", "", ""),
    ]

    is_valid, reason = validate_transition_sequence(transitions)
    assert is_valid is True
    assert "valid" in reason.lower()


def test_validate_transition_sequence_accepts_loop_back():
    """Test that GREEN→RED failure loop is accepted."""
    from tdd.phase_transition_logger import PhaseTransition, validate_transition_sequence

    transitions = [
        PhaseTransition("none", "red", "impl.py", "", ""),
        PhaseTransition("red", "green", "impl.py", "", ""),
        PhaseTransition("green", "red", "impl.py", "", ""),  # Failure
        PhaseTransition("red", "green", "impl.py", "", ""),  # Retry
    ]

    is_valid, reason = validate_transition_sequence(transitions)
    assert is_valid is True


def test_validate_transition_sequence_rejects_invalid():
    """Test that invalid transition is rejected."""
    from tdd.phase_transition_logger import PhaseTransition, validate_transition_sequence

    transitions = [
        PhaseTransition("none", "complete", "impl.py", "", ""),  # Invalid skip
    ]

    is_valid, reason = validate_transition_sequence(transitions)
    assert is_valid is False
    assert "invalid" in reason.lower()


def test_validate_transition_sequence_empty_list_valid():
    """Test that empty list is considered valid."""
    from tdd.phase_transition_logger import validate_transition_sequence

    is_valid, reason = validate_transition_sequence([])
    assert is_valid is True


def main():
    """Run all tests."""
    import pytest

    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
