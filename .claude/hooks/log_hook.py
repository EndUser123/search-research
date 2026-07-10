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
import logging as _li

_HOOKS_DIR = Path(__file__).resolve().parent
_LOG_DIR = _HOOKS_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)



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


def _is_pid_alive(pid: int) -> bool:
    """Check if a process is still running (Windows)."""
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x100000, False, pid)  # SYNCHRONIZE
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    except Exception:
        return True  # Assume alive if check fails

def get_lock(lock_file: Path) -> Path | None:
    """Atomic lock via O_EXCL — cross-platform with stale lock recovery.

    Uses os.open() with O_CREAT|O_EXCL for atomic lock file creation.
    O_EXCL fails if the file already exists (EEXIST on POSIX, ERROR_FILE_EXISTS on Windows).
    If the lock is held by a dead process, removes the stale lock and retries.
    Returns the lock file path on success, None on exhaustion.
    """
    max_attempts = 5  # Reduced from 50 — stale locks are handled explicitly
    for attempt in range(max_attempts):
        fd = None
        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return lock_file
        except FileExistsError:
            if fd is not None:
                os.close(fd)
            # Check if the lock holder is still alive
            try:
                pid_str = lock_file.read_text().strip()
                if pid_str.isdigit() and not _is_pid_alive(int(pid_str)):
                    lock_file.unlink(missing_ok=True)  # Remove stale lock
                    continue  # Retry immediately
            except OSError:
                pass
            if attempt < max_attempts - 1:
                time.sleep(0.1 * (attempt + 1))
        except OSError:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if attempt < max_attempts - 1:
                time.sleep(0.1 * (attempt + 1))
    return None


def release_lock(lock_path: Path | None) -> None:
    """Release lock by removing the lock file."""
    if lock_path and lock_path.exists():
        try:
            lock_path.unlink()
        except OSError as e:
            _logger.warning(f"WARNING: lock release failed: {lock_path}: {e}")


def _append_log(entry: dict, log_path: Path) -> None:
    """Append a JSON entry to a log file with retry on lock."""
    def _write():
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    _retry_on_locked(_write)


def _append_log_batch(entries: list, log_path: Path) -> None:
    """Append many JSON entries in one open/write/close.

    Replaces the prior per-line _append_log loop, which opened the file (and
    contended the OS file lock) once per transcript line — 50k opens on a
    lost-offset run, the actual cause of the 10s wall that blew the 5s timeout.
    """
    if not entries:
        return
    blob = "".join(json.dumps(e) + "\n" for e in entries)
    def _write():
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(blob)
    _retry_on_locked(_write)


def _atomic_write_text(path: Path, data: str) -> None:
    """Persist a small state file atomically: write sibling tmp, os.replace.

    The byte-offset design hinges on transcript.offset surviving between runs.
    A bare write_text silently loses the offset on a single WinError 32 sharing
    violation (concurrent terminals), which resets the next run to a full
    transcript re-read. tmp+replace + retry makes that loss vanishingly rare;
    the _MAX_EMIT_LINES guard below contains the damage if it ever does.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    def _write():
        tmp.write_text(data, encoding="utf-8")
        os.replace(tmp, path)
    try:
        _retry_on_locked(_write)
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass


# ponytail: ceiling on per-run TRANSCRIPT_ITEM emit. Normal fires add <50 lines;
# a lost offset re-reads the whole file (tens of thousands of lines). Capping emit
# at 5000 turns the lost-offset cliff into a sub-second recovery (read + count +
# single TRUNCATED marker + advance offset) instead of a 10s re-dump.
_MAX_EMIT_LINES = 5000


# ponytail: 512MB is a generous cap for a personal append log; raise it only
# if you actually consult deep history. The file grew to 435GB unbounded.
_MAX_LOG_BYTES = 512 * 1024 * 1024  # 512 MB


def _enforce_size_cap(log_jsonl: Path, max_bytes: int = _MAX_LOG_BYTES) -> bool:
    """Delete the log if it exceeds max_bytes. Returns True if truncated.

    Truncate (not rotate) so we free disk instead of keeping a second giant
    copy. Do NOT touch the transcript diff baseline (claude-log.transcript.jsonl):
    resetting it makes the very next run re-dump the entire transcript, which
    re-inflates the file — the opposite of capping it.

    ponytail: best-effort. Concurrent terminals may race the unlink, or another
    process may hold the file open (Windows sharing violation). Both raise
    OSError, caught here; the cap re-applies on the next invocation.
    """
    try:
        if log_jsonl.exists() and log_jsonl.stat().st_size > max_bytes:
            log_jsonl.unlink()
            return True
    except OSError as e:
        _logger.warning(f"WARNING: log size-cap check failed: {e}")
    return False


def main() -> int:
    # Determine paths
    home = Path.home()
    log_jsonl = home / "claude-log.jsonl"
    transcript_offset_file = home / "claude-log.transcript.offset"
    transcript_path_file = home / "claude-log.transcript_path.txt"

    _enforce_size_cap(log_jsonl)

    # Lock file - use temp dir (works on Windows)
    tmp_dir = Path(os.environ.get("TMPDIR", os.environ.get("TEMP", str(Path.home() / "AppData" / "Local" / "Temp"))))
    if not tmp_dir.is_dir() or not os.access(tmp_dir, os.W_OK):
        _logger.warning(f"WARNING: TMPDIR not writable: {tmp_dir}")
    lock_file = tmp_dir / "claude-log.lock"
    lock_path = None
    lock_acquired = False

    try:
        lock_path = get_lock(lock_file)
        if lock_path is None:
            _logger.warning("WARNING: could not acquire lock — proceeding without synchronization")
        else:
            lock_acquired = True
    except Exception as e:
        _logger.warning(f"WARNING: lock error: {e}")

    try:
        # Read stdin
        stdin_text = sys.stdin.read()
        stdin_data = json.loads(stdin_text)

        # Telemetry: count dispatcher firings (best-effort; never breaks the hook).
        try:
            from __lib.hook_stats import record
            record(f"log_hook:{stdin_data.get('hook_event_name', 'unknown')}", "fire")
        except Exception:
            pass

        log_timestamp = int(time.time())
        log_date = datetime.now().strftime("%a %b %d %H:%M:%S %Y")

        # Extract and validate transcript_path
        transcript_path_str = stdin_data.get("transcript_path", "")
        transcript_path = None
        if transcript_path_str:
            tp = Path(transcript_path_str)
            if _is_windows_reserved_path(tp):
                _logger.warning(f"WARNING: transcript_path is a Windows reserved name, skipping diff")
            elif not tp.exists():
                _logger.warning(f"WARNING: transcript_path does not exist: {tp}")
            else:
                transcript_path = tp

        # Check if transcript file is new/changed
        prev_transcript_path = None
        if transcript_path_file.exists():
            prev_transcript_path = transcript_path_file.read_text().strip()

        transcript_changed = transcript_path_str != prev_transcript_path

        # TRANSCRIPT_RENEW - new transcript file
        if transcript_changed:
            _append_log(
                {"logEvent": "TRANSCRIPT_RENEW", "logTimestamp": log_timestamp, "logDate": log_date},
                log_jsonl,
            )

        # Save current transcript path
        if transcript_path_str:
            _atomic_write_text(transcript_path_file, transcript_path_str)

        # Incremental tail read via byte offset — O(new bytes) per run instead of
        # O(transcript size). The offset lands on a line boundary because we store
        # the prior EOF and JSONL grows by appending whole lines; splitlines on the
        # tail therefore yields only complete new lines. On compaction (file
        # shrinks/rewrites) we reset to 0 once and re-emit RENEW.
        # ponytail: drops TRANSCRIPT_PRUNE removal-count — detecting removals needs
        # a full-file compare, which is the O(total) step this eliminates, and the
        # count was noisy under compaction anyway.
        # Fail-closed: the offset is a read-modify-write cursor shared across every
        # hook firing. Running it without the cross-process lock races a sibling
        # firing reading the same offset and emitting duplicate TRANSCRIPT_ITEMs
        # (corrupts the CHS ingestion stream). If get_lock() failed open, skip the
        # whole block — emit nothing and do NOT advance the offset — so the next
        # locked run re-reads this same delta and emits it exactly once. The HOOK
        # event below is a unique per-firing append and stays unconditional.
        if lock_acquired and transcript_path and transcript_path.exists():
            size = transcript_path.stat().st_size

            offset = 0
            if transcript_changed:
                offset = 0  # new session: ingest the (small) new transcript from start
            elif transcript_offset_file.exists():
                try:
                    offset = int(transcript_offset_file.read_text(encoding="utf-8").strip() or "0")
                except (ValueError, OSError):
                    offset = 0
            else:
                # First run after install/upgrade: skip the backlog rather than
                # one-time dump the whole history. claude-log.jsonl is an event
                # stream, not a store; the transcript file remains source-of-truth.
                offset = size

            if size < offset:  # compaction rewrote a smaller file
                offset = 0
                _append_log(
                    {"logEvent": "TRANSCRIPT_RENEW", "logTimestamp": log_timestamp, "logDate": log_date},
                    log_jsonl,
                )

            if size > offset:
                with open(transcript_path, "rb") as f:
                    f.seek(offset)
                    tail = f.read()
                lines = tail.decode("utf-8", errors="replace").splitlines()

                if len(lines) > _MAX_EMIT_LINES:
                    # Lost-offset recovery: re-reading tens of thousands of lines
                    # and re-emitting each one is what re-inflated claude-log.jsonl
                    # and blew the hook timeout. Advance the offset and emit a
                    # single marker; the transcript file remains source-of-truth.
                    _append_log(
                        {
                            "logEvent": "TRANSCRIPT_TRUNCATED",
                            "logTimestamp": log_timestamp,
                            "logDate": log_date,
                            "lineCount": len(lines),
                        },
                        log_jsonl,
                    )
                else:
                    entries = []
                    for line in lines:
                        if not line.strip():
                            continue
                        try:
                            item = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        entry = {
                            "logEvent": "TRANSCRIPT_ITEM",
                            "logTimestamp": log_timestamp,
                            "logDate": log_date,
                        }
                        entry.update(item)
                        entries.append(entry)
                    _append_log_batch(entries, log_jsonl)

            # Always advance the offset so the next run is incremental — even
            # when we skipped per-line emit above. Atomic + retried so a single
            # sharing violation can't silently reset the next run to a full read.
            _atomic_write_text(transcript_offset_file, str(size))

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
        _logger.warning(f"WARNING: failed to parse stdin as JSON: {e}")
    except LockRetryExhausted as e:
        # ponytail: best-effort logger — never surface as a hook error.
        # Returning non-zero here spammed "non-blocking status code: No stderr
        # output" on every one of the 5 wired events.
        _logger.error(f"ERROR: lock retry exhausted after {e.attempts} attempts: {e.last_error}")
    except Exception as e:
        _logger.error(f"ERROR in log-hook.py: {e}")
    finally:
        release_lock(lock_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
