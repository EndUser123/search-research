#!/usr/bin/env python3
"""
SessionStart Memory CKS Auto-Ingestion
====================================

Automatically re-ingests memory files into CKS if they've been modified
since the last ingestion. Runs once per session during SessionStart.

Logic:
1. Track last ingestion timestamp in state file
2. On session start, check if any memory file is newer
3. If yes, run ingestion script in background
4. Update timestamp

This ensures CKS always has the latest memory content without manual re-ingestion.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Paths
HOOKS_DIR = Path(__file__).resolve().parent
MEMORY_DIR = Path("C:/Users/brsth/.claude/projects/P--/memory")
STATE_DIR = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))
STATE_FILE = STATE_DIR / "memory_cks_timestamp.json"
LOCK_FILE = STATE_DIR / "memory_cks_ingest.lock"
INGEST_SCRIPT = HOOKS_DIR / "scripts" / "ingest_memory_to_cks.py"

# Configuration
LOCK_TIMEOUT = timedelta(minutes=5)  # Stale locks older than this are cleaned up
SKIP_FILES = {"MEMORY.md"}

# Environment variable to disable auto-ingestion
AUTO_INGEST_ENABLED = os.environ.get("MEMORY_CKS_AUTO_INGEST", "true").lower() in ("1", "true", "yes", "on")


def acquire_lock() -> bool:
    """Attempt to acquire ingestion lock.

    Returns:
        True if lock acquired (this terminal should ingest),
        False if another terminal is ingesting
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    current_pid = os.getpid()
    current_time = datetime.now(UTC)

    # Try to read existing lock
    if LOCK_FILE.exists():
        try:
            with open(LOCK_FILE) as f:
                lock_data = json.load(f)

            lock_pid = lock_data.get("pid")
            lock_time_str = lock_data.get("timestamp")

            if lock_pid and lock_time_str:
                try:
                    lock_time = datetime.fromisoformat(lock_time_str)

                    # Check if lock is stale
                    if current_time - lock_time > LOCK_TIMEOUT:
                        # Lock is stale, take over
                        with open(LOCK_FILE, "w") as f:
                            json.dump({
                                "pid": current_pid,
                                "timestamp": current_time.isoformat()
                            }, f)
                        return True

                    # Lock is fresh and belongs to another process
                    # Check if that PID is actually running
                    if lock_pid != current_pid:
                        if sys.platform == "win32":
                            # Windows: use tasklist to check if PID exists
                            result = subprocess.run(
                                ["tasklist", "/FI", f"PID eq {lock_pid}"],
                                capture_output=True,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
                            if str(lock_pid) in result.stdout.decode():
                                # Process is still running, don't acquire lock
                                return False
                        else:
                            # Unix: use os.kill with signal 0 to check
                            try:
                                os.kill(lock_pid, 0)
                                return False  # Process exists, don't acquire lock
                            except OSError:
                                pass  # Process doesn't exist, we can take the lock

                except (ValueError, OSError):
                    pass  # Invalid lock data, treat as unlocked

        except (OSError, json.JSONDecodeError):
            pass  # Can't read lock, treat as unlocked

    # Write our lock
    try:
        with open(LOCK_FILE, "w") as f:
            json.dump({
                "pid": current_pid,
                "timestamp": current_time.isoformat()
            }, f)
        return True
    except OSError:
        return False


def release_lock() -> None:
    """Release the ingestion lock."""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except OSError:
        pass  # Non-critical


def get_last_ingestion_timestamp() -> float | None:
    """Get timestamp of last memory ingestion from state file."""
    if not STATE_FILE.exists():
        return None

    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
        return data.get("last_ingestion_timestamp")
    except (OSError, json.JSONDecodeError):
        return None


def save_ingestion_timestamp(timestamp: float) -> None:
    """Save ingestion timestamp to state file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"last_ingestion_timestamp": timestamp}, f)
    except OSError:
        pass  # Non-critical


def get_memory_files() -> list[Path]:
    """Get list of memory files to track."""
    if not MEMORY_DIR.exists():
        return []

    return [
        f for f in MEMORY_DIR.glob("*.md")
        if f.name not in SKIP_FILES
    ]


def check_files_need_ingestion(last_timestamp: float | None) -> bool:
    """Check if any memory file is newer than last ingestion."""
    if last_timestamp is None:
        return True  # First run

    memory_files = get_memory_files()
    if not memory_files:
        return False

    # Check if any file is newer
    for filepath in memory_files:
        try:
            mtime = filepath.stat().st_mtime
            if mtime > last_timestamp:
                return True
        except OSError:
            continue

    return False


def run_ingestion() -> bool:
    """Run the memory ingestion script."""
    if not INGEST_SCRIPT.exists():
        return False

    try:
        # Run ingestion script (timeout 60 seconds)
        result = subprocess.run(
            [sys.executable, str(INGEST_SCRIPT)],
            capture_output=True,
            timeout=60.0,
            cwd=str(INGEST_SCRIPT.parent)
        )

        # Log result (non-blocking)
        if result.returncode == 0:
            print(f"✅ Memory CKS auto-ingestion: {result.stdout.decode(errors='ignore').strip()}", file=sys.stdout)
        else:
            print(f"⚠️  Memory CKS auto-ingestion failed: {result.stderr.decode(errors='ignore')[:200]}", file=sys.stdout)

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⚠️  Memory CKS auto-ingestion timed out", file=sys.stdout)
        return False
    except Exception:
        return False


def main():
    """SessionStart hook entry point."""
    if not AUTO_INGEST_ENABLED:
        return

    # Quick check: do we need to ingest?
    last_timestamp = get_last_ingestion_timestamp()

    if not check_files_need_ingestion(last_timestamp):
        return  # No changes detected

    # Try to acquire lock (multi-terminal safety)
    if not acquire_lock():
        # Another terminal is ingesting, skip gracefully
        return

    try:
        # Run ingestion (already has its own stdout for status)
        success = run_ingestion()

        if success:
            # Update timestamp
            save_ingestion_timestamp(datetime.now(UTC).timestamp())
    finally:
        # Always release lock, even if ingestion fails
        release_lock()


if __name__ == "__main__":
    main()
