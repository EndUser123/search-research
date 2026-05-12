"""OpenAI LLM provider for reasoning engine."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from .base import LLMProvider

if TYPE_CHECKING:
    from openai import AsyncOpenAI


class OpenAIProvider:
    """OpenAI LLM provider using the official SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (falls back to OPENAI_API_KEY env var)
            model: Model ID to use
            base_url: Custom endpoint for compatible APIs (Ollama, LM Studio, etc.)
            timeout: Request timeout in seconds
        """
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._model = model
        self._base_url = base_url or os.environ.get("OPENAI_API_BASE", "")
        self._timeout = timeout
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            import openai

            kwargs: dict = {"api_key": self._api_key}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = openai.AsyncOpenAI(**kwargs)
        return self._client

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate response from OpenAI.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Generated response text
        """
        response = await self.client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

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

        response = await self.client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""