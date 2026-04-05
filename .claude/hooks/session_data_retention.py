#!/usr/bin/env python3
"""
session_data_retention.py - Unified stale data cleanup
======================================================

Multi-terminal safe housekeeping for all hook data directories.
Uses an atomic lock file to ensure only one terminal runs cleanup
at a time. Other terminals skip cleanup if it ran recently.

Called from SessionStart.py at boot (before sub-hooks).

Data categories and retention policies:
- Lock files:         5 min stale threshold
- State files:        48h for verification, 5min for error attribution
- Session data:       3 days for decision logs, 1 day for spool
- Logs (append-only): Truncated to MAX_LOG_BYTES
- SQLite DBs:         VACUUM when > size threshold
- Diagnostics:        startup_probe.log truncated, old jsonl pruned

Design: All operations use try/except per-file so one bad file
never blocks cleanup of others.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────
HOOKS_DIR = Path(__file__).resolve().parent
SESSION_DATA = HOOKS_DIR / "session_data"
STATE_DIR = HOOKS_DIR / ".state"
STATE_DIR_ALT = HOOKS_DIR / "state"
LOGS_DIR = HOOKS_DIR / "logs"
DIAG_DIR = LOGS_DIR / "diagnostics"
LOCK_DIR = Path("P:/.claude/.locks")

# Import state path utilities for per-terminal state management (TASK-005)
try:
    from __lib.state_paths import (
        SESSIONS_DIR,
        SHARED_DIR,
        TERMINALS_DIR,
    )
    from __lib.state_paths import (
        STATE_DIR as STATE_DIR_NEW,
    )
except ImportError:
    # Fallback for development
    TERMINALS_DIR = None
    SESSIONS_DIR = None
    SHARED_DIR = None
    STATE_DIR_NEW = None

# ── Coordination ───────────────────────────────────────────────
CLEANUP_LOCK = HOOKS_DIR / "session_data" / ".cleanup_lock.json"
CLEANUP_COOLDOWN_SECS = 300  # Skip if cleanup ran < 5 min ago

# ── Retention policies ─────────────────────────────────────────
MAX_AGE_DAYS = 3
MAX_AGE_SECS = MAX_AGE_DAYS * 86400
MAX_LOG_BYTES = 512 * 1024       # 512KB per log file
MAX_DB_BYTES = 10 * 1024 * 1024  # 10MB triggers VACUUM + prune
STALE_LOCK_SECS = 300            # 5 min
STALE_STATE_HOURS = 48
STALE_TASK_HOURS = 72            # 3 days for task_* state files


def _try_acquire_cleanup_lock() -> bool:
    """Acquire cleanup lock atomically. Returns True if we got it."""
    now = time.time()

    # Check if cleanup ran recently
    if CLEANUP_LOCK.exists():
        try:
            data = json.loads(CLEANUP_LOCK.read_text(encoding="utf-8"))
            last_run = data.get("last_cleanup", 0)
            if now - last_run < CLEANUP_COOLDOWN_SECS:
                return False  # Too recent, skip
        except (json.JSONDecodeError, OSError):
            pass  # Corrupt lock, we'll overwrite

    # Atomic create via O_CREAT | O_EXCL
    tmp = CLEANUP_LOCK.with_suffix(".tmp")
    try:
        tmp.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(tmp), os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"last_cleanup": now, "pid": os.getpid()}, f)
        # Atomic rename
        tmp.replace(CLEANUP_LOCK)
        return True
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        return False


def _release_cleanup_lock() -> None:
    """Update lock with completion timestamp (don't delete - it's the cooldown marker)."""
    try:
        CLEANUP_LOCK.write_text(
            json.dumps({"last_cleanup": time.time(), "pid": os.getpid()}),
            encoding="utf-8",
        )
    except OSError:
        pass


# ── Cleanup functions ──────────────────────────────────────────

def _cleanup_stale_locks(stats: dict) -> None:
    """Remove stale .lock files everywhere."""
    now = time.time()

    # Session data locks
    for lock in SESSION_DATA.rglob("*.lock"):
        if lock == CLEANUP_LOCK:
            continue
        try:
            if now - lock.stat().st_mtime > STALE_LOCK_SECS:
                lock.unlink(missing_ok=True)
                stats["locks"] += 1
        except OSError:
            pass

    # Global lock directories
    if LOCK_DIR.exists():
        for session_dir in LOCK_DIR.glob("session_*"):
            if not session_dir.is_dir():
                continue
            has_files = False
            for lock in session_dir.glob("*.lock"):
                has_files = True
                try:
                    if now - lock.stat().st_mtime > STALE_LOCK_SECS:
                        # TASK-023 FIX: Retry loop with exponential backoff for TOCTOU race
                        # Problem: Multiple terminals can check stale, then both try to delete
                        # Solution: Retry on FileNotFoundError/PermissionError (concurrent access)
                        max_retries = 4
                        base_delay_ms = 100

                        for attempt in range(max_retries):
                            try:
                                lock.unlink(missing_ok=True)
                                stats["locks"] += 1
                                break  # Success, exit retry loop
                            except (FileNotFoundError, PermissionError):
                                # TOCTOU race detected - retry with exponential backoff
                                if attempt < max_retries - 1:
                                    delay_ms = base_delay_ms * (2 ** attempt)
                                    time.sleep(delay_ms / 1000.0)
                                else:
                                    # Last attempt failed, continue gracefully
                                    pass
                            except OSError:
                                # Other errors - don't retry
                                break
                except OSError:
                    pass
            # Remove empty session dirs
            if not has_files:
                try:
                    session_dir.rmdir()
                except OSError:
                    pass

    # Log dir locks
    for lock in LOGS_DIR.rglob("*.lock"):
        try:
            if now - lock.stat().st_mtime > STALE_LOCK_SECS:
                # TASK-023 FIX: Retry loop with exponential backoff for TOCTOU race
                # Problem: Multiple terminals can check stale, then both try to delete
                # Solution: Retry on FileNotFoundError/PermissionError (concurrent access)
                max_retries = 4
                base_delay_ms = 100

                for attempt in range(max_retries):
                    try:
                        lock.unlink(missing_ok=True)
                        stats["locks"] += 1
                        break  # Success, exit retry loop
                    except (FileNotFoundError, PermissionError):
                        # TOCTOU race detected - retry with exponential backoff
                        if attempt < max_retries - 1:
                            delay_ms = base_delay_ms * (2 ** attempt)
                            time.sleep(delay_ms / 1000.0)
                        else:
                            # Last attempt failed, continue gracefully
                            pass
                    except OSError:
                        # Other errors - don't retry
                        break
        except OSError:
            pass


def _cleanup_state_files(stats: dict) -> None:
    """Remove stale state files from .state/ and state/ directories."""
    now = time.time()

    # .state/ - verification state files (48h)
    if STATE_DIR.exists():
        threshold = STALE_STATE_HOURS * 3600
        for f in STATE_DIR.glob("verification_state_*.json"):
            try:
                if now - f.stat().st_mtime > threshold:
                    f.unlink(missing_ok=True)
                    stats["state_files"] += 1
            except OSError:
                pass
        # SessionStart marker files (48h)
        for f in STATE_DIR.glob("sessionstart_*.json"):
            try:
                if now - f.stat().st_mtime > threshold:
                    f.unlink(missing_ok=True)
                    stats["state_files"] += 1
            except OSError:
                pass

        # Cache subdirectories: prune files older than 48h
        for cache_dir_name in ["guidance-cache", "tdd-state", "task-identity"]:
            cache_dir = STATE_DIR / cache_dir_name
            if not cache_dir.exists():
                continue
            for f in cache_dir.rglob("*"):
                if not f.is_file():
                    continue
                try:
                    if now - f.stat().st_mtime > threshold:
                        f.unlink(missing_ok=True)
                        stats["state_files"] += 1
                except OSError:
                    pass
            # Remove empty subdirectories
            for d in sorted(cache_dir.rglob("*"), reverse=True):
                if d.is_dir():
                    try:
                        d.rmdir()  # Only succeeds if empty
                    except OSError:
                        pass

    # state/ - task files, error attribution, contract caches
    if STATE_DIR_ALT.exists():
        task_threshold = STALE_TASK_HOURS * 3600

        # Cache subdirectories: prune files older than 72h
        for cache_dir_name in ["contracts", "embeddings", "v_stage", "v_state"]:
            cache_dir = STATE_DIR_ALT / cache_dir_name
            if not cache_dir.exists():
                continue
            for f in cache_dir.rglob("*"):
                if not f.is_file():
                    continue
                try:
                    if now - f.stat().st_mtime > task_threshold:
                        f.unlink(missing_ok=True)
                        stats["state_files"] += 1
                except OSError:
                    pass
            for d in sorted(cache_dir.rglob("*"), reverse=True):
                if d.is_dir():
                    try:
                        d.rmdir()
                    except OSError:
                        pass

        for f in STATE_DIR_ALT.iterdir():
            if not f.is_file():
                continue
            try:
                age = now - f.stat().st_mtime
                name = f.name.lower()

                # Error attribution: 5 min
                if name.startswith("error_attribution_") and age > STALE_LOCK_SECS:
                    # Check expires_at field if JSON
                    try:
                        data = json.loads(f.read_text(encoding="utf-8"))
                        expires = data.get("expires_at", 0)
                        if expires and now > expires:
                            f.unlink(missing_ok=True)
                            stats["state_files"] += 1
                            continue
                    except (json.JSONDecodeError, OSError):
                        pass
                    if age > STALE_LOCK_SECS:
                        f.unlink(missing_ok=True)
                        stats["state_files"] += 1

                # Task state files: 72h
                elif name.startswith("task_") and age > task_threshold:
                    f.unlink(missing_ok=True)
                    stats["state_files"] += 1

                # Pending files: 24h
                elif name.startswith("pending_") and age > 86400:
                    f.unlink(missing_ok=True)
                    stats["state_files"] += 1

                # V-stage progress: 48h
                elif name.startswith("v-stage-progress") and age > STALE_STATE_HOURS * 3600:
                    f.unlink(missing_ok=True)
                    stats["state_files"] += 1

                # Catch-all for unknown state files: 7 days
                elif age > 7 * 86400:
                    f.unlink(missing_ok=True)
                    stats["state_files"] += 1

            except OSError:
                pass


def _cleanup_session_data(stats: dict) -> None:
    """Clean session_data/ directory."""
    now = time.time()

    if not SESSION_DATA.exists():
        return

    # Decision logs: keep last MAX_AGE_DAYS
    for log in SESSION_DATA.glob("hook_decisions_*.jsonl"):
        try:
            if now - log.stat().st_mtime > MAX_AGE_SECS:
                log.unlink(missing_ok=True)
                stats["decision_logs"] += 1
        except OSError:
            pass

    # Evidence spool: 24h
    spool = SESSION_DATA / "evidence_spool"
    if spool.exists():
        for f in spool.iterdir():
            try:
                if now - f.stat().st_mtime > 86400:
                    f.unlink(missing_ok=True)
                    stats["spool_files"] += 1
            except OSError:
                pass

    # Active command files: 24h (orphaned from crashed sessions)
    for f in SESSION_DATA.glob("active_command_*.json"):
        try:
            if now - f.stat().st_mtime > 86400:
                f.unlink(missing_ok=True)
                stats["session_data"] += 1
        except OSError:
            pass

    # Hook development session markers: 24h (orphaned sessions)
    for f in SESSION_DATA.glob("hook_dev_session_*.json"):
        try:
            if now - f.stat().st_mtime > 86400:
                f.unlink(missing_ok=True)
                stats["session_data"] += 1
        except OSError:
            pass

    # Large append-only JSONL files: truncate
    for name in [
        "enforcement_events.jsonl",
        "stop_router_debug.jsonl",
    ]:
        p = SESSION_DATA / name
        if p.exists():
            try:
                if p.stat().st_size > MAX_LOG_BYTES:
                    _truncate_jsonl(p, MAX_LOG_BYTES)
                    stats["truncated"] += 1
            except OSError:
                pass

    # Large JSON state files: reset if old
    for name in [
        "stop_churn_metrics.json",
        "stop_evidence_tokens.json",
        "stop_observation_receipts.json",
    ]:
        p = SESSION_DATA / name
        if p.exists():
            try:
                if p.stat().st_size > MAX_LOG_BYTES and now - p.stat().st_mtime > 86400:
                    p.write_text("{}", encoding="utf-8")
                    stats["session_data"] += 1
            except OSError:
                pass


def _cleanup_logs(stats: dict) -> None:
    """Truncate oversized log files, prune old entries."""
    if not LOGS_DIR.exists():
        return

    # Truncate large append-only logs
    for logfile in LOGS_DIR.glob("*.jsonl"):
        try:
            if logfile.stat().st_size > MAX_LOG_BYTES:
                _truncate_jsonl(logfile, MAX_LOG_BYTES)
                stats["truncated"] += 1
        except OSError:
            pass

    for logfile in LOGS_DIR.glob("*.log"):
        try:
            if logfile.stat().st_size > MAX_LOG_BYTES:
                _truncate_text(logfile, MAX_LOG_BYTES)
                stats["truncated"] += 1
        except OSError:
            pass

    # Diagnostics subdirectory
    if DIAG_DIR.exists():
        for logfile in DIAG_DIR.glob("*.jsonl"):
            try:
                if logfile.stat().st_size > MAX_LOG_BYTES:
                    _truncate_jsonl(logfile, MAX_LOG_BYTES)
                    stats["truncated"] += 1
            except OSError:
                pass

        for logfile in DIAG_DIR.glob("*.log"):
            try:
                if logfile.stat().st_size > MAX_LOG_BYTES:
                    _truncate_text(logfile, MAX_LOG_BYTES)
                    stats["truncated"] += 1
            except OSError:
                pass

    # BUC state: keep only 3 most recent
    buc_dir = LOGS_DIR / "buc_state"
    if buc_dir.exists():
        files = sorted(buc_dir.glob("session_*.json"), key=lambda f: f.stat().st_mtime)
        for f in files[:-3]:  # Keep 3 newest
            try:
                f.unlink(missing_ok=True)
                stats["log_files"] += 1
            except OSError:
                pass

    # CKS integration: keep only 5 most recent
    cks_dir = LOGS_DIR / "cks_integration"
    if cks_dir.exists():
        files = sorted(cks_dir.glob("*.json"), key=lambda f: f.stat().st_mtime)
        for f in files[:-5]:  # Keep 5 newest
            try:
                f.unlink(missing_ok=True)
                stats["log_files"] += 1
            except OSError:
                pass


def _cleanup_databases(stats: dict) -> None:
    """VACUUM SQLite databases that exceed size threshold."""
    db_paths = [
        SESSION_DATA / "evidence.db",
        DIAG_DIR / "diagnostics.db",
    ]
    for db_path in db_paths:
        if not db_path.exists():
            continue
        try:
            size = db_path.stat().st_size
            if size <= MAX_DB_BYTES:
                continue

            # Try to connect and prune old rows, then VACUUM
            conn = sqlite3.connect(str(db_path), timeout=2.0)
            try:
                # Delete rows older than MAX_AGE_DAYS
                cutoff = time.time() - MAX_AGE_SECS
                # Try common timestamp column names
                for table in _get_tables(conn):
                    for col in ["timestamp", "created_at", "ts", "time"]:
                        try:
                            conn.execute(
                                f"DELETE FROM [{table}] WHERE [{col}] < ?",
                                (cutoff,),
                            )
                            conn.commit()
                            break
                        except sqlite3.OperationalError:
                            continue

                conn.execute("VACUUM")
                conn.commit()
                stats["db_vacuumed"] += 1
            finally:
                conn.close()
        except (sqlite3.Error, OSError):
            pass


def _get_tables(conn: sqlite3.Connection) -> list[str]:
    """List user tables in SQLite database."""
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        return [r[0] for r in rows]
    except sqlite3.Error:
        return []


# ── Truncation helpers ─────────────────────────────────────────

def _truncate_jsonl(path: Path, max_bytes: int) -> None:
    """Keep only the last max_bytes of a JSONL file (line-aligned)."""
    try:
        size = path.stat().st_size
        if size <= max_bytes:
            return

        with open(path, "rb") as f:
            f.seek(size - max_bytes)
            tail = f.read()

        # Find first complete line
        newline_pos = tail.find(b"\n")
        if newline_pos >= 0:
            tail = tail[newline_pos + 1:]

        # Atomic write
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(tail)
        tmp.replace(path)
    except OSError:
        pass


def _truncate_text(path: Path, max_bytes: int) -> None:
    """Keep only the last max_bytes of a text file (line-aligned)."""
    _truncate_jsonl(path, max_bytes)  # Same logic works


def _cleanup_per_terminal_state(stats: dict) -> None:
    """Clean up per-terminal state directories (TASK-005).

    Cleans the new state directory structure:
    - state/terminals/{terminal_id}/ - 48h retention
    - state/sessions/{session_id}/ - 24h retention
    - state/shared/ - 7 days retention

    Maintains backward compatibility with legacy paths during transition.
    """
    now = time.time()

    # Skip if state_paths utilities not available
    if not STATE_DIR_NEW or not TERMINALS_DIR or not SESSIONS_DIR or not SHARED_DIR:
        return

    # Clean terminal-scoped state (48h)
    if TERMINALS_DIR.exists():
        terminal_threshold = 48 * 3600  # 48 hours
        for terminal_dir in TERMINALS_DIR.iterdir():
            if not terminal_dir.is_dir():
                continue
            try:
                # Check terminal directory age
                dir_age = now - terminal_dir.stat().st_mtime
                if dir_age > terminal_threshold:
                    # Terminal is stale, clean up all files in it
                    for f in terminal_dir.rglob("*"):
                        if not f.is_file():
                            continue
                        try:
                            f.unlink(missing_ok=True)
                            stats["state_files"] += 1
                        except OSError:
                            pass
                    # Try to remove empty terminal directory
                    try:
                        terminal_dir.rmdir()
                    except OSError:
                        pass
            except OSError:
                pass

    # Clean session-scoped state (24h)
    if SESSIONS_DIR.exists():
        session_threshold = 24 * 3600  # 24 hours
        for session_dir in SESSIONS_DIR.iterdir():
            if not session_dir.is_dir():
                continue
            try:
                # Check session directory age
                dir_age = now - session_dir.stat().st_mtime
                if dir_age > session_threshold:
                    # Session is stale, clean up all files in it
                    for f in session_dir.rglob("*"):
                        if not f.is_file():
                            continue
                        try:
                            f.unlink(missing_ok=True)
                            stats["state_files"] += 1
                        except OSError:
                            pass
                    # Try to remove empty session directory
                    try:
                        session_dir.rmdir()
                    except OSError:
                        pass
            except OSError:
                pass

    # Clean shared state (7 days)
    if SHARED_DIR.exists():
        shared_threshold = 7 * 86400  # 7 days
        for f in SHARED_DIR.rglob("*"):
            if not f.is_file():
                continue
            try:
                if now - f.stat().st_mtime > shared_threshold:
                    f.unlink(missing_ok=True)
                    stats["state_files"] += 1
            except OSError:
                pass


# ── Public API ─────────────────────────────────────────────────

def cleanup(force: bool = False) -> dict[str, int]:
    """Run all cleanup tasks. Returns counts of items cleaned.

    Args:
        force: Skip cooldown check (for manual/CLI invocation)
    """
    if not force and not _try_acquire_cleanup_lock():
        return {}  # Another terminal ran cleanup recently

    stats: dict[str, int] = {
        "locks": 0,
        "state_files": 0,
        "decision_logs": 0,
        "spool_files": 0,
        "session_data": 0,
        "truncated": 0,
        "log_files": 0,
        "db_vacuumed": 0,
    }

    try:
        _cleanup_stale_locks(stats)
        _cleanup_state_files(stats)
        _cleanup_per_terminal_state(stats)  # TASK-005: Clean new per-terminal state
        _cleanup_session_data(stats)
        _cleanup_logs(stats)
        _cleanup_databases(stats)
    finally:
        _release_cleanup_lock()

    return stats


if __name__ == "__main__":
    import sys

    force = "--force" in sys.argv
    result = cleanup(force=force)
    total = sum(result.values())
    if total:
        print(f"Retention cleanup: {result}")
        print(f"Total items processed: {total}")
    else:
        if not force:
            print("Skipped (ran recently or nothing to clean)")
        else:
            print("Nothing to clean")
