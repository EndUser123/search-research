import asyncio
import os
import signal
import sys
import threading
import time
from typing import Any
from typing import Any as _Any  # for type hints safety

from loguru import logger

from ..base import BaseUIDisplay, ConcurrentDownloadMixin

# TARGETED FIX: Reduce positioning conflicts while maintaining line tracking
os.environ["TQDM_MININTERVAL"] = "0.1"
os.environ["TQDM_MAXINTERVAL"] = "1.0"

try:
    import tqdm as tqdm_module  # type: ignore
    import tqdm.asyncio  # type: ignore
    from tqdm import tqdm as tqdm_class  # type: ignore
    from tqdm.utils import _unicode  # type: ignore

    TQDM_AVAILABLE = True

    # MINIMAL FIX: Reduce positioning conflicts while maintaining functionality
    if hasattr(tqdm_module, "tqdm"):
        # Reduce monitoring frequency to minimize conflicts
        tqdm_module.tqdm.monitor_interval = 10  # Increase interval instead of disabling

        # Force locale to prevent formatting issues
        import locale

        try:
            locale.setlocale(locale.LC_NUMERIC, "C")
        except locale.Error:
            pass

except ImportError:
    TQDM_AVAILABLE = False

    # Fallback shim to satisfy type checkers; will never be called at runtime because we raise in __init__
    def tqdm(*args, **kwargs):  # type: ignore
        raise ImportError("tqdm not available")

    def _unicode(x: _Any) -> str:  # type: ignore
        return str(x)


def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float with proper error handling.

    Args:
        value: Value to convert to float (can be int, float, str, None, etc.)
        default: Default value to return if conversion fails

    Returns:
        float: Converted value or default if conversion fails
    """
    if value is None:
        return default
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            # Return default for type conversion errors instead of raising
            logger.debug(f"Float conversion failed for value {value}: {e}")
            return default
    if isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            # Return default for string parsing errors instead of raising
            logger.debug(f"Float parsing failed for string '{value}': {e}")
            return default
    # For any other type, return default
    return default


class TQDMDisplay(BaseUIDisplay, ConcurrentDownloadMixin):
    """
    Clean TQDM progress display with single overall progress bar and individual file bars.

    Architecture:
    - One main progress bar at position 0 (overall progress)
    - Individual file progress bars at positions 1+ (up to max_concurrent)
    - All bars use consistent formatting and positioning
    - No redundant refreshes or duplicate creation
    """

    FILE_ICONS = {
        ".mp4": "🎥",
        ".mkv": "🎥",
        ".avi": "🎥",
        ".mp3": "🎵",
        ".wav": "🎵",
        ".flac": "🎵",
        ".jpg": "🖼️",
        ".jpeg": "🖼️",
        ".png": "🖼️",
        ".gif": "🖼️",
        ".zip": "📦",
        ".rar": "📦",
        ".7z": "📦",
        ".pdf": "📄",
        ".txt": "📝",
        ".doc": "📃",
        ".docx": "📃",
        ".xls": "📊",
        ".xlsx": "📊",
        ".ppt": "📈",
        ".pptx": "📈",
    }
    DEFAULT_ICON = "📁"
    """TQDM-based progress display"""

    # Class variable to track if warning has been shown
    _warning_shown = False

    def __init__(
        self,
        console: Any | None = None,
        show_file_progress: bool = True,
        config: Any | None = None,
        enhanced_mode: bool = False,
    ):
        super().__init__(console=console)
        self.main_tqdm: Any | None = None  # tqdm progress bar instance
        self.download_tqdms: dict[str, Any] = {}
        self.active_positions: set = set()  # Track currently used positions
        self.position_lock = threading.Lock()  # Lock for position management
        self.total_bytes_downloaded: float = (
            0.0  # Track total bytes for speed calculation
        )
        self.start_time: float | None = None  # Track start time for speed calculation
        self.last_refresh_time: float = 0.0  # Track last refresh for periodic cleanup
        self._bar_creation_lock = threading.Lock()  # Thread-safe bar creation
        self.config = config
        self.channel_name: str | None = None  # Store channel name
        self.enhanced_mode: bool = enhanced_mode  # Enable enhanced mode for UI B

        # Terminal resilience
        self._terminal_corrupted = False
        self._last_terminal_size = self._get_terminal_size()
        self._terminal_check_counter = 0  # Counter for periodic checking
        self._shutdown_requested = False  # Flag to prevent new threads during shutdown
        self._setup_terminal_resilience()

        # Get max concurrent from config or default to 2
        max_concurrent = 2
        if config and hasattr(config, "max_concurrent"):
            max_concurrent = getattr(config, "max_concurrent", 2)

        # Reserved render region parameters - limit display for cleaner output
        self.max_file_bars = max(
            1, min(3, max_concurrent)
        )  # At least 1, max 3 for cleaner display
        self.region_height = self.max_file_bars + 1  # file bars + overall bar

        if not TQDM_AVAILABLE:
            raise ImportError("tqdm not available. Install with: pip install tqdm")

    async def initialize(self) -> None:
        """Initialize the TQDM display"""
        # Warning message now shown in main.py before channel processing starts
        # Skip showing it here to avoid duplication
        TQDMDisplay._warning_shown = True

        # Show enhanced header in enhanced mode
        if self.enhanced_mode:
            self._show_enhanced_header()

    def _create_main_progress_bar(self, total_files: int) -> None:
        """Create the main progress bar with consistent configuration"""
        if self.main_tqdm is None and total_files > 0:
            self.stats["total_files"] = total_files
            self.start_time = time.time()
            self.stats["start_time"] = self.start_time

            # Main bar at position 0 (top) as per documentation
            channel_display = self.channel_name or "Channel"
            self.main_tqdm = tqdm_class(
                total=total_files,
                unit="files",
                desc=f"📊 {channel_display} Progress",
                leave=True,
                ncols=100,
                colour="green",
                position=0,  # Main bar at position 0 (top)
                dynamic_ncols=False,
                file=sys.stdout,
                # Clean format with proper progress bar display - consistent column alignment
                bar_format="{desc:<33} [{bar:25}] {percentage:3.0f}% {n_fmt:>7} / {total_fmt:<7}",
            )
            self.log(
                f"[TQDM] Main progress bar created for {channel_display} with {total_files} files at POSITION 0 (main bar).",
                "debug",
            )

    # --- Formatting helpers to construct display strings outside tqdm ---
    @staticmethod
    def _fmt_hhmm(seconds: float) -> str:
        if seconds is None or seconds == 0:
            return "--:--"
        try:
            sec = float(seconds)
        except (TypeError, ValueError) as e:
            # Return default for time conversion errors
            logger.debug(f"Time formatting failed for seconds {seconds}: {e}")
            return "--:--"
        if sec <= 0:
            return "--:--"
        m, s = divmod(int(sec + 0.5), 60)
        h, m = divmod(m, 60)
        if h > 99:
            h = 99
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        else:
            return f"{m:02d}:{s:02d}"

    @staticmethod
    def _fmt_speed(rate_bps: float) -> str:
        if rate_bps is None:
            return "?B/s"
        try:
            bps = float(rate_bps)
        except (TypeError, ValueError) as e:
            # Default to 0.0 for rate conversion errors
            logger.debug(f"Rate formatting failed for rate_bps {rate_bps}: {e}")
            bps = 0.0
        if bps <= 0:
            return "?B/s"
        mbps = bps / (1024.0 * 1024.0)
        if mbps >= 1000:
            return f"{mbps / 1024:.1f}GB/s"
        elif mbps >= 10:
            return f"{mbps:.0f}MB/s"
        elif mbps >= 1:
            return f"{mbps:.1f}MB/s"
        elif bps >= 1024:
            return f"{bps / 1024:.1f}KB/s"
        else:
            return f"{bps:.0f}B/s"

    @staticmethod
    def _build_postfix(
        elapsed_sec: float, remaining_sec: float, rate_bps: float
    ) -> str:
        # Single, pre-composed string (no commas or parentheses introduced by tqdm)
        elap = TQDMDisplay._fmt_hhmm(elapsed_sec)
        rem = TQDMDisplay._fmt_hhmm(remaining_sec)
        spd = TQDMDisplay._fmt_speed(rate_bps)
        return f" {elap:>5} | {rem:>5} | {spd:>7}"

    async def start_progress(self, total_files: int) -> None:
        """Initialize the main progress bar - called once at start"""
        # Always create a fresh progress bar to prevent state corruption between channels
        if self.main_tqdm is not None:
            # Clean up existing bar first
            try:
                self.main_tqdm.close()
            except Exception:
                pass
            self.main_tqdm = None

        self._create_main_progress_bar(total_files)

    async def update_progress(
        self,
        current: int,
        filename: str,
        status: str = "downloading",
    ) -> None:
        """Update main progress bar with status"""
        # Check terminal health periodically (Windows fallback)
        self._check_terminal_health()

        if self.main_tqdm:
            if status in ["completed", "failed", "error"]:
                self.main_tqdm.update(1)

            # Update stats first
            if status == "completed":
                self.stats["downloaded"] = self.stats.get("downloaded", 0) + 1
            elif status in ["failed", "error"]:
                self.stats["failed"] = self.stats.get("failed", 0) + 1

            # Update description with current file status - prevent duplicate rendering
            short_name = (
                filename[:33] if len(filename) > 33 else filename
            )  # Increased from 25 to 33 (+8 chars)
            current_desc = getattr(self.main_tqdm, "desc", "")

            if status == "completed":
                new_desc = f"📊 Completed: {short_name} ✅"
            elif status in ["failed", "error"]:
                new_desc = f"📊 Error: {short_name} ❌"
            else:
                new_desc = f"📊 Downloading: {short_name} 📥"

            # Only update if description actually changed
            if current_desc != new_desc:
                self.main_tqdm.set_description(new_desc, refresh=False)

            # Show enhanced statistics periodically for UI B mode
            if self.enhanced_mode and status in ["completed", "failed", "error"]:
                self._show_enhanced_statistics()

    async def finish_progress(self) -> None:
        """Finish TQDM progress and show summary"""
        # Set shutdown flag first
        self._shutdown_requested = True

        # Close main progress bar
        if self.main_tqdm:
            try:
                self.main_tqdm.close()
            except Exception:
                pass
            finally:
                self.main_tqdm = None

        # Final summary
        elapsed = 0.0
        start_time = self.stats.get("start_time", 0)
        if isinstance(start_time, (int, float)):
            elapsed = time.time() - float(start_time)

        total_files_raw = self.stats.get("total_files", 0)
        total_files = (
            int(float(total_files_raw))
            if isinstance(total_files_raw, (int, float))
            else 0
        )
        downloaded_files_raw = self.stats.get("downloaded", 0)
        downloaded_files = (
            int(float(downloaded_files_raw))
            if isinstance(downloaded_files_raw, (int, float))
            else 0
        )

        success_rate = (downloaded_files / total_files * 100) if total_files > 0 else 0

        try:
            from tqdm import tqdm

            tqdm.write("\n🎉 Download completed!")
            tqdm.write("📊 Results:")
            tqdm.write(f"   ✅ Downloaded: {downloaded_files}")
            tqdm.write(f"   ❌ Failed: {self.stats['failed']}")
            tqdm.write(f"   📈 Success rate: {success_rate:.1f}%")
            tqdm.write(f"   ⏱️  Total time: {elapsed:.1f} seconds")

            if elapsed > 0:
                tqdm.write(
                    f"   🚀 Average speed: {downloaded_files / elapsed:.1f} files/second"
                )
            else:
                tqdm.write("   🚀 Average speed: N/A (elapsed time is zero)")
        except ImportError:
            pass  # Silently skip if tqdm not available

    def clear_all_progress_bars(self) -> None:
        """Clear all progress bars immediately for clean termination display"""
        import sys

        try:
            # Close all file progress bars without delay
            for filename in list(self.download_tqdms.keys()):
                try:
                    task_info = self.download_tqdms[filename]
                    if isinstance(task_info, dict) and task_info.get("tqdm_bar"):
                        task_info["tqdm_bar"].close()
                except Exception:
                    pass

            # Close main progress bar
            if self.main_tqdm:
                try:
                    self.main_tqdm.close()
                except Exception:
                    pass

            # Move cursor to bottom for clean output and clear positioning artifacts
            sys.stdout.write("\033[0m")  # Reset all formatting
            sys.stdout.write("\n" * (self.max_file_bars + 2))
            sys.stdout.flush()

        except Exception:
            pass  # Best effort cleanup

    async def cleanup(self) -> None:
        """Cleanup TQDM resources with proper exception handling"""
        # Set shutdown flag to prevent new threads
        self._shutdown_requested = True

        # Give any running threads a moment to see the shutdown flag
        await asyncio.sleep(0.1)

        # Close all file progress bars first
        for filename in list(self.download_tqdms.keys()):
            try:
                task_info = self.download_tqdms[filename]
                if isinstance(task_info, dict) and task_info.get("tqdm_bar"):
                    # Release position if it was assigned
                    if "position" in task_info:
                        self._release_position(task_info["position"])
                    # Force close with timeout protection
                    try:
                        task_info["tqdm_bar"].close()
                    except Exception:
                        pass
            except Exception:
                pass  # Best effort cleanup
            finally:
                # Always remove from dict
                self.download_tqdms.pop(filename, None)

        # Close main progress bar
        if self.main_tqdm:
            try:
                self.main_tqdm.close()
            except Exception:
                pass  # Best effort cleanup
            finally:
                self.main_tqdm = None

    # --- INFO overlay support (fastest restoration: restore on next progress update) ---
    def show_info_line(self, text: str) -> None:
        """
        Temporarily overwrite the top-most active file bar's description with an INFO line.
        Restoration strategy: as soon as the next progress update happens for that bar,
        its description will be reset by normal update calls. This is the quickest approach.
        """
        # Find active bars and pick the one with the lowest position (top-most)
        active = []
        for info in self.download_tqdms.values():
            if isinstance(info, dict) and info.get("tqdm_bar"):
                try:
                    bar = info["tqdm_bar"]
                    pos = getattr(bar, "pos", 9999)
                    active.append((pos, bar))
                except Exception:
                    continue
        if not active:
            return
        active.sort(key=lambda t: t[0])
        top_bar = active[0][1]
        try:
            # Truncate message to avoid wrapping; ensure minimal width
            msg = text.strip().replace("\n", " ")
            if len(msg) > 60:
                msg = msg[:60]
            top_bar.set_description_str(msg, refresh=True)
            # Refresh other visible bars + overall to keep region consistent
            if self.main_tqdm:
                try:
                    self.main_tqdm.refresh()
                except Exception:
                    pass
            for _, bar in active[1:3]:
                try:
                    bar.refresh()
                except Exception:
                    pass
        except Exception:
            # Best effort; ignore overlay failures
            pass

    async def download_files(
        self,
        files: list[dict[str, Any]],
        download_func: Any,
    ) -> list[bool]:
        """
        Download files with TQDM progress display

        Args:
            files: List of file info dictionaries
            download_func: Async function to download a single file

        Returns:
            List of success/failure results
        """
        # Get max_concurrent from config, default to 2
        max_concurrent = 2
        if self.config and hasattr(self.config, "max_concurrent"):
            max_concurrent = getattr(self.config, "max_concurrent", 2)

        return await self.download_files_concurrent(
            files,
            download_func,
            max_concurrent,
        )

    # Interface methods for compatibility - simplified and optimized
    def add_main_task(
        self,
        task_id: str,
        description: str,
        total: int | None = None,
    ) -> None:
        """Add a main task - create main progress bar synchronously"""
        if self.main_tqdm is None:
            # Create progress bar even if total is None or 0, use 0 as default
            self._create_main_progress_bar(total or 0)

    def start_main_task(self, task_id: str) -> None:
        """Start a main task - no-op since bar is created in add_main_task"""
        pass

    def update_main_task(
        self,
        task_id: str,
        advance: int = 0,
        status: str | None = None,
        total: int | None = None,
    ) -> None:
        """Update main task progress - simplified"""
        if self.main_tqdm:
            # Update total if provided and different
            if (
                total is not None
                and hasattr(self.main_tqdm, "total")
                and self.main_tqdm.total != total
            ):
                self.main_tqdm.total = total
                self.stats["total_files"] = total
                self.main_tqdm.refresh()  # Force refresh to show new total

            if advance > 0:
                self.main_tqdm.update(advance)
                # Update stats
                current: float = float(self.stats.get("downloaded", 0.0))
                if isinstance(current, (int, float)):
                    self.stats["downloaded"] = current + advance

            if status:
                # The main bar's description should remain "Total Progress"
                # The file count is handled by the bar_format itself ({n}/{total})
                # No need to update description based on 'status' here.
                pass

    def complete_main_task(
        self,
        task_id: str,
        final_status: str | None = None,
    ) -> None:
        """
        Complete a main task
        """
        if self.main_tqdm and final_status:
            self.main_tqdm.set_description(f"Total Progress: {final_status} ✅")

    def is_termination_requested(self) -> bool:
        """Check if termination was requested"""
        return False  # TQDM doesn't have built-in termination detection

    def refresh_display(self) -> None:
        """Refresh only the reserved render region bars - limit frequency to prevent duplicates."""
        current_time = time.time()
        if (
            current_time - self.last_refresh_time < 0.1
        ):  # Throttle to max 10 refreshes per second
            return
        self.last_refresh_time = current_time  # type: ignore[assignment]

        # TQDM refresh is enough when using fixed positions within the region.
        if self.main_tqdm:
            try:
                self.main_tqdm.refresh()
            except Exception:
                pass

        for task_info in self.download_tqdms.values():
            if isinstance(task_info, dict) and task_info.get("tqdm_bar"):
                try:
                    task_info["tqdm_bar"].refresh()
                except Exception:
                    pass

    def force_display_cleanup(self, clear_above_lines: int | None = None) -> None:
        """
        Full cleanup for Windows/resize:
        - Clear reserved region and a small buffer above it, then refresh bars.
        - Does not wipe full scrollback.
        """
        try:
            # Determine how many lines to clear above the region to remove wrapped logs.
            if clear_above_lines is None:
                clear_above_lines = max(
                    2, self.max_file_bars
                )  # small buffer above region

            # Move cursor to top of reserved region by moving up clear_above_lines
            if clear_above_lines > 0:
                try:
                    from tqdm import tqdm

                    tqdm.write(f"\x1b[{clear_above_lines}F", end="")
                except ImportError:
                    # Skip cursor control if tqdm not available to avoid interfering
                    pass

            # Clear from cursor to end of screen (region + below)
            try:
                from tqdm import tqdm

                tqdm.write("\x1b[J", end="")
            except ImportError:
                # Skip screen clearing if tqdm not available to avoid interfering
                pass

            # Refresh all bars to redraw them into the reserved region
            if self.main_tqdm:
                try:
                    self.main_tqdm.refresh()
                except Exception:
                    pass

            for task_info in self.download_tqdms.values():
                if isinstance(task_info, dict) and task_info.get("tqdm_bar"):
                    try:
                        task_info["tqdm_bar"].refresh()
                    except Exception:
                        pass
        except Exception:
            # Best-effort only
            pass

    def log(self, message: str, level: str = "info") -> None:
        """Log a message using tqdm.write() to prevent alignment issues"""
        # Only show [TQDM] debug messages when explicitly enabled
        if message.startswith("[TQDM]") and level == "debug":
            # Check if TQDM_DEBUG environment variable is set or if we're in DEBUG mode
            import os

            if os.getenv("TQDM_DEBUG", "").lower() not in ("1", "true", "yes"):
                return

        try:
            from tqdm import tqdm

            tqdm.write(message)
        except ImportError:
            pass  # If tqdm not available, silence the log to prevent interference

    def update_stats(self, **kwargs):
        """Update statistics"""
        self.stats.update(kwargs)

    def _get_available_position(self) -> int | None:
        """Get next available position for progress bar (1, 2, 3, etc. - main bar is at position 0)"""
        with self.position_lock:
            # Try to find first available position starting from 1 (main bar is at position 0)
            position = 1
            while position in self.active_positions and position <= self.max_file_bars:
                position += 1

            # If we have space, reserve this position
            if position <= self.max_file_bars:
                self.active_positions.add(position)
                self.log(
                    f"[TQDM] Position {position} ALLOCATED. Active positions: {sorted(self.active_positions)}, max_file_bars: {self.max_file_bars}",
                    "debug",
                )
                return position
            self.log(
                f"[TQDM] No available positions. Active positions: {sorted(self.active_positions)}, max_file_bars: {self.max_file_bars}",
                "debug",
            )
            return None

    def _release_position(self, position: int) -> None:
        """Release position for reuse"""
        with self.position_lock:
            was_active = position in self.active_positions
            self.active_positions.discard(position)
            self.log(
                f"[TQDM] Position {position} RELEASED (was_active: {was_active}). Remaining active positions: {sorted(self.active_positions)}",
                "debug",
            )

    def _force_cleanup_task(self, filename: str) -> None:
        """Force cleanup of any existing task/bar for filename to prevent duplicates"""
        if filename in self.download_tqdms:
            task_info = self.download_tqdms[filename]
            if isinstance(task_info, dict) and task_info.get("tqdm_bar"):
                try:
                    # Release position if it was assigned
                    if "position" in task_info:
                        self._release_position(task_info["position"])
                    # Close the bar without clearing to avoid empty lines
                    bar = task_info["tqdm_bar"]
                    bar.close()
                except Exception:
                    pass  # Ignore cleanup errors
            # Always remove from dict
            del self.download_tqdms[filename]

    def add_download_task(self, filename: str, total_bytes: int) -> str:
        """Add individual download task - store info but don't create bar until first update"""
        # Check if task already exists with same parameters
        if filename in self.download_tqdms:
            existing_info = self.download_tqdms[filename]
            if (
                isinstance(existing_info, dict)
                and existing_info.get("total_bytes") == total_bytes
            ):
                # Same task already exists - check if it's active or completed
                if existing_info.get("tqdm_bar") is not None:
                    # Active bar exists - reuse it
                    logger.debug(f"Reusing existing task for {filename}")
                    return filename
                else:
                    # Task exists but bar is gone (completed/failed) - clean up and create new
                    self.download_tqdms.pop(filename, None)

        # Force cleanup of any existing bar for this filename
        self._force_cleanup_task(filename)

        # Store task info but don't create TQDM bar yet
        self.download_tqdms[filename] = {
            "total_bytes": total_bytes,
            "tqdm_bar": None,
            "created": False,
            "original_filename": filename,  # Keep original for display
        }
        self.log(
            f"[TQDM] Task added for {filename} (Total: {total_bytes} bytes).", "debug"
        )
        return filename

    def start_download_task(self, filename: str) -> None:
        """Start individual download task"""
        pass  # Already started when created

    def _select_icon(self, name: str) -> str:
        if not name:
            return "[DL]" if False else self.DEFAULT_ICON
        dot = name.rfind(".")
        if dot == -1:
            return "[DL]" if False else self.DEFAULT_ICON
        ext = name[dot:].lower()
        icon = self.FILE_ICONS.get(ext, self.DEFAULT_ICON)
        if False:
            return {
                "🎥": "[VID]",
                "🎵": "[AUD]",
                "🖼️": "[IMG]",
                "📦": "[ARC]",
                "📄": "[PDF]",
                "": "[TXT]",
                "📃": "[DOC]",
                "📊": "[XLS]",
                "📈": "[PPT]",
                "📁": "[DL]",
            }.get(icon, "[DL]")
        return icon

    def _truncate_filename(self, filename: str, max_len: int) -> str:
        """Truncate filename for display with better differentiation"""
        if filename is None:
            return "Unknown"

        name_part, ext_part = os.path.splitext(filename)

        # If filename is short enough, pad it to ensure alignment
        if len(filename) <= max_len:
            return filename.ljust(max_len)

        # For longer filenames, include extension and last few characters for differentiation
        if len(ext_part) < max_len:
            # Keep extension and some of the end of the name for differentiation
            available_for_name = max_len - len(ext_part) - 3  # 3 for '...'
            if available_for_name > 5:
                # Include start and end of name for better differentiation
                start_chars = available_for_name // 2
                end_chars = available_for_name - start_chars - 1
                if end_chars > 0:
                    truncated_name = (
                        name_part[:start_chars] + "…" + name_part[-end_chars:]
                    )
                else:
                    truncated_name = name_part[:available_for_name] + "…"
                return (truncated_name + ext_part).ljust(max_len)

        # Fallback: simple truncation
        return (name_part[: max_len - 3] + "..." + ext_part).ljust(max_len)

    def update_download_task(self, filename: str, advance: int) -> None:
        """Update individual download task - create bar on first update (thread-safe)"""
        # Check terminal health on each update (Windows fallback)
        self._check_terminal_health()

        if filename not in self.download_tqdms:
            return

        task_info = self.download_tqdms[filename]

        # If bar already exists, just update it (no lock needed for updates)
        existing_bar = task_info.get("tqdm_bar")
        if existing_bar is not None:
            if advance > 0:
                try:
                    existing_bar.update(advance)
                    # Calculate and set custom ETA
                    self._update_download_eta(existing_bar, task_info)
                except Exception:
                    # If update fails, remove the broken bar
                    try:
                        existing_bar.close()
                    except Exception:
                        pass
                    with self._bar_creation_lock:
                        task_info["tqdm_bar"] = None
            return

        # Create TQDM bar on first meaningful progress update (thread-safe) - BACK TO 3 BAR APPROACH
        if advance > 0:
            with self._bar_creation_lock:
                # Double-check after acquiring lock
                if task_info.get("tqdm_bar") is not None:
                    # Another thread created the bar, use it
                    try:
                        task_info["tqdm_bar"].update(advance)
                    except Exception:
                        pass
                    return

                # Count only currently active bars
                active_count = sum(
                    1
                    for info in self.download_tqdms.values()
                    if isinstance(info, dict) and info.get("tqdm_bar") is not None
                )

                # Only create if we have space (limit concurrent bars to max_file_bars)
                if active_count < self.max_file_bars:
                    # Get a unique available position using proper position management
                    position = self._get_available_position()
                    if position is None:
                        # No available positions, don't create bar
                        return

                    # Use original filename for display
                    original_filename = task_info.get("original_filename", filename)
                    icon = self._select_icon(original_filename) if True else ""

                    # Truncate filename to fit display nicely with better differentiation
                    # Account for icon (2 chars) + space (1 char) = 3 chars total overhead
                    max_display_len = 30  # 33 total desc width - 3 chars for icon and space = 30 for filename
                    display_name = self._truncate_filename(
                        original_filename, max_display_len
                    )

                    try:
                        # Create individual file progress bar - CRITICAL FIX: Use file=sys.stdout to avoid positioning conflicts
                        import sys

                        new_bar = tqdm_class(
                            total=task_info["total_bytes"],
                            unit="B",
                            unit_scale=True,
                            unit_divisor=1024,
                            desc=f"{icon} {display_name}",
                            leave=False,  # Don't keep bars visible - cleaner display
                            ncols=100,  # Consistent width with main bar
                            position=position,  # Use calculated position
                            file=sys.stdout,  # CRITICAL: Force output to stdout to avoid conflicts
                            mininterval=0.2,  # Less frequent updates for cleaner display
                            maxinterval=1.0,  # Longer max interval to reduce flicker
                            dynamic_ncols=False,
                            ascii=False,
                            bar_format="{desc:<33} [{bar:25}] {percentage:3.0f}% {n_fmt:>7} / {total_fmt:<7} {rate_fmt:>11} {postfix}",
                            colour="cyan",  # Start with cyan color
                        )

                        # Store position and assign the bar
                        task_info["position"] = position
                        task_info["tqdm_bar"] = new_bar
                        # Update with initial progress
                        if advance > 0:
                            new_bar.update(advance)
                            # Calculate and set custom ETA
                            self._update_download_eta(new_bar, task_info)
                            # Check if already completed and update color
                            if advance >= task_info["total_bytes"]:
                                new_bar.colour = "green"
                                new_bar.refresh()
                        self.log(
                            f"[TQDM] Individual bar CREATED for {filename} at POSITION {position}. Total active bars: {len([info for info in self.download_tqdms.values() if isinstance(info, dict) and info.get('tqdm_bar')])}",
                            "debug",
                        )
                    except Exception:
                        # If bar creation fails, don't store broken bar
                        pass

    def set_channel_name(self, channel_name: str) -> None:
        """Set the channel name for display in the main progress bar"""
        self.channel_name = channel_name
        # Update existing main progress bar if it exists
        if self.main_tqdm:
            channel_display = self.channel_name or "Channel"
            self.main_tqdm.set_description(
                f"📊 {channel_display} Progress", refresh=True
            )

    def complete_download_task(self, filename: str) -> None:
        """Complete individual download task - update main bar and cleanup"""
        if filename in self.download_tqdms:
            task_info = self.download_tqdms[filename]

            # Simply close the progress bar - no need for color changes that create visual noise
            if task_info.get("tqdm_bar"):
                try:
                    bar = task_info["tqdm_bar"]
                    # Complete the bar to 100% before closing
                    remaining = bar.total - bar.n if bar.total else 0
                    if remaining > 0:
                        bar.update(remaining)
                    # Release position if it was assigned
                    if "position" in task_info:
                        pos = task_info["position"]
                        self.log(
                            f"[TQDM] About to RELEASE position {pos} for completed task {filename}",
                            "debug",
                        )
                        self._release_position(pos)
                    # Close immediately - no color changes or extra refreshes
                    bar.close()
                except Exception:
                    pass

            # Simply update main progress bar count - no temporary status changes
            if self.main_tqdm:
                self.main_tqdm.update(1)

            # Remove from tracking dict
            self.download_tqdms.pop(filename, None)
            self.log(
                f"[TQDM] Task COMPLETED for {filename}. Remaining tasks: {len(self.download_tqdms)}",
                "debug",
            )

    def error_download_task(self, filename: str, error_msg: str) -> None:
        """Handle error in individual download task - update main bar with error status"""
        if filename in self.download_tqdms:
            task_info = self.download_tqdms[filename]

            # Update the progress bar to show error with faded color
            if task_info.get("tqdm_bar"):
                try:
                    # Change color to grey/white for error bar (faded appearance)
                    bar = task_info["tqdm_bar"]
                    bar.colour = (
                        "white"  # This appears lighter/greyed on most terminals
                    )
                    bar.refresh()
                except Exception:
                    pass

            # Log the error message using tqdm.write to prevent interleaving
            self.log(f"❌ Error downloading {filename}: {error_msg}", level="error")

            # Close and cleanup the progress bar
            if task_info.get("tqdm_bar"):
                try:
                    # Release position if it was assigned
                    if "position" in task_info:
                        pos = task_info["position"]
                        self.log(
                            f"[TQDM] About to RELEASE position {pos} for errored task {filename}",
                            "debug",
                        )
                        self._release_position(pos)
                    task_info["tqdm_bar"].close()
                except Exception:
                    pass

            # Simply update error count - no temporary status changes

            # Remove from tracking dict
            self.download_tqdms.pop(filename, None)
            self.log(
                f"[TQDM] Task FAILED for {filename} with error: {error_msg}. Remaining tasks: {len(self.download_tqdms)}",
                "debug",
            )

    # Terminal Resilience Methods
    def _get_terminal_size(self) -> tuple:
        """Get current terminal size safely."""
        try:
            return os.get_terminal_size()
        except (OSError, AttributeError):
            return (80, 24)  # Default fallback

    def _setup_terminal_resilience(self):
        """Set up terminal resize handling for display resilience."""
        try:
            # Register signal handler for terminal resize (Unix/Linux/Mac)
            if hasattr(signal, "SIGWINCH"):
                signal.signal(signal.SIGWINCH, self._handle_terminal_resize)
        except (AttributeError, OSError):
            # Windows or signal handling not available - use periodic checking
            pass

    def _handle_terminal_resize(self, signum=None, frame=None):
        """Handle terminal resize event."""
        try:
            # Skip terminal handling if shutdown is requested
            if self._shutdown_requested:
                return

            current_size = self._get_terminal_size()
            if current_size != self._last_terminal_size:
                self._last_terminal_size = current_size
                self._terminal_corrupted = True
                # Schedule a refresh on next update (only if not shutting down)
                if not self._shutdown_requested:
                    threading.Thread(target=self._recover_display, daemon=True).start()
        except Exception as e:
            logger.debug(f"Error handling terminal resize: {e}")

    def _recover_display(self):
        """Recover from terminal corruption/resize."""
        try:
            # Exit immediately if shutdown is requested
            if self._shutdown_requested:
                return

            time.sleep(0.1)  # Brief delay to let terminal settle

            # Double-check shutdown flag after sleep
            if self._shutdown_requested:
                return

            with self.position_lock:
                # Clear terminal screen below current cursor position
                if sys.stdout.isatty():
                    # Send escape sequences to clear and reset
                    sys.stdout.write("\033[J")  # Clear screen from cursor down
                    sys.stdout.write("\033[H")  # Move cursor to home position
                    sys.stdout.flush()

                # Force refresh all active progress bars with position reset
                if self.main_tqdm and hasattr(self.main_tqdm, "refresh"):
                    try:
                        # Reset main progress bar position
                        if hasattr(self.main_tqdm, "pos"):
                            self.main_tqdm.pos = 0
                        self.main_tqdm.refresh()
                    except Exception as e:
                        logger.debug(f"Error refreshing main tqdm: {e}")

                # Refresh all download progress bars with position management
                for filename, task_info in self.download_tqdms.items():
                    bar = task_info.get("tqdm_bar")
                    if bar and hasattr(bar, "refresh"):
                        try:
                            # Ensure position is still valid
                            position = task_info.get("position")
                            if position is not None and hasattr(bar, "pos"):
                                bar.pos = position
                            bar.refresh()
                        except Exception as e:
                            logger.debug(
                                f"Error refreshing download bar {filename}: {e}"
                            )

                self._terminal_corrupted = False
                logger.debug("Terminal display recovered after resize/corruption")

        except Exception as e:
            logger.debug(f"Error recovering display: {e}")

    def _check_terminal_health(self):
        """Periodically check for terminal size changes (Windows fallback)."""
        try:
            # Only check every 10th update to reduce overhead
            self._terminal_check_counter += 1
            if self._terminal_check_counter % 10 != 0:
                return

            current_size = self._get_terminal_size()
            if current_size != self._last_terminal_size:
                self._last_terminal_size = current_size
                if not self._terminal_corrupted:
                    self._terminal_corrupted = True
                    self._recover_display()
        except Exception:
            pass

    def _update_download_eta(self, tqdm_bar, task_info):
        """Calculate and set custom ETA for download progress bar."""
        try:
            if not hasattr(tqdm_bar, "total") or not tqdm_bar.total:
                return

            # Get current progress
            current = tqdm_bar.n
            total = tqdm_bar.total

            # Calculate remaining bytes
            remaining_bytes = total - current
            if remaining_bytes <= 0:
                tqdm_bar.set_postfix_str("00:00")
                return

            # Get current rate from tqdm (bytes per second)
            rate = getattr(tqdm_bar, "rate", None)
            if not rate or rate <= 0:
                tqdm_bar.set_postfix_str("?:??")
                return

            # Calculate ETA in seconds
            eta_seconds = remaining_bytes / rate

            # Format ETA nicely
            eta_formatted = self._fmt_hhmm(eta_seconds)
            tqdm_bar.set_postfix_str(eta_formatted)

        except Exception as e:
            logger.debug(f"Error calculating ETA: {e}")

    def _show_enhanced_header(self):
        """Show enhanced header information for UI B mode"""
        try:
            from tqdm import tqdm

            # Create header box
            header_lines = [
                "┌────────────────────────────────────────────────────────────────────┐",
                f"│ 🎯 dnld_telegram Enhanced Mode    📁 {self.channel_name or 'Loading...'}      │",
                f"│ 🕒 {time.strftime('%H:%M:%S')}                        🚀 Enhanced UI Mode B    │",
                "├────────────────────────────────────────────────────────────────────┤",
                "│ Statistics will be shown here during download                      │",
                "└────────────────────────────────────────────────────────────────────┘",
            ]

            for line in header_lines:
                tqdm.write(line)
            tqdm.write("")  # Add spacing

        except ImportError:
            pass

    def _show_enhanced_statistics(self):
        """Show enhanced statistics during downloads for UI B mode"""
        if not self.enhanced_mode:
            return

        try:
            from tqdm import tqdm

            # Calculate statistics
            elapsed = time.time() - (self.start_time or time.time())
            completed = self.stats.get("downloaded", 0)
            self.stats.get("failed", 0)
            total = self.stats.get("total_files", 0)

            completion_rate = (completed / total * 100) if total > 0 else 0
            files_per_second = (completed / elapsed) if elapsed > 0 else 0

            # Create statistics display
            stats_text = f"📊 Progress: {completed}/{total} files ({completion_rate:.1f}%) | 🚀 Speed: {files_per_second:.1f} files/s | ⏱️ {elapsed:.0f}s"

            # Use tqdm.write for clean output
            tqdm.write(f"\r{stats_text}", end="")

        except ImportError:
            pass
