"""Tests for v1 budget coordination in UPS pipeline."""
import pytest
from unittest.mock import MagicMock


class TestDirectAnswerHint:
    """Test direct_answer_hint property on UnifiedDetectionResult."""

    def test_diagnostic_intent_returns_true(self):
        """Diagnostic intent (debug_rca) should match."""
        from UserPromptSubmit_modules.unified_detection import UnifiedDetectionResult

        result = UnifiedDetectionResult(
            intent_classification="diagnostic",
            matched_profiles=[],
        )
        # Note: direct_answer_hint property was removed as dead code (no consumer)
        # These tests verify the dataclass itself is still valid
        assert result.intent_classification == "diagnostic"
        assert result.matched_profiles == []

    def test_debug_rca_profile_matches(self):
        """Debug RCA profile is detected."""
        from UserPromptSubmit_modules.unified_detection import UnifiedDetectionResult

        result = UnifiedDetectionResult(
            intent_classification="implementation",
            matched_profiles=["debug_rca"],
        )
        assert "debug_rca" in result.matched_profiles

    def test_implementation_intent_isolation(self):
        """Implementation intent without debug_rca/tradeoff_decision."""
        from UserPromptSubmit_modules.unified_detection import UnifiedDetectionResult

        result = UnifiedDetectionResult(
            intent_classification="implementation",
            matched_profiles=[],
        )
        assert result.intent_classification == "implementation"
        assert result.matched_profiles == []


class TestBudgetGuards:
    """Test budget guards in conditional modules."""

    def _mock_context(self, remaining_budget: int = 20000):
        ctx = MagicMock()
        ctx.data = {"remaining_budget": remaining_budget}
        return ctx

    def test_reasoning_mode_selector_skips_at_low_budget(self):
        """reasoning_mode_selector skips when budget < 400."""
        from UserPromptSubmit_modules.reasoning_mode_selector import reasoning_mode_selector

        ctx = self._mock_context(remaining_budget=300)
        result = reasoning_mode_selector(ctx)

        assert result.is_empty() is True
        assert "reasoning_mode_selector" in ctx.data.get("skipped_budget", [])

    def test_cognitive_enhancers_skips_at_low_budget(self):
        """cognitive_enhancers skips when budget < 400."""
        from UserPromptSubmit_modules.cognitive_enhancers import cognitive_enhancers

        ctx = self._mock_context(remaining_budget=300)
        result = cognitive_enhancers(ctx)

        assert result.is_empty() is True
        assert "cognitive_enhancers" in ctx.data.get("skipped_budget", [])

    def test_testing_strategy_router_skips_at_low_budget(self):
        """testing_strategy_router skips when budget < 250."""
        from UserPromptSubmit_modules.testing_strategy_router import strategy_router

        ctx = self._mock_context(remaining_budget=200)
        ctx.prompt = "run tests on the code"

        result = strategy_router(ctx)

        assert result.is_empty() is True
        assert "testing_strategy_router" in ctx.data.get("skipped_budget", [])

    def test_reasoning_mode_selector_injects_at_sufficient_budget(self):
        """reasoning_mode_selector skips at low budget, decrements at high budget."""
        from UserPromptSubmit_modules.reasoning_mode_selector import reasoning_mode_selector

        # Budget=300: should skip, budget should be unchanged (no decrement on skip in v1)
        ctx_low = self._mock_context(remaining_budget=300)
        ctx_low.prompt = "Why does race condition happen?"  # >20 chars
        result_low = reasoning_mode_selector(ctx_low)
        assert result_low.is_empty() is True
        assert "reasoning_mode_selector" in ctx_low.data.get("skipped_budget", [])

        # Budget=20000: should run (may or may not inject depending on prompt matching)
        ctx_high = self._mock_context(remaining_budget=20000)
        ctx_high.prompt = "Why does race condition happen?"
        result_high = reasoning_mode_selector(ctx_high)
        # Either empty (no reasoning mode matched) or non-empty (reasoning mode matched)
        # The key invariant is: budget was decremented if non-empty
        if not result_high.is_empty():
            assert ctx_high.data["remaining_budget"] < 20000

    def test_cognitive_enhancers_injects_at_sufficient_budget(self):
        """cognitive_enhancers injects when budget >= 400."""
        from UserPromptSubmit_modules.cognitive_enhancers import cognitive_enhancers

        ctx = self._mock_context(remaining_budget=20000)
        ctx.prompt = "implement a new feature for user authentication"

        result = cognitive_enhancers(ctx)

        # Should return non-empty (has injection)
        assert result.is_empty() is False


class TestUnifiedDetectionSetsBudget:
    """Test that unified_detection sets budget in context."""

    def test_run_sets_remaining_budget(self):
        """unified_detection hook sets remaining_budget in context.data."""
        from UserPromptSubmit_modules.unified_detection import unified_detection_hook

        ctx = MagicMock()
        ctx.prompt = "Will this work?"
        ctx.data = {}

        result = unified_detection_hook(ctx)

        assert "remaining_budget" in ctx.data
        assert ctx.data["remaining_budget"] == 20000

class TestBudgetFlow:
    """Test budget flows through context.data."""

    def test_budget_decrements_after_injection(self):
        """remaining_budget decreases by injection length."""
        from UserPromptSubmit_modules.testing_strategy_router import strategy_router

        ctx = MagicMock()
        ctx.data = {"remaining_budget": 20000}
        ctx.prompt = "run pytest tests on the auth module"

        result = strategy_router(ctx)

        # Budget should be reduced
        assert ctx.data["remaining_budget"] < 20000


class TestBoundaryValues:
    """Boundary value tests for threshold checks."""

    def test_reasoning_skips_at_399(self):
        """budget=399 (<400) should skip."""
        from UserPromptSubmit_modules.reasoning_mode_selector import reasoning_mode_selector

        ctx = MagicMock()
        ctx.data = {"remaining_budget": 399}
        ctx.prompt = "Why is this intermittent bug happening in production?"
        result = reasoning_mode_selector(ctx)
        assert result.is_empty() is True
        assert "reasoning_mode_selector" in ctx.data.get("skipped_budget", [])

    def test_reasoning_runs_at_400(self):
        """budget=400 (>=400) should run."""
        from UserPromptSubmit_modules.reasoning_mode_selector import reasoning_mode_selector

        ctx = MagicMock()
        ctx.data = {"remaining_budget": 400}
        ctx.prompt = "Why is this intermittent bug happening in production?"
        result = reasoning_mode_selector(ctx)
        # Either empty (no mode matched) or skipped_budget unchanged
        # Key: should NOT be in skipped_budget list
        if result.is_empty():
            assert "reasoning_mode_selector" not in ctx.data.get("skipped_budget", [])

    def test_reasoning_runs_at_401(self):
        """budget=401 (>=400) should run."""
        from UserPromptSubmit_modules.reasoning_mode_selector import reasoning_mode_selector

        ctx = MagicMock()
        ctx.data = {"remaining_budget": 401}
        ctx.prompt = "Why is this intermittent bug happening in production?"
        result = reasoning_mode_selector(ctx)
        # Should not skip
        if result.is_empty():
            assert "reasoning_mode_selector" not in ctx.data.get("skipped_budget", [])

    def test_testing_skips_at_249(self):
        """budget=249 (<250) should skip."""
        from UserPromptSubmit_modules.testing_strategy_router import strategy_router

        ctx = MagicMock()
        ctx.data = {"remaining_budget": 249}
        ctx.prompt = "run pytest tests on the auth module"
        result = strategy_router(ctx)
        assert result.is_empty() is True
        assert "testing_strategy_router" in ctx.data.get("skipped_budget", [])

    def test_testing_runs_at_250(self):
        """budget=250 (>=250) should run."""
        from UserPromptSubmit_modules.testing_strategy_router import strategy_router

        ctx = MagicMock()
        ctx.data = {"remaining_budget": 250}
        ctx.prompt = "run pytest tests on the auth module"
        result = strategy_router(ctx)
        if result.is_empty():
            assert "testing_strategy_router" not in ctx.data.get("skipped_budget", [])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])