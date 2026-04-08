"""HyDE (Hypothetical Document Embeddings) for Semantic Search.

Improves semantic search relevance by generating a hypothetical answer
to the query, then searching with both query + hypothetical embeddings.

Based on: "Precise Zero-Shot Dense Retrieval without Relevance Labels"
by Luyu Gao et al. (2022).

Key insight: Query embeddings don't capture the semantic space well.
A hypothetical "answer" to the query is closer in semantic space to
actual relevant documents.

Example:
    Query: "how to fix permission denied"
    Hypothetical: "To fix permission denied errors, you can use chmod to
    modify file permissions, check file ownership with ls -l, or run
    with sudo if needed."
    Search with: embed(query) + embed(hypothetical)

Minimal implementation - ~50 lines of code.

"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Simple in-memory cache for hypothetical documents
_HYDE_CACHE: dict[str, str] = {}
_HYDE_CACHE_MAX = 100


class HyDEQueryExpander:
    """HyDE query expansion using hypothetical document generation.

    Generates a hypothetical answer to the query and embeds both
    for improved semantic search relevance.

    Minimal implementation:
    - No external LLM calls (uses rule-based generation)
    - In-memory caching
    - < 100 lines of code
    """

    def __init__(self, enable_cache: bool = True) -> None:
        """Initialize HyDE expander.

        Args:
            enable_cache: Cache hypothetical documents (default: True)

        """
        self.enable_cache = enable_cache
        self._cache = _HYDE_CACHE

    def generate_hypothetical(self, query: str, query_type: str = "general") -> str:
        """Generate a hypothetical document for the query.

        Uses lightweight rule-based generation instead of LLM calls
        for minimal overhead and fast performance.

        Args:
            query: User's search query
            query_type: Detected query type (code, pattern, knowledge, general)

        Returns:
            Hypothetical answer text (2-3 sentences)

        """
        # Check cache first
        if self.enable_cache and query in self._cache:
            return self._cache[query]

        query.lower()

        # Rule-based hypothetical generation based on query patterns
        hypothetical = self._generate_by_rules(query, query_type)

        # Cache the result
        if self.enable_cache:
            # Simple cache eviction
            if len(self._cache) >= _HYDE_CACHE_MAX:
                self._cache.clear()
            self._cache[query] = hypothetical

        return hypothetical

    def _generate_by_rules(self, query: str, query_type: str) -> str:
        """Generate hypothetical document using pattern rules.

        This is a lightweight alternative to LLM generation.
        Works well for common technical queries.
        """
        query_lower = query.lower()

        # Code-related queries
        if query_type == "code" or any(
            w in query_lower for w in ["implement", "code", "function", "class", "api", "syntax"]
        ):
            if "error" in query_lower or "fix" in query_lower or "debug" in query_lower:
                return (
                    f"To resolve the error in {query}, check the stack trace for the "
                    f"specific line number, verify all dependencies are imported correctly, "
                    f"and ensure variable types match expected signatures. "
                    f"Common fixes include checking null values, validating input parameters, "
                    f"and reviewing recent code changes."
                )
            return (
                f"For implementing {query}, define the function with proper type hints, "
                f"add error handling for edge cases, include docstrings for documentation, "
                f"and write unit tests covering expected behavior and failure scenarios."
            )

        # Pattern/how-to queries
        if query_type == "pattern" or any(
            w in query_lower for w in ["how", "what", "pattern", "best practice", "approach"]
        ):
            if "how" in query_lower:
                return (
                    f"The approach to {query} involves breaking down the problem into smaller "
                    f"steps, identifying the key components, implementing each part incrementally, "
                    f"testing as you go, and refactoring for clarity. "
                    f"Common patterns include modular design, separation of concerns, and "
                    f"defensive programming."
                )
            return (
                f"The recommended pattern for {query} is to establish clear interfaces, "
                f"use consistent naming conventions, document assumptions and constraints, "
                f"handle errors gracefully, and maintain backward compatibility when possible."
            )

        # Knowledge/concept queries
        if query_type == "knowledge" or any(
            w in query_lower for w in ["explain", "concept", "understand", "learn", "difference"]
        ):
            return (
                f"The key concept behind {query} involves understanding the underlying "
                f"principles, how it relates to other components in the system, "
                f"common use cases and limitations, and practical considerations for "
                f"implementation. This concept is fundamental to building robust software."
            )

        # Permission/security queries (common in dev workflows)
        if any(w in query_lower for w in ["permission", "access", "denied", "auth", "security"]):
            return (
                "To fix permission or access issues, verify file ownership with ls -l, "
                "modify permissions using chmod or chown commands, check user group membership, "
                "review authentication credentials, and ensure proper access control lists "
                "are configured for the resource."
            )

        # Default: generate a generic but useful hypothetical
        return (
            f"For the query '{query}', the relevant information typically covers "
            f"the definition, implementation details, common use cases, potential "
            f"issues or edge cases, and best practices for working with this topic. "
            f"Documentation and examples are helpful for understanding practical applications."
        )

    def expand_query(self, query: str, query_type: str = "general") -> str:
        """Expand query with hypothetical document for better embedding.

        Args:
            query: Original user query
            query_type: Detected query type

        Returns:
            Combined text: query + hypothetical document

        """
        hypothetical = self.generate_hypothetical(query, query_type)
        return f"{query}\n\n{hypothetical}"

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._cache),
            "cache_enabled": self.enable_cache,
        }


def get_hypothetical_document(query: str, query_type: str = "general") -> str:
    """Convenience function to get hypothetical document for a query.

    Args:
        query: User's search query
        query_type: Query type (code, pattern, knowledge, general)

    Returns:
        Hypothetical answer text

    """
    expander = HyDEQueryExpander()
    return expander.generate_hypothetical(query, query_type)


__all__ = [
    "HyDEQueryExpander",
    "get_hypothetical_document",
]
