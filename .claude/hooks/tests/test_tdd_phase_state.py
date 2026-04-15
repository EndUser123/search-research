#!/usr/bin/env python3
"""
Unit tests for tdd_phase_state.py

Tests:
- TDDPhaseState enum values (extends TDD95State)
- Phase transition validation
- Session-scoped state file paths (FM-2406)
- State file operations with FileLock (FM-2401)
- Crash recovery (TASK-002 integration point)
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


def test_phase_state_enum_values():
    """Test TDDPhaseState enum extends TDD95State with RED/GREEN/REFACTOR."""
    from tdd.tdd_phase_state import TDDPhaseState

    # Inherited from TDD95State
    assert TDDPhaseState.NONE.value == "none"
    assert TDDPhaseState.TEST_EXISTS.value == "test_exists"
    assert TDDPhaseState.FAILING.value == "failing"
    assert TDDPhaseState.PASSING.value == "passing"
    assert TDDPhaseState.COMPLETE.value == "complete"

    # New phase states
    assert TDDPhaseState.RED.value == "red"
    assert TDDPhaseState.GREEN.value == "green"
    assert TDDPhaseState.REFACTOR.value == "refactor"


def test_phase_state_from_string():
    """Test parsing phase state from string."""
    from tdd.tdd_phase_state import TDDPhaseState

    # Existing states
    assert TDDPhaseState.from_string("none") == TDDPhaseState.NONE
    assert TDDPhaseState.from_string("failing") == TDDPhaseState.FAILING

    # New phase states
    assert TDDPhaseState.from_string("red") == TDDPhaseState.RED
    assert TDDPhaseState.from_string("green") == TDDPhaseState.GREEN
    assert TDDPhaseState.from_string("refactor") == TDDPhaseState.REFACTOR

    # Invalid defaults to NONE
    assert TDDPhaseState.from_string("bogus") == TDDPhaseState.NONE


def test_valid_phase_transitions():
    """Test can_transition_to() for valid phase progressions."""
    from tdd.tdd_phase_state import TDDPhaseState

    # NONE → TEST_EXISTS (test file created)
    assert TDDPhaseState.NONE.can_transition_to(TDDPhaseState.TEST_EXISTS)

    # TEST_EXISTS → RED (test executed and fails)
    assert TDDPhaseState.TEST_EXISTS.can_transition_to(TDDPhaseState.RED)

    # RED → GREEN (implementation passes tests)
    assert TDDPhaseState.RED.can_transition_to(TDDPhaseState.GREEN)

    # GREEN → REFACTOR (code cleanup phase)
    assert TDDPhaseState.GREEN.can_transition_to(TDDPhaseState.REFACTOR)

    # REFACTOR → GREEN (tests still pass after refactor)
    assert TDDPhaseState.REFACTOR.can_transition_to(TDDPhaseState.GREEN)

    # REFACTOR → COMPLETE (cycle finished)
    assert TDDPhaseState.REFACTOR.can_transition_to(TDDPhaseState.COMPLETE)

    # GREEN → COMPLETE (skip refactor, cycle finished)
    assert TDDPhaseState.GREEN.can_transition_to(TDDPhaseState.COMPLETE)


def test_invalid_phase_transitions():
    """Test can_transition_to() blocks invalid transitions."""
    from tdd.tdd_phase_state import TDDPhaseState

    # Cannot skip phases
    assert not TDDPhaseState.NONE.can_transition_to(TDDPhaseState.GREEN)
    assert not TDDPhaseState.NONE.can_transition_to(TDDPhaseState.COMPLETE)
    assert not TDDPhaseState.TEST_EXISTS.can_transition_to(TDDPhaseState.GREEN)

    # Cannot go backwards (except REFACTOR → GREEN for iteration)
    assert not TDDPhaseState.GREEN.can_transition_to(TDDPhaseState.RED)
    assert not TDDPhaseState.COMPLETE.can_transition_to(TDDPhaseState.RED)
    assert not TDDPhaseState.COMPLETE.can_transition_to(TDDPhaseState.GREEN)


def test_phase_state_can_edit_impl():
    """Test can_edit_impl() for each phase."""
    from tdd.tdd_phase_state import TDDPhaseState

    # Can edit impl in implementation phases
    assert TDDPhaseState.RED.can_edit_impl() == True
    assert TDDPhaseState.GREEN.can_edit_impl() == True
    assert TDDPhaseState.REFACTOR.can_edit_impl() == True

    # Cannot edit in other phases
    assert TDDPhaseState.NONE.can_edit_impl() == False
    assert TDDPhaseState.TEST_EXISTS.can_edit_impl() == False
    assert TDDPhaseState.COMPLETE.can_edit_impl() == False


def test_phase_state_can_edit_test():
    """Test can_edit_test() for each phase."""
    from tdd.tdd_phase_state import TDDPhaseState

    # Can edit test only in RED phase (write failing tests)
    assert TDDPhaseState.RED.can_edit_test() == True

    # Cannot edit test in GREEN/REFACTOR (Three-File Contract)
    assert TDDPhaseState.GREEN.can_edit_test() == False
    assert TDDPhaseState.REFACTOR.can_edit_test() == False


def test_state_file_path_includes_session_id():
    """Test that state file paths include session_id for multi-terminal isolation (FM-2406)."""
    from tdd.tdd_phase_state import TDDPhaseStateManager

    manager = TDDPhaseStateManager(session_id="test_session_123", terminal_id="terminal_456")

    # State file path should include session_id
    state_path = manager.state_file_path
    assert "test_session_123" in str(state_path), f"session_id not in path: {state_path}"

    # State file path should include terminal_id
    assert "terminal_456" in str(state_path), f"terminal_id not in path: {state_path}"


def test_state_file_operations_with_filelock():
    """Test that state file reads/writes use FileLock context manager (FM-2401)."""
    from tdd.tdd_phase_state import TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = TDDPhaseStateManager(
            session_id="test_session", terminal_id="test_terminal", state_dir=Path(tmpdir)
        )

        # Write state (should acquire lock)
        manager.set_phase("test_file.py", "red")

        # Read state (should acquire lock)
        phase = manager.get_phase("test_file.py")
        assert phase is not None
        assert phase.value == "red"


def test_atomic_write_pattern():
    """Test that JSON state writes use atomic write pattern (FM-2408)."""
    import json

    from tdd.tdd_phase_state import TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = TDDPhaseStateManager(
            session_id="test_session", terminal_id="test_terminal", state_dir=Path(tmpdir)
        )

        # Write state
        manager.set_phase("test_file.py", "red")

        # Verify JSON is valid (not corrupted by partial write)
        state_file = manager.state_file_path
        with open(state_file, encoding="utf-8") as f:
            data = json.load(f)

        assert "files" in data
        assert "test_file.py" in data["files"]


def test_concurrent_access_protection():
    """Test that concurrent state file access is protected by FileLock."""
    import threading

    from tdd.tdd_phase_state import TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = TDDPhaseStateManager(
            session_id="test_session", terminal_id="test_terminal", state_dir=Path(tmpdir)
        )

        results = {"success": 0, "errors": []}

        def write_state(i):
            try:
                manager.set_phase(f"file_{i}.py", "red")
                results["success"] += 1
            except Exception as e:
                results["errors"].append(str(e))

        # Spawn multiple threads writing concurrently
        threads = [threading.Thread(target=write_state, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All writes should succeed without corruption
        assert (
            results["success"] == 10
        ), f"Only {results['success']}/10 succeeded: {results['errors']}"


def test_crash_recovery():
    """Test that manager can recover state after crash (TASK-002 integration)."""
    from tdd.tdd_phase_state import TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create manager and write some state
        manager1 = TDDPhaseStateManager(
            session_id="test_session", terminal_id="test_terminal", state_dir=Path(tmpdir)
        )
        manager1.set_phase("file_a.py", "red")
        manager1.set_phase("file_b.py", "green")

        # Simulate crash by creating new manager (no in-memory state)
        manager2 = TDDPhaseStateManager(
            session_id="test_session", terminal_id="test_terminal", state_dir=Path(tmpdir)
        )

        # Should recover state from disk
        phase_a = manager2.get_phase("file_a.py")
        phase_b = manager2.get_phase("file_b.py")

        assert phase_a is not None and phase_a.value == "red"
        assert phase_b is not None and phase_b.value == "green"


def main():
    """Run all tests."""
    import pytest

    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)


# ---------------------------------------------------------------------------
# extract_test_file_from_command — node ID normalisation (tdd_core)
# ---------------------------------------------------------------------------


class TestExtractTestFileFromCommand:
    """extract_test_file_from_command must strip pytest node ID suffixes.

    Without this fix, a targeted run like:
        pytest tests/test_foo.py::TestClass::test_method
    returns None (the part doesn't end with .py), falls back to
    find_active_tdd_cycle(), and creates a separate state key from the
    full-suite run — so RED demonstrated on a subset never satisfies
    the AWAITING_RED requirement for the full suite.
    """

    def setup_method(self) -> None:
        from tdd_core import extract_test_file_from_command
        self.extract = extract_test_file_from_command

    def test_plain_file_path(self) -> None:
        result = self.extract("python -m pytest tests/test_foo.py -v")
        assert result is not None
        assert result.endswith("test_foo.py")

    def test_node_id_class_and_method(self) -> None:
        """Node ID suffix stripped — same file key as full-suite run."""
        result = self.extract(
            "python -m pytest tests/test_foo.py::TestClass::test_method -v"
        )
        assert result is not None
        assert result.endswith("test_foo.py")
        assert "::" not in result

    def test_node_id_class_only(self) -> None:
        result = self.extract("pytest tests/test_foo.py::TestClass")
        assert result is not None
        assert result.endswith("test_foo.py")
        assert "::" not in result

    def test_node_id_and_plain_give_same_key(self) -> None:
        """Targeted run and full-suite run resolve to the same normalised path."""
        plain = self.extract("pytest tests/test_foo.py")
        node = self.extract("pytest tests/test_foo.py::TestClass::test_bar")
        assert plain is not None
        assert node is not None
        assert plain == node

    def test_non_test_file_ignored(self) -> None:
        result = self.extract("python hook.py --run")
        assert result is None

    def test_no_py_file_returns_none(self) -> None:
        result = self.extract("pytest --collect-only -q")
        assert result is None


if __name__ == "__main__":
    main()
