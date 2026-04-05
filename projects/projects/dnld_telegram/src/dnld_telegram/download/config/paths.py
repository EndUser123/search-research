"""
Path configuration for dnld_telegram

This module centralizes all path configurations to allow easy relocation
of channel directories and media files.

Now integrated with the optimal configuration system while maintaining
backward compatibility with legacy configuration methods.
"""

import os
from pathlib import Path

import toml

# Import from new configuration system
try:
    from config.integration import (
        get_channel_media_path as get_channel_media_path_new,
    )
    from config.integration import (
        get_channel_path as get_channel_path_new,
    )
    from config.integration import (
        get_channel_temp_path as get_channel_temp_path_new,
    )
    from config.integration import (
        get_channels_base_path as get_channels_base_path_new,
    )
    from config.integration import (
        get_database_path as get_database_path_new,
    )
    from config.integration import (
        list_existing_channels as list_existing_channels_new,
    )
    from config.integration import (
        validate_channels_base_path as validate_channels_base_path_new,
    )

    NEW_CONFIG_AVAILABLE = True
except ImportError:
    NEW_CONFIG_AVAILABLE = False


def _load_config() -> dict:
    """Load configuration from config.toml file."""
    config_path = Path("config.toml")
    if config_path.exists():
        try:
            return toml.load(config_path)
        except Exception:
            pass
    return {}


def get_channels_base_path() -> Path:
    """
    Get the base directory for all channel data.

    Uses optimal configuration system if available, otherwise falls back to legacy methods.

    Priority (highest to lowest):
    1. New configuration system (with environment variable overrides)
    2. CHANNELS_BASE_PATH environment variable (legacy)
    3. paths.channels_base in config.toml (legacy)
    4. Default: "channels"

    Returns:
        Path object for the channels base directory
    """
    # Try new configuration system first
    if NEW_CONFIG_AVAILABLE:
        try:
            return get_channels_base_path_new()
        except Exception:
            pass

    # Legacy fallback methods
    # Check environment variable first
    env_path = os.getenv("CHANNELS_BASE_PATH")
    if env_path:
        return Path(env_path)

    # Check config.toml
    config = _load_config()
    config_path = config.get("paths", {}).get("channels_base")
    if config_path:
        return Path(config_path)

    # Default fallback
    return Path("channels")


def get_channel_path(channel_name: str) -> Path:
    """
    Get the full path for a specific channel's directory.

    Args:
        channel_name: Name of the channel

    Returns:
        Path object for the channel directory
    """
    # Try new configuration system first
    if NEW_CONFIG_AVAILABLE:
        try:
            return get_channel_path_new(channel_name)
        except Exception:
            pass

    # Legacy fallback
    return get_channels_base_path() / channel_name


def get_channel_media_path(channel_name: str) -> Path:
    """
    Get the media directory path for a specific channel.

    Args:
        channel_name: Name of the channel

    Returns:
        Path object for the channel's media directory
    """
    # Try new configuration system first
    if NEW_CONFIG_AVAILABLE:
        try:
            return get_channel_media_path_new(channel_name)
        except Exception:
            pass

    # Legacy fallback
    return get_channel_path(channel_name) / "_media"


def get_channel_temp_path(channel_name: str) -> Path:
    """
    Get the temporary download directory for a specific channel.

    Args:
        channel_name: Name of the channel

    Returns:
        Path object for the channel's temp directory
    """
    # Try new configuration system first
    if NEW_CONFIG_AVAILABLE:
        try:
            return get_channel_temp_path_new(channel_name)
        except Exception:
            pass

    # Legacy fallback
    return get_channel_path(channel_name) / "_temp"


def get_database_path(channel_name: str) -> str:
    """
    Get the database file path for a channel.

    Args:
        channel_name: Name of the channel

    Returns:
        String path to the channel's database file
    """
    # Try new configuration system first
    if NEW_CONFIG_AVAILABLE:
        try:
            return get_database_path_new(channel_name)
        except Exception:
            pass

    # Legacy fallback
    db_dir = get_channel_path(channel_name)
    db_dir.mkdir(parents=True, exist_ok=True)
    return str(db_dir / "telegram_data.db")


# Migration helper functions
def validate_channels_base_path() -> bool:
    """
    Validate that the channels base path exists and is accessible.

    Returns:
        True if path is valid, False otherwise
    """
    # Try new configuration system first
    if NEW_CONFIG_AVAILABLE:
        try:
            return validate_channels_base_path_new()
        except Exception:
            pass

    # Legacy fallback
    try:
        base_path = get_channels_base_path()
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path.exists() and base_path.is_dir()
    except Exception:
        return False


def list_existing_channels() -> list[str]:
    """
    List all existing channel directories in the base path.

    Returns:
        List of channel directory names
    """
    # Try new configuration system first
    if NEW_CONFIG_AVAILABLE:
        try:
            return list_existing_channels_new()
        except Exception:
            pass

    # Legacy fallback
    try:
        base_path = get_channels_base_path()
        if not base_path.exists():
            return []

        return [
            item.name
            for item in base_path.iterdir()
            if item.is_dir() and not item.name.startswith(".")
        ]
    except Exception:
        return []
