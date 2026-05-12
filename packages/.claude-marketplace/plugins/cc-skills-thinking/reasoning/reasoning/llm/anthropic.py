"""Anthropic LLM provider for reasoning engine."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from .base import LLMProvider

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic


class AnthropicProvider:
    """Anthropic LLM provider using the official SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        timeout: float = 60.0,
    ) -> None:
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env var)
            model: Model ID to use
            timeout: Request timeout in seconds
        """
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._model = model
        self._timeout = timeout
        self._client: AsyncAnthropic | None = None

    @property
    def client(self) -> AsyncAnthropic:
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            import anthropic

            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        return self._client

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate response from Anthropic.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Generated response text
        """
        response = await self.client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    async def generate_with_history(
        self,
        prompt: str,
        history: list[dict],
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate response with conversation history.

        Args:
            prompt: Current prompt
            history: Previous conversation history as [{role, content}, ...]
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Generated response text
        """
        messages = []
        for entry in history:
            messages.append(
                {
                    "role": entry.get("role", "user"),
                    "content": entry.get("content", ""),
                }
            )
        messages.append({"role": "user", "content": prompt})

        response = await self.client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,  # type: ignore[arg-type]
        )
        return response.content[0].text