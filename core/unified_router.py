"""Unified async router combining local and web search.

This module provides the UnifiedAsyncRouter class that intelligently combines
fast local search with comprehensive web search based on configurable modes:

- local-only: Only search local backends, never web
- auto: Use quality checks to determine if web search is needed
- web-fallback: Always check quality, search web if local results are poor
- unified: Always search both local and web, merge with RRF

The router implements progressive enhancement: fast local results are returned
immediately if they meet quality thresholds, avoiding expensive web searches
when not needed.

Architecture:
    Phase 1: Fast local search (<1s)
    Phase 2: Quality check (configurable thresholds)
    Phase 3: Web search (only if needed, 5-10s)
    Phase 4: RRF fusion (merge local + web results)

Example:
    >>> from core.unified_router import UnifiedAsyncRouter
    >>> router = UnifiedAsyncRouter(mode="auto")
    >>> results = await router.search_async("FastAPI patterns", limit=10)
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
import functools
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .hybrid_ensemble import reciprocal_rank_fusion
from .models import SearchResult  # CANONICAL import (Q-ARCH-001 fix)
from .quality_checker import QualityConfig, is_satisfactory, _check_freshness
from .router_async import AsyncSearchRouter

logger = logging.getLogger(__name__)

#: Maximum result content length for TF-IDF computation (bytes).
#: Prevents memory exhaustion from very large results.
MAX_RESULT_CONTENT_LENGTH: int = 10000

#: Default topic alignment threshold for TF-IDF cosine similarity.
#: Results with score <= this threshold are marked as topic-misaligned.
DEFAULT_TOPIC_ALIGNMENT_THRESHOLD: float = 0.15


class UnifiedAsyncRouter:
    """Unified async router combining local and web search with intelligent routing.

    Provides adaptive search behavior based on mode configuration:
    - local-only: Fast local search only, never calls web APIs
    - auto: Progressive enhancement via quality checks
    - web-fallback: Always check quality, fall back to web if needed
    - unified: Comprehensive search merging both sources with RRF

    Attributes:
        mode: Routing mode (auto, local-only, web-fallback, unified)
        enable_jmri: Enable jMRI token-efficient retrieval for local search
        rrf_k: RRF constant for result fusion (default: 60)
        quality_config: Quality thresholds for progressive enhancement

    Example:
        >>> router = UnifiedAsyncRouter(mode="auto", rrf_k=80)
        >>> results = await router.search_async("FastAPI patterns", limit=10)
    """

    def __init__(
        self,
        mode: str = "auto",
        enable_jmri: bool = True,
        rrf_k: int = 60,
        quality_config: QualityConfig | None = None,
        local_router: AsyncSearchRouter | None = None,
        web_router: AsyncSearchRouter | None = None,
        topic_alignment_threshold: float = DEFAULT_TOPIC_ALIGNMENT_THRESHOLD,
    ):
        """Initialize unified async router.

        Args:
            mode: Routing mode (auto, local-only, web-fallback, unified)
            enable_jmri: Enable jMRI token-efficient retrieval (default: True)
            rrf_k: RRF constant for result fusion (default: 60)
            quality_config: Quality thresholds (uses defaults if None)
            local_router: Optional injected local search router (for testing)
            web_router: Optional injected web search router (for testing)
            topic_alignment_threshold: Minimum TF-IDF cosine similarity for
                topic alignment [0.0, 1.0]. Results with score <= this threshold
                are marked as topic-misaligned in metadata. Default: 0.15

        Raises:
            ValueError: If mode is not one of the valid modes
            ValueError: If topic_alignment_threshold is outside [0.0, 1.0]
        """
        valid_modes = ["auto", "local-only", "web-fallback", "unified"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}")

        if not (0.0 <= topic_alignment_threshold <= 1.0):
            raise ValueError(
                f"topic_alignment_threshold must satisfy 0.0 <= {topic_alignment_threshold} <= 1.0"
            )

        self.mode = mode
        self.enable_jmri = enable_jmri
        self.rrf_k = rrf_k
        self.quality_config = quality_config or QualityConfig()
        self.topic_alignment_threshold = topic_alignment_threshold

        # Use injected routers if provided, otherwise create lazily
        self._async_local_router: AsyncSearchRouter | None = local_router
        self._web_router: AsyncSearchRouter | None = web_router

    @property
    def _backends(self) -> dict[str, Any]:
        """Get backends from the local router (backward compatibility).

        This property provides access to the underlying backends dictionary
        for tests that need to mock or inspect backends directly.

        Returns:
            Dictionary mapping backend names to backend instances
        """
        return self._local_router._backends

    @_backends.setter
    def _backends(self, value: dict[str, Any]) -> None:
        """Set backends on the local router (backward compatibility).

        This setter allows tests to modify the underlying backends dictionary
        for testing failure scenarios.

        Args:
            value: Dictionary mapping backend names to backend instances
        """
        self._local_router._backends = value

    @property
    def _local_router(self) -> AsyncSearchRouter:
        """Get or create the local search router."""
        if self._async_local_router is None:
            self._async_local_router = AsyncSearchRouter(enable_jmri=self.enable_jmri)
        return self._async_local_router

    @property
    def _web_router_property(self) -> AsyncSearchRouter | None:
        """Get or create the web search router.

        Returns None if web router is not available (e.g., no API keys configured).
        Tests can inject a mock router via __init__ to test web search behavior.
        """
        if self._web_router is None:
            try:
                self._web_router = AsyncSearchRouter(enable_jmri=self.enable_jmri)
                logger.debug("Web search router initialized")
            except Exception as e:
                logger.debug(f"Web search router not available: {e}")
                self._web_router = None
        return self._web_router

    # English stopwords for TF-IDF tokenization
    _STOPWORDS: frozenset[str] = frozenset(
        {
            "i",
            "me",
            "my",
            "myself",
            "we",
            "our",
            "ours",
            "ourselves",
            "you",
            "your",
            "yours",
            "yourself",
            "yourselves",
            "he",
            "him",
            "his",
            "himself",
            "she",
            "her",
            "hers",
            "herself",
            "it",
            "its",
            "itself",
            "they",
            "them",
            "their",
            "theirs",
            "themselves",
            "what",
            "which",
            "who",
            "whom",
            "this",
            "that",
            "these",
            "those",
            "am",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "having",
            "do",
            "does",
            "did",
            "doing",
            "a",
            "an",
            "the",
            "and",
            "but",
            "if",
            "or",
            "because",
            "as",
            "until",
            "while",
            "of",
            "at",
            "by",
            "for",
            "with",
            "about",
            "against",
            "between",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "to",
            "from",
            "up",
            "down",
            "in",
            "out",
            "on",
            "off",
            "over",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "s",
            "t",
            "can",
            "will",
            "just",
            "don",
            "should",
            "now",
        }
    )

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text using word-boundary splitting, lowercased."""
        tokens = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
        return [t for t in tokens if t not in self._STOPWORDS and len(t) > 1]

    @functools.lru_cache(maxsize=256)
    def _compute_tfidf_similarity(self, query: str, result_text: str) -> float:
        """Compute TF-IDF cosine similarity between query and result text."""
        if not result_text or not result_text.strip():
            return 0.0
        if len(result_text) > MAX_RESULT_CONTENT_LENGTH:
            return 0.0
        try:
            query_tokens = self._tokenize(query)
            result_tokens = self._tokenize(result_text)
            if not query_tokens or not result_tokens:
                return 0.0

            vocabulary = set(query_tokens) | set(result_tokens)
            vocab_list = sorted(vocabulary)
            vocab_index = {term: i for i, term in enumerate(vocab_list)}
            n = len(vocab_list)
            if n == 0:
                return 0.0

            query_tf = Counter(query_tokens)
            result_tf = Counter(result_tokens)

            df = {}
            for term in vocabulary:
                d = 0
                if term in query_tf:
                    d += 1
                if term in result_tf:
                    d += 1
                df[term] = d

            N = 2
            idf = {}
            for term in vocabulary:
                d = df[term]
                idf[term] = math.log((N + 1) / (d + 1)) + 1

            query_vec = [0.0] * n
            result_vec = [0.0] * n
            for term, count in query_tf.items():
                idx = vocab_index.get(term)
                if idx is not None:
                    tf_norm = 1 + math.log(count) if count > 0 else 0
                    query_vec[idx] = tf_norm * idf[term]
            for term, count in result_tf.items():
                idx = vocab_index.get(term)
                if idx is not None:
                    tf_norm = 1 + math.log(count) if count > 0 else 0
                    result_vec[idx] = tf_norm * idf[term]

            dot_product = sum(q * r for q, r in zip(query_vec, result_vec, strict=True))
            query_norm = math.sqrt(sum(v * v for v in query_vec))
            result_norm = math.sqrt(sum(v * v for v in result_vec))
            if query_norm == 0.0 or result_norm == 0.0:
                return 0.0
            cosine = dot_product / (query_norm * result_norm)
            return max(0.0, min(1.0, cosine))
        except Exception:
            return 0.0

    def _add_topic_alignment_scores(
        self, query: str, results: list[SearchResult]
    ) -> list[SearchResult]:
        """Add topic alignment scores to result metadata."""
        for result in results:
            content = result.content or ""
            score = self._compute_tfidf_similarity(query, content)
            result.metadata["topic_alignment_score"] = score
        return results

    async def search_async(
        self,
        query: str,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search with intelligent routing based on mode.

        Implements progressive enhancement:
        1. Fast local search (<1s)
        2. Quality check to determine if web search is needed
        3. Web search only if quality check fails (5-10s)
        4. RRF fusion to merge results

        Args:
            query: Search query
            limit: Maximum number of results to return (default: 10)

        Returns:
            List of search results ranked by relevance

        Raises:
            ValueError: If query is empty or contains only whitespace
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Conceptual query → semantic session search
        if self._is_conceptual_query(query):
            semantic_results = await self._search_chs_semantic(query, limit=limit)
            if semantic_results:
                return self._add_topic_alignment_scores(query, semantic_results)

        # Phase 1: Fast local search with error handling
        try:
            local_results = await self._local_router.search_async(query, limit=limit * 2)
        except Exception as e:
            logger.debug(f"Local search failed: {e}. Returning empty results.")
            local_results = []

        # Phase 2: Quality check (skip web if satisfied)
        if self._should_skip_web_search(local_results, query):
            return self._add_topic_alignment_scores(query, local_results[:limit])

        # Phase 3: Web search (only if needed)
        web_router = self._web_router_property
        if web_router:
            try:
                web_results = await web_router.search_web_providers_async(query, limit=limit)

                # Phase 4: RRF fusion
                merged_results = self._merge_results_with_rrf(local_results, web_results)
                return self._add_topic_alignment_scores(query, merged_results[:limit])
            except Exception as e:
                logger.debug(f"Web search failed: {e}. Returning local results only.")

        return self._add_topic_alignment_scores(query, local_results[:limit])

    def _should_skip_web_search(self, local_results: list[SearchResult], query: str | None = None) -> bool:
        """Determine if web search should be skipped based on mode, intent, and quality.

        Query-type awareness (when query is provided):
        - Time-sensitive signals (year, "latest", "current", "release", dates) →
          always check web; local knowledge is likely stale.
        - Factual-lookup intent (UNKNOWN) → check web; the corpus may not contain it.
        - NAVIGATIONAL/TECHNICAL/EXPLORATORY → defer to the quality gate; these
          are usually answerable from local code/knowledge.
        - INFORMATIONAL → defer to quality gate with freshness bias.

        Args:
            local_results: Results from local search
            query: The original search query (enables intent-aware gating)

        Returns:
            True if web search should be skipped, False otherwise
        """
        # local-only mode: never search web
        if self.mode == "local-only":
            return True

        # unified mode: always search web (don't skip)
        if self.mode == "unified":
            return False

        # auto and web-fallback modes: check quality
        # If no local results, web search is needed
        if not local_results:
            return False

        # Intent-aware web gating (when query is provided). Mirrors the intent
        # filter: some query types should always check web regardless of local
        # quality, because the right answer isn't in — or is stale in — the
        # local corpus.
        if query:
            skip, reason = self._intent_web_policy(query)
            if skip is not None:
                logger.debug(f"Intent web policy for {query!r}: {reason}")
                return skip

        # Check if best local result meets quality thresholds
        best_result = local_results[0]
        result_dict = self._search_result_to_dict(best_result)
        quality_result = is_satisfactory(result_dict, self.quality_config)
        logger.debug(
            f"Quality check for '{best_result.title}': "
            f"score={result_dict.get('confidence', 'N/A')}, "
            f"satisfactory={quality_result}"
        )
        # FM-4 telemetry: record the is_satisfactory verdict for the soak.
        # Non-blocking; joined to the intent_filter record by query_hash.
        if query:
            try:
                from .query_telemetry import hash_query, log_quality_check
                sources = result_dict.get("sources") or []
                log_quality_check(
                    query_hash=hash_query(query),
                    satisfactory=bool(quality_result),
                    confidence=float(result_dict.get("confidence", 0.0) or 0.0),
                    backend_diversity=len(set(sources)),
                    fresh=bool(_check_freshness(result_dict, self.quality_config)),
                )
            except Exception:
                pass
        return quality_result

    @staticmethod
    def _intent_web_policy(query: str) -> tuple[bool | None, str]:
        """Classify query intent and return a web-search policy.

        Returns (skip, reason):
        - skip=True  -> skip web (query is answerable locally)
        - skip=False -> force web (query needs fresh/external info)
        - skip=None  -> defer to the quality gate (no intent-level override)
        """
        q = query.lower()
        time_sensitive = bool(re.search(
            r"(20\d{2})"
            r"|latest|current|newest|recent"
            r"|release|released|version|v\d"
            r"|changelog|roadmap"
            r"|today|yesterday|this week|this month",
            q,
        ))
        if time_sensitive:
            return False, "time-sensitive signal -> force web"
        try:
            from .query_intent import classify_query_intent, IntentType
            result = classify_query_intent(query)
            if result.intent == IntentType.UNKNOWN:
                return False, "UNKNOWN intent -> force web"
            return None, f"{result.intent.value} intent -> quality gate"
        except Exception:
            return None, "classifier unavailable -> quality gate"

    @staticmethod
    def _is_conceptual_query(query: str) -> bool:
        """Detect if query wants semantic (conceptual) vs keyword search."""
        conceptual_patterns = [
            r"what (did|do|did we|we) discuss",
            r"what did we decide",
            r"how did we handle",
            r"remember",
            r"patterns?",
            r"approach",
        ]
        query_lower = query.lower()
        return any(re.search(p, query_lower) for p in conceptual_patterns)

    async def _search_chs_semantic(self, query: str, limit: int) -> list[SearchResult]:
        """Route to CHS semantic search using session embeddings."""
        from core.chs.db import get_connection
        from core.chs.embeddings import get_embed_client
        from core.chs.search import search_semantic_sessions

        try:
            embed_client = get_embed_client()
            db = get_connection(Path("P:/.data/chat_history.db"))
            # Run sync function in thread pool with 10s timeout to avoid blocking local backends
            sessions = await asyncio.wait_for(
                asyncio.to_thread(search_semantic_sessions, db, query, embed_client, limit),
                timeout=10.0,
            )
            results = []
            for s in sessions:
                results.append(SearchResult(
                    id=str(s["session_id"]),
                    title=(s["first_prompt"] or "Untitled")[:80],
                    content=s["summary_short"] or "",
                    score=s["score"],
                    source="chs_semantic",
                ))
            return results
        except asyncio.TimeoutError:
            logger.debug("CHS semantic search timed out after 10s, falling back to local")
            return []
        except Exception as e:
            logger.debug(f"CHS semantic search failed: {e}")
            return []

    def _merge_results_with_rrf(
        self,
        local_results: list[SearchResult],
        web_results: list[SearchResult],
    ) -> list[SearchResult]:
        """Merge local and web results using Reciprocal Rank Fusion.

        Args:
            local_results: Results from local search
            web_results: Results from web search

        Returns:
            Merged and ranked results
        """
        try:
            merged = reciprocal_rank_fusion(
                [local_results, web_results],
                k=self.rrf_k,
            )
            return merged
        except Exception as e:
            logger.debug(f"RRF fusion failed: {e}. Returning local results only.")
            return local_results

    def _search_result_to_dict(self, result: SearchResult) -> dict[str, Any]:
        """Convert SearchResult to dictionary format for quality checking.

        Produces fields expected by quality_checker.is_satisfactory():
        - confidence: mapped from result.score (relevance score)
        - sources: wrapped list from result.source (single backend name)
        - created_at: result timestamp for freshness check

        Args:
            result: SearchResult object

        Returns:
            Dictionary representation with quality checker compatible fields
        """
        return {
            "id": result.metadata.get("id", f"{result.source}-{result.title}"),
            "title": result.title,
            "content": result.content,
            "score": result.score,
            "confidence": result.score,
            "source": result.source,
            "sources": [result.source] if result.source else [],
            "url": result.url,
            "file_path": result.file_path,
            "line_number": result.line_number,
            "metadata": result.metadata,
            "created_at": result.created_at or datetime.now(timezone.utc),
        }
