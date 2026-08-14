"""HyDE Scoring - Quality assessment and phrase extraction.

This module provides utilities for:
1. Scoring the quality of generated HyDE documents
2. Extracting key phrases from documents
3. Enhancing queries with semantic keywords
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# =============================================================================
# Key Phrase Extraction
# =============================================================================


class PhraseExtractor:
    """Extracts meaningful key phrases from text using NLP-inspired heuristics."""

    # Patterns for technical terms
    _IDENTIFIER_PATTERN = re.compile(r"\b[a-z_][a-z0-9_]{2,}\b")
    _CAMEL_CASE_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b")
    _ABBREVIATION_PATTERN = re.compile(r"\b[A-Z]{2,}\b")

    # Patterns for quoted terms
    _QUOTED_TERM_PATTERN = re.compile(r'"([^"]+)"')

    # Common stop words to filter out
    _STOP_WORDS = frozenset(
        {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "were",
            "been",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
            "they",
            "them",
            "their",
            "there",
            "here",
            "when",
            "where",
            "why",
            "how",
            "what",
            "which",
            "who",
            "whom",
            "whose",
            "if",
            "then",
            "than",
            "so",
            "such",
            "no",
            "not",
            "only",
            "own",
            "same",
            "just",
            "also",
            "now",
            "all",
            "both",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "any",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
        }
    )

    __slots__ = ()

    @classmethod
    def extract(
        cls,
        text: str,
        count: int = 5,
        min_length: int = 3,
        max_length: int = 30,
    ) -> list[str]:
        """Extract key phrases from the given text.

        Args:
            text: The text to extract phrases from
            count: Maximum number of phrases to return
            min_length: Minimum phrase length in characters
            max_length: Maximum phrase length in characters

        Returns:
            List of extracted key phrases, ranked by relevance
        """
        if not text:
            return []

        phrases: dict[str, float] = {}

        # Extract quoted terms (highest priority)
        for match in cls._QUOTED_TERM_PATTERN.finditer(text):
            phrase = match.group(1).lower()
            if min_length <= len(phrase) <= max_length:
                phrases[phrase] = phrases.get(phrase, 0) + 3.0

        # Extract CamelCase identifiers
        for match in cls._CAMEL_CASE_PATTERN.finditer(text):
            phrase = match.group()
            if min_length <= len(phrase) <= max_length:
                phrases[phrase] = phrases.get(phrase, 0) + 2.5

        # Extract abbreviations
        for match in cls._ABBREVIATION_PATTERN.finditer(text):
            phrase = match.group().lower()
            if min_length <= len(phrase) <= max_length:
                phrases[phrase] = phrases.get(phrase, 0) + 2.0

        # Extract snake_case identifiers
        for match in cls._IDENTIFIER_PATTERN.finditer(text):
            phrase = match.group().lower()
            if min_length <= len(phrase) <= max_length:
                # Skip if it's a stop word
                if phrase not in cls._STOP_WORDS:
                    phrases[phrase] = phrases.get(phrase, 0) + 1.5

        # Extract technical noun phrases (capitalized sequences)
        text_lower = text.lower()
        words = text.split()

        # Look for adjacent capitalized words (potential multi-word terms)
        for i in range(len(words) - 1):
            word1, word2 = words[i], words[i + 1]

            # Check if both words are significant (not stop words)
            w1_lower = word1.strip(".,!?;:()[]{}\"'").lower()
            w2_lower = word2.strip(".,!?;:()[]{}\"'").lower()

            if w1_lower in cls._STOP_WORDS or w2_lower in cls._STOP_WORDS:
                continue

            # Check if both are capitalized (proper nouns)
            if word1[0].isupper() and word2[0].isupper():
                phrase = f"{w1_lower} {w2_lower}"
                if min_length <= len(phrase) <= max_length:
                    phrases[phrase] = phrases.get(phrase, 0) + 1.0

        # Extract individual meaningful words
        for word in words:
            clean_word = word.strip(".,!?;:()[]{}\"'").lower()

            if min_length <= len(clean_word) <= max_length and clean_word not in cls._STOP_WORDS:
                # Boost technical-looking words
                boost = 1.0
                if any(c.isdigit() for c in clean_word):
                    boost = 1.2  # Alphanumeric terms are often technical
                if "_" in clean_word:
                    boost = 1.3  # Snake_case identifiers

                phrases[clean_word] = phrases.get(clean_word, 0) + boost

        # Extract collocated phrases (multi-word technical terms)
        collocations = cls._extract_collocations(text)
        for phrase, score in collocations.items():
            if min_length <= len(phrase) <= max_length:
                phrases[phrase] = phrases.get(phrase, 0) + score

        # Sort by score and return top N
        sorted_phrases = sorted(phrases.items(), key=lambda x: x[1], reverse=True)
        return [phrase for phrase, _ in sorted_phrases[:count]]

    @classmethod
    def _extract_collocations(cls, text: str) -> dict[str, float]:
        """Extract multi-word collocations from text."""
        collocations: dict[str, float] = {}

        # Technical term patterns
        patterns = [
            (
                r"\b(?:data|error|config|file|code|log|user|auth|api|db)\s+(?:structure|handling|format|name|base|token|point|key)",
                1.5,
            ),
            (r"\b(?:machine|neural|deep|reinforcement)\s+(?:learning|network)\b", 2.0),
            (r"\b(?:natural|nlp)\s+language\s+processing\b", 2.0),
            (r"\b(?:web|rest|graphql)\s+(?:service|api|endpoint)\b", 1.8),
            (r"\b(?:unit|integration|e2e)\s+(?:test|testing)\b", 1.8),
            (r"\b(?:agile|scrum|kanban)\s+(?:development|methodology|process)\b", 1.5),
            (r"\b(?:version|git|source)\s+(?:control|code)\b", 1.5),
            (r"\b(?:continuous|ci|cd)\s+(?:integration|deployment|delivery)\b", 1.8),
        ]

        for pattern, score in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                phrase = match.group().lower()
                collocations[phrase] = max(collocations.get(phrase, 0), score)

        return collocations


# =============================================================================
# Quality Scoring
# =============================================================================


@dataclass
class RelevanceMetrics:
    """Metrics for assessing HyDE document quality."""

    semantic_overlap: float  # Query-document term overlap
    length_score: float  # Appropriate length
    specificity: float  # Specific vs generic content
    coherence: float  # Logical flow indicators
    technical_depth: float  # Domain-specific terminology
    overall_score: float  # Combined quality score

    __slots__ = (
        "semantic_overlap",
        "length_score",
        "specificity",
        "coherence",
        "technical_depth",
        "overall_score",
    )

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "semantic_overlap": self.semantic_overlap,
            "length_score": self.length_score,
            "specificity": self.specificity,
            "coherence": self.coherence,
            "technical_depth": self.technical_depth,
            "overall_score": self.overall_score,
        }


class HyDEQualityScorer:
    """Scores the quality of generated HyDE documents."""

    # Coherence indicators
    _COHERENCE_MARKERS = frozenset(
        {
            "first",
            "then",
            "next",
            "after",
            "before",
            "finally",
            "lastly",
            "however",
            "therefore",
            "thus",
            "consequently",
            "moreover",
            "furthermore",
            "additionally",
            "also",
            "similarly",
            "likewise",
            "for example",
            "for instance",
            "specifically",
            "namely",
            "in contrast",
            "on the other hand",
            "conversely",
        }
    )

    # Technical term patterns
    _TECHNICAL_PATTERNS = (
        r"\b\w+(?:_(?:\w+)_?)+\b",  # snake_case
        r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b",  # CamelCase
        r"\b[A-Z]{2,}\b",  # Abbreviations
        r"\b\d+\b",  # Numbers
        r"\b(?:class|function|method|variable|parameter|argument|API|endpoint)\b",
    )

    __slots__ = ()

    @classmethod
    def score(
        cls,
        query: str,
        hyde: str,
        weights: dict[str, float] | None = None,
    ) -> RelevanceMetrics:
        """Score the quality of a HyDE document relative to the query.

        Args:
            query: Original search query
            hyde: Generated hypothetical document
            weights: Optional weights for each metric

        Returns:
            RelevanceMetrics object with detailed scoring
        """
        # Default weights
        if weights is None:
            weights = {
                "semantic_overlap": 0.35,
                "length_score": 0.15,
                "specificity": 0.20,
                "coherence": 0.15,
                "technical_depth": 0.15,
            }

        # Calculate individual metrics
        semantic_overlap = cls._semantic_overlap(query, hyde)
        length_score = cls._length_score(hyde)
        specificity = cls._specificity_score(hyde)
        coherence = cls._coherence_score(hyde)
        technical_depth = cls._technical_depth_score(hyde)

        # Combine with weights
        overall = (
            semantic_overlap * weights.get("semantic_overlap", 0.35)
            + length_score * weights.get("length_score", 0.15)
            + specificity * weights.get("specificity", 0.20)
            + coherence * weights.get("coherence", 0.15)
            + technical_depth * weights.get("technical_depth", 0.15)
        )

        return RelevanceMetrics(
            semantic_overlap=semantic_overlap,
            length_score=length_score,
            specificity=specificity,
            coherence=coherence,
            technical_depth=technical_depth,
            overall_score=round(overall, 3),
        )

    @classmethod
    def _semantic_overlap(cls, query: str, hyde: str) -> float:
        """Calculate semantic overlap between query and document."""
        if not query or not hyde:
            return 0.0

        # Extract terms from query
        query_terms = {
            w.lower().strip(".,!?;:()[]{}\"'")
            for w in query.split()
            if len(w.strip(".,!?;:()[]{}\"'")) >= 3
        }

        # Extract terms from hyde document
        hyde_terms = {
            w.lower().strip(".,!?;:()[]{}\"'")
            for w in hyde.split()
            if len(w.strip(".,!?;:()[]{}\"'")) >= 3
        }

        if not query_terms or not hyde_terms:
            return 0.0

        # Jaccard similarity
        intersection = query_terms & hyde_terms
        union = query_terms | hyde_terms

        return len(intersection) / len(union) if union else 0.0

    @classmethod
    def _length_score(cls, text: str) -> float:
        """Score based on appropriate length."""
        length = len(text)

        # Optimal range: 200-600 characters
        if length < 50:
            return 0.3  # Too short
        if length < 100:
            return 0.6  # Still short
        if 100 <= length <= 600:
            return 1.0  # Optimal
        if length <= 1000:
            return 0.8  # Acceptable
        if length <= 1500:
            return 0.5  # Getting long
        return 0.3  # Too long

    @classmethod
    def _specificity_score(cls, text: str) -> float:
        """Score based on specific vs generic content."""
        if not text:
            return 0.0

        words = text.split()
        word_count = len(words)

        # Count specific indicators
        specific_count = 0

        # Numbers indicate specificity
        specific_count += len(re.findall(r"\b\d+\b", text))

        # Code-like identifiers
        specific_count += len(re.findall(r"\b[a-z_][a-z0-9_]{2,}\b", text.lower()))

        # Capitalized terms (proper nouns)
        specific_count += len(re.findall(r"\b[A-Z][a-z]+\b", text))

        # Technical terms
        for pattern in cls._TECHNICAL_PATTERNS:
            specific_count += len(re.findall(pattern, text))

        # Normalize by word count
        specificity = min(1.0, specific_count / max(word_count * 0.1, 1))

        return specificity

    @classmethod
    def _coherence_score(cls, text: str) -> float:
        """Score based on coherence indicators."""
        if not text:
            return 0.0

        text_lower = text.lower()
        sentences = re.split(r"[.!?]+", text)
        sentence_count = len([s for s in sentences if s.strip()])

        if sentence_count == 0:
            return 0.0

        # Count coherence markers
        marker_count = sum(1 for marker in cls._COHERENCE_MARKERS if marker in text_lower)

        # Numbered lists indicate structure
        numbered_items = len(re.findall(r"\b\d+\.\s", text))

        # Normalize
        coherence_score = min(1.0, (marker_count + numbered_items * 2) / max(sentence_count, 1))

        return coherence_score

    @classmethod
    def _technical_depth_score(cls, text: str) -> float:
        """Score based on technical terminology."""
        if not text:
            return 0.0

        score = 0.0
        word_count = len(text.split())

        # Check for various technical patterns
        for pattern in cls._TECHNICAL_PATTERNS:
            matches = len(re.findall(pattern, text))
            score += matches * 0.5

        # Normalize by word count
        normalized = min(1.0, score / max(word_count * 0.05, 1))

        return normalized


# =============================================================================
# Query Enhancement
# =============================================================================


class QueryEnhancer:
    """Enhances queries with extracted key phrases."""

    __slots__ = ()

    @classmethod
    def enhance(
        cls,
        query: str,
        hyde_doc: str | None = None,
        phrase_count: int = 5,
    ) -> str:
        """Enhance a query with semantic key phrases.

        Args:
            query: Original query
            hyde_doc: Optional HyDE document to extract phrases from
            phrase_count: Number of phrases to extract

        Returns:
            Enhanced query string
        """
        if not hyde_doc:
            return query

        # Extract key phrases from HyDE document
        phrases = PhraseExtractor.extract(hyde_doc, count=phrase_count)

        if not phrases:
            return query

        # Filter out phrases already in query
        query_lower = query.lower()
        new_phrases = [p for p in phrases if p.lower() not in query_lower]

        if not new_phrases:
            return query

        # Add top phrases to query
        top_phrases = " ".join(new_phrases[:3])  # Add up to 3 new phrases

        return f"{query} {top_phrases}"


# =============================================================================
# Public API Functions
# =============================================================================


def extract_key_phrases(
    hyde_doc: str,
    count: int = 5,
    min_length: int = 3,
    max_length: int = 30,
) -> list[str]:
    """Extract semantic key phrases from a HyDE document.

    This function identifies and ranks meaningful phrases from the document,
    prioritizing technical terms, identifiers, and domain-specific terminology.

    Args:
        hyde_doc: The HyDE document to extract phrases from
        count: Maximum number of phrases to return
        min_length: Minimum phrase length in characters
        max_length: Maximum phrase length in characters

    Returns:
        List of extracted key phrases, ranked by relevance

    Example:
        >>> hyde = generate_hyde("How to implement caching in Python?")
        >>> phrases = extract_key_phrases(hyde, count=3)
        >>> print(phrases)
        ['lru_cache', 'decorator', 'functools']

    Note:
        The extraction uses heuristics to identify:
        - Quoted terms (highest priority)
        - CamelCase identifiers
        - Abbreviations
        - Snake_case identifiers
        - Technical noun phrases
    """
    return PhraseExtractor.extract(hyde_doc, count, min_length, max_length)


def enhance_query(
    query: str,
    hyde_doc: str | None = None,
    phrase_count: int = 5,
) -> str:
    """Enhance a query with semantic key phrases from a HyDE document.

    This function combines the original query with extracted key phrases
    to create a semantically richer search query.

    Args:
        query: Original search query
        hyde_doc: Optional HyDE document to extract phrases from.
                  If None, returns the original query.
        phrase_count: Number of phrases to extract from the document

    Returns:
        Enhanced query string with additional semantic context

    Example:
        >>> query = "How do I cache results?"
        >>> hyde = generate_hyde(query)
        >>> enhanced = enhance_query(query, hyde)
        >>> print(enhanced)
        "How do I cache results? lru_cache decorator functools memoization"

    Note:
        Duplicate phrases (those already in the query) are filtered out.
    """
    return QueryEnhancer.enhance(query, hyde_doc, phrase_count)


def score_hyde_quality(
    query: str,
    hyde: str,
    weights: dict[str, float] | None = None,
) -> float:
    """Score the quality of a HyDE document relative to the query.

    Computes a relevance score from 0 to 1 based on multiple metrics:
    - Semantic overlap (term overlap between query and document)
    - Length score (appropriate document length)
    - Specificity (presence of specific, non-generic content)
    - Coherence (logical flow indicators)
    - Technical depth (domain-specific terminology)

    Args:
        query: Original search query
        hyde: Generated HyDE document to score
        weights: Optional custom weights for each metric. Default weights:
                 {"semantic_overlap": 0.35, "length_score": 0.15,
                  "specificity": 0.20, "coherence": 0.15, "technical_depth": 0.15}

    Returns:
        Quality score from 0.0 to 1.0, where higher is better

    Example:
        >>> hyde = generate_hyde("What is recursion?")
        >>> score = score_hyde_quality("What is recursion?", hyde)
        >>> print(f"Quality: {score:.2%}")
        Quality: 78.5%

    Note:
        Scores above 0.7 indicate good quality, below 0.4 suggest
        the HyDE document may need improvement.
    """
    metrics = HyDEQualityScorer.score(query, hyde, weights)
    return metrics.overall_score


# Convenience function to get full metrics
def get_detailed_metrics(
    query: str,
    hyde: str,
    weights: dict[str, float] | None = None,
) -> RelevanceMetrics:
    """Get detailed quality metrics for a HyDE document.

    Args:
        query: Original search query
        hyde: Generated HyDE document to score
        weights: Optional custom weights for each metric

    Returns:
        RelevanceMetrics object with individual metric scores

    Example:
        >>> metrics = get_detailed_metrics(query, hyde)
        >>> print(metrics.to_dict())
        {'semantic_overlap': 0.65, 'length_score': 1.0, ...}
    """
    return HyDEQualityScorer.score(query, hyde, weights)
