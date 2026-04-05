"""

Download-focused display plugin that mirrors the legacy batch output.



Matches the existing batch-download format while adding clickable channel links.

"""
from __future__ import annotations



import os

import re

import sys

from typing import Any



from rich.console import Console



from yt_fts.display.base import DisplayPlugin, PluginContext





class DownloadDefaultDisplayPlugin(DisplayPlugin):

    """

    Download display plugin with the legacy bullet-style layout.



    Keeps the current batch-download format intact and supports clickable links.

    """



    supported_commands: list[str] = ["download"]



    def __init__(self, context: PluginContext):

        """Initialize the download display plugin."""

        super().__init__(context)

        self._fallback_console = Console(force_terminal=False, legacy_windows=True)



    def get_name(self) -> str:

        """Get the plugin name."""

        return "download_default"



    def _safe_print(self, text: str) -> None:

        """

        Dual-sink print: try Rich console, fall back to plain text on OSError.

        Strips Rich markup tags for plain text fallback.

        """

        try:

            self.console.print(text)

        except OSError:

            plain_text = text

            

            # Strip Rich markup using regex for proper tag handling

            # Handle [link=url]...[/link] format first

            plain_text = re.sub(r'\[link=[^\]]+\]', '', plain_text)

            plain_text = plain_text.replace('[/link]', '')

            

            # Handle generic closing tag [/]

            plain_text = plain_text.replace('[/]', '')

            

            # Handle [tag] and [/tag] for color/style tags

            for tag in [

                "dim", "red", "bold", "cyan", "yellow", "green", "blue",

                "white", "italic", "spring_green2", "magenta", "grey62",

            ]:

                plain_text = plain_text.replace(f"[{tag}]", "")

                plain_text = plain_text.replace(f"[/{tag}]", "")

            

            try:

                self._fallback_console.print(plain_text)

            except (OSError, IOError, AttributeError):

                sys.stdout.write(plain_text + "\n")

                sys.stdout.flush()

    def _clear_and_print(self, text: str) -> None:

        """Ensure message starts on a new line (prevents progress bar artifacts on Windows)."""



        self._safe_print(text)





    def display_channel_header(self, channel_info: dict[str, Any]) -> None:

        """Display channel processing header - bullet point style."""

        # Blank line before each channel header for visual separation
        self._safe_print("")
        index = channel_info["index"]

        total = channel_info["total"]

        name = channel_info["name"]

        channel_url = channel_info.get("channel_url")

        db_stats = channel_info.get("db_stats", "0 videos")

        inconsistent = channel_info.get("inconsistent", False)

        inconsistency_reason = channel_info.get("inconsistency_reason", "")



        # Format channel name for clean display

        display_name = self._format_channel_name(name)



        # Make channel name clickable when supported; otherwise include the URL

        if channel_url:

            if getattr(self.console, "supports_hyperlinks", False) or os.getenv("WT_SESSION"):

                display_name = f"[link={channel_url}]{display_name}[/link]"

            else:

                display_name = f"{display_name} ({channel_url})"



        # Bullet point header with progress counter and index

        progress = f"{index}/{total}" if total else str(index)

        self._safe_print(f"{index}. * {display_name} [dim][{progress}][/dim]")

        # Stats as continuation line

        self._safe_print(f"   [dim]⎿ db: {db_stats}[/dim]")



        # Display inconsistency warning if present

        if inconsistent:

            details = channel_info.get("db_stats_details", {})

            parts = []

            parts.append(f"{details.get('total', 0)} total")



            video_parts = []

            video_parts.append(f"{details.get('with_subs', 0)} cc")

            video_parts.append(f"{details.get('no_subs', 0)} no cc")

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

            return f"{name[:20]}..."



        if len(name) > 30:

            return name[:27] + "..."



        return name



    def _normalize_message(self, message: str) -> str:

        """Normalize status lines to ASCII to avoid mojibake in Windows terminals."""

        replacements = {


            "\u2713": "+",

            "\u2022": "-",

            "\u2014": "-",

            "\u2013": "-",

            "\U0001f4b0": "$",

        }

        for old, new in replacements.items():

            message = message.replace(old, new)

        return message



    def display_rss_status(self, rss_info: dict[str, Any] | Any) -> None:

        """Display RSS status - continuation line."""

        if hasattr(rss_info, "get"):

            status = rss_info.get("status", "")

            message = rss_info.get("message", "")

        else:

            status = getattr(rss_info, "status", "")

            message = getattr(rss_info, "message", "")



        if not message:

            return  # Skip if no message



        self._safe_print(f"   [dim]⎿ RSS:[/dim] {message}")




    def display_ytapi_status(self, api_info: dict[str, Any] | Any) -> None:

        """Display yt-api status - continuation line."""

        if hasattr(api_info, "get"):

            status = api_info.get("status", "")

            message = api_info.get("message", "")

        else:

            status = getattr(api_info, "status", "")

            message = getattr(api_info, "message", "")



        if not message:

            return  # Skip if no message



        self._safe_print(f"   [dim]⎿ yt-api:[/dim] {message}")


    def display_ytdlp_operation(self, operation_info: dict[str, Any] | str) -> None:

        """Display yt-dlp operation status."""

        # Handle both string and dict inputs
        if isinstance(operation_info, str):
            message = operation_info
            operation = ""
        else:
            operation = operation_info.get("operation", "")
            message = operation_info.get("message", "")

        if operation and message:
            self._clear_and_print(f"   [dim]⎿ yt-dlp:[/dim] {operation} {message}")
        elif message:
            self._clear_and_print(f"   [dim]⎿ yt-dlp:[/dim] {message}")
        else:
            self._clear_and_print(f"   ⎿ [dim]yt-dlp:[/dim] {operation}")
    def display_whisper_operation(self, operation_info: dict[str, Any] | str) -> None:

        """Display Whisper operation status."""

        # Handle both string and dict inputs
        if isinstance(operation_info, str):
            message = operation_info
            operation = ""
        else:
            operation = operation_info.get("operation", "")
            message = operation_info.get("message", "")

        if operation and message:
            self._clear_and_print(f"   [dim]⎿ whisper:[/dim] {operation} {message}")
        elif message:
            self._clear_and_print(f"   ⎿ [dim]whisper:[/dim] {message}")
        else:
            self._clear_and_print(f"   ⎿ [dim]whisper:[/dim] {operation}")



    def display_download_result(self, result_info: dict[str, Any]) -> None:

        """Display download result - continuation line with metrics."""

        success = result_info["success"]

        target_reached = result_info.get("target_reached", False)

        message = result_info.get("message") or ""



        def _clean_message(raw: str) -> str:

            cleaned = " ".join(str(raw).split())

            while cleaned and cleaned[0] in {"-", "x", "*", "+"}:

                cleaned = cleaned[1:].lstrip()

            return cleaned



        if success:

            videos_count = result_info.get("videos_count", 0)

            videos_without_subtitles = result_info.get("videos_without_subtitles", 0)

            time_taken = result_info.get("time_taken", "")

            quota_used = result_info.get("quota_used", 0)

            clean_message = _clean_message(message)



            if target_reached and videos_count > 0:

                self._safe_print(

                    f"   - [cyan]+[/cyan] Reached target of {videos_count} videos saved, stopping..."

                )



            if clean_message and videos_count == 0:

                lowered = clean_message.lower()

                icon = ""

                # Skip icon for: backfill, RSS "no new videos", or "all videos already in database"

                if "backfill" in lowered:

                    icon = "+"

                elif "all videos already in database" in lowered:

                    icon = ""

                elif not ("no new videos" in lowered and "rss" in lowered):

                    icon = "!"

                if "no new videos" in lowered and "rss" in lowered:

                    clean_message = "all videos already in database"

                icon_prefix = f"{icon} " if icon else ""

                self._clear_and_print(f"   [dim]⎿ net:[/dim] {icon_prefix}{clean_message}")

            else:

                parts = []

                if videos_without_subtitles > 0:

                    parts.append(

                        f"{videos_count} new ({videos_without_subtitles} no cc)"

                    )

                else:

                    parts.append(f"{videos_count} new")



                if time_taken:

                    parts.append(f"took {time_taken}")



                if quota_used > 0:

                    from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill



                    quota_info = YouTubeAPIBackfill.get_global_quota_info()

                    remaining = quota_info["remaining"]

                    parts.append(f"+{quota_used} quota ({remaining:,} left)")



                self._clear_and_print(f"   [dim]⎿ net:[/dim] + {' | '.join(parts)}")

        else:

            error = result_info.get("error", "Unknown error")

            error = " ".join(str(error).split())



            if "rate limit" in error.lower() or "429" in error:

                emoji = "!!"

            elif "not found" in error.lower() or "404" in error:

                emoji = "x"

            elif "timeout" in error.lower():

                emoji = "!!"

            elif "network" in error.lower():

                emoji = "!!"

            else:

                emoji = "!"



            if len(error) > 80:

                error = error[:77] + "..."



            self._clear_and_print(f"   [dim]⎿ net:[/dim] {emoji} {error}")



    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:

        """Display batch summary - matches current format."""

        successful = summary_info["successful"]

        failed = summary_info["failed"]

        total_channels = summary_info["total_channels"]

        total_videos = summary_info.get("total_videos", 0)

        successful_downloads = summary_info.get("successful_downloads", len(successful))

        target = summary_info.get("target", total_channels)



        self._safe_print(

            f"  Completed: [{successful_downloads}/{target}] channels with downloads"

        )

        self._safe_print("")

        self._safe_print("[bold cyan]" + ("-" * 60) + "[/bold cyan]")

        self._safe_print("")

        self._safe_print("\n[bold]Batch Download Summary:[/bold]")

        self._safe_print(f"+ Successful: {len(successful)}")

        self._safe_print(f"x Failed: {len(failed)}")

        actual_processed = len(successful) + len(failed)

        self._safe_print(

            f"= Total processed: {total_channels}/{max(actual_processed, 1)}"

        )



        if successful:

            self._safe_print(f"= Total videos downloaded: {total_videos}")



        if failed and len(failed) > 0:

            self._safe_print(

                "\n[red]Some channels failed. Use --continue-on-error to continue with other channels.[/red]"

            )



    def info(self, message: str) -> None:

        """Display an informational message."""

        if message.startswith("   ") or message.startswith("["):

            self._safe_print(self._normalize_message(message))

        else:

            self._safe_print(f"   ⎿ [dim]{self._normalize_message(message)}[/dim]")



    def warning(self, message: str) -> None:

        """Display a warning message."""

        self._safe_print(f"   ⎿ [yellow]{message}[/yellow]")



    def error(self, message: str) -> None:

        """Display an error message."""

        self._safe_print(f"   ⎿ [red]{message}[/red]")

