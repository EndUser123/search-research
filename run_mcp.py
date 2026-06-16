#!/usr/bin/env python
"""Wrapper to run search-research MCP server via FastMCP.

This script bypasses the -m invocation to avoid a uv/Python subprocess
interaction that causes mcp.run() to exit silently on Windows.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from search_research.mcp_server import mcp
mcp.run()
