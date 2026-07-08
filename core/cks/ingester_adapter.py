"""CKS Ingester Adapter - Bridges MultiGraphDocumentIngester with CKS unified schema.

This adapter connects the document chunking and entity extraction from
MultiGraphDocumentIngester with the real CKS storage, allowing proper
persistence of multi-graph documents.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .document_ingest import (
    DocumentChunker,
    DocumentEntityExtractor,
)

# Lazy import: SmartChunker is optional — only needed when content-addressed
# chunking is requested.  Importing at module level pulls sentence-transformers
# transitively which is expensive.
_SmartChunker = None


def _get_smart_chunker():
    global _SmartChunker
    if _SmartChunker is None:
        from core.chunking.smart_chunker import SmartChunker
        _SmartChunker = SmartChunker
    return _SmartChunker

logger = logging.getLogger(__name__)

__all__ = ["AdapterIngestResult", "CKSIngesterAdapter"]


@dataclass
class AdapterIngestResult:
    """Result from CKSIngesterAdapter.ingest_document()."""

    chunk_count: int
    entities_found: int
    entry_ids: list[str] = field(default_factory=list)
    parent_title: str = ""


class CKSIngesterAdapter:
    """Bridges MultiGraphDocumentIngester with CKS unified schema.

    The MultiGraphDocumentIngester was designed for a hypergraph architecture
    with separate node types (knowledge, vector, causal, social, system). The
    real CKS uses a unified schema with a single entries table and entity
    relationships.

    This adapter:
    1. Uses DocumentChunker to split documents
    2. Uses DocumentEntityExtractor to find entities
    3. Ingests each chunk via CKS.ingest_pattern()
    4. Stores entity relationships in metadata
    5. Creates entity_relationships rows for cross-chunk links

    Example:
        cks = CKS()
        adapter = CKSIngesterAdapter(cks)
        result = adapter.ingest_document(
            text="Long document text...",
            title="My Document",
            tags=["docs", "project"]
        )
        print(f"Ingested {result.chunk_count} chunks with {result.entities_found} entities")

    """

    def __init__(self, cks, chunk_size: int = 500, overlap: int = 50,
                 use_smart_chunker: bool = False) -> None:
        """Initialize the adapter with a CKS instance.

        Args:
            cks: CKS instance for ingestion
            chunk_size: Maximum characters per chunk (default: 500)
            overlap: Character overlap between chunks (default: 50)
            use_smart_chunker: If True, use SmartChunker for content-addressed
                chunk IDs (chunk_id, text_sha256, chunker_name/version/params).
                Falls back to positional DocumentChunker when False.

        """
        self.cks = cks
        self.use_smart_chunker = use_smart_chunker
        self.chunker = DocumentChunker(chunk_size=chunk_size, overlap=overlap)
        self.extractor = DocumentEntityExtractor()

    def ingest_document(
        self,
        text: str,
        title: str,
        tags: list[str] | None = None,
        source: str = "adapter",
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> AdapterIngestResult:
        """Ingest a document with chunking and entity extraction.

        Args:
            text: Document text to ingest
            title: Document title
            tags: Optional list of tags
            source: Source identifier (default: "adapter")
            chunk_size: Override default chunk size
            overlap: Override default overlap

        Returns:
            AdapterIngestResult with chunk_count, entities_found, and entry_ids

        """
        # Handle empty text
        if not text or not text.strip():
            return AdapterIngestResult(
                chunk_count=0,
                entities_found=0,
                parent_title=title,
            )

        # Use custom chunking if specified
        if chunk_size is not None or overlap is not None:
            chunker = DocumentChunker(
                chunk_size=chunk_size or self.chunker.chunk_size,
                overlap=overlap or self.chunker.overlap,
            )
        else:
            chunker = self.chunker

        # Extract entities from full document
        entities = self.extractor.extract(text)
        entity_names = {e.name for e in entities}

        # Chunk the document — SmartChunker path or legacy positional
        if self.use_smart_chunker:
            smart = _get_smart_chunker()()
            doc_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
            records = smart.chunk_with_metadata(text, doc_id=doc_id)
            chunks = None  # not used in SmartChunker path
        else:
            chunks = chunker.chunk_text(text)
            records = None

        # Ingest each chunk
        entry_ids = []
        if records:
            # SmartChunker path — content-addressed IDs
            for rec in records:
                chunk_metadata = {
                    "chunk_id": rec["chunk_id"],
                    "chunk_index": rec["char_start"],  # use char_start as ordinal
                    "chunk_start": rec["char_start"],
                    "chunk_end": rec["char_end"],
                    "parent_id": rec["doc_id"],
                    "total_chunks": len(records),
                    "text_sha256": rec["text_sha256"],
                    "chunker_name": rec["chunker_name"],
                    "chunker_version": rec["chunker_version"],
                    "source": source,
                    "entities_in_chunk": [
                        {
                            "name": e.name,
                            "type": e.type.value,
                            "start_char": e.start_char,
                            "end_char": e.end_char,
                        }
                        for e in entities
                        if rec["char_start"] <= e.start_char < rec["char_end"]
                    ],
                    "tags": tags or [],
                }
                chunk_title = f"{title}"
                if len(records) > 1:
                    chunk_title = f"{title} (chunk {rec['chunk_id'][:8]}…)"
                entry_id = self.cks.ingest_pattern(
                    title=chunk_title,
                    content=rec["text"],
                    **chunk_metadata,
                )
                entry_ids.append(entry_id)
        else:
            # Legacy DocumentChunker path — positional IDs
            for chunk in chunks:
                # Build metadata with chunk info and entities
                chunk_metadata = {
                    "chunk_index": chunk.index,
                    "chunk_start": chunk.start_char,
                    "chunk_end": chunk.end_char,
                    "parent_id": chunk.parent_id,
                    "total_chunks": len(chunks),
                    "source": source,
                    "entities_in_chunk": [
                        {
                            "name": e.name,
                            "type": e.type.value,
                            "start_char": e.start_char,
                            "end_char": e.end_char,
                    }
                    for e in entities
                    # Include entities that appear in this chunk
                    if chunk.start_char <= e.start_char < chunk.end_char
                ],
                "tags": tags or [],
            }

            # Create chunk title with index
            chunk_title = f"{title}"
            if len(chunks) > 1:
                chunk_title = f"{title} (Part {chunk.index + 1}/{len(chunks)})"

            # Ingest via CKS
            entry_id = self.cks.ingest_pattern(
                title=chunk_title,
                content=chunk.text,
                **chunk_metadata,
            )
            entry_ids.append(entry_id)

        # Create entity relationships if we have a database connection
        if len(chunks) > 1 and hasattr(self.cks, "conn") and self.cks.conn:
            self._create_entity_relationships(entry_ids, entities, title)

        return AdapterIngestResult(
            chunk_count=len(chunks),
            entities_found=len(entity_names),
            entry_ids=entry_ids,
            parent_title=title,
        )

    def _create_entity_relationships(
        self,
        entry_ids: list[str],
        entities: list[Any],
        document_title: str,
    ) -> None:
        """Create entity_relationships rows for cross-chunk links.

        Creates relationships:
        - TEMPORAL_SEQUENCE: between consecutive chunks
        - MENTIONS: between chunks and entities

        Args:
            entry_ids: List of entry IDs for chunks
            entities: List of DocumentEntity objects
            document_title: Title of the document

        """
        if not self.cks.conn:
            return

        cursor = self.cks.conn.cursor()

        try:
            # Create TEMPORAL_SEQUENCE relationships between chunks
            for i in range(len(entry_ids) - 1):
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO entity_relationships
                    (from_entry_id, to_entry_id, relationship_type, metadata)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        entry_ids[i],
                        entry_ids[i + 1],
                        "TEMPORAL_SEQUENCE",
                        json.dumps(
                            {
                                "document": document_title,
                                "sequence_index": i,
                                "created_at": datetime.now(UTC).isoformat(),
                            }
                        ),
                    ),
                )

            # Create CONTAINS relationship from document to first chunk
            # (representing the parent-child hierarchy)
            if entry_ids:
                parent_id = f"doc_{document_title.replace(' ', '_').lower()}"
                for entry_id in entry_ids:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO entity_relationships
                        (from_entry_id, to_entry_id, relationship_type, metadata)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            parent_id,
                            entry_id,
                            "CONTAINS",
                            json.dumps(
                                {
                                    "document": document_title,
                                    "created_at": datetime.now(UTC).isoformat(),
                                }
                            ),
                        ),
                    )

            self.cks.conn.commit()

        except Exception as e:
            # Don't fail ingestion if relationships fail
            logger.debug("Failed to create entity relationships: %s", e)
