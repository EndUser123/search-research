"""Mutex/PID file singleton lock system for dreaming daemon (T-002).

This module provides a hybrid mutex system combining:
- Primary: Windows mutex via CreateMutexW (reliable singleton enforcement)
- Secondary: PID file for process tracking and stale detection

The Windows mutex is the authoritative mechanism for singleton enforcement.
The PID file provides process tracking and stale mutex detection.

Key Design:
- Mutex acquisition creates system-wide singleton
- PID file stores current PID for stale detection
- On crash: OS releases mutex automatically (no zombie risk)
- Stale mutex detection: PID mismatch = crashed daemon, acquire new mutex

Functions:
- acquire_singleton(pid_file, state_file, force, mutex_name) -> (bool, str): Acquire both locks
- release_singleton(pid_file) -> None: Release both locks
- is_instance_running(pid_file) -> bool: Check if instance is running

Backward Compatibility:
The mutex_name parameter maintains backward compatibility with a default value
of "Global\\ClaudeInsightDaemon". Existing code calling acquire_singleton()
without specifying mutex_name will continue to work as before.
"""

import ctypes
import json
import os
import tempfile
from pathlib import Path
from typing import Tuple

# Import state management for canonical PID preservation
from dreaming_state import load_state

# Windows constants
ERROR_ALREADY_EXISTS = 183

# Module-level state to track locks
_pid_file_path = None
_mutex_handle = None


def acquire_singleton(pid_file: str, state_file: str | None = None, force: bool = False, mutex_name: str = "Global\\ClaudeInsightDaemon") -> Tuple[bool, str]:
    """Acquire singleton lock using Windows mutex (primary) and PID file (secondary).

    Args:
        pid_file: Path to PID file (e.g., "dreaming-daemon.pid")
        state_file: Path to state file for canonical PID storage (optional, uses default if not provided)
        force: If True, skip running process check (for zombie cleanup)
        mutex_name: Windows mutex name (default: "Global\\ClaudeInsightDaemon" for dreaming daemon)

    Returns:
        Tuple[bool, str]: (success, error_msg) where success is True/False and
            error_msg contains details if acquisition failed

    Lock Acquisition Strategy:
    1. Check if PID file exists with running process (skip if force=True)
    2. Try to create Windows mutex (non-blocking, fail immediately if exists)
    3. If mutex exists and PID matches running process -> fail (instance running)
    4. If mutex exists but PID doesn't match -> stale mutex, acquire new
    5. Write current PID to file and preserve canonical PID

    Note:
        The mutex_name parameter allows multiple daemon types to coexist with
        distinct mutex names (e.g., "Global\\ClaudeInsightDaemon" for dreaming,
        "Global\\ClaudeSearchDaemon" for search). Default value ensures backward
        compatibility with existing code.
    """
    global _pid_file_path, _mutex_handle

    pid_file_path = Path(pid_file)
    current_pid = os.getpid()

    # Step 1: Check if PID file exists with running process (skip if force=True)
    if not force and pid_file_path.exists():
        try:
            existing_pid = int(pid_file_path.read_text().strip())
            if _is_process_running(existing_pid):
                error_msg = (
                    f"Another daemon instance is already running with PID {existing_pid}. "
                    f"Cannot acquire singleton lock."
                )
                return False, error_msg
            # PID exists but process not running -> stale, continue
        except (OSError, ValueError):
            # Corrupted PID file, ignore and continue
            pass

    # Step 2: Try to create Windows mutex
    try:
        mutex_success, mutex_handle, is_new = _create_windows_mutex(mutex_name)
    except Exception as e:
        # Catch unexpected exceptions from mutex creation
        error_msg = f"Failed to create Windows mutex: {e}"
        return False, error_msg

    if not mutex_success:
        error_msg = "Failed to create Windows mutex for singleton enforcement"
        return False, error_msg

    _mutex_handle = mutex_handle

    # Step 3: If mutex already existed, verify it's not stale (skip if force=True)
    if not is_new and not force:
        # Mutex existed, check if PID file has a running process
        if pid_file_path.exists():
            try:
                existing_pid = int(pid_file_path.read_text().strip())
                if _is_process_running(existing_pid):
                    # Mutex exists and PID is running -> another instance
                    release_singleton(pid_file)
                    error_msg = (
                        f"Another daemon instance is already running with PID {existing_pid}. "
                        f"Cannot acquire singleton lock."
                    )
                    return False, error_msg
                # PID exists but process not running -> stale mutex, continue
            except (OSError, ValueError):
                pass  # Corrupted PID file, continue

    # Step 4: Write current PID to file and preserve canonical PID
    try:
        # Use provided state_file or default to standard location
        from pathlib import Path as _Path
        if state_file is None:
            _state_path = _Path("P:/.claude/state/dreaming-daemon-state.json")
        else:
            _state_path = _Path(state_file)

        state = load_state(_state_path)

        # Preserve canonical PID on first acquisition (without backup rotation)
        if state.canonical_pid == 0:
            _update_canonical_pid_only(_state_path, current_pid)

        # Write PID file
        _atomic_write_pid(pid_file_path, current_pid)
        _pid_file_path = pid_file_path
    except OSError as e:
        # Failed to write PID - cleanup and fail
        release_singleton(pid_file)
        error_msg = f"Failed to write PID file: {e}"
        return False, error_msg

    return True, ""


def release_singleton(pid_file: str) -> None:
    """Release singleton lock (both Windows mutex and PID file).

    This function is idempotent - safe to call multiple times.

    Args:
        pid_file: Path to PID file
    """
    global _pid_file_path, _mutex_handle

    pid_file_path = Path(pid_file)

    # Release Windows mutex
    if _mutex_handle is not None:
        try:
            ctypes.windll.kernel32.ReleaseMutex(_mutex_handle)
            ctypes.windll.kernel32.CloseHandle(_mutex_handle)
        except Exception:
            pass  # Ignore errors during cleanup
        _mutex_handle = None

    # Delete PID file
    try:
        if pid_file_path.exists():
            pid_file_path.unlink()
    except Exception:
        pass  # Ignore errors during cleanup

    _pid_file_path = None


def is_instance_running(pid_file: str) -> bool:
    """Check if daemon instance is running via PID file.

    Args:
        pid_file: Path to PID file

    Returns:
        True if instance is running, False otherwise
    """
    pid_file_path = Path(pid_file)

    if not pid_file_path.exists():
        return False

    try:
        existing_pid = int(pid_file_path.read_text().strip())
        return _is_process_running(existing_pid)
    except (OSError, ValueError):
        return False


def _create_windows_mutex(mutex_name: str = "Global\\ClaudeInsightDaemon") -> Tuple[bool, object | None, bool]:
    """Create Windows mutex for singleton enforcement.

    Args:
        mutex_name: Windows mutex name (default: "Global\\ClaudeInsightDaemon")
            Must be unique per daemon type to avoid conflicts.

    Returns:
        Tuple[bool, object | None, bool]: (success, mutex_handle, is_new) where:
            - success: True if mutex was created/opened successfully
            - mutex_handle: Windows mutex handle if successful, None otherwise
            - is_new: True if mutex was newly created, False if it already existed

    Note:
        This function uses CreateMutexW which returns a handle to an existing
        mutex if one with the same name already exists. GetLastError() with
        ERROR_ALREADY_EXISTS distinguishes between new and existing mutexes.
    """
    try:
        # Create or open mutex
        handle = ctypes.windll.kernel32.CreateMutexW(
            None,  # Security attributes
            False,  # Initial owner (don't own immediately)
            mutex_name
        )

        if not handle:
            return False, None, False

        # Check if mutex already existed
        error_code = ctypes.windll.kernel32.GetLastError()
        is_new = (error_code != ERROR_ALREADY_EXISTS)

        return True, handle, is_new

    except Exception:
        return False, None, False


def _atomic_write_pid(pid_file_path: Path, pid: int) -> None:
    """Write PID to file atomically (tmp file + rename).

    Args:
        pid_file_path: Path to PID file
        pid: Process ID to write
    """
    # Get directory and filename
    pid_dir = pid_file_path.parent
    pid_filename = pid_file_path.name

    # Create temporary file in same directory
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=pid_dir,
        prefix=f'.{pid_filename}.',
        delete=False
    ) as tmp_file:
        tmp_file.write(str(pid))
        tmp_path = tmp_file.name

    # Atomic rename (same filesystem)
    try:
        # On Windows, os.replace() is atomic
        os.replace(tmp_path, pid_file_path)
    except Exception:
        # Cleanup temp file if rename fails
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        raise


# Make this function mockable for testing
def _is_process_running(pid: int) -> bool:
    """Check if process with given PID is running.

    This function can be mocked in tests to simulate running processes.

    Args:
        pid: Process ID to check

    Returns:
        True if process is running, False otherwise
    """
    # Check if it's the current process
    if pid == os.getpid():
        return True

    # Platform-specific check
    return _check_process_running_platform(pid)


def _check_process_running_platform(pid: int) -> bool:
    """Platform-specific process running check.

    Args:
        pid: Process ID to check

    Returns:
        True if process is running, False otherwise
    """
    # Use os.kill with signal 0 (works on both Unix and Windows)
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _update_canonical_pid_only(state_path: Path, pid: int) -> None:
    """Update canonical_pid field in state file without backup rotation (T-008).

    This function provides minimal state update for mutex operations without
    triggering the expensive backup rotation performed by save_state().

    Args:
        state_path: Path to state file
        pid: Canonical PID to write

    Behavior:
        - Loads existing state (or creates default)
        - Updates only canonical_pid field
        - Writes atomically to temp file, then renames
        - Does NOT rotate backups (T-008 requirement)

    Note:
        This is a specialized function for mutex acquisition. For normal
        state updates, use dreaming_state.save_state() which includes
        backup rotation and checksum calculation.
    """
    # Load existing state (creates default if missing)
    state = load_state(state_path)

    # Update canonical PID
    state.canonical_pid = pid

    # Ensure parent directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write pattern: write to temp file, then rename
    # Note: No backup rotation (T-008 requirement)
    temp_path = state_path.with_suffix('.tmp')
    try:
        # Write state to temp file
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(state.__dict__, f, indent=2)
            # Flush buffers and fsync for durability
            f.flush()
            os.fsync(f.fileno())
        # Atomic rename (temp -> actual)
        temp_path.replace(state_path)
    except Exception as e:
        # Clean up temp file if write failed
        if temp_path.exists():
            temp_path.unlink()
        raise OSError(f"Failed to update canonical PID in state file: {e}")
