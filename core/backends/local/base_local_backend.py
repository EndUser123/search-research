"""Base Local Backend - Shared functionality for local search backends.

Provides common exclude patterns and utility methods for AST-based code search
backends (CDSBackend, GrepBackend, etc.).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ...config import config

logger = logging.getLogger(__name__)

SearchResult = dict[str, Any]


class BaseLocalBackend:
    """Base class for local search backends with shared functionality."""

    # Default exclude patterns to prevent memory exhaustion
    DEFAULT_EXCLUDE_PATTERNS = {
        "_archive",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "venv",
        ".venv",
        "node_modules",
        ".git",
        "dist",
        "build",
        "*.egg-info",
    }

    def __init__(
        self,
        root_paths: list[str] | None = None,
        exclude_patterns: set[str] | None = None,
    ) -> None:
        """Initialize with root paths to search.

        Args:
            root_paths: List of root directories to index
            exclude_patterns: Additional patterns to exclude
        """
        self.root_paths = [Path(p) for p in (root_paths or config.SOURCE_ROOTS)]
        # Validate root_paths exist before use (IO-002)
        self.root_paths = [p for p in self.root_paths if p.exists()]
        if not self.root_paths:
            logger.warning("No valid root_paths found — all paths are missing or inaccessible")
        self.exclude_patterns = self.DEFAULT_EXCLUDE_PATTERNS | (exclude_patterns or set())
        self._index: dict[str, list[SearchResult]] = {}
        self._indexed = False

    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded from indexing.

        Args:
            path: Path to check

        Returns:
            True if path should be excluded, False otherwise
        """
        for part in path.parts:
            if part in self.exclude_patterns:
                return True
            for pattern in self.exclude_patterns:
                if pattern.startswith("*") and part.endswith(pattern[1:]):
                    return True
        return False

    def build_index(self) -> None:
        """Build AST index of functions, classes, and methods.

        This is a template method that should be overridden by subclasses
        to implement specific indexing strategies.
        """
        raise NotImplementedError("Subclasses must implement build_index()")
