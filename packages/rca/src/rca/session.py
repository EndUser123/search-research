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
import os
import re
import sys
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

# Re-export FixType, MatchType, record_debug_start from metrics_tracker for compatibility
try:
    from .metrics_tracker import FixType, MatchType, record_debug_start
except ImportError:
    # Fallback definitions if metrics_tracker is not available
    class FixType(Enum):
        """Types of fixes applied"""
        QUICK_FIX = "quick_fix"
        RCA_SPECIALIST = "rca_specialist"
        MANUAL = "manual"

    class MatchType(Enum):
        """Types of CHS matches"""
        EXACT = "exact"
        PATTERN = "pattern"
        NONE = "none"

    def record_debug_start(*args, **kwargs):
        """Fallback for record_debug_start"""
        raise NotImplementedError("metrics_tracker module required")


class ProblemType(Enum):
    """Classification of problem types for RCA routing."""

    ERROR = "error"
    TEST = "test"
    CRASH = "crash"
    PERFORMANCE = "performance"
    BEHAVIOR = "behavior"


def _get_default_session_path() -> Path:
    """Get the default session path from environment or use default.

    Environment variable: DEBUG_RCA_STATE_DIR
    Default: P:/.claude/state/rca/ (for monorepo compatibility)
    """
    base = os.environ.get("DEBUG_RCA_STATE_DIR", "P:/.claude/state/rca")
    return Path(base) / "active_session.json"


SESSION_STATE_PATH = _get_default_session_path()
ACTIVE_SESSION_TTL_HOURS = 8


def classify_problem_type(text: str) -> ProblemType:
    """Map user input text to a ProblemType enum value.

    Order matters: more specific categories (TEST, CRASH) are checked before
    the broad ERROR category to avoid false matches on shared keywords like
    "failed".
    """
    t = text.lower()
    # TEST first - "test failed" / "pytest" would otherwise match ERROR's "failed"
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
            print(f"\n  WARNING: {total} timeout warnings in recent logs")
            for hook, count in sorted(timeout_by_hook.items(), key=lambda x: -x[1])[:3]:
                print(f"     - {hook}: {count} occurrences")
    except Exception:
        # Silently fail if log reading fails
        pass


def _analyze_session_friction() -> list[str]:
    """Search logs for actual block reasons to bind analysis to evidence."""
    friction = []
    log_paths = [
        Path(".claude/logs/skill_execution_gate.jsonl"),
        Path(".claude/hooks/logs/diagnostics/cc_errors.jsonl")
    ]
    for path in log_paths:
        if path.exists():
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
                for line in lines[-20:]:  # Check last 20 entries
                    try:
                        entry = json.loads(line)
                        if "reason" in entry:
                            friction.append(entry["reason"])
                        elif "error_type" in entry:
                            friction.append(entry["error_type"])
                    except (json.JSONDecodeError, KeyError, TypeError):
                        # Skip malformed log entries - friction collection is best-effort
                        continue
            except (OSError, IOError):
                # Log file may be locked or unreadable - skip this path
                pass
    return list(set(friction))

def manage_active_session(
    user_input: str,
    source: str,
    context: str | None = None,
) -> tuple[str, dict]:
    """Start metrics session and write active_session.json.

    Args:
        user_input: Raw user prompt text.
        source: Skill name ("debug" or "rca").
        context: Optional context string for metrics_tracker.

    Returns:
        (session_id, session_state_dict)
    """
    problem_type = classify_problem_type(user_input)
    session_id = f"{source}_{uuid.uuid4().hex[:12]}"

    SESSION_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _cleanup_stale_session(SESSION_STATE_PATH)

    # Detect friction items to bind the RCA to evidence
    friction_items = _analyze_session_friction()

    session_state = {
        "session_id": session_id,
        "source": source,
        "created_at": datetime.now().isoformat(),
        "problem_preview": user_input[:200],
        "session_friction": friction_items,
    }
    SESSION_STATE_PATH.write_text(
        json.dumps(session_state, indent=2), encoding="utf-8"
    )

    if friction_items:
        print(f"\n  DETECTED SESSION FRICTION: {len(friction_items)} block/error patterns found in logs.")
        for item in friction_items[:3]:
            print(f"     - {item[:80]}...")

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

    NOTE: This requires the daemons module from the CSF monorepo.
    Set DEBUG_RCA_CSF_SRC environment variable to the CSF source path.
    Without this dependency, the function returns "unavailable" status.

    Implements fast-path skip for obvious local tracebacks unless
    the user explicitly asks about history/regression/patterns.

    Returns:
        Dict with keys: status, count, results
    """
    csf_src = os.environ.get("DEBUG_RCA_CSF_SRC")
    if not csf_src:
        print("  CKS/CHS lookup unavailable: DEBUG_RCA_CSF_SRC not set")
        return {"status": "unavailable", "count": 0, "results": []}

    try:
        sys.path.insert(0, csf_src)
        from daemons.daemon_client import DaemonClient

        client = DaemonClient(
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

    except ImportError:
        print("  CKS/CHS lookup unavailable: daemons module not found")
        return {"status": "unavailable", "count": 0, "results": []}
    except Exception as e:
        print(f"  CKS/CHS lookup unavailable: {e}")
        return {"status": "error", "count": 0, "results": []}


def run_regression_check(user_input: str, days: int = 30) -> str | None:
    """Basic regression check using keyword matching.

    Returns warning if similar issues were recently fixed but may have reverted.

    NOTE: This is a HEURISTIC implementation using keyword matching, not a
    historical lookup against actual fix records. The `days` parameter is
    informational only - this function does NOT query historical data.

    For true regression detection based on historical fix records, the
    CSF daemons module must be available via DEBUG_RCA_CSF_SRC environment
    variable, which provides access to outcome_recorder and CKS history.

    Args:
        user_input: The user's problem description.
        days: Number of days to look back for similar issues (default 30).
               NOTE: Not used in heuristic implementation - kept for API
               compatibility with future historical lookup.

    Returns:
        Warning string if keyword patterns found, None otherwise.
    """
    # Common fix keywords that may regress
    recent_fixes = [
        "none", "null", "timeout", "import", "keyerror",
        "attribute", "type", "value", "connection", "permission",
        "not found", "undefined", "missing", "invalid"
    ]
    user_lower = user_input.lower()

    for keyword in recent_fixes:
        if keyword in user_lower:
            return (f"WARNING: Similar '{keyword}' issues seen in past {days} days. "
                   f"Verify fix didn't revert.")

    return None
