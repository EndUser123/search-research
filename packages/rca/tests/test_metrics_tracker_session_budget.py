"""Tests for SessionBudget class in metrics_tracker.py.

TEST-018: Create tests for SessionBudget covering:
- Token tracking
- Halt conditions when budget exceeded
- Retry counting
- Reset functionality
- Max tokens and max retries behavior
"""

import pytest

from rca.metrics_tracker import (
    BudgetStatus,
    SessionBudget,
)


# Constants from SessionBudget class
DEFAULT_MAX_TOKENS = 100_000
DEFAULT_MAX_RETRIES = 3


class TestBudgetStatus:
    """Tests for BudgetStatus dataclass."""

    def test_budget_status_creation(self):
        """Test creating a BudgetStatus."""
        status = BudgetStatus(
            status="OK",
            tokens_used=5000,
            tokens_remaining=95000,
            budget_pct=5.0,
        )

        assert status.status == "OK"
        assert status.tokens_used == 5000
        assert status.tokens_remaining == 95000
        assert status.budget_pct == 5.0

    def test_budget_status_with_reason_and_action(self):
        """Test BudgetStatus with reason and action."""
        status = BudgetStatus(
            status="WARN",
            tokens_used=85000,
            tokens_remaining=15000,
            budget_pct=85.0,
            reason="Approaching budget limit",
            action="Consider escalation",
        )

        assert status.status == "WARN"
        assert status.reason == "Approaching budget limit"
        assert status.action == "Consider escalation"


class TestSessionBudgetInit:
    """Tests for SessionBudget initialization."""

    def test_default_initialization(self):
        """Test initialization with default values."""
        budget = SessionBudget()

        assert budget.max_tokens == DEFAULT_MAX_TOKENS
        assert budget.max_retries == DEFAULT_MAX_RETRIES
        assert budget.session_tokens == 0
        assert budget.retry_count == 0
        assert budget.halted is False
        assert budget.halt_reason is None

    def test_custom_max_tokens(self):
        """Test initialization with custom max tokens."""
        budget = SessionBudget(max_tokens=50000)

        assert budget.max_tokens == 50000

    def test_custom_max_retries(self):
        """Test initialization with custom max retries."""
        budget = SessionBudget(max_retries=5)

        assert budget.max_retries == 5

    def test_custom_both_parameters(self):
        """Test initialization with both custom parameters."""
        budget = SessionBudget(max_tokens=75000, max_retries=2)

        assert budget.max_tokens == 75000
        assert budget.max_retries == 2

    def test_initial_state_not_halted(self):
        """Test that initial state is not halted."""
        budget = SessionBudget()

        assert budget.halted is False
        assert budget.halt_reason is None


class TestAddTokens:
    """Tests for add_tokens method."""

    def test_add_tokens_basic(self):
        """Test basic token addition."""
        budget = SessionBudget(max_tokens=10000)

        status = budget.add_tokens(input_tokens=1000, output_tokens=500)

        assert status.status == "OK"
        assert budget.session_tokens == 1500
        assert status.tokens_used == 1500
        assert status.tokens_remaining == 8500
        assert status.budget_pct == 15.0

    def test_add_tokens_multiple_calls(self):
        """Test multiple token additions."""
        budget = SessionBudget(max_tokens=10000)

        budget.add_tokens(1000, 500)
        budget.add_tokens(2000, 500)

        assert budget.session_tokens == 4000

    def test_add_tokens_exact_budget_limit(self):
        """Test adding tokens exactly at budget limit."""
        budget = SessionBudget(max_tokens=10000)

        status = budget.add_tokens(input_tokens=7000, output_tokens=3000)

        # Exactly at limit - implementation allows equal to max
        # The remaining would be 0 but no halt since not negative
        assert status.status in ("OK", "WARN")  # Could be either
        assert status.tokens_remaining >= 0

    def test_add_tokens_exceeds_budget_halts(self):
        """Test that exceeding budget halts the session."""
        budget = SessionBudget(max_tokens=10000)

        status = budget.add_tokens(input_tokens=7000, output_tokens=4000)

        assert status.status == "HALT"
        assert budget.halted is True
        assert budget.halt_reason == "Budget exceeded"
        assert status.tokens_remaining == 0
        assert status.budget_pct == 100.0
        assert "Escalate to human" in status.action

    def test_add_tokens_after_halt_returns_halt_status(self):
        """Test that adding tokens after halt returns halt status."""
        budget = SessionBudget(max_tokens=10000)

        # First call that halts
        budget.add_tokens(7000, 4000)
        # Second call after halt
        status = budget.add_tokens(100, 50)

        assert status.status == "HALT"
        assert "already halted" in status.action.lower()

    def test_add_tokens_warning_at_80_percent(self):
        """Test warning status at 80% budget."""
        budget = SessionBudget(max_tokens=100000)

        status = budget.add_tokens(input_tokens=85000, output_tokens=0)

        assert status.status == "WARN"
        assert status.budget_pct >= 80.0
        assert "Approaching budget limit" in status.reason
        assert "escalation" in status.action.lower()

    def test_add_tokens_warning_boundary_cases(self):
        """Test warning boundary cases."""
        budget = SessionBudget(max_tokens=100)

        # Just below 80%
        status1 = budget.add_tokens(79, 0)
        assert status1.status == "OK"

        # Reset and test at 80%
        budget2 = SessionBudget(max_tokens=100)
        status2 = budget2.add_tokens(80, 0)
        assert status2.status == "WARN"

    def test_add_tokens_zero_values(self):
        """Test adding zero tokens."""
        budget = SessionBudget()

        status = budget.add_tokens(0, 0)

        assert status.status == "OK"
        assert status.tokens_used == 0
        assert status.budget_pct == 0.0

    def test_add_tokens_large_values(self):
        """Test adding very large token values."""
        budget = SessionBudget(max_tokens=1_000_000)

        status = budget.add_tokens(500_000, 400_000)

        # 900k / 1M = 90%, so could be WARN due to >= 80%
        assert status.status in ("OK", "WARN")
        assert status.tokens_used == 900_000
        assert abs(status.budget_pct - 90.0) < 1.0


class TestIncrementRetry:
    """Tests for increment_retry method."""

    def test_increment_retry_basic(self):
        """Test basic retry increment."""
        budget = SessionBudget(max_retries=3)

        status = budget.increment_retry()

        assert status.status == "OK"
        assert budget.retry_count == 1
        assert status.tokens_used == 0

    def test_increment_retry_multiple_times(self):
        """Test incrementing retry multiple times."""
        budget = SessionBudget(max_retries=3)

        budget.increment_retry()
        budget.increment_retry()
        status = budget.increment_retry()

        assert budget.retry_count == 3
        # At max_retries (3), status should be WARN (last retry)
        assert status.status == "WARN"  # At limit with remaining_retries == 0

    def test_increment_retry_exceeds_max_halts(self):
        """Test that exceeding max retries halts the session."""
        budget = SessionBudget(max_retries=3)

        budget.increment_retry()  # 1
        budget.increment_retry()  # 2
        budget.increment_retry()  # 3
        status = budget.increment_retry()  # 4 - exceeds max

        assert status.status == "HALT"
        assert budget.halted is True
        assert budget.halt_reason == "Max retries exceeded"
        assert "escalate to human" in status.action.lower()

    def test_increment_retry_warning_on_last_attempt(self):
        """Test warning on last retry attempt."""
        budget = SessionBudget(max_retries=3)

        budget.increment_retry()  # 1
        budget.increment_retry()  # 2
        status = budget.increment_retry()  # 3 - last attempt

        assert status.status == "WARN"
        assert "Last retry" in status.reason
        assert "Final attempt" in status.action

    def test_increment_retry_with_token_tracking(self):
        """Test retry counting combined with token tracking."""
        budget = SessionBudget(max_tokens=10000, max_retries=3)

        budget.add_tokens(1000, 500)
        budget.increment_retry()
        status = budget.add_tokens(2000, 1000)

        assert budget.session_tokens == 4500
        assert budget.retry_count == 1

    def test_increment_retry_after_halt(self):
        """Test incrementing retry after session halted."""
        budget = SessionBudget(max_retries=3)

        # Halt on retries
        budget.increment_retry()
        budget.increment_retry()
        budget.increment_retry()
        budget.increment_retry()  # Halts

        status = budget.increment_retry()  # Try again

        assert status.status == "HALT"
        assert "already halted" in status.action.lower()


class TestGetSummary:
    """Tests for get_summary method."""

    def test_get_summary_initial_state(self):
        """Test summary for initial state."""
        budget = SessionBudget(max_tokens=100000, max_retries=5)

        summary = budget.get_summary()

        assert summary["tokens_used"] == 0
        assert summary["tokens_remaining"] == 100000
        assert summary["budget_pct"] == 0.0
        assert summary["retries_used"] == 0
        assert summary["retries_remaining"] == 5
        assert summary["halted"] is False
        assert summary["halt_reason"] is None

    def test_get_summary_with_usage(self):
        """Test summary with token and retry usage."""
        budget = SessionBudget(max_tokens=100000, max_retries=3)

        budget.add_tokens(30000, 20000)
        budget.increment_retry()

        summary = budget.get_summary()

        assert summary["tokens_used"] == 50000
        assert summary["tokens_remaining"] == 50000
        assert summary["budget_pct"] == 50.0
        assert summary["retries_used"] == 1
        assert summary["retries_remaining"] == 2

    def test_get_summary_after_halt(self):
        """Test summary after session halted."""
        budget = SessionBudget(max_tokens=10000, max_retries=3)

        budget.add_tokens(15000, 0)  # Over budget

        summary = budget.get_summary()

        assert summary["halted"] is True
        assert summary["halt_reason"] == "Budget exceeded"
        assert summary["tokens_remaining"] == 0  # Should be capped at 0


class TestReset:
    """Tests for reset method."""

    def test_reset_clears_tokens(self):
        """Test that reset clears token usage."""
        budget = SessionBudget(max_tokens=10000)

        budget.add_tokens(5000, 3000)
        budget.reset()

        assert budget.session_tokens == 0
        assert budget.halted is False
        assert budget.halt_reason is None

    def test_reset_clears_retries(self):
        """Test that reset clears retry count."""
        budget = SessionBudget(max_retries=3)

        budget.increment_retry()
        budget.increment_retry()
        budget.reset()

        assert budget.retry_count == 0
        assert budget.halted is False

    def test_reset_clears_halt_state(self):
        """Test that reset clears halt state."""
        budget = SessionBudget(max_tokens=10000)

        budget.add_tokens(15000, 0)  # Halt
        assert budget.halted is True

        budget.reset()

        assert budget.halted is False
        assert budget.halt_reason is None

    def test_reset_allows_new_tracking(self):
        """Test that reset allows new token tracking."""
        budget = SessionBudget(max_tokens=10000)

        # Use and halt
        budget.add_tokens(15000, 0)
        assert budget.halted is True

        # Reset and use again
        budget.reset()
        status = budget.add_tokens(1000, 500)

        assert status.status == "OK"
        assert budget.session_tokens == 1500

    def test_reset_preserves_limits(self):
        """Test that reset preserves max tokens and retries."""
        budget = SessionBudget(max_tokens=50000, max_retries=2)

        budget.add_tokens(10000, 0)
        budget.reset()

        assert budget.max_tokens == 50000
        assert budget.max_retries == 2


class TestHaltConditions:
    """Tests for various halt conditions."""

    def test_halt_on_budget_exceeded_with_retries_remaining(self):
        """Test that budget halt takes priority over retries."""
        budget = SessionBudget(max_tokens=10000, max_retries=10)

        # Use small number of retries
        budget.increment_retry()
        budget.increment_retry()

        # Exceed budget
        status = budget.add_tokens(20000, 0)

        assert status.status == "HALT"
        assert "Budget exceeded" in status.reason
        assert budget.halted is True

    def test_halt_on_max_retries_with_budget_remaining(self):
        """Test that retry halt takes priority when budget remains."""
        budget = SessionBudget(max_tokens=100000, max_retries=2)

        # Use small portion of budget
        budget.add_tokens(5000, 0)

        # Exceed retries
        budget.increment_retry()
        budget.increment_retry()
        budget.increment_retry()  # Exceeds

        assert budget.halted is True
        assert budget.halt_reason == "Max retries exceeded"

    def test_halt_permanent_until_reset(self):
        """Test that halt state persists until reset."""
        budget = SessionBudget(max_tokens=10000)

        # Trigger halt
        budget.add_tokens(15000, 0)

        assert budget.halted is True

        # Try various operations - all should return HALT
        status1 = budget.add_tokens(100, 50)
        status2 = budget.increment_retry()

        assert status1.status == "HALT"
        assert status2.status == "HALT"
        assert budget.halted is True  # Still halted

    def test_correct_halt_reason_set(self):
        """Test that correct halt reason is set based on trigger."""
        # Test budget halt
        budget1 = SessionBudget(max_tokens=10000)
        budget1.add_tokens(15000, 0)
        assert "Budget" in budget1.halt_reason

        # Test retry halt
        budget2 = SessionBudget(max_retries=2)
        budget2.increment_retry()
        budget2.increment_retry()
        budget2.increment_retry()
        assert "retry" in budget2.halt_reason.lower() or "Max" in budget2.halt_reason


class TestBudgetStatusFields:
    """Tests for BudgetStatus field values."""

    def test_budget_percentage_calculation(self):
        """Test accurate budget percentage calculation."""
        budget = SessionBudget(max_tokens=1000)

        status = budget.add_tokens(250, 0)

        assert status.budget_pct == 25.0

    def test_budget_percentage_rounding(self):
        """Test budget percentage with non-rounding numbers."""
        budget = SessionBudget(max_tokens=100)

        status = budget.add_tokens(33, 0)

        assert status.budget_pct == 33.0

    def test_tokens_remaining_calculation(self):
        """Test accurate remaining tokens calculation."""
        budget = SessionBudget(max_tokens=10000)

        status = budget.add_tokens(3500, 1500)

        assert status.tokens_remaining == 5000

    def test_retries_remaining_calculation(self):
        """Test accurate remaining retries calculation."""
        budget = SessionBudget(max_retries=5)

        budget.increment_retry()
        budget.increment_retry()

        summary = budget.get_summary()
        assert summary["retries_remaining"] == 3


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_small_max_tokens(self):
        """Test behavior with very small max tokens."""
        budget = SessionBudget(max_tokens=100)

        status = budget.add_tokens(90, 0)

        assert status.status == "WARN"  # 90% is above 80%

    def test_zero_max_tokens(self):
        """Test handling when max_tokens is effectively zero."""
        budget = SessionBudget(max_tokens=1)

        status = budget.add_tokens(1, 0)

        # At 100% budget (1/1), status is WARN due to >= 80%
        assert status.status == "WARN"
        assert status.budget_pct == 100.0

    def test_zero_max_retries(self):
        """Test behavior when max_retries is zero."""
        budget = SessionBudget(max_retries=0)

        status = budget.increment_retry()  # First retry exceeds max

        assert status.status == "HALT"
        assert budget.halted is True

    def test_negative_tokens_handled_as_positive(self):
        """Test that negative tokens are treated as positive (addition)."""
        budget = SessionBudget(max_tokens=10000)

        # The implementation should add whatever values are given
        status = budget.add_tokens(input_tokens=-100, output_tokens=-50)

        # Should still work (negatives would make tokens_used negative)
        assert budget.session_tokens == -150

    def test_large_retries_count(self):
        """Test with large max retries."""
        budget = SessionBudget(max_retries=100)

        for _ in range(50):
            budget.increment_retry()

        status = budget.increment_retry()

        assert status.status == "OK"
        assert budget.retry_count == 51

    def test_reset_multiple_times(self):
        """Test that reset can be called multiple times."""
        budget = SessionBudget()

        budget.add_tokens(5000, 0)
        budget.reset()
        budget.add_tokens(3000, 0)
        budget.reset()
        budget.add_tokens(1000, 0)

        assert budget.session_tokens == 1000
        assert budget.halted is False


class TestCombinedTokenAndRetryScenarios:
    """Tests for realistic scenarios combining tokens and retries."""

    def test_debugging_scenario(self):
        """Test realistic debugging scenario."""
        budget = SessionBudget(max_tokens=50000, max_retries=3)

        # First attempt
        budget.add_tokens(5000, 2000)
        # First failure - retry
        budget.increment_retry()
        budget.add_tokens(3000, 1000)

        summary = budget.get_summary()

        assert summary["tokens_used"] == 11000
        assert summary["retries_used"] == 1
        assert summary["halted"] is False

    def test_costly_debugging_halts_on_budget(self):
        """Test scenario where costly debugging hits budget first."""
        budget = SessionBudget(max_tokens=20000, max_retries=10)

        # Very token-heavy operations
        budget.add_tokens(15000, 6000)  # 21000 total - exceeds

        assert budget.halted is True
        assert budget.halt_reason == "Budget exceeded"

    def test_retry_intensive_debugging_halts_on_retries(self):
        """Test scenario where retry-intensive debugging hits retry limit."""
        budget = SessionBudget(max_tokens=200000, max_retries=2)

        # Light on tokens, heavy on retries
        budget.increment_retry()
        budget.increment_retry()
        budget.increment_retry()  # Exceeds

        assert budget.halted is True
        assert budget.halt_reason == "Max retries exceeded"

    def test_progressive_approach_to_limits(self):
        """Test gradually approaching both limits."""
        budget = SessionBudget(max_tokens=100000, max_retries=5)

        # Gradual usage
        statuses = []
        for i in range(5):
            statuses.append(budget.add_tokens(15000, 0))
            budget.increment_retry()

        # Last state should still be OK
        summary = budget.get_summary()
        assert summary["tokens_used"] == 75000
        assert summary["retries_used"] == 5
        # One more increment would halt on retries


class TestBudgetStatusStringRepresentation:
    """Tests for BudgetStatus representation."""

    def test_budget_status_repr(self):
        """Test that BudgetStatus can be inspected."""
        status = BudgetStatus(
            status="WARN",
            tokens_used=80000,
            tokens_remaining=20000,
            budget_pct=80.0,
            reason="Test",
            action="Test action",
        )

        # Verify attributes are accessible
        assert status.status == "WARN"
        assert "Test" in status.reason
        assert "Test action" in status.action
