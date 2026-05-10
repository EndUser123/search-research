#!/usr/bin/env python3
"""CKS Usage Tracking and Stale Entry Detection.

Provides utilities for:
- Detecting stale CKS entries (not accessed recently)
- Listing entries by last_accessed timestamp
- Manual pruning support (NO AUTO-PRUNING)

Environment Variables:
- CKS_STALE_DAYS: Days before entry is considered stale (default: 90)
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path("P:\\\\\\__csf").resolve()))

from search_research.contrib.semantic_daemon.daemon_client import DaemonClient

# Default stale threshold: 90 days
DEFAULT_STALE_DAYS = int(os.environ.get("CKS_STALE_DAYS", "90"))


def get_stale_entries(days: int | None = None, limit: int = 50) -> list[dict]:
    """Find CKS entries not accessed within the threshold.

    Args:
        days: Days before considering entry stale (default: CKS_STALE_DAYS env or 90)
        limit: Maximum entries to return

    Returns:
        List of stale entries with id, title, last_accessed, days_stale

    """
    if days is None:
        days = DEFAULT_STALE_DAYS

    threshold = datetime.now(UTC) - timedelta(days=days)
    stale_entries = []

    try:
        # Query CKS for all patterns (could add other types)
        daemon = DaemonClient(auto_start=False, enable_fallback=True)
        result = daemon.search("cks", "pattern lesson", limit=500)  # Broad query

        if result.get("status") != "success":
            return []

        entries = result.get("results", [])

        for entry in entries[:limit]:
            last_accessed = entry.get("metadata", {}).get("last_accessed")

            if not last_accessed:
                # No access timestamp = very stale
                created_at = entry.get("created_at", "")
                if created_at:
                    try:
                        created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        if created_dt < threshold:
                            stale_entries.append(
                                {
                                    "id": entry.get("id", "unknown"),
                                    "title": entry.get("title", "Untitled"),
                                    "last_accessed": "never",
                                    "days_stale": (datetime.now(UTC) - created_dt).days,
                                    "entry": entry,
                                },
                            )
                    except (ValueError, TypeError):
                        pass
                continue

            try:
                # Parse last_accessed timestamp
                last_accessed_dt = datetime.fromisoformat(last_accessed.replace("Z", "+00:00"))

                if last_accessed_dt < threshold:
                    days_stale = (datetime.now(UTC) - last_accessed_dt).days
                    stale_entries.append(
                        {
                            "id": entry.get("id", "unknown"),
                            "title": entry.get("title", "Untitled"),
                            "last_accessed": last_accessed,
                            "days_stale": days_stale,
                            "entry": entry,
                        },
                    )
            except (ValueError, TypeError):
                pass

        # Sort by days_stale (oldest first)
        stale_entries.sort(key=lambda e: e["days_stale"], reverse=True)

        return stale_entries

    except Exception:
        return []


def format_stale_report(stale_entries: list[dict]) -> str:
    """Format stale entries into a report for /garden cks."""
    if not stale_entries:
        return "✅ No stale entries found."

    lines = [
        f"🍂 Found {len(stale_entries)} stale entries ({DEFAULT_STALE_DAYS}+ days unused):",
        "",
    ]

    for i, entry in enumerate(stale_entries[:20], 1):  # Show top 20
        title = entry["title"][:50]
        last = entry["last_accessed"]
        days = entry["days_stale"]
        lines.append(f"{i}. [{days}d stale] {title}")
        lines.append(f"   Last: {last} | ID: {entry['id']}")

    if len(stale_entries) > 20:
        lines.append(f"\n... and {len(stale_entries) - 20} more")

    lines.append("")
    lines.append("To prune: `/cks delete <entry_id>` for each unwanted entry")
    lines.append("To review: `/search cks <topic>` to verify relevance")

    return "\n".join(lines)


def record_access(entry_ids: list[str]) -> None:
    """Update last_accessed timestamp for entries (future implementation).

    Args:
        entry_ids: List of entry IDs to update

    Note: This requires CKS backend support for metadata updates.
          Currently a no-op that documents the intent.

    """
    if not entry_ids:
        return

    # Future: Implement metadata update via CKS
    # For now, usage tracking is done on ingest only


if __name__ == "__main__":
    """CLI for stale entry detection."""
    import argparse

    parser = argparse.ArgumentParser(description="Detect stale CKS entries")
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_STALE_DAYS,
        help=f"Days before considering stale (default: {DEFAULT_STALE_DAYS})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum entries to return (default: 50)",
    )
    args = parser.parse_args()

    stale = get_stale_entries(days=args.days, limit=args.limit)
    print(format_stale_report(stale))
