#!/usr/bin/env python3
"""
File Lock Manager for Multi-Session Coordination v3.0
======================================================
Provides file-level locking to prevent race conditions when multiple
Claude Code sessions operate concurrently.

Used by PreToolUse (acquire) and PostToolUse (release) hooks.

v2.0 changes:
- Atomic lock creation via os.O_CREAT | os.O_EXCL (eliminates TOCTOU race)
- Re-entrancy support (same session can re-acquire its own lock)
- Timestamp stored in lock data (not relying on file mtime)
- Better race condition handling

v3.0 changes:
- Session namespace isolation: each session uses its own lock subdirectory
- Prevents lock conflicts between concurrent Claude Code sessions
- Automatic per-session cleanup capability
"""

import atexit
import json
import os
import shutil
import time
from pathlib import Path

LOCK_DIR = Path("P:/.claude/.locks")
LOCK_TIMEOUT_SECONDS = 0.5  # Fail-fast timeout (500ms)  # Stale lock threshold

# Exported for testing
SESSION_LOCK_DIR: Path | None = None

# Track temp files for cleanup on exit
_temp_files: set[Path] = set()


def _cleanup_temp_files() -> None:
    """Clean up any orphaned .tmp files on exit.

    This function is called via atexit to ensure that any temporary
    files created during the session are cleaned up, even if the
    program crashes or is interrupted.
    """
    for temp_file in list(_temp_files):
        try:
            if temp_file.exists():
                temp_file.unlink()
                _temp_files.discard(temp_file)
        except OSError:
            pass


# Register cleanup on exit
atexit.register(_cleanup_temp_files)


def _get_session_id() -> str:
    """Get consistent session ID across hook invocations.

    Uses parent PID (Claude Code process) for consistency, falling back to
    environment variable or current PID.
    """
    # Try environment variable first (if set by Claude Code)
    if env_id := os.environ.get("CLAUDE_SESSION_ID"):
        return env_id

    # Use parent process ID (Claude Code's PID) for consistency
    # All hooks spawned by the same CC instance share parent PID
    try:
        import psutil
        parent = psutil.Process(os.getpid()).parent()
        if parent:
            return f"ppid_{parent.pid}"
    except (ImportError, Exception):
        pass

    # Fallback: use current PID (less reliable for multi-hook scenarios)
    return f"pid_{os.getpid()}"


def _get_session_lock_dir() -> Path:
    """Get the session-specific lock directory.

    Each session gets its own subdirectory under LOCK_DIR to prevent
    lock conflicts between concurrent Claude Code sessions.
    """
    global SESSION_LOCK_DIR
    if SESSION_LOCK_DIR is not None:
        return SESSION_LOCK_DIR

    session_id = _get_session_id()
    # Create session-prefixed subdirectory
    session_dir = LOCK_DIR / f"session_{session_id}"
    SESSION_LOCK_DIR = session_dir
    return session_dir


def _get_lock_path(file_path: str) -> Path:
    """Convert file path to lock file path with session namespace."""
    normalized = file_path.replace("\\", "/").replace(":", "_").replace("/", "_")
    session_dir = _get_session_lock_dir()
    return session_dir / f"{normalized}.lock"


def _read_lock_safe(lock_path: Path) -> dict | None:
    """Safely read lock file contents. Returns None if unreadable."""
    try:
        if not lock_path.exists():
            return None
        return json.loads(lock_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def acquire_lock(file_path: str) -> tuple[bool, str]:
    """
    Attempt to acquire lock for file atomically.

    Returns:
        (success: bool, message: str)
        - (True, "") if lock acquired
        - (False, "reason") if lock denied

    Features:
        - Atomic creation via O_CREAT | O_EXCL (kernel-level)
        - Re-entrancy: same session can re-acquire its own lock
        - Stale lock cleanup: locks older than TTL are removed
        - Session isolation: different sessions use different lock paths
    """
    # Create session directory on demand
    session_dir = _get_session_lock_dir()
    session_dir.mkdir(parents=True, exist_ok=True)

    lock_path = _get_lock_path(file_path)
    session_id = _get_session_id()
    now = time.time()

    # Check for existing lock first
    if lock_path.exists():
        data = _read_lock_safe(lock_path)
        if data:
            owner = data.get("session", "unknown")
            created = data.get("created", 0)
            age = now - created

            # Re-entrancy: same session already holds lock - allow
            if owner == session_id:
                return (True, "")

            # Stale lock: remove and try again
            if age > LOCK_TIMEOUT_SECONDS:
                try:
                    lock_path.unlink()
                except OSError:
                    pass
                # Fall through to acquisition attempt
            else:
                remaining = int(LOCK_TIMEOUT_SECONDS - age)
                return (False, f"Locked by {owner} ({remaining}s remaining). Retry shortly.")
        else:
            # Corrupted lock file - remove it
            try:
                lock_path.unlink()
            except OSError:
                pass

    # Atomic creation attempt using O_CREAT | O_EXCL
    # This is a single syscall that either succeeds (we got the lock)
    # or raises FileExistsError (someone else created it first)
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        lock_data = {
            "session": session_id,
            "file": file_path,
            "created": now,
            "pid": os.getpid()
        }
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(lock_data, f, indent=2)
        return (True, "")
    except FileExistsError:
        # Lost the race - another process created it between our check and create
        # Re-read to get current owner info
        data = _read_lock_safe(lock_path)
        if data:
            owner = data.get("session", "unknown")
            return (False, f"Lock contention with {owner} - retry shortly.")
        return (False, "File {file_path} is busy. Retry in a moment.")
    except OSError as e:
        return (False, f"Lock error: {e}")


def release_lock(file_path: str) -> bool:
    """
    Release lock for file if owned by this session.

    Returns:
        True if lock was released or didn't exist
        False if lock is held by another session (not applicable with session isolation)
    """
    lock_path = _get_lock_path(file_path)
    session_id = _get_session_id()

    if not lock_path.exists():
        return True  # No lock to release

    data = _read_lock_safe(lock_path)
    if not data:
        # Corrupted lock, safe to remove
        try:
            lock_path.unlink(missing_ok=True)
        except OSError:
            pass
        return True

    owner = data.get("session")
    created = data.get("created", 0)
    age = time.time() - created

    # Release if we own it OR if it's stale
    if owner == session_id or age > LOCK_TIMEOUT_SECONDS:
        try:
            lock_path.unlink(missing_ok=True)
            return True
        except OSError:
            return False

    # Not our lock and not stale - leave it alone
    return False


def check_lock(file_path: str) -> dict | None:
    """
    Check if file is locked (in this session's namespace).

    Returns:
        Lock info dict if locked (and not stale), None otherwise
    """
    lock_path = _get_lock_path(file_path)

    data = _read_lock_safe(lock_path)
    if not data:
        return None

    created = data.get("created", 0)
    age = time.time() - created

    if age > LOCK_TIMEOUT_SECONDS:
        return None  # Stale lock doesn't count

    # Add computed fields for convenience
    data["age_seconds"] = int(age)
    data["remaining_seconds"] = int(LOCK_TIMEOUT_SECONDS - age)
    return data


def cleanup_session_locks(session_id: str | None = None) -> int:
    """
    Remove all locks for a specific session (or current session).

    Args:
        session_id: Session ID to clean up. If None, uses current session.

    Returns:
        Count of locks removed.
    """
    if session_id is None:
        session_id = _get_session_id()

    session_dir = LOCK_DIR / f"session_{session_id}"

    if not session_dir.exists():
        return 0

    removed = 0

    # Remove all lock files in the session directory
    for lock_file in session_dir.glob("*.lock"):
        try:
            lock_file.unlink()
            removed += 1
        except OSError:
            pass

    # Try to remove the session directory itself if empty
    try:
        if session_dir.is_dir() and not list(session_dir.iterdir()):
            session_dir.rmdir()
    except OSError:
        pass

    return removed


def cleanup_stale_locks() -> int:
    """
    Remove all stale locks across all session directories.

    Also cleans up empty session directories.

    Call periodically or on session start.
    Returns count of removed locks.
    """
    if not LOCK_DIR.exists():
        return 0

    removed = 0
    now = time.time()
    empty_session_dirs = []

    # First, clean up stale locks in session directories
    for session_dir in LOCK_DIR.glob("session_*"):
        if not session_dir.is_dir():
            continue

        session_has_files = False

        for lock_file in session_dir.glob("*.lock"):
            session_has_files = True
            data = _read_lock_safe(lock_file)
            if data:
                created = data.get("created", 0)
                age = now - created
                if age > LOCK_TIMEOUT_SECONDS:
                    try:
                        lock_file.unlink()
                        removed += 1
                    except OSError:
                        pass
            else:
                # Corrupted lock file
                try:
                    lock_file.unlink()
                    removed += 1
                except OSError:
                    pass

        # Track empty session directories for removal
        if not session_has_files or not list(session_dir.glob("*")):
            empty_session_dirs.append(session_dir)

    # Clean up empty session directories
    for session_dir in empty_session_dirs:
        try:
            if session_dir.is_dir() and not list(session_dir.iterdir()):
                session_dir.rmdir()
        except OSError:
            pass

    # Also clean up legacy locks (direct .lock files in LOCK_DIR)
    for lock_file in LOCK_DIR.glob("*.lock"):
        data = _read_lock_safe(lock_file)
        if data:
            created = data.get("created", 0)
            age = now - created
            if age > LOCK_TIMEOUT_SECONDS:
                try:
                    lock_file.unlink()
                    removed += 1
                except OSError:
                    pass
        else:
            # Corrupted lock file
            try:
                lock_file.unlink()
                removed += 1
            except OSError:
                pass

    return removed


def atomic_write(file_path: Path | str, content: str) -> None:
    """
    Write content to file atomically using temp file + rename.

    This prevents corruption from concurrent writes by:
    1. Writing to a .tmp file in the same directory
    2. Using shutil.move() for atomic rename operation

    Args:
        file_path: Target file path (Path or str)
        content: Content to write

    Raises:
        OSError: If write or rename fails
    """
    target = Path(file_path)
    temp_path = target.with_suffix(target.suffix + ".tmp")

    try:
        # Write content to temp file
        temp_path.write_text(content, encoding="utf-8")
        # Track temp file for cleanup on exit
        _temp_files.add(temp_path)
        # Atomic rename operation
        shutil.move(str(temp_path), str(target))
        # Successfully renamed, remove from tracking
        _temp_files.discard(temp_path)
    except Exception:
        # Clean up temp file on any failure
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        # Remove from tracking set
        _temp_files.discard(temp_path)
        raise


if __name__ == "__main__":
    # CLI for testing
    import sys
    if len(sys.argv) < 2:
        print("Usage: file_lock_manager.py [acquire|release|check|cleanup|status|cleanup-session] [file_path]")
        print("\nCommands:")
        print("  acquire <path>       - Try to acquire lock")
        print("  release <path>       - Release lock if held")
        print("  check <path>         - Check lock status")
        print("  cleanup              - Remove all stale locks")
        print("  cleanup-session [id] - Remove all locks for a session")
        print("  status               - Show all active locks")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "cleanup":
        n = cleanup_stale_locks()
        print(f"Removed {n} stale locks")
    elif cmd == "cleanup-session":
        session_id = sys.argv[2] if len(sys.argv) > 2 else None
        n = cleanup_session_locks(session_id)
        if session_id:
            print(f"Removed {n} locks for session {session_id}")
        else:
            print(f"Removed {n} locks for current session")
    elif cmd == "status":
        if not LOCK_DIR.exists():
            print("No locks directory")
            sys.exit(0)

        # Show locks in session directories
        session_dirs = list(LOCK_DIR.glob("session_*"))
        legacy_locks = list(LOCK_DIR.glob("*.lock"))

        if not session_dirs and not legacy_locks:
            print("No active locks")
            sys.exit(0)

        print("Active locks:")

        for session_dir in session_dirs:
            if not session_dir.is_dir():
                continue
            session_name = session_dir.name
            session_locks = list(session_dir.glob("*.lock"))
            if session_locks:
                print(f"  {session_name}/ ({len(session_locks)} locks):")
                for lf in session_locks:
                    data = _read_lock_safe(lf)
                    if data:
                        age = int(time.time() - data.get("created", 0))
                        print(f"    {lf.name}: age={age}s")
                    else:
                        print(f"    {lf.name}: [corrupted]")

        # Show legacy locks
        if legacy_locks:
            print(f"  Legacy ({len(legacy_locks)} locks):")
            for lf in legacy_locks:
                data = _read_lock_safe(lf)
                if data:
                    age = int(time.time() - data.get("created", 0))
                    print(f"    {lf.name}: owner={data.get('session')}, age={age}s")
                else:
                    print(f"    {lf.name}: [corrupted]")

    elif len(sys.argv) < 3:
        print("File path required for this command")
        sys.exit(1)
    else:
        path = sys.argv[2]
        if cmd == "acquire":
            ok, msg = acquire_lock(path)
            print(f"{'Acquired' if ok else 'Denied'}: {msg}")
            sys.exit(0 if ok else 1)
        elif cmd == "release":
            ok = release_lock(path)
            print(f"{'Released' if ok else 'Not held by this session'}")
        elif cmd == "check":
            info = check_lock(path)
            if info:
                print(json.dumps(info, indent=2))
            else:
                print("Not locked")
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
