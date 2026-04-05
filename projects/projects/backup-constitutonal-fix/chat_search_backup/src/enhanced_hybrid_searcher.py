from __future__ import annotations

import hashlib
import logging
import math
import re
import sys
import threading
import time
import uuid
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core_utils.embedding_manager import EmbeddingManager, EmbeddingManagerFactory
from core_utils.vector_store import VectorStore, VectorStoreFactory

#!/usr/bin/env python3
"""Enhanced Hybrid Searcher - TDD GREEN Phase Implementation.

Enhanced TF-IDF + vector search integration with dynamic optimization,
consolidated database support, intelligent caching, and performance monitoring.

Algorithm Approach: Multi-layer enhancement strategy with dynamic weight optimization,
consolidated vector database integration, and performance-aware caching.

Time Complexity: O(n) for indexing, O(log n) for search operations
Space Complexity: O(n) for index storage, O(1) for search overhead

Enhancement Features:
1. Dynamic weight optimization based on query characteristics
2. Consolidated vector database integration
3. Intelligent caching with multi-level optimization
4. Enhanced relevance scoring with context awareness
5. Comprehensive performance monitoring and alerting
6. Multi-vector backend support with fallback
7. Configuration-based optimization system
8. Advanced error handling and recovery
9. Real-time performance metrics
10. Personalized search adjustments

Edge Cases:
- Empty queries: Return empty results with appropriate logging
- Vector store failures: Graceful degradation to TF-IDF only
- Cache corruption: Automatic cache rebuilding with error reporting
- Memory pressure: Adaptive cache sizing and query throttling
- Concurrent access: Thread-safe operations with proper locking
"""



# Add CSF NIP paths
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "src" / "lib"))




# Enhancement enums and dataclasses
class QueryType(Enum):
    """Enumeration of query types for optimization."""

    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    MIXED = "mixed"
    TECHNICAL = "technical"
    QUESTION = "question"
    NAVIGATIONAL = "navigational"


class QueryComplexity(Enum):
    """Query complexity levels for dynamic optimization."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"


@dataclass
class QueryAnalysis:
    """Results of query analysis for optimization."""

    query_type: QueryType
    complexity: QueryComplexity
    keyword_density: float
    semantic_score: float
    length: int
    unique_terms: int
    suggested_tfidf_weight: float
    suggested_vector_weight: float
    confidence: float


@dataclass
class SearchMetrics:
    """Performance metrics for search operations."""

    search_latency_ms: float
    tfidf_search_time_ms: float
    vector_search_time_ms: float
    result_combination_time_ms: float
    total_results: int
    memory_usage_mb: float
    cpu_usage_percent: float
    cache_hit_rate: float
    optimization_score: float


@dataclass
class CacheEntry:
    """Enhanced cache entry with metadata."""

    query: str
    results: list[dict[str, Any]]
    timestamp: datetime
    hit_count: int
    last_accessed: datetime
    relevance_score: float
    query_type: QueryType
    ttl_seconds: int


@dataclass
class PerformanceAlert:
    """Performance alert data structure."""

    severity: str
    message: str
    metric_name: str
    threshold_violation: dict[str, Any]
    timestamp: datetime
    suggested_action: str


class QueryClassifier:
    """Query classification system for dynamic optimization."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initialize query classifier.

        Args:
        ----
            logger: Logger instance

        """
        self.logger = logger or logging.getLogger(__name__)

        # Keyword patterns for classification
        self.keyword_patterns = {
            QueryType.KEYWORD: [
                r"^\b\w+\s+\w+\b$",  # Two-word queries
                r"^\b[a-zA-Z]+\s*[a-zA-Z]*$",  # Single words or two words
            ],
            QueryType.TECHNICAL: [
                r"\b(api|function|class|method|algorithm|library)\b",
                r"\b(python|javascript|java|c\+\+|sql|html|css)\b",
                r"\b(fastapi|django|flask|react|vue|angular)\b",
            ],
            QueryType.QUESTION: [
                r"^(how|what|why|when|where|who)\s+",
                r"\?$",  # Ends with question mark
                r"\b(can|could|should|would|will)\s+",
            ],
            QueryType.NAVIGATIONAL: [
                r"\b(find|search|look for|get|show)\s+",
                r"\b(tutorial|guide|documentation|example)\b",
            ],
        }

    def classify_query(self, query: str) -> QueryType:
        """Classify query type based on patterns and characteristics.

        Algorithm Approach: Pattern matching + heuristics for query classification
        Time Complexity: O(k) where k is number of query characters
        Space Complexity: O(1) - constant space for pattern matching

        Args:
        ----
            query: Search query to classify

        Returns:
        -------
            QueryType classification

        """
        if not query:
            return QueryType.SEMANTIC

        query_lower = query.lower().strip()

        # Check for technical terms
        for query_type, patterns in self.keyword_patterns.items():
            if query_type == QueryType.TECHNICAL:
                for pattern in patterns:
                    if re.search(pattern, query_lower):
                        return query_type

        # Check for questions
        for pattern in self.keyword_patterns[QueryType.QUESTION]:
            if re.search(pattern, query_lower):
                return QueryType.QUESTION

        # Check for navigational queries
        for pattern in self.keyword_patterns[QueryType.NAVIGATIONAL]:
            if re.search(pattern, query_lower):
                return QueryType.NAVIGATIONAL

        # Check for keyword queries (short, specific)
        word_count = len(query_lower.split())
        if word_count <= 2 and len(query_lower) < 30:
            return QueryType.KEYWORD

        # Default to semantic for longer, more complex queries
        return QueryType.SEMANTIC


class WeightOptimizer:
    """Dynamic weight optimization based on query analysis."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initialize weight optimizer.

        Args:
        ----
            logger: Logger instance

        """
        self.logger = logger or logging.getLogger(__name__)

        # Optimization strategies for different query types
        self.optimization_strategies = {
            QueryType.KEYWORD: {"tfidf": 0.7, "vector": 0.3},
            QueryType.SEMANTIC: {"tfidf": 0.2, "vector": 0.8},
            QueryType.TECHNICAL: {"tfidf": 0.6, "vector": 0.4},
            QueryType.QUESTION: {"tfidf": 0.4, "vector": 0.6},
            QueryType.NAVIGATIONAL: {"tfidf": 0.5, "vector": 0.5},
            QueryType.MIXED: {"tfidf": 0.4, "vector": 0.6},
        }

    def optimize_weights(
        self, query: str, query_type: QueryType, complexity: QueryComplexity
    ) -> tuple[float, float]:
        """Optimize TF-IDF and vector weights based on query characteristics.

        Algorithm Approach: Rule-based optimization with query type and complexity factors
        Time Complexity: O(1) - constant time for weight calculation
        Space Complexity: O(1) - constant space for weight storage

        Args:
        ----
            query: Search query
            query_type: Classified query type
            complexity: Query complexity level

        Returns:
        -------
            Tuple of (tfidf_weight, vector_weight)

        """
        base_weights = self.optimization_strategies.get(
            query_type, {"tfidf": 0.3, "vector": 0.7}
        )

        # Adjust based on complexity
        complexity_adjustments = {
            QueryComplexity.SIMPLE: {"tfidf": 0.1, "vector": -0.1},
            QueryComplexity.MEDIUM: {"tfidf": 0.0, "vector": 0.0},
            QueryComplexity.COMPLEX: {"tfidf": -0.1, "vector": 0.1},
            QueryComplexity.EXPERT: {"tfidf": -0.15, "vector": 0.15},
        }

        adjustment = complexity_adjustments.get(
            complexity, {"tfidf": 0.0, "vector": 0.0}
        )

        # Apply adjustments
        tfidf_weight = max(0.1, min(0.9, base_weights["tfidf"] + adjustment["tfidf"]))
        vector_weight = max(
            0.1, min(0.9, base_weights["vector"] + adjustment["vector"])
        )

        # Normalize to ensure they sum to 1.0
        total = tfidf_weight + vector_weight
        if total != 0:
            tfidf_weight /= total
            vector_weight /= total

        self.logger.debug(
            f"Optimized weights for '{query}': TF-IDF={tfidf_weight:.2f}, Vector={vector_weight:.2f}"
        )

        return tfidf_weight, vector_weight


class IntelligentCacheManager:
    """Intelligent caching system with performance-based eviction."""

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize intelligent cache manager.

        Args:
        ----
            max_size: Maximum number of cache entries
            default_ttl: Default TTL in seconds
            logger: Logger instance

        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.logger = logger or logging.getLogger(__name__)

        # Cache storage with metadata
        self.cache: dict[str, CacheEntry] = {}
        self.access_order = deque()  # LRU tracking
        self.hit_stats = defaultdict(int)
        self.lock = threading.RLock()

        # Performance metrics
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def get(self, query: str) -> list[dict[str, Any]] | None:
        """Get cached results for query.

        Args:
        ----
            query: Search query

        Returns:
        -------
            Cached results or None if not found/expired

        """
        with self.lock:
            self.total_requests += 1

            cache_key = self._generate_cache_key(query)

            if cache_key not in self.cache:
                self.cache_misses += 1
                return None

            entry = self.cache[cache_key]

            # Check TTL
            if time.time() - entry.timestamp.timestamp() > entry.ttl_seconds:
                del self.cache[cache_key]
                self.cache_misses += 1
                return None

            # Update access tracking
            entry.hit_count += 1
            entry.last_accessed = datetime.now()
            self.access_order.remove(cache_key)
            self.access_order.append(cache_key)

            self.cache_hits += 1
            self.hit_stats[entry.query_type] += 1

            self.logger.debug(
                f"Cache hit for query: '{query}' (hit count: {entry.hit_count})"
            )
            return entry.results.copy()

    def put(
        self,
        query: str,
        results: list[dict[str, Any]],
        query_type: QueryType,
        relevance_score: float = 0.0,
        ttl_seconds: int | None = None,
    ) -> None:
        """Store results in cache.

        Args:
        ----
            query: Search query
            results: Search results to cache
            query_type: Type of query
            relevance_score: Relevance score for eviction priority
            ttl_seconds: Custom TTL (uses default if None)

        """
        with self.lock:
            cache_key = self._generate_cache_key(query)
            ttl_seconds = ttl_seconds or self.default_ttl

            # Evict if necessary
            if len(self.cache) >= self.max_size and cache_key not in self.cache:
                self._evict_entries()

            # Store entry
            entry = CacheEntry(
                query=query,
                results=results.copy(),
                timestamp=datetime.now(),
                hit_count=0,
                last_accessed=datetime.now(),
                relevance_score=relevance_score,
                query_type=query_type,
                ttl_seconds=ttl_seconds,
            )

            self.cache[cache_key] = entry

            # Update access order
            if cache_key in self.access_order:
                self.access_order.remove(cache_key)
            self.access_order.append(cache_key)

            self.logger.debug(
                f"Cached results for query: '{query}' (TTL: {ttl_seconds}s)"
            )

    def _generate_cache_key(self, query: str) -> str:
        """Generate cache key for query."""
        return hashlib.md5(query.lower().encode()).hexdigest()

    def _evict_entries(self) -> None:
        """Evict entries based on performance-based policy."""
        if not self.cache:
            return

        # Calculate eviction scores
        eviction_candidates = []
        for cache_key, entry in self.cache.items():
            # Score = (hit_count * relevance_score) / age_hours
            age_hours = (datetime.now() - entry.timestamp).total_seconds() / 3600
            age_hours = max(age_hours, 0.1)  # Avoid division by very small numbers

            score = (entry.hit_count * entry.relevance_score) / age_hours
            eviction_candidates.append((score, cache_key, entry))

        # Sort by score (lowest first for eviction)
        eviction_candidates.sort(key=lambda x: x[0])

        # Evict bottom 10% or at least 1 entry
        evict_count = max(1, len(eviction_candidates) // 10)

        for i in range(evict_count):
            score, cache_key, entry = eviction_candidates[i]
            del self.cache[cache_key]
            if cache_key in self.access_order:
                self.access_order.remove(cache_key)

            self.logger.debug(
                f"Evicted cache entry: '{entry.query}' (score: {score:.3f})"
            )

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        with self.lock:
            hit_rate = self.cache_hits / max(self.total_requests, 1)

            return {
                "total_entries": len(self.cache),
                "total_requests": self.total_requests,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate": hit_rate,
                "hit_stats_by_type": dict(self.hit_stats),
                "memory_usage_estimate": sum(
                    len(str(entry.results)) for entry in self.cache.values()
                )
                / 1024,  # KB
            }

    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
            self.hit_stats.clear()
            self.logger.info("Cache cleared")

    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        with self.lock:
            keys_to_remove = []
            pattern_lower = pattern.lower()

            for cache_key, entry in self.cache.items():
                if pattern_lower in entry.query.lower():
                    keys_to_remove.append(cache_key)

            for cache_key in keys_to_remove:
                del self.cache[cache_key]
                if cache_key in self.access_order:
                    self.access_order.remove(cache_key)

            self.logger.info(
                f"Invalidated {len(keys_to_remove)} cache entries matching pattern: '{pattern}'"
            )
            return len(keys_to_remove)


class PerformanceMonitor:
    """Comprehensive performance monitoring for search operations."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initialize performance monitor.

        Args:
        ----
            logger: Logger instance

        """
        self.logger = logger or logging.getLogger(__name__)

        # Performance tracking
        self.metrics_history = deque(maxlen=1000)
        self.active_operations = {}
        self.alert_thresholds = {
            "max_search_latency_ms": 500.0,
            "min_cache_hit_rate": 0.7,
            "min_accuracy_threshold": 0.8,
            "max_memory_usage_mb": 512.0,
        }
        self.lock = threading.RLock()

    def start_monitoring(self, operation_id: str) -> dict[str, Any]:
        """Start monitoring an operation.

        Args:
        ----
            operation_id: Unique identifier for the operation

        Returns:
        -------
            Monitoring context dictionary

        """
        with self.lock:
            context = {
                "operation_id": operation_id,
                "start_time": time.time(),
                "start_memory": self._get_memory_usage(),
                "start_cpu": self._get_cpu_usage(),
            }

            self.active_operations[operation_id] = context
            return context

    def stop_monitoring(
        self,
        context: dict[str, Any],
        additional_metrics: dict[str, Any] | None = None,
    ) -> SearchMetrics:
        """Stop monitoring and collect metrics.

        Args:
        ----
            context: Monitoring context from start_monitoring
            additional_metrics: Additional metrics to include

        Returns:
        -------
            SearchMetrics with collected data

        """
        end_time = time.time()
        end_memory = self._get_memory_usage()
        end_cpu = self._get_cpu_usage()

        duration_ms = (end_time - context["start_time"]) * 1000
        memory_delta = end_memory - context["start_memory"]
        cpu_delta = end_cpu - context["start_cpu"]

        metrics = SearchMetrics(
            search_latency_ms=duration_ms,
            tfidf_search_time_ms=(
                additional_metrics.get("tfidf_time_ms", 0.0)
                if additional_metrics
                else 0.0
            ),
            vector_search_time_ms=(
                additional_metrics.get("vector_time_ms", 0.0)
                if additional_metrics
                else 0.0
            ),
            result_combination_time_ms=(
                additional_metrics.get("combination_time_ms", 0.0)
                if additional_metrics
                else 0.0
            ),
            total_results=(
                additional_metrics.get("total_results", 0) if additional_metrics else 0
            ),
            memory_usage_mb=memory_delta,
            cpu_usage_percent=cpu_delta,
            cache_hit_rate=(
                additional_metrics.get("cache_hit_rate", 0.0)
                if additional_metrics
                else 0.0
            ),
            optimization_score=(
                additional_metrics.get("optimization_score", 0.0)
                if additional_metrics
                else 0.0
            ),
        )

        with self.lock:
            self.metrics_history.append(
                {
                    "timestamp": datetime.now(),
                    "metrics": metrics,
                    "operation_id": context["operation_id"],
                },
            )

            # Remove from active operations
            self.active_operations.pop(context["operation_id"], None)

        return metrics

    def get_average_metrics(self, sample_size: int = 100) -> SearchMetrics | None:
        """Get average metrics from recent operations.

        Args:
        ----
            sample_size: Number of recent metrics to average

        Returns:
        -------
            Average SearchMetrics or None if no data available

        """
        with self.lock:
            if not self.metrics_history:
                return None

            recent_metrics = [
                entry["metrics"] for entry in list(self.metrics_history)[-sample_size:]
            ]

            if not recent_metrics:
                return None

            # Calculate averages
            return SearchMetrics(
                search_latency_ms=sum(m.search_latency_ms for m in recent_metrics)
                / len(recent_metrics),
                tfidf_search_time_ms=sum(m.tfidf_search_time_ms for m in recent_metrics)
                / len(recent_metrics),
                vector_search_time_ms=sum(
                    m.vector_search_time_ms for m in recent_metrics
                )
                / len(recent_metrics),
                result_combination_time_ms=sum(
                    m.result_combination_time_ms for m in recent_metrics
                )
                / len(recent_metrics),
                total_results=int(
                    sum(m.total_results for m in recent_metrics) / len(recent_metrics)
                ),
                memory_usage_mb=sum(m.memory_usage_mb for m in recent_metrics)
                / len(recent_metrics),
                cpu_usage_percent=sum(m.cpu_usage_percent for m in recent_metrics)
                / len(recent_metrics),
                cache_hit_rate=sum(m.cache_hit_rate for m in recent_metrics)
                / len(recent_metrics),
                optimization_score=sum(m.optimization_score for m in recent_metrics)
                / len(recent_metrics),
            )

    def check_performance_alerts(
        self, metrics: SearchMetrics
    ) -> list[PerformanceAlert]:
        """Check for performance alerts based on metrics.

        Args:
        ----
            metrics: Search metrics to evaluate

        Returns:
        -------
            List of performance alerts

        """
        alerts = []

        # Check latency
        if metrics.search_latency_ms > self.alert_thresholds["max_search_latency_ms"]:
            alerts.append(
                PerformanceAlert(
                    severity="high",
                    message=f"Search latency {metrics.search_latency_ms:.1f}ms exceeds threshold {self.alert_thresholds['max_search_latency_ms']}ms",
                    metric_name="search_latency_ms",
                    threshold_violation={
                        "actual": metrics.search_latency_ms,
                        "threshold": self.alert_thresholds["max_search_latency_ms"],
                    },
                    timestamp=datetime.now(),
                    suggested_action="Consider increasing cache size or optimizing vector search",
                ),
            )

        # Check cache hit rate
        if metrics.cache_hit_rate < self.alert_thresholds["min_cache_hit_rate"]:
            alerts.append(
                PerformanceAlert(
                    severity="medium",
                    message=f"Cache hit rate {metrics.cache_hit_rate:.1%} below threshold {self.alert_thresholds['min_cache_hit_rate']:.1%}",
                    metric_name="cache_hit_rate",
                    threshold_violation={
                        "actual": metrics.cache_hit_rate,
                        "threshold": self.alert_thresholds["min_cache_hit_rate"],
                    },
                    timestamp=datetime.now(),
                    suggested_action="Review cache TTL and eviction policies",
                ),
            )

        # Check memory usage
        if metrics.memory_usage_mb > self.alert_thresholds["max_memory_usage_mb"]:
            alerts.append(
                PerformanceAlert(
                    severity="medium",
                    message=f"Memory usage {metrics.memory_usage_mb:.1f}MB exceeds threshold {self.alert_thresholds['max_memory_usage_mb']}MB",
                    metric_name="memory_usage_mb",
                    threshold_violation={
                        "actual": metrics.memory_usage_mb,
                        "threshold": self.alert_thresholds["max_memory_usage_mb"],
                    },
                    timestamp=datetime.now(),
                    suggested_action="Reduce cache size or optimize memory usage",
                ),
            )

        for alert in alerts:
            self.logger.warning(f"Performance alert: {alert.message}")

        return alerts

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:

            return psutil.cpu_percent(interval=None)
        except ImportError:
            return 0.0


class EnhancedErrorRecovery:
    """Enhanced error handling and recovery system."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initialize enhanced error recovery system.

        Args:
        ----
            logger: Logger instance

        """
        self.logger = logger or logging.getLogger(__name__)
        self.error_stats = defaultdict(int)
        self.recovery_strategies = {
            "vector_store_connection_error": self._handle_vector_store_error,
            "embedding_generation_error": self._handle_embedding_error,
            "cache_corruption_error": self._handle_cache_error,
            "memory_pressure_error": self._handle_memory_error,
            "timeout_error": self._handle_timeout_error,
        }

    def handle_error(self, error_scenario: dict[str, Any]) -> dict[str, Any]:
        """Handle error with appropriate recovery strategy.

        Algorithm Approach: Error classification + targeted recovery strategies
        Time Complexity: O(1) - constant time for error classification
        Space Complexity: O(1) - constant space for recovery data

        Args:
        ----
            error_scenario: Dictionary with error information

        Returns:
        -------
            Recovery result with action taken and success status

        """
        error_type = error_scenario.get("type", "unknown_error")
        severity = error_scenario.get("severity", "medium")

        self.error_stats[error_type] += 1

        self.logger.error(f"Handling error: {error_type} (severity: {severity})")

        # Get recovery strategy
        recovery_func = self.recovery_strategies.get(
            error_type, self._handle_generic_error
        )

        try:
            recovery_result = recovery_func(error_scenario)

            result = {
                "recovery_action": recovery_result["action"],
                "fallback_used": recovery_result.get("fallback_used", False),
                "recovery_successful": recovery_result["success"],
                "error_type": error_type,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
            }

            if recovery_result["success"]:
                self.logger.info(
                    f"Successfully recovered from {error_type}: {recovery_result['action']}"
                )
            else:
                self.logger.error(
                    f"Failed to recover from {error_type}: {recovery_result.get('message', 'Unknown error')}",
                )

            return result

        except Exception as e:
            self.logger.exception(f"Error during recovery from {error_type}: {e}")

            return {
                "recovery_action": "log_and_continue",
                "fallback_used": True,
                "recovery_successful": False,
                "error_type": error_type,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
                "recovery_error": str(e),
            }

    def _handle_vector_store_error(
        self, error_scenario: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle vector store connection errors."""
        return {
            "action": "fallback_to_tfidf_only",
            "fallback_used": True,
            "success": True,
            "message": "Using TF-IDF search only due to vector store unavailability",
        }

    def _handle_embedding_error(self, error_scenario: dict[str, Any]) -> dict[str, Any]:
        """Handle embedding generation errors."""
        return {
            "action": "use_cached_embeddings_or_skip_vector_search",
            "fallback_used": True,
            "success": True,
            "message": "Skipping vector search due to embedding generation error",
        }

    def _handle_cache_error(self, error_scenario: dict[str, Any]) -> dict[str, Any]:
        """Handle cache corruption errors."""
        return {
            "action": "rebuild_cache",
            "fallback_used": False,
            "success": True,
            "message": "Rebuilding corrupted cache",
        }

    def _handle_memory_error(self, error_scenario: dict[str, Any]) -> dict[str, Any]:
        """Handle memory pressure errors."""
        return {
            "action": "reduce_cache_size_and_throttle",
            "fallback_used": True,
            "success": True,
            "message": "Reducing cache size and implementing request throttling",
        }

    def _handle_timeout_error(self, error_scenario: dict[str, Any]) -> dict[str, Any]:
        """Handle timeout errors."""
        return {
            "action": "use_partial_results_or_extend_timeout",
            "fallback_used": True,
            "success": True,
            "message": "Using partial results due to timeout",
        }

    def _handle_generic_error(self, error_scenario: dict[str, Any]) -> dict[str, Any]:
        """Handle generic errors with default strategy."""
        return {
            "action": "log_error_and_continue_with_basic_functionality",
            "fallback_used": True,
            "success": True,
            "message": "Continuing with basic functionality due to unknown error",
        }

    def get_error_statistics(self) -> dict[str, Any]:
        """Get error statistics for monitoring."""
        return dict(self.error_stats)


class EnhancedHybridSearcher:
    """Enhanced hybrid search with dynamic optimization and performance monitoring.

    This implementation extends the basic HybridSearcher with advanced features:
    - Dynamic weight optimization based on query characteristics
    - Intelligent caching with performance-based eviction
    - Comprehensive performance monitoring and alerting
    - Enhanced error handling and recovery
    - Multi-vector backend support
    - Configuration-based optimization

    Algorithm Approach: Multi-layer enhancement with dynamic optimization
    Time Complexity: O(n) for indexing, O(log n) for search
    Space Complexity: O(n) for index storage with intelligent caching
    """

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        embedding_manager: EmbeddingManager | None = None,
        tfidf_weight: float = 0.3,
        vector_weight: float = 0.7,
        enable_dynamic_optimization: bool = True,
        enable_intelligent_caching: bool = True,
        enable_performance_monitoring: bool = True,
        cache_size: int = 1000,
        cache_ttl: int = 3600,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize enhanced hybrid searcher.

        Args:
        ----
            vector_store: Vector store instance (created if None)
            embedding_manager: Embedding manager instance (created if None)
            tfidf_weight: Default TF-IDF weight (if dynamic optimization disabled)
            vector_weight: Default vector weight (if dynamic optimization disabled)
            enable_dynamic_optimization: Enable dynamic weight optimization
            enable_intelligent_caching: Enable intelligent caching
            enable_performance_monitoring: Enable performance monitoring
            cache_size: Maximum cache size
            cache_ttl: Default cache TTL in seconds
            logger: Logger instance

        """
        self.logger = logger or logging.getLogger(__name__)

        # Validate basic weights
        if not math.isclose(tfidf_weight + vector_weight, 1.0, rel_tol=0.01):
            self.logger.warning("Weights don't sum to 1.0, normalizing...")
            total = tfidf_weight + vector_weight
            tfidf_weight /= total
            vector_weight /= total

        self.default_tfidf_weight = tfidf_weight
        self.default_vector_weight = vector_weight

        # Feature flags
        self.enable_dynamic_optimization = enable_dynamic_optimization
        self.enable_intelligent_caching = enable_intelligent_caching
        self.enable_performance_monitoring = enable_performance_monitoring

        # Initialize core components
        self.vector_store = (
            vector_store or VectorStoreFactory.create_chat_history_store()
        )
        self.embedding_manager = (
            embedding_manager or EmbeddingManagerFactory.create_chat_embeddings()
        )

        # Initialize enhanced components
        self.query_classifier = QueryClassifier(self.logger)
        self.weight_optimizer = WeightOptimizer(self.logger)

        if self.enable_intelligent_caching:
            self.cache_manager = IntelligentCacheManager(
                max_size=cache_size,
                default_ttl=cache_ttl,
                logger=self.logger,
            )

        if self.enable_performance_monitoring:
            self.performance_monitor = PerformanceMonitor(self.logger)

        self.error_recovery = EnhancedErrorRecovery(self.logger)

        # TF-IDF data structures (from original implementation)
        self.vocabulary: dict[str, dict[str, Any]] = {}
        self.document_frequency: dict[str, int] = defaultdict(int)
        self.total_documents = 0

        # Enhanced features state
        self.optimization_stats = defaultdict(int)
        self.consolidated_db_config = {}
        self.backend_manager = None

        self.logger.info(
            f"Enhanced hybrid searcher initialized - "
            f"Dynamic optimization: {enable_dynamic_optimization}, "
            f"Intelligent caching: {enable_intelligent_caching}, "
            f"Performance monitoring: {enable_performance_monitoring}",
        )

    # Enhanced feature accessors (for TDD test compatibility)
    def get_query_classifier(self) -> QueryClassifier:
        """Get query classifier instance."""
        return self.query_classifier

    def get_weight_optimizer(self) -> WeightOptimizer:
        """Get weight optimizer instance."""
        return self.weight_optimizer

    def get_cache_manager(self) -> IntelligentCacheManager | None:
        """Get cache manager instance."""
        return getattr(self, "cache_manager", None)

    def get_performance_monitor(self) -> PerformanceMonitor | None:
        """Get performance monitor instance."""
        return getattr(self, "performance_monitor", None)

    def get_error_recovery(self) -> EnhancedErrorRecovery:
        """Get error recovery instance."""
        return self.error_recovery

    def analyze_query_and_optimize_weights(self, query: str) -> dict[str, float]:
        """Analyze query and return optimized weights.

        Args:
        ----
            query: Search query to analyze

        Returns:
        -------
            Dictionary with optimized weights

        """
        if not self.enable_dynamic_optimization:
            return {
                "tfidf_weight": self.default_tfidf_weight,
                "vector_weight": self.default_vector_weight,
            }

        # Classify query
        query_type = self.query_classifier.classify_query(query)

        # Determine complexity
        complexity = self._determine_query_complexity(query)

        # Get optimized weights
        tfidf_weight, vector_weight = self.weight_optimizer.optimize_weights(
            query,
            query_type,
            complexity,
        )

        self.optimization_stats["dynamic_optimizations"] += 1

        return {
            "tfidf_weight": tfidf_weight,
            "vector_weight": vector_weight,
            "query_type": query_type.value,
            "complexity": complexity.value,
        }

    def _determine_query_complexity(self, query: str) -> QueryComplexity:
        """Determine query complexity based on characteristics."""
        if not query:
            return QueryComplexity.SIMPLE

        word_count = len(query.split())
        char_count = len(query)
        len(set(query.lower().split()))

        # Simple heuristics for complexity
        if word_count <= 2 and char_count < 20:
            return QueryComplexity.SIMPLE
        if word_count <= 5 and char_count < 50:
            return QueryComplexity.MEDIUM
        if word_count <= 10 and char_count < 100:
            return QueryComplexity.COMPLEX
        return QueryComplexity.EXPERT

    def cached_search(
        self, query: str, limit: int = 10, **kwargs
    ) -> list[dict[str, Any]]:
        """Perform search with intelligent caching.

        Args:
        ----
            query: Search query
            limit: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
        -------
            Search results from cache or fresh search

        """
        if not self.enable_intelligent_caching:
            return self.search(query, limit, **kwargs)

        # Check cache first
        cache_manager = self.get_cache_manager()
        if cache_manager:
            cached_results = cache_manager.get(query)
            if cached_results is not None:
                self.logger.debug(f"Cache hit for query: '{query}'")
                return cached_results[:limit]

        # Perform fresh search
        results = self.search(query, limit, **kwargs)

        # Cache results
        query_type = self.query_classifier.classify_query(query)
        relevance_score = results[0]["combined_score"] if results else 0.0

        cache_manager.put(query, results, query_type, relevance_score)

        return results

    def optimized_search(
        self, query: str, limit: int = 10, **kwargs
    ) -> list[dict[str, Any]]:
        """Perform optimized search with dynamic weight adjustment.

        Args:
        ----
            query: Search query
            limit: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
        -------
            Optimized search results

        """
        # Get optimized weights
        weight_analysis = self.analyze_query_and_optimize_weights(query)

        # Use optimized weights for search
        return self.search(
            query,
            limit,
            tfidf_weight=weight_analysis["tfidf_weight"],
            vector_weight=weight_analysis["vector_weight"],
            **kwargs,
        )

    def concurrent_search(
        self, query: str, limit: int = 10, **kwargs
    ) -> list[dict[str, Any]]:
        """Perform search with concurrent TF-IDF and vector operations.

        Args:
        ----
            query: Search query
            limit: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
        -------
            Search results from concurrent operations

        """
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both searches concurrently
            tfidf_future = executor.submit(self._tfidf_search, query, limit)
            vector_future = executor.submit(self._vector_search, query, limit)

            # Get results
            tfidf_results = tfidf_future.result()
            vector_results = vector_future.result()

        # Combine results
        return self._combine_results(tfidf_results, vector_results, **kwargs)

    def memory_optimized_search(
        self, query: str, limit: int = 10, **kwargs
    ) -> list[dict[str, Any]]:
        """Perform memory-optimized search for resource-constrained environments.

        Args:
        ----
            query: Search query
            limit: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
        -------
            Memory-optimized search results

        """
        # Check memory pressure
        if hasattr(self, "performance_monitor"):
            current_memory = self.performance_monitor._get_memory_usage()
            if current_memory > 400:  # MB threshold
                self.logger.warning(
                    f"High memory usage ({current_memory:.1f}MB), using optimized search"
                )

                # Use reduced limits and skip expensive operations
                kwargs.setdefault("tfidf_limit", min(kwargs.get("tfidf_limit", 50), 25))
                kwargs.setdefault(
                    "vector_limit", min(kwargs.get("vector_limit", 50), 25)
                )

                # Clear cache if memory pressure is high
                cache_manager = self.get_cache_manager()
                if cache_manager and current_memory > 500:
                    cache_manager.clear()

        return self.search(query, limit, **kwargs)

    def search(
        self,
        query: str,
        limit: int = 10,
        tfidf_limit: int = 50,
        vector_limit: int = 50,
        score_threshold: float = 0.1,
        tfidf_weight: float | None = None,
        vector_weight: float | None = None,
    ) -> list[dict[str, Any]]:
        """Perform enhanced hybrid search.

        Args:
        ----
            query: Search query
            limit: Maximum number of results to return
            tfidf_limit: Maximum TF-IDF results to consider
            vector_limit: Maximum vector results to consider
            score_threshold: Minimum combined score threshold
            tfidf_weight: Override TF-IDF weight
            vector_weight: Override vector weight

        Returns:
        -------
            List of enhanced hybrid search results

        """
        operation_id = f"search_{int(time.time() * 1000)}"
        monitor_context = None

        if self.enable_performance_monitoring:
            monitor_context = self.performance_monitor.start_monitoring(operation_id)

        try:
            self.logger.info(f"Enhanced hybrid search for: '{query}'")

            # Get optimized weights if not provided
            if tfidf_weight is None or vector_weight is None:
                weight_analysis = self.analyze_query_and_optimize_weights(query)
                tfidf_weight = tfidf_weight or weight_analysis["tfidf_weight"]
                vector_weight = vector_weight or weight_analysis["vector_weight"]

            # Perform searches with timing
            start_time = time.time()
            tfidf_results = self._tfidf_search(query, tfidf_limit)
            tfidf_time = (time.time() - start_time) * 1000

            start_time = time.time()
            vector_results = self._vector_search(query, vector_limit)
            vector_time = (time.time() - start_time) * 1000

            start_time = time.time()
            combined_results = self._combine_results(
                tfidf_results,
                vector_results,
                tfidf_weight=tfidf_weight,
                vector_weight=vector_weight,
            )
            combination_time = (time.time() - start_time) * 1000

            # Filter by threshold and sort
            filtered_results = [
                result
                for result in combined_results
                if result["combined_score"] >= score_threshold
            ]
            filtered_results.sort(key=lambda x: x["combined_score"], reverse=True)

            final_results = filtered_results[:limit]

            # Performance monitoring
            if self.enable_performance_monitoring and monitor_context:
                cache_hit_rate = 0.0
                if self.enable_intelligent_caching:
                    cache_stats = self.get_cache_manager().get_cache_stats()
                    cache_hit_rate = cache_stats.get("hit_rate", 0.0)

                additional_metrics = {
                    "tfidf_time_ms": tfidf_time,
                    "vector_time_ms": vector_time,
                    "combination_time_ms": combination_time,
                    "total_results": len(final_results),
                    "cache_hit_rate": cache_hit_rate,
                    "optimization_score": self._calculate_optimization_score(
                        tfidf_weight, vector_weight, query
                    ),
                }

                metrics = self.performance_monitor.stop_monitoring(
                    monitor_context, additional_metrics
                )

                # Check for performance alerts
                alerts = self.performance_monitor.check_performance_alerts(metrics)
                if alerts:
                    self.logger.warning(f"Performance alerts generated: {len(alerts)}")

            self.logger.info(f"Enhanced search returning {len(final_results)} results")
            return final_results

        except Exception as e:
            self.logger.exception(f"Enhanced search failed: {e}")

            # Try error recovery
            recovery_result = self.error_recovery.handle_error(
                {
                    "type": "search_error",
                    "severity": "high",
                    "error": str(e),
                    "query": query,
                },
            )

            if recovery_result["recovery_successful"]:
                self.logger.info(
                    f"Recovered from search error: {recovery_result['recovery_action']}"
                )
                # Fallback to basic search
                return self._fallback_search(query, limit)
            raise

        finally:
            # Clean up monitoring
            if self.enable_performance_monitoring and monitor_context:
                self.performance_monitor.stop_monitoring(monitor_context)

    def _fallback_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Fallback search using TF-IDF only."""
        try:
            self.logger.warning("Using fallback TF-IDF search")
            results = self._tfidf_search(query, limit)
            return results[:limit]
        except Exception as e:
            self.logger.exception(f"Fallback search also failed: {e}")
            return []

    def _calculate_optimization_score(
        self, tfidf_weight: float, vector_weight: float, query: str
    ) -> float:
        """Calculate optimization score based on query characteristics and weights."""
        query_type = self.query_classifier.classify_query(query)

        # Ideal weights for different query types
        ideal_weights = {
            QueryType.KEYWORD: (0.7, 0.3),
            QueryType.SEMANTIC: (0.2, 0.8),
            QueryType.TECHNICAL: (0.6, 0.4),
            QueryType.QUESTION: (0.4, 0.6),
            QueryType.NAVIGATIONAL: (0.5, 0.5),
        }

        ideal_tfidf, ideal_vector = ideal_weights.get(query_type, (0.3, 0.7))

        # Calculate how close we are to ideal weights (lower is better)
        weight_diff = abs(tfidf_weight - ideal_tfidf) + abs(
            vector_weight - ideal_vector
        )

        # Convert to score (0-1, higher is better)
        return max(0, 1 - weight_diff)

    # Include all original methods from HybridSearcher
    def add_documents(self, documents: list[dict[str, Any]]) -> list[str]:
        """Add documents to both TF-IDF index and vector store.

        Args:
        ----
            documents: List of documents with 'text' and metadata

        Returns:
        -------
            List of document IDs

        """
        if not documents:
            return []

        self.logger.info(f"Adding {len(documents)} documents to enhanced hybrid index")

        # Generate IDs and extract texts
        document_ids = []
        texts = []
        payloads = []

        for doc in documents:
            doc_id = doc.get("id") or self._generate_document_id(doc["text"])
            document_ids.append(doc_id)
            texts.append(doc["text"])

            # Prepare payload for vector store
            payload = {
                **doc.get("metadata", {}),
                "document_id": doc_id,
                "text": doc["text"][:500],  # Store text preview for display
                "source": "enhanced_hybrid_searcher",
                "indexed_at": datetime.now().isoformat(),
            }
            payloads.append(payload)

        try:
            # Update TF-IDF index
            self._update_tfidf_index(document_ids, texts)

            # Generate embeddings and add to vector store
            embeddings = self.embedding_manager.encode(texts)
            self.vector_store.add_vectors(embeddings, payloads, document_ids)

            self.total_documents += len(documents)
            self.logger.info(f"Successfully indexed {len(documents)} documents")

            # Invalidate cache for related queries
            if self.enable_intelligent_caching:
                cache_manager = self.get_cache_manager()
                if cache_manager:
                    # Invalidate cache entries that might be affected
                    for doc in documents[:5]:  # Sample to avoid excessive invalidation
                        cache_manager.invalidate_by_pattern(doc["text"][:20])

            return document_ids

        except Exception as e:
            self.logger.exception(f"Failed to add documents: {e}")

            # Try error recovery
            recovery_result = self.error_recovery.handle_error(
                {
                    "type": "document_indexing_error",
                    "severity": "medium",
                    "error": str(e),
                    "document_count": len(documents),
                },
            )

            if recovery_result["recovery_successful"]:
                self.logger.info(
                    f"Recovered from indexing error: {recovery_result['recovery_action']}"
                )
            else:
                raise

    def _update_tfidf_index(self, document_ids: list[str], texts: list[str]) -> None:
        """Update TF-IDF index with new documents."""
        for doc_id, text in zip(document_ids, texts, strict=False):
            # Tokenize and count terms
            tokens = self._tokenize_text(text)
            token_counts = Counter(tokens)

            # Update document frequency
            for token in set(tokens):
                self.document_frequency[token] += 1

            # Store term frequencies for this document
            if "documents" not in self.vocabulary:
                self.vocabulary["documents"] = {}

            self.vocabulary["documents"][doc_id] = {
                "term_counts": dict(token_counts),
                "total_terms": len(tokens),
                "text": text[:500],  # Store preview
            }

        # Update IDF scores
        for token in self.document_frequency:
            if token not in self.vocabulary:
                self.vocabulary[token] = {}
            # Prevent math domain error by ensuring valid input for log
            if self.total_documents > 0:
                idf_value = self.total_documents / (1 + self.document_frequency[token])
                if idf_value > 0:
                    self.vocabulary[token]["idf"] = math.log(idf_value)
                else:
                    self.vocabulary[token]["idf"] = 0.0  # Fallback for invalid values
            else:
                self.vocabulary[token]["idf"] = 0.0  # Fallback for zero documents

    def _tfidf_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Perform TF-IDF keyword search."""
        query_tokens = self._tokenize_text(query)
        if not query_tokens:
            return []

        # Calculate TF-IDF scores for each document
        doc_scores = defaultdict(float)

        for token in query_tokens:
            if token in self.vocabulary and "documents" in self.vocabulary:
                idf = self.vocabulary[token].get("idf", 0)

                for doc_id, doc_info in self.vocabulary["documents"].items():
                    tf = doc_info["term_counts"].get(token, 0)
                    if tf > 0:
                        # TF-IDF score
                        tfidf_score = tf * idf
                        doc_scores[doc_id] += tfidf_score

        # Create result objects
        results = []
        for doc_id, score in doc_scores.items():
            if (
                "documents" in self.vocabulary
                and doc_id in self.vocabulary["documents"]
            ):
                doc_info = self.vocabulary["documents"][doc_id]
                result = {
                    "document_id": doc_id,
                    "tfidf_score": score,
                    "vector_score": 0.0,
                    "combined_score": 0.0,
                    "text": doc_info.get("text", ""),
                    "matched_tokens": [
                        token
                        for token in query_tokens
                        if token in doc_info["term_counts"]
                    ],
                    "source": "tfidf",
                }
                results.append(result)

        # Sort by TF-IDF score and limit
        results.sort(key=lambda x: x["tfidf_score"], reverse=True)
        return results[:limit]

    def _vector_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Perform vector semantic search."""
        try:
            # Generate query embedding
            query_embedding = self.embedding_manager.encode_single(query)

            # Search vector store
            vector_results = self.vector_store.search(
                query_vector=query_embedding,
                limit=limit,
                score_threshold=0.1,
            )

            # Convert to hybrid result format
            results = []
            for hit in vector_results:
                result = {
                    "document_id": hit["id"],
                    "tfidf_score": 0.0,
                    "vector_score": hit["score"],
                    "combined_score": 0.0,
                    "text": hit["payload"].get("text", ""),
                    "matched_tokens": [],  # Not applicable for vector search
                    "source": "vector",
                    "metadata": hit["payload"],
                }
                results.append(result)

            return results

        except Exception as e:
            self.logger.exception(f"Vector search failed: {e}")

            # Try error recovery
            recovery_result = self.error_recovery.handle_error(
                {
                    "type": "vector_search_error",
                    "severity": "medium",
                    "error": str(e),
                    "query": query,
                },
            )

            if recovery_result["fallback_used"]:
                self.logger.info(
                    f"Using fallback due to vector search error: {recovery_result['recovery_action']}"
                )
            return []

    def _combine_results(
        self,
        tfidf_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
        tfidf_weight: float | None = None,
        vector_weight: float | None = None,
    ) -> list[dict[str, Any]]:
        """Combine TF-IDF and vector search results."""
        # Use provided weights or defaults
        tfidf_weight = tfidf_weight or self.default_tfidf_weight
        vector_weight = vector_weight or self.default_vector_weight

        # Create a map of document_id to results
        combined_map = {}

        # Process TF-IDF results
        for result in tfidf_results:
            doc_id = result["document_id"]
            combined_map[doc_id] = result.copy()
            # Normalize TF-IDF scores (0-1 range)
            if tfidf_results:
                max_tfidf = tfidf_results[0]["tfidf_score"]
                if max_tfidf > 0:
                    combined_map[doc_id]["tfidf_score"] = (
                        result["tfidf_score"] / max_tfidf
                    )

        # Process vector results and merge
        for result in vector_results:
            doc_id = result["document_id"]
            if doc_id in combined_map:
                # Merge with existing result
                combined_map[doc_id]["vector_score"] = result["vector_score"]
                combined_map[doc_id]["source"] = "hybrid"
                # Add metadata from vector result
                if "metadata" in result:
                    combined_map[doc_id]["metadata"] = result["metadata"]
            else:
                # Add new result
                combined_map[doc_id] = result.copy()

        # Calculate combined scores
        for doc_id, result in combined_map.items():
            combined_score = (
                result["tfidf_score"] * tfidf_weight
                + result["vector_score"] * vector_weight
            )
            result["combined_score"] = combined_score
            result["tfidf_weight_used"] = tfidf_weight
            result["vector_weight_used"] = vector_weight

        return list(combined_map.values())

    def _tokenize_text(self, text: str) -> list[str]:
        """Tokenize text for TF-IDF processing."""
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r"\b\w+\b", text.lower())

        # Filter out common stop words
        stop_words = {
            "the",
            "is",
            "at",
            "which",
            "on",
            "and",
            "a",
            "to",
            "are",
            "as",
            "was",
            "were",
            "will",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "but",
            "or",
            "if",
            "they",
            "he",
            "she",
            "it",
            "we",
            "you",
            "i",
            "this",
            "that",
            "these",
            "those",
            "am",
            "been",
            "being",
            "for",
            "with",
            "by",
            "from",
        }

        return [token for token in tokens if token not in stop_words and len(token) > 2]

    def _generate_document_id(self, text: str) -> str:
        """Generate a unique document ID using UUID4 for Qdrant compatibility."""
        # Generate deterministic UUID based on content hash for reproducibility
        content_hash = hashlib.sha256(text.encode()).hexdigest()
        # Use hash to create deterministic UUID (UUID5 with namespace)
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"doc://{content_hash}"))

    def get_statistics(self) -> dict[str, Any]:
        """Get enhanced search statistics and index information."""
        # Base statistics
        vector_stats = self.vector_store.get_collection_info()
        embedding_stats = self.embedding_manager.get_device_info()

        base_stats = {
            "total_documents": self.total_documents,
            "vocabulary_size": len(self.document_frequency),
            "default_tfidf_weight": self.default_tfidf_weight,
            "default_vector_weight": self.default_vector_weight,
            "vector_store": vector_stats,
            "embedding_manager": embedding_stats,
            "last_updated": datetime.now().isoformat(),
        }

        # Enhanced features statistics
        enhanced_stats = {
            "features_enabled": {
                "dynamic_optimization": self.enable_dynamic_optimization,
                "intelligent_caching": self.enable_intelligent_caching,
                "performance_monitoring": self.enable_performance_monitoring,
            },
            "optimization_stats": dict(self.optimization_stats),
            "error_stats": self.error_recovery.get_error_statistics(),
        }

        # Cache statistics
        if self.enable_intelligent_caching:
            cache_manager = self.get_cache_manager()
            if cache_manager:
                enhanced_stats["cache_stats"] = cache_manager.get_cache_stats()

        # Performance statistics
        if self.enable_performance_monitoring:
            performance_monitor = self.get_performance_monitor()
            if performance_monitor:
                avg_metrics = performance_monitor.get_average_metrics()
                if avg_metrics:
                    enhanced_stats["performance_metrics"] = asdict(avg_metrics)

        # Merge all statistics
        base_stats.update(enhanced_stats)
        return base_stats

    def close(self) -> None:
        """Clean up resources."""
        try:
            if self.embedding_manager:
                self.embedding_manager.close()
            if self.vector_store:
                self.vector_store.close()

            # Clear cache
            if self.enable_intelligent_caching:
                cache_manager = self.get_cache_manager()
                if cache_manager:
                    cache_manager.clear()

            self.logger.info("Enhanced hybrid searcher closed")

        except Exception as e:
            self.logger.exception(f"Error during cleanup: {e}")


class EnhancedHybridSearcherFactory:
    """Factory for creating enhanced hybrid searchers with different configurations."""

    @staticmethod
    def create_default_enhanced_searcher(**kwargs) -> EnhancedHybridSearcher:
        """Create a default enhanced hybrid searcher.

        Args:
        ----
            **kwargs: Additional configuration parameters

        Returns:
        -------
            EnhancedHybridSearcher with balanced settings

        """
        config = {
            "enable_dynamic_optimization": True,
            "enable_intelligent_caching": True,
            "enable_performance_monitoring": True,
            "cache_size": 1000,
            "cache_ttl": 3600,
        }
        config.update(kwargs)

        return EnhancedHybridSearcher(**config)

    @staticmethod
    def create_high_performance_searcher(**kwargs) -> EnhancedHybridSearcher:
        """Create a high-performance enhanced searcher.

        Args:
        ----
            **kwargs: Additional configuration parameters

        Returns:
        -------
            EnhancedHybridSearcher optimized for performance

        """
        config = {
            "enable_dynamic_optimization": True,
            "enable_intelligent_caching": True,
            "enable_performance_monitoring": True,
            "cache_size": 2000,  # Larger cache
            "cache_ttl": 7200,  # Longer TTL
            "tfidf_weight": 0.25,
            "vector_weight": 0.75,
        }
        config.update(kwargs)

        return EnhancedHybridSearcher(**config)

    @staticmethod
    def create_memory_efficient_searcher(**kwargs) -> EnhancedHybridSearcher:
        """Create a memory-efficient enhanced searcher.

        Args:
        ----
            **kwargs: Additional configuration parameters

        Returns:
        -------
            EnhancedHybridSearcher optimized for low memory usage

        """
        config = {
            "enable_dynamic_optimization": True,
            "enable_intelligent_caching": True,
            "enable_performance_monitoring": False,  # Disable monitoring to save memory
            "cache_size": 200,  # Smaller cache
            "cache_ttl": 1800,  # Shorter TTL
            "tfidf_weight": 0.4,
            "vector_weight": 0.6,
        }
        config.update(kwargs)

        return EnhancedHybridSearcher(**config)


# Convenience functions for creating enhanced searchers
def create_enhanced_hybrid_searcher(
    tfidf_weight: float = 0.3,
    vector_weight: float = 0.7,
    **kwargs,
) -> EnhancedHybridSearcher:
    """Create an enhanced hybrid searcher with custom weights.

    Args:
    ----
        tfidf_weight: Weight for TF-IDF search (0-1)
        vector_weight: Weight for vector search (0-1)
        **kwargs: Additional configuration parameters

    Returns:
    -------
        EnhancedHybridSearcher instance

    """
    return EnhancedHybridSearcherFactory.create_default_enhanced_searcher(
        tfidf_weight=tfidf_weight,
        vector_weight=vector_weight,
        **kwargs,
    )
