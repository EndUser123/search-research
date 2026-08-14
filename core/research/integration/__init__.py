"""
Knowledge Integration Engine

A comprehensive knowledge integration system for pattern discovery,
evidence-based recommendations, and cross-implementation learning.

This modular system provides:
- Advanced pattern matching algorithms (statistical and semantic)
- Real-time knowledge ingestion and learning
- Evidence-based recommendation generation
- Cross-implementation pattern discovery
- Future implementation enabling through adaptive strategies

Architecture:
- Models: Data structures and enums
- Strategies: Pattern matching algorithms
- Core: Main integration engine
- Utils: Utility functions and factory methods
"""

from __future__ import annotations

from .core import KnowledgeIntegrationEngine
from .models import (
    AdaptationStrategy,
    ApproachPrediction,
    ConfidenceLevel,
    EvidenceBasedRecommendation,
    ImplementationResult,
    ImplementationRoadmap,
    IntegrationStatus,
    KnowledgeIntegrationError,
    KnowledgePattern,
    KnowledgeQuery,
    PatternType,
    QueryResult,
    ReusablePattern,
    SessionContext,
)
from .strategies import (
    PatternMatchingStrategy,
    SemanticPatternMatcher,
    StatisticalPatternMatcher,
)
from .utils import (
    create_knowledge_integration_engine,
    get_recommendations_for_context,
    ingest_implementation_results,
)

__version__ = "1.0.0"
__author__ = "CSF Team"

# Export main components
__all__ = [
    # Core classes
    "KnowledgeIntegrationEngine",
    "KnowledgeIntegrationError",
    # Pattern matching
    "PatternMatchingStrategy",
    "StatisticalPatternMatcher",
    "SemanticPatternMatcher",
    # Data models
    "ImplementationResult",
    "KnowledgePattern",
    "EvidenceBasedRecommendation",
    "KnowledgeQuery",
    "ReusablePattern",
    "ImplementationRoadmap",
    "ApproachPrediction",
    "AdaptationStrategy",
    # Enums and constants
    "IntegrationStatus",
    "PatternType",
    "ConfidenceLevel",
    # Utility classes
    "QueryResult",
    "SessionContext",
    # Factory functions
    "create_knowledge_integration_engine",
    "ingest_implementation_results",
    "get_recommendations_for_context",
]
