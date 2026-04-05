#!/usr/bin/env python3
"""
Tests for dreaming_aggregator.py (InsightsGenerator)

TDD Test Suite: RED Phase
Tests verify event aggregation, sliding window, and insight generation.
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dreaming_aggregator import InsightsGenerator


class TestInsightsGeneratorSlidingWindow:
    """Tests for sliding time window functionality."""

    def test_add_event_stores_event(self):
        """
        Test that add_event stores events in memory.

        Given: InsightsGenerator instance
        When: Event is added
        Then: Event is stored in events list
        """
        # Arrange
        generator = InsightsGenerator(window_seconds=3600)
        event = {
            "ts": datetime.now(UTC).isoformat(),
            "event_type": "context_grounding_violation",
            "principle": "context_reuse",
            "session_id": "test-session-1"
        }

        # Act
        generator.add_event(event)

        # Assert
        assert len(generator.events) == 1
        assert generator.events[0] == event

    def test_sliding_window_removes_old_events(self):
        """
        Test that old events outside time window are pruned.

        Given: InsightsGenerator with 1-second window
        When: Old event (2 seconds ago) and new event added
        Then: Only new event remains
        """
        # Arrange
        generator = InsightsGenerator(window_seconds=1)
        old_time = datetime.now(UTC) - timedelta(seconds=2)
        new_time = datetime.now(UTC)

        old_event = {
            "ts": old_time.isoformat(),
            "event_type": "context_grounding_violation",
            "principle": "context_reuse",
            "session_id": "test-session-1"
        }
        new_event = {
            "ts": new_time.isoformat(),
            "event_type": "change_without_evidence",
            "principle": "grounded_changes",
            "session_id": "test-session-2"
        }

        # Act
        generator.add_event(old_event)
        generator.add_event(new_event)

        # Assert
        assert len(generator.events) == 1
        assert generator.events[0]["event_type"] == "change_without_evidence"

    def test_sliding_window_keeps_recent_events(self):
        """
        Test that events within time window are kept.

        Given: InsightsGenerator with 60-second window
        When: Multiple events added within window
        Then: All events retained
        """
        # Arrange
        generator = InsightsGenerator(window_seconds=60)
        base_time = datetime.now(UTC)

        events = []
        for i in range(5):
            event_time = base_time - timedelta(seconds=i * 10)
            events.append({
                "ts": event_time.isoformat(),
                "event_type": "context_grounding_violation",
                "principle": "context_reuse",
                "session_id": f"test-session-{i}"
            })

        # Act
        for event in events:
            generator.add_event(event)

        # Assert
        assert len(generator.events) == 5


class TestInsightsGeneratorPrincipleCounts:
    """Tests for principle violation counting."""

    def test_counts_events_by_principle(self):
        """
        Test that generate_insights counts events per principle.

        Given: Multiple events with different principles
        When: generate_insights is called
        Then: Correct counts per principle returned
        """
        # Arrange
        generator = InsightsGenerator(window_seconds=3600)
        events = [
            {"ts": datetime.now(UTC).isoformat(), "event_type": "context_grounding_violation", "principle": "context_reuse", "session_id": "s1"},
            {"ts": datetime.now(UTC).isoformat(), "event_type": "change_without_evidence", "principle": "grounded_changes", "session_id": "s2"},
            {"ts": datetime.now(UTC).isoformat(), "event_type": "context_grounding_violation", "principle": "context_reuse", "session_id": "s3"},
            {"ts": datetime.now(UTC).isoformat(), "event_type": "redundant_broad_question", "principle": "minimal_redundancy", "session_id": "s4"},
            {"ts": datetime.now(UTC).isoformat(), "event_type": "opaque_uncertainty", "principle": "transparent_uncertainty", "session_id": "s5"},
        ]

        for event in events:
            generator.add_event(event)

        # Act
        insights = generator.generate_insights()

        # Assert
        assert insights["principle_counts"]["context_reuse"] == 2
        assert insights["principle_counts"]["grounded_changes"] == 1
        assert insights["principle_counts"]["minimal_redundancy"] == 1
        assert insights["principle_counts"]["transparent_uncertainty"] == 1

    def test_handles_empty_events(self):
        """
        Test that generate_insights handles no events.

        Given: InsightsGenerator with no events
        When: generate_insights is called
        Then: Returns zero counts and None for top principle
        """
        # Arrange
        generator = InsightsGenerator(window_seconds=3600)

        # Act
        insights = generator.generate_insights()

        # Assert
        assert insights["total_events"] == 0
        assert insights["top_principle"] is None
        assert insights["top_principle_count"] == 0


class TestInsightsGeneratorTopPrinciple:
    """Tests for top violated principle detection."""

    def test_detects_top_violated_principle(self):
        """
        Test that generate_insights identifies most violated principle.

        Given: Events with 3 context_reuse, 2 grounded_changes, 1 minimal_redundancy
        When: generate_insights is called
        Then: top_principle = "context_reuse", top_principle_count = 3
        """
        # Arrange
        generator = InsightsGenerator(window_seconds=3600)
        events = [
            {"ts": datetime.now(UTC).isoformat(), "event_type": "context_grounding_violation", "principle": "context_reuse", "session_id": "s1"},
            {"ts": datetime.now(UTC).isoformat(), "event_type": "context_grounding_violation", "principle": "context_reuse", "session_id": "s2"},
            {"ts": datetime.now(UTC).isoformat(), "event_type": "context_grounding_violation", "principle": "context_reuse", "session_id": "s3"},
            {"ts": datetime.now(UTC).isoformat(), "event_type": "change_without_evidence", "principle": "grounded_changes", "session_id": "s4"},
            {"ts": datetime.now(UTC).isoformat(), "event_type": "change_without_evidence", "principle": "grounded_changes", "session_id": "s5"},
            {"ts": datetime.now(UTC).isoformat(), "event_type": "redundant_broad_question", "principle": "minimal_redundancy", "session_id": "s6"},
        ]

        for event in events:
            generator.add_event(event)

        # Act
        insights = generator.generate_insights()

        # Assert
        assert insights["top_principle"] == "context_reuse"
        assert insights["top_principle_count"] == 3


class TestInsightsGeneratorHighViolationSessions:
    """Tests for high-violation session detection (>10 violations)."""

    def test_detects_high_violation_sessions(self):
        """
        Test that sessions with >10 violations are flagged.

        Given: Session with 11 violations, session with 5 violations
        When: generate_insights is called
        Then: high_violation_sessions contains only the 11-violation session
        """
        # Arrange
        generator = InsightsGenerator(window_seconds=3600)

        # Session with 11 violations
        for i in range(11):
            generator.add_event({
                "ts": datetime.now(UTC).isoformat(),
                "event_type": "context_grounding_violation",
                "principle": "context_reuse",
                "session_id": "high-violation-session"
            })

        # Session with 5 violations
        for i in range(5):
            generator.add_event({
                "ts": datetime.now(UTC).isoformat(),
                "event_type": "change_without_evidence",
                "principle": "grounded_changes",
                "session_id": "low-violation-session"
            })

        # Act
        insights = generator.generate_insights()

        # Assert
        assert "high-violation-session" in insights["high_violation_sessions"]
        assert "low-violation-session" not in insights["high_violation_sessions"]
        assert insights["high_violation_sessions"]["high-violation-session"] == 11

    def test_excludes_ten_violations_from_high(self):
        """
        Test that exactly 10 violations is not flagged as high.

        Given: Session with exactly 10 violations
        When: generate_insights is called
        Then: Session not in high_violation_sessions (threshold is >10)
        """
        # Arrange
        generator = InsightsGenerator(window_seconds=3600)

        for i in range(10):
            generator.add_event({
                "ts": datetime.now(UTC).isoformat(),
                "event_type": "context_grounding_violation",
                "principle": "context_reuse",
                "session_id": "exactly-ten-session"
            })

        # Act
        insights = generator.generate_insights()

        # Assert
        assert "exactly-ten-session" not in insights["high_violation_sessions"]


class TestInsightsGeneratorCompleteOutput:
    """Tests for complete insights output structure."""

    def test_generate_insights_returns_complete_dict(self):
        """
        Test that generate_insights returns all required fields.

        Given: InsightsGenerator with mixed events
        When: generate_insights is called
        Then: Returns dict with all expected keys
        """
        # Arrange
        generator = InsightsGenerator(window_seconds=3600)
        events = [
            {"ts": datetime.now(UTC).isoformat(), "event_type": "context_grounding_violation", "principle": "context_reuse", "session_id": "s1"},
            {"ts": datetime.now(UTC).isoformat(), "event_type": "change_without_evidence", "principle": "grounded_changes", "session_id": "s2"},
        ]

        for event in events:
            generator.add_event(event)

        # Act
        insights = generator.generate_insights()

        # Assert - verify all required keys present
        assert "total_events" in insights
        assert "principle_counts" in insights
        assert "top_principle" in insights
        assert "top_principle_count" in insights
        assert "high_violation_sessions" in insights

        # Verify types
        assert isinstance(insights["total_events"], int)
        assert isinstance(insights["principle_counts"], dict)
        assert isinstance(insights["high_violation_sessions"], dict)

        # Verify values
        assert insights["total_events"] == 2
        assert insights["top_principle"] in ["context_reuse", "grounded_changes"]
        assert insights["top_principle_count"] == 1
