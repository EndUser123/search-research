"""HyDE Engine for query enhancement."""

from typing import Any
import functools
import asyncio


class HyDEResearchEngine:
    """Mock HyDEResearchEngine for testing."""

    def enhance_query(self, query: str, mode: str = "confidence") -> dict[str, Any]:
        """Mock enhance query method."""
        return {
            "vector": [0.1, 0.2, 0.3],
            "mode": mode,
            "confidence_score": 0.85,
            "processing_time": 0.5,
            "hypothetical_document": "Test hypothetical document"
        }


class HyDEEngine:
    """HyDE Engine for query enhancement.

    Attributes:
        mode: The HyDE mode to use (confidence, multi-gen, rejection-aware).
    """

    _AVAILABLE_MODES = ["confidence", "multi-gen", "rejection-aware"]

    def __init__(self, mode: str = "confidence"):
        """Initialize HyDEEngine with the specified mode.

        Args:
            mode: The HyDE mode to use.

        Raises:
            ValueError: If mode is not valid.
        """
        if mode not in self._AVAILABLE_MODES:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {self._AVAILABLE_MODES}")
        self.mode = mode

    def get_available_modes(self) -> list[str]:
        """Get list of available HyDE modes.

        Returns:
            List of available mode names.
        """
        return self._AVAILABLE_MODES.copy()

    @functools.lru_cache(maxsize=128)
    def _sync_enhance_query_logic(self, query: str, mode: str) -> dict[str, Any]:
        """Synchronous part of enhance_query, decorated for caching."""
        hyde_engine = HyDEResearchEngine()
        return hyde_engine.enhance_query(query, mode)

    async def enhance_query(self, query: str) -> "EnhancedQuery":
        """Enhance a query using HyDE.

        Args:
            query: The original query string.

        Returns:
            EnhancedQuery: Enhanced query object containing the hypothetical
                document, vector representation, and confidence score.

        Raises:
            Exception: If the underlying HyDE engine raises an error.
        """
        from research_skill.models import EnhancedQuery

        # Run the cached synchronous logic in a separate thread
        result = await asyncio.to_thread(self._sync_enhance_query_logic, query, self.mode)

        return EnhancedQuery(
            original=query,
            enhanced=query,
            hypothetical_document=result.get("hypothetical_document", ""),
            vector=result.get("vector", []),
            confidence=result.get("confidence_score", 0.0),
        )
