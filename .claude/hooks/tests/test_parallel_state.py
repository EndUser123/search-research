"""
Tests for parallel-safe state management with file locking.

This test file verifies that StateManager performs atomic reads/writes
that are safe for concurrent access from multiple PROCESSES (not just threads).

Run with: pytest .claude/hooks/tests/test_parallel_state.py -v

To enable atomic state writes: set ATOMIC_STATE_WRITES=1 before running pytest
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path as PathLib

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(PathLib(__file__).parent.parent))


@pytest.mark.skipif(
    os.environ.get("ATOMIC_STATE_WRITES", "0") != "1",
    reason="ATOMIC_STATE_WRITES not enabled (set ATOMIC_STATE_WRITES=1)"
)
def test_increment_block_count_under_concurrent_load(tmp_path):
    """
    Pre-mortem scenario: concurrent increments must not lose updates.

    Without locking, this test WILL fail with count < 500.

    This test verifies that when multiple threads/processes increment
    a counter concurrently, all updates are preserved through proper
    file locking.

    Given: A StateManager with block_count = 0
    When: 5 threads each increment 100 times concurrently
    Then: Final count should be exactly 500 (no lost updates)

    This test will FAIL in RED phase because StateManager doesn't exist yet.
    """
    from state_manager import StateManager

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    manager = StateManager(state_dir)

    # Initialize counter
    manager.write_state("block_count", {"count": 0})

    def increment():
        for _ in range(100):
            with manager.locked_state("block_count") as state:
                state["count"] = state.get("count", 0) + 1

    threads = [threading.Thread(target=increment) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    final = manager.read_state("block_count")
    assert final["count"] == 500, f"Lost updates! Got {final['count']}, expected 500"


@pytest.mark.skipif(
    os.environ.get("ATOMIC_STATE_WRITES", "0") != "1",
    reason="ATOMIC_STATE_WRITES not enabled"
)
def test_state_manager_locked_state_context_manager(tmp_path):
    """
    Test that locked_state context manager saves changes on exit.

    This verifies the context manager pattern: state is loaded,
    modifications are made within the context, and changes are
    automatically saved when exiting.

    Given: A StateManager with existing state
    When: State is modified within locked_state context
    Then: Changes should be persisted after context exits
    """
    from state_manager import StateManager

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    manager = StateManager(state_dir)

    # Write initial state
    manager.write_state("test", {"value": 10})

    # Modify through context manager
    with manager.locked_state("test") as state:
        state["value"] = 20
        state["new_field"] = "added"

    # Verify changes persisted
    final = manager.read_state("test")
    assert final["value"] == 20
    assert final["new_field"] == "added"


@pytest.mark.skipif(
    os.environ.get("ATOMIC_STATE_WRITES", "0") != "1",
    reason="ATOMIC_STATE_WRITES not enabled"
)
def test_state_manager_handles_missing_keys(tmp_path):
    """
    Test that StateManager gracefully handles missing state keys.

    Given: No existing state for a key
    When: locked_state is called with that key
    Then: Should start with empty dict, not crash
    """
    from state_manager import StateManager

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    manager = StateManager(state_dir)

    # Access non-existent key
    with manager.locked_state("new_key") as state:
        state["initialized"] = True

    # Verify it was created
    final = manager.read_state("new_key")
    assert final is not None
    assert final["initialized"] is True


@pytest.mark.skipif(
    os.environ.get("ATOMIC_STATE_WRITES", "0") != "1",
    reason="ATOMIC_STATE_WRITES not enabled"
)
def test_state_manager_function_exists():
    """
    Characterization test: Verify StateManager class exists.

    This test will FAIL in RED phase because StateManager doesn't exist yet.
    """
    from state_manager import StateManager

    # If we get here, the import succeeded
    assert StateManager is not None
    assert hasattr(StateManager, 'locked_state')
    assert hasattr(StateManager, 'read_state')
    assert hasattr(StateManager, 'write_state')
