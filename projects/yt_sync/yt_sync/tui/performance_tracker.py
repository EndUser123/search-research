"""
Performance tracking utilities for the TUI.
"""

from collections import deque
from datetime import datetime
from statistics import mean, stdev
from typing import Any


class PerformanceTracker:
    """Tracks download performance metrics."""

    def __init__(self, max_history: int = 100):
        self.download_rates: deque[float] = deque(maxlen=max_history)
        self.session_stats = {
            "peak_speed": 0.0,
            "avg_speed": 0.0,
            "start_time": datetime.now(),
        }

    def add_rate(self, rate_mbps: float):
        """Add a new download rate measurement."""
        self.download_rates.append(rate_mbps)

        if rate_mbps > self.session_stats["peak_speed"]:
            self.session_stats["peak_speed"] = rate_mbps

        if self.download_rates:
            self.session_stats["avg_speed"] = mean(self.download_rates)

    def get_trend_analysis(self) -> dict[str, Any]:
        """Analyze performance trends."""
        if len(self.download_rates) < 5:
            return {"trend": "stable", "stability": 100}

        recent = list(self.download_rates)[-5:]
        recent_avg = mean(recent)

        if len(self.download_rates) >= 10:
            older = list(self.download_rates)[-10:-5]
            older_avg = mean(older)
            if recent_avg > older_avg * 1.1:
                trend = "improving"
            elif recent_avg < older_avg * 0.9:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            trend = "stable"

        stability = max(
            0,
            min(100, 100 - (stdev(recent) / mean(recent) * 100)),
        )

        return {"trend": trend, "stability": stability, "recent_avg": recent_avg}
