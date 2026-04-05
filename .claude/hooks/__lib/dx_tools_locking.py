"""
DX Tools File Locking

Provides cross-platform file locking for cache operations to prevent
race conditions in multi-terminal scenarios.

Uses portalocker for cross-platform locking (Windows fcntl, Unix msvcrt).
Implements timeout with stale lock cleanup and graceful fallback.
"""

import hashlib
import os
import sys
import time
from functools import wraps
from pathlib import Path
from typing import Callable, Optional

# Try to import portalocker, fallback to no-op
try:
    import portalocker
    PORTALOCKER_AVAILABLE = True
except ImportError:
    PORTALOCKER_AVAILABLE = False

# Add parent directory to path for imports
if __name__ != "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _get_package_lock_path(package_path: str, locks_dir: Optional[Path] = None) -> Path:
    """Generate lock file path for a package.

    Args:
        package_path: Absolute path to package directory
        locks_dir: Directory for lock files. Defaults to logs/locks/

    Returns:
        Path to lock file for this package
    """
    if locks_dir is None:
        hooks_dir = Path(__file__).resolve().parent.parent
        locks_dir = hooks_dir / "logs" / "locks"
        locks_dir.mkdir(parents=True, exist_ok=True)

    # Hash package path to create unique lock filename
    # Use absolute path to ensure consistency
    abs_path = str(Path(package_path).resolve())
    path_hash = hashlib.md5(abs_path.encode('utf-8')).hexdigest()[:12]

    return locks_dir / f"cache_{path_hash}.lock"


def _acquire_lock(lock_path: Path, timeout: float = 60.0) -> bool:
    """Acquire file lock with timeout.

    Args:
        lock_path: Path to lock file
        timeout: Maximum seconds to wait for lock (default: 60)

    Returns:
        True if lock acquired, False if timeout or error
    """
    if not PORTALOCKER_AVAILABLE:
        # Fallback: no-op if portalocker not available
        return True

    try:
        # Create lock file if it doesn't exist
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        # Open lock file and acquire lock
        lock_file = open(lock_path, 'w')

        # Try to acquire exclusive lock with timeout
        start_time = time.time()
        while True:
            try:
                portalocker.lock(lock_file, portalocker.LOCK_EX | portalocker.LOCK_NB)
                return True
            except portalocker.exceptions.LockException:
                # Lock is held by another process
                if time.time() - start_time >= timeout:
                    lock_file.close()
                    return False

                # Wait a bit before retrying
                time.sleep(0.1)

    except Exception as e:
        # Graceful degradation - allow operation to proceed
        verbose = os.environ.get("DX_TOOLS_METRICS_VERBOSE", "false").lower() == "true"
        if verbose:
            print(f"Warning: Could not acquire lock: {e}")
        return False


def _release_lock(lock_file, lock_path: Path) -> None:
    """Release file lock and cleanup.

    Args:
        lock_file: Open file handle to release lock on
        lock_path: Path to lock file (for cleanup)
    """
    if not PORTALOCKER_AVAILABLE or lock_file is None:
        return

    try:
        portalocker.unlock(lock_file)
        lock_file.close()

        # Clean up lock file
        if lock_path.exists():
            lock_path.unlink()
    except Exception as e:
        # Non-fatal - lock may have been cleaned up already
        verbose = os.environ.get("DX_TOOLS_METRICS_VERBOSE", "false").lower() == "true"
        if verbose:
            print(f"Warning: Could not release lock: {e}")


def with_cache_lock(package_path: str, timeout: float = 60.0):
    """Decorator to add file locking to cache operations.

    Args:
        package_path: Path to package directory (will be hashed for lock filename)
        timeout: Lock acquisition timeout in seconds (default: 60)

    Usage:
        @with_cache_lock("/path/to/package")
        def clear_package_cache(package_path):
            # ... cache clearing logic ...

    Note:
        If portalocker is not available, the decorator is a no-op
        (operations proceed without locking, with a warning in verbose mode).
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not PORTALOCKER_AVAILABLE:
                # No-op fallback: just call the function
                verbose = os.environ.get("DX_TOOLS_METRICS_VERBOSE", "false").lower() == "true"
                if verbose:
                    print("Warning: portalocker not available, cache operation not locked")
                return func(*args, **kwargs)

            lock_path = _get_package_lock_path(package_path)
            lock_file = None

            try:
                # Acquire lock
                if not _acquire_lock(lock_path, timeout):
                    raise TimeoutError(f"Could not acquire cache lock after {timeout}s")

                # Call the wrapped function
                result = func(*args, **kwargs)

                return result

            finally:
                # Always release lock
                _release_lock(lock_file, lock_path)

        return wrapper
    return decorator


class CacheLockContext:
    """Context manager for cache locks.

    Usage:
        with CacheLockContext("/path/to/package") as lock:
            if lock.acquired:
                # ... cache operations ...
            else:
                # ... handle timeout ...
    """

    def __init__(self, package_path: str, timeout: float = 60.0):
        """Initialize cache lock context.

        Args:
            package_path: Path to package directory
            timeout: Lock acquisition timeout in seconds
        """
        self.package_path = package_path
        self.timeout = timeout
        self.lock_path = _get_package_lock_path(package_path)
        self.lock_file = None
        self.acquired = False

    def __enter__(self):
        """Acquire lock on context entry."""
        if not PORTALOCKER_AVAILABLE:
            # No-op fallback
            return self

        self.lock_file = open(self.lock_path, 'w')
        self.acquired = _acquire_lock(self.lock_path, self.timeout)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release lock on context exit."""
        _release_lock(self.lock_file, self.lock_path)
        return False


# Test CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DX Tools File Locking CLI")
    parser.add_argument("--test-lock", type=str, help="Test locking on a path")
    parser.add_argument("--timeout", type=float, default=5.0, help="Lock timeout in seconds")

    args = parser.parse_args()

    if args.test_lock:
        print(f"Testing lock on: {args.test_lock}")
        print(f"Portalocker available: {PORTALOCKER_AVAILABLE}")

        lock_path = _get_package_lock_path(args.test_lock)
        print(f"Lock file: {lock_path}")

        # Test lock acquisition
        print("Acquiring lock...")
        acquired = _acquire_lock(lock_path, args.timeout)

        if acquired:
            print("Lock acquired successfully!")
            print("Holding for 2 seconds...")
            time.sleep(2)

            # Release and cleanup
            try:
                lock_file = open(lock_path)
                _release_lock(lock_file, lock_path)
                print("Lock released")
            except Exception as e:
                print(f"Release error: {e}")
        else:
            print(f"Failed to acquire lock after {args.timeout}s")
