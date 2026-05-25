"""In-process PostToolUse hook to record locally-found artifacts into session ledger.

Monitors Grep, Glob, and Read tool results. When matches are found,
records the search keyword and source path into artifact_ledger for
later cross-validation against external fetch/install commands.

Registered in-process via PostToolUse/__init__.py create_registry().
Subprocess registration via settings.json PostToolUse section is now redundant
but kept as fallback for sessions started before this conversion.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

sys.path.insert(0, str(Path(__file__).parent.parent / "__lib"))
from artifact_ledger import record


class ArtifactScraperHook(PostToolUseHook):
    """Record found artifacts from Grep/Glob/Read into ledger."""

    tool_matcher: set[str] | None = {"Grep", "Glob", "Read"}

    def process(
        self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """Record found artifacts from Grep/Glob/Read into ledger.

        Args:
            tool_name: Name of the tool that was used
            tool_input: Input parameters passed to the tool
            tool_response: Output returned by the tool

        Returns:
            Dict with results (advisory, always passes).
        """
        session_id = tool_input.get("session_id", "")
        if not session_id:
            return {"passed": True}

        # Extract keyword from tool input
        keyword = tool_input.get("pattern") or tool_input.get("file_path", "")
        if not keyword:
            return {"passed": True}

        # Use stem for file paths; full pattern for regex/glob
        if "/" in str(keyword) or "\\" in str(keyword):
            keyword = Path(str(keyword)).stem
        keyword = str(keyword)

        # Normalize tool_response
        resp_str = tool_response.get("output", "") or tool_response.get("result", "") or ""
        if isinstance(resp_str, dict):
            resp_str = str(resp_str)

        # Extract source paths from response (first few matches)
        # Windows paths: C:\path\to\file.py, Unix paths: /path/to/file.py
        sources = re.findall(
            r"[A-Za-z]:[\\/][^\s:]*\.(?:py|md|jsonl|json|ts|js)|"
            r"/[^\s:]*\.(?:py|md|jsonl|json|ts|js)|"
            r"[^\s:]*[\\/][^\s:]*\.(?:py|md|jsonl|json|ts|js)",
            resp_str
        )[:3]

        # If Read tool, use the file path directly
        if tool_name == "Read" and not sources:
            sources = [tool_input.get("file_path", "")]

        turn = tool_input.get("turn_index", 0)
        for src in sources:
            if src:
                # Normalize Windows paths to forward slashes for consistent matching
                src = Path(src).as_posix()
                record(session_id, keyword, src, turn)

        return {"passed": True}