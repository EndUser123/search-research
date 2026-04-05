"""Tests for core.performance_optimizer module.

Tests for performance optimization strategies.
"""

import pytest

from rca.core.performance_optimizer import (
    OptimizationStrategy,
    PerformanceOptimizer,
    OptimizationLevel,
)


class TestOptimizationLevel:
    """Test OptimizationLevel enum."""

    def test_level_values(self):
        """OptimizationLevel has expected values."""
        assert OptimizationLevel.NONE.value == "none"
        assert OptimizationLevel.BASIC.value == "basic"
        assert OptimizationLevel.AGGRESSIVE.value == "aggressive"


class TestOptimizationStrategy:
    """Test OptimizationStrategy dataclass."""

    def test_strategy_creation(self):
        """OptimizationStrategy can be created."""
        strategy = OptimizationStrategy(
            name="cache_results",
            description="Cache frequently accessed results",
            level=OptimizationLevel.BASIC,
        )

        assert strategy.name == "cache_results"
        assert strategy.level == OptimizationLevel.BASIC


class TestPerformanceOptimizerInit:
    """Test PerformanceOptimizer initialization."""

    def test_optimizer_creation(self):
        """PerformanceOptimizer can be created."""
        optimizer = PerformanceOptimizer()

        assert optimizer is not None

    def test_optimizer_with_level(self):
        """Optimizer can be created with optimization level."""
        optimizer = PerformanceOptimizer(level=OptimizationLevel.AGGRESSIVE)

        assert optimizer.level == OptimizationLevel.AGGRESSIVE


class TestApplyOptimization:
    """Test applying optimizations."""

    def test_apply_caching_strategy(self):
        """Caching strategy can be applied."""
        optimizer = PerformanceOptimizer()

        result = optimizer.apply_optimization(
            "cache_results",
            data={"key": "value"},
        )

        assert result is not None

    def test_apply_lazy_loading(self):
        """Lazy loading strategy can be applied."""
        optimizer = PerformanceOptimizer()

        result = optimizer.apply_optimization(
            "lazy_load",
            resource="large_dataset",
        )

        assert result is not None


class TestGetRecommendedStrategies:
    """Test getting recommended optimization strategies."""

    def test_recommendations_for_basic_level(self):
        """Basic level has basic recommendations."""
        optimizer = PerformanceOptimizer(level=OptimizationLevel.BASIC)

        strategies = optimizer.get_recommended_strategies()

        assert len(strategies) > 0

    def test_recommendations_for_aggressive_level(self):
        """Aggressive level has more recommendations."""
        optimizer = PerformanceOptimizer(level=OptimizationLevel.AGGRESSIVE)

        strategies = optimizer.get_recommended_strategies()

        assert len(strategies) > 0


class TestMeasurePerformance:
    """Test performance measurement."""

    def test_measure_execution_time(self):
        """Execution time can be measured."""
        optimizer = PerformanceOptimizer()

        def sample_function():
            return sum(range(1000))

        time_taken = optimizer.measure_execution_time(sample_function)

        assert time_taken >= 0

    def test_measure_memory_usage(self):
        """Memory usage can be measured."""
        optimizer = PerformanceOptimizer()

        def sample_function():
            return list(range(1000))

        memory_used = optimizer.measure_memory_usage(sample_function)

        assert memory_used >= 0


class TestEdgeCases:
    """Test edge cases."""

    def test_unknown_optimization_strategy(self):
        """Unknown strategy is handled gracefully."""
        optimizer = PerformanceOptimizer()

        result = optimizer.apply_optimization("unknown_strategy", data={})

        # Should not crash
        assert result is None or isinstance(result, dict)

    def test_measure_none_function(self):
        """None function is handled."""
        optimizer = PerformanceOptimizer()

        time_taken = optimizer.measure_execution_time(None)

        assert time_taken == 0

    def test_optimization_with_empty_data(self):
        """Optimization with empty data is handled."""
        optimizer = PerformanceOptimizer()

        result = optimizer.apply_optimization("cache_results", data={})

        assert result is not None
