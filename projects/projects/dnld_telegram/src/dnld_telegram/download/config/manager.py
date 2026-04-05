"""
Configuration Manager - Optimal configuration loading with hot reloading,
environment support, and validation.
"""

import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

import toml

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None
import threading
import time

from loguru import logger

try:
    from .schema import AppConfig, ChannelsConfig, Environment, LogLevel, UIMode
except ImportError:
    from schema import AppConfig, ChannelsConfig, Environment, LogLevel, UIMode


if WATCHDOG_AVAILABLE:

    class ConfigFileHandler(FileSystemEventHandler):
        """Handles configuration file changes for hot reloading."""

        def __init__(self, config_manager: "ConfigManager"):
            self.config_manager = config_manager

        def on_modified(self, event):
            if not event.is_directory and event.src_path.endswith(
                (".toml", ".yaml", ".yml")
            ):
                logger.info(f"Configuration file changed: {event.src_path}")
                # Debounce rapid file changes
                time.sleep(0.1)
                self.config_manager.reload()
else:
    ConfigFileHandler = None


class ConfigManager:
    """
    Optimal configuration manager with:
    - Hot reloading
    - Environment overrides
    - Validation
    - Type safety
    - Hierarchical loading
    """

    def __init__(self, config_dir: Path | None = None):
        """Initialize configuration manager."""
        if config_dir is None:
            # Detect config directory relative to this file
            config_dir = Path(__file__).parent

        self.config_dir = Path(config_dir)
        self.app_config: AppConfig | None = None
        self.channels_config: ChannelsConfig | None = None

        # Hot reloading setup
        self.observer: Observer | None = None
        self.hot_reload_enabled = WATCHDOG_AVAILABLE
        self._lock = threading.RLock()

        # Load initial configuration
        self.reload()

        # Start file watching if available
        if self.hot_reload_enabled and WATCHDOG_AVAILABLE:
            self._start_file_watching()

    def reload(self) -> None:
        """Reload all configuration from files."""
        with self._lock:
            try:
                self._load_app_config()
                self._load_channels_config()
                self._validate_all()
                logger.debug("Configuration reloaded successfully")
            except Exception as e:
                logger.error(f"Failed to reload configuration: {e}")

    def _load_app_config(self) -> None:
        """Load main application configuration with environment overrides."""
        # Start with default configuration
        self.app_config = AppConfig()

        # Detect environment
        env_name = os.getenv("TELEGRAM_ENV", "development").lower()
        try:
            environment = Environment(env_name)
            self.app_config.environment = environment
        except ValueError:
            logger.warning(f"Unknown environment '{env_name}', using development")
            environment = Environment.DEVELOPMENT

        # Load base configuration
        app_config_file = self.config_dir / "app.toml"
        if app_config_file.exists():
            config_data = toml.load(app_config_file)
            self._apply_config_data(config_data, self.app_config)

        # Load environment-specific overrides
        env_config_file = self.config_dir / "environments.toml"
        if env_config_file.exists():
            env_data = toml.load(env_config_file)
            if environment.value in env_data:
                env_overrides = env_data[environment.value]
                self.app_config.apply_environment_overrides(env_overrides)
                logger.debug(f"Applied {environment.value} environment overrides")

        # Apply environment variable overrides
        self._apply_env_var_overrides()

    def _load_channels_config(self) -> None:
        """Load channels configuration."""
        channels_file = self.config_dir / "channels.toml"
        if channels_file.exists():
            channels_data = toml.load(channels_file)
            # Handle both flat format and nested format
            if "TELEGRAM_CHANNELS" in channels_data:
                channel_dict = channels_data["TELEGRAM_CHANNELS"]
            elif "channels" in channels_data:
                channel_dict = channels_data["channels"]
            else:
                channel_dict = channels_data

            self.channels_config = ChannelsConfig.from_dict(channel_dict)
        else:
            logger.warning("No channels configuration found")
            self.channels_config = ChannelsConfig()

    def _apply_config_data(self, data: dict[str, Any], config_obj: Any) -> None:
        """Apply configuration data to configuration object."""
        for section_name, section_data in data.items():
            if hasattr(config_obj, section_name) and isinstance(section_data, dict):
                section_obj = getattr(config_obj, section_name)
                for key, value in section_data.items():
                    if hasattr(section_obj, key):
                        # Handle enum conversions
                        field_type = section_obj.__dataclass_fields__[key].type
                        if field_type == LogLevel or (
                            hasattr(field_type, "__origin__")
                            and field_type.__origin__ is LogLevel
                        ):
                            value = (
                                LogLevel(value)
                                if not isinstance(value, LogLevel)
                                else value
                            )
                        elif field_type == UIMode or (
                            hasattr(field_type, "__origin__")
                            and field_type.__origin__ is UIMode
                        ):
                            value = (
                                UIMode(value)
                                if not isinstance(value, UIMode)
                                else value
                            )

                        setattr(section_obj, key, value)

    def _apply_env_var_overrides(self) -> None:
        """Apply environment variable overrides using standard naming."""
        # Environment variable naming: TELEGRAM_<SECTION>_<KEY>
        prefix = "TELEGRAM_"

        for env_key, env_value in os.environ.items():
            if env_key.startswith(prefix) and len(env_key) > len(prefix):
                # Parse TELEGRAM_DOWNLOAD_MAX_CONCURRENT -> ("download", "max_concurrent")
                key_parts = env_key[len(prefix) :].lower().split("_", 1)
                if len(key_parts) == 2:
                    section_name, field_name = key_parts

                    if hasattr(self.app_config, section_name):
                        section_obj = getattr(self.app_config, section_name)
                        if hasattr(section_obj, field_name):
                            # Convert string env var to appropriate type
                            field_type = section_obj.__dataclass_fields__[
                                field_name
                            ].type
                            converted_value = self._convert_env_value(
                                env_value, field_type
                            )
                            setattr(section_obj, field_name, converted_value)
                            logger.debug(
                                f"Applied env override: {section_name}.{field_name} = {converted_value}"
                            )

    def _convert_env_value(self, value: str, target_type) -> Any:
        """Convert string environment variable to target type."""
        if target_type is bool:
            return value.lower() in ("true", "1", "yes", "on")
        elif target_type is int:
            return int(value)
        elif target_type is float:
            return float(value)
        elif target_type == LogLevel or (
            hasattr(target_type, "__origin__") and target_type.__origin__ is LogLevel
        ):
            return LogLevel(value.upper())
        elif target_type == UIMode or (
            hasattr(target_type, "__origin__") and target_type.__origin__ is UIMode
        ):
            return UIMode(value.lower())
        else:
            return value

    def _validate_all(self) -> None:
        """Validate all loaded configuration."""
        if self.app_config:
            app_errors = self.app_config.validate()
            if app_errors:
                error_msg = "App configuration errors:\n" + "\n".join(
                    f"  - {error}" for error in app_errors
                )
                raise ValueError(error_msg)

        if self.channels_config:
            channel_errors = self.channels_config.validate()
            if channel_errors:
                error_msg = "Channel configuration errors:\n" + "\n".join(
                    f"  - {error}" for error in channel_errors
                )
                raise ValueError(error_msg)

    def _start_file_watching(self) -> None:
        """Start watching configuration files for changes."""
        if not WATCHDOG_AVAILABLE:
            logger.info("Watchdog not available - hot reloading disabled")
            self.hot_reload_enabled = False
            return

        try:
            self.observer = Observer()
            handler = ConfigFileHandler(self)
            self.observer.schedule(handler, str(self.config_dir), recursive=False)
            self.observer.start()
            logger.debug(f"Started watching config directory: {self.config_dir}")
        except Exception as e:
            logger.warning(f"Could not start file watching: {e}")
            self.hot_reload_enabled = False

    def stop_watching(self) -> None:
        """Stop file watching."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

    # Public API methods
    def get_app_config(self) -> AppConfig:
        """Get application configuration."""
        if self.app_config is None:
            raise RuntimeError("Configuration not loaded")
        return self.app_config

    def get_channels_config(self) -> ChannelsConfig:
        """Get channels configuration."""
        if self.channels_config is None:
            raise RuntimeError("Channels configuration not loaded")
        return self.channels_config

    def get_channel_config(self, channel_name: str):
        """Get configuration for specific channel."""
        channels = self.get_channels_config()
        if channel_name not in channels.channels:
            raise ValueError(f"Channel '{channel_name}' not found in configuration")
        return channels.channels[channel_name]

    def export_config(self) -> dict[str, Any]:
        """Export current configuration as dictionary."""
        result = {}
        if self.app_config:
            result["app"] = asdict(self.app_config)
        if self.channels_config:
            result["channels"] = {
                name: asdict(config)
                for name, config in self.channels_config.channels.items()
            }
        return result

    def get_effective_config_summary(self) -> str:
        """Get human-readable summary of effective configuration."""
        if not self.app_config:
            return "Configuration not loaded"

        config = self.app_config
        lines = [
            "Telegram Downloader Configuration",
            f"Environment: {config.environment.value}",
            f"Channels Base: {config.paths.channels_base}",
            f"Max Concurrent: {config.download.max_concurrent}",
            f"UI Mode: {config.ui.default_mode.value}",
            f"Log Level: {config.logging.console_level.value}",
            f"Database Sharding: {config.database.shard_threshold_gb}GB threshold",
        ]

        if self.channels_config:
            enabled_channels = self.channels_config.get_enabled_channels()
            lines.append(f"Channels: {len(enabled_channels)} enabled")

        return "\n".join(lines)


# Singleton instance
_config_manager: ConfigManager | None = None
_manager_lock = threading.Lock()


def get_config_manager(config_dir: Path | None = None) -> ConfigManager:
    """Get singleton configuration manager."""
    global _config_manager

    if _config_manager is None:
        with _manager_lock:
            if _config_manager is None:
                _config_manager = ConfigManager(config_dir)

    return _config_manager


def reload_config() -> None:
    """Reload configuration (useful for testing)."""
    global _config_manager
    if _config_manager:
        _config_manager.reload()


def stop_config_watching() -> None:
    """Stop configuration file watching."""
    global _config_manager
    if _config_manager:
        _config_manager.stop_watching()
