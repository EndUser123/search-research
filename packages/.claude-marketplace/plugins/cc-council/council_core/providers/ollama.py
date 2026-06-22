"""Provider layer - Ollama adapter.

The provider interface is transport-agnostic. Ollama is the first
concrete implementation.

Local providers are treated as resource-constrained systems:
- Concurrency limits (CPU, memory)
- Health status monitoring
- Capability flags per model
- Resource-oriented status (not quota/rate-limit)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

import aiohttp

from council_core.contracts.types import (
    ModelCapability,
    ProviderAdapter,
    ProviderHealth,
)


logger = logging.getLogger(__name__)


# ── Configuration ───────────────────────────────────────────────────────────────

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_TIMEOUT_MS = 30000
DEFAULT_CONCURRENCY = 3


@dataclass
class OllamaConfig:
    """Configuration for Ollama provider."""

    base_url: str = DEFAULT_OLLAMA_BASE_URL
    timeout_ms: int = DEFAULT_TIMEOUT_MS
    max_concurrency: int = DEFAULT_CONCURRENCY
    request_timeout_s: int = 30


# ── Ollama Provider ───────────────────────────────────────────────────────────────


class OllamaProvider(ProviderAdapter):
    """Ollama HTTP API provider adapter.

    Uses Ollama's documented REST API:
    - POST /api/generate - Generate text
    - GET /api/tags - List models
    - GET /api/version - Health check

    Resource constraints:
    - Concurrency limit to avoid CPU/memory overload
    - Timeout per request
    - Health check before batch operations
    """

    provider_id = "ollama"

    def __init__(self, config: OllamaConfig | None = None):
        """Initialize Ollama provider.

        Args:
            config: Provider configuration (uses defaults if None)
        """
        self.config = config or OllamaConfig()
        self._session: aiohttp.ClientSession | None = None
        self._available_models: list[str] = []

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout_s)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session:
            await self._session.close()

    async def health_check(self) -> ProviderHealth:
        """Check if Ollama is available and list models."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.config.base_url}/api/version"
            ) as response:
                if response.status != HTTPStatus.OK:
                    return ProviderHealth(
                        provider_id=self.provider_id,
                        is_healthy=False,
                        available_models=[],
                        error_message=f"HTTP {response.status}",
                    )

                # Get model list
                async with session.get(
                    f"{self.config.base_url}/api/tags"
                ) as tags_response:
                    if tags_response.status != HTTPStatus.OK:
                        return ProviderHealth(
                            provider_id=self.provider_id,
                            is_healthy=True,
                            available_models=[],
                            error_message="Failed to list models",
                        )

                    data = await tags_response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    self._available_models = models

                    return ProviderHealth(
                        provider_id=self.provider_id,
                        is_healthy=True,
                        available_models=models,
                    )

        except aiohttp.ClientError as e:
            logger.error("Ollama health check failed: %s", e)
            return ProviderHealth(
                provider_id=self.provider_id,
                is_healthy=False,
                available_models=[],
                error_message=str(e),
            )
        except Exception as e:
            logger.exception("Ollama health check unexpected error: %s", e)
            return ProviderHealth(
                provider_id=self.provider_id,
                is_healthy=False,
                available_models=[],
                error_message=f"Unexpected error: {e}",
            )

    async def generate(
        self,
        model: str,
        prompt: str,
        *,
        max_tokens: int = 1024,
        timeout_ms: int = 30000,
        system_prompt: str | None = None,
    ) -> str:
        """Generate text from Ollama model.

        Args:
            model: Model name (e.g., "llama3:8b")
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            timeout_ms: Request timeout (overrides session timeout)
            system_prompt: Optional system message

        Returns:
            Generated text

        Raises:
            RuntimeError: If generation fails
        """
        session = await self._get_session()

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            timeout = aiohttp.ClientTimeout(total=timeout_ms / 1000)
            async with session.post(
                f"{self.config.base_url}/api/generate",
                json=payload,
                timeout=timeout,
            ) as response:
                if response.status != HTTPStatus.OK:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"Ollama generation failed: HTTP {response.status} - {error_text}"
                    )

                data = await response.json()
                return data.get("response", "")

        except aiohttp.ClientError as e:
            logger.error("Ollama generation failed for %s: %s", model, e)
            raise RuntimeError(f"Ollama request failed: {e}") from e
        except Exception as e:
            logger.exception("Ollama generation unexpected error: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e

    async def get_model_capabilities(self, model: str) -> ModelCapability:
        """Get capability flags for a model.

        This is estimated based on common patterns in model names.
        For production, query Ollama's model metadata API
        or use a capabilities database.

        Args:
            model: Model name

        Returns:
            Model capability information
        """
        # Rough estimates based on model name patterns
        model_lower = model.lower()

        if ":8b" in model_lower or "8b" in model_lower:
            max_context = 8192
            resource_score = 8
        elif ":7b" in model_lower or "7b" in model_lower:
            max_context = 8192
            resource_score = 7
        elif ":70b" in model_lower or "70b" in model_lower:
            max_context = 4096
            resource_score = 3
        elif "phi" in model_lower:
            # Phi models are smaller/faster
            max_context = 4096
            resource_score = 9
        else:
            max_context = 4096
            resource_score = 5

        # Most modern models support JSON
        supports_json = True

        # Latency estimate (resource-heavy = slower)
        estimated_latency_ms = (10 - resource_score) * 500 + 1000

        return ModelCapability(
            name=model,
            max_context=max_context,
            supports_json=supports_json,
            estimated_latency_ms=estimated_latency_ms,
            resource_score=resource_score,
        )

    async def list_models(self) -> list[str]:
        """List all available models.

        Caches results from health check if available.

        Returns:
            List of model names
        """
        if not self._available_models:
            health = await self.health_check()
            return health.available_models

        return self._available_models

    def get_concurrency_limit(self) -> int:
        """Return max concurrent requests for Ollama.

        Local models are resource-constrained. We limit concurrency
        to avoid CPU/memory overload on the host system.

        Returns:
            Maximum concurrent requests
        """
        return self.config.max_concurrency


# ── Future Provider Placeholders ──────────────────────────────────────────────────

# TODO: LM Studio adapter
# TODO: Direct GGUF/llama.cpp adapter
# TODO: vLLM REST API adapter
# TODO: OpenRouter (cloud) adapter with resource constraints