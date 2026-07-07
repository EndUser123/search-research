"""Tests for model/dim-aware search_semantic_sessions.

The read path must never compare vectors across embedding spaces:
- query dim is inferred from the query embedding (no hardcoded 384)
- rows with mismatched dim or model are excluded with a WARNING
- total mismatch raises (misconfiguration, not an empty result)
"""

from __future__ import annotations

import logging
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parents[3]))

from core.chs.search import search_semantic_sessions


def vec(values):
    return np.array(values, dtype=np.float32).tobytes()


class Client:
    """Embed client stub returning a fixed vector."""

    def __init__(self, v):
        self.v = v

    def embed_texts(self, texts):
        return [self.v for _ in texts]


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """CREATE TABLE sessions (
            id INTEGER PRIMARY KEY, first_prompt TEXT, summary_short TEXT,
            embedding BLOB, embedding_model TEXT, embedding_dim INTEGER)"""
    )
    return conn


def test_dim_inferred_from_query_not_hardcoded(db):
    # 4-dim store, 4-dim query: works even though nothing is 384
    db.execute("INSERT INTO sessions VALUES (1, 'p', 's', ?, 'm1', 4)", (vec([1, 0, 0, 0]),))
    db.commit()
    results = search_semantic_sessions(db, "q", Client(vec([1, 0, 0, 0])), threshold=0.5)
    assert len(results) == 1
    assert results[0]["score"] == pytest.approx(1.0)


def test_mixed_dims_filtered_with_warning(db, caplog):
    db.execute("INSERT INTO sessions VALUES (1, 'p', 's', ?, 'm1', 4)", (vec([1, 0, 0, 0]),))
    db.execute("INSERT INTO sessions VALUES (2, 'p', 's', ?, 'm2', 8)",
               (vec([1, 0, 0, 0, 0, 0, 0, 0]),))
    db.commit()
    with caplog.at_level(logging.WARNING):
        results = search_semantic_sessions(db, "q", Client(vec([1, 0, 0, 0])), threshold=0.5)
    assert len(results) == 1
    assert results[0]["session_id"] == 1
    assert "mixed embedding state" in caplog.text


def test_model_filter_excludes_other_models(db):
    db.execute("INSERT INTO sessions VALUES (1, 'p', 's', ?, 'model-A', 4)", (vec([1, 0, 0, 0]),))
    db.execute("INSERT INTO sessions VALUES (2, 'p', 's', ?, 'model-B', 4)", (vec([1, 0, 0, 0]),))
    db.commit()
    results = search_semantic_sessions(db, "q", Client(vec([1, 0, 0, 0])),
                                       threshold=0.5, expected_model="model-A")
    assert [r["session_id"] for r in results] == [1]


def test_legacy_null_model_rows_still_scored(db):
    db.execute("INSERT INTO sessions VALUES (1, 'p', 's', ?, NULL, NULL)", (vec([1, 0, 0, 0]),))
    db.commit()
    results = search_semantic_sessions(db, "q", Client(vec([1, 0, 0, 0])),
                                       threshold=0.5, expected_model="model-A")
    assert len(results) == 1  # dim matches; NULL model tolerated for legacy rows


def test_total_mismatch_raises(db):
    db.execute("INSERT INTO sessions VALUES (1, 'p', 's', ?, 'm1', 8)",
               (vec([1, 0, 0, 0, 0, 0, 0, 0]),))
    db.commit()
    with pytest.raises(ValueError, match="re-embed"):
        search_semantic_sessions(db, "q", Client(vec([1, 0, 0, 0])))


def test_empty_store_returns_empty(db):
    assert search_semantic_sessions(db, "q", Client(vec([1, 0, 0, 0]))) == []
