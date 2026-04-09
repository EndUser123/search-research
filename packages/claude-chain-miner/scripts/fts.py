"""FTS5 indexer for ClaudeChainMiner — full-text search over session chain exports."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

from scripts.walker import get_chain_for_slug
from scripts.exporter import export_chain, _EXPORTS_DIR

DEFAULT_DB = _EXPORTS_DIR / "fts-chain.db"


def _get_default_db() -> Path:
    _EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_DB


def init_db(db_path: Path | str) -> sqlite3.Connection:
    """Initialize FTS5 virtual table."""
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """CREATE VIRTUAL TABLE IF NOT EXISTS sessions USING fts5(
            session_id UNINDEXED,
            path UNINDEXED,
            content,
            metadata
        )"""
    )
    conn.commit()
    return conn


def index_chain(slug: str, db_path: Path | str | None = None) -> int:
    """Walk the chain, export sessions, and index them into FTS5.

    Args:
        slug: Terminal slug
        db_path: Path to SQLite FTS5 database (default: exports/fts-chain.db)

    Returns:
        Number of sessions indexed
    """
    if db_path is None:
        db_path = _get_default_db()
    else:
        db_path = Path(db_path)

    chain, origin = get_chain_for_slug(slug)
    if not chain:
        return 0

    session_ids = [e.session_id for e in chain]
    exported = export_chain(session_ids)

    conn = init_db(db_path)
    indexed = 0

    for ep in exported:
        try:
            content = ep.read_text(encoding="utf-8")
        except OSError:
            continue

        session_id = ep.stem.replace("session_", "")
        conn.execute(
            "INSERT INTO sessions (session_id, path, content, metadata) VALUES (?, ?, ?, ?)",
            (session_id, str(ep), content, ""),
        )
        indexed += 1

    conn.commit()
    conn.close()
    return indexed


def fts_mine(
    query: str,
    slug: str | None = None,
    db_path: Path | str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Query the FTS5 index.

    Args:
        query: FTS5 query string
        slug: Optional slug to filter results
        db_path: Path to SQLite FTS5 database (default: exports/fts-chain.db)
        limit: Maximum results to return

    Returns:
        List of matching session dicts with session_id, path, snippet
    """
    if db_path is None:
        db_path = _get_default_db()
    else:
        db_path = Path(db_path)

    if not Path(db_path).exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    if slug:
        chain, _ = get_chain_for_slug(slug)
        allowed_ids = {e.session_id for e in chain}
        results = []
        for row in conn.execute(
            "SELECT session_id, path, snippet(sessions, 2, '<<', '>>', '...', 20) AS snippet FROM sessions WHERE sessions MATCH ? ORDER BY rank LIMIT ?",
            (query, limit * 2),
        ):
            if row["session_id"] in allowed_ids:
                results.append(dict(row))
                if len(results) >= limit:
                    break
        conn.close()
        return results

    rows = conn.execute(
        "SELECT session_id, path, snippet(sessions, 2, '<<', '>>', '...', 20) AS snippet FROM sessions WHERE sessions MATCH ? ORDER BY rank LIMIT ?",
        (query, limit),
    )
    results = [dict(row) for row in rows]
    conn.close()
    return results
