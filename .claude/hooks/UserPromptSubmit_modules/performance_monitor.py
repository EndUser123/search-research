"""Performance monitoring for unified detection engine.

Logs detection latency to SQLite database and alerts when thresholds exceeded.
Integrates with cc_diagnostic_logger for centralized diagnostics.
"""
from __future__ import annotations

import os
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Try to import from config_loader
try:
    from config_loader import load_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# Try to import cc_diagnostic_logger
try:
    from cc_diagnostic_logger import DIAGNOSTICS_ENABLED, _get_connection, log_entry
    CC_DIAGNOSTICS_AVAILABLE = True
except ImportError:
    CC_DIAGNOSTICS_AVAILABLE = False
    DIAGNOSTICS_ENABLED = False

# =============================================================================
# CONFIGURATION
# =============================================================================

# Default thresholds (from config if available)
DEFAULT_MAX_DETECTION_MS = 60.0
DEFAULT_MAX_TOTAL_LATENCY_MS = 100.0

# Performance monitoring database path
PERF_DB_PATH = Path(__file__).resolve().parent.parent / "logs/diagnostics/performance.db"


def get_thresholds() -> dict[str, float]:
    """Get performance thresholds from config or defaults.

    Returns:
        Dict with max_detection_ms and max_total_latency_ms
    """
    if CONFIG_AVAILABLE:
        try:
            config = load_config()
            perf_config = config.performance
            return {
                "max_detection_ms": perf_config.get("max_detection_ms", DEFAULT_MAX_DETECTION_MS),
                "max_total_latency_ms": perf_config.get("max_total_latency_ms", DEFAULT_MAX_TOTAL_LATENCY_MS),
            }
        except Exception:
            pass

    return {
        "max_detection_ms": DEFAULT_MAX_DETECTION_MS,
        "max_total_latency_ms": DEFAULT_MAX_TOTAL_LATENCY_MS,
    }


# =============================================================================
# DATABASE SETUP
# =============================================================================

_local = threading.local()


def _get_perf_connection() -> sqlite3.Connection:
    """Get thread-local performance database connection."""
    if not hasattr(_local, "perf_conn"):
        # Ensure parent directory exists
        PERF_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(
            str(PERF_DB_PATH),
            check_same_thread=False,
            timeout=5.0,
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        _local.perf_conn = conn
    return _local.perf_conn


def _init_perf_schema() -> None:
    """Initialize performance monitoring database schema."""
    conn = _get_perf_connection()

    # Detection timing table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS detection_timing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            terminal_id TEXT NOT NULL,
            prompt_length INTEGER NOT NULL,
            timing_ms REAL NOT NULL,
            matched_frameworks TEXT,
            matched_modes TEXT,
            matched_profiles TEXT,
            threshold_exceeded INTEGER NOT NULL,
            threshold_value REAL
        )
    """)

    # Create indexes for common queries
    conn.execute("CREATE INDEX IF NOT EXISTS idx_detection_timestamp ON detection_timing(timestamp DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_detection_session ON detection_timing(session_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_detection_threshold_exceeded ON detection_timing(threshold_exceeded)")

    conn.commit()


# Initialize schema on module load
try:
    _init_perf_schema()
except Exception:
    # Fail silently - performance logging should never break detection
    pass


# =============================================================================
# PERFORMANCE LOGGING
# =============================================================================

def _get_session_id() -> str:
    """Get or create session ID for correlation."""
    session_file = Path(__file__).resolve().parent.parent / "logs/diagnostics/.current_session"
    try:
        if session_file.exists():
            return session_file.read_text().strip()
    except Exception:
        pass

    # Generate new session ID
    session_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    try:
        session_file.parent.mkdir(parents=True, exist_ok=True)
        session_file.write_text(session_id)
    except Exception:
        pass
    return session_id


def _get_terminal_id() -> str:
    """Get terminal ID for multi-terminal traceability."""
    try:
        from __lib.terminal_detection import detect_terminal_id
        return detect_terminal_id()
    except Exception:
        return "unknown"


def log_detection_performance(
    prompt: str,
    result: Any,  # UnifiedDetectionResult
) -> dict[str, Any]:
    """Log detection performance metrics.

    Args:
        prompt: User prompt text
        result: UnifiedDetectionResult from detect_prompt()

    Returns:
        Dict with performance status and any warnings
    """
    if not os.environ.get("COGNITIVE_PERF_MONITORING_ENABLED", "true").lower() == "true":
        return {"logged": False, "reason": "Performance monitoring disabled"}

    try:
        session_id = _get_session_id()
        terminal_id = _get_terminal_id()
        timestamp = datetime.now(UTC).isoformat()

        # Get thresholds
        thresholds = get_thresholds()
        max_detection_ms = thresholds["max_detection_ms"]

        # Extract result data
        timing_ms = result.timing_ms
        matched_frameworks = ",".join(result.matched_frameworks) if result.matched_frameworks else None
        matched_modes = ",".join(result.matched_modes) if result.matched_modes else None
        matched_profiles = ",".join(result.matched_profiles) if result.matched_profiles else None

        # Check if threshold exceeded
        threshold_exceeded = timing_ms > max_detection_ms

        # Log to performance database
        conn = _get_perf_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO detection_timing (
                timestamp, session_id, terminal_id, prompt_length,
                timing_ms, matched_frameworks, matched_modes, matched_profiles,
                threshold_exceeded, threshold_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            session_id,
            terminal_id,
            len(prompt),
            timing_ms,
            matched_frameworks,
            matched_modes,
            matched_profiles,
            1 if threshold_exceeded else 0,
            max_detection_ms,
        ))
        conn.commit()

        # Also log to cc_diagnostic_logger if available
        if CC_DIAGNOSTICS_AVAILABLE and DIAGNOSTICS_ENABLED:
            log_entry(
                "hooks",
                {
                    "event": "detection_performance",
                    "hook_name": "unified_detection",
                    "event_type": "performance",
                    "action": "measured",
                    "duration_ms": timing_ms,
                    "reason": f"Detection took {timing_ms:.2f}ms (threshold: {max_detection_ms:.2f}ms)" if threshold_exceeded else None,
                }
            )

        # Return status
        status = {
            "logged": True,
            "timing_ms": timing_ms,
            "threshold_ms": max_detection_ms,
            "threshold_exceeded": threshold_exceeded,
        }

        if threshold_exceeded:
            status["warning"] = (
                f"Detection performance warning: {timing_ms:.2f}ms "
                f"exceeds threshold of {max_detection_ms:.2f}ms"
            )

        return status

    except Exception as e:
        # Fail silently - performance logging should never break detection
        return {
            "logged": False,
            "reason": f"Performance logging failed: {e}"
        }


# =============================================================================
# ANALYSIS UTILITIES
# =============================================================================

def get_performance_summary(limit: int = 100) -> dict[str, Any]:
    """Get performance summary from recent detections.

    Args:
        limit: Number of recent detections to analyze

    Returns:
        Dict with performance statistics
    """
    try:
        conn = _get_perf_connection()
        cursor = conn.cursor()

        # Get recent detections
        cursor.execute("""
            SELECT timing_ms, threshold_exceeded
            FROM detection_timing
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()

        if not rows:
            return {
                "count": 0,
                "mean_ms": 0,
                "min_ms": 0,
                "max_ms": 0,
                "threshold_exceeded_count": 0,
            }

        timings = [row[0] for row in rows]
        exceeded_count = sum(1 for row in rows if row[1])

        return {
            "count": len(timings),
            "mean_ms": sum(timings) / len(timings),
            "min_ms": min(timings),
            "max_ms": max(timings),
            "threshold_exceeded_count": exceeded_count,
        }

    except Exception:
        return {
            "count": 0,
            "mean_ms": 0,
            "min_ms": 0,
            "max_ms": 0,
            "threshold_exceeded_count": 0,
        }


def get_recent_slow_detections(threshold_ms: float | None = None, limit: int = 10) -> list[dict]:
    """Get recent detections that exceeded performance threshold.

    Args:
        threshold_ms: Override default threshold (None = use config)
        limit: Maximum number of results

    Returns:
        List of slow detection records
    """
    try:
        if threshold_ms is None:
            thresholds = get_thresholds()
            threshold_ms = thresholds["max_detection_ms"]

        conn = _get_perf_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, session_id, terminal_id, prompt_length,
                   timing_ms, matched_frameworks, matched_modes, matched_profiles,
                   threshold_value
            FROM detection_timing
            WHERE timing_ms > ?
            ORDER BY timing_ms DESC
            LIMIT ?
        """, (threshold_ms, limit))

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        return [dict(zip(columns, row)) for row in rows]

    except Exception:
        return []
