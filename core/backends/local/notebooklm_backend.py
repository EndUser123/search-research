"""NotebookLM Search Backend - MCP-based long-form research synthesis.

This backend provides semantic search over NotebookLM notebooks using
the notebooklm-mcp CLI for authenticated queries.
"""

from __future__ import annotations

import logging
from typing import Any

from ..query_intent import QueryIntent
from .base_local_backend import BaseLocalBackend

SearchResult = dict[str, Any]

logger = logging.getLogger(__name__)

BACKEND_NOTEBOOKLM = "notebooklm"


class NotebookLMBackend(BaseLocalBackend):
    """Search backend for NotebookLM notebooks.

    Uses the notebooklm-mcp CLI for long-form research synthesis
    with citation-backed answers from curated notebooks.
    """

    name = BACKEND_NOTEBOOKLM
    description = "Long-form research synthesis from NotebookLM notebooks"
    source_types = ["notebook", "research"]

    def __init__(
        self,
        root_paths: list[str] | None = None,
        exclude_patterns: set[str] | None = None,
        notebook_id: str | None = None,
    ):
        """Initialize the NotebookLM backend.

        Args:
            root_paths: Not used (kept for BaseLocalBackend compatibility)
            exclude_patterns: Not used (kept for BaseLocalBackend compatibility)
            notebook_id: Optional specific notebook ID to query
        """
        super().__init__(root_paths, exclude_patterns)
        self.notebook_id = notebook_id

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Search NotebookLM notebooks for the query.

        Args:
            query: Search query
            limit: Maximum number of results (default 5)

        Returns:
            List of search results with title, content, url, source
        """
        try:
            from mcp__notebooklm_mcp__notebook_list import notebook_list
            from mcp__notebooklm_mcp__notebook_query import notebook_query

            notebook_id = self.notebook_id
            if not notebook_id:
                notebooks = notebook_list()
                if notebooks.get("notebooks"):
                    notebook_id = notebooks["notebooks"][0].get("id")
                else:
                    logger.warning("No NotebookLM notebooks found")
                    return []

            if not notebook_id:
                return []

            result = notebook_query(query, notebook_id=notebook_id, max_results=limit)

            return [
                {
                    "title": "NotebookLM Result",
                    "content": result,
                    "url": "",
                    "source": "notebooklm",
                }
            ]
        except Exception as e:
            logger.debug(f"NotebookLM backend error: {e}")
            return []

    def supports_intent(self, intent: QueryIntent) -> bool:
        """NotebookLM supports knowledge queries for deep research."""
        return intent == QueryIntent.KNOWLEDGE


def create_notebooklm_backend(
    notebook_id: str | None = None,
) -> NotebookLMBackend:
    """Factory function to create NotebookLM backend.

    Args:
        notebook_id: Optional specific notebook ID to query

    Returns:
        NotebookLMBackend instance
    """
    return NotebookLMBackend(notebook_id=notebook_id)
