"""Phase orchestration for two-phase research with novelty-based saturation."""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from ..analysis.density_calculator import DensityCalculator
from ..analysis.gap_analyzer import CoverageGap, GapAnalyzer
from ..analysis.topic_clusterer import NoveltyTracker, TopicClusterer
from ..query import NormalizedResult, ResultNormalizer
from .cost_tracker import CostTracker

logger = logging.getLogger(__name__)


@dataclass
class PhaseResult:
    """Result of a research phase."""
    phase: int
    total_results: int
    iterations: int
    cost: float
    novelty_score: float
    density_score: float
    all_results: list[Any] = field(default_factory=list)
    gaps: list[CoverageGap] = field(default_factory=list)


class PhaseController:
    """Orchestrates two-phase research with novelty-based saturation."""

    def __init__(
        self,
        search_provider: Any,
        normalizer: ResultNormalizer | None = None,
        budget: float = 1.0,
        max_iterations: int = 5,
        novelty_threshold: float = 0.05,
        results_per_iteration: int = 20
    ) -> None:
        self.search_provider = search_provider
        self.normalizer = normalizer or ResultNormalizer()
        self.budget = budget
        self.max_iterations = max_iterations
        self.novelty_threshold = novelty_threshold
        self.results_per_iteration = results_per_iteration

        # Initialize analyzers
        self.cost_tracker = CostTracker(budget=budget)
        self.clusterer = TopicClusterer()
        self.novelty_tracker = NoveltyTracker(novelty_threshold=novelty_threshold)
        self.gap_analyzer = GapAnalyzer()
        self.density_calculator = DensityCalculator()

    async def execute_phase_one(self, query: str) -> PhaseResult:
        """Execute Phase 1: Initial search."""
        results = await self._search_and_normalize(query)

        cost = self.cost_tracker.spent
        density = self.density_calculator.compute_density(results)

        return PhaseResult(
            phase=1,
            total_results=len(results),
            iterations=1,
            cost=cost,
            novelty_score=1.0,  # First iteration always max novelty
            density_score=density,
            all_results=results
        )

    async def execute_phase_two(self, query: str) -> PhaseResult:
        """Execute Phase 2: Iterative refinement with gap-driven queries."""
        all_results = []
        current_query = query
        iteration = 0

        while iteration < self.max_iterations:
            # Check budget before searching
            if self.cost_tracker.is_budget_exceeded():
                break

            # Search with current query
            results = await self._search_and_normalize(current_query)
            if not results:
                break

            all_results.extend(results)
            iteration += 1

            # Cluster and analyze coverage
            clusters = self.clusterer.cluster_results(results)
            source_types = {r.source_type for r in all_results}
            domains = {r.domain for r in all_results}

            coverage_state = self.novelty_tracker.compute_coverage_state(
                all_results, clusters
            )

            # Check if should continue
            if not self.novelty_tracker.should_continue(coverage_state):
                break

            # Detect gaps and generate follow-up query
            gaps = self.gap_analyzer.detect_gaps(
                all_results,
                set(clusters.keys()),
                {str(st) for st in source_types},
                domains
            )

            if not gaps:
                break

            # Use highest-severity gap for follow-up
            top_gap = gaps[0]
            current_query = self.gap_analyzer.generate_follow_up_query(query, top_gap)

        cost = self.cost_tracker.spent

        # Compute final novelty score from current vs previous state
        final_coverage = self.novelty_tracker.compute_coverage_state(
            all_results, self.clusterer.cluster_results(all_results)
        )
        novelty = self.novelty_tracker.compute_novelty(
            final_coverage,
            self.novelty_tracker._previous_state
        ) if self.novelty_tracker._previous_state else 1.0
        density = self.density_calculator.compute_density(all_results)

        return PhaseResult(
            phase=2,
            total_results=len(all_results),
            iterations=iteration,
            cost=cost,
            novelty_score=novelty,
            density_score=density,
            all_results=all_results,
            gaps=[]
        )

    async def research(self, query: str) -> PhaseResult:
        """Execute full two-phase research workflow."""
        # Phase 1: Initial search (discarded - Phase 2 supersedes)
        _ = await self.execute_phase_one(query)

        # Phase 2: Iterative refinement
        phase2_result = await self.execute_phase_two(query)

        return phase2_result

    async def _search_and_normalize(self, query: str) -> list[NormalizedResult]:
        """Search and normalize results with cost tracking and failover."""
        # Check budget
        if self.cost_tracker.is_budget_exceeded():
            return []

        try:
            # Execute search
            search_result = self.search_provider.search(query)

            # Handle both sync and async search providers
            if asyncio.iscoroutine(search_result):
                raw_results = await search_result
            else:
                raw_results = search_result

            # Track cost (per-request billing)
            provider_name = getattr(self.search_provider, '__class__', type(self.search_provider)).__name__
            self.cost_tracker.track_search(provider_name, len(raw_results))

            # Normalize results
            return self.normalizer.normalize_batch(raw_results, provider_name)

        except Exception as e:
            # Provider failed - log and return empty results
            # In production, this would trigger failover to backup providers
            logger.warning(f"Search provider failed: {e}")
            return []
