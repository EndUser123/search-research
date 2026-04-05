"""CKS Integration for /gto skill.

Stores discovered patterns in CKS for cross-session learning.
"""

import logging
from typing import Any

try:
    from knowledge.systems.chs.unified import CKS
    CKS_AVAILABLE = True
except ImportError:
    CKS_AVAILABLE = False
    CKS = None

logger = logging.getLogger(__name__)


class CKSIntegrator:
    """Store and retrieve gap patterns in CKS."""

    def __init__(self) -> None:
        """Initialize CKS integrator."""
        if not CKS_AVAILABLE:
            logger.warning("CKS not available - pattern storage disabled")
            self.cks = None
        else:
            try:
                self.cks = CKS()
                logger.info("CKS integrator initialized")
            except Exception as e:
                logger.warning(f"CKS initialization failed: {e}")
                self.cks = None

    def store_pattern(self, pattern: str, category: str, metadata: dict[str, Any]) -> bool:
        """Store a discovered pattern in CKS.

        Args:
            pattern: The pattern description (e.g., "TODO in auth.py line 45")
            category: Pattern category (e.g., "todo", "unfinished", "test_gap")
            metadata: Additional context (file path, line number, etc.)

        Returns:
            True if stored successfully, False otherwise
        """
        if self.cks is None:
            logger.debug("CKS not available - skipping pattern storage")
            return False

        try:
            # Build memory entry
            memory_content = f"Pattern: {pattern}\nCategory: {category}"
            if metadata:
                memory_content += f"\nMetadata: {metadata}"

            # Store using CKS ingest_memory
            self.cks.ingest_memory(
                content=memory_content,
                tags=["gto", "gap-pattern", category],
                metadata=metadata or {}
            )

            logger.info(f"Stored pattern in CKS: {category} - {pattern}")
            return True

        except Exception as e:
            logger.warning(f"Failed to store pattern in CKS: {e}")
            return False

    def store_session_gaps(self, session_report: dict[str, Any]) -> int:
        """Store all gaps from a session analysis.

        Args:
            session_report: Session analysis report from SessionAnalyzer

        Returns:
            Number of patterns successfully stored
        """
        stored_count = 0

        # Store TODOs
        for todo in session_report.get("todos", []):
            if self.store_pattern(todo, "todo", {"source": "session_analysis"}):
                stored_count += 1

        # Store unfinished work
        for task in session_report.get("unfinished_work", []):
            if self.store_pattern(task, "unfinished", {"source": "session_analysis"}):
                stored_count += 1

        logger.info(f"Stored {stored_count} patterns from session analysis")
        return stored_count

    def search_similar_patterns(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search for similar patterns in CKS.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of matching patterns with metadata
        """
        if self.cks is None:
            logger.debug("CKS not available - skipping pattern search")
            return []

        try:
            results = self.cks.search(query, limit=limit)
            return results
        except Exception as e:
            logger.warning(f"Failed to search CKS: {e}")
            return []
