#!/usr/bin/env python3
"""
Shared preflight utilities for /debug and /rca SKILL.md execution directives.

Eliminates ~100 lines of duplication between the two skills by extracting:
- classify_problem_type: Maps user input to ProblemType enum
- detect_error_type: Classifies error string for ReAct routing
- manage_active_session: Creates/loads/cleans up active_session.json
- search_cks_history: DaemonClient CKS search with fast-path skip
- run_regression_check: Queries outcome_recorder for previously failed fixes

Usage from SKILL.md inline code:
    from rca.session_preflight import (
        classify_problem_type, detect_error_type,
        manage_active_session, search_cks_history,
        run_regression_check,
    )
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from .session import ProblemType, record_debug_start

SESSION_STATE_PATH = Path("P:/.claude/state/rca/active_session.json")
ACTIVE_SESSION_TTL_HOURS = 8

# =============================================================================
# Module-level CSF imports with clear error handling
# =============================================================================

# Add CSF to path for imports
_CSF_SRC = str(Path("P:/__csf/src").resolve())
if _CSF_SRC not in sys.path:
    sys.path.insert(0, _CSF_SRC)

# Optional CSF dependencies - set to None if unavailable
_DaemonClient = None
_preflight_check = None
_CSF_IMPORT_ERROR = None

try:
    from daemons.daemon_client import DaemonClient as _DaemonsDaemonClient
    _DaemonClient = _DaemonsDaemonClient
except ImportError as e:
    _CSF_IMPORT_ERROR = f"DaemonClient: {e}"

try:
    from rca.metrics_preflight import preflight_check as _metrics_preflight_check
    _preflight_check = _metrics_preflight_check
except ImportError as e:
    if _CSF_IMPORT_ERROR:
        _CSF_IMPORT_ERROR += f"; metrics_preflight: {e}"
    else:
        _CSF_IMPORT_ERROR = f"metrics_preflight: {e}"


def verify_dependencies() -> bool:
    """Verify that CSF dependencies are available.

    Returns:
        True if all CSF dependencies are available, False otherwise.
    """
    return _DaemonClient is not None and _preflight_check is not None


def get_missing_dependencies() -> list[str]:
    """Get list of missing CSF dependencies.

    Returns:
        List of missing dependency names. Empty list if all available.
    """
    missing = []

    if _DaemonClient is None:
        missing.append("daemons.daemon_client")

    if _preflight_check is None:
        missing.append("rca.metrics_preflight")

    return missing


def classify_problem_type(text: str) -> ProblemType:
    """Map user input text to a ProblemType enum value.

    Order matters: more specific categories (TEST, CRASH) are checked before
    the broad ERROR category to avoid false matches on shared keywords like
    "failed".
    """
    t = text.lower()
    # TEST first — "test failed" / "pytest" would otherwise match ERROR's "failed"
    if any(k in t for k in ["test failed", "pytest", "assertionerror", "test_"]):
        return ProblemType.TEST
    if any(k in t for k in ["crash", "segfault", "core dump"]):
        return ProblemType.CRASH
    if any(k in t for k in ["slow", "latency", "performance", "timeout"]):
        return ProblemType.PERFORMANCE
    if any(k in t for k in ["traceback", "exception", "error", "failed"]):
        return ProblemType.ERROR
    return ProblemType.BEHAVIOR


def detect_error_type(text: str) -> str:
    """Classify error text for ReAct loop routing."""
    t = text.lower()
    if re.search(r"traceback|[a-z_]+error:", t):
        return "python_exception"
    if "timeout" in t:
        return "timeout"
    if "permission denied" in t:
        return "permission_error"
    if "connection refused" in t or "connection reset" in t:
        return "network_error"
    return "generic_error"


def _cleanup_stale_session(path: Path) -> None:
    """Remove active session file if it exceeds TTL."""
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        created_at = data.get("created_at")
        if not created_at:
            return
        age = datetime.now() - datetime.fromisoformat(created_at)
        if age > timedelta(hours=ACTIVE_SESSION_TTL_HOURS):
            try:
                path.unlink()
            except OSError:
                pass
            print(f"  Removed stale active session (> {ACTIVE_SESSION_TTL_HOURS}h).")
    except Exception:
        pass


def _check_timeout_patterns() -> None:
    """Check diagnostic logs for recent timeout patterns and surface them early.

    This provides early visibility into hook performance issues that might be
    related to the current problem, regardless of problem_type classification.
    """
    cc_errors_path = Path(".claude/hooks/logs/diagnostics/cc_errors.jsonl")
    if not cc_errors_path.exists():
        return

    try:
        lines = cc_errors_path.read_text(encoding="utf-8").splitlines()
        # Check last 100 lines for timeout warnings
        recent_lines = lines[-100:] if len(lines) > 100 else lines

        timeout_by_hook: dict[str, int] = {}
        for line in recent_lines:
            if "timeout" not in line.lower():
                continue
            try:
                entry = json.loads(line)
                error_type = entry.get("error_type", "")
                # Extract hook name from error_type (e.g., "PreToolUse_skill_pattern_gate_timeout_imminent")
                if "_timeout_" in error_type:
                    hook_name = error_type.split("_timeout_")[0]
                    timeout_by_hook[hook_name] = timeout_by_hook.get(hook_name, 0) + 1
            except (json.JSONDecodeError, KeyError):
                continue

        if timeout_by_hook:
            total = sum(timeout_by_hook.values())
            print(f"\n  ⚠️  DIAGNOSTIC: {total} timeout warnings in recent logs")
            for hook, count in sorted(timeout_by_hook.items(), key=lambda x: -x[1])[:3]:
                print(f"     - {hook}: {count} occurrences")
    except Exception:
        # Silently fail if log reading fails
        pass


def manage_active_session(
    user_input: str,
    source: str,
    context: str | None = None,
) -> tuple[str, dict]:
    """Start metrics session and write active_session.json.

    Args:
        user_input: Raw user prompt text.
        source: Skill name ("debug" or "rca").
        context: Optional context string for session module.

    Returns:
        (session_id, session_state_dict)
    """
    problem_type = classify_problem_type(user_input)
    session_id = record_debug_start(
        problem_description=(user_input[:500] or f"{source} session"),
        problem_type=problem_type,
        context=context or f"{source}-skill",
    )

    SESSION_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _cleanup_stale_session(SESSION_STATE_PATH)

    session_state = {
        "session_id": session_id,
        "source": source,
        "created_at": datetime.now().isoformat(),
        "problem_preview": user_input[:200],
    }
    SESSION_STATE_PATH.write_text(
        json.dumps(session_state, indent=2), encoding="utf-8"
    )

    # Check for recent timeout patterns in diagnostic logs
    _check_timeout_patterns()

    return session_id, session_state


def load_active_session(path: Path | None = None) -> dict:
    """Load active session state, expiring stale entries."""
    path = path or SESSION_STATE_PATH
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        created_at = data.get("created_at")
        if created_at:
            age = datetime.now() - datetime.fromisoformat(created_at)
            if age > timedelta(hours=ACTIVE_SESSION_TTL_HOURS):
                try:
                    path.unlink()
                except OSError:
                    pass
                print(f"  Active session expired (> {ACTIVE_SESSION_TTL_HOURS}h).")
                return {}
        return data
    except Exception:
        return {}


def search_cks_history(
    user_input: str,
    arguments: str = "",
    limit: int = 3,
) -> dict:
    """Search CKS for similar past problems using DaemonClient.

    Implements fast-path skip for obvious local tracebacks unless
    the user explicitly asks about history/regression/patterns.

    Returns:
        Dict with keys: status, count, results
    """
    if _DaemonClient is None:
        print(f"  CKS/CHS lookup unavailable: {_CSF_IMPORT_ERROR or 'CSF dependencies not found'}")
        return {"status": "error", "count": 0, "results": []}

    try:
        client = _DaemonClient(
            auto_start=True,
            enable_fallback=True,
            timeout=5.0,
        )

        obvious_local_trace = bool(
            re.search(r'Traceback|File ".*", line \d+|[A-Za-z]+Error:', user_input)
        )
        history_intent = any(
            x in user_input.lower()
            for x in ["seen before", "again", "regression", "pattern", "similar"]
        )
        force_search = "--deep" in arguments or "--synthesize" in arguments

        if obvious_local_trace and not history_intent and not force_search:
            print("  Fast-path: skipping CKS search for obvious local traceback.")
            return {"status": "skipped", "count": 0, "results": []}

        results = client.search("cks", user_input, limit=limit)

        if results["status"] == "success" and results["count"] > 0:
            print(f"\n  SIMILAR PAST PROBLEMS: {results['count']} found in CKS")
            for r in results["results"][:3]:
                title = r.get("title", "")[:80]
                print(f"     {title}")
        else:
            print("  No similar problems found in CKS.")

        return results

    except Exception as e:
        print(f"  CKS/CHS lookup unavailable: {e}")
        return {"status": "error", "count": 0, "results": []}


def run_regression_check(user_input: str, days: int = 30) -> str | None:
    """Query outcome_recorder for previously failed fixes on similar problems.

    Returns formatted warning string if failed outcomes exist, None otherwise.
    """
    if _preflight_check is None:
        return None

    try:
        report = _preflight_check(user_input, days_lookback=days)
        if report.failed_approaches:
            return report.format()
        return None
    except Exception:
        return None
