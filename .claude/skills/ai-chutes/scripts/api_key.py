"""API key management for Chutes CLI."""

from __future__ import annotations

import os
import sys
from pathlib import Path


# Project root detection
def _find_project_root() -> Path:
    """Find project root by looking for .env file."""
    current = Path.cwd()

    # Look for .env in current directory and parents
    for path in [current] + list(current.parents):
        env_file = path / ".env"
        if env_file.exists():
            return path

    # Fallback to P:\ drive if running from within skill directory
    p_drive = Path("P:/")
    if (p_drive / ".env").exists():
        return p_drive

    return current


# Load .env file
def _load_env_file() -> None:
    """Load environment variables from .env file."""
    project_root = _find_project_root()
    env_file = project_root / ".env"

    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Parse KEY=VALUE or KEY="VALUE" format
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    # Only set if not already in environment
                    if key and not os.environ.get(key):
                        os.environ[key] = value


# Load environment on module import
_load_env_file()


def get_api_key() -> str | None:
    """Get Chutes API key from environment.

    Checks CHUTES_API_KEY environment variable.

    Returns:
        The API key if set, None otherwise.
    """
    return os.environ.get("CHUTES_API_KEY")


def require_api_key() -> str:
    """Require Chutes API key, exit if not set.

    Returns:
        The API key.

    Raises:
        SystemExit: If API key is not set.
    """
    api_key = get_api_key()
    if not api_key:
        print(
            "Error: CHUTES_API_KEY environment variable not set",
            file=sys.stderr,
        )
        print("Get your key at: https://chutes.ai", file=sys.stderr)
        sys.exit(1)
    return api_key


def is_api_key_available() -> bool:
    """Check if Chutes API key is available.

    Returns:
        True if CHUTES_API_KEY is set.
    """
    return bool(get_api_key())
