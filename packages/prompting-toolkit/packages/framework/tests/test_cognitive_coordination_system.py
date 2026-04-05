#!/usr/bin/env python3
"""
Unit tests for cognitive_coordination_system module.

Tests for cognitive coordination system functionality.
"""


from prompting_framework.cognitive_coordination_system import (
    CognitiveMode,
    CognitiveState,
    CoordinationEvent,
    CoordinationHistory,
    CoordinationMechanism,
)


class TestCognitiveMode:
    """Test CognitiveMode enum."""

    def test_all_modes_defined(self):
        """Verify all expected modes are defined."""
        expected_modes = [
            "focused",
            "exploratory",
            "analytical",
            "creative",
            "critical",
            "synthetic",
        ]
        actual_values = [m.value for m in CognitiveMode]
        for expected in expected_modes:
            assert expected in actual_values


class TestCoordinationMechanism:
    """Test CoordinationMechanism enum."""

    def test_all_mechanisms_defined(self):
        """Verify all expected mechanisms are defined."""
        expected_mechanisms = [
            "attention_allocation",
            "working_memory_management",
            "context_switching",
            "load_balancing",
            "priority_scheduling",
        ]
        actual_values = [m.value for m in CoordinationMechanism]
        for expected in expected_mechanisms:
            assert expected in actual_values


class TestCognitiveState:
    """Test CognitiveState dataclass."""

    def test_create_state(self):
        """Create a cognitive state."""
        state = CognitiveState(
            state_id="state_1",
            current_mode=CognitiveMode.ANALYTICAL,
            active_tasks=["analyze_code", "check_security"],
            attention_distribution={
                "analyze_code": 0.6,
                "check_security": 0.4,
            },
            working_memory_usage=0.7,
            context_depth=3,
        )
        assert state.current_mode == CognitiveMode.ANALYTICAL
        assert state.working_memory_usage == 0.7

    def test_state_with_defaults(self):
        """Create state with default values."""
        state = CognitiveState(
            state_id="state_2",
            current_mode=CognitiveMode.FOCUSED,
        )
        assert state.active_tasks == []
        assert state.working_memory_usage == 0.0

    def test_multi_task_state(self):
        """Create state with multiple active tasks."""
        state = CognitiveState(
            state_id="multi",
            current_mode=CognitiveMode.SYNTHETIC,
            active_tasks=["task_a", "task_b", "task_c", "task_d"],
            attention_distribution={
                "task_a": 0.4,
                "task_b": 0.3,
                "task_c": 0.2,
                "task_d": 0.1,
            },
            working_memory_usage=0.85,
            context_depth=5,
        )
        assert len(state.active_tasks) == 4
        assert sum(state.attention_distribution.values()) == 1.0


class TestCoordinationEvent:
    """Test CoordinationEvent dataclass."""

    def test_create_event(self):
        """Create a coordination event."""
        event = CoordinationEvent(
            event_id="event_1",
            mechanism=CoordinationMechanism.ATTENTION_ALLOCATION,
            trigger="task_complexity_high",
            action="reallocate_attention",
            timestamp=1.5,
            outcome="attention_successfully_shifted",
        )
        assert event.mechanism == CoordinationMechanism.ATTENTION_ALLOCATION
        assert event.trigger == "task_complexity_high"

    def test_event_context_switch(self):
        """Event for context switching."""
        event = CoordinationEvent(
            event_id="switch_1",
            mechanism=CoordinationMechanism.CONTEXT_SWITCHING,
            trigger="user_interrupt",
            action="switch_context",
            from_mode=CognitiveMode.ANALYTICAL,
            to_mode=CognitiveMode.FOCUSED,
            timestamp=3.2,
        )
        assert event.mechanism == CoordinationMechanism.CONTEXT_SWITCHING
        assert event.from_mode == CognitiveMode.ANALYTICAL
        assert event.to_mode == CognitiveMode.FOCUSED


class TestCoordinationHistory:
    """Test CoordinationHistory dataclass."""

    def test_create_history(self):
        """Create coordination history."""
        events = [
            CoordinationEvent(
                event_id="e1",
                mechanism=CoordinationMechanism.ATTENTION_ALLOCATION,
                trigger="quality_drop",
                action="increase_attention",
                timestamp=1.0,
                outcome="improved",
            ),
            CoordinationEvent(
                event_id="e2",
                mechanism=CoordinationMechanism.WORKING_MEMORY_MANAGEMENT,
                trigger="memory_full",
                action="free_memory",
                timestamp=2.0,
                outcome="freed",
            ),
        ]

        history = CoordinationHistory(
            history_id="hist_1",
            events=events,
            total_events=2,
            start_time=0.0,
            end_time=3.0,
            final_state=CognitiveMode.FOCUSED,
        )
        assert len(history.events) == 2
        assert history.total_events == 2

    def test_empty_history(self):
        """Handle empty coordination history."""
        history = CoordinationHistory(
            history_id="empty",
            events=[],
            total_events=0,
            start_time=0.0,
            end_time=0.0,
            final_state=CognitiveMode.FOCUSED,
        )
        assert len(history.events) == 0


class TestCognitiveModes:
    """Test different cognitive modes."""

    def test_focused_mode(self):
        """Focused cognitive mode."""
        assert CognitiveMode.FOCUSED.value == "focused"

    def test_exploratory_mode(self):
        """Exploratory cognitive mode."""
        assert CognitiveMode.EXPLORATORY.value == "exploratory"

    def test_analytical_mode(self):
        """Analytical cognitive mode."""
        assert CognitiveMode.ANALYTICAL.value == "analytical"

    def test_creative_mode(self):
        """Creative cognitive mode."""
        assert CognitiveMode.CREATIVE.value == "creative"

    def test_critical_mode(self):
        """Critical cognitive mode."""
        assert CognitiveMode.CRITICAL.value == "critical"

    def test_synthetic_mode(self):
        """Synthetic cognitive mode."""
        assert CognitiveMode.SYNTHETIC.value == "synthetic"


class TestCoordinationMechanisms:
    """Test different coordination mechanisms."""

    def test_attention_allocation(self):
        """Attention allocation mechanism."""
        assert CoordinationMechanism.ATTENTION_ALLOCATION.value == "attention_allocation"

    def test_working_memory_management(self):
        """Working memory management mechanism."""
        assert CoordinationMechanism.WORKING_MEMORY_MANAGEMENT.value == "working_memory_management"

    def test_context_switching(self):
        """Context switching mechanism."""
        assert CoordinationMechanism.CONTEXT_SWITCHING.value == "context_switching"

    def test_load_balancing(self):
        """Load balancing mechanism."""
        assert CoordinationMechanism.LOAD_BALANCING.value == "load_balancing"

    def test_priority_scheduling(self):
        """Priority scheduling mechanism."""
        assert CoordinationMechanism.PRIORITY_SCHEDULING.value == "priority_scheduling"


class TestEdgeCases:
    """Test edge cases for cognitive coordination."""

    def test_no_active_tasks(self):
        """Handle state with no active tasks."""
        state = CognitiveState(
            state_id="idle",
            current_mode=CognitiveMode.FOCUSED,
            active_tasks=[],
            attention_distribution={},
            working_memory_usage=0.0,
        )
        assert len(state.active_tasks) == 0

    def test_full_working_memory(self):
        """Handle state at full working memory."""
        state = CognitiveState(
            state_id="full",
            current_mode=CognitiveMode.ANALYTICAL,
            active_tasks=["task_1", "task_2"],
            attention_distribution={"task_1": 0.5, "task_2": 0.5},
            working_memory_usage=1.0,
        )
        assert state.working_memory_usage == 1.0

    def test_zero_context_depth(self):
        """Handle state with minimal context."""
        state = CognitiveState(
            state_id="shallow",
            current_mode=CognitiveMode.FOCUSED,
            context_depth=0,
        )
        assert state.context_depth == 0

    def test_immediate_event(self):
        """Handle event at timestamp zero."""
        event = CoordinationEvent(
            event_id="immediate",
            mechanism=CoordinationMechanism.PRIORITY_SCHEDULING,
            trigger="startup",
            action="initialize",
            timestamp=0.0,
        )
        assert event.timestamp == 0.0


class TestComplexCoordination:
    """Test complex coordination scenarios."""

    def test_mode_transition_sequence(self):
        """Sequence of mode transitions."""
        events = [
            CoordinationEvent(
                event_id=f"trans_{i}",
                mechanism=CoordinationMechanism.CONTEXT_SWITCHING,
                trigger=f"trigger_{i}",
                action="switch_mode",
                from_mode=list(CognitiveMode)[i],
                to_mode=list(CognitiveMode)[i + 1],
                timestamp=float(i),
            )
            for i in range(len(CognitiveMode) - 1)
        ]

        history = CoordinationHistory(
            history_id="transitions",
            events=events,
            total_events=len(events),
            start_time=0.0,
            end_time=float(len(events)),
            final_state=CognitiveMode.SYNTHETIC,
        )
        assert len(events) == len(CognitiveMode) - 1

    def test_multi_task_attention_distribution(self):
        """Complex attention distribution across many tasks."""
        tasks = [f"task_{i}" for i in range(10)]
        distribution = dict.fromkeys(tasks, 0.1)

        state = CognitiveState(
            state_id="complex",
            current_mode=CognitiveMode.SYNTHETIC,
            active_tasks=tasks,
            attention_distribution=distribution,
            working_memory_usage=0.95,
            context_depth=8,
        )
        assert len(state.active_tasks) == 10
        assert sum(state.attention_distribution.values()) == 1.0

    def test_rapid_context_switches(self):
        """Handle rapid context switching events."""
        events = [
            CoordinationEvent(
                event_id=f"switch_{i}",
                mechanism=CoordinationMechanism.CONTEXT_SWITCHING,
                trigger=f"interrupt_{i}",
                action="switch",
                from_mode=CognitiveMode.FOCUSED,
                to_mode=CognitiveMode.EXPLORATORY,
                timestamp=float(i) * 0.1,
            )
            for i in range(20)
        ]

        history = CoordinationHistory(
            history_id="rapid",
            events=events,
            total_events=20,
            start_time=0.0,
            end_time=1.9,
            final_state=CognitiveMode.EXPLORATORY,
        )
        assert history.total_events == 20
        assert history.end_time < 2.0
