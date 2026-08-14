"""Tests for core.chs.scripts.backfill_embeddings.

Updated for the run-provenance contract: backfill() returns a dict
(run_id, updated, source_digest, manifest_path, model, dim) instead of an int.
Deeper provenance coverage lives in core/chs/tests/test_backfill_run_provenance.py.
"""

import pytest
import sqlite3
from unittest.mock import patch, MagicMock
import numpy as np

from core.chs.scripts.backfill_embeddings import DEFAULT_EMBEDDING_DIM, backfill


def _mock_embedding() -> bytes:
    """Create a valid float32 embedding as bytes for use in mocks."""
    return np.zeros(DEFAULT_EMBEDDING_DIM, dtype=np.float32).tobytes()


@pytest.fixture
def mem_conn():
    """In-memory connection with minimal schema."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE sessions (id INTEGER PRIMARY KEY, embedding BLOB, summary_short TEXT, first_prompt TEXT, embedding_model TEXT, embedding_dim INTEGER)")
    conn.execute("INSERT INTO sessions (id, summary_short) VALUES (1, 'test session')")
    conn.execute("INSERT INTO sessions (id, summary_short) VALUES (2, NULL)")
    conn.execute("INSERT INTO sessions (id, summary_short, embedding) VALUES (3, 'already has embedding', 'x')")
    conn.commit()
    return conn


class _NoCloseConn:
    """Proxy that ignores close(): backfill() closes its connection, but the
    test must inspect the same :memory: DB afterwards."""

    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def close(self):
        pass


def _run_backfill(mem_conn, mock_embed, **kwargs):
    proxy = _NoCloseConn(mem_conn)
    with patch("core.chs.scripts.backfill_embeddings.get_connection", return_value=proxy):
        with patch("core.chs.scripts.backfill_embeddings.get_embed_client", return_value=mock_embed):
            return backfill(":memory:", **kwargs)


def test_backfill_counts_pending(mem_conn):
    """backfill --dry-run counts sessions needing embeddings."""
    mock_embed = MagicMock()
    mock_embed.embed_texts.return_value = [_mock_embedding()]
    result = _run_backfill(mem_conn, mock_embed, dry_run=True)
    assert result["updated"] == 1  # only session 1 has text and no embedding
    assert result["run_id"] is None


def test_backfill_skips_null_text(mem_conn):
    """Sessions with NULL text are skipped."""
    mock_embed = MagicMock()
    mock_embed.embed_texts.return_value = [_mock_embedding()]
    result = _run_backfill(mem_conn, mock_embed, dry_run=True)
    assert result["updated"] == 1  # id=2 has NULL text, skipped


def test_backfill_skips_existing_embedding(mem_conn):
    """Sessions already with embedding are skipped."""
    mock_embed = MagicMock()
    mock_embed.embed_texts.return_value = [_mock_embedding()]
    result = _run_backfill(mem_conn, mock_embed, dry_run=True)
    assert result["updated"] == 1  # id=3 already has embedding, excluded by WHERE


def test_backfill_writes_embedding(mem_conn):
    """backfill writes embedding BLOB and run provenance when not dry_run."""
    mock_embed = MagicMock()
    mock_embed.embed_texts.return_value = [_mock_embedding()]
    result = _run_backfill(mem_conn, mock_embed, dry_run=False)
    assert result["updated"] == 1
    assert result["run_id"]

    row = mem_conn.execute(
        "SELECT embedding, embedding_run_id FROM sessions WHERE id = 1"
    ).fetchone()
    assert row[0] is not None
    assert row[1] == result["run_id"]


def test_backfill_rejects_dim_mismatch(mem_conn):
    """A vector of the wrong byte length must fail fast, not write."""
    mock_embed = MagicMock()
    mock_embed.embed_texts.return_value = [np.zeros(100, dtype=np.float32).tobytes()]
    with pytest.raises(ValueError, match="byte length"):
        _run_backfill(mem_conn, mock_embed, dry_run=False)
    row = mem_conn.execute("SELECT embedding FROM sessions WHERE id = 1").fetchone()
    assert row[0] is None  # rolled back
