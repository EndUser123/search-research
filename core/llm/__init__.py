"""LLM services layer for research system.

Provides HyDE generation, query enhancement, and content synthesis
using the UnifiedProviderManager from llm_providers.
"""

from .hyde_generator import HyDEGenerator
from .provider_manager import get_research_llm_manager

__all__ = [
    "HyDEGenerator",
    "get_research_llm_manager",
]
