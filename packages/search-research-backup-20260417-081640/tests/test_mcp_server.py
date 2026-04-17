"""Tests for MCP server.

Run with:
    cd P:/packages/search-research
    uv run pytest tests/test_mcp_server.py -v
"""

import sys
from pathlib import Path

import pytest

# Add src to path
src_path = Path(__file__).parent.parent / "core"
sys.path.insert(0, str(src_path))


@pytest.mark.asyncio
async def test_unified_search_tool_exists():
    """Test that unified_search tool can be imported."""
    from mcp_server import unified_search

    assert callable(unified_search)


@pytest.mark.asyncio
async def test_local_search_tool_exists():
    """Test that local_search tool can be imported."""
    from mcp_server import local_search

    assert callable(local_search)


@pytest.mark.asyncio
async def test_web_search_tool_exists():
    """Test that web_search tool can be imported."""
    from mcp_server import web_search

    assert callable(web_search)


@pytest.mark.asyncio
async def test_mcp_server_imports():
    """Test that MCP server dependencies can be imported."""
    # This will fail if mcp/fastmcp are not installed
    try:
        from mcp.server.fastmcp import FastMCP
        from pydantic import BaseModel, Field

        assert FastMCP is not None
        assert BaseModel is not None
        assert Field is not None
    except ImportError as e:
        pytest.skip(f"MCP dependencies not installed: {e}")


@pytest.mark.asyncio
async def test_unified_router_import():
    """Test that UnifiedAsyncRouter can be imported."""
    from core.unified_router import UnifiedAsyncRouter

    router = UnifiedAsyncRouter(mode="local-only")
    assert router is not None
    assert router.mode == "local-only"


@pytest.mark.asyncio
async def test_local_search_basic():
    """Test basic local search functionality."""
    from mcp_server import local_search

    # Simple test query
    result = await local_search(query="test", limit=5)

    # Should return a string (markdown formatted)
    assert isinstance(result, str)
    assert len(result) > 0
    # Should contain markdown headers
    assert "##" in result or "Search Results" in result


@pytest.mark.asyncio
async def test_unified_search_modes():
    """Test that unified_search accepts valid modes."""
    from mcp_server import unified_search

    valid_modes = ["auto", "local-only", "web-fallback", "unified"]

    for mode in valid_modes:
        # Should not raise for valid modes
        result = await unified_search(query="test", mode=mode, limit=1)
        assert isinstance(result, str)


@pytest.mark.asyncio
async def test_search_results_format():
    """Test that search results are properly formatted."""
    from mcp_server import _format_results_as_markdown

    # Sample results
    results = [
        {
            "title": "Test Result 1",
            "url": "https://example.com/1",
            "content": "Sample content for result 1",
            "score": 0.95,
            "source": "LOCAL",
        },
        {
            "title": "Test Result 2",
            "url": "https://example.com/2",
            "content": "Sample content for result 2",
            "score": 0.87,
            "source": "WEB",
        },
    ]

    formatted = _format_results_as_markdown(results, "test query", "auto", 1.5)

    # Check markdown structure
    assert "## Search Results" in formatted
    assert "test query" in formatted
    assert "Test Result 1" in formatted
    assert "Test Result 2" in formatted
    assert "0.95" in formatted
    assert "LOCAL" in formatted
    assert "WEB" in formatted


@pytest.mark.asyncio
async def test_empty_results_formatting():
    """Test formatting of empty results."""
    from mcp_server import _format_results_as_markdown

    formatted = _format_results_as_markdown([], "test query", "auto", 0.5)

    assert "No results found" in formatted
    assert "test query" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
