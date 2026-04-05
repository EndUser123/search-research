"""OpenRouter API key management.

This module provides centralized API key retrieval for the OpenRouter skill.
The API key is automatically retrieved from the OPENROUTER_API_KEY environment variable.
"""

from __future__ import annotations

import os
import sys


def get_api_key() -> str | None:
    """Get OpenRouter API key from environment.

    The API key is retrieved from the OPENROUTER_API_KEY environment variable.
    Returns None if the key is not set.

    Returns:
        The API key string, or None if not set.
    """
    return os.environ.get("OPENROUTER_API_KEY")


def require_api_key() -> str:
    """Get OpenRouter API key, exiting with error if not set.

    This is a convenience function for commands that require an API key.
    It will print an error message and exit if the key is not available.

    Returns:
        The API key string.

    Raises:
        SystemExit: If the API key is not set.
    """
    api_key = get_api_key()
    if not api_key:
        print(
            "Error: OPENROUTER_API_KEY environment variable not set",
            file=sys.stderr,
        )
        print(
            "Get your API key at: https://openrouter.ai/keys",
            file=sys.stderr,
        )
        print(
            "Set it with: export OPENROUTER_API_KEY=your-key-here",
            file=sys.stderr,
        )
        sys.exit(1)
    return api_key


def is_api_key_available() -> bool:
    """Check if OpenRouter API key is available in environment.

    Returns:
        True if the API key is set, False otherwise.
    """
    return get_api_key() is not None
