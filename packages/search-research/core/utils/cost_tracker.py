"""Cost tracking with per-request billing semantics.

This module tracks API costs across providers with accurate per-request
billing semantics (not per-result, which was incorrect).
"""

from dataclasses import dataclass


@dataclass
class CostTracker:
    """Track research costs with per-provider billing semantics.

    Attributes:
        budget: Total budget in USD
        spent: Total spent so far
        provider_costs: Per-provider cost structure {per_request, per_result}
    """

    budget: float
    spent: float = 0.0
    provider_costs: dict = None

    def __post_init__(self):
        if self.provider_costs is None:
            # Per-request billing (most providers bill per search, not per result)
            self.provider_costs = {
                "exa": {"per_request": 0.01, "per_result": 0.0},
                "tavily": {"per_request": 0.005, "per_result": 0.0},
                "serper": {"per_request": 0.005, "per_result": 0.0},
                "brave": {"per_request": 0.001, "per_result": 0.0},
                "glm": {"per_request": 0.01, "per_result": 0.0},
                "zai": {"per_request": 0.005, "per_result": 0.0},
            }

    def track_search(self, provider: str, num_results: int = 0, num_requests: int = 1) -> bool:
        """Track cost of search operation.

        Args:
            provider: Provider name (tavily, serper, etc.)
            num_results: Number of results returned (for per-result billing)
            num_requests: Number of requests made (default: 1)

        Returns:
            True if budget not exceeded, False otherwise
        """
        costs = self.provider_costs.get(provider, {"per_request": 0.01, "per_result": 0.0})
        cost = (costs["per_request"] * num_requests) + (costs["per_result"] * num_results)
        self.spent += cost
        return self.spent < self.budget

    def is_budget_exceeded(self) -> bool:
        """Check if budget cap exceeded.

        Returns:
            True if spent >= budget
        """
        return self.spent >= self.budget

    def reset(self):
        """Reset spent counter (keep budget)."""
        self.spent = 0.0

    def get_remaining(self) -> float:
        """Get remaining budget.

        Returns:
            Remaining budget in USD
        """
        return max(0, self.budget - self.spent)
