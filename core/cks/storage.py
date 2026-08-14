"""Unified storage interface for knowledge systems.

This module provides abstract base classes for CKS/CHS storage backends,
enabling polymorphic access across different storage implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass
class StorageConfig:
    """Base configuration for storage backends."""

    path: str
    read_only: bool = False
    cache_size_mb: int = 100


class KnowledgeStorage(ABC):
    """Abstract base class for knowledge storage implementations.

    All storage backends (CKS, CHS, vector stores) must implement this interface
    to ensure consistent behavior across the knowledge ecosystem.
    """

    def __init__(self, config: StorageConfig) -> None:
        """Initialize storage with configuration."""
        self.config = config
        self._initialized = False

    @abstractmethod
    def store(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> bool:
        """Store a key-value pair with optional metadata.

        Args:
            key: Unique identifier for the value
            value: Data to store
            metadata: Optional metadata dictionary

        Returns:
            True if store succeeded, False otherwise

        """
        ...

    @abstractmethod
    def retrieve(self, key: str) -> Any | None:
        """Retrieve a value by key.

        Args:
            key: Unique identifier to retrieve

        Returns:
            Stored value or None if not found

        """
        ...

    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> Iterable[dict[str, Any]]:
        """Search stored items by query string.

        Args:
            query: Search query string
            limit: Maximum results to return
            filters: Optional filter criteria

        Yields:
            Dictionaries containing matched items

        """
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a stored item by key.

        Args:
            key: Unique identifier to delete

        Returns:
            True if deletion succeeded, False otherwise

        """
        ...

    def initialize(self) -> None:
        """Initialize storage backend (called once before first use)."""
        if not self._initialized:
            self._initialize_impl()
            self._initialized = True

    def _initialize_impl(self) -> None:
        """Implementation-specific initialization (override in subclasses)."""

    def close(self) -> None:
        """Close storage backend and release resources."""
        if self._initialized:
            self._close_impl()
            self._initialized = False

    def _close_impl(self) -> None:
        """Implementation-specific cleanup (override in subclasses)."""

    def __enter__(self) -> KnowledgeStorage:
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.close()


class VectorStorage(KnowledgeStorage):
    """Abstract base class for vector storage implementations.

    Extends KnowledgeStorage with vector-specific operations like
    similarity search and batch operations.
    """

    @abstractmethod
    def store_vector(
        self,
        key: str,
        vector: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Store a vector embedding with optional metadata.

        Args:
            key: Unique identifier for the vector
            vector: Floating-point embedding vector
            metadata: Optional metadata dictionary

        Returns:
            True if store succeeded, False otherwise

        """
        ...

    @abstractmethod
    def similarity_search(
        self,
        query_vector: list[float],
        limit: int = 10,
        threshold: float = 0.0,
    ) -> Iterable[tuple[str, float, dict[str, Any] | None]]:
        """Find similar vectors by cosine similarity.

        Args:
            query_vector: Query embedding vector
            limit: Maximum results to return
            threshold: Minimum similarity score (0-1)

        Yields:
            Tuples of (key, score, metadata) for matches above threshold

        """
        ...

    @abstractmethod
    def batch_store(
        self,
        items: Iterable[tuple[str, list[float], dict[str, Any] | None]],
    ) -> int:
        """Store multiple vectors efficiently in batch.

        Args:
            items: Iterable of (key, vector, metadata) tuples

        Returns:
            Number of vectors successfully stored

        """
        ...
