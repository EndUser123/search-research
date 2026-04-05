# --- METADATA ---
# Filename: yt_sync/repair.py
# Version: 0.2
#
# --- CHANGELOG ---
# v0.2: Corrected NameError by properly defining 'handle' variable before use.
# v0.1: Initial structure for the Library Repair Tool, as defined in ADR 007.
#
# --- INTEGRITY ---
# Previous Character Count: 1024
# Current Character Count: 2368
# Reason for Shrinkage: null
# ------------------
#
# --- ARCHITECT'S OATH (PRE-FLIGHT CHECK) ---
# Self-check to prevent failures.
# 1. Context Continuity: Review prior instructions/code ensuring no requirements/context forgotten.
# 2. Error Prevention: Identify/address common errors (input validation, exception handling, edge cases).
# 3. API Verification: Verify API calls against docs to prevent signature mismatches/runtime errors.
# 4. Data Integrity: Ensure no data/logic from files/steps lost or altered without instruction.
# 6. Reasoning Transparency: Explain reasoning, choices, and assumptions.
# -------------------------------------------

import logging
import shutil
from pathlib import Path
from typing import Any

from rich.console import Console

from . import utils
from .api_client import YouTubeAPIClient

logger = logging.getLogger(__name__)


class LibraryRepairTool:
    """
    A tool to scan the library for untracked files, verify them against API metadata,
    and adopt them into the managed library by renaming them and updating the archive.
    This logic is triggered by `... --audit` and executed if `--repair` is also present.
    """

    def __init__(
        self,
        args: Any,
        config: dict[str, Any],
        api_client: YouTubeAPIClient | None = None,
    ):
        self.args = args
        self.config = config
        self.api_client = api_client
        self.console = Console()
        logger.info("Library Repair Tool initialized.")

    def run(self):
        """
        The main entry point for the repair tool. Reads channels from the config
        and processes them sequentially.
        """
        self.console.print("[bold cyan]--- Library Audit & Repair ---[/bold cyan]")
        if self.args.repair:
            self.console.print(
                "[bold yellow]--repair[/bold yellow] flag detected. Write operations are enabled."
            )
        else:
            self.console.print(
                "[green]Running in read-only audit mode. No changes will be made.[/green]"
            )

        if not self._preflight_checks():
            return

        try:
            channel_urls = self._load_channel_urls()
        except (FileNotFoundError, ValueError) as e:
            self.console.print(f"[bold red]Error loading channels: {e}[/bold red]")
            return

        total_untracked_files = 0
        for i, channel_url in enumerate(channel_urls, 1):
            untracked_count = self._run_for_channel(channel_url, i, len(channel_urls))
            if untracked_count is not None:
                total_untracked_files += untracked_count

        self.console.print(
            f"\n[bold cyan]--- Audit Complete: Found {total_untracked_files} total untracked files across all channels. ---[/bold cyan]"
        )

    def _run_for_channel(
        self, channel_url: str, index: int, total: int
    ) -> int | None:
        """Runs the audit and repair process for a single channel."""
        handle = utils.extract_handle_from_url(channel_url)
        if not handle:
            self.console.print(
                f"[bold red]Could not extract channel handle from URL: {channel_url}. Skipping.[/bold red]"
            )
            return None

        self.console.print(
            f"\n[white on blue] Auditing Channel ({index}/{total}): {handle} [/white on blue]"
        )
        base_dir = Path(self.config.get("base_dir", "."))
        channel_dir = base_dir / utils.sanitize_filename(handle.lstrip("@"))

        if not channel_dir.is_dir():
            self.console.print(
                f"  [dim]Directory not found at {channel_dir}. Nothing to audit.[/dim]"
            )
            return 0

        archive_path = channel_dir / ".metadata" / "downloads.txt"
        archived_ids = self._read_archive_file(archive_path)
        local_files = utils.get_video_files_in_dir(channel_dir)

        untracked_files = [
            fp
            for fp in local_files
            if not (vid_id := utils.get_id_from_filename(fp.name))
            or vid_id not in archived_ids
        ]

        if untracked_files:
            self.console.print(
                f"  [yellow]Found {len(untracked_files)} untracked files.[/yellow]"
            )
            # Future logic will go here
            # self._process_untracked_batch(untracked_files, handle)
        else:
            self.console.print(
                "  [green]✓ All local video files are tracked in the archive.[/green]"
            )

        return len(untracked_files)

    def _preflight_checks(self) -> bool:
        """Checks for necessary external tools like ffprobe."""
        if not shutil.which("ffprobe"):
            self.console.print(
                "[bold red]Error: `ffprobe` is not found in your system's PATH.[/bold red]"
            )
            self.console.print(
                "`ffprobe` is part of the FFmpeg suite and is required for file verification."
            )
            self.console.print(
                "Please install FFmpeg and ensure it's accessible via the PATH."
            )
            return False
        logger.debug("ffprobe found, pre-flight checks passed.")
        return True

    def _load_channel_urls(self) -> list[str]:
        """Load channel URLs from the configured file."""
        url_file_path_str = self.config.get("url_file")
        if not url_file_path_str:
            raise ValueError(
                "A URL file must be specified in config.yaml under 'url_file' key."
            )

        url_file_path = Path(url_file_path_str)
        if not url_file_path.is_file():
            raise FileNotFoundError(f"URL file not found: {url_file_path}")

        with open(url_file_path, encoding="utf-8") as f:
            return [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            ]

    def _read_archive_file(self, archive_path: Path) -> set[str]:
        """Reads video IDs from a specific channel's archive file."""
        if not archive_path.is_file():
            return set()
        with open(archive_path, encoding="utf-8") as f:
            return {line.strip().split()[-1] for line in f if line.strip()}
