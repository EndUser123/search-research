#!/usr/bin/env python3
"""
Python port of log-hook.sh for claude-log.

Appends hook events and transcript diffs to ~/claude-log.jsonl.
Works on Windows without requiring jq or bash.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime


# Windows reserved names that cannot be used as file or directory names
RESERVED_NAMES = frozenset({
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
})


def _is_windows_reserved_path(path: Path) -> bool:
    """Check if any component of a path is a Windows reserved name."""
    for part in path.parts:
        if part.upper() in RESERVED_NAMES:
            return True
    return False


class LockRetryExhausted(Exception):
    """Raised when file lock retry is exhausted.

    Attributes:
        attempts: Number of attempts made
        last_error: The last exception that was raised
    """

    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"Lock retry exhausted after {attempts} attempts: {last_error}")


def _retry_on_locked(func, *args, max_attempts: int = 5, **kwargs):
    """Retry a file operation when the file is locked (WinError 32).

    Windows file locking is advisory — a retry after a short sleep
    often succeeds once the holding process yields its handle.
    """
    if max_attempts < 1:
        raise ValueError(f"max_attempts must be >= 1, got {max_attempts}")

    last_err = None
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except (PermissionError, OSError) as e:
            last_err = e
            # On Windows, WinError 32 may appear as OSError with winerror=32
            is_lock_error = (
                isinstance(e, PermissionError)
                or (hasattr(e, "winerror") and e.winerror == 32)
            )
            if is_lock_error and attempt < max_attempts - 1:
                time.sleep(0.25 * (attempt + 1))
            elif is_lock_error:
                raise LockRetryExhausted(max_attempts, last_err)
            else:
                raise  # Non-lock error, propagate immediately
    # Should not reach here if max_attempts >= 1
    raise LockRetryExhausted(max_attempts, last_err) if last_err else ValueError("max_attempts must be >= 1")


def get_lock(lock_file: Path) -> Path | None:
    """Atomic lock via O_EXCL — cross-platform.

    Uses os.open() with O_CREAT|O_EXCL for atomic lock file creation.
    O_EXCL fails if the file already exists (EEXIST on POSIX, ERROR_FILE_EXISTS on Windows).
    Returns the lock file path on success, None on exhaustion.
    """
    max_attempts = 50
    for attempt in range(max_attempts):
        fd = None
        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            return lock_file
        except FileExistsError:
            if fd is not None:
                os.close(fd)
            if attempt < max_attempts - 1:
                time.sleep(0.2 * (attempt + 1))
        except OSError:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if attempt < max_attempts - 1:
                time.sleep(0.2 * (attempt + 1))
    return None


def release_lock(lock_path: Path | None) -> None:
    """Release lock by removing the lock file."""
    if lock_path and lock_path.exists():
        try:
            lock_path.unlink()
        except OSError as e:
            print(f"WARNING: lock release failed: {lock_path}: {e}", file=sys.stderr)


def _append_log(entry: dict, log_path: Path) -> None:
    """Append a JSON entry to a log file with retry on lock."""
    def _write():
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    _retry_on_locked(_write)


def main() -> int:
    # Determine paths
    home = Path.home()
    log_jsonl = home / "claude-log.jsonl"
    transcript_copy = home / "claude-log.transcript.jsonl"
    transcript_path_file = home / "claude-log.transcript_path.txt"

    # Lock file - use temp dir (works on Windows)
    tmp_dir = Path(os.environ.get("TMPDIR", os.environ.get("TEMP", str(Path.home() / "AppData" / "Local" / "Temp"))))
    if not tmp_dir.is_dir() or not os.access(tmp_dir, os.W_OK):
        print(f"WARNING: TMPDIR not writable: {tmp_dir}", file=sys.stderr)
    lock_file = tmp_dir / "claude-log.lock"
    lock_path = None
    lock_acquired = False

    try:
        lock_path = get_lock(lock_file)
        if lock_path is None:
            print("WARNING: could not acquire lock — proceeding without synchronization", file=sys.stderr)
        else:
            lock_acquired = True
    except Exception as e:
        print(f"WARNING: lock error: {e}", file=sys.stderr)

    try:
        # Read stdin
        stdin_text = sys.stdin.read()
        stdin_data = json.loads(stdin_text)

        log_timestamp = int(time.time())
        log_date = datetime.now().strftime("%a %b %d %H:%M:%S %Y")

        # Extract and validate transcript_path
        transcript_path_str = stdin_data.get("transcript_path", "")
        transcript_path = None
        if transcript_path_str:
            tp = Path(transcript_path_str)
            if _is_windows_reserved_path(tp):
                print(f"WARNING: transcript_path is a Windows reserved name, skipping diff", file=sys.stderr)
            elif not tp.exists():
                print(f"WARNING: transcript_path does not exist: {tp}", file=sys.stderr)
            else:
                transcript_path = tp

        # Check if transcript file is new/changed
        prev_transcript_path = None
        if transcript_path_file.exists():
            prev_transcript_path = transcript_path_file.read_text().strip()

        # TRANSCRIPT_RENEW - new transcript file
        if transcript_path_str != prev_transcript_path:
            entry = {
                "logEvent": "TRANSCRIPT_RENEW",
                "logTimestamp": log_timestamp,
                "logDate": log_date,
            }
            _append_log(entry, log_jsonl)
            # Reset transcript copy
            if transcript_copy.exists():
                _retry_on_locked(transcript_copy.unlink)

        # Ensure transcript copy exists
        if not transcript_copy.exists():
            _retry_on_locked(transcript_copy.write_text, "", encoding="utf-8")

        # Save current transcript path
        if transcript_path_str:
            _retry_on_locked(transcript_path_file.write_text, transcript_path_str, encoding="utf-8")

        # Diff transcript against stored copy
        if transcript_path and transcript_path.exists():
            current_content = _retry_on_locked(transcript_path.read_text, encoding="utf-8")
            stored_content = _retry_on_locked(transcript_copy.read_text, encoding="utf-8")

            current_lines = current_content.splitlines()
            stored_lines = stored_content.splitlines()

            # Count removals
            log_removals = 0
            max_compare = min(len(stored_lines), len(current_lines))
            for i in range(max_compare):
                if stored_lines[i] != current_lines[i]:
                    log_removals += 1
            log_removals += max(0, len(stored_lines) - len(current_lines))

            if log_removals > 0:
                entry = {
                    "logEvent": "TRANSCRIPT_PRUNE",
                    "logRemovals": log_removals,
                    "logTimestamp": log_timestamp,
                    "logDate": log_date,
                }
                _append_log(entry, log_jsonl)

            # Find additions (new lines at end of current vs stored)
            additions = []
            if len(current_lines) > len(stored_lines):
                additions = current_lines[len(stored_lines):]

            for line in additions:
                if line.strip():
                    try:
                        item = json.loads(line)
                        entry = {
                            "logEvent": "TRANSCRIPT_ITEM",
                            "logTimestamp": log_timestamp,
                            "logDate": log_date,
                        }
                        entry.update(item)
                        _append_log(entry, log_jsonl)
                    except json.JSONDecodeError:
                        pass

            # Update stored copy
            _retry_on_locked(transcript_copy.write_text, current_content, encoding="utf-8")

        # HOOK event - log the full hook payload
        entry = {
            "logEvent": "HOOK",
            "logTimestamp": log_timestamp,
            "logDate": log_date,
            "lockAcquired": lock_acquired,
        }
        entry.update(stdin_data)
        _append_log(entry, log_jsonl)

    except json.JSONDecodeError as e:
        print(f"WARNING: failed to parse stdin as JSON: {e}", file=sys.stderr)
    except LockRetryExhausted as e:
        print(f"ERROR: lock retry exhausted after {e.attempts} attempts: {e.last_error}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR in log-hook.py: {e}", file=sys.stderr)
        return 1
    finally:
        release_lock(lock_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
