'''
Quota display module for batch downloader.

Extracted from batch_downloader.py to separate concerns.
'''
from __future__ import annotations

from rich.console import Console


class QuotaDisplay:
    '''
    Handles YouTube API quota status display.

    Displays quota information when quota is low (< 1000 remaining or depleted).
    '''

    def __init__(self, console: Console) -> None:
        '''
        Initialize QuotaDisplay.

        Args:
            console: Rich Console instance for output
        '''
        self.console = console

    def print_quota_status(self, header: str) -> None:
        '''
        Print quota status if quota is low.

        Skips display if:
        - No YOUTUBE_API_KEY configured
        - All keys have >= 1000 remaining
        - No keys are depleted

        Args:
            header: Header text to display (e.g., "yt-api quota")
        '''
        from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill
        import os

        # Skip quota display if no API key configured
        if not os.getenv("YOUTUBE_API_KEY"):
            return

        api_backfill = YouTubeAPIBackfill()
        quota_lines = api_backfill.format_quota_lines()

        # Only show quota if any key has < 1000 remaining or is depleted
        has_low_quota = False
        for line in quota_lines:
            if "[red]" in line:
                has_low_quota = True
                break
            if "remaining" in line:
                try:
                    # Extract number from "Key 1: 10,000 remaining"
                    num_str = line.split(":")[1].split()[0].replace(",", "")
                    if int(num_str) < 1000:
                        has_low_quota = True
                        break
                except (ValueError, IndexError):
                    pass

        if has_low_quota:
            self.console.print(f"[cyan]{header}[/cyan]")
            for line in quota_lines:
                self.console.print(f"[cyan]  {line}[/cyan]")
            self.console.print("")
