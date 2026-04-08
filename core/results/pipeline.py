"""Result processing pipeline orchestrator.

Migrated from research_skill.processors.pipeline (2025-03-08).
"""

from typing import Any

from .deduplication import DeduplicationProcessor
from .ensemble import EnsembleResult
from .ranking import RankingProcessor
from .synthesis import SynthesisProcessor


class ResultProcessingPipeline:
    """Pipeline for processing search results.

    Orchestrates deduplication, ranking, and synthesis steps.
    """

    def __init__(
        self,
        enable_deduplication: bool = True,
        enable_ranking: bool = True,
        enable_temporal_boosting: bool = False,
        dedup_similarity_threshold: float = 0.6,
        source_weights: dict[str, float] | None = None,
        freshness_half_life: int = 180,
    ):
        """Initialize the pipeline.

        Args:
            enable_deduplication: Whether to enable deduplication.
            enable_ranking: Whether to enable ranking.
            enable_temporal_boosting: Whether to enable temporal boosting.
            dedup_similarity_threshold: Similarity threshold for deduplication.
            source_weights: Source quality weights for ranking.
            freshness_half_life: Half-life for temporal freshness.
        """
        self.enable_deduplication = enable_deduplication
        self.enable_ranking = enable_ranking
        self.enable_temporal_boosting = enable_temporal_boosting

        self.deduplicator = DeduplicationProcessor(
            similarity_threshold=dedup_similarity_threshold,
        )
        self.synthesizer = SynthesisProcessor()
        self.ranker = RankingProcessor(
            source_weights=source_weights,
            freshness_half_life=freshness_half_life,
        )

    def process(
        self,
        results: list,
        query: str = "",
        skip_errors: bool = False,
    ) -> list:
        """Process search results through the pipeline.

        Args:
            results: List of search results.
            query: The original query.
            skip_errors: Whether to skip errors and continue processing.

        Returns:
            Processed list of results.
        """
        if not results:
            return []

        try:
            processed = results

            # Step 1: Deduplication
            if self.enable_deduplication:
                try:
                    processed = self.deduplicator.deduplicate(processed)
                except Exception:
                    if not skip_errors:
                        raise
                    # Continue with original results on error

            # Step 2: Ranking
            if self.enable_ranking:
                try:
                    if self.enable_temporal_boosting:
                        processed = self.ranker.rank_by_freshness(processed)
                    else:
                        processed = self.ranker.rank_by_relevance(processed)
                except Exception:
                    if not skip_errors:
                        raise
                    # Continue with unranked results on error

            return processed

        except Exception:
            if skip_errors:
                return results
            raise

    def process_with_synthesis(
        self,
        results: list,
        query: str = "",
        use_fetched_content: bool = False,
    ) -> dict[str, Any]:
        """Process results and generate synthesis.

        Args:
            results: List of search results.
            query: The original query.
            use_fetched_content: Whether to use fetched full content.

        Returns:
            Dictionary with processed results and synthesis.
        """
        if not results:
            return {"results": [], "synthesis": ""}

        processed = self.process(results, query)

        # Generate synthesis
        if use_fetched_content:
            synthesis = self.synthesizer.synthesize_with_fetched(processed, query)
        else:
            synthesis = self.synthesizer.combine_results(processed, query)

        return {
            "results": processed,
            "synthesis": synthesis,
        }

    def process_ensemble_result(
        self,
        ensemble_result: EnsembleResult,
        query: str = "",
    ) -> list:
        """Process results from ensemble fusion.

        Args:
            ensemble_result: EnsembleResult from ensemble fusion.
            query: The original query.

        Returns:
            Processed list of results.
        """
        if not ensemble_result or not ensemble_result.combined_results:
            return []

        return self.process(ensemble_result.combined_results, query)
