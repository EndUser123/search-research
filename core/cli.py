#!/usr/bin/env python3

"""
Core Search Research CLI - Focused on search providers only.

Supports: tavily, exa, glm, serpapi, webreader, webreader_mcp, github, notebooklm, claude
Modes: auto, web, quick
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Import from core package
try:
    from .config import ResearchConfig, config
except ImportError:
    # Support direct script invocation
    if __package__ in (None, ""):
        core_root = Path(__file__).resolve().parent
        if str(core_root) not in sys.path:
            sys.path.insert(0, str(core_root))
        from core.config import ResearchConfig, config
    else:
        raise

# Import from cli_shared for shared utilities (optional)
try:
    from research_skill.cli_shared import (
        _create_timing_result,
        format_result_as_json,
        save_result_to_file,
    )
except ImportError:
    # Define locally if not available
    def _create_timing_result(
        base_result: dict[str, Any], provider: str, duration_ms: float
    ) -> dict[str, Any]:
        """Add timing metadata to a search result."""
        base_result["timing"] = {
            "provider": provider,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
        }
        return base_result

    def format_result_as_json(result: dict) -> str:
        """Format research result as JSON."""
        return json.dumps(result, indent=2, ensure_ascii=False)

    def save_result_to_file(result: dict, filepath: str) -> None:
        """Save research result to file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        if filepath.suffix == ".json":
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("# Research Results\n\n")
                f.write(f"**Query:** {result.get('query', 'N/A')}\n")
                f.write(f"**Mode:** {result.get('mode', 'N/A')}\n")
                f.write(f"**Time:** {result.get('processing_time', 0):.2f}s\n\n")
                for r in result.get("results", []):
                    f.write(f"- {r.get('title', 'No title')}\n")
                    if r.get("url"):
                        f.write(f"  {r['url']}\n")


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv(config.ENV_PATHS[0], override=True)
    load_dotenv(config.ENV_PATHS[1], override=True)
except ImportError:
    pass


def args_to_config(args: argparse.Namespace) -> ResearchConfig:
    """Convert argparse args to ResearchConfig.

    Args:
        args: The parsed argparse namespace.

    Returns:
        A ResearchConfig instance with values from args.
    """
    # Map CLI flags to ResearchConfig
    config_kwargs = {
        # Provider selection
        "default_providers": [args.mode]
        if args.mode and args.mode not in ("auto", "web", "quick")
        else ["tavily"],
        # Check if using default websearch/webfetch (external providers)
        "using_default_providers": args.mode in ("auto", "web", "quick") or not args.mode,
        # HyDE settings
        "hyde_enabled": not getattr(args, "no_hyde", False),
        "hyde_mode": getattr(args, "hyde_mode", "confidence"),
        # URL fetching
        "fetch_urls_enabled": getattr(args, "fetch_urls", True),
        "max_urls_to_fetch": getattr(args, "max_urls", getattr(args, "max_cap", 5)),
    }

    return ResearchConfig(**config_kwargs)


def create_research_engine(args: argparse.Namespace | None = None) -> Any:
    """Create a ResearchEngine from CLI args.

    Args:
        args: The parsed argparse namespace. If None, uses default config.

    Returns:
        A ResearchEngine instance configured from args.
    """
    if args is None:
        # Return a simple engine - not importing full ResearchEngine to avoid ML dependencies
        return None

    config = args_to_config(args)
    # Don't instantiate full ResearchEngine to avoid ML dependencies
    return config


class SaturationDetector:
    """Detects when research results have reached semantic saturation.

    Stops fetching when new results no longer add meaningful information.
    """

    def __init__(self, query: str, min_results: int = 5, saturation_threshold: float = 0.15):
        """Initialize saturation detector.

        Args:
            query: The research query to measure relevance against
            min_results: Minimum results before checking saturation (default: 5)
            saturation_threshold: Stop when avg novelty of last N results < this (default: 0.15)
        """
        self.query = query
        self.min_results = min_results
        self.saturation_threshold = saturation_threshold
        self.seen_texts = []
        self.relevance_scores = []

    def add_result(self, title: str, content: str) -> dict:
        """Add a result and check if we've reached saturation.

        Returns:
            Dict with 'should_stop' (bool) and 'novelty_score' (float).
        """
        text = f"{title}. {content}"
        novelty = 1.0  # Default: completely novel

        # Simple novelty calculation (without ML semantic synthesis)
        if self.seen_texts:
            # Use basic text similarity
            words = set(text.lower().split())
            for seen_text in self.seen_texts:
                seen_words = set(seen_text.lower().split())
                if words and seen_words:
                    intersection = words & seen_words
                    union = words | seen_words
                    similarity = len(intersection) / len(union) if union else 0
                    novelty = min(novelty, 1.0 - similarity)

        self.seen_texts.append(text)
        self.relevance_scores.append(novelty)

        # Check if we should stop
        should_stop = False
        if len(self.relevance_scores) >= self.min_results:
            window_size = max(1, min(5, len(self.relevance_scores) // 2))
            recent_novelty = sum(self.relevance_scores[-window_size:]) / window_size
            should_stop = recent_novelty < self.saturation_threshold

        return {
            "should_stop": should_stop,
            "novelty_score": novelty,
            "avg_recent_novelty": sum(self.relevance_scores[-min(5, len(self.relevance_scores)) :])
            / min(5, len(self.relevance_scores))
            if self.relevance_scores
            else 1.0,
        }

    def get_status(self) -> dict:
        """Get current saturation status."""
        if not self.relevance_scores:
            return {"status": "initializing", "results_count": 0}

        recent_novelty = sum(self.relevance_scores[-min(5, len(self.relevance_scores)) :]) / min(
            5, len(self.relevance_scores)
        )

        if len(self.relevance_scores) < self.min_results:
            status = "gathering"
        elif recent_novelty >= self.saturation_threshold:
            status = "gathering"
        else:
            status = "saturated"

        return {
            "status": status,
            "results_count": len(self.relevance_scores),
            "avg_recent_novelty": recent_novelty,
            "threshold": self.saturation_threshold,
        }


def _extract_mcp_search_results(content_text: str, source: str, max_results: int) -> list[dict]:
    """Normalize an MCP web_search tool response into result dicts.

    Handles JSON that may be single- OR double-encoded: z.ai returns a JSON
    string whose value is itself a JSON array. z.ai items carry ``link`` +
    ``content``; MiniMax items carry ``link`` + ``snippet``.
    """
    data: Any = None
    try:
        data = json.loads(content_text)
        while isinstance(data, str):
            data = json.loads(data)
    except (ValueError, TypeError):
        data = None
    # z.ai returns a bare list; MiniMax wraps results under e.g. "organic".
    items: list = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for k in ("organic", "organic_results", "results", "web_results", "data"):
            v = data.get(k)
            if isinstance(v, list):
                items = v
                break
        if not items:
            for v in data.values():
                if isinstance(v, list) and v and isinstance(v[0], dict) and any(
                    f in v[0] for f in ("link", "url", "href")
                ):
                    items = v
                    break
    results: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        url = item.get("link") or item.get("url") or item.get("href") or ""
        body = item.get("content") or item.get("snippet") or item.get("summary") or ""
        if not url and not body:
            continue
        results.append(
            {
                "title": item.get("title") or url or "Untitled",
                "url": url,
                "content": body,
                "source": source,
            }
        )
        if len(results) >= max_results:
            break
    return results


class CoreResearchCommand:
    """Core search research command with search providers only."""

    def __init__(self, fast_mode: bool = False) -> None:
        """Initialize the core research command.

        Args:
            fast_mode: If True, disable heavy features for quick research.
        """
        self._fast_mode = fast_mode
        self._failed_providers: dict[str, float] = {}

        # Time-to-live for failed provider entries (5 minutes)
        self._FAILURE_TTL: int = 300

        self.supported_modes = [
            "auto",
            "web",
            "quick",
            "tavily",
            "exa",
            "glm",
            "zai",  # z.ai web_search_prime MCP (remote HTTP, Coding Plan)
            "minimax",  # MiniMax Coding Plan MCP (local stdio)
            "serpapi",
            "webreader",  # Direct URL fetching via webReader adapter
            "fetch",  # Alias for webreader
            "github",  # GitHub repository search
            "claude",  # Claude Code WebSearch - built-in web search
            "webreader_mcp",  # Enhanced WebReader with MCP support
            "notebooklm",  # NotebookLM MCP - long-form research synthesis
        ]

    @staticmethod
    def _error_result(
        provider_name: str, error_message: str, processing_time: float = 0.0
    ) -> dict[str, Any]:
        """Return a standardized error result dict."""
        return {
            "success": False,
            "error": error_message,
            "results": [],
            "sources_used": [provider_name],
            "processing_time": processing_time,
        }

    @staticmethod
    def _success_result(
        provider_name: str,
        results: list[dict[str, Any]],
        processing_time: float = 0.0,
        synthesis: str | None = None,
        **extra_fields,
    ) -> dict[str, Any]:
        """Return a standardized success result dict."""
        result = {
            "success": True,
            "results": results,
            "sources_used": [provider_name],
            "processing_time": processing_time,
        }
        if synthesis:
            result["synthesis"] = synthesis
        result.update(extra_fields)
        return result

    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for the CLI."""
        parser = argparse.ArgumentParser(
            prog="search-research",
            description="Core Search Research - Multi-source search providers",
        )

        parser.add_argument("query", nargs="?", help="Research query")

        parser.add_argument("--mode", choices=self.supported_modes, default="auto")

        parser.add_argument(
            "--depth",
            choices=["quick", "detailed", "comprehensive"],
            default="comprehensive",
        )

        parser.add_argument("--output", choices=["text", "json", "markdown"], default="text")

        # Saturation controls
        parser.add_argument(
            "--saturation-threshold",
            type=float,
            default=0.15,
            help="Stop when avg novelty drops below this threshold (default: 0.15).",
        )

        parser.add_argument(
            "--min-results",
            type=int,
            default=5,
            help="Minimum results before checking saturation (default: 5).",
        )

        # Safety cap
        parser.add_argument(
            "--max-cap", type=int, default=200, help="Maximum results as safety cap (default: 200)."
        )

        parser.add_argument(
            "--max-results", type=int, default=None, help="[DEPRECATED] Use --max-cap instead."
        )

        parser.add_argument(
            "--json",
            action="store_true",
            help="Output results in JSON format (shorthand for --output json)",
        )

        parser.add_argument(
            "--save",
            type=str,
            metavar="FILE",
            help="Save results to file (format based on extension: .json or .md)",
        )

        parser.add_argument("--timeout", type=int, default=180, help="API timeout in seconds")

        parser.add_argument(
            "--vision",
            action="store_true",
            help="Enable AI vision analysis for images found in web pages",
        )

        # HyDE flags
        parser.add_argument(
            "--hyde",
            action="store_true",
            help="Enable HyDE (Hypothetical Document Embeddings) for improved search relevance",
        )

        parser.add_argument(
            "--no-hyde", action="store_true", help="Disable HyDE even when API key is available"
        )

        parser.add_argument(
            "--hyde-retrieval",
            action="store_true",
            help="Use HyDE-based retrieval where hypothetical document content is used as the search query",
        )

        # Multi-HyDE flags
        parser.add_argument(
            "--multi-hyde",
            action="store_true",
            help="Enable Multi-HyDE with multiple perspective documents",
        )

        parser.add_argument(
            "--hyde-perspectives",
            type=str,
            metavar="PERSPECTIVES",
            help="Comma-separated list of perspectives for Multi-HyDE",
        )

        # Streaming flag
        parser.add_argument(
            "--stream",
            action="store_true",
            help="Stream results as they arrive from backends instead of waiting for all backends to complete",
        )

        return parser

    async def execute_research(self, query: str, mode: str = "auto", **kwargs) -> dict[str, Any]:
        """Execute research using the specified mode.

        Args:
            query: The research query.
            mode: The search mode/provider to use.
            **kwargs: Additional research parameters.

        Returns:
            Dictionary with research results.
        """
        result = {
            "query": query,
            "mode": mode,
            "success": False,
            "results": [],
            "sources_used": [],
            "hyde_enabled": False,
        }

        start_time = time.time()

        # Handle deprecated --max-results
        if kwargs.get("max_results") and not kwargs.get("max_cap"):
            kwargs["max_cap"] = kwargs.pop("max_results")

        # Handle HyDE
        hyde_enabled = kwargs.get("hyde", False)
        multi_hyde_enabled = kwargs.get("multi_hyde", False)
        no_hyde = kwargs.get("no_hyde", False)
        use_hyde = hyde_enabled or (
            not no_hyde
            and (os.getenv("ZHIPU_API_KEY") or os.getenv("GLM_API_KEY") or os.getenv("ZAI_API_KEY"))
        )

        # Handle Multi-HyDE
        if multi_hyde_enabled:
            try:
                from core import (
                    MultiHyDEConfigComprehensive,
                )
                from core import (
                    generate_multi_hypothetical_documents_comprehensive as generate_multi_hypothetical_documents,
                )

                hyde_perspectives = kwargs.get("hyde_perspectives", None)
                config = (
                    MultiHyDEConfigComprehensive(perspectives=hyde_perspectives)
                    if hyde_perspectives
                    else None
                )

                hyde_start = time.time()
                multi_hyp_docs = generate_multi_hypothetical_documents(query, config)

                result["multi_hypothetical_documents"] = {
                    "query": multi_hyp_docs.query,
                    "perspectives": multi_hyp_docs.perspectives,
                    "total_word_count": multi_hyp_docs.total_word_count,
                    "documents": [
                        {
                            "perspective": doc.perspective,
                            "content": doc.content,
                            "word_count": doc.word_count,
                        }
                        for doc in multi_hyp_docs.documents
                    ],
                }

                result["multi_hyde_enabled"] = True
                result["hyde_enabled"] = True
                result["hyde_processing_time"] = time.time() - hyde_start

            except Exception as e:
                print(f"Multi-HyDE error: {e}", file=sys.stderr)
                pass  # Multi-HyDE is optional

        # Handle HyDE-based retrieval
        hyde_retrieval_enabled = kwargs.get("hyde_retrieval", False)
        if hyde_retrieval_enabled:
            try:
                from core import (
                    HyDERetrievalConfig,
                    search_with_hyde,
                )

                hyde_retrieval_start = time.time()
                hyde_config = HyDERetrievalConfig(
                    model=kwargs.get("hyde_model", "glm"),
                    use_full_document=kwargs.get("hyde_use_full_document", True),
                    max_retrieval_query_length=kwargs.get("hyde_max_query_length", 500),
                )
                hyde_result = search_with_hyde(query, hyde_config)

                result["results"] = hyde_result.results
                result["hypothetical_document"] = hyde_result.hypothetical_document
                result["hyde_enabled"] = True
                result["hyde_retrieval_enabled"] = True
                result["hyde_processing_time"] = time.time() - hyde_retrieval_start

            except Exception as e:
                print(f"HyDE retrieval error: {e}", file=sys.stderr)
                pass  # HyDE retrieval is optional

        elif use_hyde:
            try:
                from core import create_hypothetical_document

                pre_generated_content = kwargs.get("hyde_content")
                if pre_generated_content:
                    hyp_doc = create_hypothetical_document(query, pre_generated_content)
                    result["hypothetical_document"] = {
                        "content": hyp_doc.content,
                        "word_count": hyp_doc.word_count,
                        "query": hyp_doc.query,
                        "generation_model": hyp_doc.generation_model,
                        "generation_time": hyp_doc.generation_time,
                    }
                    result["hyde_enabled"] = True
                    result["hyde_source"] = "claude-code-orchestrator"
                else:
                    result["hyde_enabled"] = False
                    result["hyde_skipped_reason"] = "no_pre_generated_content"

            except Exception as e:
                print(f"HyDE error: {e}", file=sys.stderr)
                pass  # HyDE is optional

        # Route to appropriate provider
        try:
            if mode == "auto":
                # Auto mode: select best provider based on query
                selected_mode = self._select_mode_for_query(query)
                research_result = await self._execute_mode(selected_mode, query, **kwargs)
            elif mode == "web":
                # Web mode: try multiple web search providers
                research_result = await self._web_search(query, **kwargs)
            elif mode == "quick":
                # Quick mode: single provider, minimal results
                research_result = await self._quick_search(query, **kwargs)
            else:
                # Direct mode selection
                research_result = await self._execute_mode(mode, query, **kwargs)

            query_variants = result.get("query_variants")
            result.update(research_result)
            result["success"] = True
            if query_variants:
                result["query_variants"] = query_variants

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Research failed: {e}")
            raise

        result["processing_time"] = time.time() - start_time
        return result

    def _select_mode_for_query(self, query: str) -> str:
        """Select the best search mode based on query analysis.

        Args:
            query: The research query.

        Returns:
            The selected mode name.
        """
        query_lower = query.lower()

        # Check for code/programming keywords - use zai or glm
        code_keywords = ["code", "function", "api", "programming", "python", "javascript", "debug"]
        if any(keyword in query_lower for keyword in code_keywords):
            return "zai"

        # Check for recent/current info - use tavily
        recent_keywords = ["latest", "recent", "current", "2024", "2025", "news", "today"]
        if any(keyword in query_lower for keyword in recent_keywords):
            return "tavily"

        # Check for how-to/tutorial - use tavily
        howto_keywords = ["how to", "tutorial", "guide", "step by step", "explain"]
        if any(keyword in query_lower for keyword in howto_keywords):
            return "tavily"

        # Default to zai for general queries
        return "zai"

    async def _execute_mode(self, mode: str, query: str, **kwargs) -> dict[str, Any]:
        """Execute research with the specified mode.

        Args:
            mode: The mode/provider to use.
            query: The research query.
            **kwargs: Additional parameters.

        Returns:
            Research results dictionary.
        """
        if mode == "tavily":
            return await self._tavily_search(
                query, max_results=kwargs.get("max_results", 10), timeout=kwargs.get("timeout", 30)
            )
        elif mode == "exa":
            return await self._exa_search(
                query, kwargs.get("max_results", 10), kwargs.get("timeout", 30)
            )
        elif mode == "glm":
            return await self._glm_search(
                query, kwargs.get("max_results", 10), kwargs.get("timeout", 180)
            )
        elif mode == "zai":
            return await self._zai_mcp_search(query, kwargs)
        elif mode == "minimax":
            return await self._minimax_search(query, kwargs)
        elif mode == "serpapi":
            return await self._serpapi_search(
                query, kwargs.get("max_results", 10), kwargs.get("timeout", 30)
            )
        elif mode in ["webreader", "fetch"]:
            return await self._webreader_search(
                query,
                kwargs.get("max_results", 10),
                kwargs.get("timeout", 30),
                kwargs.get("vision", False),
            )
        elif mode == "github":
            return await self._github_search(
                query, kwargs.get("max_cap", kwargs.get("max_results", 10))
            )
        elif mode == "notebooklm":
            return await self._notebooklm_search(query, kwargs.get("max_results", 5), kwargs)
        elif mode == "claude":
            return await self._claude_search(query, kwargs.get("max_results", 10))
        elif mode == "webreader_mcp":
            return await self._webreader_mcp_search(query, kwargs.get("max_results", 10), kwargs)
        else:
            # Default fallback: z.ai MCP (grounded). glm chat is opt-in via --mode glm.
            return await self._zai_mcp_search(query, kwargs)

    async def _web_search(self, query: str, **kwargs) -> dict[str, Any]:
        """Web search mode: try multiple web search providers in parallel.

        Args:
            query: The research query.
            **kwargs: Additional parameters.

        Returns:
            Combined results from multiple providers.
        """
        # Try tavily in parallel with exa
        tasks = []

        if os.getenv("TAVILY_API_KEY"):
            tasks.append(
                self._tavily_search(
                    query,
                    max_results=kwargs.get("max_results", 10),
                    timeout=kwargs.get("timeout", 30),
                )
            )

        if os.getenv("EXA_API_KEY"):
            tasks.append(
                self._exa_search(query, kwargs.get("max_results", 10), kwargs.get("timeout", 30))
            )

        if not tasks:
            # No Tavily/Exa keys: fall back to z.ai MCP (grounded), not glm chat.
            return await self._zai_mcp_search(query, kwargs)

        # Execute in parallel and combine results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        combined_results = []
        sources_used = []

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Web search provider failed: {result}")
                continue

            if isinstance(result, dict) and result.get("results"):
                combined_results.extend(result["results"])
                sources_used.extend(result.get("sources_used", []))

        return {
            "results": combined_results,
            "sources_used": sources_used,
            "success": len(combined_results) > 0,
        }

    async def _quick_search(self, query: str, **kwargs) -> dict[str, Any]:
        """Quick search mode: single provider, minimal results.

        Args:
            query: The research query.
            **kwargs: Additional parameters.

        Returns:
            Research results.
        """
        # z.ai MCP for quick searches (glm chat returned ungrounded prose).
        return await self._zai_mcp_search(query, kwargs)

    # Provider methods

    async def _tavily_search(self, query: str, *args, **kwargs) -> dict[str, Any]:
        """Search using Tavily API."""
        start_time = time.perf_counter()
        max_results = kwargs.get("max_results", 10)
        timeout = kwargs.get("timeout", 30)

        if args and len(args) >= 1:
            try:
                max_results = args[0]
                if len(args) >= 2:
                    timeout = args[1]
            except (IndexError, TypeError):
                pass

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            duration_ms = (time.perf_counter() - start_time) * 1000
            result = {
                "results": [],
                "sources_used": [],
                "error": "TAVILY_API_KEY not set. Get one at https://tavily.com/",
            }
            return _create_timing_result(result, "tavily", duration_ms)

        try:
            import requests

            url = "https://api.tavily.com/search"
            payload = {
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "include_raw_content": False,
                "max_results": max_results,
            }

            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                result = {
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "url": item.get("url", ""),
                    "source": "tavily",
                }
                if "published_date" in item:
                    result["published_date"] = item["published_date"]
                results.append(result)

            duration_ms = (time.perf_counter() - start_time) * 1000
            result = {
                "results": results,
                "sources_used": ["tavily"],
                "synthesis": data.get("answer", ""),
                "answer": data.get("answer"),
            }
            return _create_timing_result(result, "tavily", duration_ms)

        except Exception:
            raise

    async def _exa_search(self, query: str, max_results: int, timeout: int) -> dict[str, Any]:
        """Search using Exa API."""
        start_time = time.perf_counter()
        api_key = os.getenv("EXA_API_KEY")

        if not api_key:
            duration_ms = (time.perf_counter() - start_time) * 1000
            result = self._error_result("exa", "EXA_API_KEY not set. Get one at https://exa.ai/")
            return _create_timing_result(result, "exa", duration_ms)

        try:
            import requests

            url = "https://api.exa.ai/search"
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
            }
            payload = {"query": query, "numResults": max_results, "contents": {"text": True}}

            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append(
                    {
                        "title": item.get("title", ""),
                        "content": item.get("text", ""),
                        "url": item.get("url", ""),
                        "source": "exa",
                    }
                )

            duration_ms = (time.perf_counter() - start_time) * 1000
            result = {
                "results": results,
                "sources_used": ["exa"],
            }
            return _create_timing_result(result, "exa", duration_ms)

        except Exception:
            raise

    async def _glm_search(
        self,
        query: str,
        max_results: int,
        timeout: int,
        enable_web_search: bool = False,
        extract_urls: bool = False,
    ) -> dict[str, Any]:
        """Search using GLM/Zhipu AI API."""
        start_time = time.perf_counter()
        api_key = os.getenv("ZHIPU_API_KEY") or os.getenv("GLM_API_KEY") or os.getenv("ZAI_API_KEY")

        if not api_key:
            duration_ms = (time.perf_counter() - start_time) * 1000
            result = {
                "results": [],
                "sources_used": ["glm"],
                "error": "GLM_API_KEY or ZAI_API_KEY not set. Get one at https://z.ai/",
            }
            return _create_timing_result(result, "glm", duration_ms)

        try:
            import re

            import httpx
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://api.z.ai/api/coding/paas/v4/",
                timeout=httpx.Timeout(timeout, connect=10.0),
                max_retries=0,
            )

            create_params = {
                "model": "GLM-4.5-Air",
                "messages": [{"role": "user", "content": query}],
                "max_tokens": 4000,
                "temperature": 0.2,
            }

            if enable_web_search:
                create_params["tools"] = [
                    {
                        "type": "web_search",
                        "web_search": {
                            "search_query": query,
                            "search_result": True,
                        },
                    }
                ]

            response = await client.chat.completions.create(**create_params)
            content_val = response.choices[0].message.content if response.choices else ""

            results = [
                {
                    "title": "GLM AI Answer",
                    "content": content_val,
                    "url": "",
                    "source": "glm",
                    "priority": 1,
                }
            ]

            # Extract URLs if enabled
            if extract_urls:
                urls = re.findall(r"https?://[^\s\)]+", content_val)
                for url in urls:
                    results.append(
                        {
                            "title": "Referenced URL",
                            "content": "",
                            "url": url,
                            "source": "glm",
                        }
                    )

            duration_ms = (time.perf_counter() - start_time) * 1000
            result = {
                "results": results,
                "sources_used": ["glm"],
                "synthesis": content_val,
            }
            return _create_timing_result(result, "glm", duration_ms)

        except Exception:
            raise

    async def _zai_mcp_search(self, query: str, kwargs: dict) -> dict[str, Any]:
        """Search via the z.ai web_search_prime MCP server (remote HTTP)."""
        start_time = time.perf_counter()
        api_key = os.getenv("ZAI_API_KEY") or os.getenv("ZHIPU_API_KEY") or os.getenv("GLM_API_KEY")
        if not api_key:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return _create_timing_result(
                {"results": [], "sources_used": ["zai"],
                 "error": "ZAI_API_KEY not set (z.ai Coding Plan required)."},
                "zai", duration_ms,
            )
        max_results = kwargs.get("max_results", 10)
        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamablehttp_client
        except ImportError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return _create_timing_result(
                {"results": [], "sources_used": ["zai"], "error": f"mcp SDK not installed: {e}"},
                "zai", duration_ms,
            )
        try:
            url = "https://api.z.ai/api/mcp/web_search_prime/mcp"
            headers = {"Authorization": f"Bearer {api_key}"}
            async with streamablehttp_client(url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    res = await session.call_tool(
                        "web_search_prime",
                        {"search_query": query, "content_size": "high"},
                    )
            txt = getattr(res.content[0], "text", "") if res.content else ""
            results = _extract_mcp_search_results(txt, "zai", max_results)
            duration_ms = (time.perf_counter() - start_time) * 1000
            return _create_timing_result(
                {"results": results, "sources_used": ["zai"],
                 "synthesis": f"{len(results)} grounded results from z.ai web_search_prime"},
                "zai", duration_ms,
            )
        except Exception:
            raise

    async def _minimax_search(self, query: str, kwargs: dict) -> dict[str, Any]:
        """Search via the MiniMax CLI (``mmx search query``) — official Token-Plan path.

        Replaces the ``uvx minimax-coding-plan-mcp`` stdio bridge: mmx is MiniMax's
        own CLI, already installed, reads ``MINIMAX_API_KEY`` from env, and emits the
        same ``{organic:[...]}`` JSON the normalizer already handles.
        """
        start_time = time.perf_counter()
        api_key = os.getenv("MINIMAX_API_KEY")
        if not api_key:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return _create_timing_result(
                {"results": [], "sources_used": ["minimax"],
                 "error": "MINIMAX_API_KEY not set."},
                "minimax", duration_ms,
            )
        max_results = kwargs.get("max_results", 10)
        host = os.getenv("MINIMAX_API_HOST", "https://api.minimax.io")
        region = "cn" if "minimaxi.com" in host else "global"
        try:
            env = {**os.environ, "MINIMAX_API_KEY": api_key}
            # Invoke node + mmx's .mjs entry directly. `node <file.mjs>` passes argv
            # verbatim via CreateProcess (no shell), so query metachars (& | < > %) are
            # NOT re-parsed — the `cmd /c mmx.cmd` form let cmd.exe split/inject them.
            # Also sidesteps WinError 2 (CreateProcess can't exec .cmd directly).
            if os.name == "nt":
                mmx_mjs = os.path.join(
                    os.environ.get("APPDATA", ""), "npm",
                    "node_modules", "mmx-cli", "dist", "mmx.mjs")
                mmx_bin = ["node", mmx_mjs] if os.path.isfile(mmx_mjs) else ["mmx"]
            else:
                mmx_bin = ["mmx"]
            proc = await asyncio.create_subprocess_exec(
                *mmx_bin, "search", "query", query,
                "--region", region, "--output", "json",
                "--non-interactive", "--no-color", "--quiet",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await proc.communicate()
            txt = stdout.decode("utf-8", errors="replace") if stdout else ""
            if proc.returncode != 0:
                err = stderr.decode("utf-8", errors="replace").strip()[:300]
                duration_ms = (time.perf_counter() - start_time) * 1000
                return _create_timing_result(
                    {"results": [], "sources_used": ["minimax"],
                     "error": f"mmx exit {proc.returncode}: {err}"},
                    "minimax", duration_ms,
                )
            results = _extract_mcp_search_results(txt, "minimax", max_results)
            duration_ms = (time.perf_counter() - start_time) * 1000
            return _create_timing_result(
                {"results": results, "sources_used": ["minimax"],
                 "synthesis": f"{len(results)} grounded results from minimax (mmx)"},
                "minimax", duration_ms,
            )
        except Exception:
            raise

    async def _serpapi_search(self, query: str, max_results: int, timeout: int) -> dict[str, Any]:
        """Search using SerpAPI (Google results via serpapi.com)."""
        start_time = time.perf_counter()
        api_key = os.getenv("SERPAPI_API_KEY")

        if not api_key:
            duration_ms = (time.perf_counter() - start_time) * 1000
            result = self._error_result(
                "serpapi", "SERPAPI_API_KEY not set. Get one at https://serpapi.com/"
            )
            return _create_timing_result(result, "serpapi", duration_ms)

        try:
            import serpapi

            client = serpapi.Client(api_key=api_key)
            result = client.search({"q": query, "engine": "google"})

            results = []
            for item in result.get("organic_results", [])[:max_results]:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "content": item.get("snippet", ""),
                        "url": item.get("link", ""),
                        "source": "serpapi",
                    }
                )

            duration_ms = (time.perf_counter() - start_time) * 1000
            search_result = {
                "results": results,
                "sources_used": ["serpapi"],
            }
            return _create_timing_result(search_result, "serpapi", duration_ms)

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_result = self._error_result("serpapi", str(e))
            return _create_timing_result(error_result, "serpapi", duration_ms)

    async def _webreader_search(
        self, query: str, max_results: int, timeout: int, vision: bool = False
    ) -> dict[str, Any]:
        """Direct URL fetching via webReader adapter."""
        start_time = time.perf_counter()

        try:
            # Check if query is a URL
            if not query.startswith(("http://", "https://")):
                # Not a URL - treat as error for webreader mode
                duration_ms = (time.perf_counter() - start_time) * 1000
                result = self._error_result("webreader", "Query must be a URL for webreader mode")
                return _create_timing_result(result, "webreader", duration_ms)

            # Use web-reader MCP or webReader adapter
            try:
                # Try MCP first
                from mcp__web_reader__webReader import webReader

                content = webReader(query, return_format="markdown")
                results = [
                    {
                        "title": "WebReader Result",
                        "content": content,
                        "url": query,
                        "source": "webreader",
                    }
                ]
            except ImportError:
                # Fallback to direct requests
                import requests

                response = requests.get(query, timeout=timeout)
                response.raise_for_status()

                # Simple text extraction
                from html.parser import HTMLParser

                class TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []

                    def handle_data(self, data):
                        self.text.append(data)

                    def get_text(self):
                        return " ".join(self.text)

                parser = TextExtractor()
                parser.feed(response.text)
                content = parser.get_text()

                results = [
                    {
                        "title": "WebReader Result",
                        "content": content[:5000],  # Limit content
                        "url": query,
                        "source": "webreader",
                    }
                ]

            duration_ms = (time.perf_counter() - start_time) * 1000
            result = {
                "results": results,
                "sources_used": ["webreader"],
            }
            return _create_timing_result(result, "webreader", duration_ms)

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_result = self._error_result("webreader", str(e))
            return _create_timing_result(error_result, "webreader", duration_ms)

    def _is_code_search_query(self, query: str) -> bool:
        """Detect if a query should use code search instead of repository search.

        Code search patterns:
        - Code keywords: function, class, def, import, async, await, const, let, var
        - File extensions: .py, .js, .ts, .java, .go, .rs, .rb, .php, .cpp, .c, .h
        - Language specifiers: language:python, language:javascript, etc.

        Returns True if code search should be used, False for repository search.
        """
        if not query or not query.strip():
            return False

        query_lower = query.lower()

        # Repository search indicators that override code keywords
        repo_indicators = [
            "framework",
            "library",
            "package",
            "tool",
            "tutorial",
            "guide",
            "comparison",
            "vs",
            "versus",
        ]

        # Code keywords that indicate searching for code
        code_keywords = [
            "function",
            "class",
            "def ",
            "import",
            "from import",
            "async def",
            "await",
            "const ",
            "let ",
            "var ",
            "interface",
            "type ",
            "enum",
            "struct",
            "component",
            "hook",
            "lambda",
            "decorator",
        ]

        # Check for code keywords with repo indicator override
        for keyword in code_keywords:
            if keyword in query_lower:
                # Check if repo indicators are also present
                if any(indicator in query_lower for indicator in repo_indicators):
                    return False  # Repo search wins
                return True

        # File extensions that indicate code search
        file_extensions = [
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".go",
            ".rs",
            ".rb",
            ".php",
            ".cpp",
            ".c",
            ".h",
            ".cs",
            ".swift",
            ".kt",
            ".scala",
            ".dart",
            ".lua",
            ".r",
            ".sh",
            ".bash",
            ".zsh",
            ".yaml",
            ".yml",
            ".json",
            ".xml",
            ".html",
            ".css",
            ".scss",
            "dockerfile",
            "makefile",
        ]

        for ext in file_extensions:
            if ext in query_lower:
                return True

        # Language specifiers (GitHub search syntax)
        if "language:" in query_lower:
            return True

        # Default to repository search for ambiguous queries
        return False

    async def _github_search(self, query: str, max_results: int = 10) -> dict[str, Any]:
        """Search GitHub with intelligent routing between code and repository search.

        Includes rate limit tracking with automatic fallback to repo search.
        """
        from github import Github
        from github.Auth import Token

        start_time = time.perf_counter()

        try:
            token = os.getenv("GITHUB_TOKEN")
            client = Github(auth=Token(token)) if token else Github()

            # Use pattern detection to route to code or repo search
            is_code_search = self._is_code_search_query(query)

            if is_code_search:
                try:
                    # Code search: find specific code patterns
                    code_results = client.search_code(query, top_repositories=max_results)
                    results = []
                    for item in code_results[:max_results]:
                        results.append(
                            {
                                "title": f"{item.repository.full_name} - {item.path}",
                                "content": item.text_matches[0].fragment if hasattr(item, "text_matches") and item.text_matches else "",
                                "url": item.html_url,
                                "source": "github_code",
                            }
                        )

                    duration_ms = (time.perf_counter() - start_time) * 1000
                    result = {
                        "results": results,
                        "sources_used": ["github_code"],
                    }
                    return _create_timing_result(result, "github", duration_ms)

                except Exception as code_error:
                    # Check if this is a rate limit error
                    error_str = str(code_error).lower()
                    is_rate_limit = any(
                        term in error_str
                        for term in [
                            "rate limit",
                            "403",
                            "api rate limit exceeded",
                            "secondary rate limit",
                            "abuse-rate",
                        ]
                    )

                    if is_rate_limit:
                        # Fall back to repo search with warning
                        logging.warning(
                            f"GitHub code search rate limited for query '{query}'. "
                            f"Falling back to repo search. Error: {code_error}"
                        )

                        # Attempt repo search as fallback
                        repos = client.search_repositories(query)[:max_results]
                        results = []
                        for repo in repos:
                            results.append(
                                {
                                    "title": repo.full_name,
                                    "content": repo.description or "",
                                    "url": repo.html_url,
                                    "source": "github",
                                }
                            )

                        duration_ms = (time.perf_counter() - start_time) * 1000
                        result = {
                            "results": results,
                            "sources_used": ["github"],
                            "warning": "Code search rate limited - showing repositories instead",
                        }
                        return _create_timing_result(result, "github", duration_ms)
                    else:
                        # Re-raise non-rate-limit errors
                        raise code_error

            else:
                # Repository search: find repositories
                repos = client.search_repositories(query)[:max_results]
                results = []
                for repo in repos:
                    results.append(
                        {
                            "title": repo.full_name,
                            "content": repo.description or "",
                            "url": repo.html_url,
                            "source": "github",
                        }
                    )

                duration_ms = (time.perf_counter() - start_time) * 1000
                result = {
                    "results": results,
                    "sources_used": ["github"],
                }
                return _create_timing_result(result, "github", duration_ms)

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_result = self._error_result("github", str(e))
            return _create_timing_result(error_result, "github", duration_ms)

    async def _notebooklm_search(
        self, query: str, max_results: int, kwargs: dict
    ) -> dict[str, Any]:
        """Search using NotebookLM MCP."""
        start_time = time.perf_counter()

        try:
            from mcp__notebooklm_mcp__notebook_query import notebook_query

            # Get first notebook or use specified one
            notebook_id = kwargs.get("notebook_id")
            if not notebook_id:
                from mcp__notebooklm_mcp__notebook_list import notebook_list

                notebooks = notebook_list()
                if notebooks.get("notebooks"):
                    notebook_id = notebooks["notebooks"][0]["id"]
                else:
                    raise Exception("No NotebookLM notebooks found")

            result = notebook_query(
                notebook_id=notebook_id,
                query=query,
            )

            results = [
                {
                    "title": "NotebookLM Result",
                    "content": result,
                    "url": "",
                    "source": "notebooklm",
                }
            ]

            duration_ms = (time.perf_counter() - start_time) * 1000
            return _create_timing_result(
                {
                    "results": results,
                    "sources_used": ["notebooklm"],
                },
                "notebooklm",
                duration_ms,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_result = self._error_result("notebooklm", str(e))
            return _create_timing_result(error_result, "notebooklm", duration_ms)

    async def _claude_search(self, query: str, max_results: int = 10) -> dict[str, Any]:
        """Search using Claude Code's built-in web search."""
        start_time = time.perf_counter()

        try:
            from mcp__web_search_prime__web_search_prime import web_search_prime

            search_result = web_search_prime(search_query=query, content_size="high")

            results = []
            for item in search_result.get("webResults", []):
                results.append(
                    {
                        "title": item.get("title", ""),
                        "content": item.get("pageSummary", ""),
                        "url": item.get("url", ""),
                        "source": "claude-web-search",
                    }
                )

            duration_ms = (time.perf_counter() - start_time) * 1000
            return _create_timing_result(
                {
                    "results": results,
                    "sources_used": ["claude-web-search"],
                },
                "claude",
                duration_ms,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_result = self._error_result("claude-web-search", str(e))
            return _create_timing_result(error_result, "claude", duration_ms)

    async def _webreader_mcp_search(
        self, query: str, max_results: int, kwargs: dict
    ) -> dict[str, Any]:
        """Enhanced WebReader with MCP support."""
        # This is similar to _webreader_search but with more MCP features
        return await self._webreader_search(
            query, max_results, kwargs.get("timeout", 30), kwargs.get("vision", False)
        )


async def _main_async() -> int:
    """Async entry point."""
    import argparse

    # Quick parse to get --fast flag
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--fast", action="store_true")
    pre_args, _ = pre_parser.parse_known_args()

    cmd = CoreResearchCommand(fast_mode=pre_args.fast)
    parser = cmd.create_parser()
    args = parser.parse_args()

    # Handle --json shorthand
    if args.json:
        args.output = "json"

    # Handle diagnose mode
    if hasattr(args, "diagnose") and args.diagnose:
        print("Provider Status:")
        print(f"  Tavily: {'✓' if os.getenv('TAVILY_API_KEY') else '✗'}")
        print(f"  Serper: {'✓' if os.getenv('SERPER_API_KEY') else '✗'}")
        print(f"  Exa: {'✓' if os.getenv('EXA_API_KEY') else '✗'}")
        print(
            f"  GLM/ZAI: {'✓' if os.getenv('ZHIPU_API_KEY') or os.getenv('GLM_API_KEY') or os.getenv('ZAI_API_KEY') else '✗'}"
        )
        return 0

    # Check for query
    if not args.query:
        parser.print_help()
        return 1

    # Convert args to kwargs
    kwargs = {
        "depth": args.depth,
        "output": args.output,
        "saturation_threshold": args.saturation_threshold,
        "min_results": args.min_results,
        "max_cap": args.max_cap,
        "max_results": args.max_results,
        "timeout": args.timeout,
        "vision": args.vision,
        "hyde": args.hyde,
        "no_hyde": args.no_hyde,
        "hyde_retrieval": args.hyde_retrieval,
        "multi_hyde": args.multi_hyde,
        "hyde_perspectives": args.hyde_perspectives,
    }

    # Handle streaming mode
    if getattr(args, "stream", False):
        try:
            from core.router_async import AsyncSearchRouter

            router = AsyncSearchRouter()

            print(f"Streaming results for: {args.query}")
            print("-" * 50)

            result_count = 0
            start_time = time.time()
            all_results = []

            async for result in router.search_async_stream(
                args.query,
                limit=args.max_cap or args.max_results or 10,
            ):
                result_count += 1
                all_results.append(result)

                # Print result as it arrives
                if args.output == "json":
                    print(json.dumps(result.__dict__, indent=2, default=str))
                else:
                    # Text format
                    print(f"\n[{result_count}] {result.title}")
                    if result.url:
                        print(f"    URL: {result.url}")
                    if result.content:
                        preview = (
                            result.content[:200] + "..."
                            if len(result.content) > 200
                            else result.content
                        )
                        print(f"    {preview}")
                    if hasattr(result, "score") and result.score:
                        print(f"    Score: {result.score:.3f}")

            elapsed = time.time() - start_time
            print("-" * 50)
            print(f"\nStreamed {result_count} results in {elapsed:.2f}s")

            # Save to file if requested
            if args.save:
                save_path = Path(args.save)
                final_result = {
                    "success": True,
                    "query": args.query,
                    "results": [r.__dict__ for r in all_results],
                    "processing_time": elapsed,
                    "streaming": True,
                }
                if save_path.suffix == ".json":
                    save_path.write_text(json.dumps(final_result, indent=2))
                else:
                    save_path.write_text(_format_text(final_result))
                print(f"\nResults saved to {save_path}")

            return 0

        except Exception as e:
            logger.error(f"Streaming research failed: {e}")
            return 1

    # Execute research (non-streaming)
    try:
        result = await cmd.execute_research(args.query, args.mode, **kwargs)

        # Output results
        if args.output == "json":
            print(json.dumps(result, indent=2))
        elif args.output == "markdown":
            print(_format_markdown(result))
        else:
            print(_format_text(result))

        # Save to file if requested
        if args.save:
            save_path = Path(args.save)
            if save_path.suffix == ".json":
                save_path.write_text(json.dumps(result, indent=2))
            elif save_path.suffix == ".md":
                save_path.write_text(_format_markdown(result))
            else:
                save_path.write_text(_format_text(result))
            print(f"\nResults saved to {save_path}")

        return 0 if result.get("success") else 1

    except Exception as e:
        logger.error(f"Research failed: {e}")
        return 1


def _main_sync() -> int:
    """Synchronous entry point for pip console_scripts wrapper."""
    return asyncio.run(_main_async())


def _format_text(result: dict[str, Any]) -> str:
    """Format results as plain text."""
    lines = []
    lines.append(f"Query: {result.get('query', '')}")
    lines.append(f"Mode: {result.get('mode', '')}")
    lines.append(f"Sources: {', '.join(result.get('sources_used', []))}")
    lines.append(f"Processing time: {result.get('processing_time', 0):.2f}s")
    lines.append("")

    if result.get("hyde_enabled"):
        lines.append("HyDE: Enabled")
        if result.get("hypothetical_document"):
            hyp_doc = result["hypothetical_document"]
            lines.append(f"  Words: {hyp_doc.get('word_count', 0)}")
        lines.append("")

    if result.get("synthesis"):
        lines.append("Summary:")
        lines.append(result["synthesis"])
        lines.append("")

    lines.append("Results:")
    lines.append("")

    for i, item in enumerate(result.get("results", []), 1):
        lines.append(f"{i}. {item.get('title', 'Untitled')}")
        lines.append(f"   {item.get('content', '')[:200]}...")
        lines.append(f"   URL: {item.get('url', '')}")
        lines.append("")

    return "\n".join(lines)


def _format_markdown(result: dict[str, Any]) -> str:
    """Format results as Markdown."""
    lines = []
    lines.append(f"# Research Results: {result.get('query', '')}")
    lines.append("")
    lines.append(f"**Mode:** {result.get('mode', '')}  ")
    lines.append(f"**Sources:** {', '.join(result.get('sources_used', []))}  ")
    lines.append(f"**Time:** {result.get('processing_time', 0):.2f}s  ")
    lines.append("")

    if result.get("synthesis"):
        lines.append("## Summary")
        lines.append(result["synthesis"])
        lines.append("")

    lines.append("## Results")
    lines.append("")

    for i, item in enumerate(result.get("results", []), 1):
        lines.append(f"### {i}. {item.get('title', 'Untitled')}")
        lines.append("")
        lines.append(item.get("content", "")[:500])
        lines.append("")
        lines.append(f"**URL:** {item.get('url', '')}  ")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(_main_sync())
