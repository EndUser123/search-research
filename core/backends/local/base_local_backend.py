"""Base Local Backend - Shared functionality for local search backends.

Provides common exclude patterns and utility methods for AST-based code search
backends (CDSBackend, GrepBackend, etc.).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...config import config

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

    def _sanitize_query(self, query: str, max_length: int = 500) -> str:
        """Strip non-printable characters and limit query length.

        Args:
            query: Raw query string
            max_length: Maximum allowed length

        Returns:
            Sanitized query safe for subprocess calls
        """
        return "".join(c for c in query if c.isprintable())[:max_length]

    def build_index(self) -> None:
        """Build AST index of functions, classes, and methods.

        This is a template method that should be overridden by subclasses
        to implement specific indexing strategies.
        """
        raise NotImplementedError("Subclasses must implement build_index()")
