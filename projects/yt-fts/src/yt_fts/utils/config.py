"""
Configuration utilities for yt-fts.

Provides environment variable loading, config path resolution, and database
path management across different platforms (Windows, macOS, Linux).
"""
from __future__ import annotations

import logging
import os
import subprocess
import shutil
import sys
from pathlib import Path
from typing import Optional

# =============================================================================
# Module Constants
# =============================================================================

# Valid platforms for configuration
VALID_PLATFORMS = frozenset({"win32", "darwin", "linux"})

# Platform-specific config directory names
_CONFIG_DIR_NAME = "yt-fts"
_WINDOWS_CONFIG_ENV_VAR = "APPDATA"

# Environment variable names
_ENV_YT_FTS_DB_PATH = "YT_FTS_DB_PATH"
_ENV_YOUTUBE_API_KEY = "YOUTUBE_API_KEY"
_ENV_GEMINI_API_KEY = "GEMINI_API_KEY"

# Search locations for .env file (relative to start_dir)
_ENV_SEARCH_LEVELS = (0, 1, 2)  # self, parent, grandparent

# =============================================================================
# Logging Setup
# =============================================================================

logger = logging.getLogger(__name__)


# =============================================================================
# Platform Detection Helpers
# =============================================================================

def _is_windows() -> bool:
    """Check if running on Windows platform.

    Returns:
        True if platform is Windows (win32), False otherwise.
    """
    return sys.platform == "win32"


def _is_posix() -> bool:
    """Check if running on POSIX platform (macOS or Linux).

    Returns:
        True if platform is macOS or Linux, False otherwise.
    """
    return sys.platform in {"darwin", "linux"}


# =============================================================================
# Config Path Helpers
# =============================================================================

def _get_default_config_dir() -> Path:
    """Get the default configuration directory for the current platform.

    Platform conventions:
        Windows: %APPDATA%\\yt-fts
        macOS/Linux: ~/.config/yt-fts

    Returns:
        Path object pointing to the platform-specific config directory.

    Raises:
        RuntimeError: If running on an unsupported platform or APPDATA not set on Windows.
    """
    if _is_windows():
        appdata = os.getenv(_WINDOWS_CONFIG_ENV_VAR, "")
        if not appdata:
            raise RuntimeError(
                f"{_WINDOWS_CONFIG_ENV_VAR} environment variable not set on Windows. "
                f"Cannot determine config directory location."
            )
        return Path(appdata) / _CONFIG_DIR_NAME
    elif _is_posix():
        return Path.home() / ".config" / _CONFIG_DIR_NAME
    else:
        raise RuntimeError(
            f"Unsupported platform {sys.platform!r}. "
            f"Valid platforms are: {sorted(VALID_PLATFORMS)}"
        )


def _ensure_config_dir_exists(base_path: Optional[Path] = None) -> Optional[Path]:
    """Ensure the configuration directory exists, creating it if necessary.

    Args:
        base_path: Optional custom base path for config directory.
                   If None, uses platform default.

    Returns:
        Path to config directory if successful, None if creation failed.
    """
    if base_path is None:
        try:
            base_path = _get_default_config_dir()
        except RuntimeError as e:
            logger.error("Failed to determine config directory: %s", e)
            return None

    if base_path.exists():
        return base_path

    try:
        base_path.mkdir(parents=True, exist_ok=True)
        logger.info("Created config directory: %s", base_path)
        return base_path
    except OSError as e:
        logger.error(
            "Failed to create config directory at %s: %s (error code: %s)",
            base_path, e.strerror, e.errno
        )
        return None


# =============================================================================
# Environment File Loading
# =============================================================================

def find_and_load_env(start_dir: Optional[Path] = None) -> Optional[str]:
    """Search for and load .env file from standard locations.

    Searches in priority order:
        1. Project root (start_dir)
        2. Parent directory (for monorepo setups)
        3. Grandparent directory (for P:\\\\.env scenario)

    Args:
        start_dir: Starting directory for search. Defaults to cwd().

    Returns:
        Path to .env file if found and loaded, None otherwise.

    Notes:
        - Skips .env loading for help commands (--help, -h)
        - Requires python-dotenv package for loading
    """
    # Skip .env loading for help commands
    if "--help" in sys.argv or "-h" in sys.argv:
        logger.debug("Skipping .env loading: help command detected")
        return None

    if start_dir is None:
        start_dir = Path.cwd()
    elif isinstance(start_dir, str):
        start_dir = Path(start_dir)

    # Search in priority order: start_dir, parent, grandparent
    for level in _ENV_SEARCH_LEVELS:
        location = start_dir
        for _ in range(level):
            location = location.parent

        env_path = location / ".env"
        logger.debug("Checking for .env at level %d: %s", level, env_path)

        if env_path.exists():
            return _load_env_file(env_path)

    logger.debug("No .env file found in search locations")
    return None


def _load_env_file(env_path: Path) -> Optional[str]:
    """Load environment variables from a .env file.

    Args:
        env_path: Path to the .env file to load.

    Returns:
        Path string if loading succeeded, None if failed.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path)
        logger.info("Loaded .env from %s", env_path)
        return str(env_path)
    except ImportError:
        logger.warning(
            "python-dotenv not installed. To load .env files, "
            "install with: pip install python-dotenv"
        )
        return None
    except Exception as e:
        logger.error(
            "Error loading .env from %s: %s (type: %s)",
            env_path, e, type(e).__name__
        )
        return None


def get_config_path() -> Optional[str]:
    """Get the path to the application configuration directory.

    Returns:
        Path to config directory as string if it exists, None otherwise.
    """
    try:
        config_path = _get_default_config_dir()
    except RuntimeError:
        return None

    if not config_path.exists():
        logger.debug("Config directory does not exist: %s", config_path)
        return None

    return str(config_path)


def make_config_dir() -> Optional[str]:
    """Create the configuration directory if it does not exist.

    Returns:
        Path to config directory as string if successful, None on failure.
    """
    result = _ensure_config_dir_exists()
    return str(result) if result else None


# =============================================================================
# Database Path Resolution
# =============================================================================

def get_db_path() -> str:
    """Get database path, with support for custom location via environment variable.

    Resolution order:
        1. YT_FTS_DB_PATH environment variable (custom location)
        2. Platform-specific config directory
        3. Current directory fallback

    Returns:
        Path to SQLite database file as string.
    """
    from yt_fts.db.maintenance import make_db

    custom_db_path = os.getenv(_ENV_YT_FTS_DB_PATH)
    if custom_db_path:
        return _get_custom_db_path(custom_db_path, make_db)

    return _get_standard_db_path(make_db)


def _get_custom_db_path(custom_path: str, make_db) -> str:
    """Handle custom database path from environment variable.

    Args:
        custom_path: Custom path string from YT_FTS_DB_PATH.
        make_db: Function reference to create database.

    Returns:
        Database path as string.
    """
    db_path = Path(custom_path)

    if db_path.parent and not db_path.parent.exists():
        logger.info("Creating parent directory for custom DB: %s", db_path.parent)
        db_path.parent.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        logger.info("Creating database at custom path: %s", db_path)
        make_db(str(db_path))

    return str(db_path)


def _get_standard_db_path(make_db) -> str:
    """Handle standard database path resolution.

    Args:
        make_db: Function reference to create database.

    Returns:
        Database path as string.
    """
    config_path = get_config_path()

    if config_path is None:
        config_path = make_config_dir()
        if config_path is None:
            logger.warning(
                "Unable to create config directory, using current working directory"
            )
            return "subtitles.db"

    db_path = Path(config_path) / "subtitles.db"

    if not db_path.exists():
        logger.info("Database not found at %s, creating new database", db_path)
        make_db(str(db_path))

    return str(db_path)


# =============================================================================
# Configuration Validation
# =============================================================================

def validate_configuration() -> list[str]:
    """Validate required configuration and return list of issues found.

    Checks for essential environment variables, API keys, and external tools.
    Returns warnings rather than raising exceptions to allow degraded operation.

    Returns:
        List of configuration issues (warnings, not errors).
    """
    issues = []

    if not os.getenv(_ENV_YOUTUBE_API_KEY):
        issues.append(
            f"{_ENV_YOUTUBE_API_KEY} not set - metadata backfill will be limited. "
            f"Set this environment variable to enable full YouTube API features."
        )

    if not os.getenv(_ENV_GEMINI_API_KEY):
        issues.append(
            f"{_ENV_GEMINI_API_KEY} not set - Gemini embeddings will not be available. "
            f"Set this environment variable to enable semantic search features."
        )

    db_issues = _validate_db_path()
    issues.extend(db_issues)

    ytdlp_issue = _validate_ytdlp()
    if ytdlp_issue:
        issues.append(ytdlp_issue)

    return issues


def _validate_db_path() -> list[str]:
    """Validate database path accessibility.

    Returns:
        List of issues found (empty if valid).
    """
    issues = []

    try:
        db_path = get_db_path()
        if not Path(db_path).exists():
            issues.append(
                f"Database not found at {db_path} - will be created on first use"
            )
        else:
            logger.debug("Database path validated: %s", db_path)
    except Exception as e:
        issues.append(
            f"Database path validation failed: {e} (type: {type(e).__name__})"
        )

    return issues


def _validate_ytdlp() -> Optional[str]:
    """Validate yt-dlp availability in PATH.

    Returns:
        Error message if not found, None if available.
    """
    try:
        if not shutil.which("yt-dlp"):
            return (
                "yt-dlp not found in PATH - video downloading will fail. "
                "Install with: pip install yt-dlp"
            )
        logger.debug("yt-dlp found in PATH")
    except (OSError, subprocess.SubprocessError) as e:
        return f"Unable to verify yt-dlp installation: {e}"

    return None
