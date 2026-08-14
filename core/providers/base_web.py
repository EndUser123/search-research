"""Base web backend protocol for web search providers.

This module defines the common interface that all web search providers must implement.
"""

from __future__ import annotations

import abc
import logging
import os
from typing import Any

from .provider_health import ProviderHealthStatus

logger = logging.getLogger(__name__)


class BaseWebBackend(abc.ABC):
    """Base protocol for web search backends.

    All web providers must implement this protocol to ensure consistent interface
    and enable graceful degradation when API keys are missing.

    Attributes:
        name: Provider identifier (e.g., "tavily", "serper")
        requires_api_key: Whether provider requires API key
        api_key_env_var: Environment variable name for API key

    Example:
        class TavilyBackend(BaseWebBackend):
            @property
            def name(self) -> str:
                return "tavily"

            async def search(self, query: str, **kwargs) -> list[dict]:
                # Implementation here
                pass
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Provider identifier.

        Returns:
            Provider name (lowercase, e.g., "tavily", "serper")
        """
        ...

    @property
    @abc.abstractmethod
    def requires_api_key(self) -> bool:
        """Whether provider requires API key.

        Returns:
            True if provider requires API key, False otherwise
        """
        ...

    @property
    @abc.abstractmethod
    def api_key_env_var(self) -> str:
        """Environment variable name for API key.

        Returns:
            Environment variable name (e.g., "TAVILY_API_KEY")
        """
        ...

    @abc.abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
        timeout: float = 5.0,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Execute web search.

        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 10)
            timeout: Request timeout in seconds (default: 5.0)
            **kwargs: Provider-specific parameters

        Returns:
            List of search results with keys:
                - title: Result title
                - url: Result URL
                - content: Result content/snippet
                - score: Relevance score (0-1)
                - metadata: Provider-specific metadata (optional)

        Raises:
            ValueError: If API key is required but not configured
            NotImplementedError: If provider is not yet implemented
        """
        ...

    def validate_api_key(self) -> bool:
        """Validate that API key is configured if required.

        Logs warning if API key is missing.

        Returns:
            True if API key is configured or not required, False otherwise
        """
        if not self.requires_api_key:
            return True

        api_key = os.getenv(self.api_key_env_var)
        if not api_key:
            logger.warning(
                f"{self.name.upper()} provider requires {self.api_key_env_var} "
                f"environment variable. Skipping {self.name} searches."
            )
            return False

        return True

    def is_available(self) -> bool:
        """Check if provider is available for use.

        Provider is available if:
        - Does not require API key, OR
        - Requires API key and key is configured

        Returns:
            True if provider can be used, False otherwise
        """
        return self.validate_api_key()

    async def check_health(self, timeout: float = 5.0) -> dict[str, Any]:
        """Check if backend is healthy and available.

        Verifies:
        - API key validity (if required)
        - Endpoint availability
        - Response time

        Args:
            timeout: Health check timeout in seconds (default: 5.0)

        Returns:
            Dictionary with keys:
                - healthy: bool - True if backend is healthy
                - latency_ms: float - Response time in milliseconds
                - error: str | None - Error message if unhealthy

        Example:
            status = await backend.check_health(timeout=5.0)
            if status["healthy"]:
                print(f"Backend healthy, latency: {status['latency_ms']:.0f}ms")
            else:
                print(f"Backend unhealthy: {status['error']}")
        """
        # Default implementation checks API key and does a minimal search
        import time


        start_time = time.time()

        # Check API key first
        if not self.validate_api_key():
            return ProviderHealthStatus(
                healthy=False,
                latency_ms=0.0,
                error=f"API key not configured ({self.api_key_env_var})",
            )

        # Try a minimal search to verify endpoint availability
        try:
            # Use asyncio.wait_for to enforce timeout
            import asyncio

            await asyncio.wait_for(
                self.search("test", max_results=1, timeout=timeout),
                timeout=timeout,
            )

            latency_ms = (time.time() - start_time) * 1000
            return ProviderHealthStatus(
                healthy=True,
                latency_ms=latency_ms,
                error=None,
            )

        except asyncio.TimeoutError:
            return ProviderHealthStatus(
                healthy=False,
                latency_ms=timeout * 1000,
                error=f"Health check timed out after {timeout}s",
            )
        except Exception as e:
            return ProviderHealthStatus(
                healthy=False,
                latency_ms=(time.time() - start_time) * 1000,
                error=str(e),
            )

    async def close(self) -> None:
        """Close any open connections or resources.

        Default implementation does nothing. Override if provider
        maintains persistent connections.
        """


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(self, provider: str, message: str):
        """Initialize provider error.

        Args:
            provider: Provider name
            message: Error message
        """
        self.provider = provider
        self.message = message
        super().__init__(f"[{provider.upper()}] {message}")


class ProviderNotAvailableError(ProviderError):
    """Raised when provider is not available (missing API key)."""

    def __init__(self, provider: str, api_key_env_var: str):
        """Initialize not available error.

        Args:
            provider: Provider name
            api_key_env_var: Environment variable name for API key
        """
        super().__init__(
            provider,
            f"Provider not available. Set {api_key_env_var} environment variable.",
        )
