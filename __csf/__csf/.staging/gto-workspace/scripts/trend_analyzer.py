"""Session Trend Analysis for /gto skill.

Compares current session to historical patterns.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyze session trends compared to history."""

    def __init__(self) -> None:
        """Initialize trend analyzer."""
        logger.info("TrendAnalyzer initialized")

    def compare_to_baseline(
        self,
        current_metrics: dict[str, Any],
        baseline: dict[str, Any]
    ) -> dict[str, Any]:
        """Compare current session metrics to baseline.

        Args:
            current_metrics: Current session metrics
            baseline: Historical baseline metrics

        Returns:
            Trend analysis with deltas
        """
        deltas = {}
        for key in ["todo_count", "unfinished_count", "conversation_length"]:
            current_val = current_metrics.get(key, 0)
            baseline_val = baseline.get(key, 0)
            delta = current_val - baseline_val
            pct_change = (delta / baseline_val * 100) if baseline_val > 0 else 0
            deltas[key] = {
                "current": current_val,
                "baseline": baseline_val,
                "delta": delta,
                "pct_change": pct_change,
                "trend": "increasing" if delta > 0 else "decreasing" if delta < 0 else "stable"
            }
        
        return {"deltas": deltas, "analysis_complete": True}

    def detect_pattern_emergence(
        self,
        current_gaps: list[str],
        historical_patterns: list[str]
    ) -> dict[str, Any]:
        """Detect if current gaps match historical patterns.

        Args:
            current_gaps: Gap descriptions from current session
            historical_patterns: Known gap patterns from history

        Returns:
            Pattern matching results
        """
        matches = []
        for gap in current_gaps:
            gap_lower = gap.lower()
            for pattern in historical_patterns:
                if pattern.lower() in gap_lower or gap_lower in pattern.lower():
                    matches.append({"current": gap, "historical": pattern})
        
        return {
            "recurring_patterns": matches,
            "recurrence_rate": len(matches) / len(current_gaps) if current_gaps else 0
        }
