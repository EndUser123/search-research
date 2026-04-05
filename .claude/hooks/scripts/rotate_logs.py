#!/usr/bin/env python3
"""Rotate hook error logs older than 30 days.

Usage:
    python rotate_logs.py
    python rotate_logs.py --dry-run
    python rotate_logs.py --days 7
    python rotate_logs.py --help

Arguments:
    --days N: Rotate logs older than N days (default: 30)
    --dry-run: Show what would be rotated without actually deleting
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path


def main(max_age_days: int = 30, dry_run: bool = False) -> None:
    """Rotate hook error logs older than max_age_days."""
    log_dir = Path("P:/.claude/hooks/logs")

    if not log_dir.exists():
        print("Log directory does not exist")
        print(f"Expected: {log_dir}")
        return

    cutoff = datetime.now() - timedelta(days=max_age_days)
    removed = 0
    total_size = 0

    # Find all log files
    for log_file in log_dir.glob("*.jsonl"):
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

            if mtime < cutoff:
                # Calculate file size
                size = log_file.stat().st_size
                total_size += size

                if dry_run:
                    print(f"[DRY RUN] Would remove: {log_file.name} ({size} bytes, {mtime.strftime('%Y-%m-%d')})")
                else:
                    log_file.unlink()
                    removed += 1
                    print(f"Removed: {log_file.name} ({size} bytes, {mtime.strftime('%Y-%m-%d')})")
        except Exception as e:
            print(f"Warning: Could not process {log_file}: {e}")

    # Summary
    if dry_run:
        total_size_kb = total_size / 1024
        print(f"\n[Dry run] Would rotate {removed} log files ({total_size_kb:.1f} KB)")
    elif removed > 0:
        total_size_kb = total_size / 1024
        print(f"\nRotated {removed} log files (older than {max_age_days} days, {total_size_kb:.1f} KB)")
    else:
        print(f"\nNo logs to rotate (all logs are newer than {max_age_days} days)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Rotate hook error logs older than specified days"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Rotate logs older than N days (default: 30)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be rotated without actually deleting"
    )
    args = parser.parse_args()
    main(args.days, args.dry_run)
