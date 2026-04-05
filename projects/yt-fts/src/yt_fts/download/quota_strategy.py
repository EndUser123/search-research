"""
Adaptive Quota Management Strategy

Bidirectional strategy:
- High quota: Use API when it saves time (avoid slow yt-dlp metadata)
- Low quota: Conserve API (only use when time savings are significant)

Strategy Modes:
- conservative: yt-dlp for everything (save quota)
- balanced: API for transcripts (fast), yt-dlp for metadata
- aggressive: API for everything (fastest)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from yt_fts.config import CONSERVATIVE_THRESHOLD, DAILY_QUOTA_LIMIT


class QuotaMode(str, Enum):
    """Quota usage strategy mode."""

    CONSERVATIVE = "conservative"  # Save quota: yt-dlp for everything
    BALANCED = "balanced"  # API for transcripts, yt-dlp for metadata
    AGGRESSIVE = "aggressive"  # API for everything


@dataclass(slots=True)
class QuotaConfig:
    """Configuration for quota-based strategy.

    Thresholds are data-driven based on actual PEAK usage analysis:
    - Peak: 4,821 units/day (24% of quota)
    - At 72% remaining: ~3 days of quota at peak usage rate
    - At 24% remaining: ~1 day of quota at peak usage rate
    """

    daily_quota: int = DAILY_QUOTA_LIMIT
    # Thresholds as percentages of remaining quota (peak-based)
    conservative_threshold: float = CONSERVATIVE_THRESHOLD
    aggressive_threshold: float = (
        0.72  # Above 72%: use freely (3+ days remaining at peak)
    )
    # Actual quota costs per operation (YouTube Data API v3)
    api_cost_per_video_metadata: int = (
        1  # 1 quota per API call (fetches up to 50 videos)
    )
    api_cost_per_transcript: int = 1  # 1 quota per transcript request
    api_cost_per_channel: int = 1  # 1 quota per channel info request


class QuotaStrategy:
    """
    Adaptive quota management for deciding when to use API vs yt-dlp.

    The strategy automatically adjusts based on remaining quota:
    - Conservative mode: yt-dlp for everything (save quota)
    - Balanced mode: API for transcripts (fast), yt-dlp for metadata
    - Aggressive mode: API for everything (fastest)
    """

    def __init__(
        self,
        config: QuotaConfig | None = None,
        quota_used: int = 0,
    ):
        self.config = config or QuotaConfig()
        self.quota_used = quota_used

    @property
    def remaining(self) -> int:
        """Remaining quota units."""
        return max(0, self.config.daily_quota - self.quota_used)

    @property
    def remaining_pct(self) -> float:
        """Remaining quota as percentage (0.0 to 1.0)."""
        if self.config.daily_quota == 0:
            return 0.0
        return self.remaining / self.config.daily_quota

    @property
    def mode(self) -> QuotaMode:
        """Current strategy mode based on remaining quota."""
        if self.remaining_pct < self.config.conservative_threshold:
            return QuotaMode.CONSERVATIVE
        if self.remaining_pct < self.config.aggressive_threshold:
            return QuotaMode.BALANCED
        return QuotaMode.AGGRESSIVE

    def update(self, quota_used: int) -> None:
        """Update quota used."""
        self.quota_used = quota_used

    def should_use_api_for_metadata(
        self,
        db_count: int = 0,
        db_with_subs: int = 0,
        db_no_subs: int = 0,
        context: str = "metadata_only",
    ) -> tuple[bool, str]:
        """
        SMART DECISION: Choose between API and yt-dlp based on efficiency analysis.

        REAL API COSTS: 1 quota per API call (fetches up to 50 videos).
        Effective cost: ~0.02 quota per video when batched efficiently.

        Args:
            db_count: Number of existing videos in database for this channel.
            db_with_subs: Number of videos with transcripts.
            db_no_subs: Number of videos without transcripts.
            context: Usage context - "metadata_only", "gap_fill", "new_channel", "download_needed"

        Returns:
            tuple: (use_api, reason) - API recommendation with explanation
        """
        mode = self.mode

        # Calculate channel completeness ratio
        total_videos = db_count or 0
        missing_videos = db_no_subs or 0

        if total_videos > 0:
            completeness_ratio = (db_with_subs or 0) / total_videos
            needs_more_transcripts = completeness_ratio < 0.5  # Less than 50% complete
        else:
            needs_more_transcripts = True  # New channel
            missing_videos = 50  # Assume new channels have many videos

        # SMALL GAPS: yt-dlp often more efficient (no API round-trip overhead)
        if missing_videos <= 3:
            if context == "download_needed":
                return (
                    False,
                    f"Small gap ({missing_videos} videos) - yt-dlp more efficient for downloads",
                )
            if mode == QuotaMode.CONSERVATIVE:
                return False, f"Conserve quota for small gap ({missing_videos} videos)"

        # MEDIUM GAPS: Depends on context and quota availability
        if missing_videos <= 10:
            if context == "new_channel":
                return (
                    True,
                    f"New channel bulk fetch ({missing_videos} videos) - API efficient",
                )
            if mode == QuotaMode.AGGRESSIVE:
                return (
                    True,
                    f"Medium gap ({missing_videos} videos) with high quota - use API",
                )
            if context == "gap_fill" and mode == QuotaMode.BALANCED:
                return (
                    True,
                    f"Gap fill ({missing_videos} videos) - API prevents redundant yt-dlp calls",
                )

        # LARGE GAPS: API clearly wins for bulk operations
        if missing_videos > 10:
            return True, f"Large gap ({missing_videos} videos) - API batch efficiency"

        # COMPLETENESS-BASED DECISIONS
        if mode == QuotaMode.AGGRESSIVE:
            # High quota: Use API for ANY missing videos (cost is negligible)
            if missing_videos >= 1:
                return (
                    True,
                    "Aggressive mode: API for any gaps (cost: ~0.02 quota/video)",
                )

        if mode == QuotaMode.BALANCED:
            # Medium quota: Smart decisions based on need
            if needs_more_transcripts and missing_videos >= 5:
                return (
                    True,
                    "Balanced mode: API for incomplete channels needing transcripts",
                )
            if context == "metadata_only" and missing_videos >= 1:
                return True, "Balanced mode: API efficient for metadata-only operations"
            return False, "Balanced mode: yt-dlp for complete channels or small gaps"

        # CONSERVATIVE mode: Very selective API usage
        if needs_more_transcripts and missing_videos >= 8:
            return (
                True,
                f"Conservative mode: API only for significant gaps ({missing_videos} videos)",
            )
        return False, "Conservative mode: yt-dlp to preserve quota for critical needs"

    def should_use_api_for_transcript(self, video_count: int = 1) -> bool:
        """
        Decide whether to use API for fetching transcripts.

        Args:
            video_count: Number of transcripts to fetch.

        Returns:
            True if API should be used, False if yt-dlp should be used.
        """
        mode = self.mode

        if mode == QuotaMode.AGGRESSIVE:
            # High quota: Use API for transcripts
            return True
        if mode == QuotaMode.BALANCED:
            # Medium quota: Prioritize transcripts over metadata, use API
            return True
        # CONSERVATIVE
        # Low quota: Never use API for transcripts
        return False

    def estimate_cost(
        self,
        channels: int = 0,
        videos_metadata: int = 0,
        transcripts: int = 0,
    ) -> int:
        """Estimate quota cost for planned operations."""
        cost = 0
        cost += channels * self.config.api_cost_per_channel
        cost += videos_metadata * self.config.api_cost_per_video_metadata
        cost += transcripts * self.config.api_cost_per_transcript
        return cost

    def can_afford(
        self,
        channels: int = 0,
        videos_metadata: int = 0,
        transcripts: int = 0,
    ) -> bool:
        """Check if remaining quota can afford planned operations."""
        cost = self.estimate_cost(channels, videos_metadata, transcripts)
        return self.remaining >= cost

    def get_status_message(self) -> str:
        """Get human-readable status message."""
        mode_symbol = {
            QuotaMode.CONSERVATIVE: "🟡",
            QuotaMode.BALANCED: "🟢",
            QuotaMode.AGGRESSIVE: "",
        }
        return (
            f"{mode_symbol[self.mode]} {self.mode.value.upper()} mode | "
            f"{self.quota_used:,}/{self.config.daily_quota:,} used | "
            f"{self.remaining:,} remaining ({self.remaining_pct:.1%})"
        )


def create_quota_strategy(
    daily_quota: int = DAILY_QUOTA_LIMIT,
    conservative_pct: float = 0.24,
    aggressive_pct: float = 0.72,
    quota_used: int = 0,
) -> QuotaStrategy:
    """
    Factory function to create a QuotaStrategy with custom thresholds.

    Args:
        daily_quota: Total daily API quota (default: 40000)
        conservative_pct: Threshold below which to conserve quota (default: 0.24 = 24%)
        aggressive_pct: Threshold above which to use API freely (default: 0.72 = 72%)
        quota_used: Current quota used (default: 0)

    Returns:
        Configured QuotaStrategy instance
    """
    config = QuotaConfig(
        daily_quota=daily_quota,
        conservative_threshold=conservative_pct,
        aggressive_threshold=aggressive_pct,
    )
    return QuotaStrategy(config=config, quota_used=quota_used)
