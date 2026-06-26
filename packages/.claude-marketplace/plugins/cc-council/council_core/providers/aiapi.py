from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass
from typing import Any

from pathlib import Path
from council_core.contracts.types import (
    ModelCapability,
    ProviderAdapter,
    ProviderHealth,
)

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_MS = 60000
DEFAULT_CONCURRENCY = 3
DEFAULT_TRANSPORT_DIR = os.getenv(
    "CC_COUNCIL_TRANSPORT_DIR",
    str(Path(__file__).parent.parent.parent / "cc-skills-ai-api" / "skills" / "ai-api")
)


@dataclass
class AIAPIConfig:
    """Configuration for ai-api provider adapter."""

    max_concurrency: int = DEFAULT_CONCURRENCY
    health_check_model: str = os.getenv("CC_COUNCIL_HEALTH_MODEL", "m3")


class AIAPIProvider(ProviderAdapter):
    """Adapter wrapping ai-api transport layer."""

    provider_id = "ai-api"

    def __init__(self, config: AIAPIConfig | None = None):
        self.config = config or AIAPIConfig()
        self._transport = None
        self._available_models: list[str] = []
        self._health_checked: bool = False

    def _get_transport(self):
        if self._transport is None:
            import importlib.util
            import sys
            transport_dir = Path(DEFAULT_TRANSPORT_DIR)
            if not transport_dir.exists():
                # Fallback to relative path for development
                transport_dir = Path(__file__).parent.parent.parent / "cc-skills-ai-api" / "skills" / "ai-api"
            if str(transport_dir) not in sys.path:
                sys.path.insert(0, str(transport_dir))
            import transport
            self._transport = transport
        return self._transport

    async def health_check(self) -> ProviderHealth:
        try:
            transport = self._get_transport()
            health_model = self.config.health_check_model
            provider = transport._provider_hint_for_model(health_model)
            if not provider:
                return ProviderHealth(
                    provider_id=self.provider_id,
                    is_healthy=False,
                    available_models=[],
                    error_message=f"Unknown provider for health model: {health_model}",
                )
            result = transport._sdk_call(
                provider=provider,
                model=health_model,
                prompt="ok",
                correlation_id=str(uuid.uuid4()),
                compare_id="",
                max_tokens=5,
            )
            if result.get("ok"):
                return ProviderHealth(
                    provider_id=self.provider_id,
                    is_healthy=True,
                    available_models=[health_model],
                )
            return ProviderHealth(
                provider_id=self.provider_id,
                is_healthy=True,
                available_models=[],
                error_message="No configured models responded",
            )
        except ImportError as e:
            logger.error("ai-api transport not available: %s", e)
            return ProviderHealth(
                provider_id=self.provider_id,
                is_healthy=False,
                available_models=[],
                error_message=f"Transport module not found: {e}",
            )
        except Exception as e:
            logger.exception("ai-api health check failed: %s", e)
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
        system_prompt: str | None = None,
    ) -> str:
        transport = self._get_transport()
        # Resolve provider from model name
        provider = transport._provider_hint_for_model(model)
        if not provider:
            raise RuntimeError(f"Unknown provider for model: {model}")
        result = transport._sdk_call(
            provider=provider,
            model=model,
            prompt=prompt,
            correlation_id=str(uuid.uuid4()),
            compare_id="",
            system=system_prompt,
            max_tokens=max_tokens,
        )
        if not result.get("ok"):
            error = result.get("error", "Unknown error")
            raise RuntimeError(f"Generation failed for {model}: {error}")
        return result.get("text", "")

    async def get_model_capabilities(self, model: str) -> ModelCapability:
        # Capabilities should be sourced from provider metadata, not hardcoded.
        # TODO: Integrate with model_capabilities.json or provider APIs.
        return ModelCapability(
            name=model,
            max_context=0,  # Unknown - get from provider
            supports_json=True,  # Most modern models support JSON
            estimated_latency_ms=1000,  # Unknown - measure empirically
            resource_score=5,  # Default
        )

    async def list_models(self) -> list[str]:
        """List available models from SDK provider configs and environment."""
        transport = self._get_transport()
        models = []

        # Map providers to their known models
        PROVIDER_MODELS: dict[str, list[str]] = {
            "minimax": ["m3"],
            "z.ai": ["glm-5.2"],
            "opencode-go": ["deepseek-chat", "deepseek-coder"],
            "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
            "mistral": ["mistral-large-latest", "codestral-latest"],
            "cerebras": ["llama3.1-70b"],
            "nvidia": ["meta/llama-3.1-405b-instruct", "meta/llama-3.1-70b-instruct"],
        }

        # Get models from SDK provider configs
        for provider, known_models in PROVIDER_MODELS.items():
            config = transport._SDK_PROVIDER_CONFIGS.get(provider, {})
            api_key = os.getenv(config.get("api_key_env", ""))
            if api_key:
                models.extend(known_models)

        # Add local LM Studio models
        lmstudio_models = os.getenv("BF_LOCAL_LMSTUDIO_MODELS", "").strip()
        if lmstudio_models:
            models.extend([m.strip() for m in lmstudio_models.split(",") if m.strip()])

        return list(set(models))

    def get_concurrency_limit(self) -> int:
        return self.config.max_concurrency


def create_provider(config: AIAPIConfig | None = None) -> AIAPIProvider:
    return AIAPIProvider(config)
