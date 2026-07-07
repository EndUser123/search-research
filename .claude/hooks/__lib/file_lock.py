"""
Cross-platform file locking using portalocker.
Provides a context manager for file locking that works on both
Windows and Unix systems.
"""

from __future__ import annotations

import sys
import threading
import json
from pathlib import Path
from typing import Any

sys.modules.setdefault("redis", None)

try:
    import portalocker
    from portalocker.exceptions import BaseLockException, LockException
    _PORTALOCKER_AVAILABLE = True
except ImportError:
    _PORTALOCKER_AVAILABLE = False

# Exception family that lock/IO contention surfaces as. TimeoutError (raised by
# FileLock.__enter__ on contention) is an OSError subclass, so OSError covers the
# normal path. BaseLockException covers non-timeout lock-family failures (e.g.
# AlreadyLocked) that the LockException->TimeoutError conversion does NOT catch --
# without it those leak past `except OSError` and crash the caller.
_LOCK_FAILURES: tuple[type[BaseException], ...] = (OSError,)
if _PORTALOCKER_AVAILABLE:
    _LOCK_FAILURES = (OSError, BaseLockException)


class FileLock:
    """Cross-platform file locking. Uses portalocker when available."""

    def __init__(self, lock_path: Path, timeout: float = 5.0) -> None:
        self.lock_path = Path(lock_path)
        self.timeout = timeout
        self._portalocker_lock: Any = None
        self._thread_lock: threading.Lock | None = None

    def __enter__(self) -> FileLock:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        if _PORTALOCKER_AVAILABLE:
            try:
                self._portalocker_lock = portalocker.Lock(
                    str(self.lock_path), mode="a", timeout=self.timeout,
                )
                self._portalocker_lock.acquire()
            except LockException:
                raise TimeoutError(
                    f"Could not acquire lock on {self.lock_path} within {self.timeout}s"
                )
        else:
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


def append_jsonl(log_path: Path, entry: dict) -> None:
    """Thread/process-safe JSONL append using portalocker cross-process lock.

    Acquires FileLock on a sidecar .lock file, then appends one JSON line.
    Does NOT swallow exceptions -- callers must handle their own error paths.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(log_path.with_suffix(".lock")):
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
