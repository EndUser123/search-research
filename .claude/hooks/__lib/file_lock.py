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
import threading
from pathlib import Path
from typing import Any

# Block portalocker's eager redis import — redis 7.x is incompatible with Python 3.14
# and portalocker.redis is not needed for file locking.
sys.modules.setdefault("redis", None)  # type: ignore[arg-type]

try:
    import portalocker  # noqa: E402
    from portalocker.exceptions import LockException  # noqa: E402
    _PORTALOCKER_AVAILABLE = True
except ImportError:
    _PORTALOCKER_AVAILABLE = False


class FileLock:
    """
    Cross-platform file locking. Uses portalocker when available for cross-process
    safety; falls back to threading.Lock (in-process only) when portalocker is absent.
    """

    def __init__(self, lock_path: Path, timeout: float = 5.0) -> None:
        self.lock_path = Path(lock_path)
        self.timeout = timeout
        self._portalocker_lock: Any = None
        self._thread_lock: threading.Lock | None = None

    def __enter__(self) -> FileLock:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

        if _PORTALOCKER_AVAILABLE:
            try:
                self._portalocker_lock = portalocker.Lock(  # type: ignore[union-attr]
                    str(self.lock_path),
                    mode="a",
                    timeout=self.timeout,
                )
                self._portalocker_lock.acquire()
            except LockException:  # type: ignore[misc]
                raise TimeoutError(
                    f"Could not acquire lock on {self.lock_path} within {self.timeout}s"
                )
        else:
            # portalocker unavailable — in-process threading lock only
            self._thread_lock = threading.Lock()
            self._thread_lock.acquire(timeout=self.timeout)

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._portalocker_lock:
            self._portalocker_lock.release()
            self._portalocker_lock = None
        if self._thread_lock and self._thread_lock.locked():
            self._thread_lock.release()
            self._thread_lock = None
