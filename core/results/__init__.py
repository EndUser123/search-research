"""Results processing subsystem for search-research.

Migrated from research_skill.processors (2025-03-08).

This module provides deduplication, ranking, synthesis, ensemble fusion,
and pipeline orchestration for search results.
"""

from .deduplication import DeduplicationProcessor
from .ensemble import (
    EnsembleResult,
    HybridEnsembleConfig,
    reciprocal_rank_fusion,
    run_hybrid_ensemble,
    weighted_average_fusion,
)
from .pipeline import ResultProcessingPipeline
from .ranking import RankingProcessor
from .reranking import (
    apply_temporal_boosting,
    calculate_temporal_boost,
    maximal_marginal_relevance,
)
from .synthesis import SynthesisProcessor

__all__ = [
    "HybridEnsembleConfig",
    "EnsembleResult",
    "reciprocal_rank_fusion",
    "weighted_average_fusion",
    "run_hybrid_ensemble",
    "maximal_marginal_relevance",
    "apply_temporal_boosting",
    "calculate_temporal_boost",
    "DeduplicationProcessor",
    "SynthesisProcessor",
    "RankingProcessor",
    "ResultProcessingPipeline",
]
