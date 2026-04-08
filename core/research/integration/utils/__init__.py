"""
Knowledge Integration Utilities

Contains utility functions, factory functions, and advanced components
for the knowledge integration system.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..core import KnowledgeIntegrationEngine
from ..models import (
    ImplementationResult,
)

logger = logging.getLogger(__name__)


def create_knowledge_integration_engine(
    helpful_engine=None,
    knowledge_query_engine=None,
    storage_path: str | None = None,
) -> KnowledgeIntegrationEngine:
    """
    Create a knowledge integration engine with optional integrations.

    Parameters
    ----------
    helpful_engine (HelpfulnessPattern, optional): Helpfulness engine integration
    knowledge_query_engine (KnowledgeQueryEngine, optional): CSF knowledge engine
    storage_path (str, optional): Custom storage path

    Returns
    -------
    KnowledgeIntegrationEngine: Configured integration engine

    """
    return KnowledgeIntegrationEngine(
        helpful_engine=helpful_engine,
        knowledge_query_engine=knowledge_query_engine,
        storage_path=storage_path,
    )


def ingest_implementation_results(
    engine: KnowledgeIntegrationEngine,
    implementation_results: ImplementationResult | list[ImplementationResult],
) -> dict[str, any]:
    """
    Convenience function for ingesting implementation results.

    Parameters
    ----------
    engine (KnowledgeIntegrationEngine): Integration engine instance
    implementation_results (Union[ImplementationResult, List[ImplementationResult]]):
        Implementation results to ingest

    Returns
    -------
    Dict[str, Any]: Ingestion results

    """
    return engine.automatic_knowledge_ingestion(implementation_results)


def get_recommendations_for_context(
    engine: KnowledgeIntegrationEngine,
    context: str,
    confidence_threshold: float = 0.5,
    limit: int = 10,
) -> dict[str, any]:
    """
    Convenience function for getting context-specific recommendations.

    Parameters
    ----------
    engine (KnowledgeIntegrationEngine): Integration engine instance
    context (str): Context for recommendations
    confidence_threshold (float): Minimum confidence threshold
    limit (int): Maximum number of recommendations

    Returns
    -------
    Dict[str, Any]: Evidence-based recommendations

    """
    return engine.evidence_based_recommendations(context, confidence_threshold, limit)
