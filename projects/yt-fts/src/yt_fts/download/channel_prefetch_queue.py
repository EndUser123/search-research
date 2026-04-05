"""
ChannelPrefetchQueue - Async channel metadata prefetching with progress tracking.

Reduces batch download startup latency by:
- Starting background thread immediately
- Fetching channel names in parallel
- Providing non-blocking queue interface for consumers
- Showing progress indicator

Usage:
    queue = ChannelPrefetchQueue(channel_ids, console=console)
    queue.start()
    # Consumers can now call:
    if queue.is_ready(channel_id):
        name = queue.get_name(channel_id)
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)


class ChannelPrefetchQueue:
    """
    Thread-safe queue for async channel metadata prefetching.

    Fetches channel names in background thread and stores results in database.
    Provides non-blocking interface for consumers to check completion status.
    """

    def __init__(
        self,
        channel_ids: list[str],
        fetcher: "Callable[[str], tuple[str | None, str | None]]",
        console: Console | None = None,
        suppress_verbose: bool = False,
        max_workers: int = 8,
    ):
        """
        Initialize prefetch queue.

        Args:
            channel_ids: List of channel IDs to prefetch
            fetcher: Function that fetches metadata for a single channel
                    Should return (name, url) tuple or (None, None) on failure
            console: Rich console for progress display
            suppress_verbose: If True, suppress progress output
            max_workers: Maximum number of parallel fetch threads
        """
        self.channel_ids = channel_ids
        self._fetcher = fetcher
        self.console = console
        self.suppress_verbose = suppress_verbose
        self.max_workers = max_workers

        # Thread-safe state
        self._lock = threading.Lock()
        self._completed: set[str] = set()
        self._total = len(channel_ids)
        self._thread: threading.Thread | None = None
        self._started = False
        self._stopped = False

        # Lazy imports to avoid circular dependency
        self._add_channel_info = None
        self._get_db_connection = None

    def _init_db_functions(self):
        """Lazy import of DB functions to avoid circular dependency."""
        if self._add_channel_info is None:
            from yt_fts.core.database import get_db_connection
            from yt_fts.db.channels import add_channel_info

            self._add_channel_info = add_channel_info
            self._get_db_connection = get_db_connection

    def start(self) -> None:
        """Start background prefetch thread."""
        if self._started:
            return

        self._init_db_functions()
        self._started = True
        self._thread = threading.Thread(target=self._prefetch_worker, daemon=True)
        self._thread.start()

    def is_ready(self, channel_id: str) -> bool:
        """
        Check if channel name has been fetched and is available in database.

        Args:
            channel_id: Channel ID to check

        Returns:
            True if channel name is ready in database, False otherwise
        """
        # Check if completed by our worker
        with self._lock:
            if channel_id in self._completed:
                return True

        # Also check database (might have been cached from previous run)
        self._init_db_functions()
        try:
            name = self._get_channel_name_from_db(channel_id)
            return name is not None
        except Exception:
            return False

    def get_name(self, channel_id: str) -> str | None:
        """
        Get channel name from database.

        Args:
            channel_id: Channel ID to lookup

        Returns:
            Channel name if found, None otherwise
        """
        self._init_db_functions()
        return self._get_channel_name_from_db(channel_id)

    def _get_channel_name_from_db(self, channel_id: str) -> str | None:
        """Get channel name from database (internal method)."""
        if self._get_db_connection is None:
            return None

        try:
            conn = self._get_db_connection(timeout=5.0)
            with conn:
                res = conn.execute(
                    "SELECT channel_name FROM Channels WHERE channel_id = ?",
                    (channel_id,),
                ).fetchone()
                if res:
                    return res[0]
        except Exception:
            pass
        return None

    def wait_for(self, channel_id: str, timeout: float = 5.0) -> bool:
        """
        Block until channel name is ready or timeout expires.

        Args:
            channel_id: Channel ID to wait for
            timeout: Maximum seconds to wait

        Returns:
            True if ready, False if timeout
        """
        import time

        start = time.time()
        while time.time() - start < timeout:
            if self.is_ready(channel_id):
                return True
            time.sleep(0.05)  # 50ms polling
        return False

    def get_progress(self) -> tuple[int, int]:
        """
        Get current progress.

        Returns:
            Tuple of (completed_count, total_count)
        """
        with self._lock:
            return len(self._completed), self._total

    def is_complete(self) -> bool:
        """
        Check if all channels have been processed.

        Returns:
            True if all channels done, False otherwise
        """
        completed, total = self.get_progress()
        return completed >= total

    def _prefetch_worker(self) -> None:
        """Background thread that fetches all channel metadata."""
        if not self.channel_ids:
            return

        # Batch query to find missing channels
        missing_channels = self._find_missing_channels()
        if not missing_channels:
            with self._lock:
                self._completed.update(self.channel_ids)
            return

        # Show initial message
        if not self.suppress_verbose and self.console:
            self.console.print(
                f"[cyan]Pre-fetching metadata for {len(missing_channels)} channels in parallel...[/cyan]"
            )

        # Setup progress bar (shown in both verbose and non-verbose modes if console available)
        progress = None
        if self.console:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console,
                transient=True,
                disable=False,  # Always show progress bar
            )
            progress.start()
            task = progress.add_task("Pre-fetching channels", total=len(missing_channels))

        # Run parallel fetches
        max_workers = min(self.max_workers, len(missing_channels))
        completed = 0

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_channel = {
                    executor.submit(self._fetcher, channel_id): channel_id
                    for channel_id in missing_channels
                }

                for future in as_completed(future_to_channel):
                    if self._stopped:
                        break

                    channel_id = future_to_channel[future]
                    try:
                        name, url = future.result()
                        if name:
                            save_url = url if url else f"https://www.youtube.com/channel/{channel_id}"
                            self._add_channel_info(channel_id, name, save_url)
                        else:
                            # Mark as not found to prevent future retries
                            failed_name = f"[Channel Not Found] {channel_id}"
                            self._add_channel_info(
                                channel_id, failed_name, f"https://www.youtube.com/channel/{channel_id}"
                            )
                    except Exception as e:
                        logger.debug("Prefetch error for %s: %s", channel_id, e)
                        # Mark as failed to prevent future retries
                        failed_name = f"[Fetch Error] {channel_id}"
                        self._add_channel_info(
                            channel_id, failed_name, f"https://www.youtube.com/channel/{channel_id}"
                        )

                    # Update state
                    with self._lock:
                        self._completed.add(channel_id)
                    completed += 1

                    if progress:
                        progress.update(task, completed=completed)

        finally:
            if progress:
                progress.stop()

        # Mark all as complete (including ones that were already cached)
        with self._lock:
            self._completed.update(self.channel_ids)

    def _find_missing_channels(self) -> list[str]:
        """Find channels that need fetching (not in DB or have raw ID as name)."""
        if not self.channel_ids or self._get_db_connection is None:
            return []

        # Batch query to get all names at once
        name_map: dict[str, str | None] = {}
        try:
            conn = self._get_db_connection(timeout=5.0)
            with conn:
                placeholders = ",".join(["?"] * len(self.channel_ids))
                rows = conn.execute(
                    f"SELECT channel_id, channel_name FROM Channels WHERE channel_id IN ({placeholders})",
                    self.channel_ids,
                ).fetchall()
                name_map = {row[0]: row[1] for row in rows}
        except Exception:
            pass

        # Find missing ones
        missing = []
        for channel_id in self.channel_ids:
            name = name_map.get(channel_id)
            if not name or self._is_raw_channel_id(name):
                missing.append(channel_id)

        return missing

    def _is_raw_channel_id(self, name: str) -> bool:
        """Check if name is a raw channel ID (e.g., UC...)."""
        return (
            name.startswith("UC")
            and len(name) == 24
            and all(c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" for c in name[2:])
        )

    def stop(self) -> None:
        """Signal the prefetch thread to stop."""
        with self._lock:
            self._stopped = True

    def join(self, timeout: float | None = None) -> bool:
        """
        Wait for prefetch thread to complete.

        Args:
            timeout: Maximum seconds to wait, None for infinite

        Returns:
            True if thread completed, False if timeout
        """
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            return not self._thread.is_alive()
        return True
