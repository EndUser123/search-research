"""Ranking processor for scoring and sorting search results."""

from datetime import datetime, timezone
import math


# Seconds per day for age calculations
_SECONDS_PER_DAY = 86400


class RankingProcessor:
    """Processor for ranking search results.

    Ranks by relevance, source quality, and temporal freshness.
    """

    def __init__(
        self,
        source_weights: dict[str, float] | None = None,
        freshness_half_life: int = 180,
    ):
        """Initialize the ranking processor.

        Args:
            source_weights: Weight multipliers for different sources.
            freshness_half_life: Half-life in days for temporal decay.
        """
        self.source_weights = source_weights or {}
        self.freshness_half_life = freshness_half_life

    def rank_by_relevance(
        self,
        results: list,
        limit: int | None = None,
    ) -> list:
        """Rank results by relevance score.

        Args:
            results: List of search results.
            limit: Maximum number of results to return.

        Returns:
            Results sorted by relevance score (descending).
        """
        if not results:
            return []

        # Sort by score descending
        ranked = sorted(results, key=lambda x: x.score or 0, reverse=True)

        if limit is not None:
            ranked = ranked[:limit]

        return ranked

    def rank_by_source_quality(self, results: list) -> list:
        """Rank results by source quality weights.

        Adjusts scores based on source quality weights and re-sorts.

        Args:
            results: List of search results.

        Returns:
            Results ranked by quality-adjusted score.
        """
        if not results:
            return []

        # Calculate quality-adjusted scores
        adjusted = []
        for result in results:
            weight = self.source_weights.get(result.source, 1.0)
            adjusted_score = result.score * weight

            # Create a copy to avoid modifying original
            adjusted_result = result
            if not hasattr(result, '_metadata_adjusted'):
                adjusted_result.metadata = result.metadata.copy()
            adjusted_result.metadata["quality_adjusted_score"] = adjusted_score
            adjusted_result.metadata["source_weight"] = weight

            adjusted.append(adjusted_result)

        # Sort by adjusted score
        adjusted.sort(key=lambda x: x.metadata.get("quality_adjusted_score", x.score), reverse=True)

        return adjusted

    def rank_by_freshness(
        self,
        results: list,
        limit: int | None = None,
    ) -> list:
        """Rank results by temporal freshness.

        Boosts recent results using exponential decay.

        Args:
            results: List of search results.
            limit: Maximum number of results to return.

        Returns:
            Results ranked by freshness-boosted score.
        """
        if not results:
            return []

        now = datetime.now(timezone.utc)

        boosted = []
        for result in results:
            base_score = result.score

            # Get published date
            published_date = result.metadata.get("published_date", "")
            boost = 1.0

            if published_date:
                try:
                    if isinstance(published_date, str):
                        pub_dt = datetime.fromisoformat(
                            published_date.replace('Z', '+00:00')
                        )
                    else:
                        pub_dt = published_date

                    # Calculate age in days
                    age = (now - pub_dt).total_seconds() / _SECONDS_PER_DAY

                    # Calculate boost using half-life decay
                    # Recent content gets boost > 1, older gets boost close to 0.5
                    decay = math.pow(0.5, age / self.freshness_half_life)
                    # Base boost from decay (0.5 to 1.5)
                    # Recent content (age=0): boost = 1.5
                    # Old content: boost approaches 0.5
                    boost = 0.5 + 1.0 * decay  # Range: 0.5 to 1.5

                except (ValueError, AttributeError):
                    boost = 1.0

            boosted_score = base_score * boost

            # Store boosted score
            if not hasattr(result, '_metadata_boosted'):
                result.metadata = result.metadata.copy()
            result.metadata["freshness_boost"] = boost
            result.metadata["boosted_score"] = boosted_score
            result._temp_score = boosted_score  # Temporary attribute for sorting

            boosted.append(result)

        # Sort by boosted score
        boosted.sort(key=lambda x: getattr(x, '_temp_score', x.score), reverse=True)

        # Clean up temporary attributes
        for r in boosted:
            if hasattr(r, '_temp_score'):
                delattr(r, '_temp_score')

        if limit is not None:
            boosted = boosted[:limit]

        return boosted

    def rank_combined(
        self,
        results: list,
        weights: dict[str, float] | None = None,
        limit: int | None = None,
    ) -> list:
        """Rank using combined scoring factors.

        Combines relevance, quality, and freshness into a single score.

        Args:
            results: List of search results.
            weights: Weights for each factor (relevance, quality, freshness).
            limit: Maximum number of results to return.

        Returns:
            Results ranked by combined score.
        """
        if not results:
            return []

        if weights is None:
            weights = {"relevance": 0.5, "quality": 0.3, "freshness": 0.2}

        now = datetime.now(timezone.utc)

        scored = []
        for result in results:
            # Relevance component
            relevance = result.score

            # Quality component
            source_weight = self.source_weights.get(result.source, 1.0)
            quality = relevance * source_weight

            # Freshness component
            published_date = result.metadata.get("published_date", "")
            freshness = relevance
            freshness_boost = 1.0

            if published_date:
                try:
                    if isinstance(published_date, str):
                        pub_dt = datetime.fromisoformat(
                            published_date.replace('Z', '+00:00')
                        )
                    else:
                        pub_dt = published_date

                    age = (now - pub_dt).total_seconds() / _SECONDS_PER_DAY
                    decay = math.pow(0.5, age / self.freshness_half_life)
                    freshness_boost = 1.0 + (0.5 * (1.0 - decay))
                    freshness = relevance * freshness_boost

                except (ValueError, AttributeError):
                    freshness_boost = 1.0

            # Combined score
            combined = (
                weights.get("relevance", 0.5) * relevance +
                weights.get("quality", 0.3) * quality +
                weights.get("freshness", 0.2) * freshness
            ) / sum(weights.values())

            # Store scores in metadata
            if not hasattr(result, '_metadata_combined'):
                result.metadata = result.metadata.copy()
            result.metadata["combined_score"] = combined
            result.metadata["freshness_boost"] = freshness_boost
            result.metadata["source_weight"] = source_weight
            result._temp_combined = combined

            scored.append(result)

        # Sort by combined score
        scored.sort(key=lambda x: getattr(x, '_temp_combined', x.score), reverse=True)

        # Clean up
        for r in scored:
            if hasattr(r, '_temp_combined'):
                delattr(r, '_temp_combined')

        if limit is not None:
            scored = scored[:limit]

        return scored
