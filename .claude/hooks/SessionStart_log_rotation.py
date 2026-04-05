#!/usr/bin/env python3
"""
SessionStart Log Rotation

Automatically rotates diagnostic logs on session start.
Uses throttling to only run once per day to avoid overhead.

Configuration:
    LOG_ROTATION_ENABLED: Enable/disable (default: true)
    LOG_ROTATION_RETENTION_DAYS: Days to keep logs (default: 30)
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add hooks to path
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

# Configuration
ENABLED = os.environ.get("LOG_ROTATION_ENABLED", "true").lower() in ("1", "true", "yes")
RETENTION_DAYS = int(os.environ.get("LOG_ROTATION_RETENTION_DAYS", "30"))

# Throttle file to avoid running too frequently
_THROTTLE_FILE = HOOKS_DIR / "state" / "last_log_rotation.txt"


def _should_run_rotation() -> bool:
    """Check if log rotation should run (throttled to once per day).

    Returns:
        True if rotation should run
    """
    if not _THROTTLE_FILE.exists():
        return True

    try:
        last_run_str = _THROTTLE_FILE.read_text().strip()
        if not last_run_str:
            return True

        last_run = datetime.fromisoformat(last_run_str)
        now = datetime.now(timezone.utc)

        # Only run if 24+ hours have passed
        if (now - last_run) > timedelta(hours=24):
            return True

        return False
    except Exception:
        # If we can't read the throttle file, run rotation
        return True


def _update_throttle_timestamp() -> None:
    """Update the throttle file with current timestamp."""
    try:
        _THROTTLE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _THROTTLE_FILE.write_text(datetime.now(timezone.utc).isoformat())
    except Exception:
        pass  # Fail silently


def _rotate_adversarial_files() -> int:
    """Rotate adversarial review files, keeping only N most recent per category.

    Scans state/ and findings/ for adversarial-*.json files, groups by
    category (e.g., compliance, testing, security), and removes excess
    files keeping only the newest MAX_PER_CATEGORY per group.

    Returns:
        Number of files removed
    """

    state_dir = HOOKS_DIR / "state"
    findings_dir = HOOKS_DIR.parent / "findings"
    max_per_category = int(os.environ.get("ADVERSARIAL_ROTATION_KEEP", "10"))

    # Group adversarial files by category
    pattern = re.compile(r"^adversarial-(\w+)-.*\.json$")
    categories: dict[str, list[Path]] = {}

    for scan_dir in (state_dir, findings_dir):
        if not scan_dir.exists():
            continue
        for f in scan_dir.glob("adversarial-*.json"):
            match = pattern.match(f.name)
            if match:
                cat = match.group(1)
                categories.setdefault(cat, []).append(f)

    removed = 0
    for cat, files in categories.items():
        # Sort by modification time, newest first
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        # Remove excess
        for old_file in files[max_per_category:]:
            try:
                old_file.unlink()
                removed += 1
            except OSError:
                pass

    return removed


def main() -> None:
    """Run log rotation if throttling allows."""
    if not ENABLED:
        return

    try:
        if not _should_run_rotation():
            return

        # Import and run rotation
        from __lib.log_rotation import rotate_diagnostic_logs

        stats = rotate_diagnostic_logs(retention_days=RETENTION_DAYS)

        # Update throttle timestamp
        _update_throttle_timestamp()

        # Optional: log to stdout for visibility (but not stderr!)
        if stats["total_logs_rotated"] > 0:
            print(
                f'{{"additionalContext": "🧹 Log rotation: {stats["compressed"]} compressed, '
                f'{stats["deleted"]} deleted, {stats["truncated"]} truncated"}}'
            )

        # Rotate adversarial review files (keep 10 most recent per category)
        adversarial_removed = _rotate_adversarial_files()
        if adversarial_removed > 0:
            print(
                f'{{"additionalContext": "🧹 Adversarial rotation: {adversarial_removed} old review files removed"}}'
            )
    except Exception:
        # Fail silently - log rotation is optional
        pass


if __name__ == "__main__":
    main()
