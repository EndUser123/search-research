"""Tests for core.chs.scripts.backfill_embeddings."""

import pytest
import sqlite3
from unittest.mock import patch, MagicMock
import numpy as np

from core.chs.scripts.backfill_embeddings import backfill


def _mock_embedding() -> bytes:
    """Create a valid 384-dim float32 embedding as bytes for use in mocks."""
    return np.zeros(384, dtype=np.float32).tobytes()


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


def test_backfill_counts_pending(mem_conn):
    """backfill --dry-run counts sessions needing embeddings."""
    mock_embed = MagicMock()
    mock_embed.embed_texts.return_value = [_mock_embedding()]

    with patch("core.chs.scripts.backfill_embeddings.get_connection", return_value=mem_conn):
        with patch("core.chs.scripts.backfill_embeddings.get_embed_client", return_value=mock_embed):
            updated = backfill(":memory:", dry_run=True)
            assert updated == 1  # only session 1 has text and no embedding


def test_backfill_skips_null_text(mem_conn):
    """Sessions with NULL text are skipped."""
    mock_embed = MagicMock()
    mock_embed.embed_texts.return_value = [_mock_embedding()]

    with patch("core.chs.scripts.backfill_embeddings.get_connection", return_value=mem_conn):
        with patch("core.chs.scripts.backfill_embeddings.get_embed_client", return_value=mock_embed):
            updated = backfill(":memory:", dry_run=True)
            assert updated == 1  # id=2 has NULL text, skipped


def test_backfill_skips_existing_embedding(mem_conn):
    """Sessions already with embedding are skipped."""
    mock_embed = MagicMock()
    mock_embed.embed_texts.return_value = [_mock_embedding()]

    with patch("core.chs.scripts.backfill_embeddings.get_connection", return_value=mem_conn):
        with patch("core.chs.scripts.backfill_embeddings.get_embed_client", return_value=mock_embed):
            updated = backfill(":memory:", dry_run=True)
            assert updated == 1  # id=3 already has embedding, excluded by WHERE


def test_backfill_writes_embedding(mem_conn):
    """backfill writes embedding BLOB when not dry_run."""
    mock_embed = MagicMock()
    mock_embed.embed_texts.return_value = [_mock_embedding()]

    with patch("core.chs.scripts.backfill_embeddings.get_connection", return_value=mem_conn):
        with patch("core.chs.scripts.backfill_embeddings.get_embed_client", return_value=mock_embed):
            updated = backfill(":memory:", dry_run=False)
            assert updated == 1

    row = mem_conn.execute("SELECT embedding FROM sessions WHERE id = 1").fetchone()
    assert row[0] is not None
