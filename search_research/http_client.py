"""Re-export core.http_client so `from search_research.http_client import ...` resolves.

The web provider clients (serper_client.py, tavily_client.py) import via this path.
"""

from core.http_client import *  # noqa: F401,F403
from core.http_client import get_async_client

__all__ = ["get_async_client"]
