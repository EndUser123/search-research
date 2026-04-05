#!/usr/bin/env python3
"""
Unit tests for prompting_orchestrator module.

Tests for prompting orchestration functionality.
"""


from prompting_framework.prompting_orchestrator import (
    OrchestrationMode,
    OrchestrationRequest,
    OrchestrationResult,
    OrchestrationStrategy,
    OrchestratorConfig,
)


class TestOrchestrationMode:
    """Test OrchestrationMode enum."""

    def test_all_modes_defined(self):
        """Verify all expected modes are defined."""
        expected_modes = [
            "single",
            "sequential",
            "parallel",
            "hierarchical",
            "adaptive",
        ]
        actual_values = [m.value for m in OrchestrationMode]
        for expected in expected_modes:
            assert expected in actual_values


class TestOrchestrationStrategy:
    """Test OrchestrationStrategy enum."""

    def test_all_strategies_defined(self):
        """Verify all expected strategies are defined."""
        expected_strategies = [
            "quality_first",
            "speed_first",
            "balanced",
            "resource_optimized",
            "cost_optimized",
        ]
        actual_values = [s.value for s in OrchestrationStrategy]
        for expected in expected_strategies:
            assert expected in actual_values


class TestOrchestrationRequest:
    """Test OrchestrationRequest dataclass."""

    def test_create_request(self):
        """Create an orchestration request."""
        request = OrchestrationRequest(
            request_id="req_1",
            prompt="Analyze this code",
            mode=OrchestrationMode.SEQUENTIAL,
            strategy=OrchestrationStrategy.QUALITY_FIRST,
            techniques=["chain_of_thought", "self_refine"],
            max_iterations=3,
            timeout=30.0,
        )
        assert request.request_id == "req_1"
        assert request.mode == OrchestrationMode.SEQUENTIAL
        assert len(request.techniques) == 2

    def test_request_with_defaults(self):
        """Create request with default values."""
        request = OrchestrationRequest(
            request_id="req_2",
            prompt="Simple request",
        )
        assert request.mode == OrchestrationMode.SINGLE
        assert request.strategy == OrchestrationStrategy.BALANCED
        assert request.techniques == []
        assert request.max_iterations == 1

    def test_request_multiple_techniques(self):
        """Create request with multiple techniques."""
        request = OrchestrationRequest(
            request_id="req_3",
            prompt="Complex analysis",
            mode=OrchestrationMode.PARALLEL,
            techniques=[
                "chain_of_thought",
                "self_refine",
                "chain_of_verification",
                "query_fanout",
            ],
            max_iterations=5,
        )
        assert len(request.techniques) == 4


class TestOrchestrationResult:
    """Test OrchestrationResult dataclass."""

    def test_create_result_success(self):
        """Create successful orchestration result."""
        result = OrchestrationResult(
            request_id="req_1",
            success=True,
            final_response="Here is the analyzed code",
            techniques_applied=["chain_of_thought", "self_refine"],
            execution_time=5.5,
            iterations_completed=2,
            quality_score=0.85,
            intermediate_results=[
                {"iteration": 1, "response": "Initial analysis"},
                {"iteration": 2, "response": "Refined analysis"},
            ],
        )
        assert result.success is True
        assert len(result.techniques_applied) == 2
        assert result.quality_score == 0.85

    def test_create_result_failure(self):
        """Create failed orchestration result."""
        result = OrchestrationResult(
            request_id="req_2",
            success=False,
            final_response="",
            techniques_applied=[],
            execution_time=1.0,
            iterations_completed=0,
            error_message="Timeout: Request exceeded 30s limit",
        )
        assert result.success is False
        assert "Timeout" in result.error_message

    def test_result_with_progression(self):
        """Result showing progression through iterations."""
        result = OrchestrationResult(
            request_id="req_3",
            success=True,
            final_response="Final refined answer",
            techniques_applied=["self_refine"],
            execution_time=8.0,
            iterations_completed=3,
            quality_score=0.92,
            intermediate_results=[
                {"iteration": 1, "response": "Draft 1", "quality": 0.7},
                {"iteration": 2, "response": "Draft 2", "quality": 0.85},
                {"iteration": 3, "response": "Final", "quality": 0.92},
            ],
        )
        assert result.iterations_completed == 3
        assert len(result.intermediate_results) == 3


class TestOrchestratorConfig:
    """Test OrchestratorConfig dataclass."""

    def test_create_config(self):
        """Create orchestrator configuration."""
        config = OrchestratorConfig(
            default_mode=OrchestrationMode.ADAPTIVE,
            default_strategy=OrchestrationStrategy.BALANCED,
            max_parallelism=4,
            default_timeout=60.0,
            enable_caching=True,
            cache_ttl=3600,
            quality_threshold=0.7,
        )
        assert config.default_mode == OrchestrationMode.ADAPTIVE
        assert config.max_parallelism == 4
        assert config.enable_caching is True

    def test_config_with_defaults(self):
        """Create config with default values."""
        config = OrchestratorConfig()
        assert config.default_mode == OrchestrationMode.SINGLE
        assert config.default_strategy == OrchestrationStrategy.BALANCED
        assert config.max_parallelism == 1
        assert config.enable_caching is False

    def test_config_high_performance(self):
        """High-performance configuration."""
        config = OrchestratorConfig(
            default_mode=OrchestrationMode.PARALLEL,
            default_strategy=OrchestrationStrategy.SPEED_FIRST,
            max_parallelism=10,
            default_timeout=10.0,
            enable_caching=True,
            cache_ttl=7200,
            quality_threshold=0.5,  # Lower threshold for speed
        )
        assert config.max_parallelism == 10
        assert config.default_timeout == 10.0
        assert config.quality_threshold < 0.6


class TestOrchestrationModes:
    """Test different orchestration modes."""

    def test_single_mode(self):
        """Single execution mode."""
        assert OrchestrationMode.SINGLE.value == "single"

    def test_sequential_mode(self):
        """Sequential execution mode."""
        assert OrchestrationMode.SEQUENTIAL.value == "sequential"

    def test_parallel_mode(self):
        """Parallel execution mode."""
        assert OrchestrationMode.PARALLEL.value == "parallel"

    def test_hierarchical_mode(self):
        """Hierarchical execution mode."""
        assert OrchestrationMode.HIERARCHICAL.value == "hierarchical"

    def test_adaptive_mode(self):
        """Adaptive execution mode."""
        assert OrchestrationMode.ADAPTIVE.value == "adaptive"


class TestOrchestrationStrategies:
    """Test different orchestration strategies."""

    def test_quality_first_strategy(self):
        """Quality-first strategy."""
        assert OrchestrationStrategy.QUALITY_FIRST.value == "quality_first"

    def test_speed_first_strategy(self):
        """Speed-first strategy."""
        assert OrchestrationStrategy.SPEED_FIRST.value == "speed_first"

    def test_balanced_strategy(self):
        """Balanced strategy."""
        assert OrchestrationStrategy.BALANCED.value == "balanced"

    def test_resource_optimized_strategy(self):
        """Resource-optimized strategy."""
        assert OrchestrationStrategy.RESOURCE_OPTIMIZED.value == "resource_optimized"

    def test_cost_optimized_strategy(self):
        """Cost-optimized strategy."""
        assert OrchestrationStrategy.COST_OPTIMIZED.value == "cost_optimized"


class TestEdgeCases:
    """Test edge cases for orchestration."""

    def test_empty_techniques_list(self):
        """Handle request with no techniques."""
        request = OrchestrationRequest(
            request_id="no_tech",
            prompt="Direct question",
            techniques=[],
        )
        assert len(request.techniques) == 0

    def test_zero_iterations(self):
        """Handle result with zero iterations."""
        result = OrchestrationResult(
            request_id="zero",
            success=False,
            final_response="",
            techniques_applied=[],
            execution_time=0.0,
            iterations_completed=0,
            error_message="No techniques to apply",
        )
        assert result.iterations_completed == 0

    def test_zero_timeout(self):
        """Handle immediate timeout."""
        result = OrchestrationResult(
            request_id="timeout",
            success=False,
            final_response="",
            techniques_applied=[],
            execution_time=0.0,
            iterations_completed=0,
            error_message="Timeout: 0s limit exceeded",
        )
        assert "Timeout" in result.error_message

    def test_max_quality_score(self):
        """Handle perfect quality score."""
        result = OrchestrationResult(
            request_id="perfect",
            success=True,
            final_response="Perfect answer",
            techniques_applied=["chain_of_thought"],
            execution_time=5.0,
            iterations_completed=1,
            quality_score=1.0,
        )
        assert result.quality_score == 1.0

    def test_min_quality_score(self):
        """Handle minimum quality score."""
        result = OrchestrationResult(
            request_id="poor",
            success=True,
            final_response="Poor answer",
            techniques_applied=["zero_shot"],
            execution_time=1.0,
            iterations_completed=1,
            quality_score=0.0,
        )
        assert result.quality_score == 0.0


class TestComplexOrchestrations:
    """Test complex orchestration scenarios."""

    def test_multi_technique_sequential(self):
        """Sequential application of multiple techniques."""
        result = OrchestrationResult(
            request_id="multi_seq",
            success=True,
            final_response="Highly refined response",
            techniques_applied=[
                "chain_of_thought",
                "self_refine",
                "chain_of_verification",
            ],
            execution_time=15.0,
            iterations_completed=3,
            quality_score=0.95,
            intermediate_results=[
                {"technique": "chain_of_thought", "response": "Reasoned response"},
                {"technique": "self_refine", "response": "Refined response"},
                {"technique": "chain_of_verification", "response": "Verified response"},
            ],
        )
        assert len(result.techniques_applied) == 3

    def test_parallel_multi_technique(self):
        """Parallel execution of multiple techniques."""
        request = OrchestrationRequest(
            request_id="parallel",
            prompt="Analyze from multiple angles",
            mode=OrchestrationMode.PARALLEL,
            techniques=["query_fanout", "socratic", "chain_of_thought"],
            max_parallelism=3,
        )
        assert request.mode == OrchestrationMode.PARALLEL
        assert request.max_parallelism >= 3
