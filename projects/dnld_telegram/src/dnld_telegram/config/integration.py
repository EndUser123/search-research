"""
Configuration Integration Layer - Bridges new ConfigManager to existing codebase.

This module provides compatibility functions that allow existing code to use
the new optimal ConfigManager while maintaining backward compatibility.
"""

from pathlib import Path
from typing import Any

try:
    from .manager import get_config_manager
except ImportError:
    from manager import get_config_manager


class ConfigurationBridge:
    """
    Bridge class that provides legacy-compatible interfaces while using
    the new ConfigManager underneath.
    """

    def __init__(self):
        # Initialize config manager with the project config directory
        # Path is: src/dnld_telegram/config/integration.py
        # We want: config/ (3 levels up from this file)
        config_dir = Path(__file__).resolve().parents[3] / "config"
        self._config_manager = get_config_manager(config_dir)

    # Legacy channel loading functions (for src/download/config/settings.py)
    def get_channels_dict(self) -> dict[str, int]:
        """
        Get channels in the legacy format expected by existing code.
        Returns: Dict[channel_name, chat_id]
        """
        channels_config = self._config_manager.get_channels_config()
        return {
            name: config.chat_id
            for name, config in channels_config.get_enabled_channels().items()
        }

    def load_telegram_channels(self) -> dict[str, int]:
        """Legacy function name compatibility."""
        return self.get_channels_dict()

    # Legacy path functions (for src/download/config/paths.py)
    def get_channels_base_path(self) -> Path:
        """Get channels base path from new configuration system."""
        app_config = self._config_manager.get_app_config()
        return Path(app_config.paths.channels_base)

    def get_channel_path(self, channel_name: str) -> Path:
        """Get channel directory path."""
        app_config = self._config_manager.get_app_config()
        return app_config.paths.get_channel_path(channel_name)

    def get_channel_media_path(self, channel_name: str) -> Path:
        """Get channel media directory path."""
        app_config = self._config_manager.get_app_config()
        return app_config.paths.get_channel_media_path(channel_name)

    def get_channel_temp_path(self, channel_name: str) -> Path:
        """Get channel temp directory path."""
        app_config = self._config_manager.get_app_config()
        return app_config.paths.get_channel_temp_path(channel_name)

    def get_database_path(self, channel_name: str) -> str:
        """Get database file path for channel."""
        app_config = self._config_manager.get_app_config()
        return str(app_config.paths.get_database_path(channel_name))

    # Additional utilities
    def get_download_config(self) -> dict[str, Any]:
        """Get download configuration as dictionary."""
        app_config = self._config_manager.get_app_config()
        return {
            "max_concurrent": app_config.download.max_concurrent,
            "connection_timeout": app_config.download.connection_timeout,
            "retry_attempts": app_config.download.retry_attempts,
            "verify_downloads": app_config.download.verify_downloads,
        }

    def get_logging_config(self) -> dict[str, Any]:
        """Get logging configuration as dictionary."""
        app_config = self._config_manager.get_app_config()
        return {
            "console_level": app_config.logging.console_level.value,
            "file_level": app_config.logging.file_level.value,
            "max_size_mb": app_config.logging.max_size_mb,
            "backup_count": app_config.logging.backup_count,
            "format": app_config.logging.format,
        }

    def get_ui_config(self, mode: str | None = None) -> dict[str, Any]:
        """Get UI configuration, optionally overridden by mode."""
        app_config = self._config_manager.get_app_config()
        ui_config = {
            "default_mode": app_config.ui.default_mode.value,
            "fallback_mode": app_config.ui.fallback_mode.value,
            "show_speed": app_config.ui.show_speed,
            "show_eta": app_config.ui.show_eta,
            "show_file_progress": app_config.ui.show_file_progress,
            "update_frequency": app_config.ui.update_frequency,
        }

        # Override default mode if specified
        if mode:
            ui_config["default_mode"] = mode

        return ui_config

    def get_environment(self) -> str:
        """Get current environment setting."""
        app_config = self._config_manager.get_app_config()
        return app_config.environment.value


# Global bridge instance for legacy compatibility
_bridge_instance: ConfigurationBridge | None = None


def get_config_bridge() -> ConfigurationBridge:
    """Get singleton configuration bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = ConfigurationBridge()
    return _bridge_instance


# Legacy compatibility functions that existing code can import
def get_channels() -> dict[str, int]:
    """Legacy function for src/download/config/settings.py"""
    return get_config_bridge().get_channels_dict()


def get_channels_base_path() -> Path:
    """Legacy function for src/download/config/paths.py"""
    return get_config_bridge().get_channels_base_path()


def get_channel_path(channel_name: str) -> Path:
    """Legacy function for src/download/config/paths.py"""
    return get_config_bridge().get_channel_path(channel_name)


def get_channel_media_path(channel_name: str) -> Path:
    """Legacy function for src/download/config/paths.py"""
    return get_config_bridge().get_channel_media_path(channel_name)


def get_channel_temp_path(channel_name: str) -> Path:
    """Legacy function for src/download/config/paths.py"""
    return get_config_bridge().get_channel_temp_path(channel_name)


def get_database_path(channel_name: str) -> str:
    """Legacy function for src/download/config/paths.py"""
    return get_config_bridge().get_database_path(channel_name)


def validate_channels_base_path() -> bool:
    """Validate that the channels base path exists and is accessible."""
    try:
        base_path = get_channels_base_path()
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path.exists() and base_path.is_dir()
    except Exception:
        return False


def list_existing_channels() -> list[str]:
    """List all existing channel directories in the base path."""
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


# Configuration getter for main application
def get_config_manager(config_dir: Path | None = None):
    """Get the configuration manager (re-export for convenience)."""
    try:
        from .manager import get_config_manager as _get_config_manager
    except ImportError:
        from manager import get_config_manager as _get_config_manager

    # If no config_dir provided, use the project config directory
    if config_dir is None:
        config_dir = Path(__file__).resolve().parent / "config"
    return _get_config_manager(config_dir)
