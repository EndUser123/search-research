"""
Default display plugin for yt-fts.

Provides clean, formatted output using Rich for all commands.
"""

import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel

from yt_fts.display.base import DisplayPlugin, PluginContext
from yt_fts.utils.types import (
    ChannelDisplayInfo,
    DownloadResultInfo,
    ImportProgressInfo,
    ImportResultInfo,
    RssInfo,
    SearchResults,
)


class DefaultDisplayPlugin(DisplayPlugin):
    """
    Default display plugin with clean Rich formatting.

    Supports all commands with styled, readable output.
    """

    supported_commands: list[str] = []  # Supports all commands

    def __init__(self, context: PluginContext):
        """Initialize the default display plugin."""
        super().__init__(context)
        self._fallback_console = Console(force_terminal=False, legacy_windows=True)

    def get_name(self) -> str:
        """Get the plugin name."""
        return "default"

    def get_formatter(self) -> Any | None:
        """
        Get a RichTextFormatter for colored real-time logging.

        Returns:
            RichTextFormatter instance with the plugin's console
        """
        from yt_fts.utils.text_formatter import RichTextFormatter

        return RichTextFormatter(console=self.console)

    def _safe_print(self, text: str) -> None:
        """
        Dual-sink print: try Rich console, fall back to plain text on OSError.
        """
        try:
            self.console.print(text)
        except OSError:
            # Strip Rich markup and print plain text
            plain_text = text
            for tag in [
                "dim",
                "red",
                "bold",
                "cyan",
                "yellow",
                "green",
                "blue",
                "white",
                "italic",
                "spring_green2",
                "magenta",
                "grey62",
            ]:
                plain_text = plain_text.replace(f"[{tag}]", "")
                plain_text = plain_text.replace(f"[/{tag}]", "")
            plain_text = plain_text.replace("[/]", "")
            plain_text = plain_text.replace("[link=", "")
            plain_text = plain_text.replace("]", "")
            try:
                self._fallback_console.print(plain_text)
            except Exception:
                sys.stdout.write(plain_text + "\n")
                sys.stdout.flush()

    # Search display methods

    def display_search_results(self, results: SearchResults) -> None:
        """Display search results with formatted output."""
        results.get("query", "")
        results.get("scope", "all")
        matches = results.get("matches", [])
        total_matches = results.get("total_matches", len(matches))
        total_videos = results.get("total_videos", 0)
        total_channels = results.get("total_channels", 0)

        if not matches:
            self._safe_print("[yellow]No matches found[/yellow]")
            self._safe_print("- Try shortening the search to specific words")
            self._safe_print(
                "- Try using the wildcard operator [bold]*[/bold] to search for partial words"
            )
            self._safe_print(
                "- Try using the [bold]OR[/bold] operator to search for multiple words"
            )
            return

        # Group results by channel and video
        fts_dict: dict[str, dict[tuple[str, str, str], list[dict[str, Any]]]] = {}

        for quote in matches:
            channel_name = quote.get("channel_name", "Unknown")
            video_title = quote.get("video_title", "")
            video_date = quote.get("video_date", "")
            video_id = quote.get("video_id", "")
            quote_data = {
                "text": quote.get("text", ""),
                "time_stamp": quote.get("time_stamp", ""),
                "link": quote.get("link", ""),
                "subs": quote.get("subs", quote.get("text", "")),
            }

            if channel_name not in fts_dict:
                fts_dict[channel_name] = {}

            key = (video_title, video_date, video_id)
            if key not in fts_dict[channel_name]:
                fts_dict[channel_name][key] = []
            fts_dict[channel_name][key].append(quote_data)

        # Display results grouped by channel
        for channel_name, videos in fts_dict.items():
            self._safe_print(
                f"[spring_green2][bold]{channel_name}[/bold][/spring_green2]"
            )
            self._safe_print("")

            for (video_name, video_date, video_id), quotes in videos.items():
                self._safe_print(
                    f'{video_id} ({video_date}) "[bold][blue]{video_name}[/blue][/bold]"'
                )
                self._safe_print("")

                for quote in quotes:
                    link = quote["link"]
                    time_stamp = quote["time_stamp"]
                    words = quote["subs"]
                    self._safe_print(
                        f"       [grey62][link={link}]{time_stamp}[/link][/grey62] -> "
                        f'[italic][white]"{words}"[/white][/italic]'
                    )
                self._safe_print("")

        # Summary
        summary = f"Found [bold]{total_matches}[/bold] matches in [bold]{total_videos}[/bold] "
        summary += f"videos from [bold]{total_channels}[/bold] channel"
        if total_channels != 1:
            summary += "s"
        self._safe_print(summary)

    # Download display methods

    def display_channel_header(self, channel_info: ChannelDisplayInfo) -> None:
        """Display channel processing header."""
        index = channel_info["index"]
        total = channel_info["total"]
        name = channel_info["name"]
        channel_url = channel_info.get("channel_url")
        db_stats = channel_info.get("db_stats", "0 videos")
        successful_downloads = channel_info.get("successful_downloads", 0)

        display_name = self._format_channel_name(name)

        # Make channel name clickable if URL is available
        if channel_url:
            clickable_name = f"[link={channel_url}]{display_name}[/link]"
        else:
            clickable_name = display_name

        self._safe_print(
            f"{index}. [cyan]●[/cyan] {clickable_name} [dim][{successful_downloads}/{total}][/dim]"
        )
        self._safe_print(f"   [dim]⎿ db: {db_stats}[/dim]")

    def _format_channel_name(self, name: str) -> str:
        """Format channel name for clean display."""
        if not name:
            return "Unknown"

        if (
            not name.startswith("http")
            and not name.startswith("@")
            and not name.startswith("UC")
        ):
            return name

        if name.startswith("@"):
            return name

        if "youtube.com/@" in name:
            handle_part = name.split("youtube.com/@")[-1].split("/")[0]
            return f"@{handle_part}"

        if "/channel/" in name:
            channel_id = name.split("/channel/")[-1].split("/")[0]
            if len(channel_id) > 20:
                return f"channel/{channel_id[:18]}..."
            return f"channel/{channel_id}"

        if name.startswith("UC") and len(name) >= 20:
            return f"channel/{name[:18]}..."

        if len(name) > 30:
            return name[:27] + "..."

        return name

    def display_rss_status(self, rss_info: RssInfo) -> None:
        """Display RSS status."""
        message = rss_info.get("message", "")
        self._safe_print(f"   [dim]⎿ RSS:[/dim] {message}")

    def display_download_result(self, result_info: DownloadResultInfo) -> None:
        """Display download result."""
        success = result_info["success"]
        target_reached = result_info.get("target_reached", False)

        if success:
            videos_count = result_info.get("videos_count", 0)
            videos_without_subtitles = result_info.get("videos_without_subtitles", 0)
            time_taken = result_info.get("time_taken", "")
            quota_used = result_info.get("quota_used", 0)

            if target_reached and videos_count > 0:
                self._safe_print(
                    f"   ⎿ [cyan]✓[/cyan] Reached target of {videos_count} videos saved, stopping..."
                )

            message = result_info.get("message", "")
            if message and videos_count == 0:
                self._safe_print(f"   ⎿ [dim]net:[/dim] {message}")
            else:
                parts = []
                if videos_without_subtitles > 0:
                    parts.append(
                        f"✅ {videos_count} new ({videos_without_subtitles} no subs)"
                    )
                else:
                    parts.append(f"✅ {videos_count} new")

                if time_taken:
                    parts.append(f"took {time_taken}")

                if quota_used > 0:
                    parts.append(f"+{quota_used} quota")

                self._safe_print(f"   ⎿ [dim]net:[/dim] {' | '.join(parts)}")
        else:
            error = result_info.get("error", "Unknown error")
            error = " ".join(str(error).split())

            # Classify error for emoji
            if "rate limit" in error.lower() or "429" in error:
                emoji = "⏱"
            elif "not found" in error.lower() or "404" in error:
                emoji = "🔍"
            elif "timeout" in error.lower():
                emoji = "⏰"
            elif "network" in error.lower():
                emoji = "🌐"
            else:
                emoji = "✗"

            if len(error) > 80:
                error = error[:77] + "..."

            self._safe_print(f"   ⎿ [dim]net:[/dim] {emoji} {error}")

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """Display batch summary."""
        successful = summary_info["successful"]
        failed = summary_info["failed"]
        total_videos = summary_info.get("total_videos", 0)
        successful_downloads = summary_info.get("successful_downloads", len(successful))
        target = summary_info.get("target", len(successful) + len(failed))

        self._safe_print(
            f"  Completed: [{successful_downloads}/{target}] channels with downloads"
        )
        self._safe_print("")
        self._safe_print("[bold cyan]─[/bold cyan]".ljust(60, "─"))
        self._safe_print("")
        self._safe_print("[bold]Batch Download Summary:[/bold]")
        self._safe_print(f"✓ Successful: {len(successful)}")
        self._safe_print(f"✗ Failed: {len(failed)}")
        self._safe_print(f"📊 Total processed: {len(successful) + len(failed)}")

        if successful:
            self._safe_print(f"📹 Total videos downloaded: {total_videos}")

        if failed and len(failed) > 0:
            self._safe_print(
                "\n[red]Some channels failed. Use --continue-on-error to continue with other channels.[/red]"
            )

    # Status display methods

    def display_status(self, status_info: dict[str, Any]) -> None:
        """Display system status."""
        db_stats = status_info.get("db_stats", {})
        quota_info = status_info.get("quota_info", {})
        config_info = status_info.get("config_info", {})
        status_info.get("detailed", False)

        # Main status panel
        status_text = f"""[bold cyan]Database[/bold cyan]
  Channels: {db_stats.get('channels', 0):,}
  Videos: {db_stats.get('videos', 0):,}
  Subtitles: {db_stats.get('subtitles', 0):,}
  With Transcripts: {db_stats.get('with_transcripts', 0):,}"""

        if "path" in db_stats:
            status_text += f"\n  Path: {db_stats['path']}"
        if "size" in db_stats:
            status_text += f"\n  Size: {db_stats['size']}"

        status_text += "\n\n[bold cyan]API Quota[/bold cyan]"
        status_text += f"\n  Used: {quota_info.get('used', 0):,} / {quota_info.get('limit', 10000):,}"
        status_text += f"\n  Remaining: {quota_info.get('remaining', 10000):,}"

        if config_info:
            status_text += "\n\n[bold cyan]Config[/bold cyan]"
            for key, value in config_info.items():
                status_text += f"\n  {key}: {value}"

        self.console.print(
            Panel(
                status_text,
                title="[bold green]System Status[/bold green]",
                border_style="cyan",
            )
        )

    # Import display methods

    def display_import_progress(self, import_info: ImportProgressInfo) -> None:
        """Display import progress."""
        source = import_info.get("source", "")
        progress = import_info.get("progress", 0)
        message = import_info.get("message", "")
        imported = import_info.get("imported", 0)

        self._safe_print(f"[dim]Importing from {source}:[/dim] {progress}% - {message}")
        if imported > 0:
            self._safe_print(f"  [dim]→ {imported} items imported[/dim]")

    def display_import_result(self, result_info: ImportResultInfo) -> None:
        """Display import completion result."""
        success = result_info.get("success", False)
        imported = result_info.get("imported", 0)
        failed = result_info.get("failed", 0)
        duration = result_info.get("duration", "")

        if success:
            self._safe_print("[green]✓ Import complete[/green]")
            self._safe_print(f"  Imported: {imported} items")
            if duration:
                self._safe_print(f"  Duration: {duration}")
            if failed > 0:
                self._safe_print(f"  [yellow]Failed: {failed} items[/yellow]")
        else:
            self._safe_print("[red]✗ Import failed[/red]")
            errors = result_info.get("errors", [])
            for error in errors[:3]:
                self._safe_print(f"  [dim]→ {error}[/dim]")
