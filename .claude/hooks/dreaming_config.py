"""Dreaming config system (T-001).

Loads configuration for dreaming daemon with default fallback behavior.

Usage:
    from dreaming_config import load_config
    config = load_config()  # Uses default path
    config = load_config(config_path="/custom/path/config.json")
"""
import json
from pathlib import Path

DEFAULT_CONFIG = {
    "enabled": True,
    "cycle_interval_minutes": 60,
    "orphans_per_cycle": 10,
    "relationship_threshold": 0.7,
    "max_relationships_per_orphan": 5,
    # Daemon heartbeat and zombie detection (T-009)
    "heartbeat_interval_seconds": 60,
    "zombie_timeout_seconds": 180,
}


def load_config(config_path: str | None = None) -> dict:
    """Load dreaming configuration from file, falling back to defaults.

    Args:
        config_path: Path to config file. If None, uses default path.

    Returns:
        dict: Configuration dict with defaults merged with file values.

    Behavior:
        - If config file missing: create file with defaults, return defaults
        - If config file exists and valid: load and return (merge with defaults)
        - If config file has invalid JSON: fall back to defaults
        - Extra keys from config file are preserved
    """
    if config_path is None:
        config_path = "P:/.claude/state/dreaming-config.json"

    config_file = Path(config_path)

    # Start with defaults
    config = DEFAULT_CONFIG.copy()

    # Try to load existing config
    if config_file.exists():
        try:
            with open(config_file, encoding="utf-8") as f:
                loaded = json.load(f)

            # Merge: loaded values override defaults, preserve extras
            config.update(loaded)

        except (json.JSONDecodeError, OSError):
            # Invalid JSON or read error - fall back to defaults
            pass
    else:
        # Create config file with defaults
        try:
            # Create parent directory if missing
            config_file.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write pattern: write to temp, then rename
            temp_path = config_file.with_suffix(".tmp")
            temp_path.write_text(
                json.dumps(DEFAULT_CONFIG, indent=2),
                encoding="utf-8"
            )
            temp_path.replace(config_file)

        except OSError:
            # If we can't create the file, continue with defaults
            pass

    return config
