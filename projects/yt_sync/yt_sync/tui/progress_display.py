"""
Progress display components for the TUI.
"""

from typing import Any

from textual.containers import Container, Horizontal
from textual.widget import Widget
from textual.widgets import ProgressBar, Static

from .performance_tracker import PerformanceTracker


class EnhancedProgressDisplay(Widget):
    """Enhanced progress display with better tracking."""

    def __init__(self, max_slots: int = 4):
        super().__init__(id="enhanced-progress")
        self.max_slots = max_slots
        self.download_slots: list[dict[str, Any]] = []
        self.active_downloads: dict[str, int] = {}
        self.performance_tracker = PerformanceTracker()

        for i in range(max_slots):
            self.download_slots.append(
                {
                    "id": i,
                    "active": False,
                    "video_id": None,
                    "filename": "",
                    "progress": 0.0,
                    "rate": 0.0,
                    "eta": 0,
                }
            )

    def compose(self):
        yield Static("⚡ Download Progress", classes="section-title")

        with Horizontal(classes="progress-summary"):
            yield Static("Active: 0", id="active-count", classes="stat-item")
            yield Static("Avg Speed: 0 MB/s", id="avg-speed", classes="stat-item")
            yield Static("Peak: 0 MB/s", id="peak-speed", classes="stat-item")

        with Container(id="download-slots"):
            for i in range(self.max_slots):
                with Container(classes="download-slot", id=f"slot-{i}"):
                    yield Static(
                        f"Slot {i + 1}: Idle",
                        classes="slot-header",
                        id=f"slot-{i}-header",
                    )
                    yield ProgressBar(id=f"slot-{i}-progress", show_percentage=True)
                    yield Static("", id=f"slot-{i}-details", classes="slot-details")

    def update_slot(
        self, video_id: str, filename: str, progress: float, rate: float, eta: int
    ):
        """Update a download slot."""
        if video_id not in self.active_downloads:
            slot_id = self._find_available_slot()
            if slot_id is not None:
                self.active_downloads[video_id] = slot_id
                self.download_slots[slot_id]["active"] = True
                self.download_slots[slot_id]["video_id"] = video_id
            else:
                return

        slot_id = self.active_downloads[video_id]
        slot = self.download_slots[slot_id]

        slot.update(
            {"filename": filename, "progress": progress, "rate": rate, "eta": eta}
        )

        self.performance_tracker.add_rate(rate / 1024 / 1024)
        self._update_slot_display(slot_id)
        self._update_summary()

    def complete_slot(self, video_id: str):
        """Mark a download slot as completed."""
        if video_id in self.active_downloads:
            slot_id = self.active_downloads[video_id]
            slot = self.download_slots[slot_id]

            slot.update(
                {
                    "active": False,
                    "video_id": None,
                    "filename": "",
                    "progress": 0.0,
                    "rate": 0.0,
                    "eta": 0,
                }
            )

            del self.active_downloads[video_id]
            self._update_slot_display(slot_id)
            self._update_summary()

    def complete_download(self, video_id: str):
        """Compatibility method - calls complete_slot."""
        self.complete_slot(video_id)

    def update_download_progress(
        self, video_id: str, filename: str, progress: float, rate: float, eta: int
    ):
        """Compatibility method - calls update_slot."""
        self.update_slot(video_id, filename, progress, rate, eta)

    def _initial_display_setup(self):
        """Set up initial display state."""
        self._update_summary()
        for i in range(self.max_slots):
            self._update_slot_display(i)

    def _find_available_slot(self) -> int | None:
        """Find the first available download slot."""
        for i, slot in enumerate(self.download_slots):
            if not slot["active"]:
                return i
        return None

    def _update_slot_display(self, slot_id: int):
        """Update the display for a specific slot."""
        try:
            slot = self.download_slots[slot_id]

            header = self.query_one(f"#slot-{slot_id}-header", Static)
            progress_bar = self.query_one(f"#slot-{slot_id}-progress", ProgressBar)
            details = self.query_one(f"#slot-{slot_id}-details", Static)

            if slot["active"]:
                display_name = slot["filename"]
                if len(display_name) > 35:
                    display_name = f"...{display_name[-32:]}"

                header.update(f"Slot {slot_id + 1}: {display_name}")
                progress_bar.update(progress=slot["progress"])

                rate = slot["rate"]
                if rate > 1024 * 1024:
                    rate_str = f"{rate / 1024 / 1024:.1f} MB/s"
                else:
                    rate_str = f"{rate / 1024:.1f} KB/s"

                eta_str = f"{slot['eta']}s" if slot["eta"] > 0 else "∞"
                details.update(f"{rate_str} • ETA: {eta_str}")
            else:
                header.update(f"Slot {slot_id + 1}: Idle")
                progress_bar.update(progress=0)
                details.update("")
        except Exception:
            pass

    def _update_summary(self):
        """Update the summary statistics."""
        try:
            active_slots = [slot for slot in self.download_slots if slot["active"]]

            active_count = self.query_one("#active-count", Static)
            avg_speed = self.query_one("#avg-speed", Static)
            peak_speed = self.query_one("#peak-speed", Static)

            active_count.update(f"Active: {len(active_slots)}")

            if active_slots:
                avg_rate = sum(slot["rate"] for slot in active_slots) / len(
                    active_slots
                )
                avg_rate_mb = avg_rate / 1024 / 1024
                avg_speed.update(f"Avg: {avg_rate_mb:.1f} MB/s")
            else:
                avg_speed.update("Avg: 0 MB/s")

            peak_speed.update(
                f"Peak: {self.performance_tracker.session_stats['peak_speed']:.1f} MB/s"
            )
        except Exception:
            pass
