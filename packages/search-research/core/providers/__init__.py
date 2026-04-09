"""Web search providers for comprehensive research.

This module provides web search providers that integrate with external APIs:
- Tavily: AI-powered search with answer generation
- Serper: Google Search API wrapper
- Exa: Semantic search for research
- YouTube: YouTube video transcript search (yt-dlp + intelligence-stream)
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
from .exa import ExaBackend
from .google import GoogleBackend
from .kagi import KagiBackend
from .mojeek import MojeekBackend
from .serper import SerperBackend
from .tavily import TavilyBackend
from .you import YouBackend
from .youtube import YouTubeBackend

__all__ = [
    "BaseWebBackend",
    "ProviderError",
    "ProviderNotAvailableError",
    "TavilyBackend",
    "SerperBackend",
    "ExaBackend",
    "YouTubeBackend",
    "BraveBackend",
    "BingBackend",
    "GoogleBackend",
    "KagiBackend",
    "YouBackend",
    "MojeekBackend",
]
