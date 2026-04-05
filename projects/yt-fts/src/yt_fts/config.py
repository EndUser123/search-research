"""
Centralized configuration for yt-fts.

Single source of truth for all configuration values.
Eliminates hardcoded constants scattered across the codebase.

Usage:
    from yt_fts.config import (
        DAILY_QUOTA_LIMIT,
        QUOTA_PER_KEY,
        NUM_API_KEYS,
        get_db_path,
    )
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Final

# =============================================================================
# API Configuration
# =============================================================================

# YouTube API Keys - loaded from environment
# YOUTUBE_API_KEY, YOUTUBE_API_KEY_2, YOUTUBE_API_KEY_3, YOUTUBE_API_KEY_4
_API_KEY_1: Final[str] = os.getenv("YOUTUBE_API_KEY", "")
_API_KEY_2: Final[str] = os.getenv("YOUTUBE_API_KEY_2", "")
_API_KEY_3: Final[str] = os.getenv("YOUTUBE_API_KEY_3", "")
_API_KEY_4: Final[str] = os.getenv("YOUTUBE_API_KEY_4", "")

# All non-empty API keys
API_KEYS: Final[tuple[str, ...]] = tuple(
    k for k in [_API_KEY_1, _API_KEY_2, _API_KEY_3, _API_KEY_4] if k
)

# Number of available API keys (auto-calculated)
NUM_API_KEYS: Final[int] = len(API_KEYS)

# Quota per API key (YouTube Data API v3 limit)
QUOTA_PER_KEY: Final[int] = 10_000

# Total daily quota (auto-calculated based on available keys)
# This replaces hardcoded values scattered across:
#   - quota_strategy.py (was 20000)
#   - metadata_backfill_api.py (was 10000)
#   - cli.py (was 20000)
DAILY_QUOTA_LIMIT: Final[int] = (
    QUOTA_PER_KEY * NUM_API_KEYS if NUM_API_KEYS > 0 else QUOTA_PER_KEY
)

# =============================================================================
# Database Configuration
# =============================================================================

# Default database location (platform-specific)
_DEFAULT_DB_PATH: Final[Path] = Path.home() / ".config" / "yt-fts" / "subtitles.db"

# Allow override via environment variable
# Used by deploy.ps1 and testing scripts
_DB_PATH_OVERRIDE: Final[str | None] = os.getenv("YT_FTS_DB_PATH")

# Final database path (override takes precedence)
DB_PATH: Final[Path] = (
    Path(_DB_PATH_OVERRIDE) if _DB_PATH_OVERRIDE else _DEFAULT_DB_PATH
)


def get_db_path() -> str:
    """
    Get the database path as a string.

    This function exists for backward compatibility with existing code
    that imports get_db_path from various modules.

    Returns:
        Path to the SQLite database file
    """
    return str(DB_PATH)


# =============================================================================
# Quota Strategy Configuration
# =============================================================================#

# Quota strategy thresholds (percentages of remaining quota)
CONSERVATIVE_THRESHOLD: Final[float] = (
    0.15  # Below 15%: conserve quota (reserves ~6,000 quota)
)
AGGRESSIVE_THRESHOLD: Final[float] = 0.60  # Above 60%: use freely

# =============================================================================
# Display Configuration
# =============================================================================#

# Default display plugin
DEFAULT_DISPLAY_PLUGIN: Final[str] = "default"

# Valid display plugin categories
VALID_DISPLAY_CATEGORIES: Final[tuple[str, ...]] = (
    "core",
    "verbose",
    "diagnostic",
    "monitoring",
)

# =============================================================================
# Logging Configuration
# =============================================================================#

# Dual-sink logging: JSON file + clean console
LOG_DIR: Final[Path] = DB_PATH.parent / "logs"
LOG_FILE: Final[Path] = LOG_DIR / "yt_fts.log"
LOG_FORMAT_JSON: Final[str] = "json"
LOG_FORMAT_CONSOLE: Final[str] = "console"

# =============================================================================
# Configuration Schema & Validation
# =============================================================================#

from typing import Any


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""


class ConfigurationSchema:
    """
    Schema definition and validation for yt-fts configuration.

    Defines expected configuration structure with types, defaults, and validation rules.
    """

    def __init__(self):
        self.schema = {
            "api": {
                "keys": {
                    "type": "list",
                    "required": False,  # Optional - can work without API keys
                    "description": "YouTube API keys for enhanced channel resolution",
                    "env_vars": [
                        "YOUTUBE_API_KEY",
                        "YOUTUBE_API_KEY_2",
                        "YOUTUBE_API_KEY_3",
                        "YOUTUBE_API_KEY_4",
                    ],
                    "validation": self._validate_api_keys,
                },
                "quota_per_key": {
                    "type": "int",
                    "default": 10_000,
                    "description": "YouTube API quota per key per day",
                    "range": (1, 1_000_000),
                },
            },
            "database": {
                "path": {
                    "type": "path",
                    "default": str(_DEFAULT_DB_PATH),
                    "description": "Path to SQLite database file",
                    "env_var": "YT_FTS_DB_PATH",
                    "validation": self._validate_db_path,
                },
            },
            "display": {
                "plugin": {
                    "type": "str",
                    "default": "default",
                    "description": "Default display plugin",
                    "choices": ["default", "compact", "detailed", "progress"],
                },
            },
            "logging": {
                "level": {
                    "type": "str",
                    "default": "INFO",
                    "description": "Logging level",
                    "choices": ["DEBUG", "INFO", "WARNING", "ERROR"],
                },
                "dir": {
                    "type": "path",
                    "default": str(LOG_DIR),
                    "description": "Log directory path",
                },
            },
        }

    def _validate_api_keys(self, value: list[str]) -> str | None:
        """Validate API keys list."""
        if not value:
            return "No API keys configured (optional but recommended)"

        invalid_keys = [k for k in value if not self._is_valid_api_key(k)]
        if invalid_keys:
            return f"Invalid API key format(s): {len(invalid_keys)} key(s) appear malformed"

        return None  # Valid

    def _is_valid_api_key(self, key: str) -> bool:
        """Check if an API key looks valid (basic format check)."""
        if not key or len(key) < 10:
            return False

        # YouTube API keys typically start with specific prefixes
        valid_prefixes = ["AIza", "AIzaSy"]  # Common Google API key prefixes
        return any(key.startswith(prefix) for prefix in valid_prefixes)

    def _validate_db_path(self, value: str) -> str | None:
        """Validate database path."""
        path = Path(value)

        # Check if parent directory is writable
        parent = path.parent
        if parent.exists() and not os.access(parent, os.W_OK):
            return f"Database directory not writable: {parent}"

        # Check if database file itself is writable (if it exists)
        if path.exists() and not os.access(path, os.W_OK):
            return f"Database file not writable: {path}"

        return None  # Valid

    def validate_config(self) -> dict[str, Any]:
        """
        Validate current configuration against schema.

        Returns:
            Dict with validation results and any error messages

        Raises:
            ConfigValidationError: If critical configuration issues found
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "config": {},
        }

        # Validate each section
        for section_name, section_schema in self.schema.items():
            section_result = self._validate_section(section_name, section_schema)
            results["config"][section_name] = section_result

            if section_result.get("errors"):
                results["errors"].extend(section_result["errors"])
                if section_result.get("critical", False):
                    results["valid"] = False

            if section_result.get("warnings"):
                results["warnings"].extend(section_result["warnings"])

        return results

    def _validate_section(
        self, section_name: str, section_schema: dict
    ) -> dict[str, Any]:
        """Validate a configuration section."""
        result = {"values": {}, "errors": [], "warnings": []}

        for key, spec in section_schema.items():
            value, error = self._get_config_value(section_name, key, spec)

            if error:
                if spec.get("required", False):
                    result["errors"].append(f"{section_name}.{key}: {error}")
                    result["critical"] = True
                else:
                    result["warnings"].append(f"{section_name}.{key}: {error}")
            else:
                result["values"][key] = value

        return result

    def _get_config_value(
        self, section: str, key: str, spec: dict
    ) -> tuple[Any, str | None]:
        """Get and validate a configuration value."""
        # Get value from environment or use default
        if "env_vars" in spec:
            # Multiple environment variables (like API keys)
            values = [os.getenv(var, "") for var in spec["env_vars"]]
            values = [v for v in values if v]  # Filter empty values
            value = values if spec["type"] == "list" else (values[0] if values else "")
        elif "env_var" in spec:
            value = os.getenv(spec["env_var"], spec.get("default", ""))
        else:
            value = spec.get("default", "")

        # Type conversion
        try:
            value = self._convert_type(value, spec["type"])
        except (ValueError, TypeError) as e:
            return None, f"Invalid type: {e}"

        # Validation
        if "validation" in spec:
            error = spec["validation"](value)
            if error:
                return value, error

        # Range/choice validation
        if "range" in spec and isinstance(value, (int, float)):
            min_val, max_val = spec["range"]
            if not (min_val <= value <= max_val):
                return value, f"Value {value} not in range [{min_val}, {max_val}]"

        if "choices" in spec and value not in spec["choices"]:
            return value, f"Value '{value}' not in allowed choices: {spec['choices']}"

        return value, None

    def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert value to target type."""
        if target_type == "int":
            return int(value) if value != "" else 0
        if target_type == "float":
            return float(value) if value != "" else 0.0
        if target_type == "bool":
            return str(value).lower() in ("true", "1", "yes", "on")
        if target_type == "path":
            return str(value)
        if target_type == "list":
            return value if isinstance(value, list) else [value] if value else []
        return str(value)


# Global configuration validator instance
_config_validator = ConfigurationSchema()


def validate_config() -> dict[str, Any]:
    """
    Validate current configuration and return detailed status.

    Returns:
        Dict with validation results, errors, and warnings
    """
    return _config_validator.validate_config()


def get_config_validation_errors() -> list[str]:
    """
    Get list of critical configuration errors.

    Returns:
        List of error messages (empty if configuration is valid)
    """
    validation = validate_config()
    return validation.get("errors", [])


def get_config_warnings() -> list[str]:
    """
    Get list of configuration warnings (non-critical issues).

    Returns:
        List of warning messages
    """
    validation = validate_config()
    return validation.get("warnings", [])


def ensure_config_valid() -> None:
    """
    Ensure configuration is valid, raising an exception if critical errors found.

    This should be called early in application startup.
    """
    validation = validate_config()

    if not validation["valid"]:
        errors = validation["errors"]
        error_msg = "Critical configuration errors found:\n" + "\n".join(
            f"  • {e}" for e in errors
        )
        raise ConfigValidationError(error_msg)

    # Log warnings but don't fail
    warnings = validation.get("warnings", [])
    if warnings:
        print("Configuration warnings:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
        print()


def print_config_status() -> None:
    """
    Print comprehensive configuration status for debugging/setup.
    """
    validation = validate_config()

    print("🔧 yt-fts Configuration Status")
    print("=" * 50)

    # API Configuration
    api_config = validation["config"]["api"]
    print(f"📺 API Keys: {len(api_config['values'].get('keys', []))} configured")
    print(f"📊 Daily Quota: {DAILY_QUOTA_LIMIT:,} units")

    # Database
    db_config = validation["config"]["database"]
    db_path = db_config["values"].get("path", "unknown")
    print(f"💾 Database: {db_path}")
    print(f"   Exists: {Path(db_path).exists()}")

    # Status
    if validation["valid"]:
        print("✅ Configuration: VALID")
    else:
        print("❌ Configuration: INVALID")

    # Errors
    if validation["errors"]:
        print("\n🚨 Critical Errors:")
        for error in validation["errors"]:
            print(f"   • {error}")

    # Warnings
    if validation["warnings"]:
        print("\n⚠️  Warnings:")
        for warning in validation["warnings"]:
            print(f"   • {warning}")

    print("=" * 50)


# =============================================================================
# Progress Bar Configuration
# =============================================================================#

from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from typing import Any

# Common console configuration (stderr for progress bars)
_PROGRESS_CONSOLE = Console(stderr=True, legacy_windows=False)


def _create_base_progress_config(**overrides: Any) -> dict[str, Any]:
    """Create base progress configuration with common settings.

    Args:
        **overrides: Additional parameters to override defaults

    Returns:
        Configuration dict for Progress initialization
    """
    config = {
        # Note: console is NOT included here - let caller pass explicitly
        # This avoids "got multiple values for keyword argument 'console'" errors
        "auto_refresh": True,
        "redirect_stderr": True,
        "redirect_stdout": False,
        "transient": True,  # Progress bars disappear when complete (prevents visual "hang")
    }
    config.update(overrides)
    return config


# Batch download progress configuration
# Used in: batch_downloader.py
# Description: Multi-channel batch processing with stacked progress bars
BATCH_PROGRESS_CONFIG: dict[str, Any] = _create_base_progress_config(
    expand=False,
)


# Single-channel download progress configuration
# Used in: batch_downloader.py (single channel mode)
# Description: Progress bar for individual channel downloads
SINGLE_CHANNEL_PROGRESS_CONFIG: dict[str, Any] = _create_base_progress_config(
    auto_refresh=False,
)


# Worker progress configuration
# Used in: download_handler.py, progress_tracker.py
# Description: Progress bars for worker threads during subtitle downloads
WORKER_PROGRESS_CONFIG: dict[str, Any] = _create_base_progress_config(
    refresh_per_second=2,
)


if __name__ == "__main__":
    # Self-test: print configuration when run directly
    print("yt-fts Configuration")
    print("=" * 40)
    print(f"API Keys: {NUM_API_KEYS}")
    print(f"Daily Quota: {DAILY_QUOTA_LIMIT:,}")
    print(f"Database: {DB_PATH}")
    print()
    print("Validation:")
    print(json.dumps(validate_config(), indent=2))
