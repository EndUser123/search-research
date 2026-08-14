"""Multi-Graph Document Ingestion for CKS.

Implements document chunking and ingestion across 5 graph types:
- Knowledge Graph: Structural hierarchy (parent document + child chunks)
- Vector Graph: Semantic embeddings (per chunk)
- Causal Graph: Temporal sequences (chunk order)
- Social Graph: Entity relationships (people, orgs, concepts)
- System Graph: Provenance tracking (ingestion metadata)
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Types of entities that can be extracted from documents."""

    PERSON = "person"
    ORGANIZATION = "organization"
    CONCEPT = "concept"
    LOCATION = "location"
    TECHNOLOGY = "technology"


@dataclass(frozen=True)
class DocumentEntity:
    """An entity extracted from a document."""

    name: str
    type: EntityType
    start_char: int
    end_char: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.type.value,
            "start_char": self.start_char,
            "end_char": self.end_char,
        }


@dataclass
class DocumentChunk:
    """A chunk of text extracted from a document."""

    text: str
    index: int
    parent_id: str
    start_char: int
    end_char: int
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def size(self) -> int:
        """Return the size of this chunk in characters."""
        return len(self.text)


class DocumentChunker:
    """Chunks documents into semantically meaningful pieces.

    Uses sentence boundary detection with configurable overlap.
    Industry standard: 400-512 tokens = ~500-800 characters.
    """

    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_OVERLAP = 50  # 10% of chunk size

    # Sentence boundary pattern
    SENTENCE_BOUNDARY = re.compile(
        r"(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s*$|(?<=\n)\s*",
        re.MULTILINE,
    )

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
    ) -> None:
        """Initialize the document chunker.

        Args:
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks

        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0:
            raise ValueError("overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")

        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> list[DocumentChunk]:
        """Split text into chunks with metadata.

        Args:
            text: The text to chunk

        Returns:
            List of DocumentChunk objects with parent_id and indices

        """
        if not text:
            return []

        # Generate parent_id for this document
        parent_id = self._generate_parent_id(text)

        # If text is shorter than chunk_size, return single chunk
        if len(text) <= self.chunk_size:
            return [
                DocumentChunk(
                    text=text,
                    index=0,
                    parent_id=parent_id,
                    start_char=0,
                    end_char=len(text),
                    metadata={"chunk_type": "single"},
                ),
            ]

        # Split into sentences first (for boundary preservation)
        sentences = self._split_into_sentences(text)

        # Group sentences into chunks
        return self._group_sentences_into_chunks(
            sentences,
            text,
            parent_id,
        )

    def _generate_parent_id(self, text: str) -> str:
        """Generate a unique parent document ID."""
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"doc_{content_hash}"

    def _split_into_sentences(self, text: str) -> list[tuple[str, int, int]]:
        """Split text into sentences with position tracking.

        Returns:
            List of (sentence, start_pos, end_pos) tuples

        """
        sentences: list[tuple[str, int, int]] = []
        current_pos = 0

        # Split on sentence boundaries
        parts = self.SENTENCE_BOUNDARY.split(text)

        for part in parts:
            if not part.strip():
                current_pos += len(part)
                continue

            start_pos = current_pos
            end_pos = current_pos + len(part)
            sentences.append((part.strip(), start_pos, end_pos))
            current_pos = end_pos

        return sentences

    def _group_sentences_into_chunks(
        self,
        sentences: list[tuple[str, int, int]],
        original_text: str,
        parent_id: str,
    ) -> list[DocumentChunk]:
        """Group sentences into chunks of appropriate size.

        Args:
            sentences: List of (sentence, start_pos, end_pos) tuples
            original_text: The original full text
            parent_id: Parent document ID

        Returns:
            List of DocumentChunk objects

        """
        chunks: list[DocumentChunk] = []
        current_text = ""
        current_start = 0
        overlap_buffer: list[tuple[str, int, int]] = []
        chunk_index = 0

        for sentence, sent_start, sent_end in sentences:
            # Check if adding this sentence would exceed chunk size
            potential_size = len(current_text) + len(sentence) + 1

            if potential_size <= self.chunk_size:
                # Add to current chunk
                if not current_text:
                    current_start = sent_start
                current_text = current_text + " " + sentence if current_text else sentence
                overlap_buffer.append((sentence, sent_start, sent_end))
            else:
                # Save current chunk if it has content
                if current_text:
                    chunks.append(
                        self._create_chunk(
                            current_text,
                            current_start,
                            current_start + len(current_text),
                            parent_id,
                            chunk_index,
                        )
                    )
                    chunk_index += 1

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(overlap_buffer)
                current_start = sent_start - len(overlap_text)
                current_text = overlap_text + " " + sentence if overlap_text else sentence
                overlap_buffer = [(sentence, sent_start, sent_end)]

        # Add final chunk
        if current_text:
            chunks.append(
                self._create_chunk(
                    current_text,
                    current_start,
                    current_start + len(current_text),
                    parent_id,
                    chunk_index,
                )
            )

        return chunks

    def _get_overlap_text(self, overlap_buffer: list[tuple[str, int, int]]) -> str:
        """Get overlap text from buffer."""
        overlap_sentences: list[str] = []
        overlap_chars = 0

        # Take from the end of the buffer (most recent sentences)
        for sentence, _, _ in reversed(overlap_buffer):
            if overlap_chars + len(sentence) > self.overlap:
                break
            overlap_sentences.insert(0, sentence)
            overlap_chars += len(sentence)

        return " ".join(overlap_sentences)

    def _create_chunk(
        self,
        text: str,
        start_char: int,
        end_char: int,
        parent_id: str,
        index: int,
    ) -> DocumentChunk:
        """Create a DocumentChunk with metadata."""
        return DocumentChunk(
            text=text.strip(),
            index=index,
            parent_id=parent_id,
            start_char=start_char,
            end_char=end_char,
            metadata={
                "chunk_size": len(text),
                "created_at": datetime.now(UTC).isoformat(),
            },
        )


class DocumentEntityExtractor:
    """Extract entities from documents for Social graph.

    Uses pattern-based extraction for common entity types.
    """

    # Patterns for capitalized words (person names, organizations)
    CAPITALIZED_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b")

    # Technology/concept patterns
    TECH_PATTERNS = [
        r"\bPython\b",
        r"\bJavaScript\b",
        r"\bTypeScript\b",
        r"\bSQL\b",
        r"\bFAISS\b",
        r"\bSQLite\b",
        r"\bPostgreSQL\b",
        r"\bReact\b",
        r"\bDocker\b",
        r"\bk8s\b",
        r"\bKubernetes\b",
        r"\bGit\b",
        r"\bAPI\b",
    ]

    # Organization patterns (capitalized, typically 2+ words)
    ORG_PATTERNS = [
        r"\bGoogle\b",
        r"\bOpenAI\b",
        r"\bAnthropic\b",
        r"\bMicrosoft\b",
        r"\bMeta\b",
    ]

    def __init__(self) -> None:
        """Initialize the entity extractor."""
        self.tech_pattern = re.compile("|".join(self.TECH_PATTERNS), re.IGNORECASE)
        self.org_pattern = re.compile("|".join(self.ORG_PATTERNS), re.IGNORECASE)

    def extract(self, text: str) -> list[DocumentEntity]:
        """Extract entities from text.

        Args:
            text: The text to extract entities from

        Returns:
            List of unique DocumentEntity objects

        """
        entities: list[DocumentEntity] = []

        # Extract technology/concept entities
        for match in self.tech_pattern.finditer(text):
            entities.append(
                DocumentEntity(
                    name=match.group(),
                    type=EntityType.CONCEPT,
                    start_char=match.start(),
                    end_char=match.end(),
                )
            )

        # Extract organization entities
        for match in self.org_pattern.finditer(text):
            entities.append(
                DocumentEntity(
                    name=match.group(),
                    type=EntityType.ORGANIZATION,
                    start_char=match.start(),
                    end_char=match.end(),
                )
            )

        # Extract person names (simplified: capitalized words not in tech/org lists)
        # This is a basic implementation - production would use NLP
        seen = {e.name.lower() for e in entities}
        for match in self.CAPITALIZED_PATTERN.finditer(text):
            name = match.group()
            if len(name.split()) >= 2 and name.lower() not in seen:
                # Likely a person name (2+ capitalized words)
                entities.append(
                    DocumentEntity(
                        name=name,
                        type=EntityType.PERSON,
                        start_char=match.start(),
                        end_char=match.end(),
                    )
                )
                seen.add(name.lower())

        # Deduplicate by name and type
        unique_entities: dict[tuple[str, EntityType], DocumentEntity] = {}
        for entity in entities:
            key = (entity.name, entity.type)
            if key not in unique_entities:
                unique_entities[key] = entity

        return list(unique_entities.values())


@dataclass
class IngestResult:
    """Result of a document ingestion operation."""

    parent_id: str
    chunk_count: int
    entities_found: int
    ingestion_id: str | None = None
    vector_ids: list[str] = field(default_factory=list)
    edge_ids: list[str] = field(default_factory=list)


class MultiGraphDocumentIngester:
    """Ingest documents across all 5 graph types.

    Orchestrates chunking, entity extraction, and multi-graph storage.
    """

    def __init__(
        self,
        storage: Any | None = None,
        vector_manager: Any | None = None,
        chunker: DocumentChunker | None = None,
        extractor: DocumentEntityExtractor | None = None,
    ) -> None:
        """Initialize the multi-graph document ingester.

        Args:
            storage: Storage manager for multi-graph operations
            vector_manager: Vector manager for embeddings
            chunker: Optional custom chunker
            extractor: Optional custom entity extractor

        """
        self.storage = storage
        self.vector_manager = vector_manager
        self.chunker = chunker or DocumentChunker()
        self.extractor = extractor or DocumentEntityExtractor()

    def ingest(
        self,
        text: str,
        title: str,
        source: str = "user_paste",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IngestResult:
        """Ingest a document across all 5 graph types.

        Args:
            text: The document text to ingest
            title: Title for the document
            source: Source identifier (user_paste, file, url)
            tags: Optional tags for categorization
            metadata: Additional metadata

        Returns:
            IngestResult with IDs and counts

        """
        # Step 1: Chunk the text
        chunks = self.chunker.chunk_text(text)
        parent_id = chunks[0].parent_id if chunks else self.chunker._generate_parent_id(text)

        # Step 2: Extract entities
        entities = self.extractor.extract(text)

        # Step 3: Create parent document node (Knowledge Graph)
        if self.storage:
            self._create_parent_node(
                parent_id,
                title,
                text,
                len(chunks),
                source,
                tags,
                metadata,
            )

        # Step 4: Create chunk nodes (Knowledge Graph) + embeddings (Vector Graph)
        chunk_ids = []
        vector_ids = []
        for chunk in chunks:
            chunk_id = self._create_chunk_node(chunk, parent_id)
            chunk_ids.append(chunk_id)

            if self.vector_manager:
                vid = self._create_vector_embedding(chunk, chunk_id)
                if vid:
                    vector_ids.append(vid)

        # Step 5: Create temporal edges (Causal Graph)
        edge_ids = self._create_temporal_edges(chunk_ids)

        # Step 6: Create entity nodes and mention edges (Social Graph)
        entity_nodes = self._create_entity_nodes(entities, parent_id, source)
        self._create_mention_edges(chunk_ids, entity_nodes)

        # Step 7: Create provenance tracking (System Graph)
        ingestion_id = self._create_provenance_node(
            parent_id,
            source,
            len(chunks),
            len(entities),
        )

        # Step 8: Create cross-graph relationships
        self._create_cross_graph_relations(
            parent_id,
            chunk_ids,
            vector_ids,
            entity_nodes,
        )

        return IngestResult(
            parent_id=parent_id,
            chunk_count=len(chunks),
            entities_found=len(entities),
            ingestion_id=ingestion_id,
            vector_ids=vector_ids,
            edge_ids=edge_ids,
        )

    def _create_parent_node(
        self,
        parent_id: str,
        title: str,
        text: str,
        chunk_count: int,
        source: str,
        tags: list[str] | None,
        metadata: dict[str, Any] | None,
    ) -> str:
        """Create parent document node in Knowledge graph."""
        if not self.storage:
            return f"node_{parent_id}"

        node_data = {
            "id": parent_id,
            "type": "document",
            "content": text[:2000],  # First 2k chars for preview
            "metadata": {
                "title": title,
                "source": source,
                "chunk_count": chunk_count,
                "tags": tags or [],
                "full_length": len(text),
                "ingested_at": datetime.now(UTC).isoformat(),
                **(metadata or {}),
            },
        }
        return self.storage.create_knowledge_node(node_data)

    def _create_chunk_node(self, chunk: DocumentChunk, parent_id: str) -> str:
        """Create a chunk node in Knowledge graph."""
        if not self.storage:
            return f"chunk_{chunk.index}_{parent_id}"

        chunk_id = f"chunk_{chunk.index}_{parent_id}"
        node_data = {
            "id": chunk_id,
            "type": "document_chunk",
            "content": chunk.text,
            "metadata": {
                "parent_id": parent_id,
                "chunk_index": chunk.index,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "chunk_size": chunk.size,
                **chunk.metadata,
            },
        }
        return self.storage.create_knowledge_node(node_data)

    def _create_vector_embedding(self, chunk: DocumentChunk, chunk_id: str) -> str | None:
        """Create vector embedding for a chunk."""
        if not self.vector_manager:
            return None

        vector_id = f"vector_{chunk_id}"
        success = self.vector_manager.ingest(
            id=chunk_id,
            text=chunk.text,
            metadata={
                "chunk_index": chunk.index,
                "parent_id": chunk.parent_id,
            },
        )
        return vector_id if success else None

    def _create_temporal_edges(self, chunk_ids: list[str]) -> list[str]:
        """Create TEMPORAL_SEQUENCE edges between chunks."""
        edge_ids = []
        if not self.storage:
            return edge_ids

        for i in range(len(chunk_ids) - 1):
            edge_data = {
                "id": f"temporal_{chunk_ids[i]}_{chunk_ids[i+1]}",
                "source": chunk_ids[i],
                "target": chunk_ids[i + 1],
                "relationship": "TEMPORAL_SEQUENCE",
                "metadata": {
                    "strength": 1.0,
                    "confidence": 1.0,
                },
            }
            edge_id = self.storage.create_knowledge_edge(edge_data)
            edge_ids.append(edge_id)

        return edge_ids

    def _create_entity_nodes(
        self,
        entities: list[DocumentEntity],
        parent_id: str,
        source: str,
    ) -> list[str]:
        """Create entity nodes in Social graph."""
        entity_ids = []
        if not self.storage:
            return entity_ids

        for entity in entities:
            entity_id = f"entity_{entity.type.value}_{hash(entity.name)}"
            node_data = {
                "id": entity_id,
                "type": "entity",
                "content": entity.name,
                "metadata": {
                    "entity_type": entity.type.value,
                    "source_document": parent_id,
                    "source_type": source,
                },
            }
            # Would use create_social_node if available
            try:
                eid = self.storage.create_knowledge_node(node_data)
                entity_ids.append(eid)
            except Exception as e:
                logger.debug("Failed to create entity node for %s: %s", entity.name, e)
                entity_ids.append(entity_id)

        return entity_ids

    def _create_mention_edges(
        self,
        chunk_ids: list[str],
        entity_ids: list[str],
    ) -> None:
        """Create MENTIONS edges between chunks and entities."""
        if not self.storage:
            return

        for chunk_id in chunk_ids:
            for entity_id in entity_ids:
                edge_data = {
                    "id": f"mention_{chunk_id}_{entity_id}",
                    "source": chunk_id,
                    "target": entity_id,
                    "relationship": "MENTIONS",
                    "metadata": {
                        "strength": 0.8,
                        "confidence": 0.7,
                    },
                }
                try:
                    self.storage.create_knowledge_edge(edge_data)
                except Exception as e:
                    logger.debug(
                        "Failed to create mention edge %s -> %s: %s", chunk_id, entity_id, e
                    )

    def _create_provenance_node(
        self,
        parent_id: str,
        source: str,
        chunk_count: int,
        entity_count: int,
    ) -> str | None:
        """Create provenance tracking node in System graph."""
        if not self.storage:
            return None

        ingestion_id = f"ingest_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{parent_id[:8]}"
        node_data = {
            "id": ingestion_id,
            "type": "ingestion_event",
            "content": f"Document ingestion from {source}",
            "metadata": {
                "source": source,
                "document_id": parent_id,
                "chunk_count": chunk_count,
                "entity_count": entity_count,
                "ingested_at": datetime.now(UTC).isoformat(),
            },
        }

        try:
            self.storage.create_knowledge_node(node_data)

            # Link ingestion to document
            edge_data = {
                "id": f"created_{ingestion_id}_{parent_id}",
                "source": ingestion_id,
                "target": parent_id,
                "relationship": "CREATED",
                "metadata": {"strength": 1.0},
            }
            self.storage.create_knowledge_edge(edge_data)
        except Exception as e:
            logger.debug("Failed to create provenance tracking for %s: %s", ingestion_id, e)

        return ingestion_id

    def _create_cross_graph_relations(
        self,
        parent_id: str,
        chunk_ids: list[str],
        vector_ids: list[str],
        entity_ids: list[str],
    ) -> None:
        """Create cross-graph relationships."""
        if not self.storage:
            return

        # Link parent to chunks (Knowledge → Knowledge)
        for chunk_id in chunk_ids:
            edge_data = {
                "id": f"contains_{parent_id}_{chunk_id}",
                "source": parent_id,
                "target": chunk_id,
                "relationship": "CONTAINS",
                "metadata": {"strength": 1.0},
            }
            try:
                self.storage.create_knowledge_edge(edge_data)
            except Exception as e:
                logger.debug("Failed to create CONTAINS edge %s -> %s: %s", parent_id, chunk_id, e)
