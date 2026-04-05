"""
Default display plugin - clean visual hierarchy with bullet points.

Implements dual-sink pattern:
- Primary: Rich console with formatting
- Fallback: Plain text output for Windows encoding issues

Visual style:
  ● @Channel [progress]
    ⎿ detail line 1
    ⎿ detail line 2
"""

import sys
from typing import Any

from rich.console import Console

from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

from .base import DisplayPlugin


class DefaultDisplayPlugin(DisplayPlugin):
    """
    Default display plugin with clean visual hierarchy.

    Uses bullet points (●) for main items and continuation markers (⎿)
    for related details, creating clear visual flow without boxes.
    """

    name = "default"
    description = "Clean visual hierarchy with bullet points and continuation markers"
    category = "core"

    def __init__(self, console: Console):
        """
        Initialize the default display plugin.

        Args:
            console: Rich console instance for output
        """
        super().__init__(console)
        # Fallback console for Windows encoding errors
        self._fallback_console = Console(force_terminal=False, legacy_windows=True)

    def _safe_print(self, text: str) -> None:
        """
        Dual-sink print: try Rich console, fall back to plain text on OSError.

        Windows terminals can raise OSError: [Errno 22] Invalid argument
        when printing certain Unicode characters or Rich markup.
        """
        try:
            self.console.print(text)
        except OSError:
            # Strip Rich markup and print plain text
            plain_text = text.replace("[dim]", "").replace("[/dim]", "")
            plain_text = plain_text.replace("[red]", "").replace("[/red]", "")
            plain_text = plain_text.replace("[bold]", "").replace("[/bold]", "")
            plain_text = plain_text.replace("[cyan]", "").replace("[/cyan]", "")
            plain_text = plain_text.replace("[yellow]", "").replace("[/yellow]", "")
            plain_text = plain_text.replace("[/]", "")  # Catch-all for closing tags
            try:
                self._fallback_console.print(plain_text)
            except Exception:
                # Ultimate fallback: raw stdout
                sys.stdout.write(plain_text + "\n")
                sys.stdout.flush()

    def display_channel_header(self, channel_info: dict[str, Any]) -> None:
        """Display channel processing header - bullet point style."""
        index = channel_info["index"]
        total = channel_info["total"]
        name = channel_info["name"]
        db_stats = channel_info.get("db_stats", "0 videos")
        inconsistent = channel_info.get("inconsistent", False)
        inconsistency_reason = channel_info.get("inconsistency_reason", "")

        # Format channel name for clean display
        display_name = self._format_channel_name(name)

        # Make channel name clickable if URL is available
        channel_url = channel_info.get("channel_url")
        if channel_url:
            clickable_name = f"[link={channel_url}]{display_name}[/link]"
        else:
            clickable_name = display_name

        # Bullet point header with progress counter and index
        progress = f"{index}/{total}" if total else str(index)
        self._safe_print(f"{index}. ● {clickable_name} [dim][{progress}][/dim]")
        # Stats as continuation line
        self._safe_print(f"   ⎿ [dim]db: {db_stats}[/dim]")

        # Display inconsistency warning if present
        if inconsistent:
            # Format inconsistency details cleanly
            details = channel_info.get("db_stats_details", {})
            parts = []
            parts.append(f"{details.get('total', 0)} total")

            video_parts = []
            video_parts.append(f"{details.get('with_subs', 0)} with transcripts")
            video_parts.append(f"{details.get('no_subs', 0)} no subs")
            video_parts.append(f"{details.get('scheduled', 0)} sch")
            video_parts.append(f"{details.get('members', 0)} mem")

            parts.append(", ".join(video_parts))
            stats_str = " | ".join(parts)

            if details.get("shorts", 0) > 0:
                stats_str += f" | {details.get('shorts', 0)} shorts"

            self._safe_print(
                f"   ⎿ [yellow]! WARNING: Inconsistent DB stats: {stats_str}[/yellow]"
            )

            if inconsistency_reason:
                self._safe_print(f"   ⎿ [dim]reason:[/dim] {inconsistency_reason}")

    def _format_channel_name(self, name: str) -> str:
        """
        Format channel name for clean display.

        Priority:
        1. Actual channel names (human-readable) - use as-is
        2. @handle format - use as-is
        3. Extract @handle from URL
        4. Format channel IDs as channel/ID...
        5. Truncate long strings at 30 chars
        """
        if not name:
            return "Unknown"

        # Actual channel name (human-readable, not a URL pattern)
        # Check: doesn't look like a URL or channel ID
        if (
            not name.startswith("http")
            and not name.startswith("@")
            and not name.startswith("UC")
        ):
            return name

        # Already formatted (starts with @)
        if name.startswith("@"):
            return name

        # Extract @handle from URL
        if "youtube.com/@" in name:
            handle_part = name.split("youtube.com/@")[-1].split("/")[0]
            return f"@{handle_part}"

        # Extract channel ID and format as channel/ID...
        if "/channel/" in name:
            channel_id = name.split("/channel/")[-1].split("/")[0]
            if len(channel_id) > 20:
                return f"channel/{channel_id[:18]}..."
            return f"channel/{channel_id}"

        # Direct channel ID - truncate but keep raw format (no channel/ prefix)
        if name.startswith("UC") and len(name) >= 20:
            return f"{name[:20]}..."

        # Truncate long strings
        if len(name) > 30:
            return name[:27] + "..."

        return name

    def display_rss_status(self, rss_info: dict[str, Any] | Any) -> None:
        """Display RSS status - continuation line."""
        # Handle both dict-style (legacy) and RssCheckResult dataclass
        if hasattr(rss_info, "get"):
            status = rss_info.get("status", "")
            message = rss_info.get("message", "")
        else:
            status = getattr(rss_info, "status", "")
            message = getattr(rss_info, "message", "")

        if status == "skip":
            self._safe_print("   ⎿ [dim]rss:[/dim]   No new videos")
            return

        self._safe_print(f"   ⎿ [dim]rss:[/dim] {message}")

    def display_download_result(self, result_info: dict[str, Any]) -> None:
        """Display download result - continuation line with metrics."""
        success = result_info["success"]
        target_reached = result_info.get("target_reached", False)
        message = result_info.get("message") or ""

        def _clean_message(raw: str) -> str:
            cleaned = " ".join(str(raw).split())
            while cleaned and cleaned[0] in {"û", "✓", "⏭", "?", "●"}:
                cleaned = cleaned[1:].lstrip()
            return cleaned

        if success:
            videos_count = result_info.get("videos_count", 0)
            videos_without_subtitles = result_info.get("videos_without_subtitles", 0)
            result_info.get("total_videos", videos_count)
            time_taken = result_info.get("time_taken", "")
            quota_used = result_info.get("quota_used", 0)
            clean_message = _clean_message(message)

            # Show target reached message if applicable
            if target_reached and videos_count > 0:
                self._safe_print(
                    f"   ⎿ [cyan]✓[/cyan] Reached target of {videos_count} videos saved, stopping..."
                )

            # Build result line with metrics
            if clean_message and videos_count == 0:
                icon = "⏭"
                lowered = clean_message.lower()
                if "backfill" in lowered:
                    icon = "✓"
                if "no new videos" in lowered and "rss" in lowered:
                    clean_message = "all videos already in database"
                    icon = "⏭"
                icon_prefix = f"{icon} " if icon else ""
                self._safe_print(f"   ⎿ [dim]net:[/dim] {icon_prefix}{clean_message}")
            else:
                # Main result: videos saved
                parts = []
                if videos_without_subtitles > 0:
                    parts.append(
                        f"{videos_count} new ({videos_without_subtitles} no subs)"
                    )
                else:
                    parts.append(f"{videos_count} new")

                # Add time taken
                if time_taken:
                    parts.append(f"took {time_taken}")

                # Add quota used
                if quota_used > 0:
                    quota_info = YouTubeAPIBackfill.get_global_quota_info()
                    remaining = quota_info["remaining"]
                    parts.append(f"+{quota_used} quota ({remaining:,} left)")

                self._safe_print(f"   ⎿ [dim]net:[/dim] ✓ {' | '.join(parts)}")
        else:
            error = result_info.get("error", "Unknown error")
            # Clean up error message: remove newlines and extra whitespace
            error = " ".join(str(error).split())

            # Classify error for emoji (simplified version)
            if "rate limit" in error.lower() or "429" in error:
                emoji = "⚠️"
            elif "not found" in error.lower() or "404" in error:
                emoji = "❌"
            elif "timeout" in error.lower():
                emoji = "⏱️"
            elif "network" in error.lower():
                emoji = "🌐"
            else:
                emoji = "❌"

            # For long errors, truncate to keep output clean
            if len(error) > 80:
                error = error[:77] + "..."

            self._safe_print(f"   ⎿ [dim]net:[/dim] {emoji} {error}")

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """Display batch summary - matches current format."""
        successful = summary_info["successful"]
        failed = summary_info["failed"]
        total_channels = summary_info["total_channels"]
        total_videos = summary_info.get("total_videos", 0)
        successful_downloads = summary_info.get("successful_downloads", len(successful))
        target = summary_info.get("target", total_channels)

        # Show completion message - matches original format
        self._safe_print(
            f"  Completed: [{successful_downloads}/{target}] channels with downloads"
        )

        self._safe_print("")
        self._safe_print("[bold cyan]─[/bold cyan]".ljust(60, "─"))
        self._safe_print("")

        self._safe_print("\n[bold]Batch Download Summary:[/bold]")
        self._safe_print(f"✓ Successful: {len(successful)}")
        self._safe_print(f"✗ Failed: {len(failed)}")
        # Use max(1, ...) to avoid division by zero when all channels were skipped
        actual_processed = len(successful) + len(failed)
        self._safe_print(
            f"📊 Total processed: {total_channels}/{max(actual_processed, 1)}"
        )

        if successful:
            self._safe_print(f"📹 Total videos downloaded: {total_videos}")

        if failed and len(failed) > 0:
            self._safe_print(
                "\n[red]Some channels failed. Use --continue-on-error to continue with other channels.[/red]"
            )
