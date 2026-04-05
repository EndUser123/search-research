"""Tests for outcome_recorder module.

Tests for RCA outcome recording and tracking.
"""

import pytest

from rca.outcome_recorder import (
    Outcome,
    OutcomeRecorder,
    OutcomeStatus,
    get_outcome_recorder,
)


class TestOutcomeDataclass:
    """Test Outcome dataclass."""

    def test_outcome_creation(self):
        """Outcome can be created with all fields."""
        outcome = Outcome(
            session_id="rca_123",
            status=OutcomeStatus.RESOLVED,
            problem_type="error",
            root_cause="Missing null check",
            fix_applied="Added if check",
            resolution_time_seconds=300,
            hypothesis_count=5,
            evidence_count=12,
        )

        assert outcome.session_id == "rca_123"
        assert outcome.status == OutcomeStatus.RESOLVED
        assert outcome.root_cause == "Missing null check"

    def test_outcome_with_minimal_fields(self):
        """Outcome can be created with minimal fields."""
        outcome = Outcome(
            session_id="rca_456",
            status=OutcomeStatus.IN_PROGRESS,
        )

        assert outcome.session_id == "rca_456"
        assert outcome.status == OutcomeStatus.IN_PROGRESS


class TestOutcomeStatus:
    """Test OutcomeStatus enum."""

    def test_status_values(self):
        """OutcomeStatus has expected values."""
        assert OutcomeStatus.IN_PROGRESS.value == "in_progress"
        assert OutcomeStatus.RESOLVED.value == "resolved"
        assert OutcomeStatus.UNRESOLVED.value == "unresolved"
        assert OutcomeStatus.ABANDONED.value == "abandoned"


class TestOutcomeRecorderInit:
    """Test OutcomeRecorder initialization."""

    def test_recorder_creation(self):
        """OutcomeRecorder can be created."""
        recorder = OutcomeRecorder()

        assert len(recorder._outcomes) == 0

    def test_singleton_get_outcome_recorder(self):
        """get_outcome_recorder returns singleton instance."""
        recorder1 = get_outcome_recorder()
        recorder2 = get_outcome_recorder()

        assert recorder1 is recorder2


class TestStartSession:
    """Test session start tracking."""

    def test_start_session(self):
        """Session can be started."""
        recorder = OutcomeRecorder()
        recorder.start_session("rca_123", "error")

        assert "rca_123" in recorder._outcomes
        assert recorder._outcomes["rca_123"].status == OutcomeStatus.IN_PROGRESS

    def test_start_session_with_metadata(self):
        """Session can include metadata."""
        recorder = OutcomeRecorder()
        recorder.start_session(
            "rca_123",
            "error",
            error_message="AttributeError: 'NoneType' object",
            tool_used="Read",
        )

        outcome = recorder._outcomes["rca_123"]

        assert outcome.error_message == "AttributeError: 'NoneType' object"


class TestRecordOutcome:
    """Test recording RCA outcomes."""

    def test_record_resolved_outcome(self):
        """Resolved outcome can be recorded."""
        recorder = OutcomeRecorder()
        recorder.start_session("rca_123", "error")

        recorder.record_outcome(
            session_id="rca_123",
            status=OutcomeStatus.RESOLVED,
            root_cause="Missing null check",
            fix_applied="Added if check",
        )

        outcome = recorder.get_outcome("rca_123")

        assert outcome.status == OutcomeStatus.RESOLVED
        assert outcome.root_cause == "Missing null check"
        assert outcome.fix_applied == "Added if check"

    def test_record_unresolved_outcome(self):
        """Unresolved outcome can be recorded."""
        recorder = OutcomeRecorder()
        recorder.start_session("rca_123", "error")

        recorder.record_outcome(
            session_id="rca_123",
            status=OutcomeStatus.UNRESOLVED,
            notes="Unable to reproduce",
        )

        outcome = recorder.get_outcome("rca_123")

        assert outcome.status == OutcomeStatus.UNRESOLVED
        assert outcome.notes == "Unable to reproduce"

    def test_record_abandoned_outcome(self):
        """Abandoned outcome can be recorded."""
        recorder = OutcomeRecorder()
        recorder.start_session("rca_123", "error")

        recorder.record_outcome(
            session_id="rca_123",
            status=OutcomeStatus.ABANDONED,
            notes="User cancelled session",
        )

        outcome = recorder.get_outcome("rca_123")

        assert outcome.status == OutcomeStatus.ABANDONED


class TestUpdateMetrics:
    """Test metrics updating."""

    def test_update_hypothesis_count(self):
        """Hypothesis count can be updated."""
        recorder = OutcomeRecorder()
        recorder.start_session("rca_123", "error")

        recorder.update_metrics("rca_123", hypothesis_count=5)

        outcome = recorder.get_outcome("rca_123")

        assert outcome.hypothesis_count == 5

    def test_update_evidence_count(self):
        """Evidence count can be updated."""
        recorder = OutcomeRecorder()
        recorder.start_session("rca_123", "error")

        recorder.update_metrics("rca_123", evidence_count=12)

        outcome = recorder.get_outcome("rca_123")

        assert outcome.evidence_count == 12

    def test_update_multiple_metrics(self):
        """Multiple metrics can be updated at once."""
        recorder = OutcomeRecorder()
        recorder.start_session("rca_123", "error")

        recorder.update_metrics(
            "rca_123",
            hypothesis_count=3,
            evidence_count=8,
            tools_used=["Read", "Grep", "Edit"],
        )

        outcome = recorder.get_outcome("rca_123")

        assert outcome.hypothesis_count == 3
        assert outcome.evidence_count == 8
        assert len(outcome.tools_used) == 3


class TestGetOutcome:
    """Test retrieving outcomes."""

    def test_get_existing_outcome(self):
        """Existing outcome can be retrieved."""
        recorder = OutcomeRecorder()
        recorder.start_session("rca_123", "error")

        outcome = recorder.get_outcome("rca_123")

        assert outcome is not None
        assert outcome.session_id == "rca_123"

    def test_get_nonexistent_outcome(self):
        """Nonexistent outcome returns None."""
        recorder = OutcomeRecorder()

        outcome = recorder.get_outcome("nonexistent")

        assert outcome is None


class TestListOutcomes:
    """Test listing outcomes."""

    def test_list_all_outcomes(self):
        """All outcomes can be listed."""
        recorder = OutcomeRecorder()
        recorder.start_session("rca_1", "error")
        recorder.start_session("rca_2", "test")

        outcomes = recorder.list_outcomes()

        assert len(outcomes) == 2

    def test_list_by_status(self):
        """Outcomes can be filtered by status."""
        recorder = OutcomeRecorder()
        recorder.start_session("rca_1", "error")
        recorder.record_outcome("rca_1", OutcomeStatus.RESOLVED)
        recorder.start_session("rca_2", "error")

        resolved = recorder.list_outcomes(status=OutcomeStatus.RESOLVED)

        assert len(resolved) == 1
        assert resolved[0].session_id == "rca_1"

    def test_list_by_problem_type(self):
        """Outcomes can be filtered by problem type."""
        recorder = OutcomeRecorder()
        recorder.start_session("rca_1", "error")
        recorder.start_session("rca_2", "test")

        errors = recorder.list_outcomes(problem_type="error")

        assert len(errors) == 1
        assert errors[0].session_id == "rca_1"


class TestResolutionTime:
    """Test resolution time tracking."""

    def test_auto_calculate_resolution_time(self):
        """Resolution time is calculated automatically."""
        import time

        recorder = OutcomeRecorder()
        recorder.start_session("rca_123", "error")

        time.sleep(0.1)  # Small delay

        recorder.record_outcome("rca_123", OutcomeStatus.RESOLVED, root_cause="Test")

        outcome = recorder.get_outcome("rca_123")

        assert outcome.resolution_time_seconds is not None
        assert outcome.resolution_time_seconds >= 0.1


class TestEdgeCases:
    """Test edge cases."""

    def test_record_without_start(self):
        """Recording without start creates session."""
        recorder = OutcomeRecorder()

        recorder.record_outcome(
            "rca_123",
            OutcomeStatus.RESOLVED,
            root_cause="Test",
        )

        outcome = recorder.get_outcome("rca_123")

        assert outcome is not None

    def test_update_nonexistent_session(self):
        """Updating nonexistent session is handled gracefully."""
        recorder = OutcomeRecorder()

        # Should not crash
        recorder.update_metrics("nonexistent", hypothesis_count=5)

    def test_multiple_sessions_independent(self):
        """Multiple sessions are tracked independently."""
        recorder = OutcomeRecorder()
        recorder.start_session("rca_1", "error")
        recorder.start_session("rca_2", "test")

        recorder.update_metrics("rca_1", hypothesis_count=3)
        recorder.update_metrics("rca_2", hypothesis_count=5)

        outcome1 = recorder.get_outcome("rca_1")
        outcome2 = recorder.get_outcome("rca_2")

        assert outcome1.hypothesis_count == 3
        assert outcome2.hypothesis_count == 5
