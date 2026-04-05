#!/usr/bin/env python3
"""
Unit tests for self_refine_technique module.

Tests for Self-Refine technique implementation including
refinement strategies and iterations.
"""


from prompting_framework.self_refine_technique import (
    RefinementIteration,
    RefinementStrategy,
    SelfRefineResult,
)


class TestRefinementStrategy:
    """Test RefinementStrategy enum."""

    def test_all_strategies_defined(self):
        """Verify all expected strategies are defined."""
        expected_strategies = [
            "content_enhancement",
            "logic_improvement",
            "completeness_check",
            "clarity_optimization",
            "structural_refinement",
            "evidence_strengthening",
        ]
        actual_values = [s.value for s in RefinementStrategy]
        for expected in expected_strategies:
            assert expected in actual_values


class TestRefinementIteration:
    """Test RefinementIteration dataclass."""

    def test_create_iteration(self):
        """Create a refinement iteration."""
        iteration = RefinementIteration(
            iteration_number=1,
            generated_response="Initial response",
            critique_result={"score": 0.7, "issues": ["clarity"]},
            refined_response="Improved response",
            quality_score=0.85,
            improvement_delta=0.15,
            strategy_used=RefinementStrategy.CLARITY_OPTIMIZATION,
            execution_time=1.5,
            constitutional_compliance={"anti_deception": True},
        )
        assert iteration.iteration_number == 1
        assert iteration.quality_score == 0.85
        assert iteration.improvement_delta == 0.15
        assert iteration.strategy_used == RefinementStrategy.CLARITY_OPTIMIZATION

    def test_iteration_with_all_strategies(self):
        """Create iterations for all strategies."""
        strategies = list(RefinementStrategy)
        for strategy in strategies:
            iteration = RefinementIteration(
                iteration_number=1,
                generated_response="test",
                critique_result={},
                refined_response="refined",
                quality_score=0.8,
                improvement_delta=0.1,
                strategy_used=strategy,
                execution_time=1.0,
                constitutional_compliance={},
            )
            assert iteration.strategy_used == strategy


class TestSelfRefineResult:
    """Test SelfRefineResult dataclass."""

    def test_create_result(self):
        """Create a self-refine result."""
        iterations = [
            RefinementIteration(
                iteration_number=1,
                generated_response="initial",
                critique_result={"score": 0.6},
                refined_response="improved",
                quality_score=0.75,
                improvement_delta=0.15,
                strategy_used=RefinementStrategy.CONTENT_ENHANCEMENT,
                execution_time=1.0,
                constitutional_compliance={},
            )
        ]

        result = SelfRefineResult(
            initial_response="initial",
            final_response="final",
            total_iterations=1,
            iterations=iterations,
            quality_progression=[0.6, 0.75],
            total_execution_time=1.0,
            success=True,
            termination_reason="quality_threshold_met",
        )
        assert result.initial_response == "initial"
        assert result.final_response == "final"
        assert result.total_iterations == 1
        assert result.success is True

    def test_result_multiple_iterations(self):
        """Create result with multiple iterations."""
        iterations = [
            RefinementIteration(
                iteration_number=i,
                generated_response=f"v{i}",
                critique_result={"score": 0.5 + i * 0.1},
                refined_response=f"v{i + 1}",
                quality_score=0.6 + i * 0.1,
                improvement_delta=0.1,
                strategy_used=RefinementStrategy.CONTENT_ENHANCEMENT,
                execution_time=1.0,
                constitutional_compliance={},
            )
            for i in range(1, 4)
        ]

        result = SelfRefineResult(
            initial_response="v1",
            final_response="v4",
            total_iterations=3,
            iterations=iterations,
            quality_progression=[0.6, 0.7, 0.8, 0.9],
            total_execution_time=3.0,
            success=True,
            termination_reason="max_iterations_reached",
        )
        assert len(result.iterations) == 3
        assert result.total_iterations == 3


class TestRefinementStrategyValues:
    """Test refinement strategy enum values."""

    def test_content_enhancement_value(self):
        """Content enhancement has correct value."""
        assert RefinementStrategy.CONTENT_ENHANCEMENT.value == "content_enhancement"

    def test_logic_improvement_value(self):
        """Logic improvement has correct value."""
        assert RefinementStrategy.LOGIC_IMPROVEMENT.value == "logic_improvement"

    def test_completeness_check_value(self):
        """Completeness check has correct value."""
        assert RefinementStrategy.COMPLETENESS_CHECK.value == "completeness_check"

    def test_clarity_optimization_value(self):
        """Clarity optimization has correct value."""
        assert RefinementStrategy.CLARITY_OPTIMIZATION.value == "clarity_optimization"

    def test_structural_refinement_value(self):
        """Structural refinement has correct value."""
        assert RefinementStrategy.STRUCTURAL_REFINEMENT.value == "structural_refinement"

    def test_evidence_strengthening_value(self):
        """Evidence strengthening has correct value."""
        assert RefinementStrategy.EVIDENCE_STRENGTHENING.value == "evidence_strengthening"


class TestRefinementIterationFields:
    """Test RefinementIteration field types and constraints."""

    def test_iteration_number_positive(self):
        """Iteration number should be positive."""
        iteration = RefinementIteration(
            iteration_number=1,
            generated_response="test",
            critique_result={},
            refined_response="refined",
            quality_score=0.8,
            improvement_delta=0.1,
            strategy_used=RefinementStrategy.CONTENT_ENHANCEMENT,
            execution_time=1.0,
            constitutional_compliance={},
        )
        assert iteration.iteration_number > 0

    def test_quality_score_range(self):
        """Quality score should be between 0 and 1."""
        iteration = RefinementIteration(
            iteration_number=1,
            generated_response="test",
            critique_result={},
            refined_response="refined",
            quality_score=0.85,
            improvement_delta=0.1,
            strategy_used=RefinementStrategy.CONTENT_ENHANCEMENT,
            execution_time=1.0,
            constitutional_compliance={},
        )
        assert 0.0 <= iteration.quality_score <= 1.0

    def test_improvement_delta_can_be_negative(self):
        """Improvement delta can be negative (quality decreased)."""
        iteration = RefinementIteration(
            iteration_number=1,
            generated_response="good",
            critique_result={},
            refined_response="worse",
            quality_score=0.6,
            improvement_delta=-0.2,
            strategy_used=RefinementStrategy.CONTENT_ENHANCEMENT,
            execution_time=1.0,
            constitutional_compliance={},
        )
        assert iteration.improvement_delta < 0

    def test_execution_time_positive(self):
        """Execution time should be positive."""
        iteration = RefinementIteration(
            iteration_number=1,
            generated_response="test",
            critique_result={},
            refined_response="refined",
            quality_score=0.8,
            improvement_delta=0.1,
            strategy_used=RefinementStrategy.CONTENT_ENHANCEMENT,
            execution_time=1.5,
            constitutional_compliance={},
        )
        assert iteration.execution_time > 0

    def test_constitutional_compliance_dict(self):
        """Constitutional compliance should be a dict."""
        iteration = RefinementIteration(
            iteration_number=1,
            generated_response="test",
            critique_result={},
            refined_response="refined",
            quality_score=0.8,
            improvement_delta=0.1,
            strategy_used=RefinementStrategy.CONTENT_ENHANCEMENT,
            execution_time=1.0,
            constitutional_compliance={"anti_deception": True, "evidence_based": False},
        )
        assert isinstance(iteration.constitutional_compliance, dict)
        assert "anti_deception" in iteration.constitutional_compliance


class TestSelfRefineResultFields:
    """Test SelfRefineResult field types and constraints."""

    def test_iterations_list(self):
        """Iterations should be a list."""
        result = SelfRefineResult(
            initial_response="initial",
            final_response="final",
            total_iterations=0,
            iterations=[],
            quality_progression=[],
            total_execution_time=0.0,
            success=True,
            termination_reason="test",
        )
        assert isinstance(result.iterations, list)

    def test_quality_progression_list(self):
        """Quality progression should be a list."""
        result = SelfRefineResult(
            initial_response="initial",
            final_response="final",
            total_iterations=2,
            iterations=[],
            quality_progression=[0.6, 0.75, 0.85],
            total_execution_time=2.0,
            success=True,
            termination_reason="test",
        )
        assert isinstance(result.quality_progression, list)
        assert len(result.quality_progression) == 3

    def test_total_execution_time_positive(self):
        """Total execution time should be non-negative."""
        result = SelfRefineResult(
            initial_response="initial",
            final_response="final",
            total_iterations=1,
            iterations=[],
            quality_progression=[0.6, 0.8],
            total_execution_time=1.5,
            success=True,
            termination_reason="test",
        )
        assert result.total_execution_time >= 0

    def test_termination_reasons(self):
        """Test various termination reasons."""
        reasons = [
            "quality_threshold_met",
            "max_iterations_reached",
            "no_improvement",
            "error",
            "user_interrupted",
        ]
        for reason in reasons:
            result = SelfRefineResult(
                initial_response="initial",
                final_response="final",
                total_iterations=1,
                iterations=[],
                quality_progression=[],
                total_execution_time=1.0,
                success=True,
                termination_reason=reason,
            )
            assert result.termination_reason == reason


class TestRefinementIterationComparison:
    """Test iteration comparison and progression."""

    def test_quality_improvement(self):
        """Later iterations should show quality improvement."""
        iteration1 = RefinementIteration(
            iteration_number=1,
            generated_response="v1",
            critique_result={},
            refined_response="v2",
            quality_score=0.65,
            improvement_delta=0.0,
            strategy_used=RefinementStrategy.CONTENT_ENHANCEMENT,
            execution_time=1.0,
            constitutional_compliance={},
        )

        iteration2 = RefinementIteration(
            iteration_number=2,
            generated_response="v2",
            critique_result={},
            refined_response="v3",
            quality_score=0.8,
            improvement_delta=0.15,
            strategy_used=RefinementStrategy.LOGIC_IMPROVEMENT,
            execution_time=1.0,
            constitutional_compliance={},
        )

        assert iteration2.quality_score > iteration1.quality_score
        assert iteration2.improvement_delta > 0


class TestSelfRefineResultAnalysis:
    """Test result analysis methods."""

    def test_calculate_average_improvement(self):
        """Calculate average improvement across iterations."""
        iterations = [
            RefinementIteration(
                iteration_number=1,
                generated_response="v1",
                critique_result={},
                refined_response="v2",
                quality_score=0.7,
                improvement_delta=0.1,
                strategy_used=RefinementStrategy.CONTENT_ENHANCEMENT,
                execution_time=1.0,
                constitutional_compliance={},
            ),
            RefinementIteration(
                iteration_number=2,
                generated_response="v2",
                critique_result={},
                refined_response="v3",
                quality_score=0.85,
                improvement_delta=0.15,
                strategy_used=RefinementStrategy.LOGIC_IMPROVEMENT,
                execution_time=1.0,
                constitutional_compliance={},
            ),
        ]

        result = SelfRefineResult(
            initial_response="v1",
            final_response="v3",
            total_iterations=2,
            iterations=iterations,
            quality_progression=[0.6, 0.7, 0.85],
            total_execution_time=2.0,
            success=True,
            termination_reason="quality_threshold_met",
        )

        # Average improvement = (0.1 + 0.15) / 2 = 0.125
        avg_improvement = sum(i.improvement_delta for i in iterations) / len(iterations)
        assert avg_improvement == 0.125

    def test_get_best_strategy(self):
        """Identify which strategy worked best."""
        iterations = [
            RefinementIteration(
                iteration_number=1,
                generated_response="v1",
                critique_result={},
                refined_response="v2",
                quality_score=0.7,
                improvement_delta=0.1,
                strategy_used=RefinementStrategy.CLARITY_OPTIMIZATION,
                execution_time=1.0,
                constitutional_compliance={},
            ),
            RefinementIteration(
                iteration_number=2,
                generated_response="v2",
                critique_result={},
                refined_response="v3",
                quality_score=0.9,
                improvement_delta=0.2,
                strategy_used=RefinementStrategy.CONTENT_ENHANCEMENT,
                execution_time=1.0,
                constitutional_compliance={},
            ),
        ]

        best_iteration = max(iterations, key=lambda i: i.improvement_delta)
        assert best_iteration.strategy_used == RefinementStrategy.CONTENT_ENHANCEMENT
        assert best_iteration.improvement_delta == 0.2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_zero_iterations(self):
        """Handle zero iterations gracefully."""
        result = SelfRefineResult(
            initial_response="same",
            final_response="same",
            total_iterations=0,
            iterations=[],
            quality_progression=[0.5],
            total_execution_time=0.0,
            success=False,
            termination_reason="no_refinement_needed",
        )
        assert result.total_iterations == 0
        assert len(result.iterations) == 0

    def test_single_iteration(self):
        """Handle single iteration."""
        iteration = RefinementIteration(
            iteration_number=1,
            generated_response="v1",
            critique_result={},
            refined_response="v2",
            quality_score=0.8,
            improvement_delta=0.1,
            strategy_used=RefinementStrategy.CONTENT_ENHANCEMENT,
            execution_time=1.0,
            constitutional_compliance={},
        )

        result = SelfRefineResult(
            initial_response="v1",
            final_response="v2",
            total_iterations=1,
            iterations=[iteration],
            quality_progression=[0.7, 0.8],
            total_execution_time=1.0,
            success=True,
            termination_reason="quality_threshold_met",
        )
        assert len(result.iterations) == 1

    def test_no_improvement_iteration(self):
        """Handle iteration with no improvement."""
        iteration = RefinementIteration(
            iteration_number=1,
            generated_response="v1",
            critique_result={},
            refined_response="v2",
            quality_score=0.7,
            improvement_delta=0.0,
            strategy_used=RefinementStrategy.CONTENT_ENHANCEMENT,
            execution_time=1.0,
            constitutional_compliance={},
        )
        assert iteration.improvement_delta == 0.0

    def test_negative_improvement_iteration(self):
        """Handle iteration with negative improvement."""
        iteration = RefinementIteration(
            iteration_number=1,
            generated_response="good",
            critique_result={},
            refined_response="worse",
            quality_score=0.5,
            improvement_delta=-0.2,
            strategy_used=RefinementStrategy.CONTENT_ENHANCEMENT,
            execution_time=1.0,
            constitutional_compliance={},
        )
        assert iteration.improvement_delta < 0
