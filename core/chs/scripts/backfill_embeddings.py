"""Backfill embeddings for sessions that lack them.

Usage:
    python -m core.chs.scripts.backfill_embeddings
    python -m core.chs.scripts.backfill_embeddings --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from .config import get_chs_db_path
from .db import get_connection
from .embeddings import get_embed_client


def backfill(db_path: str, dry_run: bool = False) -> int:
    """Backfill embeddings for sessions that lack them.

    Args:
        db_path: Path to the SQLite database
        dry_run: If True, count but don't write

    Returns:
        Number of sessions updated (or would be updated if dry_run)
    """
    conn = get_connection(db_path)
    embed_client = get_embed_client()

    cursor = conn.execute(
        "SELECT id, COALESCE(summary_short, first_prompt) AS text FROM sessions WHERE embedding IS NULL"
    )
    rows = cursor.fetchall()
    updated = 0
    for row_id, text in rows:
        if not text:
            continue
        embedding = embed_client.embed_texts([text])[0]
        if not dry_run:
            conn.execute(
                "UPDATE sessions SET embedding = ?, embedding_model = ?, embedding_dim = ? WHERE id = ?",
                (embedding, "all-MiniLM-L6-v2", 384, row_id),
            )
        updated += 1
    if not dry_run:
        conn.commit()
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill session embeddings")
    parser.add_argument("--dry-run", action="store_true", help="Count pending but don't write")
    parser.add_argument("--db", default=None, help="Path to database (default: from db config)")
    args = parser.parse_args()

    db_path = args.db or get_chs_db_path()
    updated = backfill(db_path, dry_run=args.dry_run)
    action = "Would update" if args.dry_run else "Updated"
    print(f"{action} {updated} sessions")


if __name__ == "__main__":
    main()
