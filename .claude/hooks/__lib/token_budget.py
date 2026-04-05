#!/usr/bin/env python3
"""
Token Budget Circuit Breaker - Prevent surprise API bills.

Tracks monthly token usage with configurable thresholds:
- Warn at 70% of budget
- Block at 90% of budget

Constitutional Requirements:
- Solo developer optimization (manual reset, simple JSON storage)
- Evidence-based implementation (thresholds based on actual usage)
- Force multiplier (prevent bill shock)
- No enterprise bloat (direct file I/O, no database)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BudgetStatus:
    """Current budget status."""
    monthly_budget: int
    used_this_month: int
    remaining: int
    percent_used: float
    status: str  # "ok", "warning", "blocked"


class TokenBudget:
    """
    Token budget circuit breaker with monthly tracking.

    Thresholds:
    - 0-70%: OK (allow operations)
    - 70-90%: WARNING (allow with warning message)
    - 90-100%: BLOCKED (deny operations)

    Usage:
        budget = TokenBudget(Path("P:/"), monthly_budget=1_000_000)
        ok, msg = budget.check_budget(5000)
        if ok:
            budget.record_usage(5000)
    """

    def __init__(self, project_root: Path | None = None, monthly_budget: int = 1_000_000):
        """
        Initialize token budget tracker.

        Args:
            project_root: Root directory of project (defaults to P:/)
            monthly_budget: Monthly token budget (default: 1M tokens)
        """
        self.project_root = Path(project_root) if project_root else Path("P:/")
        self.budget_file = self.project_root / ".claude" / "token_budget.json"
        self.monthly_budget = monthly_budget

        # Ensure budget file exists
        self._init_budget_file()

    def _init_budget_file(self) -> None:
        """Initialize budget file with defaults if missing."""
        if not self.budget_file.exists():
            self.budget_file.parent.mkdir(parents=True, exist_ok=True)
            default_data = {
                "monthly_budget": self.monthly_budget,
                "used_this_month": 0,
                "month": datetime.now().strftime("%Y-%m"),
                "last_updated": datetime.now().isoformat(),
                "history": []
            }
            self.budget_file.write_text(json.dumps(default_data, indent=2))
            logger.info(f"[TokenBudget] Initialized budget file: {self.budget_file}")

    def _load_data(self) -> dict:
        """Load budget data from file."""
        try:
            raw = self.budget_file.read_text()
            return json.loads(raw)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"[TokenBudget] Failed to load budget: {e}")
            return {}

    def _save_data(self, data: dict) -> bool:
        """Save budget data to file."""
        try:
            data["last_updated"] = datetime.now().isoformat()
            self.budget_file.write_text(json.dumps(data, indent=2))
            return True
        except OSError as e:
            logger.error(f"[TokenBudget] Failed to save budget: {e}")
            return False

    def _check_month_reset(self, data: dict) -> dict:
        """
        Check if month has rolled over and reset if needed.

        Args:
            data: Current budget data

        Returns:
            Updated data (reset if new month)
        """
        current_month = datetime.now().strftime("%Y-%m")
        stored_month = data.get("month", "")

        if current_month != stored_month:
            logger.info(f"[TokenBudget] Month rollover: {stored_month} -> {current_month}")

            # Archive previous month to history
            if data.get("used_this_month", 0) > 0:
                history_entry = {
                    "month": stored_month,
                    "used": data.get("used_this_month", 0),
                    "budget": data.get("monthly_budget", self.monthly_budget)
                }
                data.setdefault("history", []).append(history_entry)

            # Reset counters
            data["month"] = current_month
            data["used_this_month"] = 0

        return data

    def check_budget(self, tokens_needed: int) -> tuple[bool, str]:
        """
        Check if operation is allowed within budget.

        Args:
            tokens_needed: Number of tokens required for operation

        Returns:
            Tuple of (allowed: bool, message: str)
        """
        data = self._load_data()
        data = self._check_month_reset(data)

        used = data.get("used_this_month", 0)
        remaining = self.monthly_budget - used
        percent_used = (used / self.monthly_budget) * 100

        # Check block threshold (90%)
        if percent_used >= 90:
            msg = (
                f"[TokenBudget] BLOCKED: Budget at {percent_used:.1f}%. "
                f"Used: {used:,}/{self.monthly_budget:,}, Remaining: {remaining:,}"
            )
            logger.warning(msg)
            return False, f"BLOCKED: {msg}"

        # Check if would exceed budget
        if used + tokens_needed > self.monthly_budget:
            msg = (
                f"[TokenBudget] BLOCKED: Would exceed budget. "
                f"Used: {used:,}/{self.monthly_budget:,} ({percent_used:.1f}%), "
                f"Need: {tokens_needed:,}, Remaining: {remaining:,}"
            )
            logger.warning(msg)
            return False, f"BLOCKED: {msg}"

        # Check warning threshold (70%)
        if percent_used >= 70:
            msg = (
                f"[TokenBudget] WARNING: Budget at {percent_used:.1f}%. "
                f"Used: {used:,}/{self.monthly_budget:,}, Remaining: {remaining:,}"
            )
            logger.warning(msg)
            return True, f"WARNING: {msg}"

        # Within budget
        msg = (
            f"[TokenBudget] OK: Budget at {percent_used:.1f}%. "
            f"Used: {used:,}/{self.monthly_budget:,}, Remaining: {remaining:,}"
        )
        logger.info(msg)
        return True, msg

    def record_usage(self, tokens_used: int) -> bool:
        """
        Record token usage after operation completes.

        Args:
            tokens_used: Actual tokens consumed

        Returns:
            True if successful
        """
        data = self._load_data()
        data = self._check_month_reset(data)

        data["used_this_month"] = data.get("used_this_month", 0) + tokens_used

        success = self._save_data(data)
        if success:
            logger.info(f"[TokenBudget] Recorded: {tokens_used:,} tokens (total: {data['used_this_month']:,})")

        return success

    def reset_monthly(self) -> bool:
        """
        Manually reset monthly counter (use with caution).

        Useful for mid-month budget adjustments.

        Returns:
            True if successful
        """
        data = self._load_data()
        current_month = datetime.now().strftime("%Y-%m")

        # Archive to history before reset
        if data.get("used_this_month", 0) > 0:
            history_entry = {
                "month": data.get("month", current_month),
                "used": data.get("used_this_month", 0),
                "budget": data.get("monthly_budget", self.monthly_budget),
                "manual_reset": True,
                "reset_at": datetime.now().isoformat()
            }
            data.setdefault("history", []).append(history_entry)

        data["month"] = current_month
        data["used_this_month"] = 0

        success = self._save_data(data)
        if success:
            logger.info("[TokenBudget] Monthly counter reset")

        return success

    def get_status(self) -> BudgetStatus:
        """
        Get current budget status.

        Returns:
            BudgetStatus dataclass with current state
        """
        data = self._load_data()
        data = self._check_month_reset(data)

        used = data.get("used_this_month", 0)
        remaining = self.monthly_budget - used
        percent_used = (used / self.monthly_budget) * 100

        # Determine status
        if percent_used >= 90:
            status = "blocked"
        elif percent_used >= 70:
            status = "warning"
        else:
            status = "ok"

        return BudgetStatus(
            monthly_budget=self.monthly_budget,
            used_this_month=used,
            remaining=remaining,
            percent_used=round(percent_used, 2),
            status=status
        )

    def set_budget(self, new_budget: int) -> bool:
        """
        Update monthly budget allocation.

        Args:
            new_budget: New monthly token budget

        Returns:
            True if successful
        """
        data = self._load_data()
        data["monthly_budget"] = new_budget
        self.monthly_budget = new_budget

        success = self._save_data(data)
        if success:
            logger.info(f"[TokenBudget] Budget updated: {new_budget:,} tokens/month")

        return success


if __name__ == "__main__":
    # Test token budget

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    budget = TokenBudget(Path("P:/"), monthly_budget=1000)

    print("Token Budget Test")
    print("=" * 50)

    # Test 1: Check budget at 0%
    ok, msg = budget.check_budget(500)
    print(f"Test 1 (0%): {ok} - {msg}")
    assert ok, "Should allow at 0%"

    # Test 2: Use 500 tokens (50%)
    budget.record_usage(500)
    status = budget.get_status()
    print(f"Test 2 (50%): status={status.status}, used={status.used_this_month}")
    assert status.status == "ok", "Should be OK at 50%"

    # Test 3: Check budget at 50% (need 300 more = 80%)
    ok, msg = budget.check_budget(300)
    print(f"Test 3 (50%->80%): {ok} - {msg}")
    assert ok, "Should allow at 80%"
    assert "WARNING" in msg, "Should warn at 70%+"

    # Test 4: Try to exceed budget (50% + 300 + 300 = 110%)
    ok, msg = budget.check_budget(300)
    print(f"Test 4 (80%->110%): {ok} - {msg}")
    assert not ok, "Should block at 90%+"
    assert "BLOCKED" in msg, "Should block when exceeding budget"

    # Test 5: Get status
    status = budget.get_status()
    print(f"\nFinal status: {status.percent_used}% used ({status.used_this_month:,}/{status.monthly_budget:,})")

    # Reset for next test
    budget.reset_monthly()

    print("\n✓ All tests passed!")
