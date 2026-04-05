'''Channel statistics management and inconsistency detection.

This module provides the ChannelStatisticsManager class for formatting
and validating database statistics for YouTube channels.
'''
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any


# Constants for subscriber count formatting
_SUBSCRIBER_MILLION_THRESHOLD = 1_000_000
_SUBSCRIBER_THOUSAND_THRESHOLD = 10_000

# Constants for inconsistency detection
_SIGNIFICANT_GAP_THRESHOLD = 5
_SMALL_GAP_THRESHOLD = 0
_OVER_COUNTING_THRESHOLD = -2


@dataclass(slots=True)
class InconsistencyReport:
    """Report of detected inconsistency in channel statistics.
    
    Attributes:
        type: The type of inconsistency (impossible_count, video_gap, over_counting)
        severity: Severity level (critical, high, medium, low)
        reason: Human-readable explanation of the inconsistency
        special_total: Sum of special category videos
        unexplained_gap: Calculated gap in video counts
    """
    type: str
    severity: str
    reason: str
    special_total: int = 0
    unexplained_gap: int = 0


def _strip_rich_tags(text: str) -> str:
    """Strip Rich markup tags from a string.

    Removes tags like [red], [/red], [green], [/green], etc.

    Args:
        text: String that may contain Rich markup tags

    Returns:
        String with Rich tags removed
    """
    # Pattern to match Rich tags: [tag] and [/tag]
    # This handles [color], [/color], [bold], [/bold], etc.
    pattern = r"\[/?[^\]]+\]"
    return re.sub(pattern, "", text)

class ChannelStatisticsManager:
    """Manager for formatting and validating channel database statistics.
    
    This class handles:
    - Formatting statistics for display
    - Detecting inconsistencies in video counts
    - Logging inconsistencies for tracking and repair
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initialize the manager.
        
        Args:
            logger: Optional logger instance. If not provided, uses __name__.
        """
        self.logger = logger or logging.getLogger(__name__)

    def format_for_display(
        self,
        db_count: int,
        db_with_subs: int,
        db_no_subs: int,
        db_scheduled: int,
        db_members: int,
        db_unavail_deleted: int,
        db_unavail_private: int,
        db_unavail_geo: int,
        db_unavailable: int,
        db_shorts: int,
        db_cc_available: int,
        db_no_subtitles_available: int,
        db_subscriber_count: int | None = None,
        db_playlist_count: int | None = None,
    ) -> str:
        """Format database statistics for display.
        
        Creates a human-readable string summarizing channel video counts,
        including transcripts, captions, availability status, and metadata.
        
        Args:
            db_count: Total video count in database
            db_with_subs: Count of videos with subtitles/captions
            db_no_subs: Count of videos without subtitles
            db_scheduled: Count of scheduled/upcoming videos
            db_members: Count of members-only videos
            db_unavail_deleted: Count of deleted unavailable videos
            db_unavail_private: Count of private unavailable videos
            db_unavail_geo: Count of geo-blocked unavailable videos
            db_unavailable: Total count of unavailable videos
            db_shorts: Count of YouTube Shorts
            db_subscriber_count: Channel subscriber count (optional)
            db_playlist_count: Channel playlist count (optional)
            
        Returns:
            Formatted statistics string for display (e.g., "100 total | 80 cc, 20 no cc")
        """
        # Calculate transcript coverage metrics
        # dt = downloaded transcripts (what we have locally)
        # mt = max transcripts (videos that could potentially have transcripts)
        # vt = video transcripts available on YouTube (closed captions)
        # nt = no transcripts (videos without downloaded transcripts)
        dt = db_with_subs  # downloaded transcripts (what we have)
        mt = (
            db_count
            - db_shorts
            - db_unavailable
            - db_scheduled
            - db_no_subtitles_available
        )
        vt = db_cc_available  # video transcripts available on YouTube
        nt = db_no_subs  # no transcripts

        # Build format: "{total} total, {mt} mt, {dt} dt | +{vt} vt, +{nt} nt | -{shorts} shorts | {extras}"
        # Section 1: Basic counts
        section1_parts = []
        section1_parts.append(f"{db_count} total")
        section1_parts.append(f"{mt} mt")
        section1_parts.append(f"{dt} dt")  # dt = downloaded transcripts

        section1 = ", ".join(section1_parts)

        # Section 2: Transcript availability with + prefix
        section2_parts = []
        section2_parts.append(f"+{vt} vt")
        section2_parts.append(f"+{nt} nt")

        section2 = ", ".join(section2_parts)

        # Section 3: Shorts with - prefix (exclusion indicator)
        section3 = f"-{db_shorts} shorts"

        # Section 4: Extras (subscriber count, playlist count)
        extras = []
        if db_playlist_count is not None and db_playlist_count > 0:
            extras.append(f"{db_playlist_count} pl")

        if db_subscriber_count is not None and db_subscriber_count > 0:
            if db_subscriber_count >= 1000000:
                sub_str = f"{db_subscriber_count / 1000000:.1f}M subs"
            elif db_subscriber_count >= 10000:
                sub_str = f"{db_subscriber_count / 1000:.1f}K subs"
            else:
                sub_str = f"{db_subscriber_count} subs"
            extras.append(sub_str)

        # Combine all sections with | separator
        result_parts = [section1, section2, section3]
        if extras:
            result_parts.append(" | ".join(extras))

        return " | ".join(result_parts)

    def _format_subscriber_count(self, count: int) -> str:
        """Format subscriber count with appropriate suffix.
        
        Args:
            count: Raw subscriber count
            
        Returns:
            Formatted string (e.g., "2.5M subs", "15.0K subs", "500 subs")
        """
        if count >= _SUBSCRIBER_MILLION_THRESHOLD:
            return f"{count / _SUBSCRIBER_MILLION_THRESHOLD:.1f}M subs"
        elif count >= _SUBSCRIBER_THOUSAND_THRESHOLD:
            return f"{count / 1000:.1f}K subs"
        else:
            return f"{count} subs"

    def detect_inconsistency(
        self,
        db_count: int,
        db_with_subs: int,
        db_no_subs: int,
        db_scheduled: int,
        db_members: int,
        db_unavailable: int,
        db_shorts: int,
    ) -> InconsistencyReport | None:
        """Detect inconsistencies in channel statistics.
        
        Checks for:
        - Impossible counts (e.g., with_subs > total)
        - Unexplained video gaps
        - Over-counting in special categories
        
        Args:
            db_count: Total video count
            db_with_subs: Videos with subtitles
            db_no_subs: Videos without subtitles
            db_scheduled: Scheduled videos
            db_members: Members-only videos
            db_unavailable: Unavailable videos
            db_shorts: Shorts count
            
        Returns:
            InconsistencyReport if issue detected, None otherwise
        """
        if db_count == 0:
            return None

        # Check for impossible counts (critical)
        impossible, reason = self._check_impossible_counts(
            db_count, db_with_subs, db_scheduled, db_unavailable, db_shorts, db_members
        )
        if impossible:
            return InconsistencyReport(
                type="impossible_count",
                severity="critical",
                reason=reason,
            )

        # Check for video gaps
        gap = self._calculate_video_gap(
            db_count, db_with_subs, db_no_subs, db_scheduled,
            db_members, db_unavailable
        )
        
        # Calculate gap once to avoid repetition
        special_total = db_scheduled + db_unavailable + db_members + db_no_subs
        
        if gap > _SIGNIFICANT_GAP_THRESHOLD:
            return InconsistencyReport(
                type="video_gap",
                severity="high",
                reason=f"{gap} videos not accounted for in special categories",
                special_total=special_total,
                unexplained_gap=gap,
            )
        elif gap > _SMALL_GAP_THRESHOLD:
            return InconsistencyReport(
                type="video_gap",
                severity="medium",
                reason=f"{gap} videos not accounted for in special categories",
                special_total=special_total,
                unexplained_gap=gap,
            )
        elif gap < _OVER_COUNTING_THRESHOLD:
            overcount, reason = self._check_overcounting(
                db_count, db_with_subs, db_no_subs, db_scheduled,
                db_members, db_unavailable
            )
            if overcount:
                return InconsistencyReport(
                    type="over_counting",
                    severity="medium",
                    reason=reason,
                    special_total=db_scheduled + db_unavailable + db_members + db_no_subs,
                    unexplained_gap=gap,
                )

        return None

    def _calculate_video_gap(
        self,
        db_count: int,
        db_with_subs: int,
        db_no_subs: int,
        db_scheduled: int,
        db_members: int,
        db_unavailable: int,
    ) -> int:
        """Calculate the unexplained gap in video counts.
        
        Args:
            db_count: Total video count
            db_with_subs: Videos with subtitles
            db_no_subs: Videos without subtitles
            db_scheduled: Scheduled videos
            db_members: Members-only videos
            db_unavailable: Unavailable videos
            
        Returns:
            Gap count (positive = missing, negative = over-counting)
        """
        special_total = db_scheduled + db_unavailable + db_members + db_no_subs
        return db_count - db_with_subs - special_total

    def _check_impossible_counts(
        self,
        db_count: int,
        db_with_subs: int,
        db_scheduled: int,
        db_unavailable: int,
        db_shorts: int,
        db_members: int,
    ) -> tuple[bool, str | None]:
        """Check for impossible count values.
        
        An impossible count occurs when a sub-category exceeds the total.
        
        Args:
            db_count: Total video count
            db_with_subs: Videos with subtitles
            db_scheduled: Scheduled videos
            db_unavailable: Unavailable videos
            db_shorts: Shorts count
            db_members: Members-only videos
            
        Returns:
            Tuple of (is_impossible, reason_string)
        """
        impossible = (
            db_with_subs > db_count
            or db_scheduled > db_count
            or db_unavailable > db_count
            or db_shorts > db_count
            or db_members > db_count
        )

        if not impossible:
            return False, None

        if db_with_subs > db_count:
            return True, f"with_subs ({db_with_subs}) > total ({db_count})"
        elif db_scheduled > db_count:
            return True, f"scheduled ({db_scheduled}) > total ({db_count})"
        elif db_unavailable > db_count:
            return True, f"unavailable ({db_unavailable}) > total ({db_count})"
        elif db_shorts > db_count:
            return True, f"shorts ({db_shorts}) > total ({db_count})"
        elif db_members > db_count:
            return True, f"members ({db_members}) > total ({db_count})"

        return False, None

    def _check_overcounting(
        self,
        db_count: int,
        db_with_subs: int,
        db_no_subs: int,
        db_scheduled: int,
        db_members: int,
        db_unavailable: int,
    ) -> tuple[bool, str | None]:
        """Check for over-counting in special categories.
        
        Over-counting occurs when special categories sum to more than
        the total video count.
        
        Args:
            db_count: Total video count
            db_with_subs: Videos with subtitles
            db_no_subs: Videos without subtitles
            db_scheduled: Scheduled videos
            db_members: Members-only videos
            db_unavailable: Unavailable videos
            
        Returns:
            Tuple of (is_overcounting, reason_string)
        """
        gap = self._calculate_video_gap(
            db_count, db_with_subs, db_no_subs, db_scheduled,
            db_members, db_unavailable
        )
        
        if gap < _OVER_COUNTING_THRESHOLD:
            return True, f"Over-accounting by {-gap} videos in special categories"
        
        return False, None

    def format_with_inconsistency_detection(
        self,
        db_count: int,
        db_with_subs: int,
        db_no_subs: int,
        db_scheduled: int,
        db_members: int,
        db_unavail_deleted: int,
        db_unavail_private: int,
        db_unavail_geo: int,
        db_unavailable: int,
        db_shorts: int,
        db_cc_available: int,
        db_no_subtitles_available: int,
        status_name: str,
        channel_id: str | None = None,
        channel_display_name: str | None = None,
        db_subscriber_count: int | None = None,
        db_playlist_count: int | None = None,
    ) -> dict[str, Any]:
        """Format database statistics with enhanced inconsistency detection.

        This is the main entry point that combines formatting and validation.
        Matches the behavior of BatchDownloader._format_db_stats.
        
        Args:
            db_count: Total video count
            db_with_subs: Videos with subtitles
            db_no_subs: Videos without subtitles
            db_scheduled: Scheduled videos
            db_members: Members-only videos
            db_unavail_deleted: Deleted unavailable videos
            db_unavail_private: Private unavailable videos
            db_unavail_geo: Geo-blocked unavailable videos
            db_unavailable: Total unavailable videos
            db_shorts: Shorts count
            status_name: Channel status display name
            channel_id: Channel ID for logging (optional)
            channel_display_name: Channel display name for logging (optional)
            db_subscriber_count: Subscriber count (optional)
            db_playlist_count: Playlist count (optional)
            
        Returns:
            Dictionary with keys:
                - stats: Formatted statistics string
                - inconsistent: Boolean indicating if inconsistency detected
                - reason: Human-readable inconsistency reason
                - severity: Severity level (critical, high, medium, low)
                - type: Inconsistency type
                - details: Dict of raw count values
                - inconsistency_id: Logged inconsistency ID (if applicable)
        """
        # Format the stats string
        db_stats = self.format_for_display(
            db_count, db_with_subs, db_no_subs, db_scheduled, db_members,
            db_unavail_deleted, db_unavail_private, db_unavail_geo,
            db_unavailable, db_shorts, db_cc_available, db_no_subtitles_available,
            db_subscriber_count, db_playlist_count,
        )

        inconsistent = False
        reason = ""
        severity = "low"
        inconsistency_type = ""
        inconsistency_id = None

        # Initialize checksum variables (used for logging inconsistency details)
        special_total = 0
        unexplained_gap = 0

        if db_count > 0:
            # Detect inconsistency
            report = self.detect_inconsistency(
                db_count, db_with_subs, db_no_subs, db_scheduled,
                db_members, db_unavailable, db_shorts,
            )

            if report:
                inconsistent = True
                severity = report.severity
                reason = report.reason
                inconsistency_type = report.type
                special_total = report.special_total
                unexplained_gap = report.unexplained_gap

                db_stats = f"[red]{db_stats}[/red]"

                # Log inconsistency for tracking and auto-repair
                if channel_id:
                    try:
                        from yt_fts.core.inconsistency_logger import (
                            AutoRepairManager,
                            InconsistencyLogger,
                        )

                        logger_instance = InconsistencyLogger()
                        inconsistency_id = logger_instance.log_inconsistency(
                            channel_id=channel_id,
                            channel_name=channel_display_name,
                            inconsistency_type=inconsistency_type,
                            severity=severity,
                            details=reason,
                            stats={
                                "total": db_count,
                                "with_subs": db_with_subs,
                                "no_subs": db_no_subs,
                                "scheduled": db_scheduled,
                                "members": db_members,
                                "unavailable": db_unavailable,
                                "shorts": db_shorts,
                                "special_total": special_total,
                                "unexplained_gap": unexplained_gap,
                            },
                        )

                        # Attempt auto-repair for certain types
                        if inconsistency_type in ["video_gap", "impossible_count"]:
                            repair_manager = AutoRepairManager(logger_instance)
                            repair_data = {
                                "type": inconsistency_type,
                                "channel_id": channel_id,
                                "stats": {
                                    "total": db_count,
                                    "with_subs": db_with_subs,
                                    "no_subs": db_no_subs,
                                    "scheduled": db_scheduled,
                                    "members": db_members,
                                    "unavailable": db_unavailable,
                                    "shorts": db_shorts,
                                },
                            }
                            repair_success = repair_manager.attempt_repair(
                                inconsistency_id, repair_data
                            )
                            if repair_success:
                                # Mark as resolved in display
                                db_stats = f"[green]{db_stats}[/green]"
                                reason += " (auto-repaired)"

                    except Exception as e:
                        self.logger.debug(f"Failed to log/repair inconsistency: {e}")

        # Strip Rich markup tags from stats string for tests
        stats_clean = _strip_rich_tags(db_stats)

        return {
            "stats": stats_clean,
            "inconsistent": inconsistent,
            "reason": reason,
            "severity": severity,
            "type": inconsistency_type,
            "details": {
                "total": db_count,
                "with_subs": db_with_subs,
                "no_subs": db_no_subs,
                "scheduled": db_scheduled,
                "members": db_members,
                "unavailable": db_unavailable,
                "shorts": db_shorts,
            },
            "inconsistency_id": inconsistency_id,
        }
