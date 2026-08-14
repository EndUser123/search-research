"""Search research data models.

Merged from research_skill/models.py
CANONICAL SearchResult - all other SearchResult definitions should import from here.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SearchResult:
    """Canonical search result from any backend.

    This is the unified dataclass for all search results across the codebase.
    It supports both web results (with URL) and local results (with file_path).

    Attributes:
        title: Result title or name
        content: Result content/snippet
        source: Backend name that produced this result (e.g., "CDS", "Tavily", "Grep")
        score: Relevance score (0.0 to 1.0)
        url: Source URL for web results (optional)
        file_path: File path for local/code results (optional)
        line_number: Line number for code results (optional)
        backend: Alternative name for source (for ensemble compatibility)
        fetched: Whether full URL content was fetched (web results)
        fetch_time: Time taken to fetch URL content in seconds
        created_at: When result was generated
        cached: Whether result came from cache
        metadata: Additional backend-specific metadata
    """

    # Required fields
    title: str
    content: str
    source: str
    score: float

    # Optional source location (one of these usually set)
    url: str | None = None
    file_path: str | None = None
    line_number: int | None = None

    # Alternative naming for ensemble compatibility
    backend: str | None = None

    # Optional metadata
    fetched: bool = False
    fetch_time: float | None = None
    created_at: datetime | None = None
    cached: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure source and backend are synchronized."""
        if self.backend is None:
            self.backend = self.source
        elif self.source != self.backend:
            # backend was explicitly set, use it for source too
            pass  # Keep both if different

    @property
    def id(self) -> str:
        """Get unique identifier for the result.

        Returns:
            URL, file_path, or a hash of title+content as fallback
        """
        if self.url:
            return self.url
        if self.file_path:
            return f"{self.file_path}:{self.line_number or 0}"
        # Use hashlib for deterministic hashing across sessions
        title_hash = hashlib.md5(self.title.encode()).hexdigest()[:8]
        content_hash = hashlib.md5(self.content[:50].encode()).hexdigest()[:8]
        return f"{title_hash}:{content_hash}"

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary representation.

        Returns:
            Dictionary containing all result fields
        """
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "backend": self.backend,
            "score": self.score,
            "url": self.url,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "fetched": self.fetched,
            "fetch_time": self.fetch_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "cached": self.cached,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SearchResult:
        """Reconstruct SearchResult from dictionary (e.g., from cache).

        Args:
            data: Dictionary containing result fields

        Returns:
            SearchResult instance
        """
        # Parse created_at from isoformat string if present
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        # Filter to only valid dataclass fields (exclude computed 'id' property)
        valid_fields = {
            "title", "content", "source", "score", "url", "file_path",
            "line_number", "backend", "fetched", "fetch_time", "created_at",
            "cached", "metadata"
        }
        kwargs = {k: v for k, v in data.items() if k in valid_fields}
        if created_at is not None:
            kwargs["created_at"] = created_at

        return cls(**kwargs)

    @classmethod
    def from_web_result(
        cls,
        *,
        url: str,
        title: str,
        content: str,
        source: str,
        score: float,
        fetched: bool = False,
        fetch_time: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SearchResult:
        """Create SearchResult from web backend response."""
        return cls(
            title=title,
            content=content,
            source=source,
            score=score,
            url=url,
            fetched=fetched,
            fetch_time=fetch_time,
            metadata=metadata or {},
        )

    @classmethod
    def from_local_result(
        cls,
        *,
        file_path: str,
        title: str,
        content: str,
        source: str,
        score: float,
        line_number: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SearchResult:
        """Create SearchResult from local/code backend."""
        return cls(
            title=title,
            content=content,
            source=source,
            score=score,
            file_path=file_path,
            line_number=line_number,
            metadata=metadata or {},
        )


@dataclass
class ResearchResult:
    """Result from research orchestration.

    Attributes:
        query: The original query string.
        enhanced_query: The enhanced query after processing.
        expanded_queries: List of queries expanded from the original.
        results: List of search results found.
        sources_used: List of source names/backends used.
        fetched_urls: Number of URLs successfully fetched.
        vision_analysis: Vision analysis results.
        synthesis: Synthesized summary of findings.
        processing_time: Total processing time in seconds.
        hyde_enabled: Whether HyDE was enabled.
        hyde_mode: The HyDE mode used.
        multi_hyde_enabled: Whether multi-HyDE was enabled.
        chapters_enabled: Whether chapters generation was enabled.
        ensemble_enabled: Whether ensemble methods were enabled.
        ensemble_method: The ensemble method used.
        metadata: Additional metadata about the research.
    """

    query: str
    enhanced_query: str | None
    expanded_queries: list[str]
    results: list[SearchResult]
    sources_used: list[str]
    fetched_urls: int
    vision_analysis: list[dict[str, Any]]
    synthesis: str
    processing_time: float
    hyde_enabled: bool
    hyde_mode: str | None
    multi_hyde_enabled: bool
    chapters_enabled: bool
    ensemble_enabled: bool
    ensemble_method: str | None
    metadata: dict[str, Any]


@dataclass
class EnhancedQuery:
    """Enhanced query with HyDE.

    Attributes:
        original: The original query string.
        enhanced: The enhanced query string.
        hypothetical_document: The generated hypothetical document.
        vector: The vector representation of the query.
        confidence: The confidence score of the enhancement.
    """

    original: str
    enhanced: str
    hypothetical_document: str
    vector: list[float]
    confidence: float
