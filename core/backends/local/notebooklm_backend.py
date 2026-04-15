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

import asyncio
import json
import logging
import subprocess
from typing import Any

from ..query_intent import QueryIntent
from .base_local_backend import BaseLocalBackend

SearchResult = dict[str, Any]

logger = logging.getLogger(__name__)

BACKEND_NOTEBOOKLM = "notebooklm"

NLM_LIST_TIMEOUT = 10
NLM_QUERY_TIMEOUT = 60


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

    def _run_nlm_sync(self, args: list[str], timeout: int) -> str | None:
        """Run nlm CLI synchronously. Used by sync search()."""
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

    async def _run_nlm_async(self, args: list[str], timeout: int) -> str | None:
        """Run nlm CLI asynchronously. Used by search_async()."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "nlm", *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                logger.warning(f"nlm command timed out after {timeout}s")
                return None

            if proc.returncode != 0:
                logger.warning(f"nlm command failed: {stderr.decode() if stderr else ''}")
                return None
            return stdout.decode() if stdout else ""
        except FileNotFoundError:
            logger.warning("nlm CLI not found in PATH")
            return None
        except Exception as e:
            logger.warning(f"NotebookLM backend error: {e}")
            return None

    async def search_async(self, query: str, limit: int = 5) -> list["SearchResult"]:
        """Search NotebookLM notebooks asynchronously.

        Args:
            query: Search query
            limit: Maximum number of results (default 5)

        Returns:
            List of search results with title, content, url, source
        """
        # Determine which notebook to query
        notebook_id = self.notebook_id
        if not notebook_id:
            output = await self._run_nlm_async(
                ["notebook", "list", "--json"], timeout=NLM_LIST_TIMEOUT
            )
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
        output = await self._run_nlm_async(
            ["notebook", "query", notebook_id, query, "--json"],
            timeout=NLM_QUERY_TIMEOUT,
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

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Sync wrapper for backward compatibility."""
        return asyncio.get_event_loop().run_until_complete(
            self.search_async(query, limit)
        )

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
