"""
Tests for NBM-3: Circuit Breaker to Prevent Infinite Repair Turn Loops.

These tests validate that the circuit breaker pattern prevents gates from
trapping the agent in infinite loops when stop_hook_active=true.

Run with: pytest .claude/hooks/tests/test_circuit_breaker.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# The circuit breaker logic doesn't exist yet - use skipif pattern
try:
    from __lib.circuit_breaker import (
        CircuitBreaker,
        get_iteration_count,
        increment_iteration,
        reset_iteration,
        should_allow_continue,
    )
except (ImportError, ModuleNotFoundError):
    CircuitBreaker = None
    get_iteration_count = None
    increment_iteration = None
    reset_iteration = None
    should_allow_continue = None


# -------------------------------------------------------------------
# Test: NBM3-001 — Circuit breaker exits 0 after threshold
# -------------------------------------------------------------------
@pytest.mark.skipif(
    CircuitBreaker is None,
    reason="circuit_breaker not implemented yet",
)
def test_circuit_breaker_exits_0_after_threshold(tmp_path, monkeypatch):
    """
    When stop_hook_active=true and iteration count exceeds threshold,
    the gate must exit with code 0 (allow) instead of blocking.

    This prevents the infinite repair turn loop described in NBM-3.
    """
    # Set up temp file for iteration tracking
    iteration_file = tmp_path / "iteration_count_test.tmp"
    monkeypatch.setenv("CIRCUIT_BREAKER_ITERATION_FILE", str(iteration_file))

    session_id = "test_session_123"
    threshold = 3

    # Simulate iterations at threshold
    for _ in range(threshold):
        increment_iteration(session_id)

    # Check that we should allow continuation
    result = should_allow_continue(session_id, stop_hook_active=True, threshold=threshold)
    assert result is True, "Should allow continuation after threshold exceeded"


# -------------------------------------------------------------------
# Test: NBM3-002 — Circuit breaker increments atomically
# -------------------------------------------------------------------
@pytest.mark.skipif(
    increment_iteration is None,
    reason="circuit_breaker not implemented yet",
)
def test_atomic_increment(tmp_path, monkeypatch):
    """
    Iteration count must be incremented atomically to prevent race conditions.

    Multiple concurrent increments must all be accounted for.
    """
    import threading

    iteration_file = tmp_path / "iteration_count_test.tmp"
    monkeypatch.setenv("CIRCUIT_BREAKER_ITERATION_FILE", str(iteration_file))

    session_id = "test_session_456"
    iterations_per_thread = 10
    num_threads = 5

    def do_increments():
        for _ in range(iterations_per_thread):
            increment_iteration(session_id)

    threads = [threading.Thread(target=do_increments) for _ in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Final count must be exactly num_threads * iterations_per_thread
    count = get_iteration_count(session_id)
    expected = num_threads * iterations_per_thread
    assert count == expected, f"Expected {expected} increments, got {count}"


# -------------------------------------------------------------------
# Test: NBM3-003 — Counter resets on new session
# -------------------------------------------------------------------
@pytest.mark.skipif(
    reset_iteration is None,
    reason="circuit_breaker not implemented yet",
)
def test_resets_on_new_session(tmp_path, monkeypatch):
    """
    Iteration count must be reset when a new session starts.

    The counter is session-scoped to prevent cross-session contamination.
    """
    iteration_file = tmp_path / "iteration_count_test.tmp"
    monkeypatch.setenv("CIRCUIT_BREAKER_ITERATION_FILE", str(iteration_file))

    session1 = "session_aaa"
    session2 = "session_bbb"

    # Increment for session 1
    increment_iteration(session1)
    increment_iteration(session1)
    count1 = get_iteration_count(session1)
    assert count1 == 2, "Session 1 should have count of 2"

    # Reset session 1
    reset_iteration(session1)

    # Session 1 should be 0
    count1_after = get_iteration_count(session1)
    assert count1_after == 0, "Session 1 should be reset to 0"

    # Session 2 should be independent
    count2 = get_iteration_count(session2)
    assert count2 == 0, "Session 2 should have count of 0 (new session)"


# -------------------------------------------------------------------
# Test: NBM3-004 — Below threshold still blocks
# -------------------------------------------------------------------
@pytest.mark.skipif(
    should_allow_continue is None,
    reason="circuit_breaker not implemented yet",
)
def test_below_threshold_still_blocks(tmp_path, monkeypatch):
    """
    When stop_hook_active=true but iteration count is BELOW threshold,
    the gate should still block (return False).

    The circuit breaker only kicks in after threshold is exceeded.
    """
    iteration_file = tmp_path / "iteration_count_test.tmp"
    monkeypatch.setenv("CIRCUIT_BREAKER_ITERATION_FILE", str(iteration_file))

    session_id = "test_session_789"
    threshold = 3

    # Only 2 iterations (below threshold of 3)
    increment_iteration(session_id)
    increment_iteration(session_id)

    result = should_allow_continue(session_id, stop_hook_active=True, threshold=threshold)
    assert result is False, "Should still block when below threshold"


# -------------------------------------------------------------------
# Test: NBM3-005 — stop_hook_active=false bypasses circuit breaker
# -------------------------------------------------------------------
@pytest.mark.skipif(
    should_allow_continue is None,
    reason="circuit_breaker not implemented yet",
)
def test_stop_hook_active_false_bypasses(tmp_path, monkeypatch):
    """
    When stop_hook_active=false, the circuit breaker is bypassed.

    The iteration count is still tracked but doesn't affect the decision.
    """
    iteration_file = tmp_path / "iteration_count_test.tmp"
    monkeypatch.setenv("CIRCUIT_BREAKER_ITERATION_FILE", str(iteration_file))

    session_id = "test_session_abc"
    threshold = 3

    # Exceed threshold
    for _ in range(threshold + 1):
        increment_iteration(session_id)

    # But stop_hook_active is False - should NOT allow
    result = should_allow_continue(session_id, stop_hook_active=False, threshold=threshold)
    assert result is False, "Should not bypass when stop_hook_active=False"


# -------------------------------------------------------------------
# Test: NBM3-006 — CircuitBreaker class integration
# -------------------------------------------------------------------
@pytest.mark.skipif(
    CircuitBreaker is None,
    reason="circuit_breaker not implemented yet",
)
def test_circuit_breaker_class(tmp_path, monkeypatch):
    """
    CircuitBreaker class provides a clean interface for circuit breaking.

    The class should handle file management and provide a simple API.
    """
    iteration_file = tmp_path / "iteration_count_cb.tmp"
    monkeypatch.setenv("CIRCUIT_BREAKER_ITERATION_FILE", str(iteration_file))

    cb = CircuitBreaker(session_id="test_session_class", threshold=3)

    # Initial state
    assert cb.get_count() == 0, "Initial count should be 0"
    assert cb.should_block() is True, "Should block initially"

    # Increment to threshold
    cb.increment()
    cb.increment()
    cb.increment()

    # Now should allow
    assert cb.get_count() == 3, "Count should be 3"
    assert cb.should_block() is False, "Should not block after threshold"


# -------------------------------------------------------------------
# Characterization test: Import module
# -------------------------------------------------------------------
def test_module_import():
    """
    Characterization test: Verify circuit_breaker module can be imported.

    This test will FAIL in the RED phase because the module doesn't exist yet.
    """
    from __lib.circuit_breaker import (
        CircuitBreaker,
        get_iteration_count,
        increment_iteration,
        reset_iteration,
        should_allow_continue,
    )

    assert CircuitBreaker is not None
    assert get_iteration_count is not None
    assert increment_iteration is not None
    assert reset_iteration is not None
    assert should_allow_continue is not None
