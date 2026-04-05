"""
Analytics service for TUI session tracking and performance monitoring.
"""

from datetime import datetime
from typing import Any

from textual.widgets import Pretty


class AnalyticsService:
    """Handles analytics display and performance tracking for TUI sessions."""

    def __init__(self, session_overview: Any, performance_tracker: Any, log_store: Any):
        self.session_overview = session_overview
        self.performance_tracker = performance_tracker
        self.log_store = log_store
        self.start_time = datetime.now()

    def update_analytics_display(self):
        """Update the analytics display with current metrics."""
        try:
            # Assuming the analytics display is accessible via app.query_one
            analytics_display = self.session_overview.app.query_one(
                "#analytics-display", Pretty
            )

            perf_analysis = self.performance_tracker.get_trend_analysis()
            error_summary = self.log_store.get_error_summary()

            analytics_data = {
                "📊 Session Analytics": {
                    "uptime": str(datetime.now() - self.start_time).split(".")[0],
                    "channels_processed": self.session_overview.stats["processed"],
                    "total_downloads": self.session_overview.stats["new_videos"]
                    + self.session_overview.stats["upgrades"],
                    "success_rate": f"{((self.session_overview.stats['new_videos'] + self.session_overview.stats['upgrades'] - self.session_overview.stats['failed']) / max(1, self.session_overview.stats['new_videos'] + self.session_overview.stats['upgrades']) * 100):.1f}%",
                },
                "⚡ Performance Metrics": {
                    "trend": perf_analysis.get("trend", "stable"),
                    "stability": f"{perf_analysis.get('stability', 0):.1f}%",
                    "peak_speed": f"{self.performance_tracker.session_stats['peak_speed']:.1f} MB/s",
                    "avg_speed": f"{self.performance_tracker.session_stats['avg_speed']:.1f} MB/s",
                },
                "🚨 Error Summary": {
                    "recent_errors": error_summary["total_recent"],
                    "last_error": (
                        error_summary["last_error"]["message"]
                        if error_summary["last_error"]
                        else "None"
                    ),
                },
            }

            analytics_display.update(analytics_data)

        except Exception:
            pass

    def get_session_summary(self) -> dict[str, Any]:
        """Get a summary of the current session."""
        return {
            "start_time": self.start_time,
            "uptime": str(datetime.now() - self.start_time),
            "channels_processed": self.session_overview.stats["processed"],
            "downloads": {
                "new_videos": self.session_overview.stats["new_videos"],
                "upgrades": self.session_overview.stats["upgrades"],
                "failed": self.session_overview.stats["failed"],
            },
            "performance": {
                "peak_speed": self.performance_tracker.session_stats["peak_speed"],
                "avg_speed": self.performance_tracker.session_stats["avg_speed"],
                "trend_analysis": self.performance_tracker.get_trend_analysis(),
            },
        }
