"""HyDE (Hypothetical Document Embeddings) multi-perspective generation.

This module provides multi-perspective HyDE generation, which creates multiple
hypothetical documents from different audience perspectives (technical, beginner)
for comprehensive query enhancement with rich metadata tracking.

HYDE-MP-001: Multi-Perspective Configuration
MultiHyDEConfig dataclass configures perspective-based generation with
perspectives list and n_generations parameters.

HYDE-MP-002: Hypothetical Document Data Structure
HypotheticalDocument dataclass stores document content with metadata including
word_count, token_count, perspective, and generation_time.

HYDE-MP-003: Multi-Document Result Container
MultiHypotheticalDocuments aggregates multiple documents with combined metrics
and helper methods for perspective-based access.
"""

import time
from dataclasses import dataclass, field


@dataclass
class MultiHyDEConfig:
    """Configuration for multi-perspective HyDE.

    Attributes:
        perspectives: List of perspective names to generate.
        n_generations: Number of generations per perspective.
    """

    perspectives: list[str] = field(default_factory=lambda: ["technical", "beginner"])
    n_generations: int = 3


@dataclass
class HypotheticalDocument:
    """A hypothetical document from a specific perspective.

    Attributes:
        query: The original query.
        content: The generated content.
        generation_model: Model used for generation.
        generation_time: Time taken for generation.
        word_count: Number of words in content.
        token_count: Estimated token count.
        perspective: The perspective name.
    """

    query: str
    content: str
    generation_model: str = "glm"
    generation_time: float = 0.0
    word_count: int = 0
    token_count: int = 0
    perspective: str = "technical"


@dataclass
class MultiHypotheticalDocuments:
    """Result from multi-perspective HyDE generation.

    HYDE-MP-003: Aggregates multiple documents with combined metrics.

    Attributes:
        query: The original query.
        documents: List of generated hypothetical documents.
        perspectives: List of perspective names used.
        total_generation_time: Total time for generation.
        total_word_count: Total word count across all documents.
        total_token_count: Total token count across all documents.
    """

    query: str
    documents: list[HypotheticalDocument]
    perspectives: list[str]
    total_generation_time: float = 0.0
    total_word_count: int = 0
    total_token_count: int = 0

    def get_document_by_perspective(self, perspective: str) -> HypotheticalDocument | None:
        """Get document by perspective name.

        Args:
            perspective: The perspective name to find.

        Returns:
            The HypotheticalDocument if found, None otherwise.

        Examples:
            >>> docs = MultiHypotheticalDocuments(query="test", documents=[], perspectives=[])
            >>> docs.get_document_by_perspective("technical")
            None
        """
        for doc in self.documents:
            if doc.perspective == perspective:
                return doc
        return None

    def get_combined_content(self) -> str:
        """Get combined content from all documents.

        Returns:
            Combined content with separator.

        Examples:
            >>> from search_research.hyde_multi_perspective import HypotheticalDocument
            >>> doc1 = HypotheticalDocument(query="test", content="A", perspective="technical")
            >>> doc2 = HypotheticalDocument(query="test", content="B", perspective="beginner")
            >>> docs = MultiHypotheticalDocuments(
            ...     query="test",
            ...     documents=[doc1, doc2],
            ...     perspectives=["technical", "beginner"]
            ... )
            >>> combined = docs.get_combined_content()
            >>> "--- technical ---" in combined
            >>> True
        """
        contents = [f"--- {doc.perspective} ---\n{doc.content}" for doc in self.documents]
        return "\n\n".join(contents)


def _generate_mock_content_for_perspective(query: str, perspective: str) -> str:
    """Generate mock content for a specific perspective.

    Args:
        query: The query string.
        perspective: The perspective name.

    Returns:
            Generated content string.
    """
    return f"Generated content for perspective '{perspective}' based on query: {query}"


def generate_multi_hypothetical_documents(
    query: str, config: MultiHyDEConfig | None = None
) -> MultiHypotheticalDocuments:
    """Generate multiple hypothetical documents from different perspectives.

    HYDE-MP-003: Creates multiple documents with metadata tracking.

    Args:
        query: The query string.
        config: Configuration for generation. Uses default if None.

    Returns:
        MultiHypotheticalDocuments with generated documents.

    Raises:
        ValueError: If query is empty.
        TypeError: If query is None.

    Examples:
        >>> result = generate_multi_hypothetical_documents("FastAPI patterns")
        >>> len(result.documents)
        2
        >>> result.documents[0].perspective
        'technical'
    """
    if query is None:
        raise TypeError("Query cannot be None")
    if not query or query.strip() == "":
        raise ValueError("Query cannot be empty")

    if config is None:
        config = MultiHyDEConfig()

    start_time = time.time()

    documents = []
    total_word_count = 0
    total_token_count = 0

    for perspective in config.perspectives:
        content = _generate_mock_content_for_perspective(query, perspective)
        word_count = len(content.split())
        token_count = len(content) // 4

        doc = HypotheticalDocument(
            query=query,
            content=content,
            perspective=perspective,
            generation_model="glm",
            generation_time=0.5,
            word_count=word_count,
            token_count=token_count,
        )
        documents.append(doc)
        total_word_count += word_count
        total_token_count += token_count

    total_generation_time = time.time() - start_time

    return MultiHypotheticalDocuments(
        query=query,
        documents=documents,
        perspectives=config.perspectives.copy(),
        total_generation_time=total_generation_time,
        total_word_count=total_word_count,
        total_token_count=total_token_count,
    )
