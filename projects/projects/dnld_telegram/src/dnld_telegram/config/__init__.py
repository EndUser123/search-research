"""
Configuration package for optimal Telegram downloader configuration management.

This package provides:
- Schema-driven configuration with type safety
- Hot reloading with file system monitoring
- Environment-specific overrides
- Legacy compatibility layer
"""

# Re-export main configuration functions for easy access
try:
    from .integration import (
        get_channels,
        get_channels_base_path,
        get_config_bridge,
    )
    from .manager import get_config_manager
    from .schema import AppConfig, ChannelsConfig, Environment, LogLevel, UIMode

    # Make commonly used functions available at package level
    __all__ = [
        "get_config_manager",
        "get_config_bridge",
        "get_channels",
        "get_channels_base_path",
        "AppConfig",
        "ChannelsConfig",
        "Environment",
        "LogLevel",
        "UIMode",
    ]

except ImportError:
    # If there are import issues, don't break the package
    __all__ = []
