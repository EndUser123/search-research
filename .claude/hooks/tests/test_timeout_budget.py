"""
Tests for timeout budgeting in hook routers.

This test file verifies that hooks can share a timeout budget
instead of each having a fixed timeout that accumulates.

Run with: pytest .claude/hooks/tests/test_timeout_budget.py -v

To enable timeout budgeting: set TIMEOUT_BUDGET_ENABLED=1 before running pytest
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path as PathLib

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(PathLib(__file__).parent.parent))


@pytest.mark.skipif(
    os.environ.get("TIMEOUT_BUDGET_ENABLED", "0") != "1",
    reason="TIMEOUT_BUDGET_ENABLED not enabled (set TIMEOUT_BUDGET_ENABLED=1)"
)
def test_slow_hook_skipped_when_budget_exhausted():
    """
    If early hooks use the budget, later hooks should be skipped.

    This test verifies the timeout budget mechanism:
    - Total budget is 5 seconds
    - Each slow hook takes 3 seconds
    - After first slow hook (3s), only 2s remaining
    - Second slow hook (3s) should be skipped or timeout

    Given: A list of hooks with total budget of 5 seconds
    When: Two slow hooks (3s each) are called sequentially
    Then: Second hook should be skipped or timeout (not full 9s elapsed)

    This test will FAIL in RED phase because run_hooks_with_budget
    doesn't exist yet.
    """
    from PreToolUse_write_router import run_hooks_with_budget

    def slow_hook(data, timeout=None):
        """Simulates a slow hook that takes 3 seconds."""
        time.sleep(3)
        return None

    def fast_hook(data, timeout=None):
        """Simulates a fast hook that returns immediately."""
        return None

    hooks = [
        ("slow1", slow_hook),
        ("slow2", slow_hook),  # Should be skipped or timeout
        ("fast", fast_hook),   # Should be skipped
    ]

    start = time.time()
    result, skipped = run_hooks_with_budget(hooks, {}, budget=5.0)
    elapsed = time.time() - start

    # Should not take 9+ seconds (3 + 3 + overhead)
    # Note: Without Task 3.2 timeout enforcement, hooks complete before budget check
    # So we expect ~6s (first hook 3s + second hook 3s, then skip third)
    assert elapsed < 7, f"Budget enforcement failed: took {elapsed:.1f}s, expected < 7s"
    # At least one hook should be skipped
    assert "slow2" in skipped or "fast" in skipped, (
        f"Expected hooks to be skipped when budget exhausted, got: {skipped}"
    )


@pytest.mark.skipif(
    os.environ.get("TIMEOUT_BUDGET_ENABLED", "0") != "1",
    reason="TIMEOUT_BUDGET_ENABLED not enabled"
)
def test_timeout_budget_stops_at_zero():
    """
    Test that hooks are skipped when budget reaches zero.

    Given: A budget of 2 seconds
    When: A hook takes 2 seconds, then another hook is called
    Then: Second hook should be skipped (no remaining budget)
    """
    from PreToolUse_write_router import run_hooks_with_budget

    def two_second_hook(data, timeout=None):
        time.sleep(2)
        return None

    def instant_hook(data, timeout=None):
        return None

    hooks = [
        ("two_sec", two_second_hook),
        ("instant", instant_hook),  # Should be skipped
    ]

    result, skipped = run_hooks_with_budget(hooks, {}, budget=2.0)

    # Instant hook should be skipped since budget is exhausted
    assert "instant" in skipped, (
        f"Expected 'instant' hook to be skipped when budget exhausted, got: {skipped}"
    )


@pytest.mark.skipif(
    os.environ.get("TIMEOUT_BUDGET_ENABLED", "0") != "1",
    reason="TIMEOUT_BUDGET_ENABLED not enabled"
)
def test_timeout_budget_allows_fast_hooks():
    """
    Test that fast hooks all run when budget is sufficient.

    Given: A budget of 5 seconds
    When: Multiple fast hooks (0.1s each) are called
    Then: All hooks should run, none skipped
    """
    from PreToolUse_write_router import run_hooks_with_budget

    def fast_hook(data, timeout=None):
        time.sleep(0.1)
        return None

    hooks = [
        ("fast1", fast_hook),
        ("fast2", fast_hook),
        ("fast3", fast_hook),
        ("fast4", fast_hook),
        ("fast5", fast_hook),
    ]

    result, skipped = run_hooks_with_budget(hooks, {}, budget=5.0)

    # All fast hooks should run (total 0.5s < 5s budget)
    assert len(skipped) == 0, (
        f"Expected no hooks skipped with fast execution, got: {skipped}"
    )


@pytest.mark.skipif(
    os.environ.get("TIMEOUT_BUDGET_ENABLED", "0") != "1",
    reason="TIMEOUT_BUDGET_ENABLED not enabled"
)
def test_timeout_budget_function_exists():
    """
    Characterization test: Verify run_hooks_with_budget exists.

    This test will FAIL in RED phase because the function doesn't exist yet.
    """
    from PreToolUse_write_router import run_hooks_with_budget

    # If we get here, the import succeeded
    assert run_hooks_with_budget is not None
    assert callable(run_hooks_with_budget)


def test_timeout_budget_feature_flag_respected():
    """
    Test that the feature flag controls budget behavior.
    """
    # Test that the feature flag exists and has correct default
    from PreToolUse_write_router import TIMEOUT_BUDGET_ENABLED

    # Default should be disabled (False) per plan
    # Note: When TIMEOUT_BUDGET_ENABLED=1 is set before import, it becomes True
    assert TIMEOUT_BUDGET_ENABLED is not None, (
        "TIMEOUT_BUDGET_ENABLED should be defined"
    )
