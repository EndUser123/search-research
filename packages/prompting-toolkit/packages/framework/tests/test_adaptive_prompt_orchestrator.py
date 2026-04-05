#!/usr/bin/env python3
"""
Unit tests for adaptive_prompt_orchestrator module.

Tests for adaptive prompt orchestration functionality.
"""


from prompting_framework.adaptive_prompt_orchestrator import (
    AdaptationAction,
    AdaptationCriterion,
    AdaptationResult,
    AdaptationTrigger,
    OrchestratorState,
)


class TestAdaptationCriterion:
    """Test AdaptationCriterion enum."""

    def test_all_criteria_defined(self):
        """Verify all expected criteria are defined."""
        expected_criteria = [
            "complexity",
            "performance",
            "quality",
            "user_feedback",
            "resource_availability",
        ]
        actual_values = [c.value for c in AdaptationCriterion]
        for expected in expected_criteria:
            assert expected in actual_values


class TestAdaptationTrigger:
    """Test AdaptationTrigger enum."""

    def test_all_triggers_defined(self):
        """Verify all expected triggers are defined."""
        expected_triggers = [
            "threshold_exceeded",
            "quality_degraded",
            "performance_slow",
            "user_dissatisfied",
            "resource_constrained",
        ]
        actual_values = [t.value for t in AdaptationTrigger]
        for expected in expected_triggers:
            assert expected in actual_values


class TestAdaptationAction:
    """Test AdaptationAction enum."""

    def test_all_actions_defined(self):
        """Verify all expected actions are defined."""
        expected_actions = [
            "switch_technique",
            "add_technique",
            "remove_technique",
            "adjust_parameters",
            "terminate_early",
        ]
        actual_values = [a.value for a in AdaptationAction]
        for expected in expected_actions:
            assert expected in actual_values


class TestOrchestratorState:
    """Test OrchestratorState dataclass."""

    def test_create_state(self):
        """Create orchestrator state."""
        state = OrchestratorState(
            state_id="state_1",
            current_technique="chain_of_thought",
            active_techniques=["chain_of_thought"],
            performance_metrics={"response_time": 2.0, "quality": 0.8},
            resource_usage={"memory": 256, "cpu": 0.3},
            iteration_count=1,
        )
        assert state.current_technique == "chain_of_thought"
        assert state.iteration_count == 1

    def test_state_with_defaults(self):
        """Create state with default values."""
        state = OrchestratorState(
            state_id="state_2",
            current_technique="zero_shot",
        )
        assert state.active_techniques == []
        assert state.iteration_count == 0

    def test_state_multiple_techniques(self):
        """Create state with multiple active techniques."""
        state = OrchestratorState(
            state_id="state_3",
            current_technique="self_refine",
            active_techniques=["chain_of_thought", "self_refine", "chain_of_verification"],
            performance_metrics={"response_time": 5.0, "quality": 0.9},
            resource_usage={"memory": 512, "cpu": 0.6},
            iteration_count=3,
        )
        assert len(state.active_techniques) == 3


class TestAdaptationResult:
    """Test AdaptationResult dataclass."""

    def test_create_result_success(self):
        """Create successful adaptation result."""
        result = AdaptationResult(
            original_state="chain_of_thought",
            trigger=AdaptationTrigger.QUALITY_DEGRADED,
            action_taken=AdaptationAction.SWITCH_TECHNIQUE,
            new_state="self_refine",
            success=True,
            improvement_delta=0.15,
            reasoning="Quality dropped below threshold, switched to refinement technique",
        )
        assert result.success is True
        assert result.action_taken == AdaptationAction.SWITCH_TECHNIQUE
        assert result.improvement_delta == 0.15

    def test_create_result_failure(self):
        """Create failed adaptation result."""
        result = AdaptationResult(
            original_state="technique_a",
            trigger=AdaptationTrigger.PERFORMANCE_SLOW,
            action_taken=AdaptationAction.SWITCH_TECHNIQUE,
            new_state="technique_b",
            success=False,
            improvement_delta=0.0,
            error_message="Technique B not available",
        )
        assert result.success is False
        assert result.error_message == "Technique B not available"

    def test_result_add_technique(self):
        """Result for adding a technique."""
        result = AdaptationResult(
            original_state="chain_of_thought",
            trigger=AdaptationTrigger.THRESHOLD_EXCEEDED,
            action_taken=AdaptationAction.ADD_TECHNIQUE,
            new_state="chain_of_thought + verification",
            success=True,
            improvement_delta=0.2,
            reasoning="Added verification for higher quality requirement",
        )
        assert result.action_taken == AdaptationAction.ADD_TECHNIQUE


class TestAdaptationCriteria:
    """Test different adaptation criteria."""

    def test_complexity_criterion(self):
        """Complexity adaptation criterion."""
        assert AdaptationCriterion.COMPLEXITY.value == "complexity"

    def test_performance_criterion(self):
        """Performance adaptation criterion."""
        assert AdaptationCriterion.PERFORMANCE.value == "performance"

    def test_quality_criterion(self):
        """Quality adaptation criterion."""
        assert AdaptationCriterion.QUALITY.value == "quality"

    def test_user_feedback_criterion(self):
        """User feedback adaptation criterion."""
        assert AdaptationCriterion.USER_FEEDBACK.value == "user_feedback"

    def test_resource_availability_criterion(self):
        """Resource availability adaptation criterion."""
        assert AdaptationCriterion.RESOURCE_AVAILABILITY.value == "resource_availability"


class TestAdaptationTriggers:
    """Test different adaptation triggers."""

    def test_threshold_exceeded_trigger(self):
        """Threshold exceeded trigger."""
        assert AdaptationTrigger.THRESHOLD_EXCEEDED.value == "threshold_exceeded"

    def test_quality_degraded_trigger(self):
        """Quality degraded trigger."""
        assert AdaptationTrigger.QUALITY_DEGRADED.value == "quality_degraded"

    def test_performance_slow_trigger(self):
        """Performance slow trigger."""
        assert AdaptationTrigger.PERFORMANCE_SLOW.value == "performance_slow"

    def test_user_dissatisfied_trigger(self):
        """User dissatisfied trigger."""
        assert AdaptationTrigger.USER_DISSATISFIED.value == "user_dissatisfied"

    def test_resource_constrained_trigger(self):
        """Resource constrained trigger."""
        assert AdaptationTrigger.RESOURCE_CONSTRAINED.value == "resource_constrained"


class TestAdaptationActions:
    """Test different adaptation actions."""

    def test_switch_technique_action(self):
        """Switch technique action."""
        assert AdaptationAction.SWITCH_TECHNIQUE.value == "switch_technique"

    def test_add_technique_action(self):
        """Add technique action."""
        assert AdaptationAction.ADD_TECHNIQUE.value == "add_technique"

    def test_remove_technique_action(self):
        """Remove technique action."""
        assert AdaptationAction.REMOVE_TECHNIQUE.value == "remove_technique"

    def test_adjust_parameters_action(self):
        """Adjust parameters action."""
        assert AdaptationAction.ADJUST_PARAMETERS.value == "adjust_parameters"

    def test_terminate_early_action(self):
        """Terminate early action."""
        assert AdaptationAction.TERMINATE_EARLY.value == "terminate_early"


class TestEdgeCases:
    """Test edge cases for adaptive orchestration."""

    def test_empty_state(self):
        """Handle empty orchestrator state."""
        state = OrchestratorState(
            state_id="empty",
            current_technique="",
        )
        assert state.current_technique == ""
        assert state.active_techniques == []

    def test_no_improvement(self):
        """Handle adaptation with no improvement."""
        result = AdaptationResult(
            original_state="technique_a",
            trigger=AdaptationTrigger.QUALITY_DEGRADED,
            action_taken=AdaptationAction.SWITCH_TECHNIQUE,
            new_state="technique_b",
            success=True,
            improvement_delta=0.0,
            reasoning="No improvement but no regression",
        )
        assert result.improvement_delta == 0.0

    def test_negative_improvement(self):
        """Handle adaptation with negative improvement (regression)."""
        result = AdaptationResult(
            original_state="technique_a",
            trigger=AdaptationTrigger.PERFORMANCE_SLOW,
            action_taken=AdaptationAction.SWITCH_TECHNIQUE,
            new_state="technique_b",
            success=True,
            improvement_delta=-0.1,
            reasoning="New technique performed worse",
        )
        assert result.improvement_delta < 0

    def test_terminate_early_action(self):
        """Handle early termination."""
        result = AdaptationResult(
            original_state="complex_pipeline",
            trigger=AdaptationTrigger.RESOURCE_CONSTRAINED,
            action_taken=AdaptationAction.TERMINATE_EARLY,
            new_state="terminated",
            success=True,
            improvement_delta=0.0,
            reasoning="Insufficient resources, terminated early",
        )
        assert result.action_taken == AdaptationAction.TERMINATE_EARLY

    def test_max_iterations(self):
        """Handle state at max iterations."""
        state = OrchestratorState(
            state_id="maxed",
            current_technique="self_refine",
            active_techniques=["self_refine"],
            performance_metrics={},
            resource_usage={},
            iteration_count=10,
            max_iterations=10,
        )
        assert state.iteration_count == state.max_iterations


class TestComplexAdaptations:
    """Test complex adaptation scenarios."""

    def test_cascade_adaptations(self):
        """Multiple adaptations in sequence."""
        result1 = AdaptationResult(
            original_state="technique_a",
            trigger=AdaptationTrigger.QUALITY_DEGRADED,
            action_taken=AdaptationAction.SWITCH_TECHNIQUE,
            new_state="technique_b",
            success=True,
            improvement_delta=0.1,
        )

        result2 = AdaptationResult(
            original_state="technique_b",
            trigger=AdaptationTrigger.PERFORMANCE_SLOW,
            action_taken=AdaptationAction.ADD_TECHNIQUE,
            new_state="technique_b + cache",
            success=True,
            improvement_delta=0.2,
        )
        assert result1.new_state == "technique_b"
        assert result2.action_taken == AdaptationAction.ADD_TECHNIQUE

    def test_multi_technique_adaptation(self):
        """Adaptation involving multiple techniques."""
        state = OrchestratorState(
            state_id="multi",
            current_technique="orchestrated",
            active_techniques=["chain_of_thought", "self_refine", "verification"],
            performance_metrics={"quality": 0.95, "time": 8.0},
            resource_usage={"memory": 768, "cpu": 0.8},
            iteration_count=5,
        )
        assert len(state.active_techniques) == 3
        assert state.performance_metrics["quality"] > 0.9

    def test_parameter_adjustment(self):
        """Adaptation by adjusting parameters."""
        result = AdaptationResult(
            original_state="technique_a with default params",
            trigger=AdaptationTrigger.THRESHOLD_EXCEEDED,
            action_taken=AdaptationAction.ADJUST_PARAMETERS,
            new_state="technique_a with optimized params",
            success=True,
            improvement_delta=0.12,
            reasoning="Adjusted temperature and top_p for better quality",
        )
        assert result.action_taken == AdaptationAction.ADJUST_PARAMETERS
