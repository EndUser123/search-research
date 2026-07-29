"""Host primitive: atomic file writes with optional cross-platform locking.

Lives at P:/.agents/__lib/atomic_io.py so any skill can `from __lib.atomic_io
import atomic_write_only, atomic_write_with_lock`.

Why this exists:
- Multiple skills (currently email-skill, future ones) need to write JSON
  files under P:/.data/ that are shared across processes/terminals.
- Naive `open(path, 'w').write(...)` can corrupt the file under concurrent
  writers (last writer wins, partial writes visible to readers mid-call).
- This module provides two patterns:
    1. atomic_write_only: tmp + os.replace, single-process safe.
    2. atomic_write_with_lock: same, plus a cross-platform exclusive file
       lock (msvcrt.locking on Windows, fcntl.flock on POSIX) so concurrent
       processes serialize their writes.

Encoding is always utf-8. On Windows, os.replace handles overwriting an
existing target atomically when both paths are on the same filesystem.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Union

PathLike = Union[str, Path]


def _ensure_parent(path: PathLike) -> None:
    """Create parent directory tree if missing; idempotent."""
    parent = Path(path).parent
    if parent and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)


def _tmp_path_for(target: Path) -> Path:
    """Pick a tmp path adjacent to target, on the same filesystem."""
    if target.suffix:
        return target.with_name(target.name + ".tmp")
    return target.with_name(target.name + ".tmp")


def atomic_write_only(target_path: PathLike, content: str) -> None:
    """Write content to target_path atomically (no external lock).

    Strategy:
      1. Write content to <target>.tmp (same dir as target).
      2. Flush and fsync the tmp file.
      3. os.replace(tmp, target) — atomic on Windows + POSIX when on the
         same filesystem.

    Encoding: utf-8. Newlines are normalized to '\\n' (the OS-default
    text-mode translation is disabled via newline='\\n').
    """
    target = Path(target_path)
    _ensure_parent(target)
    tmp = _tmp_path_for(target)
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            # Some filesystems don't support fsync; not fatal.
            pass
    os.replace(tmp, target)


def atomic_write_with_lock(
    lock_path: PathLike,
    target_path: PathLike,
    content: str,
    timeout: float = 30.0,
) -> None:
    """Acquire an exclusive file lock, write atomically, release the lock.

    Cross-platform:
      - Windows: msvcrt.locking(fd, LK_NBLCK, 1) — non-blocking 1-byte
        exclusive lock on the lockfile fd. Release happens on close.
      - POSIX:   fcntl.flock(fd, LOCK_EX | LOCK_NB) — non-blocking exclusive
        advisory lock. Release happens on close or explicit LOCK_UN.

    The lock is advisory: all participants must use this primitive.
    On timeout, raises TimeoutError. On any other error during the
    locked write, the lock is still released (fd closed) before the
    exception propagates.
    """
    lock_path = Path(lock_path)
    target_path = Path(target_path)
    _ensure_parent(lock_path)
    _ensure_parent(target_path)

    deadline = time.time() + timeout
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)

    got_lock = False
    try:
        # Retry loop: non-blocking acquire, sleep, retry until deadline.
        while True:
            try:
                if sys.platform == "win32":
                    import msvcrt  # type: ignore[import-not-found]
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl  # type: ignore[import-not-found]
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                got_lock = True
                break
            except (IOError, OSError):
                if time.time() >= deadline:
                    raise TimeoutError(
                        f"atomic_write_with_lock: could not acquire "
                        f"{lock_path} within {timeout}s"
                    )
                time.sleep(0.1)

        # We hold the lock. Do the atomic write.
        atomic_write_only(target_path, content)
    finally:
        # Release lock: on POSIX we explicitly unlock before close so the
        # release is immediate; on Windows msvcrt releases on close.
        try:
            if got_lock and sys.platform != "win32":
                import fcntl  # type: ignore[import-not-found]
                try:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                except (IOError, OSError):
                    pass
        finally:
            try:
                os.close(fd)
            except OSError:
                pass