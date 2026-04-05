#!/usr/bin/env python3
"""
Unified Log Rotation for Diagnostic Logs
==========================================

Provides centralized log rotation, compression, and retention for all
diagnostic logs in the hooks directory.

Features:
- Size and entry-based truncation (keep recent logs)
- Automatic compression of old logs (gzip)
- Time-based retention (delete after N days)
- Unified policy across all diagnostic logs

Usage:
    from log_rotation import rotate_diagnostic_logs

    # Rotate all diagnostic logs
    rotate_diagnostic_logs()

    # Or rotate specific log
    from log_rotation import rotate_log_file
    rotate_log_file(log_path)
"""

from __future__ import annotations

import gzip
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Configuration
_LOG_RETENTION_DAYS = 30  # Delete logs older than this
_LOG_COMPRESS_AFTER_DAYS = 7  # Compress logs older than this
_LOG_MAX_SIZE_MB = 10  # Compress if file larger than this
_LOG_MAX_ENTRIES = 1000  # Truncate to this many entries


def get_hooks_dir() -> Path:
    """Get the hooks directory path.

    Returns:
        Path to hooks directory
    """
    # Try to detect from this file's location
    try:
        return Path(__file__).resolve().parent.parent
    except Exception:
        # Fallback to known location
        return Path("P:/.claude/hooks")


def rotate_diagnostic_logs(
    retention_days: int = _LOG_RETENTION_DAYS,
    compress_after_days: int = _LOG_COMPRESS_AFTER_DAYS,
    max_size_mb: int = _LOG_MAX_SIZE_MB,
    max_entries: int = _LOG_MAX_ENTRIES,
) -> dict[str, int]:
    """Rotate all diagnostic logs in hooks directory.

    Args:
        retention_days: Delete logs older than this many days
        compress_after_days: Compress logs older than this many days
        max_size_mb: Compress files larger than this many MB
        max_entries: Truncate JSONL files to this many entries

    Returns:
        Dict with rotation statistics
    """
    hooks_dir = get_hooks_dir()
    diag_dir = hooks_dir / "logs" / "diagnostics"

    if not diag_dir.exists():
        return {"total_logs_rotated": 0}

    stats = {
        "total_logs_rotated": 0,
        "compressed": 0,
        "deleted": 0,
        "truncated": 0,
        "errors": 0,
    }

    # Process all structured diagnostics
    for log_file in diag_dir.glob("*.jsonl"):
        try:
            _rotate_single_log(
                log_file,
                retention_days=retention_days,
                compress_after_days=compress_after_days,
                max_size_mb=max_size_mb,
                max_entries=max_entries,
                stats=stats,
            )
            stats["total_logs_rotated"] += 1
        except Exception:
            stats["errors"] += 1
            # Fail silently to avoid disrupting hook execution
            pass

    # Process plain-text diagnostics too (startup probes, failsafe logs, opt-in canaries)
    for log_file in diag_dir.glob("*.log"):
        try:
            _rotate_single_log(
                log_file,
                retention_days=retention_days,
                compress_after_days=compress_after_days,
                max_size_mb=max_size_mb,
                max_entries=max_entries,
                stats=stats,
            )
            stats["total_logs_rotated"] += 1
        except Exception:
            stats["errors"] += 1
            pass

    # Also clean up old compressed logs
    _cleanup_old_compressed_logs(
        diag_dir,
        retention_days=retention_days,
        stats=stats,
    )

    return stats


def _rotate_single_log(
    log_file: Path,
    retention_days: int,
    compress_after_days: int,
    max_size_mb: int,
    max_entries: int,
    stats: dict,
) -> None:
    """Rotate a single log file.

    Args:
        log_file: Path to log file
        retention_days: Delete logs older than this
        compress_after_days: Compress logs older than this
        max_size_mb: Compress if larger than this
        max_entries: Truncate to this many entries
        stats: Statistics dict to update
    """
    if not log_file.exists():
        return

    # 1. Check file size - compress if too large
    file_size_mb = log_file.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        _compress_log(log_file)
        stats["compressed"] += 1
        return  # Don't truncate if we just compressed

    # 2. Check entry count - truncate if too many
    if log_file.suffix == ".jsonl":
        entry_count = _count_jsonl_entries(log_file)
        if entry_count > max_entries:
            _truncate_jsonl(log_file, max_entries)
            stats["truncated"] += 1

    # 3. Compress old logs
    if _should_compress(log_file, compress_after_days):
        _compress_log(log_file)
        stats["compressed"] += 1

    # 4. Delete very old logs
    if _should_delete(log_file, retention_days):
        log_file.unlink()
        stats["deleted"] += 1


def _count_jsonl_entries(log_file: Path) -> int:
    """Count entries in a JSONL file.

    Args:
        log_file: Path to JSONL file

    Returns:
        Number of entries
    """
    try:
        with open(log_file, encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


def _truncate_jsonl(log_file: Path, max_entries: int) -> None:
    """Truncate JSONL file to last N entries.

    Args:
        log_file: Path to JSONL file
        max_entries: Maximum entries to keep
    """
    try:
        with open(log_file, encoding="utf-8") as f:
            lines = f.readlines()

        if len(lines) > max_entries:
            with open(log_file, "w", encoding="utf-8") as f:
                f.writelines(lines[-max_entries:])
    except Exception:
        pass  # Fail silently


def _should_compress(log_file: Path, compress_after_days: int) -> bool:
    """Check if log file should be compressed.

    Args:
        log_file: Path to log file
        compress_after_days: Compress if older than this

    Returns:
        True if should compress
    """
    if log_file.suffix == ".gz":
        return False  # Already compressed

    # Check file age
    mtime = datetime.fromtimestamp(log_file.stat().st_mtime, tz=timezone.utc)
    age_days = (datetime.now(timezone.utc) - mtime).days

    return age_days >= compress_after_days


def _should_delete(log_file: Path, retention_days: int) -> bool:
    """Check if log file should be deleted.

    Args:
        log_file: Path to log file
        retention_days: Delete if older than this

    Returns:
        True if should delete
    """
    # Check file age
    mtime = datetime.fromtimestamp(log_file.stat().st_mtime, tz=timezone.utc)
    age_days = (datetime.now(timezone.utc) - mtime).days

    return age_days > retention_days


def _compress_log(log_file: Path) -> Path:
    """Compress a log file with gzip.

    Args:
        log_file: Path to log file

    Returns:
        Path to compressed file
    """
    compressed_path = log_file.with_suffix(log_file.suffix + ".gz")

    # Read original file
    with open(log_file, "rb") as f_in:
        with gzip.open(compressed_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Delete original
    log_file.unlink()

    return compressed_path


def _cleanup_old_compressed_logs(
    diag_dir: Path,
    retention_days: int,
    stats: dict,
) -> None:
    """Delete old compressed logs that exceed retention period.

    Args:
        diag_dir: Diagnostics directory
        retention_days: Delete logs older than this
        stats: Statistics dict to update
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    for compressed_file in diag_dir.glob("*.gz"):
        try:
            mtime = datetime.fromtimestamp(
                compressed_file.stat().st_mtime,
                tz=timezone.utc,
            )
            if mtime < cutoff:
                compressed_file.unlink()
                stats["deleted"] += 1
        except Exception:
            pass  # Fail silently


def rotate_log_file(
    log_path: Path | str,
    retention_days: int = _LOG_RETENTION_DAYS,
    compress_after_days: int = _LOG_COMPRESS_AFTER_DAYS,
    max_size_mb: int = _LOG_MAX_SIZE_MB,
    max_entries: int = _LOG_MAX_ENTRIES,
) -> dict[str, int]:
    """Rotate a specific log file.

    Args:
        log_path: Path to log file
        retention_days: Delete logs older than this
        compress_after_days: Compress logs older than this
        max_size_mb: Compress if larger than this
        max_entries: Truncate JSONL to this many entries

    Returns:
        Statistics dict
    """
    log_file = Path(log_path)
    stats = {"compressed": 0, "deleted": 0, "truncated": 0, "errors": 0}

    _rotate_single_log(
        log_file,
        retention_days=retention_days,
        compress_after_days=compress_after_days,
        max_size_mb=max_size_mb,
        max_entries=max_entries,
        stats=stats,
    )

    return stats


if __name__ == "__main__":
    # Run rotation when executed directly
    import sys

    retention = int(sys.argv[1]) if len(sys.argv) > 1 else _LOG_RETENTION_DAYS

    print(f"Rotating diagnostic logs (retention: {retention} days)...")
    stats = rotate_diagnostic_logs(retention_days=retention)

    print("Rotation complete:")
    print(f"  Total logs processed: {stats['total_logs_rotated']}")
    print(f"  Compressed: {stats['compressed']}")
    print(f"  Deleted: {stats['deleted']}")
    print(f"  Truncated: {stats['truncated']}")
    print(f"  Errors: {stats['errors']}")
