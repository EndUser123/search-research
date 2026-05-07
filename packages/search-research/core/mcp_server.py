"""MCP server for unified search across local and web sources.

This module provides a Model Context Protocol (MCP) server that exposes
unified search capabilities via stdio. It uses FastMCP for protocol handling
and delegates to UnifiedAsyncRouter for actual search execution.

Architecture:
    - Thin protocol wrapper around existing search infrastructure
    - Layer 1 filtering (rule-based, clustering, complexity) - pure Python
    - Layer 2 (Agent semantic filtering) - NOT exposed via MCP (see below)
    - Layer 3 (presentation) - markdown formatting

Layer 2 Semantic Filtering Status:
    The /all skill provides Agent-based semantic filtering (Layer 2) that
    extracts key insights and groups results by theme. This is NOT currently
    exposed via MCP for the following reasons:

    1. **MCP subprocess limitation**: Agent tool is only available in skill
       execution context, not subprocess mode where MCP server runs.

    2. **Performance considerations**: Agent-based filtering adds 3-5 seconds
       of overhead, which may not be desirable for programmatic access.

    3. **Use case separation**: MCP is for programmatic access (tools, APIs),
       while /all skill is for interactive human consumption.

    Future enhancement: If Agent-based filtering is needed via MCP, consider:
    - Adding an `enable_semantic_filter: bool` parameter to unified_search
    - Running Agent tool in a separate Claude Code process and passing results
    - Implementing a lighter-weight keyword-based fallback for subprocess mode

CKS Integration:
    The Constitutional Knowledge System (CKS) provides knowledge management
    with SQLite storage and FAISS vector search. Exposed via MCP for:
    - Knowledge ingestion (memories, patterns, corrections, decisions)
    - Full-text search (FTS5)
    - Semantic/vector search with embeddings

Example:
    # Run server directly
    python -m search_research.mcp_server

    # Or via uv
    uv --directory P:\\\\packages/search-research run python -m search_research.mcp_server
"""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import Any

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .cks.unified import CKS
from .quality_checker import QualityConfig
from .router_async import AsyncSearchRouter, SearchResult
from .unified_router import UnifiedAsyncRouter

logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("search-research")


@functools.cache
def _get_cks() -> CKS:
    """Get or create CKS instance (thread-safe singleton via functools.cache).

    Uses config.CKS_DB_PATH as the authoritative source of truth for the DB path.
    """
    from .config import config as _search_config

    return CKS(db_path=Path(_search_config.CKS_DB_PATH))


def _search_result_to_dict(result: SearchResult) -> dict[str, Any]:
    """Convert SearchResult to dictionary for JSON serialization.

    Args:
        result: SearchResult object to convert

    Returns:
        Dictionary with all result fields
    """
    return {
        "title": result.title,
        "content": result.content,
        "score": result.score,
        "source": result.source,
        "url": result.url,
        "file_path": result.file_path,
        "line_number": result.line_number,
        "metadata": result.metadata or {},
    }


def _format_markdown_results(
    *,
    query: str,
    mode: str,
    duration: float,
    result_count: int,
    format_item: Callable[[int], list[str]],
    empty_message: str = "No results found.",
) -> str:
    """Unified markdown formatter for search results.

    Args:
        query: Original search query
        mode: Search mode/type used
        duration: Search duration in seconds
        result_count: Number of results
        format_item: Callback that takes result index (1-based) and returns formatted lines
        empty_message: Message to show when no results

    Returns:
        Markdown formatted results string
    """
    output = [f'## Search Results: "{query}"']
    output.append(
        f"**Mode**: {mode} | **Duration**: {duration:.2f}s | **Results**: {result_count}\n"
    )

    if result_count == 0:
        output.append(empty_message)
        return "\n".join(output)

    for i in range(1, result_count + 1):
        output.extend(format_item(i))

    return "\n".join(output)


def _format_results_as_markdown(
    results: list[SearchResult],
    query: str,
    mode: str,
    duration: float,
) -> str:
    """Format search results as markdown.

    Args:
        results: List of search results
        query: Original search query
        mode: Search mode used
        duration: Search duration in seconds

    Returns:
        Markdown formatted results string
    """

    def format_item(i: int) -> list[str]:
        result = results[i - 1]
        lines = []
        score = getattr(result, "score", 0.0)
        title = getattr(result, "title", "Untitled")
        source = getattr(result, "source", "UNKNOWN")
        url = getattr(result, "url", "")
        content = getattr(result, "content", "")[:300]

        lines.append(f"### {i}. {title}")
        lines.append(f"**Source**: {source} | **Score**: {score:.2f}")

        if url:
            lines.append(f"**URL**: {url}")

        if result.file_path:
            lines.append(f"**File**: {result.file_path}")
            if result.line_number:
                lines.append(f"**Line**: {result.line_number}")

        lines.append(f"**Preview**: {content}...")
        lines.append("")
        return lines

    return _format_markdown_results(
        query=query,
        mode=mode,
        duration=duration,
        result_count=len(results),
        format_item=format_item,
        empty_message="No results found.",
    )


@mcp.tool(description="""Unified search across local and web sources with intelligent routing.

Use when: user asks something like "find how X works in our codebase", "search for Y",
or wants results from both local files and the web simultaneously.

Use local_search instead when: query is clearly local-only
(e.g., "find all uses of function X", "search our docs for Y").

Use web_search instead when: query is clearly web-only
(e.g., "latest Next.js docs", "how does library X work" with no local context needed).

mode: "auto" (default) tries local fast, quality-gates web;
"local-only" for fast local-only; "web-fallback" for quality-gated web;
"unified" for simultaneous local+web.

Returns: markdown with title, source, score, URL/file_path, and content preview per result.""")
async def unified_search(
    query: str,
    mode: str = "auto",
    limit: int = 30,
    min_score: float = 0.5,
    min_results: int = 3,
) -> str:
    """Search with intelligent routing combining local and web sources.

    Progressive enhancement:
    1. Fast local search (<1s)
    2. Quality check determines if web search needed
    3. Web search only if quality check fails (5-10s)
    4. RRF fusion merges results

    Args:
        query: Search query string
        mode: Routing mode - "auto" (progressive), "local-only" (fast),
              "web-fallback" (quality-gated), "unified" (comprehensive)
        limit: Maximum number of results to return (default: 30)
        min_score: Minimum quality threshold for local results (default: 0.5)
        min_results: Minimum number of satisfactory results required (default: 3)

    Returns:
        Markdown formatted search results

    Raises:
        ValueError: If query is empty or mode is invalid
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    valid_modes = ["auto", "local-only", "web-fallback", "unified"]
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}")

    start_time = time.time()

    try:
        # Configure quality thresholds
        quality_config = QualityConfig(
            confidence_threshold=min_score,
        )

        # Create unified router
        router = UnifiedAsyncRouter(
            mode=mode,
            quality_config=quality_config,
        )

        # Execute search
        results = await router.search_async(query, limit=limit)
        duration = time.time() - start_time

        return _format_results_as_markdown(results, query, mode, duration)

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        duration = time.time() - start_time
        return f'## Search Error\n\nQuery: "{query}"\nMode: {mode}\nDuration: {duration:.2f}s\n\nError: {e}'


@mcp.tool(description="""Fast local-only search across codebase, knowledge base, and docs.

Use when: query is clearly local — "find all uses of function X", "search our docs for Y",
"where is Z defined", "grep for pattern X in the codebase".

Also use when: results are needed fast (<1s) and web search is unnecessary.

Do NOT use for: general knowledge questions, documentation lookup, or queries about
things outside the codebase (use web_search instead).

Returns: markdown with title, source, score, file_path/line_number, and content preview per result.""")
async def local_search(
    query: str,
    limit: int = 30,
    min_score: float = 0.0,
) -> str:
    """Search local sources only - fast, private, no API calls.

    Searches across:
    - Code files (grep-based)
    - Chat history (CKS)
    - Documentation
    - Knowledge base

    Args:
        query: Search query string
        limit: Maximum number of results to return (default: 30)
        min_score: Minimum relevance score threshold (default: 0.0)

    Returns:
        Markdown formatted search results

    Raises:
        ValueError: If query is empty
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    start_time = time.time()

    try:
        # Create local-only router
        router = UnifiedAsyncRouter(mode="local-only")

        # Execute search
        results = await router.search_async(query, limit=limit)
        duration = time.time() - start_time

        # Filter by min_score
        filtered = [r for r in results if r.score >= min_score]

        return _format_results_as_markdown(filtered, query, "local-only", duration)

    except Exception as e:
        logger.error(f"Local search failed: {e}", exc_info=True)
        duration = time.time() - start_time
        return f'## Local Search Error\n\nQuery: "{query}"\nDuration: {duration:.2f}s\n\nError: {e}'


@mcp.tool(description="""Web-only search across multiple providers (Tavily, Serper, Exa, Brave).

Use when: query is clearly web-only — "latest Next.js docs", "how does library X work",
"best practices for Y", "Python package Z documentation", "current status of X".

Do NOT use for: searching local codebase, files, or anything that lives in the repo
(use local_search instead). Only use when the answer lives on the web.

Returns: markdown with title, source, score, URL, and content preview per result.""")
async def web_search(
    query: str,
    limit: int = 30,
) -> str:
    """Search web providers only - current docs, best practices, external research.

    Providers used (based on API key availability):
    - Tavily (comprehensive research)
    - Serper (Google Search)
    - Exa (semantic search)
    - Brave (privacy-focused)

    Args:
        query: Search query string
        limit: Maximum number of results to return (default: 30)

    Returns:
        Markdown formatted search results

    Raises:
        ValueError: If query is empty
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    start_time = time.time()

    try:
        # Create web search router
        router = AsyncSearchRouter()

        # Execute web search only
        results = await router.search_web_providers_async(query, limit=limit)
        duration = time.time() - start_time

        return _format_results_as_markdown(results, query, "web-only", duration)

    except Exception as e:
        logger.error(f"Web search failed: {e}", exc_info=True)
        duration = time.time() - start_time
        return f'## Web Search Error\n\nQuery: "{query}"\nDuration: {duration:.2f}s\n\nError: {e}'


# ============================================================================
# CKS Tools - Constitutional Knowledge System
# ============================================================================


def _format_cks_results_as_markdown(
    results: list[dict[str, Any]],
    query: str,
    search_type: str,
    duration: float,
) -> str:
    """Format CKS search results as markdown.

    Args:
        results: List of CKS result dictionaries
        query: Original search query
        search_type: Type of search (fts or semantic)
        duration: Search duration in seconds

    Returns:
        Markdown formatted results string
    """
    output = [f'## CKS Search Results: "{query}"']
    output.append(
        f"**Type**: {search_type} | **Duration**: {duration:.2f}s | **Results**: {len(results)}\n"
    )

    if not results:
        output.append("No results found in knowledge base.")
        return "\n".join(output)

    for i, result in enumerate(results, 1):
        title = result.get("title", "Untitled")
        entry_type = result.get("type", "unknown")
        score = result.get("score", 0.0)
        content = result.get("content", "")[:300]
        entry_id = result.get("id", "")

        output.append(f"### {i}. {title}")
        output.append(f"**Type**: {entry_type} | **Score**: {score:.2f}")

        if entry_id:
            output.append(f"**ID**: {entry_id}")

        output.append(f"**Preview**: {content}...")
        output.append("")

    return "\n".join(output)


@mcp.tool(description="""Search the Constitutional Knowledge System (CKS) using full-text search.

Use when: user asks about past decisions, patterns, corrections, or learnings stored in CKS.
Examples: "what decision did we make about X", "show me our logging patterns",
"any corrections related to Y", "what do we know about Z pattern".

CKS stores: memories, patterns, code snippets, corrections, decisions, commitments, insights, learnings.

Returns: markdown with title, entry_type, score, and content preview per result.""")
def cks_search(
    query: str,
    entry_type: str | None = None,
    limit: int = 10,
) -> str:
    """Search CKS knowledge base using FTS5 full-text search.

    Searches across all stored knowledge including:
    - Memories (chat history, Q&A)
    - Patterns (documentation, best practices)
    - Code snippets
    - Corrections (mistakes and fixes)
    - Decisions (choices and rationale)
    - Learnings (lessons learned)

    Args:
        query: Search query string
        entry_type: Optional filter by type (memory, pattern, code, correction,
                   decision, commitment, insight, learning, knowledge)
        limit: Maximum number of results to return (default: 10)

    Returns:
        Markdown formatted search results

    Raises:
        ValueError: If query is empty
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    start_time = time.time()

    try:
        cks = _get_cks()
        results = cks.search(query, entry_type=entry_type, limit=limit)
        duration = time.time() - start_time

        return _format_cks_results_as_markdown(results, query, "fts", duration)

    except Exception as e:
        logger.error(f"CKS search failed: {e}", exc_info=True)
        duration = time.time() - start_time
        return f'## CKS Search Error\n\nQuery: "{query}"\nDuration: {duration:.2f}s\n\nError: {e}'


@mcp.tool(description="""Search CKS using semantic/vector search with embeddings.

Use when: user asks about related concepts, similar patterns, or things where exact
keyword matching isn't needed. Best for: "find patterns like X", "what's similar to Y",
"concepts related to Z even if worded differently".

Use cks_search (FTS) instead when: query has specific keywords that should match exactly
or when entry_type filtering is needed.

expand_query: enable to break complex queries into multiple searches for better recall.

Returns: markdown with title, entry_type, score, and content preview per result.""")
def cks_search_semantic(
    query: str,
    entry_type: str | None = None,
    limit: int = 10,
    expand_query: bool = False,
) -> str:
    """Search CKS knowledge base using semantic vector search.

    Uses sentence embeddings to find conceptually similar content,
    even if exact keywords don't match. Best for:
    - Finding related concepts
    - Discovering similar patterns
    - Cross-domain knowledge retrieval

    Args:
        query: Search query string
        entry_type: Optional filter by type (memory, pattern, code, etc.)
        limit: Maximum number of results to return (default: 10)
        expand_query: Enable query expansion for better recall (default: False)

    Returns:
        Markdown formatted search results with similarity scores

    Raises:
        ValueError: If query is empty
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    start_time = time.time()

    try:
        cks = _get_cks()
        results = cks.search_semantic(
            query,
            entry_type=entry_type,
            limit=limit,
            expand_query=expand_query,
        )
        duration = time.time() - start_time

        return _format_cks_results_as_markdown(results, query, "semantic", duration)

    except Exception as e:
        logger.error(f"CKS semantic search failed: {e}", exc_info=True)
        duration = time.time() - start_time
        return f'## CKS Semantic Search Error\n\nQuery: "{query}"\nDuration: {duration:.2f}s\n\nError: {e}'


@mcp.tool(description="""Store knowledge in CKS for future retrieval.

Use when: capturing decisions, patterns, corrections, insights, or learnings to remember.
Examples: "remember we decided X because Y", "note that pattern Z is preferred over Q",
"store this insight about W", "log that we fixed bug X by doing Y".

entry_type options: memory, pattern, code, correction, decision, commitment, insight, learning, knowledge.

Returns: success message with entry ID.""")
def cks_ingest(
    content: str,
    title: str | None = None,
    entry_type: str = "knowledge",
    category: str | None = None,
) -> str:
    """Store knowledge in CKS for future retrieval.

    Entry types and when to use them:
    - memory: Chat history, Q&A pairs, conversations
    - pattern: Documentation, best practices, reusable solutions
    - code: Code snippets, examples, implementations
    - correction: Mistakes and their fixes
    - decision: Choices made and rationale
    - commitment: Promises or resolutions
    - insight: Realizations, aha moments
    - learning: Lessons learned from experience
    - knowledge: General factual knowledge (default)

    Args:
        content: The knowledge content to store
        title: Optional title (auto-generated from content if not provided)
        entry_type: Type of knowledge entry (default: knowledge)
        category: Optional category for organization

    Returns:
        Success message with entry ID or error message

    Raises:
        ValueError: If content is empty
    """
    if not content or not content.strip():
        raise ValueError("Content cannot be empty")

    try:
        cks = _get_cks()

        # Route to appropriate ingest method based on entry_type
        if entry_type == "memory":
            # For memories, treat title as question if provided
            question = title or content[:80]
            entry_id = cks.ingest_memory(question, content)
        elif entry_type == "pattern":
            pattern_title = title or content[:80]
            entry_id = cks.ingest_pattern(pattern_title, content)
        elif entry_type == "correction":
            correction_title = title or content[:80]
            entry_id = cks.ingest_correction(correction_title, content)
        elif entry_type == "decision":
            decision_title = title or content[:80]
            entry_id = cks.ingest_decision(decision_title, content)
        elif entry_type == "commitment":
            commitment_title = title or content[:80]
            entry_id = cks.ingest_commitment(commitment_title, content)
        elif entry_type == "insight":
            insight_title = title or content[:80]
            entry_id = cks.ingest_insight(insight_title, content)
        elif entry_type == "learning":
            learning_title = title or content[:80]
            entry_id = cks.ingest_learning(learning_title, content)
        else:
            # Default: use pattern for generic knowledge
            pattern_title = title or content[:80]
            entry_id = cks.ingest_pattern(pattern_title, content, entry_type=entry_type)

        return f"✅ Knowledge stored successfully\n\n**ID**: {entry_id}\n**Type**: {entry_type}\n**Title**: {title or 'Auto-generated'}"

    except Exception as e:
        logger.error(f"CKS ingest failed: {e}", exc_info=True)
        return f"## CKS Ingest Error\n\nError: {e}"


@mcp.tool(description="Get statistics about the Constitutional Knowledge System")
def cks_stats() -> str:
    """Get statistics about the CKS knowledge base.

    Returns counts by entry type, database size, and index status.

    Returns:
        JSON-formatted statistics about the CKS database
    """
    try:
        cks = _get_cks()
        stats = cks.get_statistics()

        output = ["## CKS Statistics\n"]
        output.append(f"**Total Entries**: {stats.get('total_entries', 0)}")
        output.append(
            f"**Database Size**: {stats.get('database_size_bytes', 0) / (1024 * 1024):.2f} MB"
        )

        # Entry type breakdown
        by_type = stats.get("by_type", {})
        if by_type:
            output.append("\n### Entries by Type")
            for entry_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
                output.append(f"- **{entry_type}**: {count}")

        # Semantic search status
        output.append(f"\n**Semantic Search**: {'Enabled' if cks.enable_semantic else 'Disabled'}")

        return "\n".join(output)

    except Exception as e:
        logger.error(f"CKS stats failed: {e}", exc_info=True)
        return f"## CKS Stats Error\n\nError: {e}"


def main() -> None:
    """Entry point for running the MCP server.

    The server communicates via stdio using the MCP protocol.
    """
    mcp.run()


if __name__ == "__main__":
    main()
