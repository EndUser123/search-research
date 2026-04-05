#!/usr/bin/env python3
"""
Log Rotation CLI Command

Manual trigger for diagnostic log rotation.

Usage:
    python P:/.claude/hooks/rotate_logs.py [retention_days]

Default retention: 30 days
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add hooks to path
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))


def main() -> None:
    """Run log rotation manually."""
    # Parse retention days from command line
    retention_days = 30  # default
    if len(sys.argv) > 1:
        try:
            retention_days = int(sys.argv[1])
        except ValueError:
            print(f"Invalid retention days: {sys.argv[1]}")
            print("Usage: python rotate_logs.py [retention_days]")
            sys.exit(1)

    # Import and run rotation
    from __lib.log_rotation import rotate_diagnostic_logs

    print(f"Rotating diagnostic logs (retention: {retention_days} days)...")
    stats = rotate_diagnostic_logs(retention_days=retention_days)

    print("\nRotation complete:")
    print(f"  Total logs processed: {stats['total_logs_rotated']}")
    print(f"  Compressed: {stats['compressed']}")
    print(f"  Deleted: {stats['deleted']}")
    print(f"  Truncated: {stats['truncated']}")
    print(f"  Errors: {stats['errors']}")


if __name__ == "__main__":
    main()
