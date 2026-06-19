#!/usr/bin/env python3
from __future__ import annotations

"""
CC Diagnostic Logger - SQLite + WAL Mode
==========================================

Central logging infrastructure for diagnosing Claude Code behavior.
Uses SQLite with WAL mode for concurrent multi-terminal access.

Purpose:
- Capture what context CC receives
- Track hook invocations and injections
- Log full tool inputs/outputs
- Identify decision points and assumptions

SQLite Benefits:
- WAL mode enables concurrent reads/writes
- Built-in transaction handling (ACID)
- No manual file locking needed
- 5-second busy timeout covers any realistic hook duration

Author: CSF
Version: 2.0.0 (SQLite migration)
"""

import hashlib
import json
import os
import sqlite3
import sys
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# Import terminal detection for multi-terminal traceability
try:
    from __lib.terminal_detection import detect_terminal_id

    TERMINAL_DETECTION_AVAILABLE = True
except ImportError:
    TERMINAL_DETECTION_AVAILABLE = False
    detect_terminal_id = lambda: "unknown"

# Try to import buffered logger for better performance
try:
    from buffered_logger import (
        BufferedLogger,
        get_context_logger,
        get_hook_invocation_logger,
        get_tool_call_logger,
    )

    BUFFERED_LOGGER_AVAILABLE = True
except ImportError:
    BUFFERED_LOGGER_AVAILABLE = False

# =============================================================================
# CONFIGURATION
# =============================================================================

DIAGNOSTICS_ENABLED = os.environ.get("CC_DIAGNOSTICS_ENABLED", "true").lower() == "true"
DIAGNOSTICS_DEBUG = os.environ.get("CC_DIAGNOSTICS_DEBUG", "false").lower() == "true"
LOG_DIR = Path(
    os.environ.get(
        "CC_DIAGNOSTICS_DIR", str(Path(__file__).resolve().parent / "logs/diagnostics")
    )
)
MAX_CONTENT_LENGTH = 5000  # Truncate very long content
BUSY_TIMEOUT_MS = 5000  # Wait up to 5 seconds for database lock
IMPORTER_RETENTION_DAYS = max(
    1, int(os.environ.get("CC_IMPORTER_RETENTION_DAYS", "14"))
)
# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# DATABASE SETUP
# =============================================================================

DB_PATH = LOG_DIR / "diagnostics.db"

# Thread-local storage for connections (each thread gets its own connection)
_local = threading.local()


def _get_connection() -> sqlite3.Connection:
    """Get thread-local database connection with WAL mode enabled."""
    if not hasattr(_local, "conn"):
        conn = sqlite3.connect(
            str(DB_PATH),
            check_same_thread=False,  # Allow sharing across threads
            timeout=BUSY_TIMEOUT_MS / 1000.0,  # Convert to seconds
        )
        conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL for concurrency
        conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety/performance
        conn.execute("PRAGMA busy_timeout=%d" % BUSY_TIMEOUT_MS)  # Wait for locks
        _local.conn = conn
    return _local.conn


def _init_schema() -> None:
    """Initialize database schema if not exists."""
    conn = _get_connection()

    # Context logs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            terminal_id TEXT NOT NULL,
            event TEXT NOT NULL,
            prompt_preview TEXT,
            prompt_length INTEGER,
            prompt_hash TEXT,
            claude_md_present INTEGER,
            injected_content TEXT,
            injected_total_tokens INTEGER,
            conversation_length INTEGER,
            metadata TEXT
        )
    """)

    # Hook invocations
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            terminal_id TEXT NOT NULL,
            turn_id TEXT,
            event TEXT NOT NULL,
            hook_name TEXT NOT NULL,
            event_type TEXT NOT NULL,
            action TEXT NOT NULL,
            injection_preview TEXT,
            injection_length INTEGER,
            reason TEXT,
            duration_ms REAL,
            execution_time_ms REAL,
            timeout_ms INTEGER,
            output_size_bytes INTEGER
        )
    """)

    # Tool calls
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            terminal_id TEXT NOT NULL,
            event TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            tool_input TEXT,
            tool_output_preview TEXT,
            tool_output_length INTEGER,
            success INTEGER NOT NULL,
            error_type TEXT,
            error_message TEXT,
            duration_ms REAL
        )
    """)

    # Assumptions
    conn.execute("""
        CREATE TABLE IF NOT EXISTS assumptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            terminal_id TEXT NOT NULL,
            event TEXT NOT NULL,
            assumption_type TEXT NOT NULL,
            assumption TEXT NOT NULL,
            source TEXT NOT NULL,
            verified INTEGER NOT NULL,
            verification_result TEXT
        )
    """)

    # Errors
    conn.execute("""
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            terminal_id TEXT NOT NULL,
            event TEXT NOT NULL,
            error_type TEXT NOT NULL,
            error_message TEXT NOT NULL,
            context TEXT,
            stack_trace TEXT,
            user_prompt_preview TEXT,
            user_prompt_hash TEXT,
            claude_session_id TEXT
        )
    """)

    # Importer anomalies
    conn.execute("""
        CREATE TABLE IF NOT EXISTS importer_diagnostics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            hook_name TEXT NOT NULL,
            phase TEXT NOT NULL,
            session_id TEXT,
            terminal_id TEXT,
            tool_name TEXT,
            input_hash TEXT,
            input_bytes INTEGER,
            error_text TEXT NOT NULL,
            traceback TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS diag_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    try:
        conn.execute("ALTER TABLE hooks ADD COLUMN turn_id TEXT")
    except sqlite3.OperationalError:
        pass

    # Create indexes for common queries after the migration has had a chance to
    # add the new column on older databases.
    conn.execute("CREATE INDEX IF NOT EXISTS idx_context_session ON context(session_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hooks_session ON hooks(session_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hooks_turn ON hooks(turn_id)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_hooks_session_turn ON hooks(session_id, turn_id)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tools_session ON tools(session_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_assumptions_session ON assumptions(session_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_errors_session ON errors(session_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hooks_timestamp ON hooks(timestamp DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tools_timestamp ON tools(timestamp DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_importer_timestamp ON importer_diagnostics(timestamp DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_importer_hook_phase ON importer_diagnostics(hook_name, phase)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_importer_session ON importer_diagnostics(session_id)")

    conn.commit()


def _meta_get(key: str) -> str | None:
    """Fetch a diagnostic metadata value."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM diag_meta WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else None


def _meta_set(key: str, value: str) -> None:
    """Persist a diagnostic metadata value."""
    conn = _get_connection()
    conn.execute(
        """
        INSERT INTO diag_meta(key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )
    conn.commit()


def _maybe_cleanup_importer_diagnostics() -> None:
    """Prune stale importer diagnostics and occasionally vacuum the database."""
    if not DIAGNOSTICS_ENABLED:
        return

    now = datetime.now(UTC)
    try:
        last_cleanup_raw = _meta_get("importer_diag_last_cleanup")
        if last_cleanup_raw:
            last_cleanup = datetime.fromisoformat(last_cleanup_raw)
            if (now - last_cleanup).total_seconds() < 24 * 3600:
                return
    except Exception:
        pass

    cutoff = now - timedelta(days=IMPORTER_RETENTION_DAYS)
    conn = _get_connection()
    deleted_rows = 0
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM importer_diagnostics WHERE timestamp < ?",
            (cutoff.isoformat(),),
        )
        deleted_rows = cursor.rowcount if cursor.rowcount is not None else 0
        conn.commit()
        _meta_set("importer_diag_last_cleanup", now.isoformat())
    except Exception:
        return

    # VACUUM intentionally omitted: VACUUM rewrites the entire DB file and,
    # when interrupted mid-write during concurrent multi-terminal access,
    # corrupts the main DB header. WAL mode reuses free pages from deleted
    # rows without compaction, so file growth stays bounded after cleanup.


# Initialize schema on module load when diagnostics are enabled.
# If initialization fails (e.g., filesystem/ACL restrictions), fail open by
# disabling diagnostics for this process to prevent repeated noisy warnings.
if DIAGNOSTICS_ENABLED:
    try:
        _init_schema()
        _maybe_cleanup_importer_diagnostics()
    except Exception as e:
        DIAGNOSTICS_ENABLED = False
        if DIAGNOSTICS_DEBUG:
            _logger.info(f"[DIAG] Failed to initialize database: {e}")


# =============================================================================
# BUFFERED LOGGER INSTANCES (lazy initialization)
# =============================================================================

_buffered_loggers: dict[str, BufferedLogger] = {}


def _get_buffered_logger(log_type: str) -> BufferedLogger | None:
    """Get buffered logger instance for a log type."""
    if not BUFFERED_LOGGER_AVAILABLE:
        return None

    if log_type not in _buffered_loggers:
        if log_type == "hooks":
            _buffered_loggers[log_type] = get_hook_invocation_logger()
        elif log_type == "tools":
            _buffered_loggers[log_type] = get_tool_call_logger()
        elif log_type == "context":
            _buffered_loggers[log_type] = get_context_logger()

    return _buffered_loggers.get(log_type)


# =============================================================================
# CORE LOGGING
# =============================================================================


def _truncate(content: Any, max_len: int = MAX_CONTENT_LENGTH) -> str:
    """Truncate content for logging, preserving start and end."""
    s = str(content)
    if len(s) <= max_len:
        return s
    half = (max_len - 50) // 2
    return f"{s[:half]}\n\n[...TRUNCATED {len(s) - max_len} chars...]\n\n{s[-half:]}"


def _get_session_id() -> str:
    """Get or create session ID for correlation."""
    session_file = LOG_DIR / ".current_session"
    try:
        if session_file.exists():
            return session_file.read_text().strip()
    except:
        pass

    # Generate new session ID
    session_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    try:
        session_file.write_text(session_id)
    except:
        pass
    return session_id


def _required_text(value: Any, fallback: str) -> str:
    """Ensure NOT NULL text columns are always populated."""
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def log_entry(log_type: str, data: dict) -> None:
    """
    Write a log entry to the appropriate SQLite table.

    Args:
        log_type: One of 'context', 'hooks', 'tools', 'assumptions', 'errors'
        data: Dictionary of data to log
    """
    if not DIAGNOSTICS_ENABLED:
        return

    # Map log_type to table name
    table_map = {
        "context": "context",
        "hooks": "hooks",
        "tools": "tools",
        "assumptions": "assumptions",
        "errors": "errors",
    }

    table = table_map.get(log_type)
    if not table:
        return

    # Get terminal_id for multi-terminal traceability
    terminal_id = (
        str(
            data.get("terminal_id")
            or data.get("terminalId")
            or data.get("CLAUDE_TERMINAL_ID")
            or (detect_terminal_id() if TERMINAL_DETECTION_AVAILABLE else "unknown")
        )
    )
    session_id = str(
        data.get("session_id")
        or data.get("sessionId")
        or data.get("CLAUDE_SESSION_ID")
        or _get_session_id()
    )
    timestamp = datetime.now(UTC).isoformat()

    try:
        conn = _get_connection()
        cursor = conn.cursor()

        if log_type == "context":
            cursor.execute("""
                INSERT INTO context (
                    timestamp, session_id, terminal_id, event, prompt_preview,
                    prompt_length, prompt_hash, claude_md_present, injected_content,
                    injected_total_tokens, conversation_length, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, session_id, terminal_id,
                _required_text(data.get("event"), "unknown"),
                data.get("prompt_preview"),
                data.get("prompt_length"),
                data.get("prompt_hash"),
                1 if data.get("claude_md_present") else 0,
                json.dumps(data.get("injected_content", [])),
                data.get("injected_total_tokens"),
                data.get("conversation_length"),
                json.dumps(data.get("metadata", {}))
            ))

        elif log_type == "hooks":
            cursor.execute("""
                INSERT INTO hooks (
                    timestamp, session_id, terminal_id, turn_id, event, hook_name, event_type,
                    action, injection_preview, injection_length, reason, duration_ms,
                    execution_time_ms, timeout_ms, output_size_bytes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, session_id, terminal_id, data.get("turn_id"),
                _required_text(data.get("event"), "hook_event"),
                _required_text(data.get("hook_name"), "unknown_hook"),
                _required_text(data.get("event_type"), "unknown_event_type"),
                _required_text(data.get("action"), "unknown_action"),
                data.get("injection_preview"),
                data.get("injection_length"),
                data.get("reason"),
                data.get("duration_ms"),
                data.get("execution_time_ms"),
                data.get("timeout_ms"),
                data.get("output_size_bytes")
            ))

        elif log_type == "tools":
            cursor.execute("""
                INSERT INTO tools (
                    timestamp, session_id, terminal_id, event, tool_name, tool_input,
                    tool_output_preview, tool_output_length, success, error_type,
                    error_message, duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, session_id, terminal_id,
                _required_text(data.get("event"), "tool_event"),
                _required_text(data.get("tool_name"), "unknown_tool"),
                json.dumps(data.get("tool_input")),
                data.get("tool_output_preview"),
                data.get("tool_output_length"),
                1 if data.get("success", True) else 0,
                data.get("error_type"),
                data.get("error_message"),
                data.get("duration_ms")
            ))

        elif log_type == "assumptions":
            cursor.execute("""
                INSERT INTO assumptions (
                    timestamp, session_id, terminal_id, event, assumption_type,
                    assumption, source, verified, verification_result
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, session_id, terminal_id,
                _required_text(data.get("event"), "assumption_event"),
                _required_text(data.get("assumption_type"), "unknown_assumption_type"),
                _required_text(data.get("assumption"), "unknown_assumption"),
                _required_text(data.get("source"), "unknown_source"),
                1 if data.get("verified", False) else 0,
                data.get("verification_result")
            ))

        elif log_type == "errors":
            cursor.execute("""
                INSERT INTO errors (
                    timestamp, session_id, terminal_id, event, error_type,
                    error_message, context, stack_trace, user_prompt_preview,
                    user_prompt_hash, claude_session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, session_id, terminal_id,
                _required_text(data.get("event"), "error_event"),
                _required_text(data.get("error_type"), "unknown_error_type"),
                _required_text(data.get("error_message"), "unknown_error"),
                json.dumps(data.get("context")),
                data.get("stack_trace"),
                data.get("user_prompt_preview"),
                data.get("user_prompt_hash"),
                data.get("claude_session_id")
            ))

        conn.commit()

    except Exception as e:
        # Fail silently - logging should never break the hook
        _logger.info(f"[DIAG] Log write failed: {e}")


# =============================================================================
# SPECIALIZED LOGGERS
# =============================================================================


def log_context(
    prompt: str,
    claude_md_present: bool,
    injected_content: list[str],
    conversation_length: int,
    metadata: dict | None = None,
) -> None:
    """Log what context CC receives at prompt time."""
    log_entry(
        "context",
        {
            "event": "prompt_received",
            "prompt_preview": _truncate(prompt, 500),
            "prompt_length": len(prompt),
            "prompt_hash": hashlib.md5(prompt.encode()).hexdigest()[:8],
            "claude_md_present": claude_md_present,
            "injected_content": injected_content,
            "injected_total_tokens": sum(len(c.split()) for c in injected_content),
            "conversation_length": conversation_length,
            "metadata": metadata or {},
        },
    )


def log_hook_invocation(
    hook_name: str,
    event_type: str,
    action: str,  # 'pass', 'inject', 'warn', 'block'
    injection_content: str | None = None,
    reason: str | None = None,
    duration_ms: float | None = None,
    execution_time_ms: float | None = None,
    timeout_ms: int | None = None,
    output_size_bytes: int | None = None,
    turn_id: str | None = None,
    session_id: str | None = None,
    terminal_id: str | None = None,
) -> None:
    """Log when a hook fires and what it does."""
    log_entry(
        "hooks",
        {
            "session_id": session_id,
            "terminal_id": terminal_id,
            "turn_id": turn_id,
            "event": "hook_invoked",
            "hook_name": hook_name,
            "event_type": event_type,
            "action": action,
            "injection_preview": (
                _truncate(injection_content, 300) if injection_content else None
            ),
            "injection_length": len(injection_content) if injection_content else 0,
            "reason": reason,
            "duration_ms": duration_ms,
            "execution_time_ms": execution_time_ms,
            "timeout_ms": timeout_ms,
            "output_size_bytes": output_size_bytes,
        },
    )


def log_tool_call(
    tool_name: str,
    tool_input: dict,
    tool_output: str | None = None,
    success: bool = True,
    error_type: str | None = None,
    error_message: str | None = None,
    duration_ms: float | None = None,
) -> None:
    """Log full tool call with input and output."""
    log_entry(
        "tools",
        {
            "event": "tool_call",
            "tool_name": tool_name,
            "tool_input": (
                {k: _truncate(v, 1000) for k, v in tool_input.items()}
                if isinstance(tool_input, dict)
                else _truncate(tool_input, 1000)
            ),
            "tool_output_preview": (
                _truncate(tool_output, 1000) if tool_output else None
            ),
            "tool_output_length": len(tool_output) if tool_output else 0,
            "success": success,
            "error_type": error_type,
            "error_message": error_message,
            "duration_ms": duration_ms,
        },
    )


def log_assumption(
    assumption_type: str,
    assumption: str,
    source: str,  # What led to this assumption
    verified: bool = False,
    verification_result: str | None = None,
) -> None:
    """Log detected assumptions CC makes before verification."""
    log_entry(
        "assumptions",
        {
            "event": "assumption_detected",
            "assumption_type": assumption_type,
            "assumption": assumption,
            "source": source,
            "verified": verified,
            "verification_result": verification_result,
        },
    )


def log_error(
    error_type: str,
    error_message: str,
    context: dict | None = None,
    stack_trace: str | None = None,
    user_prompt: str | None = None,
    claude_session_id: str | None = None,
) -> None:
    """Log errors for debugging with optional user prompt for traceability.

    Args:
        error_type: Category of error (e.g., 'hook_error', 'parse_error')
        error_message: Human-readable error description
        context: Additional context dict (hook name, tool name, etc.)
        stack_trace: Python traceback if available
        user_prompt: The user prompt that triggered the error (for traceability)
        claude_session_id: Claude Code's session_id from hook input (different from our file-based session_id)
    """
    # Derive structured classification fields from error_type + context
    hook_name = (context or {}).get("hook", "")
    error_class, failure_code, is_startup_actionable, root_cause_key = (
        _error_class_and_code(hook_name, error_type, error_message, stack_trace or "")
    )

    log_entry(
        "errors",
        {
            "event": "error",
            "error_type": error_type,
            "error_message": error_message,
            # Structured classification (A3)
            "error_class": error_class,
            "failure_code": failure_code,
            "is_startup_actionable": is_startup_actionable,
            "root_cause_key": root_cause_key,
            "context": context,
            "stack_trace": stack_trace,
            "user_prompt_preview": _truncate(user_prompt, 200) if user_prompt else None,
            "user_prompt_hash": (
                hashlib.md5(user_prompt.encode()).hexdigest()[:8]
                if user_prompt
                else None
            ),
            "claude_session_id": claude_session_id,  # Claude Code's actual session ID from hook input
        },
    )


def _error_class_and_code(
    hook_name: str, error_type: str, error_message: str, tb: str,
) -> tuple[str, str, bool, str]:
    """Derive structured classification fields from error type + context.

    Maps error_type -> (error_class, failure_code, is_startup_actionable, root_cause_key).

    Mapping rules (A3):
      timeout_imminent/killed/terminated/exceeded -> ("timeout", code, False, key)
        Rationale: operational noise; timeout means hook ran but took too long — not a bug.
      syntax_error/parse_error -> ("load_failure", code, False, key)
        Rationale: known fixed; syntax errors from previous edits are not current failures.
      import_error/module_not_found -> ("load_failure", code, True, key)
        Rationale: actionable; missing dependencies are real problems requiring user action.
      runtime_error with known traceback patterns (name 'anomalies', name 'user_prompt',
        AttributeError.*unknown, AttributeError.*audit_report) -> ("known_fixed", code, False, key)
        Rationale: known fixed; these are refactoring artifacts already addressed.
      runtime_error generic -> ("runtime_error", code, True, key)
        Rationale: actionable; genuine unexpected errors need investigation.
      unknown error_type -> ("runtime_error", code, True, key)
        Rationale: fail-open; unclassified errors default to actionable to avoid silencing real bugs.

    The four output fields feed the startup health classifier (A4):
      error_class: coarse bucket for routing in Layer 1 of _classify_error_events.
      failure_code: stable identifier; used as root_cause_key for telemetry grouping.
      is_startup_actionable: True = real failure to count; False = suppress from alert.
      root_cause_key: stable key for grouping; mirrors failure_code.
    """
    failure_code = f"{hook_name}_{error_type}"
    root_cause_key = failure_code

    if error_type in ("timeout_imminent", "timeout_killed", "timeout_terminated", "timeout_exceeded"):
        return "timeout", failure_code, False, root_cause_key
    if error_type in ("syntax_error", "parse_error"):
        return "load_failure", failure_code, False, root_cause_key
    if error_type in ("import_error", "module_not_found"):
        return "load_failure", failure_code, True, root_cause_key
    if error_type == "runtime_error":
        msg_lower = error_message.lower()
        tb_lower = (tb or "").lower()
        combined = f"{msg_lower}|{tb_lower}"
        if any(k in combined for k in ("name 'anomalies'", "name 'user_prompt'",
                                        "attributeerror.*unknown", "attributeerror.*audit_report")):
            return "known_fixed", failure_code, False, root_cause_key
        return "runtime_error", failure_code, True, root_cause_key
    return "runtime_error", failure_code, True, root_cause_key


def log_importer_anomaly(
    hook_name: str,
    phase: str,
    error_text: str,
    session_id: str | None = None,
    terminal_id: str | None = None,
    tool_name: str | None = None,
    input_hash: str | None = None,
    input_bytes: int | None = None,
    traceback_text: str | None = None,
) -> bool:
    """Log importer-specific anomalies to SQLite."""
    if not DIAGNOSTICS_ENABLED:
        return False

    try:
        conn = _get_connection()
        conn.execute(
            """
            INSERT INTO importer_diagnostics (
                timestamp, hook_name, phase, session_id, terminal_id,
                tool_name, input_hash, input_bytes, error_text, traceback
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(UTC).isoformat(),
                _required_text(hook_name, "unknown_hook"),
                _required_text(phase, "unknown_phase"),
                session_id,
                terminal_id,
                tool_name,
                input_hash,
                input_bytes,
                _required_text(error_text, "unknown_importer_error"),
                traceback_text,
            ),
        )
        conn.commit()
        return True
    except Exception:
        return False


# =============================================================================
# PATTERN DETECTORS
# =============================================================================

# Patterns that indicate CC is making assumptions
ASSUMPTION_PATTERNS = [
    # Path assumptions
    (
        r"C:\\Users\\[^\\]+\\\.config\\",
        "path_assumption",
        "Using .config path without verification",
    ),
    (
        r"C:\\Users\\[^\\]+\\AppData\\",
        "path_assumption",
        "Using AppData path without verification",
    ),
    (r"~\/\.", "path_assumption", "Using home directory path without verification"),
    # Database assumptions
    (r"sqlite3.*\.db", "db_assumption", "Accessing database without verifying path"),
    (r"SELECT.*FROM", "db_assumption", "Running SQL query"),
    # State assumptions
    (r"should (now |be )", "state_assumption", "Assuming state without verification"),
    (r"(is|are) (now |already )", "state_assumption", "Claiming current state"),
    # Success assumptions
    (r"(fixed|resolved|working|completed)", "success_assumption", "Claiming success"),
]


def detect_assumptions(text: str) -> list[dict]:
    """Detect potential assumptions in text."""
    import re

    found = []
    for pattern, assumption_type, description in ASSUMPTION_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            found.append(
                {
                    "type": assumption_type,
                    "matched": match.group(),
                    "description": description,
                    "position": match.start(),
                }
            )
    return found


# =============================================================================
# ANALYSIS UTILITIES
# =============================================================================


def get_recent_logs(log_type: str, n: int = 20) -> list[dict]:
    """Get the N most recent log entries of a type."""
    table_map = {
        "context": "context",
        "hooks": "hooks",
        "tools": "tools",
        "assumptions": "assumptions",
        "errors": "errors",
    }

    table = table_map.get(log_type)
    if not table:
        return []

    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM {table}
            ORDER BY timestamp DESC
            LIMIT ?
        """, (n,))

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        results = []
        for row in rows:
            entry = dict(zip(columns, row))
            # Convert JSON strings back to objects
            for key, value in entry.items():
                if key.endswith("_preview") or key in ["injected_content", "metadata", "tool_input", "context"]:
                    if value:
                        try:
                            entry[key] = json.loads(value)
                        except:
                            pass  # Keep as string if not valid JSON
                # Convert integers back to bool for boolean fields
                if key.endswith("_present") or key in ["verified", "success"]:
                    if isinstance(value, int):
                        entry[key] = bool(value)
            results.append(entry)

        return results
    except Exception as e:
        _logger.info(f"[DIAG] Failed to get recent logs: {e}")
        return []


def query_hook_invocations(
    days: int = 7,
    turn_id: str | None = None,
    session_id: str | None = None,
    terminal_id: str | None = None,
    actions: list[str] | None = None,
    limit: int = 50,
) -> list[dict]:
    """Query hook invocation rows from the diagnostics database."""
    if not DIAGNOSTICS_ENABLED:
        return []

    cutoff = datetime.now(UTC) - timedelta(days=days)
    clauses = ["timestamp >= ?"]
    params: list[Any] = [cutoff.isoformat()]

    if turn_id:
        clauses.append("turn_id = ?")
        params.append(turn_id)
    if session_id:
        clauses.append("session_id = ?")
        params.append(session_id)
    if terminal_id:
        clauses.append("terminal_id = ?")
        params.append(terminal_id)
    if actions:
        placeholders = ",".join("?" for _ in actions)
        clauses.append(f"action IN ({placeholders})")
        params.extend(actions)

    params.append(limit)
    query = f"""
        SELECT *
        FROM hooks
        WHERE {" AND ".join(clauses)}
        ORDER BY timestamp DESC
        LIMIT ?
    """

    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        _logger.info(f"[DIAG] Failed to query hook invocations: {e}")
        return []


def get_session_summary(session_id: str | None = None) -> dict:
    """Get summary of activity for a session."""
    session_id = session_id or _get_session_id()

    summary = {
        "session_id": session_id,
        "context_events": 0,
        "hook_invocations": 0,
        "tool_calls": 0,
        "assumptions_detected": 0,
        "errors": 0,
        "hooks_triggered": set(),
        "tools_used": set(),
    }

    try:
        conn = _get_connection()
        cursor = conn.cursor()

        # Count events per table
        cursor.execute("SELECT COUNT(*) FROM context WHERE session_id = ?", (session_id,))
        summary["context_events"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM hooks WHERE session_id = ?", (session_id,))
        summary["hook_invocations"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tools WHERE session_id = ?", (session_id,))
        summary["tool_calls"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM assumptions WHERE session_id = ?", (session_id,))
        summary["assumptions_detected"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM errors WHERE session_id = ?", (session_id,))
        summary["errors"] = cursor.fetchone()[0]

        # Get unique hooks and tools
        cursor.execute("SELECT DISTINCT hook_name FROM hooks WHERE session_id = ?", (session_id,))
        summary["hooks_triggered"] = {row[0] for row in cursor.fetchall()}

        cursor.execute("SELECT DISTINCT tool_name FROM tools WHERE session_id = ?", (session_id,))
        summary["tools_used"] = {row[0] for row in cursor.fetchall()}

    except Exception as e:
        _logger.info(f"[DIAG] Failed to get session summary: {e}")

    # Convert sets to lists for JSON serialization
    summary["hooks_triggered"] = list(summary["hooks_triggered"])
    summary["tools_used"] = list(summary["tools_used"])

    return summary


# =============================================================================
# CLI
# =============================================================================


def main():
    """CLI for viewing diagnostic logs."""
    import argparse

    parser = argparse.ArgumentParser(description="CC Diagnostic Log Viewer")
    parser.add_argument("command", choices=["recent", "summary", "clear", "status"])
    parser.add_argument("--type", "-t", choices=["context", "hooks", "tools", "assumptions", "errors"], default="tools")
    parser.add_argument("--count", "-n", type=int, default=10)
    parser.add_argument("--session", "-s", help="Session ID to filter")

    args = parser.parse_args()

    if args.command == "recent":
        entries = get_recent_logs(args.type, args.count)
        for entry in entries:
            print(json.dumps(entry, indent=2, default=str))
            print("-" * 40)

    elif args.command == "summary":
        summary = get_session_summary(args.session)
        print(json.dumps(summary, indent=2, default=str))

    elif args.command == "clear":
        conn = _get_connection()
        cursor = conn.cursor()
        for table in ["context", "hooks", "tools", "assumptions", "errors"]:
            cursor.execute(f"DELETE FROM {table}")
            print(f"Cleared: {table}")
        conn.commit()

    elif args.command == "status":
        print(f"Diagnostics enabled: {DIAGNOSTICS_ENABLED}")
        print(f"Database: {DB_PATH}")

        conn = _get_connection()
        cursor = conn.cursor()

        tables = ["context", "hooks", "tools", "assumptions", "errors"]
        print("Table row counts:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} rows")


# =============================================================================
# SIMPLE LOG API (hook_logger compatibility layer)
# =============================================================================


def log(hook: str, event: str, data: dict = None):
    """
    Drop-in replacement for hook_logger.log().

    Maintains compatibility with existing hook code while using
    the more robust cc_diagnostic_logger infrastructure.

    Usage:
        from cc_diagnostic_logger import log
        log("my_hook", "event_type", {"key": "value"})

    Args:
        hook: Hook name (e.g., "error_attribution_validator")
        event: Event type (e.g., "commitment_injected", "blocked")
        data: Optional additional data to log
    """
    log_entry("hooks", {"event": event, "hook_name": hook, **(data or {})})


if __name__ == "__main__":
    main()
