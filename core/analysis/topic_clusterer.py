"""Topic clustering and novelty tracking for saturation detection."""

from collections import Counter
from dataclasses import dataclass, field
from hashlib import sha256
from re import findall
from typing import Any


@dataclass
class TopicSignature:
    """Topic signature with hash-based identity."""
    topic_id: str
    keyword_hash: int
    keywords: set[str]
    result_ids: set[str] = field(default_factory=set)


@dataclass
class CoverageState:
    """Coverage state for novelty computation."""
    topics: set[str] = field(default_factory=set)
    source_types: set[str] = field(default_factory=set)
    domains: set[str] = field(default_factory=set)
    claim_terms: set[str] = field(default_factory=set)


class TopicClusterer:
    """Hash-based topic clustering for fast grouping."""

    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
        "be", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "this", "that", "these",
        "those", "it", "its", "get", "use", "make", "when", "what", "how",
        "all", "each", "more", "some", "such", "only", "own", "same", "so",
        "than", "too", "very", "just", "also", "now", "new", "first", "last",
        "into"
    }

    def __init__(self) -> None:
        self.topics: dict[str, TopicSignature] = {}

    def extract_keywords(self, text: str, top_n: int = 6) -> set[str]:
        """Extract top keywords from text."""
        words = findall(r'\b[a-z]{3,}\b', text.lower())
        words = [w for w in words if w not in self.STOPWORDS]
        freq = Counter(words)
        return set(word for word, _ in freq.most_common(top_n))

    def _compute_keyword_hash(self, keywords: set[str]) -> int:
        """Compute hash of sorted keywords for topic identity."""
        sorted_keys = tuple(sorted(keywords))
        hash_input = "|".join(sorted_keys).encode()
        return int(sha256(hash_input).hexdigest(), 16)

    def cluster_results(self, results: Any) -> dict[str, TopicSignature]:
        """Cluster results by topic keywords."""
        self.topics.clear()

        for result in results:
            # Combine title and snippet for keyword extraction
            text = f"{result.title} {result.snippet}"
            keywords = self.extract_keywords(text)

            if not keywords:
                continue

            keyword_hash = self._compute_keyword_hash(keywords)
            topic_id = f"topic_{keyword_hash:x}"

            # Create or update topic signature
            if topic_id not in self.topics:
                self.topics[topic_id] = TopicSignature(
                    topic_id=topic_id,
                    keyword_hash=keyword_hash,
                    keywords=keywords
                )

            # Track result in topic (use URL or index as ID)
            result_id = getattr(result, "url", str(id(result)))
            self.topics[topic_id].result_ids.add(result_id)

        return self.topics


class NoveltyTracker:
    """Track novelty and detect saturation."""

    def __init__(self, novelty_threshold: float = 0.05):
        self.novelty_threshold = novelty_threshold
        self._iteration_count = 0
        self._low_novelty_streak = 0
        self._previous_state: CoverageState | None = None

    def compute_coverage_state(
        self,
        results: Any,
        clusters: dict[str, TopicSignature]
    ) -> CoverageState:
        """Compute coverage state from results and clusters."""
        source_types = set()
        domains = set()
        claim_terms = set()

        for result in results:
            source_type = getattr(result, "source_type", "unknown")
            domain = getattr(result, "domain", "")
            snippet = getattr(result, "snippet", "")

            source_types.add(str(source_type))
            if domain:
                domains.add(domain)
            # Extract claim terms from snippet (simple word extraction)
            claim_terms.update(self.extract_keywords(snippet))

        topics = set(clusters.keys())

        return CoverageState(
            topics=topics,
            source_types=source_types,
            domains=domains,
            claim_terms=claim_terms
        )

    def extract_keywords(self, text: str, top_n: int = 6) -> set[str]:
        """Extract keywords for claim term tracking."""
        words = findall(r'\b[a-z]{3,}\b', text.lower())
        words = [w for w in words if w not in TopicClusterer.STOPWORDS]
        freq = Counter(words)
        return set(word for word, _ in freq.most_common(top_n))

    def compute_novelty(
        self,
        current: CoverageState,
        previous: CoverageState
    ) -> float:
        """Compute novelty score (0-1)."""
        if previous is None:
            return 1.0

        new_topics = len(current.topics - previous.topics)
        new_sources = len(current.source_types - previous.source_types)
        new_domains = len(current.domains - previous.domains)
        new_terms = len(current.claim_terms - previous.claim_terms)

        # Weighted novelty formula
        topic_novelty = 0.4 * (new_topics / max(1, len(current.topics)))
        source_novelty = 0.2 * (new_sources / 5)
        domain_novelty = 0.2 * (new_domains / 10)
        term_novelty = 0.2 * (new_terms / 40)

        return min(1.0, topic_novelty + source_novelty + domain_novelty + term_novelty)

    def should_continue(self, current_state: CoverageState) -> bool:
        """Determine if research should continue based on novelty."""
        self._iteration_count += 1

        if self._iteration_count == 1:
            self._previous_state = current_state
            self._low_novelty_streak = 0
            return True

        if self._previous_state is None:
            self._previous_state = current_state
            return True

        novelty = self.compute_novelty(current_state, self._previous_state)
        self._previous_state = current_state

        if novelty < self.novelty_threshold:
            self._low_novelty_streak += 1
        else:
            self._low_novelty_streak = 0

        return self._low_novelty_streak < 2
