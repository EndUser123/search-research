"""
Rich Layout downloader for Windows Terminal optimized display.

Provides a fixed footer layout to prevent duplicate progress bar lines
in Windows Terminal + PowerShell 7.
"""

import contextlib
import logging
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel

from .logging_utils import LogStream


class RichLayoutDownloader:
    """
    Handles Rich Layout-based download display with fixed footer.

    This prevents duplicate progress bar lines in Windows Terminal + PowerShell 7
    by using a fixed footer layout instead of traditional progress bars.
    """

    def __init__(
        self,
        console: Console,
        batch_downloader,  # The BatchDownloader instance
        cookies_from_browser: str | None = None,
        max_videos: int | None = None,
    ):
        """
        Initialize the Rich Layout downloader.

        Args:
            console: Rich console instance
            batch_downloader: The parent BatchDownloader instance
            cookies_from_browser: Browser to extract cookies from
            max_videos: Maximum videos per channel
        """
        self.console = console
        self.batch_downloader = batch_downloader
        self.cookies_from_browser = cookies_from_browser
        self.max_videos = max_videos

    def _read_available_channels_pool(self, processed_channels):
        """Read channels.txt to get available channels for dynamic expansion.

        Args:
            processed_channels: Set of channels already processed

        Returns:
            Set of available channel names not yet processed
        """

        channels_file = (
            Path(__file__).parent.parent.parent.parent / "data" / "channels.txt"
        )
        all_available_channels = set()
        if channels_file.exists():
            try:
                with open(channels_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            all_available_channels.add(line)
            except FileNotFoundError:
                pass
            except PermissionError:
                pass
            except OSError:
                pass
            except Exception:
                pass
        else:
            pass

        return all_available_channels - processed_channels

    def download_with_layout(
        self,
        channel_downloads: list,
        invalid_channels: list | None = None,
    ) -> dict:
        """
        Download channels using Rich Layout with fixed footer (Windows 11 optimized).

        Args:
            channel_downloads: List of (original_channel, resolved_url, channel_id) tuples
            invalid_channels: List of channels that were filtered out (404s)

        Returns:
            dict: Results with success/failure status for each channel
        """
        results = {
            "successful": [],
            "failed": [],
            "skipped": [],
            "invalid_channels": invalid_channels or [],
        }

        # Suppress INFO logging during Rich mode to prevent console output from breaking display
        logging.getLogger().setLevel(logging.WARNING)

        # Create layout structure with dynamic sizing
        terminal_height = self.console.height
        header_size = 3
        footer_size = 12  # Reduced to prevent cramping
        padding = 2  # Space for borders and margins
        main_size = max(10, terminal_height - header_size - footer_size - padding)

        layout = Layout()
        layout.split(
            Layout(name="header", size=header_size),
            Layout(name="main", size=main_size),
            Layout(name="footer", size=footer_size),
        )

        # Split main section into queue (top) and logs (bottom)
        layout["main"].split(
            Layout(name="queue_panel", size=8),
            Layout(name="log_panel"),
        )

        header_state = {"status": "[dim]Waiting for channels...[/dim]"}

        def update_header(status_line: str | None = None) -> None:
            """Update header with optional status line."""
            if status_line is not None:
                header_state["status"] = status_line
            header_text = (
                f"[bold cyan]🔍 CHANNEL PROCESSING[/bold cyan]\n"
                f"[dim]Processing {len(channel_downloads)} channels[/dim]\n"
                f"{header_state['status']}"
            )
            layout["header"].update(Panel(header_text, border_style="cyan"))

        update_header()

        # Simple static footer (no dynamic progress to prevent flashing)
        layout["footer"].update(
            Panel(
                f"[dim]Processing {len(channel_downloads)} channels[/dim]",
                title="Status",
                border_style="green",
            )
        )

        # Create main panel before Live starts
        layout["main"]["queue_panel"].update(
            Panel("Initializing...", title="Queue", border_style="blue")
        )
        layout["main"]["log_panel"].update(
            Panel("Waiting for logs...", title="Log Output", border_style="blue")
        )

        # Show loading message before Live takes over the screen
        self.console.print("[blue]Initializing Rich interface...[/blue]")

        # Use Live to render the layout with manual refresh
        with contextlib.ExitStack() as stack:
            live = stack.enter_context(
                Live(
                    layout,
                    console=self.console,
                    screen=True,
                    auto_refresh=False,
                    vertical_overflow="crop",
                )
            )

            # Queue-based real-time log updates
            log_queue = queue.Queue()
            displayed_logs = []

            # Redirect stdout and stderr to our log panel
            log_stream = LogStream(log_queue)
            stack.enter_context(contextlib.redirect_stdout(log_stream))
            stack.enter_context(contextlib.redirect_stderr(log_stream))

            # Force immediate render to eliminate "dots" flash
            live.refresh()

            # Thread-safe logging infrastructure
            log_messages = []
            log_lock = threading.Lock()

            def log_callback(message: str) -> None:
                """Thread-safe callback for logging video status updates."""
                with log_lock:
                    log_messages.append(message)

            # Wrap callback to also add to queue for real-time display
            original_log_callback = log_callback

            def log_callback_with_queue(message: str) -> None:
                """Callback that sends messages to both original callback and log queue."""
                original_log_callback(message)
                log_queue.put(message)

            log_callback = log_callback_with_queue

            def update_log_panel() -> None:
                """Drain log queue and refresh the log panel immediately."""
                with log_lock:
                    try:
                        while not log_queue.empty():
                            msg = log_queue.get_nowait()
                            displayed_logs.append(msg)
                            if len(displayed_logs) > 50:
                                displayed_logs.pop(0)
                    except (queue.Empty, IndexError):
                        pass

                    recent_logs = (
                        displayed_logs[-10:]
                        if len(displayed_logs) > 10
                        else displayed_logs
                    )
                video_logs = (
                    "\n".join(recent_logs) if recent_logs else "Waiting for logs..."
                )
                layout["main"]["log_panel"].update(
                    Panel(video_logs, title="Log Output", border_style="blue")
                )

            def update_queue_panel(
                processing_list: list[str] | None = None,
                pool_remaining: int | None = None,
                current_status: str | None = None,
            ) -> None:
                """Update the queue panel with pending items and optional status."""
                processing_header = "[bold]Processing:[/bold]"
                if current_status:
                    processing_header += f"\n{current_status}"
                if processing_list:
                    processing_header += "\n" + "\n".join(processing_list)
                elif pool_remaining is not None:
                    if pool_remaining > 0:
                        processing_header += f"\n[dim]{pool_remaining} in pool[/dim]"
                    else:
                        processing_header += "\n[dim]No more channels[/dim]"
                layout["main"]["queue_panel"].update(
                    Panel(processing_header, title="Queue", border_style="blue")
                )

            # Manual executor lifecycle for proper KeyboardInterrupt handling
            executor = ThreadPoolExecutor(max_workers=1)

            try:
                # Track which channels have been attempted
                processed_channels = {item[0] for item in channel_downloads}

                # Read available channels from channels.txt for dynamic expansion
                all_available_channels = self._read_available_channels_pool(processed_channels)
                remaining_channels = all_available_channels - processed_channels

                log_callback(
                    f"[dim]Found {len(all_available_channels)} total channels in pool, {len(remaining_channels)} available for expansion[/dim]"
                )

                # Dynamic channel processing
                channels_to_check = list(channel_downloads)
                channels_with_videos_found = 0
                channels_needed = len(channel_downloads)
                channels_checked = 0

                while channels_to_check:
                    # Get next channel to process
                    if channels_to_check:
                        try:
                            item = channels_to_check.pop(0)
                        except IndexError:
                            continue
                        original_channel, resolved_url, channel_id = item[:3]
                    elif remaining_channels:
                        next_channel = remaining_channels.pop()
                        processed_channels.add(next_channel)

                        try:
                            from .fast_channel_resolver import create_fast_resolver

                            fast_resolver = create_fast_resolver(
                                cookies_from_browser=self.cookies_from_browser,
                                console=self.console,
                            )
                            single_resolved = fast_resolver.batch_resolve(
                                [next_channel], max_workers=1
                            )
                            if next_channel in single_resolved:
                                resolved_url = single_resolved[next_channel]
                                original_channel = next_channel
                                if "/channel/" in resolved_url:
                                    channel_id = resolved_url.split("/channel/")[
                                        1
                                    ].split("/")[0]
                                else:
                                    channel_id = None
                            else:
                                log_callback(
                                    f"[yellow]Failed to resolve: {next_channel}[/yellow]"
                                )
                                continue
                        except Exception as e:
                            log_callback(
                                f"[red]Error resolving {next_channel}: {str(e)[:50]}[/red]"
                            )
                            continue
                    else:
                        break

                    # Create display name
                    if "@" in resolved_url:
                        handle = resolved_url.split("@")[-1].split("/")[0]
                        display_name = f"@{handle}"
                    elif channel_id and len(channel_id) > 15:
                        display_name = channel_id[:20] + "..."
                    elif channel_id:
                        display_name = f"channel/{channel_id}"
                    else:
                        display_name = resolved_url[:40] + "..."

                    # RSS pre-check to determine if download is needed
                    should_download = True
                    rss_video_ids = None

                    # Show which channel is being processed
                    projected_count = channels_with_videos_found + 1
                    checking_msg = f"[dim][{projected_count}/{channels_needed}][/dim] [cyan]🔍 {display_name}[/cyan] [dim](checking...)[/dim]"

                    log_callback(checking_msg)
                    update_header(checking_msg)
                    update_queue_panel(
                        pool_remaining=len(remaining_channels),
                        current_status=checking_msg,
                    )

                    # Try writing to Windows console directly (strip Rich markup for raw console)
                    try:
                        import ctypes
                        import re

                        STD_ERROR_HANDLE_ID = -12
                        kernel32 = ctypes.windll.kernel32
                        h_std = kernel32.GetStdHandle(STD_ERROR_HANDLE_ID)
                        if h_std and h_std != -1:
                            # Strip Rich markup tags like [dim], [/dim], [cyan], etc.
                            plain_msg = re.sub(r"\[[^\]]+\]", "", checking_msg)
                            msg_bytes = plain_msg + "\n"
                            kernel32.WriteConsoleW(
                                h_std, msg_bytes, len(msg_bytes), None, None
                            )
                    except Exception:
                        pass

                    update_log_panel()
                    live.refresh()

                    if channel_id:
                        from yt_fts.core.database import get_vid_ids_by_channel_id
                        from yt_fts.services.rss_precheck import create_rss_checker

                        try:
                            local_vid_ids = [
                                v[0] for v in get_vid_ids_by_channel_id(channel_id)
                            ]
                            db_video_ids = set(local_vid_ids)
                        except Exception:
                            db_video_ids = set()

                        # Run RSS pre-check
                        rss_checker = create_rss_checker(timeout=10.0)
                        handle = handle if "@" in resolved_url else None
                        rss_result = rss_checker.check(
                            channel_id=channel_id,
                            handle=handle,
                            resolved_url=resolved_url,
                            db_video_ids=db_video_ids,
                        )

                        if rss_result.status == "skip":
                            channels_checked += 1
                            results["skipped"].append(
                                {
                                    "channel": original_channel,
                                    "message": f"All {len(rss_result.video_ids)} videos already in database (RSS check)",
                                }
                            )
                            log_callback(
                                f"[dim][{channels_with_videos_found}/{channels_needed}][/dim] [yellow]⏭ {display_name}[/yellow] [dim]({len(rss_result.video_ids)} total, 0 new via RSS)[/dim]"
                            )
                            should_download = False
                        elif rss_result.status == "new_videos":
                            projected_count = channels_with_videos_found + 1
                            rss_video_ids = rss_result.video_ids[:]
                            if self.max_videos and len(rss_video_ids) > self.max_videos:
                                rss_video_ids = rss_video_ids[: self.max_videos]
                            limit_suffix = ""
                            if self.max_videos:
                                limit_suffix = f" [dim](downloading {len(rss_video_ids)} of {len(rss_result.video_ids)} new)[/dim]"
                            status_msg = f"[dim][{projected_count}/{channels_needed}][/dim] [cyan]📺 {display_name}[/cyan][dim]{limit_suffix}[/dim]"
                            log_callback(status_msg)
                            update_header(status_msg)
                            update_log_panel()
                            live.refresh()
                            should_download = True
                        elif rss_result.status == "gap_detected":
                            projected_count = channels_with_videos_found + 1
                            missing = [
                                vid
                                for vid in rss_result.video_ids
                                if vid not in db_video_ids
                            ]
                            missing_count = len(missing)
                            limit_suffix = (
                                f" [dim]({missing_count} RSS videos missing)[/dim]"
                            )
                            status_msg = f"[dim][{projected_count}/{channels_needed}][/dim] [yellow]🔍 {display_name}[/yellow][dim]{limit_suffix}[/dim]"
                            log_callback(status_msg)
                            update_header(status_msg)
                            update_log_panel()
                            live.refresh()
                            should_download = True
                        else:
                            projected_count = channels_with_videos_found + 1
                            status_msg = f"[dim][{projected_count}/{channels_needed}][/dim] [cyan]📺 {display_name}[/cyan] [dim](checking...)[/dim]"
                            log_callback(status_msg)
                            update_header(status_msg)
                            update_log_panel()
                            live.refresh()
                            should_download = True

                    if not should_download:
                        update_log_panel()
                        live.refresh()
                        continue

                    # Submit download task
                    future = executor.submit(
                        self.batch_downloader._download_single_channel_optimized,
                        original_channel,
                        resolved_url,
                        channel_id,
                        None,
                        log_callback,
                        True,
                        rss_video_ids,
                    )

                    # Wait for result
                    try:
                        result = future.result()
                        channels_checked += 1

                        if result["success"]:
                            videos_count = result.get("videos_count", 0)
                            if videos_count > 0:
                                channels_with_videos_found += 1
                                results["successful"].append(
                                    {
                                        "channel": original_channel,
                                        "videos_count": videos_count,
                                        "message": result.get("message", "Success"),
                                    }
                                )
                                log_callback(
                                    f"[green]✓ {display_name}[/green] [dim]- {videos_count} videos[/dim]"
                                )
                            else:
                                results["skipped"].append(
                                    {
                                        "channel": original_channel,
                                        "message": "No new videos",
                                    }
                                )
                                log_callback(
                                    f"[dim][{channels_with_videos_found}/{channels_needed}][/dim] [yellow]⏭ {display_name}[/yellow] [dim]- No new videos[/dim]"
                                )
                        else:
                            results["failed"].append(
                                {
                                    "channel": original_channel,
                                    "error": result.get("error", "Unknown error"),
                                }
                            )
                            log_callback(
                                f"[dim][{channels_checked}/?][/dim] [red]✗ Failed {display_name}[/red]"
                            )
                    except Exception as exc:
                        channels_checked += 1
                        results["failed"].append(
                            {"channel": original_channel, "error": str(exc)}
                        )
                        log_callback(
                            f"[dim][{channels_checked}/?][/dim] [red]✗ Failed {display_name}: {exc}[/red]"
                        )

                    # Update panels
                    update_log_panel()

                    # Build processing list
                    processing_list = []
                    if channels_to_check:
                        for item in list(channels_to_check)[:5]:
                            ch = item[0] if isinstance(item, tuple) else item
                            if "@" in ch:
                                handle = ch.split("@")[-1]
                                processing_list.append(
                                    f"  [dim]pending @{handle}[/dim]"
                                )
                            else:
                                processing_list.append(
                                    f"  [dim]pending {ch[:30]}[/dim]"
                                )

                    update_queue_panel(
                        processing_list=processing_list,
                        pool_remaining=len(remaining_channels),
                        current_status=header_state["status"],
                    )

                    update_log_panel()
                    live.refresh()
                    time.sleep(0.1)

            except KeyboardInterrupt:
                executor.shutdown(wait=False, cancel_futures=True)
                raise
            finally:
                if not executor._shutdown:
                    executor.shutdown(wait=True)

        # Restore logging level after Rich display
        logging.getLogger().setLevel(logging.INFO)

        # Print final summary
        self.console.print()
        self.console.print("[bold cyan]─[/bold cyan]".ljust(60, "─"))
        self.console.print()
        from .summary import print_summary
        print_summary(self.console, results, self.batch_downloader.channels, self.batch_downloader.continue_on_error)

        # Log batch completion
        from yt_fts.utils.dual_sink_logger import log_operation, log_user_message
        successful_count = len(results["successful"])
        failed_count = len(results["failed"])
        total_videos = sum(r.get("videos_count", 0) for r in results["successful"])

        log_user_message(20, f"✅ Batch download complete: {successful_count} successful, {failed_count} failed")
        log_operation("batch_complete", "Batch download finished",
                      successful=successful_count,
                      failed=failed_count,
                      total_videos=total_videos,
                      level=20)

        return results
