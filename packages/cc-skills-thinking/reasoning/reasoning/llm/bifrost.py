"""Bifrost LLM provider for reasoning engine.

Wraps bf_agent from P:/tools/mcp/bf_agent.py for external LLM access.
Uses Bifrost's routing infrastructure (models, targets, etc.) via HTTP.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .base import LLMProvider

# Add bf_agent path
BF_AGENT_PATH = Path("P:/tools/mcp")
if str(BF_AGENT_PATH) not in sys.path:
    sys.path.insert(0, str(BF_AGENT_PATH))

if TYPE_CHECKING:
    from bf_agent import run_simple as _bf_run_simple
    from bf_agent import run_compare as _bf_run_compare


class BifrostProvider:
    """Bifrost LLM provider using bf_agent library.

    Wraps run_simple() and run_compare() from P:/tools/mcp/bf_agent.py.
    Supports modes: brainstorm, design, plan, review, explore, compare, code.
    """

    def __init__(
        self,
        default_model: str = "DSv4-flash",
        default_mode: str = "brainstorm",
        timeout_ms: int = 120000,
    ) -> None:
        """
        Initialize Bifrost provider.

        Args:
            default_model: Default model alias (e.g., "DSv4-flash", "M27", "GLM-5.1")
            default_mode: Default run mode (brainstorm/design/plan/review/explore/compare/code)
            timeout_ms: Request timeout in milliseconds
        """
        self._default_model = default_model
        self._default_mode = default_mode
        self._timeout_ms = timeout_ms

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate response from Bifrost (run_simple).

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate (passed as part of response)
            temperature: Sampling temperature (passed to bf_agent)

        Returns:
            Generated response text
        """
        import asyncio

        def _sync_call() -> dict:
            from bf_agent import run_simple

            return run_simple(
                mode=self._default_mode,
                prompt=prompt,
                model=self._default_model,
            )

        result = await asyncio.to_thread(_sync_call)

        if not result.get("ok", False):
            error = result.get("error", "Unknown error")
            raise RuntimeError(f"Bifrost error: {error}")

        return result.get("text", "")

    async def generate_with_history(
        self,
        prompt: str,
        history: list[dict],
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate response with conversation history via compare mode.

        Args:
            prompt: Current prompt
            history: Previous conversation history as [{role, content}, ...]
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated response text
        """
        import asyncio

        # Build context from history
        history_text = ""
        for entry in history:
            role = entry.get("role", "user")
            content = entry.get("content", "")
            history_text += f"\n{role.capitalize()}: {content}"

        full_prompt = f"{history_text}\n\nUser: {prompt}"

        def _sync_call() -> dict:
            from bf_agent import run_compare

            return run_compare(
                prompt=full_prompt,
                models=[self._default_model],
            )

        result = await asyncio.to_thread(_sync_call)

        if not result.get("ok", False):
            error = result.get("error", "Unknown error")
            raise RuntimeError(f"Bifrost compare error: {error}")

        # Extract from compare results
        results = result.get("results", [])
        if results:
            return results[0].get("text", "")

        return result.get("synthesis", "")

    def get_available_models(self) -> list[str]:
        """Get list of available models from Bifrost catalog."""
        import asyncio

        def _sync_call() -> list[dict]:
            from bf_agent import list_catalog_models

            return list_catalog_models(min_context=128000, free_only=True)

        return asyncio.to_thread(_sync_call)