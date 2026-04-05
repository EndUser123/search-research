"""Configuration module for dnld_telegram."""

from .media_types import (
    MediaTypeConfig,
    classify_media_type,
    get_media_config,
    reload_config,
    should_download_media_type,
)

__all__ = [
    "MediaTypeConfig",
    "get_media_config",
    "classify_media_type",
    "should_download_media_type",
    "reload_config",
]
