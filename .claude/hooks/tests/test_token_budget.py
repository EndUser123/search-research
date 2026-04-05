"""
Tests for TokenBudget class.

These tests verify token budget tracking behavior including:
- Budget checking (allow/deny based on thresholds)
- Token usage recording
- Monthly reset behavior
- Status reporting

Run with: pytest P:/.claude/hooks/tests/test_token_budget.py -v
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from __lib.token_budget import BudgetStatus, TokenBudget


class TestTokenBudgetInit:
    """Tests for TokenBudget initialization."""

    @pytest.fixture
    def temp_project_root(self):
        """Create temporary directory for test budget files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def budget(self, temp_project_root):
        """Create TokenBudget instance with test directory."""
        return TokenBudget(project_root=temp_project_root, monthly_budget=1000)

    def test_initialization_creates_budget_file(self, budget, temp_project_root):
        """
        Test that initializing TokenBudget creates budget file.

        Given: A new TokenBudget instance
        When: Initializing with project_root and monthly_budget
        Then: Budget file should be created with default values
        """
        budget_file = temp_project_root / ".claude" / "token_budget.json"
        assert budget_file.exists(), "Budget file should be created"

        data = json.loads(budget_file.read_text())
        assert data["monthly_budget"] == 1000
        assert data["used_this_month"] == 0
        assert data["month"] == datetime.now().strftime("%Y-%m")


class TestCheckBudgetAllowsWithinLimit:
    """Tests for check_budget allowing tokens when under budget."""

    @pytest.fixture
    def temp_project_root(self):
        """Create temporary directory for test budget files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def budget(self, temp_project_root):
        """Create TokenBudget instance with test directory."""
        return TokenBudget(project_root=temp_project_root, monthly_budget=1000)

    def test_check_budget_allows_within_limit(self, budget):
        """
        Test that tokens are allowed when under budget.

        Given: Budget is at 0% usage (0/1000 tokens used)
        When: Checking budget for 500 tokens
        Then: Should return (True, message) with OK status
        """
        allowed, message = budget.check_budget(500)

        assert allowed is True, f"Expected True, got {allowed}"
        assert "OK" in message, f"Expected 'OK' in message, got: {message}"
        assert "0.0%" in message or "0%" in message, f"Expected 0% in message, got: {message}"


class TestCheckBudgetDeniesOverLimit:
    """Tests for check_budget denying tokens when over budget."""

    @pytest.fixture
    def temp_project_root(self):
        """Create temporary directory for test budget files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def budget(self, temp_project_root):
        """Create TokenBudget instance with test directory."""
        return TokenBudget(project_root=temp_project_root, monthly_budget=1000)

    def test_check_budget_denies_over_limit(self, budget):
        """
        Test that tokens are denied when exceeding budget.

        Given: Budget is at 50% usage (500/1000 tokens used)
        When: Checking budget for 600 tokens (would exceed)
        Then: Should return (False, message) with BLOCKED status
        """
        # First, use 500 tokens
        budget.record_usage(500)

        # Try to use 600 more (would exceed 1000)
        allowed, message = budget.check_budget(600)

        assert allowed is False, f"Expected False (deny), got {allowed}"
        assert "BLOCKED" in message, f"Expected 'BLOCKED' in message, got: {message}"
        assert "exceed" in message.lower(), f"Expected 'exceed' in message, got: {message}"


class TestCheckBudgetWarningThreshold:
    """Tests for 70% warning threshold behavior."""

    @pytest.fixture
    def temp_project_root(self):
        """Create temporary directory for test budget files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def budget(self, temp_project_root):
        """Create TokenBudget instance with test directory."""
        return TokenBudget(project_root=temp_project_root, monthly_budget=1000)

    def test_check_budget_warns_at_70_percent(self, budget):
        """
        Test that warning is shown at 70% threshold.

        Given: Budget is at 70% usage (700/1000 tokens used)
        When: Checking budget for more tokens
        Then: Should return (True, message) with WARNING status
        """
        # Use 700 tokens (70%)
        budget.record_usage(700)

        # Check budget for 100 more
        allowed, message = budget.check_budget(100)

        assert allowed is True, f"Expected True (still allow with warning), got {allowed}"
        assert "WARNING" in message, f"Expected 'WARNING' in message, got: {message}"

    def test_check_budget_warns_at_75_percent(self, budget):
        """
        Test that warning is shown above 70% threshold.

        Given: Budget is at 75% usage (750/1000 tokens used)
        When: Checking budget for more tokens
        Then: Should return (True, message) with WARNING status
        """
        # Use 750 tokens (75%)
        budget.record_usage(750)

        # Check budget for 50 more
        allowed, message = budget.check_budget(50)

        assert allowed is True, f"Expected True (still allow with warning), got {allowed}"
        assert "WARNING" in message, f"Expected 'WARNING' in message, got: {message}"
        assert "75" in message or "70" in message, f"Expected percentage in message, got: {message}"


class TestCheckBudgetBlockThreshold:
    """Tests for 90% blocking threshold behavior."""

    @pytest.fixture
    def temp_project_root(self):
        """Create temporary directory for test budget files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def budget(self, temp_project_root):
        """Create TokenBudget instance with test directory."""
        return TokenBudget(project_root=temp_project_root, monthly_budget=1000)

    def test_check_budget_blocks_at_90_percent(self, budget):
        """
        Test that operations are blocked at 90% threshold.

        Given: Budget is at 90% usage (900/1000 tokens used)
        When: Checking budget for more tokens
        Then: Should return (False, message) with BLOCKED status
        """
        # Use 900 tokens (90%)
        budget.record_usage(900)

        # Check budget for 100 more
        allowed, message = budget.check_budget(100)

        assert allowed is False, f"Expected False (block at 90%), got {allowed}"
        assert "BLOCKED" in message, f"Expected 'BLOCKED' in message, got: {message}"


class TestCheckBudgetResetsOnNewMonth:
    """Tests for monthly reset behavior."""

    @pytest.fixture
    def temp_project_root(self):
        """Create temporary directory for test budget files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def budget(self, temp_project_root):
        """Create TokenBudget instance with test directory."""
        return TokenBudget(project_root=temp_project_root, monthly_budget=1000)

    def test_check_budget_resets_on_new_month(self, budget, temp_project_root):
        """
        Test that budget counter resets when month changes.

        Given: Budget has 500 tokens used in previous month
        When: Month rolls over and check_budget is called
        Then: Counter should reset to 0 for new month
        """
        # Use 500 tokens
        budget.record_usage(500)

        # Verify usage is 500
        status = budget.get_status()
        assert status.used_this_month == 500, f"Expected 500 used, got {status.used_this_month}"

        # Manually modify budget file to simulate new month
        budget_file = temp_project_root / ".claude" / "token_budget.json"
        data = json.loads(budget_file.read_text())

        # Set month to previous month
        current_date = datetime.now()
        if current_date.month == 1:
            prev_month = "12"
            prev_year = current_date.year - 1
        else:
            prev_month = f"{current_date.month - 1:02d}"
            prev_year = current_date.year

        data["month"] = f"{prev_year}-{prev_month}"
        budget_file.write_text(json.dumps(data))

        # Check budget should trigger reset
        allowed, message = budget.check_budget(100)

        # Verify counter was reset
        status = budget.get_status()
        assert status.used_this_month == 0, f"Expected 0 used after month reset, got {status.used_this_month}"
        assert allowed is True, "Should allow tokens after reset"


class TestRecordUsage:
    """Tests for record_usage method."""

    @pytest.fixture
    def temp_project_root(self):
        """Create temporary directory for test budget files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def budget(self, temp_project_root):
        """Create TokenBudget instance with test directory."""
        return TokenBudget(project_root=temp_project_root, monthly_budget=1000)

    def test_record_usage_increments_counter(self, budget):
        """
        Test that record_usage increments the token counter.

        Given: Budget has 0 tokens used
        When: Recording 500 tokens used
        Then: Counter should increment to 500
        """
        status_before = budget.get_status()
        assert status_before.used_this_month == 0

        success = budget.record_usage(500)
        assert success is True, "record_usage should return True"

        status_after = budget.get_status()
        assert status_after.used_this_month == 500, f"Expected 500 used, got {status_after.used_this_month}"

    def test_record_usage_multiple_calls(self, budget):
        """
        Test that multiple record_usage calls accumulate correctly.

        Given: Budget has 0 tokens used
        When: Recording 300 tokens, then 200 tokens
        Then: Counter should show 500 total
        """
        budget.record_usage(300)
        budget.record_usage(200)

        status = budget.get_status()
        assert status.used_this_month == 500, f"Expected 500 used, got {status.used_this_month}"


class TestResetMonthly:
    """Tests for reset_monthly method."""

    @pytest.fixture
    def temp_project_root(self):
        """Create temporary directory for test budget files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def budget(self, temp_project_root):
        """Create TokenBudget instance with test directory."""
        return TokenBudget(project_root=temp_project_root, monthly_budget=1000)

    def test_reset_monthly_clears_counter(self, budget):
        """
        Test that reset_monthly clears the usage counter.

        Given: Budget has 500 tokens used
        When: Calling reset_monthly()
        Then: Counter should reset to 0
        """
        # Use some tokens
        budget.record_usage(500)
        assert budget.get_status().used_this_month == 500

        # Reset
        success = budget.reset_monthly()
        assert success is True, "reset_monthly should return True"

        # Verify reset
        status = budget.get_status()
        assert status.used_this_month == 0, f"Expected 0 used after reset, got {status.used_this_month}"

    def test_reset_monthly_archives_to_history(self, budget, temp_project_root):
        """
        Test that reset_monthly archives usage to history.

        Given: Budget has 500 tokens used
        When: Calling reset_monthly()
        Then: Previous usage should be in history array
        """
        # Use some tokens
        budget.record_usage(500)

        # Reset
        budget.reset_monthly()

        # Check history
        budget_file = temp_project_root / ".claude" / "token_budget.json"
        data = json.loads(budget_file.read_text())

        assert "history" in data, "Budget data should have history array"
        assert len(data["history"]) > 0, "History should have at least one entry"

        last_entry = data["history"][-1]
        assert last_entry["used"] == 500, f"Expected history entry with 500 used, got {last_entry}"
        assert last_entry.get("manual_reset") is True, "History entry should mark manual reset"


class TestGetStatus:
    """Tests for get_status method."""

    @pytest.fixture
    def temp_project_root(self):
        """Create temporary directory for test budget files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def budget(self, temp_project_root):
        """Create TokenBudget instance with test directory."""
        return TokenBudget(project_root=temp_project_root, monthly_budget=1000)

    def test_get_status_returns_remaining_tokens(self, budget):
        """
        Test that get_status shows remaining tokens.

        Given: Budget is 1000 with 400 used
        When: Calling get_status()
        Then: Status should show 600 remaining
        """
        budget.record_usage(400)

        status = budget.get_status()
        assert status.remaining == 600, f"Expected 600 remaining, got {status.remaining}"

    def test_get_status_shows_percentage_used(self, budget):
        """
        Test that get_status shows percentage used.

        Given: Budget is 1000 with 250 used
        When: Calling get_status()
        Then: Status should show 25% used
        """
        budget.record_usage(250)

        status = budget.get_status()
        assert status.percent_used == 25.0, f"Expected 25.0%, got {status.percent_used}"

    def test_get_status_ok_when_under_70_percent(self, budget):
        """
        Test that get_status returns 'ok' status when under 70%.

        Given: Budget is at 50% usage
        When: Calling get_status()
        Then: Status should be 'ok'
        """
        budget.record_usage(500)

        status = budget.get_status()
        assert status.status == "ok", f"Expected 'ok' status, got {status.status}"

    def test_get_status_warning_when_70_to_90_percent(self, budget):
        """
        Test that get_status returns 'warning' status between 70-90%.

        Given: Budget is at 75% usage
        When: Calling get_status()
        Then: Status should be 'warning'
        """
        budget.record_usage(750)

        status = budget.get_status()
        assert status.status == "warning", f"Expected 'warning' status, got {status.status}"

    def test_get_status_blocked_when_over_90_percent(self, budget):
        """
        Test that get_status returns 'blocked' status over 90%.

        Given: Budget is at 95% usage
        When: Calling get_status()
        Then: Status should be 'blocked'
        """
        budget.record_usage(950)

        status = budget.get_status()
        assert status.status == "blocked", f"Expected 'blocked' status, got {status.status}"

    def test_get_status_returns_budget_status_dataclass(self, budget):
        """
        Test that get_status returns BudgetStatus dataclass.

        Given: A TokenBudget instance
        When: Calling get_status()
        Then: Should return BudgetStatus with correct fields
        """
        budget.record_usage(300)

        status = budget.get_status()

        assert isinstance(status, BudgetStatus), f"Expected BudgetStatus instance, got {type(status)}"
        assert hasattr(status, "monthly_budget")
        assert hasattr(status, "used_this_month")
        assert hasattr(status, "remaining")
        assert hasattr(status, "percent_used")
        assert hasattr(status, "status")

        assert status.monthly_budget == 1000
        assert status.used_this_month == 300
        assert status.remaining == 700
        assert status.percent_used == 30.0
        assert status.status == "ok"


class TestSetBudget:
    """Tests for set_budget method."""

    @pytest.fixture
    def temp_project_root(self):
        """Create temporary directory for test budget files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def budget(self, temp_project_root):
        """Create TokenBudget instance with test directory."""
        return TokenBudget(project_root=temp_project_root, monthly_budget=1000)

    def test_set_budget_updates_monthly_allocation(self, budget):
        """
        Test that set_budget updates the monthly budget.

        Given: Budget is set to 1000 tokens
        When: Calling set_budget(2000)
        Then: Budget should update to 2000 tokens
        """
        budget.set_budget(2000)

        status = budget.get_status()
        assert status.monthly_budget == 2000, f"Expected 2000 budget, got {status.monthly_budget}"

    def test_set_budget_affects_remaining_calculation(self, budget):
        """
        Test that set_budget affects remaining tokens calculation.

        Given: 500 used out of 1000 budget
        When: Updating budget to 2000
        Then: Remaining should be 1500
        """
        budget.record_usage(500)
        budget.set_budget(2000)

        status = budget.get_status()
        assert status.remaining == 1500, f"Expected 1500 remaining, got {status.remaining}"
