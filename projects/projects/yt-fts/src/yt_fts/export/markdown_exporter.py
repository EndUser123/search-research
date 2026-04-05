"""
Markdown export functionality for Obsidian and Roam Research.

Exports video transcripts as Markdown files with YAML frontmatter,
supporting both Obsidian wikilinks and Roam Research page references.
"""

import re
from pathlib import Path
from typing import Literal

from rich.console import Console

from yt_fts.core.database import (
    get_channel_name_from_id,
    get_metadata_from_db,
    get_subs_by_video_id,
    get_vid_ids_by_channel_id,
)

MarkdownFormat = Literal["obsidian", "roam"]


class MarkdownExporter:
    """Export video transcripts as Markdown with YAML frontmatter."""

    def __init__(
        self,
        format: MarkdownFormat = "obsidian",
        output_dir: str | None = None,
    ) -> None:
        """
        Initialize the Markdown exporter.

        Args:
            format: Markdown format - "obsidian" or "roam"
            output_dir: Directory to save markdown files (default: channel_id_md)
        """
        self.format = format
        self.output_dir = output_dir
        self.console = Console()

    def export_channel(self, channel_id: str) -> Path | None:
        """
        Export all videos from a channel to markdown files.

        Args:
            channel_id: YouTube channel ID

        Returns:
            Path to output directory, or None if failed
        """
        channel_name = get_channel_name_from_id(channel_id)

        # Create output directory
        if self.output_dir:
            output_path = Path(self.output_dir)
        else:
            output_path = Path(f"{channel_id}_md")

        if output_path.exists():
            self.console.print(
                f"[red]Error:[/red] Directory [yellow]{output_path}[/yellow] already exists"
            )
            return None

        output_path.mkdir(parents=True)

        # Get all videos for channel
        vid_ids = get_vid_ids_by_channel_id(channel_id)

        if not vid_ids:
            self.console.print(f"[yellow]No videos found for channel {channel_name}[/yellow]")
            return None

        # Export each video
        with self.console.status(
            f"[bold green]Exporting {len(vid_ids)} videos from {channel_name}...[/bold green]"
        ) as status:
            for i, (vid_id,) in enumerate(vid_ids, 1):
                status.update(
                    f"[bold green]Exporting video {i}/{len(vid_ids)}: {vid_id}[/bold green]"
                )
                self.export_video(vid_id, output_path)

        self.console.print(
            f"[green]✓[/green] Exported [bold]{len(vid_ids)}[/bold] videos to [bold]{output_path}[/bold]"
        )
        return output_path

    def export_video(self, video_id: str, output_dir: Path) -> Path:
        """
        Export a single video to markdown file.

        Args:
            video_id: YouTube video ID
            output_dir: Directory to save markdown file

        Returns:
            Path to created markdown file
        """
        # Get video metadata
        metadata = get_metadata_from_db(video_id)
        subs = get_subs_by_video_id(video_id)

        # Generate markdown content
        content = self._generate_markdown(video_id, metadata, subs)

        # Sanitize title for filename
        safe_title = self._sanitize_title(metadata["video_title"])
        filename = f"{safe_title}.md"

        # Write markdown file
        filepath = output_dir / filename
        with filepath.open("w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def _generate_markdown(
        self,
        video_id: str,
        metadata: dict,
        subs: list[tuple[str, str, str]],
    ) -> str:
        """
        Generate markdown content with YAML frontmatter.

        Args:
            video_id: YouTube video ID
            metadata: Video metadata dictionary
            subs: List of (start_time, stop_time, text) tuples

        Returns:
            Complete markdown document as string
        """
        # Generate YAML frontmatter
        frontmatter = self._generate_frontmatter(video_id, metadata)

        # Generate transcript body
        body = self._generate_transcript_body(video_id, metadata, subs)

        return f"---\n{frontmatter}\n---\n\n{body}"

    def _generate_frontmatter(self, video_id: str, metadata: dict) -> str:
        """
        Generate YAML frontmatter for markdown file.

        Args:
            video_id: YouTube video ID
            metadata: Video metadata dictionary

        Returns:
            YAML frontmatter as string
        """
        # Extract metadata
        title = metadata.get("video_title", "Unknown Title")
        channel_id = metadata.get("channel_id", "")
        channel_name = get_channel_name_from_id(channel_id) if channel_id else "Unknown"
        video_date = metadata.get("video_date", "")
        url = f"https://youtu.be/{video_id}"

        # Generate tags from video title (simple keyword extraction)
        tags = self._extract_tags(title)

        # Build YAML frontmatter
        frontmatter_lines = [
            f'title: "{self._escape_yaml(title)}"',
            f"youtube_id: {video_id}",
            f"url: {url}",
            f'channel: "{self._escape_yaml(channel_name)}"',
            f"channel_id: {channel_id}",
        ]

        if video_date:
            frontmatter_lines.append(f"publish_date: {video_date}")

        if tags:
            tags_str = ", ".join(tags)
            frontmatter_lines.append(f"tags: [{tags_str}]")

        return "\n".join(frontmatter_lines)

    def _generate_transcript_body(
        self,
        video_id: str,
        metadata: dict,
        subs: list[tuple[str, str, str]],
    ) -> str:
        """
        Generate transcript body with timestamps and content.

        Args:
            video_id: YouTube video ID
            metadata: Video metadata dictionary
            subs: List of (start_time, stop_time, text) tuples

        Returns:
            Transcript body as markdown string
        """
        title = metadata.get("video_title", "Unknown Title")
        url = f"https://youtu.be/{video_id}"

        # Header
        lines = [
            f"# {title}\n",
            f"**Source:** [{url}]({url})\n",
            "---\n\n",
            "## Transcript\n\n",
        ]

        # Process subtitles
        for start_time, _stop_time, text in subs:
            # Format timestamp based on markdown format
            timestamp_link = self._format_timestamp(video_id, start_time)

            # Add subtitle text
            lines.append(f"{timestamp_link} {text.strip()}\n\n")

        return "".join(lines)

    def _format_timestamp(self, video_id: str, timestamp: str) -> str:
        """
        Format timestamp as clickable link.

        Args:
            video_id: YouTube video ID
            timestamp: Timestamp in HH:MM:SS format

        Returns:
            Formatted timestamp link
        """
        url = f"https://youtu.be/{video_id}?t={self._timestamp_to_seconds(timestamp)}"

        if self.format == "obsidian":
            # Obsidian format: [[HH:MM:SS]]
            return f"[[{timestamp}]]"
        if self.format == "roam":
            # Roam format: #[[HH:MM:SS]]
            return f"#[[{timestamp}]]"
        # Fallback: plain text link
        return f"[{timestamp}]({url})"

    def _timestamp_to_seconds(self, timestamp: str) -> int:
        """
        Convert HH:MM:SS or HH:MM:SS.mmm timestamp to seconds.

        Args:
            timestamp: Timestamp in HH:MM:SS or HH:MM:SS.mmm format

        Returns:
            Seconds as integer
        """
        # Remove milliseconds if present
        timestamp = timestamp.split(".")[0]

        parts = timestamp.split(":")
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + int(s)
        if len(parts) == 2:
            m, s = parts
            return int(m) * 60 + int(s)
        return 0

    def _extract_tags(self, title: str) -> list[str]:
        """
        Extract simple tags from video title.

        Args:
            title: Video title

        Returns:
            List of tag strings
        """
        # Simple keyword extraction: split by common separators
        # Remove special characters, convert to lowercase
        words = re.split(r"[\s\-_|,.]+", title.lower())

        # Filter out common words and short words
        stop_words = {"the", "a", "an", "is", "are", "with", "and", "or", "in", "on", "at"}
        tags = [w for w in words if len(w) > 2 and w not in stop_words]

        # Limit to 5 tags
        return tags[:5]

    def _sanitize_title(self, title: str) -> str:
        """
        Sanitize video title for use as filename.

        Args:
            title: Video title

        Returns:
            Sanitized filename-safe string
        """
        # Remove invalid filename characters
        sanitized = re.sub(r'[<>:"/\\|?*]', "", title)
        # Replace multiple spaces with single space
        sanitized = re.sub(r"\s+", " ", sanitized)
        # Limit length
        return sanitized.strip()[:100]

    def _escape_yaml(self, text: str) -> str:
        """
        Escape special characters for YAML strings.

        Args:
            text: Text to escape

        Returns:
            YAML-safe string
        """
        # Escape quotes and backslashes
        return text.replace("\\", "\\\\").replace('"', '\\"')
