#!/usr/bin/env python3
"""Cleanup corrupted package names from dependency verification state files.

This script removes entries with shell metacharacters from verification state,
leftover from before the clean_package_name() fix was applied.

Run once to clean up legacy corrupted data.
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Configuration
HOOK_DIR = Path(__file__).resolve().parent
STATE_DIR = HOOK_DIR / "state"

# Pattern to detect corrupted package names (shell metacharacters)
CORRUPTED_PATTERN = re.compile(r'["\'`\\]+')


def is_corrupted_package_name(package: str) -> bool:
    """Check if package name contains shell metacharacters.

    Args:
        package: Package name to check

    Returns:
        True if package contains corrupted characters, False otherwise
    """
    # Check if package name has trailing/leading quotes, backticks, or backslashes
    if package != package.strip('"\'`\\'):
        return True

    # Check for embedded metacharacters
    if CORRUPTED_PATTERN.search(package):
        return True

    return False


def cleanup_state_file(state_file: Path) -> dict:
    """Clean up corrupted package entries from a state file.

    Args:
        state_file: Path to state file

    Returns:
        Dict with cleanup statistics
    """
    stats = {
        "file": str(state_file),
        "total_entries": 0,
        "corrupted_entries": 0,
        "cleaned_entries": 0,
        "skipped_entries": 0,
    }

    if not state_file.exists():
        return stats

    try:
        with open(state_file, encoding='utf-8') as f:
            state = json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupted state file - skip
        return stats

    verified = state.get("verified_packages", {})
    stats["total_entries"] = len(verified)

    # Filter out corrupted entries
    clean_packages = {}
    for package, timestamp in verified.items():
        if is_corrupted_package_name(package):
            stats["corrupted_entries"] += 1
            # Skip corrupted entry (don't copy to clean_packages)
            stats["cleaned_entries"] += 1
            logger.info(f"Removing corrupted package: {package!r}")
        else:
            # Keep clean entry
            clean_packages[package] = timestamp
            stats["skipped_entries"] += 1

    # Update state file
    if stats["cleaned_entries"] > 0:
        state["verified_packages"] = clean_packages

        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)

            logger.info(f"Cleaned {stats['cleaned_entries']} corrupted entries from {state_file.name}")
        except OSError:
            logger.error(f"Failed to write cleaned state to {state_file.name}")

    return stats


def cleanup_old_state_files(max_age_hours: int = 1) -> list[Path]:
    """Remove old verification state files.

    Args:
        max_age_hours: Maximum age in hours before removing state file

    Returns:
        List of removed file paths
    """
    removed_files = []
    cutoff_time = time.time() - (max_age_hours * 3600)

    for state_file in STATE_DIR.glob("dependency_verification_*.json"):
        try:
            mtime = state_file.stat().st_mtime
            if mtime < cutoff_time:
                state_file.unlink()
                removed_files.append(state_file)
                logger.info(f"Removed old state file: {state_file.name}")
        except OSError:
            continue

    return removed_files


def main() -> None:
    """Main cleanup function."""
    import sys

    # Parse arguments
    dry_run = "--dry-run" in sys.argv
    remove_old = "--remove-old" in sys.argv

    print("Dependency Verification State Cleanup")
    print("=" * 50)

    # Clean up corrupted entries
    print("\nCleaning corrupted package names...")
    total_cleaned = 0
    total_corrupted = 0

    for state_file in STATE_DIR.glob("dependency_verification_*.json"):
        stats = cleanup_state_file(state_file)

        if stats["corrupted_entries"] > 0:
            print(f"\n{stats['file']}:")
            print(f"  Total entries: {stats['total_entries']}")
            print(f"  Corrupted: {stats['corrupted_entries']}")
            print(f"  Cleaned: {stats['cleaned_entries']}")
            print(f"  Kept: {stats['skipped_entries']}")

            total_cleaned += stats["cleaned_entries"]
            total_corrupted += stats["corrupted_entries"]

    print(f"\n✅ Cleaned {total_cleaned} corrupted entries from {total_corrupted} total corrupted entries")

    # Remove old state files
    if remove_old:
        print("\nRemoving old state files (older than 1 hour)...")
        removed_files = cleanup_old_state_files()
        print(f"✅ Removed {len(removed_files)} old state file(s)")

    print("\nCleanup complete!")


if __name__ == "__main__":
    main()
