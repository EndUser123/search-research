#!/usr/bin/env python3
"""
PostToolUse Hook: Investigation Ledger Tracker (In-Process)

Records file reads, searches, and executions to the investigation ledger.
Used by Stop_investigation_validator to validate claims against investigation.

Lazy-imports ledger module to avoid ~64ms import cost on non-matching tools.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

# Path setup at module level (cheap), actual import deferred to process()
_LEDGER_DIR = Path(__file__).resolve().parent.parent / "investigation-ledger"


class InvestigationTracker(PostToolUseHook):
    """Tracks tool usage to the investigation ledger.

    Records file reads, searches, and command executions.
    Used by Stop_investigation_validator to validate claims against investigation.
    """

    tool_matcher = {"Read", "Grep", "Glob", "Bash"}
    env_var = "INVESTIGATION_LEDGER_ENABLED"
    default_enabled = True

    # Cache ledger functions after first successful import
    _ledger_funcs: dict | None = None

    def _get_ledger(self) -> dict | None:
        """Lazy-import ledger module. Returns dict of functions or None."""
        if self._ledger_funcs is not None:
            return self._ledger_funcs

        if str(_LEDGER_DIR) not in sys.path:
            sys.path.insert(0, str(_LEDGER_DIR))

        try:
            from ledger import record_execution, record_file_read, record_search
            self._ledger_funcs = {
                "file_read": record_file_read,
                "search": record_search,
                "execution": record_execution,
            }
            return self._ledger_funcs
        except ImportError:
            # Mark as permanently unavailable
            self._ledger_funcs = {}
            return None

    def process(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_response: dict[str, Any],
    ) -> dict[str, Any]:
        ledger = self._get_ledger()
        if not ledger:
            return {"passed": True, "skipped": True, "reason": "ledger unavailable"}

        try:
            recorded = False

            # Dispatch by exact tool_name (matcher already filtered)
            if tool_name == "Read":
                path = tool_input.get("file_path") or tool_input.get("path") or ""
                if path:
                    result_str = str(tool_response)[:500]
                    if "error" not in result_str.lower():
                        recorded = ledger["file_read"](path)

            elif tool_name in ("Grep", "Glob"):
                query = tool_input.get("pattern") or ""
                if query:
                    results_count = 0
                    if isinstance(tool_response, dict):
                        results = tool_response.get("results", tool_response.get("matches", []))
                        if isinstance(results, list):
                            results_count = len(results)
                    recorded = ledger["search"](query, results_count)

            elif tool_name == "Bash":
                command = tool_input.get("command") or ""
                if command:
                    exit_code = -1
                    if isinstance(tool_response, dict):
                        exit_code = tool_response.get("exit_code", tool_response.get("exitCode", -1))
                    recorded = ledger["execution"](command, exit_code)

            return {"passed": True, "recorded": recorded, "tool": tool_name}
        except Exception:
            # Fail open: investigation logging should never block PostToolUse.
            return {"passed": True, "recorded": False, "tool": tool_name}
