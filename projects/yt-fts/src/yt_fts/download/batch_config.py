"""
Batch download configuration.

Encapsulates all configuration parameters for batch download operations,
reducing parameter passing complexity and improving maintainability.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BatchDownloadConfig:
    """Configuration for batch download operations.

    This dataclass encapsulates all 38 parameters from the batch_download
    Click command, providing a single object to pass through the system.
    """

    # Input options
    input_file: str | None = None
    import_file: str | None = None
    import_only: bool = False
    dry_run: bool = False
    output_file: str | None = None

    # Download options
    jobs: int = 2
    language: str = "en"
    cookies_from_browser: str | None = None
    no_cookies: bool = False
    delay: float = 60.0
    max_retries: int = 3
    continue_on_error: bool = False
    no_fail_fast: bool = False
    no_skip_initial_wait: bool = False

    # Display options
    tui: bool = False
    export_report: str = "text"
    limit: int = 0
    richo: bool = False
    rich: bool = False
    rich_1: bool = False
    simple: bool = False
    fzf: bool = False
    output_format: str = "rich"
    import_progress: bool = False

    # Parallel processing
    parallel_workers: int = 4
    rich_progress: bool = True
    rich_display: str = "auto"
    video_jobs: int | None = None
    no_auto_adjust_video_jobs: bool = False

    # Auto-backfill options
    auto_backfill: bool = False
    freshness_hours: int = 24
    use_cache: bool = True

    # Per-batch/channel limits
    videos_download_per_channel: int = 0
    channels_download_per_batch: int = 0
    videos_download_per_batch: int = 0

    # Quota management
    quota_daily: int = 10000
    quota_conservative_pct: float = 0.8
    quota_aggressive_pct: float = 1.2
    use_phase2: bool = False
    phase2_batch_size: int = 50

    # Transcription options
    whisper_model: str = "base"
    keep_audio: bool = False

    # Timeouts
    time_per_video: float = 300.0
    time_per_channel: float = 1800.0
    time_per_batch: float = 3600.0

    # Display plugin
    display_plugin: str = "default"

    # Runtime state (not from CLI parameters)
    from_database_mode: bool = False
    quiet_mode: bool = False
    rich_mode: str | None = None  # None, 'new', 'old'

    @staticmethod
    def from_click_params(**kwargs) -> "BatchDownloadConfig":
        """Create config from Click command parameters.

        This method provides a clean way to construct the config object
        from the 38 Click parameters.
        """
        # Filter out None values for cleaner config
        filtered = {k: v for k, v in kwargs.items() if v is not None}
        return BatchDownloadConfig(**filtered)

    def get_video_jobs_value(self) -> int:
        """Get the effective video_jobs value, with auto-adjustment logic."""
        if self.video_jobs is not None:
            return self.video_jobs
        if self.no_auto_adjust_video_jobs:
            return self.jobs
        # Auto-adjust is enabled by default
        return 2

    def should_use_rich(self) -> bool:
        """Determine if Rich display should be used."""
        return self.rich or self.rich_1 or self.richo

    def get_effective_delay(self) -> float:
        """Get the effective delay, accounting for metadata-only mode."""
        # Metadata-only mode: no rate limit, only daily quota
        if self.videos_download_per_channel == 0 and self.delay == 60.0:
            return 0.0
        return self.delay


# ===== BATCH DOWNLOADER CONFIG DATACLASSES =====
# Refactor: BatchDownloader constructor from 29 params to 5 configs

from typing import Any


@dataclass(frozen=True)
class ExecutionConfig:
    """Configuration for parallel execution behavior."""
    jobs: int = 2
    language: str = "en"
    cookies_from_browser: str | None = None
    delay_between_channels: float = 3.0
    max_retries: int = 3
    continue_on_error: bool = True

    def __post_init__(self):
        """Validate execution parameters."""
        if not 1 <= self.jobs <= 128:
            raise ValueError(f"jobs must be 1-128, got {self.jobs}")
        if self.delay_between_channels < 0:
            raise ValueError(f"delay_between_channels must be non-negative")


@dataclass(frozen=True)
class LimitsConfig:
    """Configuration for execution limits and timeouts."""
    time_per_channel: float | None = None
    time_per_video: float | None = None
    time_per_batch: float | None = None
    max_videos: int | None = None
    min_saved: int | None = None
    target_downloads: int | None = None
    videos_download_per_batch: int | None = None


@dataclass(frozen=False, slots=True)
class UIConfig:
    """Configuration for user interface display."""
    rich_mode: str | None = None
    display_plugin: str | None = None
    suppress_verbose: bool = False


@dataclass(frozen=True)
class ContentConfig:
    """Configuration for content filtering and quotas."""
    auto_backfill: bool = False
    dry_run: bool = False
    freshness_hours: int = 6
    quota_strategy: Any = None
    min_saved: int | None = None
    target_downloads: int | None = None
    videos_download_per_batch: int | None = None
    suppress_quota_print: bool = False


@dataclass(frozen=True)
class TranscriptConfig:
    """Configuration for transcript generation."""
    whisper_model: str = "base"
    keep_audio: bool = False
