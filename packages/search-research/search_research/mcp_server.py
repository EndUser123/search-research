"""MCP server re-export for search-research package.

This module re-exports the MCP server from core.mcp_server, allowing
python -m search_research.mcp_server to work via the stdio registration.
"""

from core.mcp_server import mcp, main

__all__ = ["mcp", "main"]
