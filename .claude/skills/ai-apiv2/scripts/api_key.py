"""API key management for multi-provider CLI."""

from __future__ import annotations

import os

# Provider environment variable mapping
PROVIDER_ENV_KEYS = {
    "chutes": "CHUTES_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "nvidia": "NVIDIA_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "zai": "ZAI_API_KEY",
}


def get_api_key(provider: str) -> str | None:
    """Get API key for a provider from environment.

    Args:
        provider: Provider name (chutes, openrouter, nvidia, gemini, openai, zai)

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
