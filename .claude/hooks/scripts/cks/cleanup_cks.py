#!/usr/bin/env python3
"""
Cleanup CKS - Remove low-quality entries to maintain signal quality

This script identifies and optionally removes low-quality CKS entries that
don't provide useful knowledge (noise reduction).
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path


def calculate_entry_quality(entry: dict) -> float:
    """Calculate quality score for a CKS entry (0.0 to 1.0) based on metadata quality."""
    score = 0.0

    # Factor 1: Content size (max 0.4) - INCREASED from 0.3
    content_length = len(entry.get("content", ""))
    if content_length > 500:
        score += 0.4
    elif content_length > 200:
        score += 0.3
    elif content_length > 100:
        score += 0.15

    # Factor 2: Metadata richness (max 0.5) - RESTRUCTURED from 0.6
    metadata = entry.get("metadata", {})
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except (json.JSONDecodeError, TypeError):
            metadata = {}

    if metadata:
        score += 0.2  # Has metadata (base)

        # High-value signals
        if isinstance(metadata, dict) and metadata.get("work_type") and metadata.get("work_type") != "unknown":
            score += 0.15  # Known work type (reduced from 0.2)

        if isinstance(metadata, dict) and metadata.get("problem") and metadata.get("problem") != "Not specified":
            score += 0.15  # Problem context (reduced from 0.2)

    # Factor 3: Title quality (max 0.1)
    title = entry.get("title", "")
    if title and len(title) > 10:
        score += 0.1

    # NO TEMPORAL DECAY - time doesn't reduce knowledge value
    # Old high-quality content (patterns, corrections) remains valuable

    return min(score, 1.0)


def find_low_quality_entries(min_quality: float = 0.3, days: int = 30) -> list:
    """Find low-quality CKS entries below threshold."""
    cks_db = Path("P:/__csf/data/cks.db")

    if not cks_db.exists():
        return []

    try:
        conn = sqlite3.connect(str(cks_db))
        cursor = conn.cursor()

        # Calculate date threshold
        threshold = (datetime.now() - timedelta(days=days)).isoformat()

        # Get all entries from period
        cursor.execute("""
            SELECT id, title, content, metadata, created_at
            FROM entries
            WHERE created_at >= ?
            ORDER BY created_at DESC
        """, (threshold,))

        entries = []
        for row in cursor.fetchall():
            entry = {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "metadata": row[3],
                "created_at": row[4],
            }
            quality = calculate_entry_quality(entry)
            if quality < min_quality:
                entry["quality"] = quality
                entries.append(entry)

        conn.close()
        return entries

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return []


def delete_entries(entry_ids: list) -> int:
    """Delete entries by IDs. Returns count of deleted entries."""
    if not entry_ids:
        return 0

    cks_db = Path("P:/__csf/data/cks.db")
    if not cks_db.exists():
        return 0

    try:
        conn = sqlite3.connect(str(cks_db))
        cursor = conn.cursor()

        placeholders = ",".join("?" * len(entry_ids))
        cursor.execute(f"""
            DELETE FROM entries
            WHERE id IN ({placeholders})
        """, entry_ids)

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted

    except Exception as e:
        print(f"Error deleting entries: {e}", file=sys.stderr)
        return 0


def print_cleanup_report(entries: list, min_quality: float) -> None:
    """Print cleanup report."""
    if not entries:
        print("✅ No low-quality entries found")
        return

    print(f"🧹 Found {len(entries)} low-quality entries (quality < {min_quality})")
    print("=" * 80)
    print()

    # Group by quality range
    very_low = [e for e in entries if e["quality"] < 0.1]
    low = [e for e in entries if 0.1 <= e["quality"] < 0.2]
    marginal = [e for e in entries if 0.2 <= e["quality"] < min_quality]

    if very_low:
        print(f"❌ Very Low Quality (<0.1): {len(very_low)} entries")
        for entry in very_low[:5]:
            print(f"  • {entry['title'][:60]}... (Q:{entry['quality']:.2f})")
        if len(very_low) > 5:
            print(f"  ... and {len(very_low) - 5} more")
        print()

    if low:
        print(f"⚠️  Low Quality (0.1-0.2): {len(low)} entries")
        for entry in low[:5]:
            print(f"  • {entry['title'][:60]}... (Q:{entry['quality']:.2f})")
        if len(low) > 5:
            print(f"  ... and {len(low) - 5} more")
        print()

    if marginal:
        print(f"📊 Marginal Quality (0.2-{min_quality}): {len(marginal)} entries")
        for entry in marginal[:5]:
            print(f"  • {entry['title'][:60]}... (Q:{entry['quality']:.2f})")
        if len(marginal) > 5:
            print(f"  ... and {len(marginal) - 5} more")
        print()


def main():
    parser = argparse.ArgumentParser(description="Cleanup low-quality CKS entries")
    parser.add_argument(
        "--min-quality",
        type=float,
        default=0.3,
        help="Minimum quality score (default: 0.3)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Look back period in days (default: 30)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting"
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete low-quality entries"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    args = parser.parse_args()

    entries = find_low_quality_entries(min_quality=args.min_quality, days=args.days)

    if args.json:
        print(json.dumps(entries, indent=2))
    else:
        print_cleanup_report(entries, args.min_quality)

    if args.delete and not args.dry_run:
        if entries:
            entry_ids = [e["id"] for e in entries]
            deleted = delete_entries(entry_ids)
            print()
            print(f"🗑️  Deleted {deleted} low-quality entries")
        else:
            print("✅ No entries to delete")
    elif args.dry_run:
        print()
        print(f"🔍 Dry run mode: Would delete {len(entries)} entries")
        print("   Use --delete to actually remove them")


if __name__ == "__main__":
    main()
