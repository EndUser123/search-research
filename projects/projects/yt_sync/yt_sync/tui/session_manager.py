"""
Session management for TUI applications.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class SessionManager:
    """Manages TUI session state and data export."""

    def __init__(
        self, session_overview: Any, performance_tracker: Any, start_time: datetime
    ):
        self.session_overview = session_overview
        self.performance_tracker = performance_tracker
        self.start_time = start_time

    def export_session_data(self):
        """Export session data to JSON file."""
        try:
            session_data = {
                "session_info": {
                    "start_time": self.start_time.isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "duration": str(datetime.now() - self.start_time),
                    "channels_processed": self.session_overview.stats["processed"],
                },
                "performance": {
                    "peak_speed": self.performance_tracker.session_stats["peak_speed"],
                    "avg_speed": self.performance_tracker.session_stats["avg_speed"],
                    "trend_analysis": self.performance_tracker.get_trend_analysis(),
                },
                "results": {
                    "new_videos": self.session_overview.stats["new_videos"],
                    "upgrades": self.session_overview.stats["upgrades"],
                    "failed": self.session_overview.stats["failed"],
                },
            }

            session_file = Path(
                f"session_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=2, default=str)

        except Exception:
            pass

    def get_final_summary(self) -> str:
        """Generate final session summary."""
        try:
            success_rate = (
                (
                    self.session_overview.stats["new_videos"]
                    + self.session_overview.stats["upgrades"]
                    - self.session_overview.stats["failed"]
                )
                / max(
                    1,
                    self.session_overview.stats["new_videos"]
                    + self.session_overview.stats["upgrades"],
                )
                * 100
            )

            summary_msg = (
                f"🎉 Session complete! "
                f"Processed {self.session_overview.stats['processed']} channels, "
                f"{self.session_overview.stats['new_videos'] + self.session_overview.stats['upgrades']} downloads, "
                f"{success_rate:.1f}% success rate"
            )

            return summary_msg

        except Exception:
            return "Session completed."

    def update_session_display(self):
        """Update session display components."""
        if (
            hasattr(self.session_overview, "app")
            and self.session_overview.app.is_shutting_down
        ):
            return

        processed_count = len(
            [
                node
                for node in self.session_overview.app.enhanced_channel_tree.channel_nodes.values()
                if hasattr(node, "data")
            ]
        )

        self.session_overview.update_stats({"processed": processed_count})
