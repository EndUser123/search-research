"""
Adaptive Quota Management Strategy

Bidirectional strategy:
- High quota: Use API when it saves time (avoid slow yt-dlp metadata)
- Low quota: Conserve API (only use when time savings are significant)

Strategy Modes:
- conservative: yt-dlp for metadata (slow but free), skip transcript API
- balanced: API for metadata (fast), yt-dlp for transcripts
- aggressive: API for everything (fastest)
"""

from dataclasses import dataclass
from enum import Enum

from yt_fts.config import CONSERVATIVE_THRESHOLD, DAILY_QUOTA_LIMIT


class QuotaMode(str, Enum):
    """Quota usage strategy mode."""
    CONSERVATIVE = "conservative"  # Save quota: yt-dlp metadata, no transcript API
    BALANCED = "balanced"  # API metadata only, yt-dlp for transcripts
    AGGRESSIVE = "aggressive"  # API for everything


@dataclass
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
    aggressive_threshold: float = 0.72   # Above 72%: use freely (3+ days remaining at peak)
    # Estimated quota costs per operation
    api_cost_per_video_metadata: int = 100  # ~100 quota per video metadata fetch
    api_cost_per_transcript: int = 200      # ~200 quota per transcript
    api_cost_per_channel: int = 100         # ~100 quota per channel list


class QuotaStrategy:
    """
    Adaptive quota management for deciding when to use API vs yt-dlp.

    The strategy automatically adjusts based on remaining quota:
    - Conservative mode: Use yt-dlp (slow but free)
    - Balanced mode: API for metadata (fast), yt-dlp for transcripts
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

    def should_use_api_for_metadata(self, db_count: int = 0) -> bool:
        """
        Decide whether to use API for fetching video metadata.

        Args:
            db_count: Number of existing videos in database for this channel.
                     Used to estimate yt-dlp cost (more videos = slower).

        Returns:
            True if API should be used, False if yt-dlp should be used.
        """
        mode = self.mode

        if mode == QuotaMode.AGGRESSIVE:
            # High quota: Always use API for metadata (much faster)
            return True
        if mode == QuotaMode.BALANCED:
            # Medium quota: Use API for metadata, but not for transcripts
            return True
        # CONSERVATIVE
        # Low quota: Only use API if yt-dlp would be very slow
        # Use API if channel has many videos (>50) since yt-dlp is slow
        return (db_count or 0) > 50

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
            # Medium quota: Use yt-dlp for transcripts (save quota)
            return False
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
