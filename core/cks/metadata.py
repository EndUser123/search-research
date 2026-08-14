"""Metadata and citation types for knowledge systems.

This module provides dataclasses and types for tracking citations,
file metadata, and categorization across the knowledge ecosystem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Iterable


class Category(str, Enum):
    """Knowledge content categories for classification and filtering.

    Categories align with CSF knowledge domains and enable
    targeted retrieval and analysis.
    """

    CODE = "code"  # Code snippets, functions, classes
    DOCUMENTATION = "documentation"  # Docs, README, guides
    ARCHITECTURE = "architecture"  # Design patterns, system design
    RESEARCH = "research"  # Research findings, analysis
    SKILL = "skill"  # Skill definitions, commands
    SESSION = "session"  # Chat session transcripts
    CONFIGURATION = "configuration"  # Config files, settings
    TESTING = "testing"  # Tests, test results
    DEPLOYMENT = "deployment"  # Deployment scripts, CI/CD
    MONITORING = "monitoring"  # Observability, health checks
    MEMORY = "memory"  # Learned patterns, lessons
    UNKNOWN = "unknown"  # Uncategorized content


@dataclass(frozen=True)
class Citation:
    """Immutable reference to a source location in the codebase.

    Citations provide precise source attribution for knowledge items,
    enabling traceability and verification.

    Attributes:
        file_path: Absolute path to the source file
        line_number: Line number where the content originates (1-indexed)
        end_line_number: Optional end line for multi-line citations
        char_offset: Optional character offset within the line
        skill_source: Name of skill that created this citation (optional)
        timestamp: When this citation was created

    """

    file_path: str
    line_number: int
    end_line_number: int | None = None
    char_offset: int | None = None
    skill_source: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate citation fields."""
        if self.line_number < 1:
            msg = f"line_number must be >= 1, got {self.line_number}"
            raise ValueError(msg)
        if self.end_line_number is not None and self.end_line_number < self.line_number:
            msg = (
                f"end_line_number ({self.end_line_number}) must be >= "
                f"line_number ({self.line_number})"
            )
            raise ValueError(msg)
        if self.char_offset is not None and self.char_offset < 0:
            msg = f"char_offset must be >= 0, got {self.char_offset}"
            raise ValueError(msg)

    @property
    def is_multiline(self) -> bool:
        """Check if citation spans multiple lines."""
        return self.end_line_number is not None and self.end_line_number > self.line_number

    @property
    def line_range(self) -> range:
        """Get line range as Python range object."""
        end = (self.end_line_number or self.line_number) + 1
        return range(self.line_number, end)

    def format_location(self, style: Literal["short", "full", "url"] = "short") -> str:
        """Format citation as string.

        Args:
            style: Format style ('short', 'full', or 'url')

        Returns:
            Formatted location string

        """
        path = Path(self.file_path)
        if style == "short":
            loc = f"{path.name}:{self.line_number}"
            if self.is_multiline:
                loc += f"-{self.end_line_number}"
            return loc
        if style == "full":
            return f"{self.file_path}:{self.line_number}"
        if style == "url":
            # Format for IDE URL navigation (VS Code, JetBrains)
            line = self.line_number
            col = self.char_offset or 0
            return f"file://{self.file_path}:{line}:{col}"
        return str(self.file_path)

    def __str__(self) -> str:
        """String representation using short format."""
        return self.format_location("short")


@dataclass(frozen=True)
class FileMetadata:
    """Immutable metadata for a source file in the knowledge system.

    Tracks file classification, provenance, and analysis state
    across the knowledge lifecycle.

    Attributes:
        path: Absolute file path
        category: Content category for classification
        skill_source: Skill that added this file (optional)
        indexed: Whether file has been indexed for search
        last_modified: File modification timestamp
        last_indexed: When file was last indexed
        citation_count: Number of citations referencing this file
        tags: User or system-assigned tags
        checksum: Optional file hash for change detection

    """

    path: str
    category: Category
    skill_source: str | None = None
    indexed: bool = False
    last_modified: datetime = field(default_factory=datetime.utcnow)
    last_indexed: datetime | None = None
    citation_count: int = 0
    tags: frozenset[str] = frozenset()
    checksum: str | None = None

    def __post_init__(self) -> None:
        """Validate metadata fields."""
        if self.citation_count < 0:
            msg = f"citation_count must be >= 0, got {self.citation_count}"
            raise ValueError(msg)

    @property
    def filename(self) -> str:
        """Get filename from path."""
        return Path(self.path).name

    @property
    def extension(self) -> str | None:
        """Get file extension including dot."""
        return Path(self.path).suffix or None

    def with_category(self, new_category: Category) -> FileMetadata:
        """Return new metadata with updated category."""
        return FileMetadata(
            path=self.path,
            category=new_category,
            skill_source=self.skill_source,
            indexed=self.indexed,
            last_modified=self.last_modified,
            last_indexed=self.last_indexed,
            citation_count=self.citation_count,
            tags=self.tags,
            checksum=self.checksum,
        )

    def add_tags(self, new_tags: Iterable[str]) -> FileMetadata:
        """Return new metadata with additional tags."""
        combined = self.tags | frozenset(new_tags)
        return FileMetadata(
            path=self.path,
            category=self.category,
            skill_source=self.skill_source,
            indexed=self.indexed,
            last_modified=self.last_modified,
            last_indexed=self.last_indexed,
            citation_count=self.citation_count,
            tags=combined,
            checksum=self.checksum,
        )

    def mark_indexed(self) -> FileMetadata:
        """Return new metadata marked as indexed."""
        return FileMetadata(
            path=self.path,
            category=self.category,
            skill_source=self.skill_source,
            indexed=True,
            last_modified=self.last_modified,
            last_indexed=datetime.utcnow(),
            citation_count=self.citation_count,
            tags=self.tags,
            checksum=self.checksum,
        )

    def increment_citations(self, delta: int = 1) -> FileMetadata:
        """Return new metadata with incremented citation count."""
        new_count = max(0, self.citation_count + delta)
        return FileMetadata(
            path=self.path,
            category=self.category,
            skill_source=self.skill_source,
            indexed=self.indexed,
            last_modified=self.last_modified,
            last_indexed=self.last_indexed,
            citation_count=new_count,
            tags=self.tags,
            checksum=self.checksum,
        )


@dataclass
class KnowledgeItem:
    """A knowledge item with content, citations, and metadata.

    Represents a unit of knowledge stored in the system with
    full provenance tracking.

    Attributes:
        id: Unique item identifier
        content: Item content (text, code, JSON, etc.)
        citations: Source citations for this item
        metadata: File metadata
        embedding: Optional vector embedding
        created_at: Item creation timestamp
        updated_at: Last update timestamp

    """

    id: str
    content: str
    citations: frozenset[Citation]
    metadata: FileMetadata
    embedding: list[float] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def primary_citation(self) -> Citation | None:
        """Get first citation if available."""
        return next(iter(self.citations), None)

    @property
    def source_files(self) -> frozenset[str]:
        """Get unique source files from all citations."""
        return frozenset(c.file_path for c in self.citations)

    def add_citation(self, citation: Citation) -> KnowledgeItem:
        """Return new item with additional citation."""
        return KnowledgeItem(
            id=self.id,
            content=self.content,
            citations=self.citations | {citation},
            metadata=self.metadata.increment_citations(),
            embedding=self.embedding,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def with_embedding(self, embedding: list[float]) -> KnowledgeItem:
        """Return new item with vector embedding."""
        return KnowledgeItem(
            id=self.id,
            content=self.content,
            citations=self.citations,
            metadata=self.metadata,
            embedding=embedding,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )
