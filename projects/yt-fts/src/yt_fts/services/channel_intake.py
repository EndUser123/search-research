"""
Channel Intake Service

Handles reading, validating, and importing channels from external sources
into the yt-fts database.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

from yt_fts.core.progress import UnifiedProgress


class ChannelStatus(Enum):
    """Status of a channel during import processing."""
    VALID = "valid"
    DUPLICATE = "duplicate"
    NOT_FOUND = "not_found"
    PRIVATE = "private"
    INVALID_FORMAT = "invalid_format"
    ERROR = "error"


@dataclass
class ChannelResult:
    """Result of processing a single channel."""
    input: str                  # Original input from file
    normalized: str | None      # Normalized URL/handle
    status: ChannelStatus       # Processing status
    channel_id: str | None = None
    channel_name: str | None = None
    error_message: str | None = None
    line_number: int = 0


@dataclass
class ImportSummary:
    """Summary statistics for channel import operation."""
    total_read: int = 0
    existing_count: int = 0  # Channels in database before import
    valid: int = 0
    duplicates: int = 0
    not_found: int = 0
    private: int = 0
    invalid_format: int = 0
    errors: int = 0

    @property
    def new_total(self) -> int:
        """Total channels in database after import."""
        return self.existing_count + self.valid

    @property
    def total_processed(self) -> int:
        return self.valid + self.duplicates + self.not_found + self.private + self.invalid_format + self.errors

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        from dataclasses import asdict
        return asdict(self)


class ChannelIntakeService:
    """Service for importing channels from external sources."""

    def __init__(
            self,
            console: "Console | None" = None,
            use_progress: bool = False,
        ):
        """
        Initialize the channel intake service.

        Args:
            console: Rich console for output
            use_progress: Enable progress bar display
        """
        self.console = console
        if console is None:
            from rich.console import Console
            self.console = Console()
        self.use_progress = use_progress

    def read_channels_file(self, file_path: str) -> list[tuple[int, str]]:
        """
        Read channels from file, preserving line numbers.

        Args:
            file_path: Path to channels file

        Returns:
            List of (line_number, channel) tuples
        """
        path = Path(file_path)
        if not path.exists():
            msg = f"Channels file not found: {file_path}"
            raise FileNotFoundError(msg)

        channels = []
        with path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                stripped = line.strip()
                # Skip empty lines and comments
                if not stripped or stripped.startswith("#"):
                    continue
                channels.append((line_num, stripped))

        return channels

    def _validate_channel_id_format(self, channel_id: str) -> bool:
        """
        Validate channel ID format matches YouTube requirements.

        YouTube channel IDs must be exactly 24 characters, starting with 'UC'
        followed by 22 alphanumeric characters, underscores, or hyphens.

        Args:
            channel_id: Channel ID to validate

        Returns:
            True if valid format, False otherwise
        """
        import re
        return bool(re.match(r"^UC[a-zA-Z0-9_-]{22}$", channel_id))

    def validate_channel(self, channel_input: str) -> ChannelResult:
        """
        Validate a single channel - format check only (fast).

        Args:
            channel_input: Raw channel input (handle, URL, ID)

        Returns:
            ChannelResult with validation status
        """
        import re

        result = ChannelResult(
            input=channel_input,
            normalized=None,
            status=ChannelStatus.ERROR,
        )

        # If input looks like a raw channel ID (starts with UC), validate format BEFORE normalizing
        # This catches invalid channel IDs that normalize_channel would convert to @handle format
        if channel_input.startswith("UC") and not channel_input.startswith(("https://", "http://")):
            if not self._validate_channel_id_format(channel_input):
                result.status = ChannelStatus.INVALID_FORMAT
                result.error_message = f"Invalid channel ID format: {channel_input}"
                return result

        # Normalize the channel input using normalize_channel (no progress output)
        try:
            from yt_fts.services.channel_cleaner import ChannelCleaner
            cleaner = ChannelCleaner(console=self.console)
            normalized = cleaner.normalize_channel(channel_input)

            # Check if normalized result looks like a valid YouTube channel reference
            if normalized and (
                normalized.startswith(("https://www.youtube.com/", "@")) or bool(re.match(r"^UC[a-zA-Z0-9_-]{22}$", normalized))
            ):
                # If it's a /channel/ URL, validate the channel_id format
                if "/channel/" in normalized:
                    parts = normalized.split("/channel/")
                    if len(parts) > 1:
                        channel_id = parts[1].split("/")[0]
                        if not self._validate_channel_id_format(channel_id):
                            result.status = ChannelStatus.INVALID_FORMAT
                            result.error_message = f"Invalid channel ID format: {channel_id}"
                            return result

                result.normalized = normalized
                result.status = ChannelStatus.VALID
            else:
                result.status = ChannelStatus.INVALID_FORMAT
                result.error_message = "Could not normalize channel format"
        except Exception as e:
            result.status = ChannelStatus.INVALID_FORMAT
            result.error_message = str(e)

        return result

    def check_duplicates(self, results: list[ChannelResult]) -> tuple[list[ChannelResult], int]:
        """
        Mark channels that already exist in database.

        Args:
            results: List of ChannelResult objects

        Returns:
            Tuple of (updated results with duplicates marked, existing channel count)
        """
        from sqlite_utils import Database

        from yt_fts.core.database import get_db_path


        db = Database(get_db_path())

        # Get existing channel count and URLs/IDs
        existing_count = 0
        existing_urls = set()
        existing_ids = set()

        for row in db.execute("SELECT channel_url, channel_id FROM Channels").fetchall():
            existing_count += 1
            url = row[0]
            existing_urls.add(url)
            existing_urls.add(url.rstrip("/"))  # Normalize trailing slash
            existing_urls.add(url.removesuffix("/videos"))  # Match database.py normalization
            if row[1]:
                existing_ids.add(row[1])

        for result in results:
            if result.status != ChannelStatus.VALID:
                continue

            # Check by URL using same normalization as database.py
            if result.normalized:
                normalized = result.normalized
                # Check direct match and normalized forms (/, /videos suffixes)
                if (normalized in existing_urls or
                    normalized.rstrip("/") in existing_urls or
                    normalized.removesuffix("/videos") in existing_urls):
                    result.status = ChannelStatus.DUPLICATE
                    continue

                # Also check by channel_id (PRIMARY KEY constraint)
                # Extract channel_id from normalized URL for comparison
                channel_id = None
                if "/channel/" in normalized:
                    parts = normalized.split("/channel/")
                    if len(parts) > 1:
                        channel_id = parts[1].split("/")[0]
                elif "/c/" in normalized:
                    parts = normalized.split("/c/")
                    if len(parts) > 1:
                        channel_id = parts[1].split("/")[0]
                elif "@" in normalized:
                    # @handle format - no channel_id extraction possible
                    pass
                elif normalized.startswith("UC") and len(normalized) == 24:
                    # Raw channel ID
                    channel_id = normalized

                if channel_id and channel_id in existing_ids:
                    result.status = ChannelStatus.DUPLICATE

        return results, existing_count

    def insert_channels(self, results: list[ChannelResult]) -> int:
        """
        Insert valid, non-duplicate channels into database.

        Args:
            results: List of ChannelResult objects

        Returns:
            Number of channels inserted
        """
        from yt_fts.core.database import add_channel_info_batch

        to_insert = []
        for r in results:
            if r.status == ChannelStatus.VALID:
                normalized = r.normalized or r.input
                channel_id = None

                # Extract channel_id from URL if possible
                if "/channel/" in normalized:
                    parts = normalized.split("/channel/")
                    if len(parts) > 1:
                        channel_id = parts[1].split("/")[0]
                        # Validate extracted channel_id format
                        if not self._validate_channel_id_format(channel_id):
                            r.status = ChannelStatus.INVALID_FORMAT
                            r.error_message = f"Invalid channel ID format: {channel_id}"
                            continue
                elif "/c/" in normalized:
                    # Custom URL - channel_id will be resolved during download
                    # Use a placeholder based on the custom name
                    parts = normalized.split("/c/")
                    if len(parts) > 1:
                        custom_name = parts[1].split("/")[0]
                        channel_id = f"CUSTOM_{custom_name}"
                elif "@" in normalized:
                    # Handle format - channel_id will be resolved during download
                    channel_id = normalized  # Store handle, will be resolved later
                # Raw channel ID input - validate format
                elif self._validate_channel_id_format(normalized):
                    channel_id = normalized
                else:
                    r.status = ChannelStatus.INVALID_FORMAT
                    r.error_message = f"Invalid channel ID format: {normalized}"
                    continue

                to_insert.append((channel_id, "", normalized))

        if not to_insert:
            return 0

        return add_channel_info_batch(to_insert)

    def process(
        self,
        file_path: str,
        validate_only: bool = False,
        dry_run: bool = False,
        show_progress: bool = True,
    ) -> tuple[list[ChannelResult], ImportSummary]:
        """
        Process channels from file: read, validate, deduplicate, insert.

        Args:
            file_path: Path to channels file
            validate_only: Skip database insertion
            dry_run: Show what would be done
            show_progress: Show progress bar

        Returns:
            Tuple of (results list, summary)
        """
        # Determine whether to use progress display
        use_progress = show_progress and self.use_progress

        progress: UnifiedProgress | None = None
        if use_progress:
            progress = UnifiedProgress.create(use_rich=True, display_mode="bar", console=self.console)

        try:
            # Step 1: Read file
            channels = self.read_channels_file(file_path)
            summary = ImportSummary(total_read=len(channels))

            if not channels:
                return [], summary

            if progress:
                progress.start()
                task = progress.add_task("Validating channels", total=len(channels))

            # Step 2: Validate (format check only - fast)
            results = []
            for i, (line_num, channel) in enumerate(channels):
                result = self.validate_channel(channel)
                result.line_number = line_num
                results.append(result)

                if progress:
                    progress.update(task, completed=i + 1)

            # Step 3: Check duplicates (always check for accurate summary)
            if progress:
                progress.update(task, status="Checking duplicates...")

            results, existing_count = self.check_duplicates(results)
            summary.existing_count = existing_count

            # Step 4: Insert valid channels (unless validate_only or dry_run)
            if not validate_only and not dry_run:
                if progress:
                    progress.update(task, status="Inserting channels...")
                self.insert_channels(results)

            if progress:
                progress.complete(task)

            # Calculate summary
            for result in results:
                if result.status == ChannelStatus.VALID:
                    summary.valid += 1
                elif result.status == ChannelStatus.DUPLICATE:
                    summary.duplicates += 1
                elif result.status == ChannelStatus.NOT_FOUND:
                    summary.not_found += 1
                elif result.status == ChannelStatus.PRIVATE:
                    summary.private += 1
                elif result.status == ChannelStatus.INVALID_FORMAT:
                    summary.invalid_format += 1
                elif result.status == ChannelStatus.ERROR:
                    summary.errors += 1

            return results, summary

        finally:
            if progress:
                progress.stop()

    def display_summary(self, summary: ImportSummary) -> None:
        """Display import summary."""
        self.console.print(f"  • Total read: {summary.total_read}")
        if summary.duplicates > 0:
            self.console.print(f"  • [yellow]Duplicates:[/yellow] {summary.duplicates}")
        self.console.print(f"  • [green]Valid (new):[/green] {summary.valid}")
        if summary.existing_count > 0:
            new_total = summary.existing_count + summary.valid
            self.console.print(f"  • New total: {new_total}")
        else:
            new_total = summary.existing_count + summary.valid
            self.console.print(f"  • New total: {new_total}")
        if summary.invalid_format > 0:
            self.console.print(f"  • [yellow]Invalid format:[/yellow] {summary.invalid_format}")
        if summary.errors > 0:
            self.console.print(f"  • [red]Errors:[/red] {summary.errors}")

    def export_valid_channels(self, results: list[ChannelResult], output_path: str) -> int:
        """
        Export valid channels (including duplicates) to a file.

        Args:
            results: List of ChannelResult objects
            output_path: Path to output file

        Returns:
            Number of channels exported
        """
        valid_channels = [
            r.normalized or r.input
            for r in results
            if r.status in (ChannelStatus.VALID, ChannelStatus.DUPLICATE)
        ]

        Path(output_path).write_text("\n".join(valid_channels))
        return len(valid_channels)
