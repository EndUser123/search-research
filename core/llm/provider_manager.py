"""Provider manager wrapper for research LLM services.

Integrates with UnifiedProviderManager from llm_providers module.
"""

from typing import Any
import logging

logger = logging.getLogger(__name__)

# Lazy import of UnifiedProviderManager to avoid circular dependencies
_manager_instance = None


def get_research_llm_manager() -> Any:
    """Get or create the research LLM manager instance.
    
    Returns:
        UnifiedProviderManager configured for research tasks.
    """
    global _manager_instance
    
    if _manager_instance is None:
        try:
            from csf.llm_providers import UnifiedProviderManager
            _manager_instance = UnifiedProviderManager()
            logger.debug("Initialized UnifiedProviderManager for research")
        except ImportError as e:
            logger.warning(f"llm_providers not available: {e}")
            _manager_instance = None
    
    return _manager_instance


async def generate_with_fallback(
    prompt: str,
    system_prompt: str | None = None,
    max_tokens: int = 2000,
    temperature: float = 0.7
) -> tuple[str, bool]:
    """Generate text using LLM provider.

    FAIL-FAST: Requires LLM provider to be available.
    No mock fallback is provided - missing providers will raise an error.

    Args:
        prompt: The user prompt.
        system_prompt: Optional system prompt.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.

    Returns:
        Tuple of (generated_text, success_flag).

    Raises:
        RuntimeError: If LLM provider manager is not available.
    """
    manager = get_research_llm_manager()

    if manager is None:
        raise RuntimeError(
            "LLM provider manager is not available. "
            "Configure at least one LLM provider in llm_providers."
        )

    try:
        # Use UnifiedProviderManager's async generate
        response = await manager.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            task_category="research"
        )

        if response and response.success:
            return response.content, True
        else:
            # Provider returned unsuccessful response
            error_msg = getattr(response, 'error', 'Unknown error') if response else 'No response'
            raise RuntimeError(f"LLM generation failed: {error_msg}")

    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise  # Re-raise for fail-fast behavior
