"""
Main TUI application for YouTube Sync.
"""

import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

import os
import sys

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal
from textual.widgets import Footer, Header, Log, Pretty, TabbedContent, TabPane

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api_client import YouTubeAPIClient
from syncer import ChannelSyncer

from .analytics_service import AnalyticsService
from .channel_tree import EnhancedChannelTree
from .log_store import EnhancedLogStore
from .performance_tracker import PerformanceTracker
from .progress_display import EnhancedProgressDisplay
from .session_manager import SessionManager
from .session_overview import SessionOverview
from .tui_logger import TUILogger


class ProfessionalTUIDisplay(App):
    def handle_download_progress(self, msg: dict):
        """Thread-safe handler for download progress updates from downloader (called by downloader_rich)."""
        # This method is called from downloader threads; use call_from_thread for UI updates
        status = msg.get("status")
        info_dict = msg.get("info_dict", {})
        video_id = info_dict.get("id")
        filename = msg.get("filename", "")
        progress = 0.0
        rate = 0.0
        eta = 0
        if status == "downloading":
            total = msg.get("total_bytes_estimate") or msg.get("total_bytes") or 1
            downloaded = msg.get("downloaded_bytes", 0)
            progress = min(1.0, downloaded / total) if total else 0.0
            rate = msg.get("speed", 0.0)
            eta = int(msg.get("eta", 0) or 0)
            self.call_from_thread(
                self.enhanced_progress.update_download_progress,
                video_id,
                filename,
                progress,
                rate,
                eta,
            )
        elif status == "finished":
            self.call_from_thread(self.enhanced_progress.complete_download, video_id)

    """Professional YouTube Sync TUI with enhanced features."""

    BINDINGS = [
        Binding("d", "toggle_dark", "Dark Mode"),
        Binding("ctrl+p", "show_performance", "Performance"),
        Binding("ctrl+s", "export_session", "Export"),
        Binding("f5", "refresh_display", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    CSS_PATH = "tui_layout.css"

    args: Any = None  # Allows dynamic assignment from main_logic

    def __init__(self, total_channels: int):
        super().__init__()
        self.total_channels = total_channels
        self.start_time = datetime.now()
        self.shutdown_event = threading.Event()
        self.is_shutting_down = False

        # Core components
        self.log_store = EnhancedLogStore()
        self.performance_tracker = PerformanceTracker()
        self.session_overview = SessionOverview(total_channels)
        self.enhanced_progress = EnhancedProgressDisplay()
        self.enhanced_channel_tree = EnhancedChannelTree()

        # Services
        self.tui_logger = TUILogger(self)
        self.analytics_service = AnalyticsService(
            self.session_overview, self.performance_tracker, self.log_store
        )
        self.session_manager = SessionManager(
            self.session_overview, self.performance_tracker, self.start_time
        )

        self.current_channel = None

    def compose(self) -> ComposeResult:
        """Create the professional TUI layout."""
        yield Header(show_clock=True, name="YouTube Sync Pro")

        with Grid(id="main-grid"):
            with Horizontal(id="top-section"):
                yield self.session_overview
                yield self.enhanced_progress

            with Horizontal(id="bottom-section"):
                yield self.enhanced_channel_tree
                with TabbedContent(id="log-tabs"):
                    with TabPane("Smart Logs", id="smart-tab"):
                        yield Log(id="smart-log", classes="log-widget")
                    with TabPane("Performance", id="perf-tab"):
                        yield Log(id="performance-log", classes="log-widget")
                    with TabPane("Analytics", id="analytics-tab"):
                        yield Pretty(
                            {"status": "Initializing analytics..."},
                            id="analytics-display",
                        )

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the professional TUI."""
        self.set_interval(1.0, self.session_manager.update_session_display)
        self.set_interval(5.0, self.analytics_service.update_analytics_display)
        self.tui_logger.setup_logging()
        self.run_sync_process()  # Start the main sync process
        self.notify(
            "🚀 Professional YouTube Sync TUI initialized", severity="information"
        )

    # --- Worker Management and Message Handling ---

    @work(exclusive=True, thread=True)
    def run_sync_process(self) -> None:
        """The main worker that orchestrates the entire sync operation."""
        # This code is now running in a background thread, managed by Textual.
        from main_logic import (
            handle_session_resume,
            load_channel_urls,
            load_configuration,
        )

        args = self.args  # Access args passed to the app
        config_path = Path(args.config)
        config = load_configuration(config_path)

        # Clear the channel tree at the start of each sync session
        self.enhanced_channel_tree.clear_tree()

        api_client = None
        if config.get("youtube_api_keys"):
            api_client = YouTubeAPIClient(config["youtube_api_keys"])

        channel_urls = load_channel_urls(config)
        channels_to_process, original_count = handle_session_resume(
            channel_urls, args.from_start
        )

        for i, channel_url in enumerate(
            channels_to_process, start=original_count - len(channels_to_process) + 1
        ):
            if self.shutdown_event.is_set():
                logger.warning("Shutdown signal received, stopping channel processing.")
                break

            syncer = ChannelSyncer(
                url=channel_url,
                index=i,
                args=args,
                all_filters=config.get("filters", {}),
                api_client=api_client,
                display=self,
            )
            syncer.process()

    def set_current_channel(self, name: str, index: int, total: int):
        """Set the currently processing channel."""
        if self.is_shutting_down:
            return

        self.current_channel = {"name": name, "index": index, "total": total}

        self.tui_logger.set_current_channel(name)

        self.enhanced_channel_tree.add_channel_node(name, "processing")
        self.log_store.add_log(
            f"Processing channel {index}/{total}: {name}", "INFO", name
        )
        self.call_from_thread(self.tui_logger.set_current_channel, name)

    def add_channel_result(self, result: dict[str, Any]):
        """Add a completed channel result."""
        if self.is_shutting_down:
            return

        def _add_result():
            if self.is_shutting_down:
                return

            try:
                channel_name = result.get("name", "Unknown")
                status = result.get("status", "complete")

                self.enhanced_channel_tree.update_channel_status(
                    channel_name, status, result
                )

                stats_update = {
                    "new_videos": self.session_overview.stats["new_videos"]
                    + result.get("new_videos", 0),
                    "upgrades": self.session_overview.stats["upgrades"]
                    + result.get("upgrades", 0),
                    "failed": self.session_overview.stats["failed"]
                    + result.get("failed", 0),
                }
                self.session_overview.update_stats(stats_update)

                self.log_store.add_log(
                    f"Completed: {channel_name} - New: {result.get('new_videos', 0)}, Upgrades: {result.get('upgrades', 0)}, Failed: {result.get('failed', 0)}",
                    "INFO",
                    channel_name,
                )

                if result.get("failed", 0) > 0:
                    self.notify(
                        f"⚠️ {result['failed']} downloads failed for {channel_name}",
                        severity="warning",
                        timeout=8,
                    )
                elif result.get("new_videos", 0) > 5:
                    self.notify(
                        f"📈 {result['new_videos']} new videos from {channel_name}",
                        severity="information",
                        timeout=5,
                    )

            except Exception:
                pass

        try:
            if self.is_running:
                self.call_from_thread(_add_result)
        except Exception:
            pass

    def update_download_progress(self, progress_data: dict[str, Any]) -> None:
        """Update download progress."""
        if self.is_shutting_down:
            return

        logger.debug(f"TUI_TRACE: update_download_progress received: {progress_data}")
        try:
            video_id = progress_data.get("info_dict", {}).get("id", "unknown")
            filename = progress_data.get("filename", "Unknown file")

            logger.debug(
                f"TUI_TRACE: Extracted video_id '{video_id}' and filename '{filename}'"
            )

            if progress_data.get("status") == "downloading":
                downloaded = progress_data.get("downloaded_bytes", 0)
                total = progress_data.get("total_bytes") or progress_data.get(
                    "total_bytes_estimate", 0
                )

                if total > 0:
                    progress_pct = (downloaded / total) * 100
                    speed = progress_data.get("speed", 0) or 0
                    eta = progress_data.get("eta", 0)

                    logger.debug(
                        f"TUI_TRACE: Calling update_slot for '{video_id}' with progress {progress_pct:.2f}%"
                    )
                    self.enhanced_progress.update_slot(
                        video_id, Path(filename).name, progress_pct, speed, eta
                    )

            elif progress_data.get("status") == "finished":
                self.enhanced_progress.complete_slot(video_id)
        except Exception as e:
            logger.debug(f"TUI_TRACE: Exception in update_download_progress: {e}")

    # Add the multi_progress property for compatibility
    @property
    def multi_progress(self):
        """Compatibility property for multi_progress access."""
        return self.enhanced_progress

    def final_summary(self):
        """Display final summary."""
        if self.is_shutting_down:
            return

        summary_msg = self.session_manager.get_final_summary()
        self.notify(summary_msg, severity="information", timeout=15)
        self.session_manager.export_session_data()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
        self.notify("🌓 Theme toggled", severity="information", timeout=2)

    def action_show_performance(self) -> None:
        """Show performance analysis."""
        analysis = self.performance_tracker.get_trend_analysis()
        self.notify(
            f"📊 Performance: {analysis['trend']} trend, {analysis['stability']:.1f}% stability",
            severity="information",
            timeout=5,
        )

    def action_export_session(self) -> None:
        """Export session data."""
        self.session_manager.export_session_data()
        self.notify("💾 Session data exported", severity="information", timeout=3)

    def action_refresh_display(self) -> None:
        """Refresh display."""
        self.notify("🔄 Display refreshed", severity="information", timeout=2)

    async def action_quit(self) -> None:
        """Graceful shutdown."""
        self.is_shutting_down = True
        self.shutdown_event.set()
        self.final_summary()

        self.tui_logger.shutdown()

        self.exit()

    def on_unmount(self) -> None:
        """Clean up when TUI shuts down."""
        self.is_shutting_down = True
        self.tui_logger.shutdown()


# Compatibility aliases
TUIDisplay = ProfessionalTUIDisplay


def setup_tui_logging(app_instance):
    """
    Configures the root logger to send records to the TUI app's queue.
    This is called from the main thread before the app starts.
    """

    class TUIQueueHandler(logging.Handler):
        def __init__(self, queue_list):
            super().__init__()
            self.queue_list = queue_list

        def emit(self, record):
            self.queue_list.append(self.format(record))

    # In a more complex app, this would be a real queue.Queue
    # For now, we can adapt the existing log store.
    # The key is to stop using RichHandler in TUI mode.
