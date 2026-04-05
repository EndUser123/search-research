
from __future__ import annotations
"""State-based video discovery system."""

from yt_fts.discovery.state_detection import (
    ChannelState,
    DiscoveryMethod,
    detect_channel_state,
    transition_strategy,
    steady_state_strategy,
    recovery_strategy,
    get_download_queue,
)

from yt_fts.discovery.video_classifier import (
    VideoType,
    classify_video,
    is_short_video,
    is_scheduled_video,
    has_no_subtitles,
)

__all__ = [
    # State detection
    'ChannelState',
    'DiscoveryMethod',
    'detect_channel_state',
    'transition_strategy',
    'steady_state_strategy',
    'recovery_strategy',
    'get_download_queue',
    # Video classification
    'VideoType',
    'classify_video',
    'is_short_video',
    'is_scheduled_video',
    'has_no_subtitles',
]


