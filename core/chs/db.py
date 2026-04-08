"""CHS v2 Database Functions - Connection management and initialization.

Provides database connection with WAL mode, schema initialization,
and embeddings configuration management.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(db_path: Path | str) -> sqlite3.Connection:
    """Get a SQLite database connection with optimized settings.

    Enables WAL mode for concurrent access and sets cache size for
    better performance. Creates parent directories if needed.

    Args:
        db_path: Path to SQLite database file or ':memory:' string

    Returns:
        sqlite3.Connection: Configured database connection
    """
    if isinstance(db_path, str) and db_path != ":memory:":
        db_path = Path(db_path)
    if isinstance(db_path, Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA cache_size=-64000;")
    return conn


def init_db(db_path: Path | str) -> None:
    """Initialize the database schema from schema.sql.

    Creates all tables, indexes, and triggers. Safe to call multiple
    times (idempotent) - uses IF NOT EXISTS throughout schema.

    Args:
        db_path: Path to SQLite database file or ':memory:'
    """
    schema_sql = _SCHEMA_PATH.read_text()
    conn = get_connection(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


def load_embeddings_config(db_path: Path | str) -> dict | None:
    """Load the active embeddings configuration.

    Returns the most recently created embeddings config entry
    that is marked as active.

    Args:
        db_path: Path to SQLite database file

    Returns:
        dict with keys 'model_name' and 'embedding_dim', or None if no config
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT model_name, embedding_dim\n               FROM embeddings_config\n               WHERE is_active = 1\n               ORDER BY id DESC\n               LIMIT 1"
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {"model_name": row[0], "embedding_dim": row[1]}
    finally:
        conn.close()


def set_embeddings_config(db_path: Path | str, model_name: str, embedding_dim: int) -> None:
    """Set a new embeddings configuration and deactivate old configs.

    Creates a new embeddings_config entry marked as active and sets
    all existing entries to inactive.

    Args:
        db_path: Path to SQLite database file
        model_name: Name of the embedding model
        embedding_dim: Dimension count for embeddings
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE embeddings_config\n               SET is_active = 0\n               WHERE is_active = 1"
        )
        cursor.execute(
            "INSERT INTO embeddings_config (model_name, embedding_dim, is_active)\n               VALUES (?, ?, 1)",
            (model_name, embedding_dim),
        )
        conn.commit()
    finally:
        conn.close()
