"""
Cross-platform file locking using portalocker.

Provides a context manager for file locking that works on both
Windows and Unix systems.

Usage:
    with FileLock(Path("myfile.lock")):
        # Safe to read/write shared files here
        data = read_file()
        data["count"] += 1
        write_file(data)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Block portalocker's eager redis import — redis 7.x is incompatible with Python 3.14
# and portalocker.redis is not needed for file locking.
sys.modules.setdefault("redis", None)  # type: ignore[arg-type]

import portalocker  # noqa: E402
from portalocker.exceptions import LockException  # noqa: E402


class FileLock:
    """
    Cross-platform file locking that works on Windows and Unix.

    Use as a context manager to ensure lock is always released.
    """

    def __init__(self, lock_path: Path, timeout: float = 5.0) -> None:
        """
        Args:
            lock_path: Path to the lock file (will be created if doesn't exist)
            timeout: Max seconds to wait for lock (default 5s)
        """
        self.lock_path = Path(lock_path)
        self.timeout = timeout
        self._portalocker_lock: portalocker.Lock | None = None

    def __enter__(self) -> FileLock:
        # Ensure parent directory exists
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

        # Use portalocker.Lock which has built-in timeout support
        # portalocker.Lock raises LockException (specifically AlreadyLocked)
        # when timeout occurs, so we convert to TimeoutError for consistency
        try:
            self._portalocker_lock = portalocker.Lock(
                str(self.lock_path),
                mode="a",
                timeout=self.timeout,
            )
            self._portalocker_lock.acquire()
        except LockException:
            raise TimeoutError(
                f"Could not acquire lock on {self.lock_path} within {self.timeout} seconds"
            )

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # Release the lock
        if self._portalocker_lock:
            self._portalocker_lock.release()
            self._portalocker_lock = None
