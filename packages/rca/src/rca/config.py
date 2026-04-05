"""Configuration for rca Tier 1 implementation.

Provides environment variable access and settings management for
evidence saturation thresholds, phase state persistence, and
hypothesis scoring.
"""

import json
import os
from pathlib import Path


def get_local_only_mode() -> bool:
    """Check if rca should run in local-only fallback mode.

    Reads the DEBUGRCA_LOCAL_ONLY environment variable.

    Returns:
        True if local-only mode is enabled, False otherwise.

    Examples:
        >>> os.environ["DEBUGRCA_LOCAL_ONLY"] = "true"
        >>> get_local_only_mode()
        True
        >>> os.environ["DEBUGRCA_LOCAL_ONLY"] = "false"
        >>> get_local_only_mode()
        False
    """
    value = os.environ.get("DEBUGRCA_LOCAL_ONLY", "false").lower()
    return value in ("true", "1", "yes", "on")


def is_saturation_disabled() -> bool:
    """Check if evidence saturation detection is disabled.

    Reads the DEBUGRCA_SATURATION_DISABLED environment variable.

    Returns:
        True if saturation detection is disabled, False otherwise.

    Examples:
        >>> os.environ["DEBUGRCA_SATURATION_DISABLED"] = "1"
        >>> is_saturation_disabled()
        True
    """
    value = os.environ.get("DEBUGRCA_SATURATION_DISABLED", "false").lower()
    return value in ("true", "1", "yes", "on")


def get_state_dir() -> str:
    """Get the state directory for phase state persistence.

    Reads DEBUGRCA_STATE_DIR environment variable if set,
    otherwise returns the default state directory.

    Returns:
        Path to the state directory.

    Examples:
        >>> os.environ["DEBUGRCA_STATE_DIR"] = "P:/custom/state"
        >>> get_state_dir()
        'P:/custom/state'
    """
    custom_dir = os.environ.get("DEBUGRCA_STATE_DIR")
    if custom_dir:
        return custom_dir
    return "P:/.claude/state/rca/"


def _load_settings() -> dict:
    """Load settings.json for rca configuration.

    Returns:
        The debugrca section from settings.json, or empty dict if not found.
    """
    settings_path = Path("P:/.claude/settings.json")
    try:
        if settings_path.exists():
            with open(settings_path, encoding="utf-8") as f:
                settings = json.load(f)
                return settings.get("debugrca", {})
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def get_saturation_threshold(query_type: str = "default") -> float:
    """Get the saturation threshold for a given query type.

    Reads from settings.json debugrca.saturation_thresholds.

    Args:
        query_type: The type of query ("technical", "balanced",
                     "preference", or "default").

    Returns:
        The saturation threshold value between 0 and 1.

    Examples:
        >>> get_saturation_threshold("technical")
        0.85
        >>> get_saturation_threshold("balanced")
        0.75
    """
    settings = _load_settings()
    thresholds = settings.get("saturation_thresholds", {})

    # Default thresholds
    default_thresholds = {
        "technical": 0.85,
        "balanced": 0.75,
        "preference": 0.70,
        "default": 0.75,
    }

    return thresholds.get(query_type, default_thresholds.get(query_type, 0.75))


class LocalFallbackMode:
    """Context manager for local-only fallback mode.

    When enabled, rca operates without external dependencies
    like semantic search or knowledge base integration.

    Attributes:
        enabled: Whether local mode is currently active.

    Examples:
        >>> with LocalFallbackMode():
        ...     # Operations run in local-only mode
        ...     pass
    """

    def __init__(self, enabled: bool = True):
        """Initialize the local fallback mode context.

        Args:
            enabled: Whether to enable local mode.
        """
        self.enabled = enabled
        self._original_value = None

    def __enter__(self):
        """Enter local-only mode."""
        self._original_value = os.environ.get("DEBUGRCA_LOCAL_ONLY")
        os.environ["DEBUGRCA_LOCAL_ONLY"] = "true" if self.enabled else "false"
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit local-only mode and restore original value."""
        if self._original_value is None:
            os.environ.pop("DEBUGRCA_LOCAL_ONLY", None)
        else:
            os.environ["DEBUGRCA_LOCAL_ONLY"] = self._original_value
        return False
