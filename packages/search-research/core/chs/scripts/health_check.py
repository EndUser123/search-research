"""CHS v2 Health Check CLI.

Check database health including table counts, embedding coverage,
last indexed timestamp, and recent session information.

Usage:
    python -m core.chs.scripts.health_check
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path


def format_timestamp(ts: int | None) -> str:
    """Format Unix timestamp as human-readable string.

    Args:
        ts: Unix timestamp or None

    Returns:
        Formatted datetime string or "N/A"
    """
    if ts is None:
        return "N/A"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def main() -> int:
    """Health check main entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(description="Check CHS v2 system health")
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to database file (default: from CHS_DB_PATH env var or P:\\\\__csf/data/chat_history.db)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()
    if args.db_path:
        db_path = Path(args.db_path).expanduser()
    else:
        import os

        db_path = Path(os.getenv("CHS_DB_PATH", "P:\\\\__csf/data/chat_history.db")).expanduser()
    try:
        from core.chs.db import database_is_initialized, get_connection

        if not db_path.exists():
            print(f"ERROR: Database does not exist: {db_path}", file=sys.stderr)
            return 1
        if not database_is_initialized(db_path):
            print(f"ERROR: Database exists but CHS schema is not initialized: {db_path}", file=sys.stderr)
            print(
                "Run: python -m core.chs.scripts.reindex_from_jsonl",
                file=sys.stderr,
            )
            return 1
        conn = get_connection(db_path)
        health_data = {}
        tables = ["projects", "sessions", "messages", "turns", "topics"]
        for table in tables:
            try:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                health_data[table] = count
            except Exception:
                health_data[table] = 0
        try:
            cursor = conn.execute(
                "\n                SELECT COUNT(*) as total,\n                       SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as embedded\n                FROM turns\n            "
            )
            row = cursor.fetchone()
            if row and row[0] > 0:
                total, embedded = row
                health_data["embedding_coverage"] = {
                    "total": total,
                    "embedded": embedded,
                    "percentage": round(100 * embedded / total, 1) if total > 0 else 0,
                }
            else:
                health_data["embedding_coverage"] = {"total": 0, "embedded": 0, "percentage": 0}
        except Exception:
            health_data["embedding_coverage"] = {"total": 0, "embedded": 0, "percentage": 0}
        try:
            cursor = conn.execute(
                "\n                SELECT MAX(last_indexed_at) FROM indexer_checkpoints\n            "
            )
            row = cursor.fetchone()
            health_data["last_indexed_at"] = row[0] if row and row[0] else None
        except Exception:
            health_data["last_indexed_at"] = None
        try:
            cursor = conn.execute(
                "\n                SELECT id, started_at, message_count\n                FROM sessions\n                ORDER BY started_at DESC\n                LIMIT 1\n            "
            )
            row = cursor.fetchone()
            if row:
                health_data["recent_session"] = {
                    "id": row[0],
                    "started_at": row[1],
                    "message_count": row[2],
                }
            else:
                health_data["recent_session"] = None
        except Exception:
            health_data["recent_session"] = None
        conn.close()
        if args.json:
            import json

            print(json.dumps(health_data, indent=2, default=str))
        else:
            print("=" * 60)
            print("Chat History Search v2 - Health Check")
            print("=" * 60)
            print(f"\nDatabase: {db_path}\n")
            print("Table Counts:")
            for table in tables:
                count = health_data.get(table, 0)
                print(f"  {table:20} {count:>10,}")
            coverage = health_data.get("embedding_coverage", {})
            if coverage.get("total", 0) > 0:
                total = coverage["total"]
                embedded = coverage["embedded"]
                percentage = coverage["percentage"]
                print(f"\nEmbedding Coverage: {embedded}/{total} ({percentage}%)")
            last_indexed = health_data.get("last_indexed_at")
            if last_indexed:
                print(f"\nLast Indexed: {format_timestamp(last_indexed)}")
            recent = health_data.get("recent_session")
            if recent:
                print("\nRecent Session:")
                print(f"  ID: {recent['id']}")
                print(f"  Started: {format_timestamp(recent['started_at'])}")
                print(f"  Messages: {recent['message_count']}")
            print("\n" + "=" * 60)
            print("OK")
            print("=" * 60)
        return 0
    except Exception as e:
        print(f"ERROR: Health check failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
