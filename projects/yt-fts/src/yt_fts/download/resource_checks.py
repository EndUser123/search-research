"""
Resource checks for batch-download to prevent critical failures.

This module provides functions to check system resources before and during
batch processing to prevent:
- OOM kills (memory pressure)
- Silent data corruption (disk full)
- Connection pool exhaustion
"""

import logging
import shutil
import socket

logger = logging.getLogger(__name__)

# Constants
MIN_DISK_GB = 10.0  # Minimum 10GB free disk space
MIN_MEMORY_PCT = 20.0  # Minimum 20% free memory
MIN_MEMORY_MB = 1024  # Minimum 1GB absolute memory


def check_disk_space(path: str = None) -> tuple[bool, str, float]:
    """
    Check available disk space before processing.
    
    Args:
        path: Path to check (default: current directory or database path)
    
    Returns:
        Tuple of (is_ok, message, free_gb)
    """
    try:
        if path is None:
            # Use current directory
            path = "."

        stat = shutil.disk_usage(path)
        free_gb = stat.free / (1024**3)  # Convert to GB

        if free_gb < MIN_DISK_GB:
            return False, f"Insufficient disk space: {free_gb:.1f}GB free (minimum {MIN_DISK_GB}GB)", free_gb

        logger.debug("Disk space check passed: %.1fGB free", free_gb)
        return True, f"Disk space OK: {free_gb:.1f}GB free", free_gb

    except Exception as e:
        logger.warning("Failed to check disk space: %s", e)
        # Fail open - allow proceeding but log warning
        return True, f"Disk space check failed: {e}", 0.0


def check_memory() -> tuple[bool, str, float]:
    """
    Check available memory to prevent OOM kills.
    
    Returns:
        Tuple of (is_ok, message, free_pct)
    """
    try:
        import psutil
        mem = psutil.virtual_memory()

        # Calculate free memory percentage
        free_pct = (mem.available / mem.total) * 100 if mem.total > 0 else 0

        # Also check absolute minimum
        free_mb = mem.available / (1024**2)

        if free_pct < MIN_MEMORY_PCT and free_mb < MIN_MEMORY_MB:
            return False, f"Low memory: {free_pct:.1f}% free ({free_mb:.0f}MB)", free_pct

        logger.debug("Memory check passed: %.1f%% free", free_pct)
        return True, f"Memory OK: {free_pct:.1f}% free", free_pct

    except ImportError:
        # psutil not available - skip check but log
        logger.warning("psutil not available - skipping memory check")
        return True, "Memory check skipped (psutil unavailable)", 100.0
    except Exception as e:
        logger.warning("Failed to check memory: %s", e)
        return True, f"Memory check failed: {e}", 100.0


def check_database_integrity(db_path: str) -> tuple[bool, str]:
    """
    Check database integrity before batch processing.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Tuple of (is_ok, message)
    """
    try:
        import sqlite3

        # Fast startup check:
        # - integrity_check is extremely expensive on large DBs and can look like a hang.
        # - quick_check(1) gives a lightweight corruption signal suitable for pre-flight.
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()

        # Ensure schema is readable and database opens cleanly.
        cursor.execute("SELECT name FROM sqlite_master LIMIT 1")
        cursor.fetchone()

        # Run PRAGMA quick_check with a small row limit for speed.
        cursor.execute("PRAGMA quick_check(1)")
        quick_result = cursor.fetchone()

        conn.close()

        if quick_result and quick_result[0] != "ok":
            return False, f"Database quick check failed: {quick_result[0]}"

        logger.debug("Database pre-flight check passed")
        return True, "Database quick check OK"

    except Exception as e:
        return False, f"Database integrity check failed: {e}"


def classify_network_error(error: Exception) -> str:
    """
    Classify network errors for better handling.
    
    Args:
        error: Exception object
        
    Returns:
        Error type string: 'dns', 'timeout', 'connection_refused', 'ssl_error', 'unknown'
    """
    error_str = str(error).lower()
    error_type = type(error).__name__

    # DNS failures
    if isinstance(error, socket.gaierror):
        return "dns"
    if "getaddrinfo failed" in error_str or "name resolution" in error_str:
        return "dns"

    # Timeouts
    if "timed out" in error_str or "timeout" in error_type.lower():
        return "timeout"

    # Connection refused
    if "connection refused" in error_str or "econnrefused" in error_str:
        return "connection_refused"

    # SSL/TLS errors
    if "ssl" in error_str or "tls" in error_str or "certificate" in error_str:
        return "ssl_error"

    # Network unreachable
    if "network is unreachable" in error_str or "enetworkunreachable" in error_str:
        return "network_unreachable"

    return "unknown"


def classify_http_error(status_code: int, error_msg: str = "") -> str:
    """
    Classify HTTP errors for appropriate handling.
    
    Args:
        status_code: HTTP status code
        error_msg: Error message (optional)
        
    Returns:
        Classification: 'rate_limit', 'forbidden', 'not_found', 'server_error', 'unknown'
    """
    if status_code == 429:
        return "rate_limit"
    if status_code == 403:
        return "forbidden"
    if status_code == 404:
        return "not_found"
    if 500 <= status_code < 600:
        return "server_error"
    if status_code == 400:
        return "bad_request"
    return "unknown"


def get_pre_flight_summary(checks: dict) -> str:
    """
    Generate a summary of pre-flight checks.
    
    Args:
        checks: Dictionary of check results
        
    Returns:
        Formatted summary string
    """
    lines = ["Pre-flight Checks:", "=" * 50]

    for check_name, result in checks.items():
        if not isinstance(result, tuple) or len(result) < 2:
            passed, message = False, f"Invalid check result format: {result!r}"
        else:
            passed, message = bool(result[0]), result[1]
        status = "✓" if passed else "✗"
        lines.append(f"{status} {check_name:25s}: {message}")

    return "\\n".join(lines)


# Main pre-flight check function
def run_pre_flight_checks(db_path: str, skip_memory_check: bool = False) -> tuple[bool, str]:
    """
    Run all pre-flight checks before batch processing.
    
    Args:
        db_path: Path to SQLite database
        skip_memory_check: Skip memory check (if psutil unavailable)
        
    Returns:
        Tuple of (all_passed, summary_message)
    """
    checks = {}

    # 1. Disk space check
    checks["Disk Space"] = check_disk_space()

    # 2. Memory check (optional)
    if not skip_memory_check:
        checks["Memory"] = check_memory()
    else:
        checks["Memory"] = (True, "Skipped (psutil unavailable)")

    # 3. Database integrity
    checks["Database Integrity"] = check_database_integrity(db_path)

    # Check overall status
    all_passed = all(
        bool(result[0]) if isinstance(result, tuple) and len(result) >= 1 else False
        for result in checks.values()
    )
    summary = get_pre_flight_summary(checks)

    return all_passed, summary
