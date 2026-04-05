"""
Shared tracking module for constitutional hooks.
Logs blocked operations for sensitivity analysis.

Severity levels:
- CRITICAL: Hard blocks, security violations, must always show
- WARN: Soft blocks, policy violations, show if threshold exceeded
- INFO: Logged for analysis only, never shown in summary
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Severity level constants
SEVERITY_CRITICAL = "critical"  # Always show, blocks execution
SEVERITY_WARN = "warn"  # Show if threshold exceeded
SEVERITY_INFO = "info"  # Log only, never show in summary

# Terminal ID for isolation
try:
    from __lib.terminal_detection import detect_terminal_id

    TERMINAL_ID = detect_terminal_id()
except ImportError:
    TERMINAL_ID = "unknown"

# Terminal-scoped log files for multi-terminal isolation
TRACKING_FILE = Path(f"P:/.claude/hooks/logs/constructional_blocks_{TERMINAL_ID}.jsonl")
TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)

# Parallel execution event log (terminal-scoped)
PARALLEL_LOG_FILE = Path(f"P:/.claude/hooks/logs/parallel_execution_{TERMINAL_ID}.jsonl")
PARALLEL_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Session tracking for Stop hook summaries
SESSION_DIR = Path(__file__).resolve().parent.parent / "sessions"
SESSION_MARKER = SESSION_DIR / ".session_start"
SESSION_FALLBACK_MINUTES = int(os.environ.get("HOOK_TRACKER_SESSION_FALLBACK_MINUTES", "30"))
SESSION_MAX_AGE_HOURS = float(os.environ.get("HOOK_TRACKER_SESSION_MAX_AGE_HOURS", "6"))
FALLBACK_TERMINAL_WINDOW_MINUTES = int(
    os.environ.get("HOOK_TRACKER_FALLBACK_TERMINAL_WINDOW_MINUTES", "20")
)


def _get_session_start() -> datetime:
    """Get session start time from marker file, or now if no marker exists."""
    now = datetime.now()

    # Fallback terminal IDs are globally shared in some environments.
    # Restrict lookback to avoid cross-session noise accumulation.
    if str(TERMINAL_ID).startswith("fallback_"):
        return now - timedelta(minutes=max(1, FALLBACK_TERMINAL_WINDOW_MINUTES))

    if SESSION_MARKER.exists():
        try:
            with open(SESSION_MARKER) as f:
                iso_time = f.read().strip()
                session_start = datetime.fromisoformat(iso_time)
                if (now - session_start).total_seconds() > (SESSION_MAX_AGE_HOURS * 3600):
                    return now - timedelta(minutes=max(1, SESSION_FALLBACK_MINUTES))
                return session_start
        except:
            pass
    # Fallback: bounded recent window
    return now - timedelta(minutes=max(1, SESSION_FALLBACK_MINUTES))


SESSION_ID = os.environ.get("CLAUDE_SESSION_ID", "unknown")


def is_hook_self_operation(command: str) -> bool:
    """Check if command is modifying hooks themselves - should allow."""
    cmd_lower = command.lower()
    return ".claude/hooks/" in cmd_lower or ".claude\\\\hooks\\\\" in cmd_lower


def is_bypass_enabled() -> bool:
    """Check if bypass is enabled via environment variable."""
    return os.environ.get("CONSTITUTIONAL_HOOKS_BYPASS", "").lower() in ("1", "true", "yes")


def is_scoped_bypass(log_bypass: bool = True) -> bool:
    """
    Check if a scoped bypass is enabled via environment variable.

    Scoped bypasses allow specific operations while maintaining audit logging.
    Unlike CONSTITUTIONAL_HOOKS_BYPASS, these are operation-specific and logged.

    Supported bypass variables:
    - ALLOW_VDATE_VALIDATION=1: Allow vdate validation commands
    - ALLOW_BUILD_VALIDATION=1: Allow build validation commands

    Args:
        log_bypass: If True, log the bypass to audit trail

    Returns:
        True if any scoped bypass is enabled, False otherwise
    """
    scoped_bypass_vars = [
        "ALLOW_VDATE_VALIDATION",
        "ALLOW_BUILD_VALIDATION",
    ]

    active_bypasses = []
    for var in scoped_bypass_vars:
        if os.environ.get(var, "").lower() in ("1", "true", "yes"):
            active_bypasses.append(var)

    if active_bypasses and log_bypass:
        # Log the scoped bypass for audit trail
        log_block(
            "scoped_bypass", "environment_check", "", f"scoped_bypass: {', '.join(active_bypasses)}"
        )

    return len(active_bypasses) > 0


def is_test_pattern(command: str) -> bool:
    """Check if command is a test pattern (should not be logged)."""
    cmd_lower = command.lower()

    # Pytest environment detection
    if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("PYTEST_XDIST_WORKER"):
        return True

    # Obvious test command patterns
    test_indicators = [
        'eval("evil")',
        "eval('evil')",
        'exec("evil")',
        "exec('evil')",
        'open("settings.json", "w")',
        "open('settings.json', 'w')",
        'open(".env", "w")',
        "open('.env', 'w')",
        'open("test.py", "w")',
        "open('test.py', 'w')",
        '.write("test")',
        ".write('test')",
    ]
    return any(indicator in cmd_lower for indicator in test_indicators)


def log_block(hook_name: str, tool: str, command: str, reason: str, severity: str = SEVERITY_WARN):
    """Log a blocked operation for analysis.

    Args:
        hook_name: Name of the hook that triggered
        tool: Tool being used (e.g., "Bash")
        command: The command that was flagged
        reason: Why it was flagged
        severity: One of SEVERITY_CRITICAL, SEVERITY_WARN, SEVERITY_INFO
    """
    # Skip logging hook self-operations, bypassed operations, or test patterns
    # EXCEPTION: Always log scoped_bypass entries (for audit trail in tests)
    # Check if this is a scoped bypass log entry
    is_scoped_bypass_log = hook_name == "scoped_bypass" or "scoped_bypass" in reason.lower()

    if is_scoped_bypass_log:
        # Always log scoped bypass, even in test mode
        pass
    elif is_hook_self_operation(command) or is_bypass_enabled() or is_test_pattern(command):
        return

    entry = {
        "timestamp": datetime.now().isoformat(),
        "terminal_id": TERMINAL_ID,  # For filtering by terminal
        "hook": hook_name,
        "tool": tool,
        "command": command[:200],  # Truncate for readability
        "reason": reason[:100],
        "severity": severity,
    }
    try:
        # Access TRACKING_FILE dynamically to support patching in tests
        import sys

        hook_tracker_module = sys.modules.get("hook_tracker")
        if hook_tracker_module and hasattr(hook_tracker_module, "TRACKING_FILE"):
            tracking_file = hook_tracker_module.TRACKING_FILE
        else:
            tracking_file = globals()["TRACKING_FILE"]

        # Use file-level locking to prevent race conditions in parallel execution
        from file_lock_manager import acquire_lock, release_lock

        lock_path = str(tracking_file) + ".write"
        lock_acquired, _ = acquire_lock(lock_path)
        try:
            with open(tracking_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        finally:
            if lock_acquired:
                release_lock(lock_path)
    except Exception:
        pass  # Non-fatal if logging fails


def log_parallel_event(
    event_type: str, hooks_involved: list[str], details: str, error_count: int = 0
) -> None:
    """Log a parallel execution event for auditing.

    Args:
        event_type: Type of event (error, timeout, auto_disable)
        hooks_involved: List of hooks involved in the event
        details: Description of what happened
        error_count: Current error count (for auto-disable tracking)
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "terminal_id": TERMINAL_ID,
        "event_type": event_type,
        "hooks": hooks_involved,
        "details": details[:200],
        "error_count": error_count,
    }
    try:
        from file_lock_manager import acquire_lock, release_lock

        lock_path = str(PARALLEL_LOG_FILE) + ".write"
        lock_acquired, _ = acquire_lock(lock_path)
        try:
            with open(PARALLEL_LOG_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        finally:
            if lock_acquired:
                release_lock(lock_path)
    except Exception:
        pass  # Non-fatal


def log_parallel_metrics(
    hooks: list[str], elapsed: float, errors: int = 0, timed_out: list[str] | None = None
) -> None:
    """Log parallel execution performance metrics.

    Logs timing and error information for parallel hook execution.
    Used to monitor performance and detect problems during soak testing.

    Args:
        hooks: List of hook names that were executed in parallel
        elapsed: Time taken for parallel execution (seconds)
        errors: Number of errors that occurred (default: 0)
        timed_out: Optional list of hooks that timed out (default: None)
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "terminal_id": TERMINAL_ID,
        "event_type": "metrics",
        "hooks": hooks,
        "parallel": True,
        "elapsed_ms": round(elapsed * 1000, 2),
        "errors": errors,
        "timed_out": timed_out or [],
    }
    try:
        from file_lock_manager import acquire_lock, release_lock

        lock_path = str(PARALLEL_LOG_FILE) + ".write"
        lock_acquired, _ = acquire_lock(lock_path)
        try:
            with open(PARALLEL_LOG_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        finally:
            if lock_acquired:
                release_lock(lock_path)
    except Exception:
        pass  # Non-fatal


def get_parallel_health() -> dict:
    """Get parallel execution health summary.

    Returns:
        Dict with error_count, auto_disable_count, recent_errors
    """
    if not PARALLEL_LOG_FILE.exists():
        return {"error_count": 0, "auto_disable_count": 0, "recent_errors": []}

    errors = 0
    auto_disables = 0
    recent = []

    try:
        with open(PARALLEL_LOG_FILE) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("event_type") == "error":
                        errors += 1
                        if len(recent) < 5:
                            recent.append(entry)
                    elif entry.get("event_type") == "auto_disable":
                        auto_disables += 1
                except json.JSONDecodeError:
                    pass
    except Exception:
        pass

    return {"error_count": errors, "auto_disable_count": auto_disables, "recent_errors": recent}


def get_session_summary() -> dict:
    """Get summary of hook violations for current session.

    Returns: {
        "total": int,              # Total entries (all severities)
        "warn_count": int,         # WARN severity count (for threshold)
        "critical_count": int,     # CRITICAL severity count (always show)
        "info_count": int,         # INFO severity count (never show)
        "by_hook": {hook: count},  # Breakdown by hook name
        "by_reason": {reason: count},  # Breakdown by reason (WARN+ only)
    }
    """
    if not TRACKING_FILE.exists():
        return {
            "total": 0,
            "warn_count": 0,
            "critical_count": 0,
            "info_count": 0,
            "by_hook": {},
            "by_hook_critical": {},
            "by_hook_warn": {},
            "by_hook_info": {},
            "by_reason": {},
        }

    try:
        session_entries = []
        with open(TRACKING_FILE) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    # Filter by terminal_id (ignore entries from other terminals)
                    if entry.get("terminal_id", "unknown") != TERMINAL_ID:
                        continue
                    # Parse timestamp and check if within session
                    try:
                        ts = datetime.fromisoformat(entry["timestamp"])
                        if ts >= _get_session_start():
                            session_entries.append(entry)
                    except:
                        pass
                except:
                    pass

        if not session_entries:
            return {
                "total": 0,
                "warn_count": 0,
                "critical_count": 0,
                "info_count": 0,
                "by_hook": {},
                "by_hook_critical": {},
                "by_hook_warn": {},
                "by_hook_info": {},
                "by_reason": {},
            }

        by_hook = {}
        by_hook_critical = {}
        by_hook_warn = {}
        by_hook_info = {}
        by_reason = {}  # Only WARN+ reasons
        critical_count = 0
        warn_count = 0
        info_count = 0

        for e in session_entries:
            hook = e.get("hook", "unknown")
            reason = e.get("reason", "unknown")
            severity = e.get("severity", SEVERITY_WARN)  # Default old entries to WARN

            # Override severity detection for legacy entries without severity field
            if "severity" not in e:
                # Infer severity from patterns
                if "HARD BLOCK" in reason.upper() or hook == "recursive_failure_detector":
                    severity = SEVERITY_CRITICAL
                elif reason.startswith("WARNING:"):
                    severity = SEVERITY_INFO  # Demote old WARNING patterns to INFO
                else:
                    severity = SEVERITY_WARN

            by_hook[hook] = by_hook.get(hook, 0) + 1

            # Track by severity
            if severity == SEVERITY_CRITICAL:
                critical_count += 1
                by_hook_critical[hook] = by_hook_critical.get(hook, 0) + 1
                by_reason[reason] = by_reason.get(reason, 0) + 1
            elif severity == SEVERITY_WARN:
                warn_count += 1
                by_hook_warn[hook] = by_hook_warn.get(hook, 0) + 1
                by_reason[reason] = by_reason.get(reason, 0) + 1
            else:  # INFO
                info_count += 1
                by_hook_info[hook] = by_hook_info.get(hook, 0) + 1
                # INFO entries don't go into by_reason (not shown in summary)

        return {
            "total": len(session_entries),
            "warn_count": warn_count,
            "critical_count": critical_count,
            "info_count": info_count,
            "by_hook": by_hook,
            "by_hook_critical": by_hook_critical,
            "by_hook_warn": by_hook_warn,
            "by_hook_info": by_hook_info,
            "by_reason": by_reason,
        }
    except Exception:
        return {
            "total": 0,
            "warn_count": 0,
            "critical_count": 0,
            "info_count": 0,
            "by_hook": {},
            "by_hook_critical": {},
            "by_hook_warn": {},
            "by_hook_info": {},
            "by_reason": {},
        }
