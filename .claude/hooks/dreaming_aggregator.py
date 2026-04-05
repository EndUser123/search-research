#!/usr/bin/env python3
"""
Event Aggregation Module for Dreaming Hook

Implements InsightsGenerator class with sliding window for aggregating
principle violation events and generating behavioral insights.

Key Features:
- Sliding time window (configurable)
- Count events per principle type
- Detect top violated principle
- Flag high-violation sessions (>10 violations)

Used by: dreaming_hook.py (Stop event)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

# Event type to principle mapping (same as principle_monitor.py)
EVENT_TO_PRINCIPLE = {
    "context_grounding_violation": "context_reuse",
    "change_without_evidence": "grounded_changes",
    "redundant_broad_question": "minimal_redundancy",
    "opaque_uncertainty": "transparent_uncertainty",
}


class InsightsGenerator:
    """
    Aggregates events within a sliding time window and generates insights.

    Args:
        window_seconds: Time window in seconds (default: 3600 = 1 hour)
    """

    def __init__(self, window_seconds: int = 3600):
        self.window_seconds = window_seconds
        self.events: list[dict[str, Any]] = []

    def add_event(self, event: dict) -> None:
        """
        Add an event and prune old events outside the time window.

        Args:
            event: Event dict with 'ts', 'event_type', 'principle', 'session_id'
        """
        self.events.append(event)
        self._prune_old_events()

    def _prune_old_events(self) -> None:
        """Remove events outside the sliding time window."""
        if not self.events:
            return

        cutoff_time = datetime.now(UTC) - self._get_window_timedelta()
        pruned_events = []

        for event in self.events:
            try:
                event_ts = datetime.fromisoformat(event["ts"])
                if event_ts >= cutoff_time:
                    pruned_events.append(event)
            except (ValueError, KeyError):
                # Keep events with invalid timestamps (fail-safe)
                pruned_events.append(event)

        self.events = pruned_events

    def _get_window_timedelta(self) -> Any:
        """Get timedelta for window (imported at runtime for compatibility)."""
        from datetime import timedelta
        return timedelta(seconds=self.window_seconds)

    def generate_insights(self) -> dict[str, Any]:
        """
        Generate insights from events in the time window.

        Returns:
            Dict with:
                - total_events: Total event count
                - principle_counts: Count per principle type
                - top_principle: Most violated principle (or None)
                - top_principle_count: Count of top principle
                - high_violation_sessions: Dict of sessions with >10 violations
        """
        # Count events by principle
        principle_counts: dict[str, int] = {}
        session_counts: dict[str, int] = {}

        for event in self.events:
            principle = event.get("principle", "unknown")
            session_id = event.get("session_id", "unknown")

            # Count per principle
            principle_counts[principle] = principle_counts.get(principle, 0) + 1

            # Count per session
            session_counts[session_id] = session_counts.get(session_id, 0) + 1

        # Find top violated principle
        top_principle = None
        top_principle_count = 0

        if principle_counts:
            top_principle = max(principle_counts.keys(), key=lambda k: principle_counts[k])
            top_principle_count = principle_counts[top_principle]

        # Detect high-violation sessions (>10 violations)
        high_violation_sessions = {
            session_id: count
            for session_id, count in session_counts.items()
            if count > 10
        }

        return {
            "total_events": len(self.events),
            "principle_counts": principle_counts,
            "top_principle": top_principle,
            "top_principle_count": top_principle_count,
            "high_violation_sessions": high_violation_sessions,
        }


if __name__ == "__main__":
    # Simple demo
    generator = InsightsGenerator(window_seconds=3600)

    # Add some sample events
    for i in range(3):
        generator.add_event({
            "ts": datetime.now(UTC).isoformat(),
            "event_type": "context_grounding_violation",
            "principle": "context_reuse",
            "session_id": "demo-session"
        })

    insights = generator.generate_insights()
    print("Insights:", insights)
