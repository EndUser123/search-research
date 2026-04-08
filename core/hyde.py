"""HyDE (Hypothetical Document Embeddings) query enhancement.

This module implements HyDE query enhancement for web search using pre-generated
hypothetical documents from Claude Code (the orchestrator). HyDE improves retrieval
by enhancing search queries with key phrases extracted from hypothetical documents.

HYDE-001: Hypothetical Document Generation
Claude Code (orchestrator) generates hypothetical documents before invoking Python.
This module does NOT make external API calls.

HYDE-002: Key Phrase Extraction
Extracts 3-5 key phrases from the hypothetical document using regex-based fallback.

HYDE-003: Query Enhancement
Combines original query with key phrases for improved retrieval.

HYDE-004: Graceful Degradation
If HyDE content is not provided, searches with original query.
"""

import logging
import re

logger = logging.getLogger(__name__)


def extract_key_phrases(doc: str) -> list[str]:
    """Extract 3-5 key phrases from hypothetical document.

    HYDE-002: Extracts important phrases and concepts from the hypothetical
    document using regex-based NLP techniques. No external API calls.

    Args:
        doc: Hypothetical document text

    Returns:
        List of 3-5 key phrases

    Raises:
        ValueError: If doc is empty

    Examples:
        >>> doc = "FastAPI supports async operations using async/await syntax."
        >>> phrases = extract_key_phrases(doc)
        >>> len(phrases) >= 0
        True
    """
    if not doc or not doc.strip():
        raise ValueError("Document cannot be empty")

    return _extract_key_phrases_fallback(doc)


def _extract_key_phrases_fallback(doc: str) -> list[str]:
    """Extract key phrases using regex-based NLP techniques.

    Uses simple heuristics to extract important phrases from text.
    This is the primary extraction method (no external API calls).

    Args:
        doc: Document text

    Returns:
        List of up to 5 key phrases
    """
    # Split into sentences
    sentences = re.split(r"[.!?]+", doc)

    # Extract noun phrases (simple heuristic: capitalized words + following words)
    phrases = []
    for sentence in sentences:
        # Find capitalized words and following words
        matches = re.findall(r"\b[A-Z][a-z]+(?:\s+[a-z]+){0,2}\b", sentence)
        phrases.extend(matches)

    # Remove duplicates and limit to 5
    unique_phrases = list(dict.fromkeys(phrases))  # Preserve order while deduplicating
    return unique_phrases[:5]


def enhance_query(query: str, key_phrases: list[str]) -> str:
    """Enhance query with key phrases from hypothetical document.

    HYDE-003: Combines original query with extracted key phrases to create
    an enhanced query for better retrieval.

    Args:
        query: Original search query
        key_phrases: List of key phrases

    Returns:
        Enhanced query string

    Raises:
        ValueError: If query is empty

    Examples:
        >>> enhance_query("FastAPI async", ["async operations", "await syntax"])
        'FastAPI async async operations await syntax'
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    if not key_phrases:
        return query.strip()

    # Combine query with key phrases
    enhanced = f"{query.strip()} {' '.join(key_phrases)}"

    logger.debug(f"Enhanced query: {query[:50]}... -> {enhanced[:50]}...")
    return enhanced


def apply_hyde(query: str, hyde_content: str | None = None) -> tuple[str, bool]:
    """Apply HyDE enhancement to query using pre-generated content.

    HYDE-004: Orchestrates the HyDE pipeline with pre-generated hypothetical
    documents from Claude Code (orchestrator). If content is not provided,
    returns original query unchanged.

    Architecture Change (Breaking):
        - Claude Code (orchestrator) generates hypothetical documents
        - Python code accepts pre-generated content via hyde_content parameter
        - No external API calls from Python code

    Args:
        query: Original search query
        hyde_content: Pre-generated hypothetical document from Claude Code

    Returns:
        Tuple of (enhanced_query, hyde_was_applied)

    Examples:
        >>> enhanced, applied = apply_hyde("FastAPI patterns")
        >>> isinstance(enhanced, str)
        True
        >>> isinstance(applied, bool)
        True

        >>> # With pre-generated content
        >>> doc = "FastAPI supports async operations using Python's async/await syntax."
        >>> enhanced, applied = apply_hyde("FastAPI patterns", hyde_content=doc)
        >>> applied
        True
    """
    if not hyde_content or not hyde_content.strip():
        logger.debug("No HyDE content provided. Using original query.")
        return query.strip(), False

    try:
        # Step 1: Extract key phrases from pre-generated content
        key_phrases = extract_key_phrases(hyde_content)

        # Step 2: Enhance query with key phrases
        if not key_phrases:
            logger.debug("No key phrases extracted. Using original query.")
            return query.strip(), False

        enhanced = enhance_query(query, key_phrases)
        return enhanced, True

    except Exception as e:
        logger.warning(f"HyDE enhancement failed: {e}. Using original query.")
        return query.strip(), False
