"""NotebookLM Search Backend - CLI-based long-form research synthesis.

This backend provides semantic search over NotebookLM notebooks using
the nlm CLI (not MCP) for authenticated queries.

CLI approach is preferred over MCP because:
- No server process needed
- Full feature parity
- Better error messages
- No module import failures
"""

from __future__ import annotations

import json
import logging
import subprocess
from typing import Any

from ..query_intent import QueryIntent
from .base_local_backend import BaseLocalBackend

SearchResult = dict[str, Any]

logger = logging.getLogger(__name__)

BACKEND_NOTEBOOKLM = "notebooklm"

NLM_TIMEOUT = 30  # seconds per nlm operation


class NotebookLMBackend(BaseLocalBackend):
    """Search backend for NotebookLM notebooks.

    Uses the nlm CLI for long-form research synthesis
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

    def _run_nlm(self, args: list[str], timeout: int = NLM_TIMEOUT) -> str | None:
        """Run nlm CLI and return stdout, or None on failure."""
        try:
            result = subprocess.run(
                ["nlm"] + args,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode != 0:
                logger.warning(f"nlm command failed: {result.stderr}")
                return None
            return result.stdout
        except FileNotFoundError:
            logger.warning("nlm CLI not found in PATH")
            return None
        except subprocess.TimeoutExpired:
            logger.warning(f"nlm command timed out after {timeout}s")
            return None
        except Exception as e:
            logger.warning(f"NotebookLM backend error: {e}")
            return None

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Search NotebookLM notebooks for the query.

        Args:
            query: Search query
            limit: Maximum number of results (default 5)

        Returns:
            List of search results with title, content, url, source
        """
        # Determine which notebook to query
        notebook_id = self.notebook_id
        if not notebook_id:
            # List notebooks and use the first one
            output = self._run_nlm(["notebook", "list", "--json"])
            if not output:
                return []
            try:
                notebooks = json.loads(output)
                if not isinstance(notebooks, list) or not notebooks:
                    logger.warning("No NotebookLM notebooks found")
                    return []
                notebook_id = notebooks[0].get("id")
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                logger.warning(f"Failed to parse notebook list: {e}")
                return []

        if not notebook_id:
            return []

        # Query the notebook
        output = self._run_nlm(
            ["notebook", "query", notebook_id, query, "--json"],
            timeout=NLM_TIMEOUT * 2,  # Query can be slower
        )
        if not output:
            return []

        try:
            data = json.loads(output)
            # nlm notebook query returns {"value": {"answer": "...", "sources": [...]}}
            if isinstance(data, dict) and "value" in data:
                data = data["value"]
            answer = data.get("answer", "") if isinstance(data, dict) else str(data)
            return [
                {
                    "title": "NotebookLM Result",
                    "content": answer,
                    "url": "",
                    "source": "notebooklm",
                }
            ]
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse notebook query response: {e}")
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
