"""Web search providers for comprehensive research.

This module provides web search providers that integrate with external APIs:
- Tavily: AI-powered search with answer generation
- Serper: Google Search API wrapper
- Exa: Semantic search for research
- Brave: Privacy-focused search
- Bing: Microsoft Search API
- Google: Google Custom Search API
- Kagi: Premium search with AI summaries
- You.com: Privacy-focused AI search
- Mojeek: Independent search engine

All providers implement BaseWebBackend protocol for consistent interface.
"""

from .base_web import BaseWebBackend, ProviderError, ProviderNotAvailableError
from .bing import BingBackend
from .brave import BraveBackend
from .ddgs_backend import DDGsBackend
from .exa import ExaBackend
from .mmx_backend import MMXBackend
from .zai_backend import ZAIBackend
from .google import GoogleBackend
from .kagi import KagiBackend
from .mojeek import MojeekBackend
from .serper import SerperBackend
from .tavily import TavilyBackend
from .you import YouBackend

__all__ = [
    "BaseWebBackend",
    "ProviderError",
    "ProviderNotAvailableError",
    "TavilyBackend",
    "SerperBackend",
    "ExaBackend",
    "BraveBackend",
    "DDGsBackend",
    "MMXBackend",
    "ZAIBackend",
    "BingBackend",
    "GoogleBackend",
    "KagiBackend",
    "YouBackend",
    "MojeekBackend",
]
