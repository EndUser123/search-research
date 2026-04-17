"""Canonical Archive — append-only raw event storage and watermark persistence for CHS multi-provider history layer."""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from filelock import FileLock

_ARCHIVE_BASE = Path("P:/__csf/data/chs_archive")
_WATERMARK_DIR = _ARCHIVE_BASE / "watermarks"

# Lock settings
_LOCK_TIMEOUT = 30
_STALE_LOCK_THRESHOLD = 300  # 5 minutes


def _stale_lock_recovery(lock_path: Path) -> None:
    """Delete lock file if older than _STALE_LOCK_THRESHOLD seconds."""
    try:
        if lock_path.exists():
            mtime = lock_path.stat().st_mtime
            if time.time() - mtime > _STALE_LOCK_THRESHOLD:
                lock_path.unlink()
    except OSError:
        pass


def _event_timestamp_year_month(timestamp_ms: int | float | None) -> tuple[int, int]:
    """Return (year, month) derived from ms-since-epoch timestamp."""
    if timestamp_ms:
        try:
            # timestamp is ms-since-epoch; convert to seconds
            ts = int(timestamp_ms) / 1000
            import time as _time_module

            # Use gmtime for UTC year/month
            broken = _time_module.gmtime(ts)
            return broken.tm_year, broken.tm_mon
        except (ValueError, OSError, ZeroDivisionError):
            pass
    now = time.gmtime()
    return now.tm_year, now.tm_mon


def _blocking_write_watermark_logic(
    lock_path: Path, target_dir: Path, target: Path, watermark: dict[str, Any]
) -> None:
    with FileLock(lock_path, timeout=_LOCK_TIMEOUT):
        staged_fd, staged_path = tempfile.mkstemp(
            dir=str(target_dir),
            suffix=".staged",
        )
        try:
            with os.fdopen(staged_fd, "w", encoding="utf-8") as fh:
                json.dump(watermark, fh, separators=(",", ":"))
            os.replace(staged_path, target)
        except OSError:
            try:
                os.unlink(staged_path)
            except OSError:
                pass
            raise


def append_raw_event(provider_id: str, source_id: str, event: dict[str, Any]) -> str:
    """Append event to append-only raw archive.

    Path: P:/__csf/data/chs_archive/{provider_id}/{year}/{month}/{source_id}/raw_{event_id}.jsonl

    Returns the absolute path to the written raw file.
    """
    event_id = event.get("uuid") or str(uuid.uuid4())
    timestamp_ms = event.get("timestamp")

    year, month = _event_timestamp_year_month(timestamp_ms)

    target_dir = _ARCHIVE_BASE / provider_id / str(year) / f"{month:02d}" / source_id
    target_dir.mkdir(parents=True, exist_ok=True)

    target = target_dir / f"raw_{event_id}.jsonl"

    # Atomic staging: write to tempfile in same directory, then os.replace()
    staged_fd, staged_path = tempfile.mkstemp(
        dir=str(target_dir),
        suffix=".staged",
    )
    try:
        with os.fdopen(staged_fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(event, separators=(",", ":")) + "\n")
        os.replace(staged_path, target)
    except OSError:
        # Clean up staged file on failure
        try:
            os.unlink(staged_path)
        except OSError:
            pass
        raise

    return str(target)


async def write_watermark(provider_id: str, source_id: str, terminal_id: str, watermark: dict[str, Any]) -> None:
    """Write watermark using staged atomic write + FileLock."""
    # Path: P:/__csf/data/chs_archive/watermarks/{provider_id}/{source_id}/watermark_{terminal_id}.json
    safe_tid = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id)
    target_dir = _WATERMARK_DIR / provider_id / source_id
    await asyncio.to_thread(target_dir.mkdir, parents=True, exist_ok=True)

    target = target_dir / f"watermark_{safe_tid}.json"

    lock_dir = target_dir / "locks"
    await asyncio.to_thread(lock_dir.mkdir, parents=True, exist_ok=True)
    lock_path = lock_dir / f"{safe_tid}.lock"

    # Stale lock recovery on startup
    await asyncio.to_thread(_stale_lock_recovery, lock_path)

    await asyncio.to_thread(
        _blocking_write_watermark_logic, lock_path, target_dir, target, watermark
    )


async def read_watermark(provider_id: str, source_id: str, terminal_id: str) -> dict[str, Any] | None:
    """Read watermark. Returns None if not exists."""
    safe_tid = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id)
    target = _WATERMARK_DIR / provider_id / source_id / f"watermark_{safe_tid}.json"

    if not await asyncio.to_thread(target.exists):
        return None

    try:
        def _blocking_read():
            with open(target, encoding="utf-8") as fh:
                return json.load(fh)
        return await asyncio.to_thread(_blocking_read)
    except (OSError, json.JSONDecodeError):
        return None
