"""
Configuration for batch download operations.

Consolidates 41 parameters into a single configuration object.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class BatchDownloadConfig:
    """Configuration for batch download operations.

    This dataclass consolidates the 41 parameters of batch_download into
    a single, structured configuration object for better maintainability.
    """

    # === Input/Output ===
    input_file: str | None
    import_file: str | None = None
    import_only: bool = False
    dry_run: bool = False
    output_file: str | None = None

    # === Download Settings ===
    jobs: int = 1
    language: str = "en"
    cookies_from_browser: str = ""
    delay: float = 60.0
    max_retries: int = 3

    # === Error Handling ===
    continue_on_error: bool = False
    no_fail_fast: bool = False

    # === Timing ===
    no_skip_initial_wait: bool = False
    time_per_video: float = 600.0
    time_per_channel: float = 3600.0
    time_per_batch: float = 7200.0

    # === Limits ===
    limit: int = 0
    videos_download_per_channel: int = 0
    channels_download_per_batch: int = 0
    videos_download_per_batch: int = 0

    # === Display/UI ===
    tui: bool = False
    export_report: str = ""
    display_plugin: str = "default"
    rich_progress: bool = False
    rich_display: str = "default"
    output_format: str = "default"
    import_progress: bool = False

    # === Legacy Display Flags (for compatibility) ===
    richo: bool = False  # Old rich formatter
    rich: bool = False   # New rich layout
    rich_1: bool = False  # Alias for rich
    simple: bool = False
    fzf: bool = False

    # === Quota Strategy ===
    quota_daily: int = 10000
    quota_conservative_pct: float = 0.8
    quota_aggressive_pct: float = 1.2

    # === Phase 2 (Backfill) ===
    use_phase2: bool = False
    phase2_batch_size: int = 100
    auto_backfill: bool = False
    freshness_hours: int = 24
    use_cache: bool = True

    # === Transcription ===
    transcribe_audio_only: bool = True
    whisper_model: str = "base"

    # === Parallel Processing ===
    parallel_workers: int = 1

    @classmethod
    def from_click_args(cls, **kwargs: Any) -> "BatchDownloadConfig":
        """Create config from Click command arguments.

        This provides compatibility with the existing Click interface
        while transitioning to the dataclass-based approach.
        """
        # Filter out None values to use defaults
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return cls(**filtered_kwargs)

    def get_effective_output_format(self) -> str:
        """Get the effective output format, handling legacy flags."""
        # Legacy flags override output_format
        if self.simple:
            return "simple"
        if self.fzf:
            return "fzf"
        if self.rich or self.rich_1 or self.richo:
            return "rich"
        return self.output_format

    def get_rich_mode(self) -> Literal["new", "old", None] | None:
        """Determine which Rich mode to use."""
        if self.rich_1 or self.rich:
            return "new"
        if self.richo:
            return "old"
        return None

    def should_use_parallel(self) -> bool:
        """Determine if parallel processing should be used."""
        return self.parallel_workers > 1

    def get_fail_fast(self) -> bool:
        """Get fail-fast setting."""
        return not self.no_fail_fast

    def get_skip_initial_delay(self) -> bool:
        """Get skip initial delay setting."""
        return not self.no_skip_initial_wait

    def is_metadata_only_mode(self) -> bool:
        """Check if this is metadata-only mode (no actual downloads)."""
        return self.videos_download_per_channel == 0 and self.delay == 60.0
