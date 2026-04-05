"""Ensemble and reranking processors for research results."""

from .ensemble import (
    HybridEnsembleConfig,
    EnsembleResult,
    reciprocal_rank_fusion,
    weighted_average_fusion,
    run_hybrid_ensemble,
)

from .reranking import (
    maximal_marginal_relevance,
    apply_temporal_boosting,
    calculate_temporal_boost,
)

from .deduplication import DeduplicationProcessor
from .synthesis import SynthesisProcessor
from .ranking import RankingProcessor
from .pipeline import ResultProcessingPipeline

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
