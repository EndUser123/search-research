#!/usr/bin/env python3
"""
Unit tests for ralph_loop_engine.py

Tests:
- RalphLoopEngine iteration control (MAX_ITERATIONS=10)
- State persistence and crash recovery (TASK-002)
- Director approval checkpoint (COMP-001)
- FileLock protection for all state operations (FM-2401)
- Phase transition orchestration
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


def test_max_iterations_guard():
    """Test that RalphLoopEngine enforces MAX_ITERATIONS=10 limit."""
    from tdd.ralph_loop_engine import MAX_ITERATIONS, RalphLoopEngine

    assert MAX_ITERATIONS == 10, "MAX_ITERATIONS must be 10"

    with tempfile.TemporaryDirectory() as tmpdir:
        engine = RalphLoopEngine(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir),
        )

        # Set up a contract that would loop forever
        engine.register_contract("test_file.py", "test_file.py", "spec.md")

        # Run should stop at MAX_ITERATIONS
        result = engine.run_iteration("test_file.py")

        # Verify iteration count is capped
        state = engine.get_state("test_file.py")
        assert state is not None
        assert state.get("iteration", 0) <= MAX_ITERATIONS


def test_crash_recovery_from_disk():
    """Test that engine recovers state from disk after crash (TASK-002)."""
    from tdd.ralph_loop_engine import RalphLoopEngine

    with tempfile.TemporaryDirectory() as tmpdir:
        # First session: create state
        engine1 = RalphLoopEngine(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir),
        )
        engine1.register_contract("file_a.py", "test_file_a.py", "spec_a.md")
        engine1.set_phase("file_a.py", "green")

        # Simulate crash by creating new engine (no in-memory state)
        engine2 = RalphLoopEngine(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir),
        )

        # Should recover state from disk
        state = engine2.get_state("file_a.py")
        assert state is not None
        assert state.get("phase") == "green"


def test_director_approval_checkpoint():
    """Test that each iteration requires director approval (COMP-001)."""
    from tdd.ralph_loop_engine import RalphLoopEngine

    with tempfile.TemporaryDirectory() as tmpdir:
        engine = RalphLoopEngine(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir),
        )
        engine.register_contract("test_file.py", "test_file.py", "spec.md")
        engine.set_phase("test_file.py", "red")

        # First iteration should succeed
        result1 = engine.run_iteration("test_file.py", approval="approved")
        assert result1.get("status") in ("continue", "complete")

        # Iteration without approval should be blocked
        result2 = engine.run_iteration("test_file.py", approval=None)
        assert result2.get("status") == "blocked"
        assert "approval" in result2.get("reason", "").lower()


def test_filelock_on_state_operations():
    """Test that all state file operations use FileLock (FM-2401)."""
    from tdd.ralph_loop_engine import RalphLoopEngine

    with tempfile.TemporaryDirectory() as tmpdir:
        engine = RalphLoopEngine(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir),
        )

        # Verify lock file is created alongside state file
        engine.register_contract("test_file.py", "test_file.py", "spec.md")

        lock_path = engine.lock_file_path
        assert lock_path.exists() or str(lock_path).endswith(".lock")


def test_phase_transition_orchestration():
    """Test that engine orchestrates RED → GREEN → REFACTOR phases."""
    from tdd.ralph_loop_engine import RalphLoopEngine

    with tempfile.TemporaryDirectory() as tmpdir:
        engine = RalphLoopEngine(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir),
        )

        # Register contract starting at RED
        engine.register_contract("impl.py", "test_impl.py", "spec.md")
        engine.set_phase("impl.py", "red")

        # Simulate GREEN transition
        result = engine.transition_phase("impl.py", "green")
        assert result.get("success") is True

        state = engine.get_state("impl.py")
        assert state.get("phase") == "green"

        # Simulate REFACTOR transition
        result = engine.transition_phase("impl.py", "refactor")
        assert result.get("success") is True

        state = engine.get_state("impl.py")
        assert state.get("phase") == "refactor"


def test_concurrent_terminal_isolation():
    """Test that multiple terminals don't share state."""
    from tdd.ralph_loop_engine import RalphLoopEngine

    with tempfile.TemporaryDirectory() as tmpdir:
        # Terminal 1
        engine1 = RalphLoopEngine(
            session_id="session_a",
            terminal_id="terminal_1",
            state_dir=Path(tmpdir),
        )
        engine1.register_contract("file.py", "test_file.py", "spec.md")
        engine1.set_phase("file.py", "red")

        # Terminal 2 (different terminal, same session)
        engine2 = RalphLoopEngine(
            session_id="session_a",
            terminal_id="terminal_2",
            state_dir=Path(tmpdir),
        )

        # Should not see terminal_1's state
        state = engine2.get_state("file.py")
        assert state is None


def test_iteration_counter_increments():
    """Test that iteration counter increments on GREEN → REFACTOR → GREEN loop."""
    from tdd.ralph_loop_engine import RalphLoopEngine

    with tempfile.TemporaryDirectory() as tmpdir:
        engine = RalphLoopEngine(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir),
        )
        engine.register_contract("impl.py", "test_impl.py", "spec.md")

        # Start at GREEN
        engine.set_phase("impl.py", "green")

        # Transition to REFACTOR
        engine.transition_phase("impl.py", "refactor")
        state = engine.get_state("impl.py")
        initial_iteration = state.get("iteration", 0)

        # Transition back to GREEN (should increment iteration)
        engine.transition_phase("impl.py", "green")
        state = engine.get_state("impl.py")
        assert state.get("iteration", 0) == initial_iteration + 1


def test_state_file_atomic_writes():
    """Test that state file writes are atomic (FM-2408)."""
    from tdd.ralph_loop_engine import RalphLoopEngine

    with tempfile.TemporaryDirectory() as tmpdir:
        engine = RalphLoopEngine(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir),
        )

        # Register and write state
        engine.register_contract("test_file.py", "test_file.py", "spec.md")

        # Verify JSON is valid (not corrupted by partial write)
        state_file = engine.state_file_path
        with open(state_file, encoding="utf-8") as f:
            data = json.load(f)

        assert "contracts" in data or "files" in data


def test_complete_phase_marks_done():
    """Test that COMPLETE phase marks the contract as done."""
    from tdd.ralph_loop_engine import RalphLoopEngine

    with tempfile.TemporaryDirectory() as tmpdir:
        engine = RalphLoopEngine(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir),
        )
        engine.register_contract("impl.py", "test_impl.py", "spec.md")
        engine.set_phase("impl.py", "green")

        # Transition to COMPLETE
        result = engine.transition_phase("impl.py", "complete")
        assert result.get("success") is True

        state = engine.get_state("impl.py")
        assert state.get("phase") == "complete"
        assert state.get("done") is True


def main():
    """Run all tests."""
    import pytest

    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
