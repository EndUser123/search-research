#!/usr/bin/env python3
"""CKS Quality Statistics Module.

Provides data quality insights for archival decisions and system health.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root for imports
project_root = Path(__file__).parent.parent.parent


@dataclass
class QualityStats:
    """Quality statistics for CKS data."""

    total_entries: int = 0
    database_size_mb: float = 0.0

    # Distribution stats
    usage_distribution: dict[str, int] = field(default_factory=dict)
    feedback_distribution: dict[str, int] = field(default_factory=dict)
    age_distribution: dict[str, int] = field(default_factory=dict)
    type_distribution: dict[str, int] = field(default_factory=dict)

    # Archival candidates
    archive_candidates_high_confidence: int = 0
    archive_candidates_medium_confidence: int = 0
    archive_candidates_low_confidence: int = 0

    # Quality issues
    zero_usage_entries: int = 0
    negative_feedback_entries: int = 0
    orphaned_entries: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_entries": self.total_entries,
            "database_size_mb": round(self.database_size_mb, 2),
            "usage_distribution": self.usage_distribution,
            "feedback_distribution": self.feedback_distribution,
            "age_distribution": self.age_distribution,
            "type_distribution": self.type_distribution,
            "archive_candidates": {
                "high_confidence": self.archive_candidates_high_confidence,
                "medium_confidence": self.archive_candidates_medium_confidence,
                "low_confidence": self.archive_candidates_low_confidence,
            },
            "quality_issues": {
                "zero_usage": self.zero_usage_entries,
                "negative_feedback": self.negative_feedback_entries,
                "orphaned": self.orphaned_entries,
            },
        }


def calculate_decay_score(entry: dict[str, Any]) -> float:
    """Calculate decay score (0.0 = fresh, 1.0 = stale).

    Combines age, usage, success rate, and feedback signals.
    """
    created_at = entry.get("created_at", "")
    if isinstance(created_at, str):
        try:
            created_dt = datetime.fromisoformat(created_at.replace(" ", "T"))
        except Exception:
            created_dt = datetime.now()
    else:
        created_dt = datetime.now()

    days_old = (datetime.now() - created_dt).days / 365  # normalized to years

    # Temporal factor (max 0.4)
    temporal = min(0.4, days_old * 0.1)

    # Usage factor (never used = 0.3 staleness penalty)
    usage_count = entry.get("usage_count", 0) or 0
    usage_factor = 0.3 if usage_count == 0 else 0.0

    # Success rate penalty
    total_usage = usage_count
    if total_usage > 0:
        success_count = entry.get("success_count", 0) or 0
        success_rate = success_count / total_usage
        success_penalty = max(0, (0.5 - success_rate) * 0.2)
    else:
        success_penalty = 0.1

    # Explicit feedback penalty
    thumbs_up = entry.get("thumbs_up", 0) or 0
    thumbs_down = entry.get("thumbs_down", 0) or 0
    total_feedback = thumbs_up + thumbs_down
    if total_feedback > 0:
        feedback_score = thumbs_down / total_feedback
        feedback_penalty = feedback_score * 0.2
    else:
        feedback_penalty = 0.0

    return min(1.0, temporal + usage_factor + success_penalty + feedback_penalty)


def get_quality_statistics(db_path: str | Path = "P:/__csf/data/cks.db") -> QualityStats:
    """Calculate comprehensive quality statistics for CKS database.

    Args:
        db_path: Path to CKS database

    Returns:
        QualityStats object with all statistics

    """
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"CKS database not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    stats = QualityStats()

    # Database size
    stats.database_size_mb = db_path.stat().st_size / (1024 * 1024)

    # Total entries
    cursor.execute("SELECT COUNT(*) as count FROM entries")
    stats.total_entries = cursor.fetchone()["count"]

    # Usage distribution
    cursor.execute("""
        SELECT
            CASE
                WHEN usage_count = 0 THEN 'never_used'
                WHEN usage_count <= 5 THEN 'rarely_used'
                WHEN usage_count <= 20 THEN 'moderately_used'
                ELSE 'frequently_used'
            END as usage_tier,
            COUNT(*) as count
        FROM entries
        GROUP BY usage_tier
    """)
    stats.usage_distribution = {row["usage_tier"]: row["count"] for row in cursor.fetchall()}

    # Feedback distribution
    cursor.execute("""
        SELECT
            CASE
                WHEN thumbs_down > thumbs_up THEN 'negative'
                WHEN thumbs_up > thumbs_down THEN 'positive'
                ELSE 'neutral'
            END as feedback_tier,
            COUNT(*) as count
        FROM entries
        GROUP BY feedback_tier
    """)
    stats.feedback_distribution = {row["feedback_tier"]: row["count"] for row in cursor.fetchall()}

    # Age distribution
    cursor.execute("""
        SELECT
            CASE
                WHEN created_at < datetime('now', '-90 days') THEN 'old'
                WHEN created_at < datetime('now', '-30 days') THEN 'mature'
                ELSE 'recent'
            END as age_tier,
            COUNT(*) as count
        FROM entries
        GROUP BY age_tier
    """)
    stats.age_distribution = {row["age_tier"]: row["count"] for row in cursor.fetchall()}

    # Type distribution
    cursor.execute("""
        SELECT type, COUNT(*) as count
        FROM entries
        GROUP BY type
        ORDER BY count DESC
    """)
    stats.type_distribution = {row["type"]: row["count"] for row in cursor.fetchall()}

    # Zero usage entries
    cursor.execute(
        "SELECT COUNT(*) as count FROM entries WHERE usage_count = 0 OR usage_count IS NULL",
    )
    stats.zero_usage_entries = cursor.fetchone()["count"]

    # Negative feedback entries
    cursor.execute("SELECT COUNT(*) as count FROM entries WHERE thumbs_down > COALESCE(thumbs_up, 0)")
    stats.negative_feedback_entries = cursor.fetchone()["count"]

    # High confidence archival candidates (90+ days old, never used, 2+ downvotes)
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM entries
        WHERE created_at < datetime('now', '-90 days')
          AND (usage_count = 0 OR usage_count IS NULL)
          AND (thumbs_down >= 2 OR thumbs_down IS NULL)
    """)
    stats.archive_candidates_high_confidence = cursor.fetchone()["count"]

    # Medium confidence archival candidates (180+ days old, never used, no upvotes)
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM entries
        WHERE created_at < datetime('now', '-180 days')
          AND (usage_count = 0 OR usage_count IS NULL)
          AND (thumbs_up = 0 OR thumbs_up IS NULL)
    """)
    stats.archive_candidates_medium_confidence = cursor.fetchone()["count"]

    # Low confidence archival candidates (5+ downvotes, 2x more down than up)
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM entries
        WHERE (thumbs_down >= 5 OR thumbs_down IS NULL)
          AND (thumbs_up * 2 < thumbs_down OR thumbs_up IS NULL)
    """)
    stats.archive_candidates_low_confidence = cursor.fetchone()["count"]

    conn.close()

    return stats


def format_stats_terminal(stats: QualityStats) -> str:
    """Format quality statistics for terminal display."""
    lines = [
        "╔═══════════════════════════════════════════════════════════════════╗",
        "║                  CKS Data Quality Statistics                        ║",
        "╚═══════════════════════════════════════════════════════════════════╝",
        "",
        "📊 Database Overview",
        f"   Total Entries:     {stats.total_entries:,}",
        f"   Database Size:      {stats.database_size_mb:.1f} MB",
        "",
        "📈 Usage Distribution",
    ]

    # Usage distribution
    for tier, label in [
        ("never_used", "Never used"),
        ("rarely_used", "Rarely used (1-5)"),
        ("moderately_used", "Moderately (6-20)"),
        ("frequently_used", "Frequently (20+)"),
    ]:
        count = stats.usage_distribution.get(tier, 0)
        pct = count / stats.total_entries * 100 if stats.total_entries > 0 else 0
        bar = "█" * int(pct / 5)
        lines.append(f"   {label:20} {count:6,}  {pct:5.1f}%  {bar}")

    lines.extend(
        [
            "",
            "👍 Feedback Distribution",
        ],
    )

    # Feedback distribution
    sum(stats.feedback_distribution.values())
    for tier, label in [("positive", "Positive"), ("neutral", "Neutral"), ("negative", "Negative")]:
        count = stats.feedback_distribution.get(tier, 0)
        pct = count / stats.total_entries * 100 if stats.total_entries > 0 else 0
        bar = "█" * int(pct / 5)
        emoji = {"positive": "👍", "neutral": "😐", "negative": "👎"}[tier]
        lines.append(f"   {emoji} {label:12} {count:6,}  {pct:5.1f}%  {bar}")

    lines.extend(
        [
            "",
            "📅 Age Distribution",
        ],
    )

    # Age distribution
    for tier, label in [("recent", "< 30 days"), ("mature", "30-90 days"), ("old", "> 90 days")]:
        count = stats.age_distribution.get(tier, 0)
        pct = count / stats.total_entries * 100 if stats.total_entries > 0 else 0
        bar = "█" * int(pct / 5)
        lines.append(f"   {label:15} {count:6,}  {pct:5.1f}%  {bar}")

    lines.extend(
        [
            "",
            "📦 Entry Types",
        ],
    )

    # Type distribution
    for entry_type, count in sorted(stats.type_distribution.items(), key=lambda x: -x[1]):
        pct = count / stats.total_entries * 100 if stats.total_entries > 0 else 0
        lines.append(f"   {entry_type:20} {count:6,}  {pct:5.1f}%")

    lines.extend(
        [
            "",
            "🔍 Quality Issues",
            f"   Zero usage entries:      {stats.zero_usage_entries:,}",
            f"   Negative feedback entries: {stats.negative_feedback_entries:,}",
            "",
            "📦 Archival Candidates",
            f"   🔴 High confidence:   {stats.archive_candidates_high_confidence:,}",
            f"   🟡 Medium confidence: {stats.archive_candidates_medium_confidence:,}",
            f"   🟢 Low confidence:    {stats.archive_candidates_low_confidence:,}",
            "",
            f"   Total candidates:     {stats.archive_candidates_high_confidence + stats.archive_candidates_medium_confidence + stats.archive_candidates_low_confidence:,}",
            "",
            "💡 Run '/cks quality sample' to see example candidates",
        ],
    )

    return "\n".join(lines)


def sample_archival_candidates(
    db_path: str | Path = "P:/__csf/data/cks.db", limit: int = 10,
) -> list[dict]:
    """Sample entries that would be archived."""
    db_path = Path(db_path)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get sample candidates
    cursor.execute(
        """
        SELECT
            id, type, title, created_at,
            usage_count, thumbs_up, thumbs_down,
            LENGTH(content) as content_length
        FROM entries
        WHERE created_at < datetime('now', '-90 days')
          AND (usage_count = 0 OR usage_count IS NULL)
        ORDER BY created_at ASC
        LIMIT ?
    """,
        (limit,),
    )

    candidates = []
    for row in cursor.fetchall():
        entry = dict(row)
        entry["decay_score"] = calculate_decay_score(entry)
        candidates.append(entry)

    conn.close()
    return candidates


def main() -> None:
    """CLI entry point for quality statistics."""
    parser = argparse.ArgumentParser(
        description="CKS Quality Statistics - Analyze data quality and archival candidates",
    )

    parser.add_argument(
        "--db-path",
        type=str,
        default="P:/__csf/data/cks.db",
        help="Path to CKS database",
    )

    parser.add_argument(
        "--format",
        choices=["terminal", "json", "markdown"],
        default="terminal",
        help="Output format",
    )

    parser.add_argument(
        "--sample",
        type=int,
        metavar="N",
        help="Show N sample archival candidates",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (shorthand for --format json)",
    )

    args = parser.parse_args()

    if args.json:
        args.format = "json"

    try:
        # Get statistics
        stats = get_quality_statistics(args.db_path)

        if args.format == "json":
            print(json.dumps(stats.to_dict(), indent=2, default=str))

        elif args.format == "markdown":
            print("# CKS Quality Statistics\n")
            print(f"**Total Entries**: {stats.total_entries:,}")
            print(f"**Database Size**: {stats.database_size_mb:.1f} MB\n")
            print("## Usage Distribution\n")
            for tier, label in [
                ("never_used", "Never used"),
                ("rarely_used", "Rarely used (1-5)"),
                ("moderately_used", "Moderately (6-20)"),
                ("frequently_used", "Frequently (20+)"),
            ]:
                count = stats.usage_distribution.get(tier, 0)
                pct = count / stats.total_entries * 100 if stats.total_entries > 0 else 0
                print(f"- **{label}**: {count:,} ({pct:.1f}%)")
            print("\n## Archival Candidates\n")
            print(f"- High confidence: {stats.archive_candidates_high_confidence:,}")
            print(f"- Medium confidence: {stats.archive_candidates_medium_confidence:,}")
            print(f"- Low confidence: {stats.archive_candidates_low_confidence:,}")

        else:  # terminal
            print(format_stats_terminal(stats))

        # Show samples if requested
        if args.sample:
            print("\n" + "─" * 70)
            print(f"\n📋 Sample Archival Candidates (showing {args.sample})\n")
            candidates = sample_archival_candidates(args.db_path, args.sample)

            for i, entry in enumerate(candidates, 1):
                created = entry.get("created_at", "unknown")[:10]
                decay = entry.get("decay_score", 0)
                usage = entry.get("usage_count", 0)
                down = entry.get("thumbs_down", 0)
                title = entry.get("title", "")[:60]

                print(f"{i}. [{entry['type']}] {title}")
                print(
                    f"   Created: {created}  |  Decay: {decay:.2f}  |  Usage: {usage}  |  Down: {down}",
                )
                print()

    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
