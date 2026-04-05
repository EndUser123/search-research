from __future__ import annotations

import logging
import threading
import time
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from typing import Any

from .context_models import PromptingContext, PromptingTechnique, TechniqueApplicability

"""Performance optimization system for the Adaptive Universal Prompting Framework.

This module provides intelligent performance optimization, caching strategies,
and resource management for prompting technique selection and execution.
"""





@dataclass
class PerformanceMetrics:
    """Performance metrics for technique execution."""

    technique_name: str
    execution_time: float
    memory_usage: float
    success_rate: float
    confidence_correlation: float
    user_satisfaction_score: float = 0.0
    last_used: float = field(default_factory=time.time)


@dataclass
class OptimizationStrategy:
    """Optimization strategy for technique selection."""

    name: str
    priority: int
    conditions: list[str]
    actions: list[str]
    expected_improvement: dict[str, float]


class TechniqueCache:
    """LRU cache with TTL for technique assessments."""

    def __init__(self, max_size: int = 1000, ttl_seconds: float = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.RLock()

    def get(self, key: str) -> TechniqueApplicability | None:
        """Get item from cache if valid."""
        with self.lock:
            if key not in self.cache:
                return None

            # Check TTL
            if time.time() - self.timestamps[key] > self.ttl_seconds:
                self._remove(key)
                return None

            # Move to end (LRU)
            value = self.cache.pop(key)
            self.cache[key] = value
            return value

    def put(self, key: str, value: TechniqueApplicability) -> None:
        """Put item in cache with LRU eviction."""
        with self.lock:
            current_time = time.time()

            # Remove if exists and expired
            if key in self.cache and current_time - self.timestamps[key] > self.ttl_seconds:
                self._remove(key)

            # Evict if at capacity
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                self._remove(oldest_key)

            # Add new item
            self.cache[key] = value
            self.timestamps[key] = current_time

    def _remove(self, key: str) -> None:
        """Remove item from cache."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)

    def clear_expired(self) -> int:
        """Clear expired items and return count removed."""
        with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, timestamp in self.timestamps.items() if current_time - timestamp > self.ttl_seconds
            ]

            for key in expired_keys:
                self._remove(key)

            return len(expired_keys)

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "utilization": len(self.cache) / self.max_size,
            }


class PerformanceOptimizer:
    """Intelligent performance optimization for prompting framework."""

    def __init__(self, cache_size: int = 1000, learning_enabled: bool = True):
        self.logger = logging.getLogger(__name__)
        self.technique_cache = TechniqueCache(cache_size)
        self.performance_history = defaultdict(list)
        self.learning_enabled = learning_enabled
        self.optimization_strategies = self._initialize_strategies()
        self.budget_tracker = {}

    def _initialize_strategies(self) -> list[OptimizationStrategy]:
        """Initialize optimization strategies."""
        return [
            OptimizationStrategy(
                name="fast_response",
                priority=1,
                conditions=["response_time_constraint", "simple_query"],
                actions=["use_cached_results", "limit_techniques", "prefer_fast_techniques"],
                expected_improvement={"response_time": 0.5, "memory_usage": 0.3},
            ),
            OptimizationStrategy(
                name="high_accuracy",
                priority=2,
                conditions=["complex_query", "no_time_constraint"],
                actions=["use_multiple_techniques", "enable_consensus", "deep_analysis"],
                expected_improvement={"accuracy": 0.3, "confidence": 0.2},
            ),
            OptimizationStrategy(
                name="memory_constrained",
                priority=3,
                conditions=["low_memory", "high_volume"],
                actions=["lightweight_techniques", "aggressive_caching", "batch_processing"],
                expected_improvement={"memory_usage": 0.6, "throughput": 0.4},
            ),
            OptimizationStrategy(
                name="balanced",
                priority=4,
                conditions=["standard_operation"],
                actions=["adaptive_selection", "moderate_caching", "performance_monitoring"],
                expected_improvement={"overall": 0.2},
            ),
        ]

    async def optimize_technique_selection(
        self,
        context: PromptingContext,
        applicable_techniques: list[TechniqueApplicability],
    ) -> list[TechniqueApplicability]:
        """Optimize technique selection based on context and performance history."""
        start_time = time.time()

        # Select optimization strategy
        strategy = self._select_strategy(context)
        self.logger.debug(f"Selected optimization strategy: {strategy.name}")

        # Apply optimization
        optimized_techniques = await self._apply_optimization(
            context,
            applicable_techniques,
            strategy,
        )

        # Record optimization metrics
        optimization_time = time.time() - start_time
        self._record_optimization_metrics(
            context,
            strategy,
            len(applicable_techniques),
            len(optimized_techniques),
            optimization_time,
        )

        return optimized_techniques

    def _select_strategy(self, context: PromptingContext) -> OptimizationStrategy:
        """Select optimization strategy based on context."""
        conditions = self._analyze_conditions(context)

        # Find matching strategies
        matching_strategies = [
            strategy
            for strategy in self.optimization_strategies
            if any(condition in conditions for condition in strategy.conditions)
        ]

        # Return highest priority matching strategy
        if matching_strategies:
            return min(matching_strategies, key=lambda s: s.priority)

        # Return default balanced strategy
        return next(s for s in self.optimization_strategies if s.name == "balanced")

    def _analyze_conditions(self, context: PromptingContext) -> set[str]:
        """Analyze context conditions for strategy selection."""
        conditions = set()

        # Performance constraints
        if context.performance_constraints.get("max_response_time", 5.0) < 2.0:
            conditions.add("response_time_constraint")

        if context.performance_constraints.get("max_memory_usage", 512) < 256:
            conditions.add("low_memory")

        # Query complexity
        if context.complexity in ["simple"]:
            conditions.add("simple_query")
        elif context.complexity in ["complex", "expert"]:
            conditions.add("complex_query")

        # Evidence requirements
        if not context.has_evidence_requirements():
            conditions.add("fast_path")

        # Default condition
        if not conditions:
            conditions.add("standard_operation")

        return conditions

    async def _apply_optimization(
        self,
        context: PromptingContext,
        techniques: list[TechniqueApplicability],
        strategy: OptimizationStrategy,
    ) -> list[TechniqueApplicability]:
        """Apply optimization strategy to technique list."""
        optimized = techniques.copy()

        for action in strategy.actions:
            if action == "use_cached_results":
                optimized = self._apply_caching(optimized)
            elif action == "limit_techniques":
                optimized = self._limit_techniques(optimized, context)
            elif action == "prefer_fast_techniques":
                optimized = self._prefer_fast_techniques(optimized)
            elif action == "use_multiple_techniques":
                optimized = self._expand_techniques(optimized, context)
            elif action == "enable_consensus":
                optimized = self._enable_consensus(optimized)
            elif action == "deep_analysis":
                optimized = self._prioritize_accuracy(optimized)
            elif action == "lightweight_techniques":
                optimized = self._select_lightweight(optimized)
            elif action == "aggressive_caching":
                optimized = self._apply_aggressive_caching(optimized)
            elif action == "batch_processing":
                optimized = self._optimize_for_batching(optimized)
            elif action == "adaptive_selection":
                optimized = self._adaptive_selection(optimized, context)
            elif action == "moderate_caching":
                optimized = self._apply_moderate_caching(optimized)
            elif action == "performance_monitoring":
                self._enable_monitoring(optimized)

        return optimized

    def _apply_caching(self, techniques: list[TechniqueApplicability]) -> list[TechniqueApplicability]:
        """Apply caching optimization."""
        # Techniques with high cache hit rate get priority
        return sorted(
            techniques,
            key=lambda t: self._get_cache_hit_rate(t.technique),
            reverse=True,
        )

    def _limit_techniques(
        self,
        techniques: list[TechniqueApplicability],
        context: PromptingContext,
    ) -> list[TechniqueApplicability]:
        """Limit number of techniques based on constraints."""
        max_techniques = context.performance_constraints.get("max_technique_count", 3)
        return techniques[:max_techniques]

    def _prefer_fast_techniques(self, techniques: list[TechniqueApplicability]) -> list[TechniqueApplicability]:
        """Prefer faster techniques."""
        return sorted(
            techniques,
            key=lambda t: t.performance_impact.get("response_time", float("inf")),
        )

    def _expand_techniques(
        self,
        techniques: list[TechniqueApplicability],
        context: PromptingContext,
    ) -> list[TechniqueApplicability]:
        """Expand technique selection for complex queries."""
        # Add complementary techniques
        expanded = techniques.copy()
        for technique in techniques:
            if technique.technique == PromptingTechnique.CHAIN_OF_THOUGHT:
                # Add self-consistency for verification
                if not any(t.technique == PromptingTechnique.SELF_CONSISTENCY for t in expanded):
                    # Would create a synthetic technique here
                    pass
        return expanded

    def _enable_consensus(self, techniques: list[TechniqueApplicability]) -> list[TechniqueApplicability]:
        """Enable consensus building techniques."""
        return sorted(
            techniques,
            key=lambda t: t.confidence * t.applicable,
            reverse=True,
        )

    def _prioritize_accuracy(self, techniques: list[TechniqueApplicability]) -> list[TechniqueApplicability]:
        """Prioritize accuracy over speed."""
        return sorted(
            techniques,
            key=lambda t: t.confidence,
            reverse=True,
        )

    def _select_lightweight(self, techniques: list[TechniqueApplicability]) -> list[TechniqueApplicability]:
        """Select lightweight techniques."""
        return sorted(
            techniques,
            key=lambda t: t.performance_impact.get("memory_usage", float("inf")),
        )

    def _apply_aggressive_caching(self, techniques: list[TechniqueApplicability]) -> list[TechniqueApplicability]:
        """Apply aggressive caching."""
        # Extend cache TTL and prioritize cached techniques
        return self._apply_caching(techniques)

    def _optimize_for_batching(self, techniques: list[TechniqueApplicability]) -> list[TechniqueApplicability]:
        """Optimize techniques for batch processing."""
        return sorted(
            techniques,
            key=lambda t: t.performance_impact.get("cpu_usage", 0),
        )

    def _adaptive_selection(
        self,
        techniques: list[TechniqueApplicability],
        context: PromptingContext,
    ) -> list[TechniqueApplicability]:
        """Adaptive selection based on historical performance."""
        if not self.learning_enabled:
            return techniques

        # Boost techniques based on historical success
        for technique in techniques:
            success_rate = self._get_technique_success_rate(technique.technique, context)
            technique.confidence *= 1 + success_rate * 0.2  # Boost confidence

        return sorted(techniques, key=lambda t: t.confidence, reverse=True)

    def _apply_moderate_caching(self, techniques: list[TechniqueApplicability]) -> list[TechniqueApplicability]:
        """Apply moderate caching."""
        return self._apply_caching(techniques)

    def _enable_monitoring(self, techniques: list[TechniqueApplicability]) -> list[TechniqueApplicability]:
        """Enable performance monitoring."""
        # This would enable detailed monitoring - placeholder for implementation
        return techniques

    def _get_cache_hit_rate(self, technique: PromptingTechnique) -> float:
        """Get cache hit rate for technique."""
        # Placeholder implementation
        return 0.5

    def _get_technique_success_rate(self, technique: PromptingTechnique, context: PromptingContext) -> float:
        """Get historical success rate for technique."""
        # Placeholder implementation
        return 0.7

    def _record_optimization_metrics(
        self,
        context: PromptingContext,
        strategy: OptimizationStrategy,
        input_count: int,
        output_count: int,
        optimization_time: float,
    ) -> None:
        """Record optimization metrics for learning."""
        if not self.learning_enabled:
            return

        metrics = {
            "strategy": strategy.name,
            "input_count": input_count,
            "output_count": output_count,
            "optimization_time": optimization_time,
            "timestamp": time.time(),
        }

        # Store for learning
        self.performance_history[context.domain].append(metrics)

    def get_performance_report(self) -> dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            "cache_stats": self.technique_cache.stats(),
            "optimization_strategies": len(self.optimization_strategies),
            "performance_history_size": sum(len(history) for history in self.performance_history.values()),
            "learning_enabled": self.learning_enabled,
            "recommendations": self._generate_recommendations(),
        }

        return report

    def _generate_recommendations(self) -> list[str]:
        """Generate performance optimization recommendations."""
        recommendations = []

        cache_stats = self.technique_cache.stats()
        if cache_stats["utilization"] > 0.8:
            recommendations.append("Consider increasing cache size for better performance")

        if cache_stats["utilization"] < 0.2:
            recommendations.append("Consider decreasing cache size to save memory")

        # Analyze strategy effectiveness
        strategy_usage = defaultdict(int)
        for domain_history in self.performance_history.values():
            for metrics in domain_history:
                strategy_usage[metrics["strategy"]] += 1

        if not strategy_usage:
            recommendations.append("Enable learning to collect performance data")

        return recommendations

    def clear_expired_cache(self) -> int:
        """Clear expired cache entries."""
        return self.technique_cache.clear_expired()

    def optimize_for_context(self, context: PromptingContext) -> dict[str, Any]:
        """Get optimization recommendations for specific context."""
        strategy = self._select_strategy(context)

        return {
            "recommended_strategy": strategy.name,
            "expected_improvements": strategy.expected_improvement,
            "optimization_actions": strategy.actions,
            "cache_hit_probability": self._estimate_cache_hit_probability(context),
            "performance_prediction": self._predict_performance(context),
        }

    def _estimate_cache_hit_probability(self, context: PromptingContext) -> float:
        """Estimate probability of cache hit for context."""
        # Simple heuristic based on domain and complexity
        base_probability = 0.3

        # Common domains have higher hit probability
        if context.domain in ["security", "architecture", "debugging"]:
            base_probability += 0.2

        # Simple queries more likely to be cached
        if context.complexity == "simple":
            base_probability += 0.1

        return min(base_probability, 0.8)

    def _predict_performance(self, context: PromptingContext) -> dict[str, float]:
        """Predict performance characteristics for context."""
        return {
            "estimated_response_time": 0.5 if context.complexity == "simple" else 2.0,
            "estimated_memory_usage": 64 if context.complexity == "simple" else 256,
            "confidence_level": 0.8 if context.domain in ["security", "architecture"] else 0.6,
        }
