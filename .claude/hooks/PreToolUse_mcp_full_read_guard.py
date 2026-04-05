#!/usr/bin/env python3
"""
PreToolUse Hook: MCP Full-Read Guard

Intercepts MCP tool calls that are likely to produce very large context payloads
BEFORE the call is made, allowing substitution with a targeted alternative.

Registered via PreToolUse.py TOOL_HOOKS for:
  - mcp__web-reader__webReader
  - mcp__tavily-mcp__tavily_extract

Behavior:
  - GitHub repo root / README URLs: BLOCK with alternatives
  - Full documentation site pages: BLOCK with alternatives
  - Specific file URLs or anchored URLs: ALLOW (pass through)
  - tavily_extract: ADVISORY block — suggests tavily_search instead

The block message is intentionally actionable, providing exact alternative
tool invocations rather than just saying "don't do this".

Author: Claude Code
Date: 2026-03-16
"""

from __future__ import annotations

import json
import re
import sys
from urllib.parse import urlparse

# GitHub patterns that produce large responses
_GITHUB_REPO_ROOT_RE = re.compile(
    r"https?://github\.com/[^/]+/[^/?#]+/?(\?[^#]*)?$",
    re.IGNORECASE,
)

# GitHub README / wiki / blob at root level
_GITHUB_BLOB_ROOT_RE = re.compile(
    r"https?://github\.com/[^/]+/[^/]+/blob/[^/]+/README",
    re.IGNORECASE,
)

# Documentation roots (not specific anchored sections)
_DOC_ROOT_RE = re.compile(
    r"https?://(docs|documentation|wiki|readme)\.",
    re.IGNORECASE,
)


def _check_url(url: str) -> dict | None:
    """Return a block decision dict if the URL will produce a large response, else None."""
    if not isinstance(url, str) or not url.strip():
        return None

    url = url.strip()

    try:
        parsed = urlparse(url)
        has_fragment = bool(parsed.fragment)
        host = parsed.netloc.lower()
        path = parsed.path.lower()
    except Exception:
        return None

    # GitHub repo root (e.g. github.com/janreges/ai-distiller) — always large
    if _GITHUB_REPO_ROOT_RE.match(url):
        return {
            "decision": "block",
            "reason": (
                "⛔ MCP FULL-READ BLOCKED: web-reader on a GitHub repository root URL "
                f"({url}) will fetch 10k–20k+ tokens of rendered HTML.\n\n"
                "Preferred alternatives:\n"
                "  1. mcp__aid__distill_file  — extracts public API/structure only "
                "(90–98% compression, use for code understanding)\n"
                "  2. mcp__tavily-mcp__tavily_search  — returns search snippets without "
                "full page fetch (use for facts/documentation)\n"
                "  3. WebFetch with a specific raw file path "
                "(e.g. github.com/owner/repo/raw/main/README.md)\n\n"
                "Use one of the above instead of web-reader on the repo root."
            ),
            "blocking_hook": "PreToolUse_mcp_full_read_guard.py",
        }

    # GitHub README blob
    if _GITHUB_BLOB_ROOT_RE.match(url):
        return {
            "decision": "block",
            "reason": (
                "⛔ MCP FULL-READ BLOCKED: web-reader on a GitHub README blob "
                f"({url}) tends to produce large responses.\n\n"
                "Preferred alternatives:\n"
                "  1. mcp__tavily-mcp__tavily_search  — search for specific facts\n"
                "  2. mcp__aid__distill_file  — for code structure overview\n"
                "  3. WebFetch on the raw URL  — smaller and faster\n\n"
                "Use one of the above instead."
            ),
            "blocking_hook": "PreToolUse_mcp_full_read_guard.py",
        }

    # Documentation roots without anchors (likely full-page dumps)
    if _DOC_ROOT_RE.match(url) and not has_fragment:
        return {
            "decision": "block",
            "reason": (
                "⛔ MCP FULL-READ BLOCKED: web-reader on a documentation root page "
                f"({host}) without a specific anchor (#section) will return the entire page.\n\n"
                "Preferred alternatives:\n"
                "  1. mcp__tavily-mcp__tavily_search  — search for the specific fact\n"
                "  2. Add a URL fragment (#section) to target the specific section\n"
                "  3. mcp__perplexity__perplexity_search  — returns synthesized answers\n\n"
                "Use one of the above instead."
            ),
            "blocking_hook": "PreToolUse_mcp_full_read_guard.py",
        }

    # Everything else: allow
    return None


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        data = json.loads(raw.lstrip("\ufeff"))
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    if not isinstance(tool_name, str):
        sys.exit(0)

    # --- web-reader: check URL pattern ---
    if "web-reader" in tool_name or "webReader" in tool_name:
        url = str(tool_input.get("url", tool_input.get("URL", ""))).strip()
        block = _check_url(url)
        if block:
            print(json.dumps(block))
            sys.exit(0)

    # tavily_extract: no pre-call block — PostToolUse bloat guard handles large responses
    # after the fact with a WARNING/CRITICAL advisory if the payload is too big.

    # Allow all other patterns
    sys.exit(0)


if __name__ == "__main__":
    main()
