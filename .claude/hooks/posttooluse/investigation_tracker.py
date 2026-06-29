#!/usr/bin/env python3
"""
PostToolUse Hook: Investigation Ledger Tracker (In-Process)

Records file reads, searches, and executions to the investigation ledger.
Used by Stop_investigation_validator to validate claims against investigation.

Lazy-imports ledger module to avoid ~64ms import cost on non-matching tools.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

# Path setup at module level (cheap), actual import deferred to process()
_LEDGER_DIR = Path(__file__).resolve().parent.parent / "investigation-ledger"

# CHANGE-007 write-side: a passing verification command records the files it
# covered so is_verified() can later detect edits made after this point.
# Pattern-gated so an unrelated passing command (ls, git status) does not mark
# files verified. ponytail: git diff is the cheapest correct source of "what
# changed" — import-resolution from test names would be heavier and wrong-often.
# ponytail: over-stamping ceiling — git diff lists ALL changed files, not just
# the ones this runner executed, so an untested-but-changed sibling gets stamped
# too (a false negative at the consumer, not a nag). Accept until a measured FN
# rate justifies per-runner output parsing; narrow the trigger then, not now.
_VERIFICATION_CMD_RE = re.compile(
    r"\b(?:pytest|python\s+-m\s+pytest|python\s+-m\s+unittest|"
    r"npm\s+(?:test|run\s+test)|yarn\s+test|pnpm\s+test|"
    r"cargo\s+test|make\s+test|go\s+test)\b"
)


def _git_changed_files() -> list[str]:
    """Files changed vs HEAD (staged + unstaged). Fail-open: [] on any error."""
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
        if out.returncode == 0:
            return [f for f in out.stdout.splitlines() if f.strip()]
    except Exception:
        pass
    return []


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
            from ledger import (
                record_execution,
                record_file_read,
                record_search,
                record_verification,
            )
            self._ledger_funcs = {
                "file_read": record_file_read,
                "search": record_search,
                "execution": record_execution,
                "verification": record_verification,
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

                    # CHANGE-007 write-side: a successful verification command
                    # stamps the changed files as verified-at-this-hash.
                    # is_verified() then answers "did the model edit after
                    # verifying?" — Stop_fake_done_detector consumes that.
                    stamp = ledger.get("verification")
                    if exit_code == 0 and stamp and _VERIFICATION_CMD_RE.search(command):
                        for f in _git_changed_files():
                            try:
                                stamp(f, mode="strict",
                                      command=command[:500],
                                      exit_code=exit_code)
                            except Exception:
                                pass

            return {"passed": True, "recorded": recorded, "tool": tool_name}
        except Exception:
            # Fail open: investigation logging should never block PostToolUse.
            return {"passed": True, "recorded": False, "tool": tool_name}
