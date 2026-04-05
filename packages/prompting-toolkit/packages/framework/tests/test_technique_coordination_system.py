#!/usr/bin/env python3
"""
Unit tests for technique_coordination_system module.

Tests for technique coordination system functionality.
"""


from prompting_framework.technique_coordination_system import (
    CoordinationPattern,
    CoordinationPlan,
    CoordinationResult,
    CoordinationStrategy,
    TechniqueDependency,
)


class TestCoordinationPattern:
    """Test CoordinationPattern enum."""

    def test_all_patterns_defined(self):
        """Verify all expected patterns are defined."""
        expected_patterns = [
            "sequential",
            "parallel",
            "hierarchical",
            "cyclic",
            "adaptive",
        ]
        actual_values = [p.value for p in CoordinationPattern]
        for expected in expected_patterns:
            assert expected in actual_values


class TestCoordinationStrategy:
    """Test CoordinationStrategy enum."""

    def test_all_strategies_defined(self):
        """Verify all expected strategies are defined."""
        expected_strategies = [
            "composition",
            "fusion",
            "ensemble",
            "cascade",
            "competitive",
        ]
        actual_values = [s.value for s in CoordinationStrategy]
        for expected in expected_strategies:
            assert expected in actual_values


class TestTechniqueDependency:
    """Test TechniqueDependency dataclass."""

    def test_create_dependency(self):
        """Create a technique dependency."""
        dependency = TechniqueDependency(
            technique="chain_of_thought",
            depends_on=["context_builder"],
            requires=["evidence_collector"],
            optional=["quality_checker"],
        )
        assert dependency.technique == "chain_of_thought"
        assert len(dependency.depends_on) == 1
        assert len(dependency.optional) == 1

    def test_dependency_no_requirements(self):
        """Create dependency with no requirements."""
        dependency = TechniqueDependency(
            technique="zero_shot",
            depends_on=[],
            requires=[],
            optional=[],
        )
        assert len(dependency.depends_on) == 0
        assert len(dependency.requires) == 0

    def test_complex_dependency(self):
        """Create complex dependency graph."""
        dependency = TechniqueDependency(
            technique="chain_of_verification",
            depends_on=["claim_extractor", "verification_generator"],
            requires=["source_validator", "fact_checker"],
            optional=["confidence_scorer", "ui_formatter"],
        )
        assert len(dependency.depends_on) == 2
        assert len(dependency.requires) == 2
        assert len(dependency.optional) == 2


class TestCoordinationPlan:
    """Test CoordinationPlan dataclass."""

    def test_create_plan(self):
        """Create a coordination plan."""
        dependencies = [
            TechniqueDependency(
                technique="chain_of_thought",
                depends_on=[],
                requires=["reasoner"],
            ),
            TechniqueDependency(
                technique="self_refine",
                depends_on=["chain_of_thought"],
                requires=["critiquer"],
            ),
        ]

        plan = CoordinationPlan(
            plan_id="plan_1",
            pattern=CoordinationPattern.SEQUENTIAL,
            strategy=CoordinationStrategy.COMPOSITION,
            techniques=["chain_of_thought", "self_refine"],
            dependencies=dependencies,
            estimated_duration=5.0,
        )
        assert plan.pattern == CoordinationPattern.SEQUENTIAL
        assert len(plan.techniques) == 2

    def test_parallel_plan(self):
        """Create parallel coordination plan."""
        plan = CoordinationPlan(
            plan_id="parallel_plan",
            pattern=CoordinationPattern.PARALLEL,
            strategy=CoordinationStrategy.ENSEMBLE,
            techniques=["query_fanout", "socratic", "chain_of_thought"],
            dependencies=[],
            estimated_duration=2.0,
        )
        assert plan.pattern == CoordinationPattern.PARALLEL
        assert plan.strategy == CoordinationStrategy.ENSEMBLE

    def test_hierarchical_plan(self):
        """Create hierarchical coordination plan."""
        plan = CoordinationPlan(
            plan_id="hierarchical_plan",
            pattern=CoordinationPattern.HIERARCHICAL,
            strategy=CoordinationStrategy.CASCADE,
            techniques=["context_analyzer", "chain_of_thought", "verifier"],
            dependencies=[
                TechniqueDependency(
                    technique="verifier",
                    depends_on=["context_analyzer", "chain_of_thought"],
                    requires=[],
                )
            ],
            estimated_duration=8.0,
        )
        assert plan.pattern == CoordinationPattern.HIERARCHICAL


class TestCoordinationResult:
    """Test CoordinationResult dataclass."""

    def test_create_result_success(self):
        """Create successful coordination result."""
        result = CoordinationResult(
            plan_id="plan_1",
            success=True,
            techniques_completed=["chain_of_thought", "self_refine"],
            execution_order=["chain_of_thought", "self_refine"],
            total_time=4.5,
            intermediate_outputs={
                "chain_of_thought": "Initial reasoning",
                "self_refine": "Refined output",
            },
            final_output="Final refined output",
        )
        assert result.success is True
        assert len(result.techniques_completed) == 2
        assert "final_output" in result.final_output.lower()

    def test_create_result_failure(self):
        """Create failed coordination result."""
        result = CoordinationResult(
            plan_id="plan_2",
            success=False,
            techniques_completed=["context_builder"],
            execution_order=["context_builder"],
            total_time=1.0,
            failed_at="chain_of_thought",
            error_message="Chain of thought technique failed to initialize",
        )
        assert result.success is False
        assert result.failed_at == "chain_of_thought"

    def test_result_with_partial_completion(self):
        """Result with partial technique completion."""
        result = CoordinationResult(
            plan_id="plan_3",
            success=False,
            techniques_completed=["technique_a", "technique_b"],
            execution_order=["technique_a", "technique_b", "technique_c"],
            total_time=3.0,
            intermediate_outputs={
                "technique_a": "Output A",
                "technique_b": "Output B",
            },
            failed_at="technique_c",
            error_message="Technique C timeout",
        )
        assert len(result.techniques_completed) == 2
        assert len(result.execution_order) == 3


class TestCoordinationPatterns:
    """Test different coordination patterns."""

    def test_sequential_pattern(self):
        """Sequential coordination pattern."""
        assert CoordinationPattern.SEQUENTIAL.value == "sequential"

    def test_parallel_pattern(self):
        """Parallel coordination pattern."""
        assert CoordinationPattern.PARALLEL.value == "parallel"

    def test_hierarchical_pattern(self):
        """Hierarchical coordination pattern."""
        assert CoordinationPattern.HIERARCHICAL.value == "hierarchical"

    def test_cyclic_pattern(self):
        """Cyclic coordination pattern."""
        assert CoordinationPattern.CYCLIC.value == "cyclic"

    def test_adaptive_pattern(self):
        """Adaptive coordination pattern."""
        assert CoordinationPattern.ADAPTIVE.value == "adaptive"


class TestCoordinationStrategies:
    """Test different coordination strategies."""

    def test_composition_strategy(self):
        """Composition coordination strategy."""
        assert CoordinationStrategy.COMPOSITION.value == "composition"

    def test_fusion_strategy(self):
        """Fusion coordination strategy."""
        assert CoordinationStrategy.FUSION.value == "fusion"

    def test_ensemble_strategy(self):
        """Ensemble coordination strategy."""
        assert CoordinationStrategy.ENSEMBLE.value == "ensemble"

    def test_cascade_strategy(self):
        """Cascade coordination strategy."""
        assert CoordinationStrategy.CASCADE.value == "cascade"

    def test_competitive_strategy(self):
        """Competitive coordination strategy."""
        assert CoordinationStrategy.COMPETITIVE.value == "competitive"


class TestEdgeCases:
    """Test edge cases for technique coordination."""

    def test_empty_plan(self):
        """Handle plan with no techniques."""
        plan = CoordinationPlan(
            plan_id="empty",
            pattern=CoordinationPattern.SEQUENTIAL,
            strategy=CoordinationStrategy.COMPOSITION,
            techniques=[],
            dependencies=[],
            estimated_duration=0.0,
        )
        assert len(plan.techniques) == 0

    def test_single_technique_plan(self):
        """Handle plan with single technique."""
        plan = CoordinationPlan(
            plan_id="single",
            pattern=CoordinationPattern.SEQUENTIAL,
            strategy=CoordinationStrategy.COMPOSITION,
            techniques=["zero_shot"],
            dependencies=[],
            estimated_duration=1.0,
        )
        assert len(plan.techniques) == 1

    def test_no_dependencies(self):
        """Handle techniques with no dependencies."""
        result = CoordinationResult(
            plan_id="no_deps",
            success=True,
            techniques_completed=["technique_a", "technique_b"],
            execution_order=["technique_a", "technique_b"],
            total_time=2.0,
            intermediate_outputs={},
            final_output="Combined output",
        )
        assert len(result.techniques_completed) == 2

    def test_zero_duration(self):
        """Handle cached plan (zero duration)."""
        plan = CoordinationPlan(
            plan_id="cached",
            pattern=CoordinationPattern.PARALLEL,
            strategy=CoordinationStrategy.ENSEMBLE,
            techniques=["cached_technique"],
            dependencies=[],
            estimated_duration=0.0,
        )
        assert plan.estimated_duration == 0.0


class TestComplexCoordination:
    """Test complex coordination scenarios."""

    def test_multi_level_hierarchy(self):
        """Multi-level hierarchical coordination."""
        dependencies = [
            TechniqueDependency(
                technique="level_3_final",
                depends_on=["level_2_a", "level_2_b"],
                requires=[],
            ),
            TechniqueDependency(
                technique="level_2_a",
                depends_on=["level_1"],
                requires=[],
            ),
            TechniqueDependency(
                technique="level_2_b",
                depends_on=["level_1"],
                requires=[],
            ),
        ]

        plan = CoordinationPlan(
            plan_id="multi_level",
            pattern=CoordinationPattern.HIERARCHICAL,
            strategy=CoordinationStrategy.CASCADE,
            techniques=["level_1", "level_2_a", "level_2_b", "level_3_final"],
            dependencies=dependencies,
            estimated_duration=10.0,
        )
        assert len(plan.techniques) == 4
        assert len(plan.dependencies) == 3

    def test_parallel_with_fusion(self):
        """Parallel execution with fusion strategy."""
        plan = CoordinationPlan(
            plan_id="parallel_fusion",
            pattern=CoordinationPattern.PARALLEL,
            strategy=CoordinationStrategy.FUSION,
            techniques=["socratic", "chain_of_thought", "query_fanout"],
            dependencies=[],
            estimated_duration=3.0,
        )
        assert plan.pattern == CoordinationPattern.PARALLEL
        assert plan.strategy == CoordinationStrategy.FUSION

    def test_cyclic_coordination(self):
        """Cyclic coordination pattern."""
        result = CoordinationResult(
            plan_id="cyclic",
            success=True,
            techniques_completed=["refine_1", "refine_2", "refine_3"],
            execution_order=["refine_1", "refine_2", "refine_3", "refine_1"],
            total_time=6.0,
            cycles_completed=2,
            final_output="Converged output",
        )
        assert "refine_1" in result.execution_order
        assert result.execution_order.count("refine_1") == 2
