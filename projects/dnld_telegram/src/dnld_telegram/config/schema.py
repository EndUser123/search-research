"""
Configuration schema and validation for Telegram Downloader.
Defines the complete configuration structure with types and validation.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class UIMode(str, Enum):
    TQDM = "tqdm"
    SIMPLE = "simple"
    RICH = "rich"
    TEXTUAL = "textual"
    ALIVE = "alive"
    PANELED = "paneled"
    QUIET = "quiet"
    CLEAN = "clean"
    PRODUCTION = "production"


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class PathsConfig:
    """Path configuration with automatic resolution and validation."""

    channels_base: str = "channels"
    temp_base: str | None = None
    media_base: str | None = None
    database_base: str | None = None
    logs_base: str = "logs"

    def __post_init__(self):
        """Resolve relative paths and apply defaults."""
        # Resolve channels_base first (can come from env var)
        if channels_base_env := os.getenv("CHANNELS_BASE_PATH"):
            self.channels_base = channels_base_env

        # Convert to Path for manipulation
        base_path = Path(self.channels_base)

        # Apply defaults if not specified
        if self.temp_base is None:
            self.temp_base = str(base_path / "_temp")
        if self.media_base is None:
            self.media_base = str(base_path / "_media")
        if self.database_base is None:
            self.database_base = str(base_path / "_databases")

    def get_channel_path(self, channel_name: str) -> Path:
        """Get path for specific channel."""
        return Path(self.channels_base) / channel_name

    def get_channel_media_path(self, channel_name: str) -> Path:
        """Get media path for specific channel."""
        return self.get_channel_path(channel_name) / "_media"

    def get_channel_temp_path(self, channel_name: str) -> Path:
        """Get temp path for specific channel."""
        return self.get_channel_path(channel_name) / "_temp"

    def get_database_path(self, channel_name: str) -> Path:
        """Get database path for specific channel."""
        return self.get_channel_path(channel_name) / "telegram_data.db"

    def validate(self) -> list[str]:
        """Validate path configuration."""
        errors = []
        try:
            base_path = Path(self.channels_base)
            if not base_path.exists():
                base_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create channels_base path: {e}")
        return errors


@dataclass
class DatabaseConfig:
    """Database configuration with SQLite optimization."""

    connection_timeout: int = 30
    max_connections: int = 5
    pragma_settings: list[str] = field(
        default_factory=lambda: [
            "journal_mode=WAL",
            "synchronous=NORMAL",
            "cache_size=10000",
            "temp_store=memory",
        ]
    )
    shard_threshold_gb: float = 5.0
    max_shard_size_gb: float = 50.0
    auto_shard: bool = True

    def validate(self) -> list[str]:
        """Validate database configuration."""
        errors = []
        if self.connection_timeout <= 0:
            errors.append("connection_timeout must be positive")
        if self.shard_threshold_gb <= 0:
            errors.append("shard_threshold_gb must be positive")
        if self.max_shard_size_gb <= self.shard_threshold_gb:
            errors.append("max_shard_size_gb must be greater than shard_threshold_gb")
        return errors


@dataclass
class DownloadConfig:
    """Download behavior configuration."""

    max_concurrent: int = 2
    connection_timeout: int = 30
    read_timeout: int = 60
    retry_attempts: int = 3
    retry_delay: int = 2
    verify_downloads: bool = True
    cleanup_temp_on_exit: bool = True
    organize_by_channel: bool = True

    def validate(self) -> list[str]:
        """Validate download configuration."""
        errors = []
        if self.max_concurrent <= 0:
            errors.append("max_concurrent must be positive")
        if self.connection_timeout <= 0:
            errors.append("connection_timeout must be positive")
        return errors


@dataclass
class LoggingConfig:
    """Logging configuration."""

    console_level: LogLevel = LogLevel.WARNING
    file_level: LogLevel = LogLevel.DEBUG
    max_size_mb: int = 50
    backup_count: int = 5
    retention_days: int = 30
    format: str = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )

    def validate(self) -> list[str]:
        """Validate logging configuration."""
        errors = []
        if self.max_size_mb <= 0:
            errors.append("max_size_mb must be positive")
        if self.backup_count < 0:
            errors.append("backup_count must be non-negative")
        return errors


@dataclass
class UIConfig:
    """UI configuration."""

    default_mode: UIMode = UIMode.TQDM
    fallback_mode: UIMode = UIMode.SIMPLE
    show_speed: bool = True
    show_eta: bool = True
    show_file_progress: bool = True
    update_frequency: float = 0.1

    def validate(self) -> list[str]:
        """Validate UI configuration."""
        errors = []
        if self.update_frequency <= 0:
            errors.append("update_frequency must be positive")
        return errors


@dataclass
class PerformanceConfig:
    """Performance tuning configuration."""

    max_memory_mb: int = 1024
    gc_threshold: int = 100
    buffer_size: int = 65536
    use_aiofiles: bool = True

    def validate(self) -> list[str]:
        """Validate performance configuration."""
        errors = []
        if self.max_memory_mb <= 0:
            errors.append("max_memory_mb must be positive")
        return errors


@dataclass
class AppConfig:
    """Main application configuration."""

    name: str = "Telegram Downloader"
    version: str = "2.0"
    environment: Environment = Environment.DEVELOPMENT

    # Sub-configurations
    paths: PathsConfig = field(default_factory=PathsConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    def validate(self) -> list[str]:
        """Validate entire configuration."""
        all_errors = []
        all_errors.extend(self.paths.validate())
        all_errors.extend(self.database.validate())
        all_errors.extend(self.download.validate())
        all_errors.extend(self.logging.validate())
        all_errors.extend(self.ui.validate())
        all_errors.extend(self.performance.validate())
        return all_errors

    def apply_environment_overrides(self, env_overrides: dict[str, Any]) -> None:
        """Apply environment-specific configuration overrides."""
        for section, values in env_overrides.items():
            if hasattr(self, section):
                section_obj = getattr(self, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        # Handle enum conversions for environment overrides
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


@dataclass
class ChannelConfig:
    """Individual channel configuration."""

    name: str
    chat_id: int
    enabled: bool = True
    max_concurrent_override: int | None = None
    media_types: list[str] = field(default_factory=lambda: ["all"])
    size_limit_mb: int | None = None

    def validate(self) -> list[str]:
        """Validate channel configuration."""
        errors = []
        if not self.name:
            errors.append("Channel name cannot be empty")
        if self.chat_id == 0:
            errors.append("chat_id cannot be zero")
        return errors


@dataclass
class ChannelsConfig:
    """All channels configuration."""

    channels: dict[str, ChannelConfig] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChannelsConfig":
        """Create from dictionary format."""
        channels = {}
        for name, chat_id in data.items():
            if isinstance(chat_id, int):
                channels[name] = ChannelConfig(name=name, chat_id=chat_id)
            elif isinstance(chat_id, dict):
                channels[name] = ChannelConfig(name=name, **chat_id)
        return cls(channels=channels)

    def validate(self) -> list[str]:
        """Validate all channels."""
        all_errors = []
        for name, channel in self.channels.items():
            errors = channel.validate()
            all_errors.extend([f"Channel {name}: {error}" for error in errors])
        return all_errors

    def get_enabled_channels(self) -> dict[str, ChannelConfig]:
        """Get only enabled channels."""
        return {
            name: config for name, config in self.channels.items() if config.enabled
        }
