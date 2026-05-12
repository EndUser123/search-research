"""LLM provider router and factory."""

from __future__ import annotations

import os

from .base import LLMProvider
from .bifrost import BifrostProvider


# Environment variable to select provider
_PROVIDER_ENV = "REASONING_LLM_PROVIDER"
# Valid provider names
_PROVIDER_NAMES = {"bifrost", "anthropic", "openai"}


def get_provider(
    provider: str | None = None,
    **kwargs,
) -> LLMProvider:
    """
    Factory function to get an LLM provider.

    Args:
        provider: Provider name ("bifrost", "anthropic", "openai"). Falls back to
            REASONING_LLM_PROVIDER env var, then auto-detection.
        **kwargs: Additional arguments passed to provider constructor.

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If provider is unknown or no credentials available
    """
    # Determine provider
    if provider is None:
        provider = os.environ.get(_PROVIDER_ENV, "")

    if not provider:
        # Auto-detect based on available credentials
        # bifrost is default (uses ANTHROPIC_API_KEY via BIFROST_VK)
        if os.environ.get("ANTHROPIC_API_KEY"):
            provider = "bifrost"  # bifrost uses ANTHROPIC_API_KEY
        else:
            raise ValueError(
                "No LLM provider configured. Set REASONING_LLM_PROVIDER or ANTHROPIC_API_KEY."
            )

    provider = provider.lower()
    if provider not in _PROVIDER_NAMES:
        raise ValueError(
            f"Unknown provider: {provider}. Valid: {', '.join(_PROVIDER_NAMES)}"
        )

    if provider == "bifrost":
        return BifrostProvider(**kwargs)
    elif provider == "anthropic":
        from .anthropic import AnthropicProvider
        return AnthropicProvider(**kwargs)
    elif provider == "openai":
        from .openai import OpenAIProvider
        return OpenAIProvider(**kwargs)

    # Should not reach here
    raise ValueError(f"Invalid provider: {provider}")


# Convenience singleton for synchronous access
_provider_cache: LLMProvider | None = None


def get_cached_provider(**kwargs) -> LLMProvider:
    """
    Get a cached provider instance (singleton pattern).

    Args:
        **kwargs: Provider configuration arguments (only used on first call)

    Returns:
        Cached LLM provider instance
    """
    global _provider_cache
    if _provider_cache is None:
        _provider_cache = get_provider(**kwargs)
    return _provider_cache


def clear_provider_cache() -> None:
    """Clear the cached provider (useful for testing or reconfiguration)."""
    global _provider_cache
    _provider_cache = None