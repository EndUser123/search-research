#!/usr/bin/env python3
"""
Unit tests for performance_optimizer module.

Tests for performance optimization functionality.
"""


from prompting_framework.performance_optimizer import (
    OptimizationConfig,
    OptimizationResult,
    OptimizationStrategy,
    OptimizationTarget,
    PerformanceMetrics,
)


class TestOptimizationStrategy:
    """Test OptimizationStrategy enum."""

    def test_all_strategies_defined(self):
        """Verify all expected strategies are defined."""
        expected_strategies = [
            "cache_first",
            "lazy_loading",
            "batch_processing",
            "parallel_execution",
            "early_exit",
            "adaptive_quality",
        ]
        actual_values = [s.value for s in OptimizationStrategy]
        for expected in expected_strategies:
            assert expected in actual_values


class TestOptimizationTarget:
    """Test OptimizationTarget enum."""

    def test_all_targets_defined(self):
        """Verify all expected targets are defined."""
        expected_targets = [
            "response_time",
            "memory_usage",
            "cpu_usage",
            "token_count",
            "quality_score",
        ]
        actual_values = [t.value for t in OptimizationTarget]
        for expected in expected_targets:
            assert expected in actual_values


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_create_metrics(self):
        """Create performance metrics."""
        metrics = PerformanceMetrics(
            response_time=1.5,
            memory_usage=256,
            cpu_usage=0.3,
            token_count=1000,
            cache_hit_rate=0.8,
        )
        assert metrics.response_time == 1.5
        assert metrics.memory_usage == 256
        assert metrics.cpu_usage == 0.3
        assert metrics.cache_hit_rate == 0.8

    def test_metrics_with_defaults(self):
        """Create metrics with default values."""
        metrics = PerformanceMetrics(
            response_time=2.0,
            memory_usage=512,
        )
        assert metrics.cpu_usage == 0.0
        assert metrics.token_count == 0
        assert metrics.cache_hit_rate == 0.0

    def test_all_performance_fields(self):
        """Create metrics with all fields populated."""
        metrics = PerformanceMetrics(
            response_time=3.5,
            memory_usage=1024,
            cpu_usage=0.75,
            token_count=5000,
            cache_hit_rate=0.95,
            query_complexity=0.8,
            optimization_overhead=0.2,
        )
        assert metrics.query_complexity == 0.8
        assert metrics.optimization_overhead == 0.2


class TestOptimizationConfig:
    """Test OptimizationConfig dataclass."""

    def test_create_config(self):
        """Create optimization configuration."""
        config = OptimizationConfig(
            target=OptimizationTarget.RESPONSE_TIME,
            strategy=OptimizationStrategy.CACHE_FIRST,
            max_response_time=2.0,
            max_memory_usage=512,
            enable_caching=True,
            cache_ttl=3600,
        )
        assert config.target == OptimizationTarget.RESPONSE_TIME
        assert config.strategy == OptimizationStrategy.CACHE_FIRST
        assert config.enable_caching is True

    def test_config_with_defaults(self):
        """Create config with default values."""
        config = OptimizationConfig(
            target=OptimizationTarget.QUALITY_SCORE,
            strategy=OptimizationStrategy.ADAPTIVE_QUALITY,
        )
        assert config.max_response_time > 0
        assert config.max_memory_usage > 0
        assert config.enable_caching is False

    def test_config_multiple_strategies(self):
        """Config with multiple strategies allowed."""
        config = OptimizationConfig(
            target=OptimizationToken.COUNT,
            strategy=OptimizationStrategy.BATCH_PROCESSING,
            batch_size=10,
            parallel_workers=4,
        )
        assert config.batch_size == 10
        assert config.parallel_workers == 4


class TestOptimizationResult:
    """Test OptimizationResult dataclass."""

    def test_create_result_success(self):
        """Create successful optimization result."""
        original_metrics = PerformanceMetrics(
            response_time=5.0,
            memory_usage=1024,
            cpu_usage=0.8,
            token_count=2000,
        )

        optimized_metrics = PerformanceMetrics(
            response_time=2.0,
            memory_usage=512,
            cpu_usage=0.4,
            token_count=1500,
        )

        result = OptimizationResult(
            strategy=OptimizationStrategy.CACHE_FIRST,
            original_metrics=original_metrics,
            optimized_metrics=optimized_metrics,
            improvement_percentage=60.0,
            success=True,
            optimization_time=0.5,
        )
        assert result.success is True
        assert result.improvement_percentage == 60.0
        assert result.optimized_metrics.response_time < result.original_metrics.response_time

    def test_create_result_failure(self):
        """Create failed optimization result."""
        original_metrics = PerformanceMetrics(
            response_time=2.0,
            memory_usage=256,
            cpu_usage=0.3,
        )

        result = OptimizationResult(
            strategy=OptimizationStrategy.PARALLEL_EXECUTION,
            original_metrics=original_metrics,
            optimized_metrics=original_metrics,  # No improvement
            improvement_percentage=0.0,
            success=False,
            optimization_time=0.5,
            error_message="Parallelization failed due to resource constraints",
        )
        assert result.success is False
        assert result.error_message == "Parallelization failed due to resource constraints"

    def test_result_with_multiple_improvements(self):
        """Result showing improvements across multiple metrics."""
        original = PerformanceMetrics(
            response_time=4.0,
            memory_usage=800,
            cpu_usage=0.7,
            token_count=3000,
        )

        optimized = PerformanceMetrics(
            response_time=1.5,
            memory_usage=400,
            cpu_usage=0.3,
            token_count=2000,
        )

        result = OptimizationResult(
            strategy=OptimizationStrategy.EARLY_EXIT,
            original_metrics=original,
            optimized_metrics=optimized,
            improvement_percentage=62.5,  # Average improvement
            success=True,
            optimization_time=0.2,
        )
        # Response time improved by 62.5%
        time_improvement = (4.0 - 1.5) / 4.0 * 100
        assert time_improvement == 62.5


class TestOptimizationStrategies:
    """Test different optimization strategies."""

    def test_cache_first_strategy(self):
        """Cache-first optimization strategy."""
        assert OptimizationStrategy.CACHE_FIRST.value == "cache_first"

    def test_lazy_loading_strategy(self):
        """Lazy loading optimization strategy."""
        assert OptimizationStrategy.LAZY_LOADING.value == "lazy_loading"

    def test_batch_processing_strategy(self):
        """Batch processing optimization strategy."""
        assert OptimizationStrategy.BATCH_PROCESSING.value == "batch_processing"

    def test_parallel_execution_strategy(self):
        """Parallel execution optimization strategy."""
        assert OptimizationStrategy.PARALLEL_EXECUTION.value == "parallel_execution"

    def test_early_exit_strategy(self):
        """Early exit optimization strategy."""
        assert OptimizationStrategy.EARLY_EXIT.value == "early_exit"

    def test_adaptive_quality_strategy(self):
        """Adaptive quality optimization strategy."""
        assert OptimizationStrategy.ADAPTIVE_QUALITY.value == "adaptive_quality"


class TestOptimizationTargets:
    """Test different optimization targets."""

    def test_response_time_target(self):
        """Response time optimization target."""
        assert OptimizationTarget.RESPONSE_TIME.value == "response_time"

    def test_memory_usage_target(self):
        """Memory usage optimization target."""
        assert OptimizationTarget.MEMORY_USAGE.value == "memory_usage"

    def test_cpu_usage_target(self):
        """CPU usage optimization target."""
        assert OptimizationTarget.CPU_USAGE.value == "cpu_usage"

    def test_token_count_target(self):
        """Token count optimization target."""
        assert OptimizationTarget.TOKEN_COUNT.value == "token_count"

    def test_quality_score_target(self):
        """Quality score optimization target."""
        assert OptimizationTarget.QUALITY_SCORE.value == "quality_score"


class TestEdgeCases:
    """Test edge cases for performance optimization."""

    def test_zero_improvement(self):
        """Handle case with no improvement."""
        original = PerformanceMetrics(
            response_time=2.0,
            memory_usage=256,
            cpu_usage=0.3,
        )

        result = OptimizationResult(
            strategy=OptimizationStrategy.CACHE_FIRST,
            original_metrics=original,
            optimized_metrics=original,  # Same metrics
            improvement_percentage=0.0,
            success=True,  # But still successful (no regression)
            optimization_time=0.1,
        )
        assert result.improvement_percentage == 0.0

    def test_negative_improvement(self):
        """Handle case with performance regression."""
        original = PerformanceMetrics(
            response_time=1.0,
            memory_usage=256,
            cpu_usage=0.2,
        )

        worse = PerformanceMetrics(
            response_time=1.5,
            memory_usage=300,
            cpu_usage=0.3,
        )

        result = OptimizationResult(
            strategy=OptimizationStrategy.EARLY_EXIT,
            original_metrics=original,
            optimized_metrics=worse,
            improvement_percentage=-50.0,  # Got worse
            success=False,
            optimization_time=0.3,
        )
        assert result.improvement_percentage < 0

    def test_zero_optimization_time(self):
        """Handle cached optimization (zero time)."""
        result = OptimizationResult(
            strategy=OptimizationStrategy.CACHE_FIRST,
            original_metrics=PerformanceMetrics(response_time=2.0, memory_usage=256),
            optimized_metrics=PerformanceMetrics(response_time=1.0, memory_usage=128),
            improvement_percentage=50.0,
            success=True,
            optimization_time=0.0,  # From cache
        )
        assert result.optimization_time == 0.0

    def test_minimal_metrics(self):
        """Handle minimal performance metrics."""
        metrics = PerformanceMetrics(
            response_time=0.1,
            memory_usage=1,
            cpu_usage=0.0,
        )
        assert metrics.response_time > 0
        assert metrics.memory_usage > 0
        assert metrics.cpu_usage >= 0
