"""API key management for NVIDIA NIM CLI."""

from __future__ import annotations

import os
import sys


def get_api_key() -> str | None:
    """Get NVIDIA NIM API key from environment.

    Checks NVIDIA_API_KEY environment variable.

    Returns:
        The API key if set, None otherwise.
    """
    return os.environ.get("NVIDIA_API_KEY")


def require_api_key() -> str:
    """Require NVIDIA NIM API key, exit if not set.

    Returns:
        The API key.

    Raises:
        SystemExit: If API key is not set.
    """
    api_key = get_api_key()
    if not api_key:
        print(
            "Error: NVIDIA_API_KEY environment variable not set",
            file=sys.stderr,
        )
        print("Get your key at: https://build.nvidia.com/", file=sys.stderr)
        sys.exit(1)
    return api_key


def is_api_key_available() -> bool:
    """Check if NVIDIA NIM API key is available.

    Returns:
        True if NVIDIA_API_KEY is set.
    """
    return bool(get_api_key())
