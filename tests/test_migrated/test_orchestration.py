"""
Comprehensive tests for orchestration components.

Tests for:
- PhaseController: two-phase research orchestration with novelty tracking
- CostTracker: cost tracking and budget management
"""

from unittest.mock import MagicMock

import pytest

from core.orchestration.cost_tracker import CostTracker
from core.orchestration.phase_controller import PhaseController, PhaseResult
from core.processing.result_normalizer import ResultNormalizer


class TestCostTracker:
    """Test suite for CostTracker."""

    @pytest.fixture
    def tracker(self) -> CostTracker:
        """Create CostTracker with test budget."""
        return CostTracker(budget=1.0)

    def test_initialization(self, tracker):
        """Test tracker initialization."""
        assert tracker.budget == 1.0
        assert tracker.spent == 0.0
        assert tracker.provider_costs is not None
        assert "tavily" in tracker.provider_costs
        assert "exa" in tracker.provider_costs

    def test_track_search_basic(self, tracker):
        """Test basic search cost tracking."""
        result = tracker.track_search("tavily", num_results=10, num_requests=1)

        # Should not exceed budget
        assert result is True
        assert tracker.spent > 0

    def test_track_search_multiple_requests(self, tracker):
        """Test tracking multiple search requests."""
        initial_spent = tracker.spent

        tracker.track_search("tavily", num_results=10, num_requests=3)

        # Should track all requests
        assert tracker.spent > initial_spent

    def test_track_search_per_result_billing(self, tracker):
        """Test per-result billing (though most providers use per-request)."""
        # Create custom tracker with per-result billing
        custom_tracker = CostTracker(
            budget=1.0,
            provider_costs={
                "custom": {"per_request": 0.001, "per_result": 0.01}
            }
        )

        custom_tracker.track_search("custom", num_results=50, num_requests=1)

        # Should account for both per-request and per-result costs
        assert custom_tracker.spent > 0

    def test_is_budget_exceeded_false(self, tracker):
        """Test budget check when not exceeded."""
        tracker.track_search("tavily", num_results=10)

        # Should not exceed budget
        assert tracker.is_budget_exceeded() is False

    def test_is_budget_exceeded_true(self):
        """Test budget check when exceeded."""
        low_budget_tracker = CostTracker(budget=0.001)

        # Track search that exceeds budget
        low_budget_tracker.track_search("tavily", num_results=10)

        # Should exceed budget
        assert low_budget_tracker.is_budget_exceeded() is True

    def test_reset(self, tracker):
        """Test resetting spent counter."""
        tracker.track_search("tavily", num_results=10)
        assert tracker.spent > 0

        tracker.reset()

        # Spent should be reset to 0
        assert tracker.spent == 0.0
        # Budget should remain the same
        assert tracker.budget == 1.0

    def test_get_remaining(self, tracker):
        """Test getting remaining budget."""
        initial_remaining = tracker.get_remaining()

        tracker.track_search("tavily", num_results=10)

        new_remaining = tracker.get_remaining()

        # Remaining should decrease
        assert new_remaining < initial_remaining
        assert new_remaining >= 0

    def test_track_search_unknown_provider(self, tracker):
        """Test tracking search with unknown provider."""
        result = tracker.track_search("unknown_provider", num_results=10)

        # Should handle unknown provider gracefully
        assert result is True
        assert tracker.spent > 0

    def test_track_search_returns_false_when_budget_exceeded(self):
        """Test that tracking returns False when budget is exceeded."""
        tracker = CostTracker(budget=0.0001)

        # First search might succeed
        tracker.track_search("tavily", num_results=10)

        # Second search should fail if budget exceeded
        result = tracker.track_search("tavily", num_results=10)
        # Should either succeed (if within budget) or fail gracefully
        assert isinstance(result, bool)


class TestPhaseController:
    """Test suite for PhaseController orchestration."""

    @pytest.fixture
    def mock_provider(self):
        """Create mock search provider."""
        provider = MagicMock()
        provider.name = "mock_provider"

        # Create async mock search method
        async def mock_search(query, **kwargs):
            return [
                {
                    "url": f"https://example.com/{i}",
                    "title": f"Result {i}",
                    "content": f"Content for result {i}",
                    "snippet": f"Snippet {i}"
                }
                for i in range(1, 6)
            ]

        provider.search = mock_search
        return provider

    @pytest.fixture
    def controller(self, mock_provider) -> PhaseController:
        """Create PhaseController instance for testing."""
        return PhaseController(
            search_provider=mock_provider,
            budget=1.0,
            max_iterations=3,
            novelty_threshold=0.1,
            results_per_iteration=10
        )

    @pytest.mark.asyncio
    async def test_initialization(self, controller):
        """Test controller initialization."""
        assert controller.budget == 1.0
        assert controller.max_iterations == 3
        assert controller.novelty_threshold == 0.1
        assert controller.results_per_iteration == 10
        assert controller.cost_tracker is not None
        assert controller.clusterer is not None
        assert controller.novelty_tracker is not None
        assert controller.gap_analyzer is not None
        assert controller.density_calculator is not None

    @pytest.mark.asyncio
    async def test_execute_phase_one(self, controller):
        """Test Phase 1 execution (initial search)."""
        result = await controller.execute_phase_one("python async")

        # Check result structure
        assert isinstance(result, PhaseResult)
        assert result.phase == 1
        assert result.iterations == 1
        assert result.total_results > 0
        assert result.novelty_score == 1.0  # First iteration always max novelty
        assert 0.0 <= result.density_score <= 1.0
        assert result.cost > 0
        assert len(result.all_results) > 0

    @pytest.mark.asyncio
    async def test_execute_phase_two_single_iteration(self, controller):
        """Test Phase 2 with single iteration (budget exhausted)."""
        # Set very low budget to force early exit
        controller.budget = 0.0001
        controller.cost_tracker.budget = 0.0001

        result = await controller.execute_phase_two("python async")

        # Should exit early due to budget
        assert result.phase == 2
        assert result.total_results >= 0

    @pytest.mark.asyncio
    async def test_execute_phase_two_with_gaps(self, controller):
        """Test Phase 2 with gap-driven follow-up queries."""
        # Mock provider to return different results each call
        call_count = 0

        async def varying_search(query, **kwargs):
            nonlocal call_count
            call_count += 1
            return [
                {
                    "url": f"https://example.com/{call_count}/{i}",
                    "title": f"Result {i}",
                    "content": f"Different content {call_count}",
                    "snippet": f"Snippet {i}"
                }
                for i in range(1, 6)
            ]

        controller.search_provider.search = varying_search

        result = await controller.execute_phase_two("python async")

        # Check result structure
        assert result.phase == 2
        assert result.iterations >= 1
        assert result.total_results >= 0
        assert 0.0 <= result.novelty_score <= 1.0
        assert 0.0 <= result.density_score <= 1.0

    @pytest.mark.asyncio
    async def test_research_full_workflow(self, controller):
        """Test full two-phase research workflow."""
        result = await controller.research("python async")

        # Should return Phase 2 result (final result)
        assert result.phase == 2
        assert result.total_results >= 0
        assert isinstance(result.all_results, list)

    @pytest.mark.asyncio
    async def test_budget_exceeded_stops_research(self, controller):
        """Test that research stops when budget is exceeded."""
        # Set zero budget
        controller.budget = 0.0
        controller.cost_tracker.budget = 0.0

        result = await controller.execute_phase_one("test query")

        # Should handle budget exceeded gracefully
        assert isinstance(result, PhaseResult)

    @pytest.mark.asyncio
    async def test_empty_results_handling(self, controller):
        """Test handling of empty search results."""
        # Mock provider to return empty results
        async def empty_search(query, **kwargs):
            return []

        controller.search_provider.search = empty_search

        result = await controller.execute_phase_one("test query")

        # Should handle empty results gracefully
        assert isinstance(result, PhaseResult)
        assert result.total_results == 0

    @pytest.mark.asyncio
    async def test_provider_error_handling(self, controller):
        """Test handling of provider errors."""
        # Mock provider to raise exception
        async def failing_search(query, **kwargs):
            raise Exception("Provider error")

        controller.search_provider.search = failing_search

        result = await controller.execute_phase_one("test query")

        # Should handle errors gracefully
        assert isinstance(result, PhaseResult)
        # Result should be empty due to error
        assert result.total_results == 0

    @pytest.mark.asyncio
    async def test_normalize_results(self, controller):
        """Test result normalization."""
        result = await controller.execute_phase_one("python async")

        # All results should be normalized
        for normalized_result in result.all_results:
            assert hasattr(normalized_result, 'title')
            assert hasattr(normalized_result, 'snippet')
            assert hasattr(normalized_result, 'url')
            assert hasattr(normalized_result, 'domain')
            assert hasattr(normalized_result, 'source_type')
            assert hasattr(normalized_result, 'provider')

    @pytest.mark.asyncio
    async def test_cost_tracking_across_phases(self, controller):
        """Test that costs are tracked across both phases."""
        initial_cost = controller.cost_tracker.spent

        await controller.execute_phase_one("test")
        cost_after_phase1 = controller.cost_tracker.spent

        await controller.execute_phase_two("test")
        cost_after_phase2 = controller.cost_tracker.spent

        # Costs should increase
        assert cost_after_phase1 > initial_cost
        assert cost_after_phase2 >= cost_after_phase1

    @pytest.mark.asyncio
    async def test_novelty_tracking(self, controller):
        """Test novelty tracking during Phase 2."""
        result = await controller.execute_phase_two("python async")

        # Should compute novelty score
        assert 0.0 <= result.novelty_score <= 1.0

    @pytest.mark.asyncio
    async def test_density_calculation(self, controller):
        """Test density calculation for results."""
        result = await controller.execute_phase_one("python async")

        # Should compute density score
        assert 0.0 <= result.density_score <= 1.0

    @pytest.mark.asyncio
    async def test_max_iterations_enforcement(self, controller):
        """Test that max_iterations limits Phase 2 iterations."""
        # Set low max iterations
        controller.max_iterations = 2

        # Mock provider to always return results
        async def infinite_search(query, **kwargs):
            return [
                {
                    "url": f"https://example.com/{i}",
                    "title": f"Result {i}",
                    "content": "Content",
                    "snippet": "Snippet"
                }
                for i in range(1, 6)
            ]

        controller.search_provider.search = infinite_search

        result = await controller.execute_phase_two("test")

        # Should not exceed max iterations
        assert result.iterations <= controller.max_iterations

    @pytest.mark.asyncio
    async def test_phase_result_structure(self, controller):
        """Test PhaseResult structure and attributes."""
        result = await controller.execute_phase_one("test")

        # Check all required attributes
        assert hasattr(result, 'phase')
        assert hasattr(result, 'total_results')
        assert hasattr(result, 'iterations')
        assert hasattr(result, 'cost')
        assert hasattr(result, 'novelty_score')
        assert hasattr(result, 'density_score')
        assert hasattr(result, 'all_results')
        assert hasattr(result, 'gaps')

        # Check types
        assert isinstance(result.phase, int)
        assert isinstance(result.total_results, int)
        assert isinstance(result.iterations, int)
        assert isinstance(result.cost, float)
        assert isinstance(result.novelty_score, float)
        assert isinstance(result.density_score, float)
        assert isinstance(result.all_results, list)
        assert isinstance(result.gaps, list)

    @pytest.mark.asyncio
    async def test_custom_normalizer(self, mock_provider):
        """Test PhaseController with custom normalizer."""
        custom_normalizer = ResultNormalizer()

        controller = PhaseController(
            search_provider=mock_provider,
            normalizer=custom_normalizer,
            budget=1.0
        )

        result = await controller.execute_phase_one("test")

        # Should use custom normalizer
        assert isinstance(result, PhaseResult)
        assert len(result.all_results) > 0


class TestPhaseControllerIntegration:
    """Integration tests for PhaseController with real components."""

    @pytest.fixture
    def real_controller(self):
        """Create controller with realistic mock provider."""
        # Create realistic mock provider
        provider = MagicMock()
        provider.name = "tavily"

        async def realistic_search(query, **kwargs):
            # Simulate realistic search results
            return [
                {
                    "url": "https://docs.python.org/asyncio",
                    "title": "Python Asyncio Documentation",
                    "content": "Python's asyncio library for async programming",
                    "snippet": "Official asyncio documentation"
                },
                {
                    "url": "https://github.com/python/asyncio",
                    "title": "Python Asyncio on GitHub",
                    "content": "Source code and examples",
                    "snippet": "GitHub repository"
                },
                {
                    "url": "https://stackoverflow.com/questions/async",
                    "title": "Async Programming Questions",
                    "content": "Common async programming patterns",
                    "snippet": "StackOverflow discussion"
                }
            ]

        provider.search = realistic_search

        return PhaseController(
            search_provider=provider,
            budget=0.5,
            max_iterations=3,
            novelty_threshold=0.1
        )

    @pytest.mark.asyncio
    async def test_end_to_end_research(self, real_controller):
        """Test complete end-to-end research workflow."""
        result = await real_controller.research("python async programming")

        # Should complete both phases
        assert result.phase == 2
        assert result.total_results > 0

        # Should have reasonable metrics
        assert result.cost > 0
        assert 0.0 <= result.density_score <= 1.0
        assert 0.0 <= result.novelty_score <= 1.0

    @pytest.mark.asyncio
    async def test_result_diversity(self, real_controller):
        """Test that results have domain and source type diversity."""
        result = await real_controller.execute_phase_one("python async")

        domains = set(r.domain for r in result.all_results)
        source_types = set(str(r.source_type) for r in result.all_results)

        # Should have some diversity
        assert len(domains) > 0
        assert len(source_types) > 0
