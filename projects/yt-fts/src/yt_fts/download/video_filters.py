"""
Video filtering utilities for YouTube downloads.

Provides video classification and filter reason tracking for the download pipeline.
Extracted from download_handler.py for better separation of concerns.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


class VideoFilter:
    """
    Handles video filtering and classification logic.
    
    This class manages:
    - Filter reason tracking (why videos were skipped)
    - Video classification (shorts, scheduled, no subtitles)
    - Filter summary generation for user feedback
    
    Filter Reasons:
        - no_subtitles: Video has no captions available
        - shorts: Video is a YouTube Short
        - scheduled: Video is scheduled for future release
        - unavailable: Video is unavailable/private
        - members_only: Video is members-only content
    """
    
    DISPLAY_NAMES = {
        "no_subtitles": "no cc",
        "shorts": "Shorts",
        "scheduled": "scheduled",
        "unavailable": "unavailable",
        "members_only": "members-only",
    }
    
    def __init__(self) -> None:
        """Initialize the video filter with empty tracking state."""
        self.filter_reasons: dict[str, int] = {
            "no_subtitles": 0,
            "shorts": 0,
            "scheduled": 0,
            "unavailable": 0,
            "members_only": 0,
        }
        self._filtered_video_ids: dict[str, str] = {}
    
    def initialize(self) -> None:
        """Initialize or reset filter reason tracking."""
        self.filter_reasons = {
            "no_subtitles": 0,
            "shorts": 0,
            "scheduled": 0,
            "unavailable": 0,
            "members_only": 0,
        }
        self._filtered_video_ids = {}
    
    def track(self, reason: str, video_id: str) -> None:
        """
        Track a video that was filtered and the reason.
        
        Args:
            reason: One of 'no_subtitles', 'shorts', 'scheduled', 'unavailable', 'members_only'
            video_id: The video ID that was filtered
        """
        if reason in self.filter_reasons:
            self.filter_reasons[reason] += 1
        self._filtered_video_ids[video_id] = reason
    
    def get_summary(self) -> str:
        """
        Get a summary message of why videos were filtered.
        
        Returns:
            String describing filter reasons, or empty string if no filters
        """
        reasons_parts = []
        
        for reason, count in self.filter_reasons.items():
            if count > 0:
                name = self.DISPLAY_NAMES.get(reason, reason)
                reasons_parts.append(f"{count} {name}")
        
        if not reasons_parts:
            return ""
        
        if len(reasons_parts) == 1:
            return reasons_parts[0]
        if len(reasons_parts) == 2:
            return f"{reasons_parts[0]} and {reasons_parts[1]}"
        return ", ".join(reasons_parts[:-1]) + f", and {reasons_parts[-1]}"
    
    def is_short_video(self, video_url: str) -> bool:
        """
        Check if a video URL is a YouTube Short.
        
        Args:
            video_url: The video URL to check
        
        Returns:
            True if the video is a Short
        """
        return "/shorts/" in video_url
    
    def is_scheduled_video(self, info: dict) -> bool:
        """
        Check if a video is scheduled or upcoming.
        
        Args:
            info: yt-dlp info dict for the video
        
        Returns:
            True if the video is scheduled/upcoming
        """
        # Check live_status for upcoming
        live_status = info.get("live_status", "")
        if live_status == "is_upcoming":
            return True
        
        # Check release_timestamp for future datetime
        release_timestamp = info.get("release_timestamp")
        if release_timestamp:
            try:
                release_time = datetime.fromisoformat(
                    release_timestamp.replace("Z", "+00:00")
                )
                if release_time > datetime.now(release_time.tzinfo):
                    return True
            except Exception:
                pass
        
        return False
    
    def has_no_subtitles(self, info: dict) -> bool:
        """
        Check if a video has no subtitles in any language.
        
        Args:
            info: yt-dlp info dict for the video
        
        Returns:
            True if the video has no subtitles (manual or auto)
        """
        subtitles = info.get("subtitles", {})
        auto_captions = info.get("automatic_captions", {})
        return not subtitles and not auto_captions
    
    def get_no_videos_message(self, summary: str | None = None) -> str:
        """
        Get the message to show when no videos could be downloaded.
        
        Args:
            summary: Optional pre-computed filter summary
        
        Returns:
            Message describing why videos were filtered, or empty if no videos were found
        """
        if summary is None:
            summary = self.get_summary()
        
        if summary:
            return f"All new videos were {summary}"
        return ""
    
    def get_result_message(
        self, 
        videos_saved_to_db: int,
        summary: str | None = None
    ) -> str:
        """
        Get the result message based on what was accomplished.
        
        Args:
            videos_saved_to_db: Number of videos successfully saved
            summary: Optional pre-computed filter summary
        
        Returns:
            Result message describing the outcome
        """
        if videos_saved_to_db > 0:
            return "Successfully downloaded channel"
        
        # No videos saved - check why
        if summary is None:
            summary = self.get_summary()
        
        if summary:
            if self.filter_reasons.get("no_subtitles", 0) > 0:
                return "no transcript to store in db"
            return f"all videos filtered ({summary})"
        return "no transcript to store in db"
    
    @property
    def filtered_video_ids(self) -> dict[str, str]:
        """Get the mapping of filtered video IDs to their filter reasons."""
        return self._filtered_video_ids
    
    @property
    def total_filtered(self) -> int:
        """Get the total number of filtered videos."""
        return sum(self.filter_reasons.values())
