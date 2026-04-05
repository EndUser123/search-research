"""Tests for phase_state_manager module.

Tests for RCA phase state management and transitions.
"""

import pytest

from rca.phase_state_manager import (
    Phase,
    PhaseState,
    PhaseStateManager,
)


class TestPhaseEnum:
    """Test Phase enum."""

    def test_phase_values(self):
        """Phase has expected values."""
        assert Phase.PREPARATION.value == "preparation"
        assert Phase.DATA_COLLECTION.value == "data_collection"
        assert Phase.HYPOTHESIS_GENERATION.value == "hypothesis_generation"
        assert Phase.VERIFICATION.value == "verification"
        assert Phase.RESOLUTION.value == "resolution"


class TestPhaseStateDataclass:
    """Test PhaseState dataclass."""

    def test_phase_state_creation(self):
        """PhaseState can be created."""
        state = PhaseState(
            phase=Phase.DATA_COLLECTION,
            start_time="2026-02-28T12:00:00",
            evidence_count=5,
            hypothesis_count=2,
        )

        assert state.phase == Phase.DATA_COLLECTION
        assert state.evidence_count == 5

    def test_phase_state_default_values(self):
        """PhaseState has sensible defaults."""
        state = PhaseState(phase=Phase.PREPARATION)

        assert state.phase == Phase.PREPARATION
        assert state.evidence_count == 0
        assert state.hypothesis_count == 0


class TestPhaseStateManagerInit:
    """Test PhaseStateManager initialization."""

    def test_manager_creation(self):
        """Manager can be created."""
        manager = PhaseStateManager("rca_123")

        assert manager.session_id == "rca_123"
        assert len(manager._history) == 0

    def test_initial_phase(self):
        """Initial phase is PREPARATION."""
        manager = PhaseStateManager("rca_123")

        assert manager.current_phase == Phase.PREPARATION


class TestPhaseTransitions:
    """Test phase transition logic."""

    def test_transition_to_next_phase(self):
        """Can transition to next phase."""
        manager = PhaseStateManager("rca_123")

        manager.transition_to(Phase.DATA_COLLECTION)

        assert manager.current_phase == Phase.DATA_COLLECTION

    def test_transition_records_history(self):
        """Transitions are recorded in history."""
        manager = PhaseStateManager("rca_123")

        manager.transition_to(Phase.DATA_COLLECTION)
        manager.transition_to(Phase.HYPOTHESIS_GENERATION)

        assert len(manager._history) == 2
        assert manager._history[0].phase == Phase.DATA_COLLECTION

    def test_valid_transition_sequence(self):
        """Standard phase sequence is valid."""
        manager = PhaseStateManager("rca_123")

        manager.transition_to(Phase.DATA_COLLECTION)
        manager.transition_to(Phase.HYPOTHESIS_GENERATION)
        manager.transition_to(Phase.VERIFICATION)
        manager.transition_to(Phase.RESOLUTION)

        assert manager.current_phase == Phase.RESOLUTION


class TestGetCurrentState:
    """Test getting current state."""

    def test_get_current_state(self):
        """Current state can be retrieved."""
        manager = PhaseStateManager("rca_123")
        manager.transition_to(Phase.DATA_COLLECTION)

        state = manager.get_current_state()

        assert state.phase == Phase.DATA_COLLECTION
        assert state.session_id == "rca_123"

    def test_current_state_has_timestamp(self):
        """Current state has timestamp."""
        manager = PhaseStateManager("rca_123")

        state = manager.get_current_state()

        assert state.start_time is not None


class TestUpdateMetrics:
    """Test updating phase metrics."""

    def test_update_evidence_count(self):
        """Evidence count can be updated."""
        manager = PhaseStateManager("rca_123")

        manager.update_metrics(evidence_count=5)

        state = manager.get_current_state()
        assert state.evidence_count == 5

    def test_update_hypothesis_count(self):
        """Hypothesis count can be updated."""
        manager = PhaseStateManager("rca_123")

        manager.update_metrics(hypothesis_count=3)

        state = manager.get_current_state()
        assert state.hypothesis_count == 3

    def test_update_multiple_metrics(self):
        """Multiple metrics can be updated."""
        manager = PhaseStateManager("rca_123")

        manager.update_metrics(evidence_count=10, hypothesis_count=4)

        state = manager.get_current_state()
        assert state.evidence_count == 10
        assert state.hypothesis_count == 4


class TestGetHistory:
    """Test retrieving phase history."""

    def test_get_full_history(self):
        """Full phase history can be retrieved."""
        manager = PhaseStateManager("rca_123")

        manager.transition_to(Phase.DATA_COLLECTION)
        manager.transition_to(Phase.HYPOTHESIS_GENERATION)
        manager.transition_to(Phase.VERIFICATION)

        history = manager.get_history()

        assert len(history) == 3

    def test_history_preserves_order(self):
        """History preserves chronological order."""
        manager = PhaseStateManager("rca_123")

        manager.transition_to(Phase.DATA_COLLECTION)
        manager.transition_to(Phase.HYPOTHESIS_GENERATION)

        history = manager.get_history()

        assert history[0].phase == Phase.DATA_COLLECTION
        assert history[1].phase == Phase.HYPOTHESIS_GENERATION

    def test_history_isolated_by_session(self):
        """Different sessions have independent histories."""
        manager1 = PhaseStateManager("rca_1")
        manager2 = PhaseStateManager("rca_2")

        manager1.transition_to(Phase.DATA_COLLECTION)
        manager2.transition_to(Phase.HYPOTHESIS_GENERATION)

        assert len(manager1.get_history()) == 1
        assert len(manager2.get_history()) == 1


class TestPhaseDuration:
    """Test phase duration tracking."""

    def test_phase_duration_calculation(self):
        """Phase duration can be calculated."""
        import time

        manager = PhaseStateManager("rca_123")

        manager.transition_to(Phase.DATA_COLLECTION)
        time.sleep(0.1)

        duration = manager.get_phase_duration(Phase.DATA_COLLECTION)

        assert duration is not None
        assert duration >= 0.1


class TestEdgeCases:
    """Test edge cases."""

    def test_transition_to_same_phase(self):
        """Transitioning to same phase is handled."""
        manager = PhaseStateManager("rca_123")
        manager.transition_to(Phase.DATA_COLLECTION)

        # Should not create duplicate history entry
        manager.transition_to(Phase.DATA_COLLECTION)

        assert manager.current_phase == Phase.DATA_COLLECTION

    def test_get_state_for_nonexistent_session(self):
        """Getting state for session without history works."""
        manager = PhaseStateManager("rca_123")

        state = manager.get_current_state()

        assert state is not None
        assert state.phase == Phase.PREPARATION
