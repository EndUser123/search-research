"""Tests for FTS5 indexer."""

import pytest
import sqlite3
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.fts import init_db, index_chain, fts_mine, _EXPORTS_DIR


def test_init_db_creates_table(tmp_path):
    """init_db creates the FTS5 virtual table."""
    db = tmp_path / "test.db"
    conn = init_db(db)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    assert "sessions" in tables
    conn.close()


def test_init_db_is_idempotent(tmp_path):
    """Second init_db call does not raise."""
    db = tmp_path / "test.db"
    conn1 = init_db(db)
    conn2 = init_db(db)
    conn1.close()
    conn2.close()

