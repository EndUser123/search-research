#!/usr/bin/env python3
"""
Source Reliability Module for Research CLI

Contradiction Detection: Identifies when sources disagree on the same topic.
This helps users identify conflicting information across multiple sources.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from functools import total_ordering
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """A single research result with metadata."""
    title: str
    url: str
    content: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


@total_ordering
@dataclass
class Contradiction:
    """A detected contradiction between sources."""
    topic: str
    description: str
    sources_conflicting: list[str]
    preferred_source_url: str | None = None
    confidence: float = 0.0

    def __lt__(self, other: Contradiction) -> bool:
        """Sort by confidence, then by topic."""
        if self.confidence != other.confidence:
            return self.confidence < other.confidence
        return self.topic < other.topic


class ContradictionDetector:
    """Detects contradictions between multiple sources."""

    # Patterns that indicate contradictions
    CONTRADICTION_PATTERNS = [
        (r"(only supports?|only|仅支持|目前\s+仅支持|目前\s+仅)", "exclusive_claim"),
        (r"(not supported|unsupported|不支持|cannot|无法)", "negative_claim"),
        (r"(supports?|支持)\s+(both|and|和|or|或)", "inclusive_claim"),
        (r"(currently|目前|at this time)\s+(only|仅|not)", "temporal_claim"),
    ]

    def __init__(self) -> None:
        """Initialize the contradiction detector."""

    def detect_contradictions(
        self,
        results: list[ResearchResult] | list[dict[str, Any]],
        query: str,
    ) -> list[Contradiction]:
        """Detect contradictions between research results.

        Args:
            results: List of research results (as dicts or ResearchResult objects)
            query: Original research query for context

        Returns:
            List of detected contradictions
        """
        # Normalize results
        normalized_results = []
        for r in results:
            if isinstance(r, dict):
                normalized_results.append(ResearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    content=r.get("content", ""),
                    source=r.get("source", "unknown"),
                ))
            else:
                normalized_results.append(r)

        if len(normalized_results) < 2:
            return []

        contradictions = []

        # Compare all pairs of results
        for i, result_a in enumerate(normalized_results):
            for result_b in normalized_results[i + 1:]:
                contradiction = self._compare_results(
                    result_a, result_b, query
                )
                if contradiction:
                    contradictions.append(contradiction)

        # Sort by confidence
        contradictions.sort(reverse=True)
        return contradictions

    def _compare_results(
        self,
        result_a: ResearchResult,
        result_b: ResearchResult,
        query: str,
    ) -> Contradiction | None:
        """Compare two results and detect contradictions.

        Args:
            result_a: First research result
            result_b: Second research result
            query: Original query for context

        Returns:
            Contradiction object if found, None otherwise
        """
        # Check for content-level contradictions and get confidence
        has_contradiction, confidence = self._has_content_contradiction(
            result_a.content, result_b.content, query
        )

        if has_contradiction:
            return Contradiction(
                topic=self._infer_topic(query, result_a.content[:100], result_b.content[:100]),
                description=f"Sources disagree: '{self._truncate(result_a.content)}' vs '{self._truncate(result_b.content)}'",
                sources_conflicting=[result_a.url, result_b.url],
                preferred_source_url=None,
                confidence=confidence,
            )

        return None

    def _has_content_contradiction(
        self,
        content_a: str,
        content_b: str,
        query: str,
    ) -> tuple[bool, float]:
        """Check if two contents have contradictions using semantic patterns.

        Args:
            content_a: First content
            content_b: Second content
            query: Query for context

        Returns:
            Tuple of (has_contradiction, confidence_score)
            Confidence ranges from 0.0 to 1.0
        """
        content_a_lower = content_a.lower()
        content_b_lower = content_b.lower()

        confidence = 0.0

        # Check for direct negation contradictions (boolean opposites) - HIGHEST CONFIDENCE
        positive_indicators = [" supported", " supports", " available", " works", " can ", " enabled", " 是"]
        negative_indicators = [" not supported", " unsupported", " not available", " doesn't work",
                               " cannot", " disabled", " 不支持", " 无法", " 不能"]

        a_positive = any(word in content_a_lower for word in positive_indicators)
        a_negative = any(word in content_a_lower for word in negative_indicators)
        b_positive = any(word in content_b_lower for word in positive_indicators)
        b_negative = any(word in content_b_lower for word in negative_indicators)

        # Direct contradiction: one says positive, other says negative
        if (a_positive and b_negative) or (a_negative and b_positive):
            # Verify they're talking about the same thing
            words_a = set(re.findall(r'\w+', content_a_lower))
            words_b = set(re.findall(r'\w+', content_b_lower))
            common = words_a & words_b

            # Confidence based on how much content overlap
            overlap_ratio = len(common) / max(len(words_a), len(words_b), 1)

            if len(common) >= 2:
                # High confidence for direct negation with good overlap
                confidence = max(confidence, 0.7 + (overlap_ratio * 0.25))
                return True, min(confidence, 1.0)

        # Key terms to look for (case-insensitive matching)
        # Only terms that represent options/features, not conjunctions
        value_terms = ["command", "prompt", "type", "hook", "feature", "option"]

        # Extract quoted values like "command", "prompt", etc.
        quote_pattern = r'["\'`](\w+)["\'`]'
        quotes_a = set(re.findall(quote_pattern, content_a))
        quotes_b = set(re.findall(quote_pattern, content_b))

        # Filter out common non-value words from quotes
        non_values = {"also", "both", "either", "now", "still", "just", "well"}
        quotes_a = {q for q in quotes_a if q not in non_values}
        quotes_b = {q for q in quotes_b if q not in non_values}

        # Also find key terms that appear unquoted
        terms_a = {t for t in value_terms if t in content_a_lower}
        terms_b = {t for t in value_terms if t in content_b_lower}

        # Combine quoted and unquoted key terms
        all_terms_a = quotes_a | terms_a
        all_terms_b = quotes_b | terms_b

        # Check for exclusive/inclusive language patterns - MEDIUM CONFIDENCE
        exclusive_words = ["only", "仅", "仅支持", "merely", "currently only", "目前仅", "目前仅支持"]
        inclusive_words = [" and ", " or ", "plus", "以及", "also supports", "supports both", "both"]

        a_exclusive = any(word in content_a_lower for word in exclusive_words)
        b_exclusive = any(word in content_b_lower for word in exclusive_words)
        a_inclusive = any(word in content_a_lower for word in inclusive_words)
        b_inclusive = any(word in content_b_lower for word in inclusive_words)

        # Find common terms
        common_terms = all_terms_a & all_terms_b

        if common_terms:
            a_multiple = len([t for t in all_terms_a if t in ["command", "prompt", "type"]]) >= 2
            b_multiple = len([t for t in all_terms_b if t in ["command", "prompt", "type"]]) >= 2

            # Contradiction patterns with confidence scoring
            if ((a_exclusive and b_inclusive) or (b_exclusive and a_inclusive)):
                # "only X" vs "X and Y" - medium-high confidence
                confidence = max(confidence, 0.6)
            if (a_exclusive and b_multiple) or (b_exclusive and a_multiple):
                # "only X" vs "X, Y, Z" - high confidence
                confidence = max(confidence, 0.7)
            if (a_exclusive and b_exclusive and all_terms_a != all_terms_b):
                # Both say "only" but about different things - medium confidence
                confidence = max(confidence, 0.5)

            # Different sets of options for the same topic - lower confidence
            # Only trigger if there are actual different option terms, not just different wording
            if all_terms_a != all_terms_b and (a_multiple or b_multiple):
                # Must have at least one quoted value term in each that differs
                quoted_diff_a = quotes_a - quotes_b
                quoted_diff_b = quotes_b - quotes_a
                if quoted_diff_a and quoted_diff_b:
                    confidence = max(confidence, 0.4)

            # Only boost confidence if we already have a contradiction pattern
            if confidence > 0 and len(common_terms) >= 2:
                confidence += 0.1

            if confidence > 0:
                return True, min(confidence, 1.0)

        return False, 0.0

    def _infer_topic(
        self,
        query: str,
        content_a: str,
        content_b: str,
    ) -> str:
        """Infer the topic of contradiction from query and contents.

        Args:
            query: Original query
            content_a: First content snippet
            content_b: Second content snippet

        Returns:
            Inferred topic string
        """
        # Build topic from query words
        query_words = re.findall(r'\w+', query.lower())

        # Filter out specific value words but keep context words
        value_words = {"command", "prompt"}
        topic_words = [w for w in query_words if w not in value_words]

        if topic_words:
            return " ".join(topic_words) + " support"

        return "feature support"

    def _truncate(self, text: str, max_len: int = 50) -> str:
        """Truncate text to max length."""
        if len(text) <= max_len:
            return text
        return text[:max_len] + "..."

    def get_contradiction_summary(
        self,
        contradictions: list[Contradiction],
    ) -> str:
        """Get a human-readable summary of contradictions.

        Args:
            contradictions: List of detected contradictions

        Returns:
            Human-readable summary string
        """
        if not contradictions:
            return "No contradictions detected."

        lines = [f"Detected {len(contradictions)} contradiction(s):"]
        for c in contradictions:
            lines.append(f"  - {c.topic}: {c.description[:80]}...")

        return "\n".join(lines)
