"""CHS Provider Registry.

Registry for history providers. Use register() to add providers,
discover() or discover_all() to retrieve them.
"""

from .base import Provider

# Global registry: provider_id -> provider class
_REGISTRY: dict[str, type[Provider]] = {}


def register(provider_id: str, provider_class: type[Provider]) -> None:
    """Register a provider class.
    Args:
        provider_id: Unique identifier for the provider
        provider_class: Provider class implementing Provider Protocol
    """
    _REGISTRY[provider_id] = provider_class


def discover(provider_id: str) -> Provider:
    """Get a provider instance by provider_id.
    Args:
        provider_id: Unique identifier for the provider
    Returns:
        Provider instance
    Raises:
        KeyError: If provider_id not registered
    """
    provider_class = _REGISTRY[provider_id]
    return provider_class()


def discover_all() -> list[Provider]:
    """Get all registered providers.
    Returns:
        List of all registered provider instances
    """
    return [cls() for cls in _REGISTRY.values()]


def ingest_since(provider_id: str, watermark: dict | None = None) -> list[dict]:
    """Convenience wrapper to ingest events from a provider.
    Args:
        provider_id: Unique identifier for the provider
        watermark: Optional watermark from previous ingest
    Returns:
        List of event dicts
    """
    provider = discover(provider_id)
    return provider.ingest_since(watermark)


# Register built-in providers
from .claude_code_raw import ClaudeCodeRawProvider  # noqa: E402
from .codex_desktop import CodexDesktopProvider  # noqa: E402
from .claude_log import ClaudeLogProvider  # noqa: E402
from .grok_sessions import GrokSessionsProvider  # noqa: E402

register("claude_code_raw", ClaudeCodeRawProvider)
register("codex_desktop", CodexDesktopProvider)
register("claude_log", ClaudeLogProvider)
register("grok_sessions", GrokSessionsProvider)
