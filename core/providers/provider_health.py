"""Provider health check interface.

This module provides the health check interface for all web search providers.
"""

from dataclasses import dataclass


@dataclass
class ProviderHealthStatus:
    """Health check result for a provider.

    Attributes:
        healthy: Whether provider is healthy and available
        latency_ms: Response time in milliseconds
        error: Error message if unhealthy (None if healthy)

    Example:
        status = await provider.check_health(timeout=5.0)
        if status.healthy:
            print(f"Provider healthy, latency: {status.latency_ms:.0f}ms")
        else:
            print(f"Provider unhealthy: {status.error}")
    """

    healthy: bool
    latency_ms: float
    error: str | None = None
