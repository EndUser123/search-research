"""LLM context management.

This module provides context management for LLM calls including query tracking
and result ID management.
"""

from typing import Any


class LLMContext:
    """Manages context for LLM calls."""

    def __init__(self, query: str, result_ids: list[str]) -> None:
        """Initialize LLM context.

        Args:
            query: The search query or prompt
            result_ids: List of search result IDs being considered
        """
        self.query = query
        self.result_ids = result_ids
        self.metadata: dict[str, Any] = {}

    def get_query(self) -> str:
        """Get the query.

        Returns:
            Query string
        """
        return self.query

    def get_result_ids(self) -> list[str]:
        """Get the result IDs.

        Returns:
            List of result IDs
        """
        return self.result_ids

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata key-value pair.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)


def create_llm_context(query: str, result_ids: list[str]) -> LLMContext:
    """Create an LLM context.

    Args:
        query: The search query
        result_ids: List of search result IDs

    Returns:
        LLMContext instance
    """
    return LLMContext(query, result_ids)
