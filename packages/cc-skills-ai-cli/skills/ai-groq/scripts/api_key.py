"""API key management for Groq CLI."""

from __future__ import annotations

import os
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

# Provider environment variable mapping
PROVIDER_ENV_KEYS = {
    "groq": "GROQ_API_KEY",
}


def get_api_key(provider: str) -> str | None:
    """Get API key for a provider from environment.

    Args:
        provider: Provider name (groq)

    Returns:
        The API key if set, None otherwise.
    """
    env_key = PROVIDER_ENV_KEYS.get(provider)
    if not env_key:
        return None
    return os.environ.get(env_key)


def get_available_providers() -> list[str]:
    """Get list of providers with available API keys.

    Returns:
        List of provider names that have API keys set.
    """
    available = []
    for provider, env_key in PROVIDER_ENV_KEYS.items():
        if os.environ.get(env_key):
            available.append(provider)
    return available


def require_api_key(provider: str) -> str | None:
    """Require API key for a provider, exit if not set.

    Args:
        provider: Provider name

    Returns:
        The API key, or None if not set.
    """
    return get_api_key(provider)
