"""Research-Flash - Multi-Source Knowledge Research."""

from .query_engine import QueryResult, ResearchFlashEngine, ResearchResult

# Alias for test compatibility
QueryEngine = ResearchFlashEngine

__all__ = [
    "QueryEngine",
    "QueryResult",
    "ResearchFlashEngine",
    "ResearchResult",
]
