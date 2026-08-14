"""Tests for embedding run provenance in backfill_embeddings.

Covers:
- run row creation in embedding_runs with digest/model/status
- per-row embedding_run_id tagging
- manifest.json written next to the database
- dry-run writes nothing
- --re-embed embeds all rows, not just NULL embeddings
- ensure_embedding_run_schema migrates legacy databases
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3]))

from core.chs.db import ensure_embedding_run_schema, get_connection, init_db
from core.chs.scripts.backfill_embeddings import EMBEDDING_DIM, MODEL_NAME, backfill


class FakeEmbedClient:
    """Deterministic stand-in for the semantic daemon client."""

    def __init__(self):
        self.calls = 0

    def embed_texts(self, texts):
        self.calls += len(texts)
        return [bytes(EMBEDDING_DIM * 4) for _ in texts]  # zeroed float32 vector


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "chs_test.db"
    init_db(path)
    conn = get_connection(path)
    conn.execute("INSERT INTO projects (id, path) VALUES (1, '/proj')")
    for i in range(3):
        conn.execute(
            """INSERT INTO sessions (session_key, project_id, started_at, first_prompt)
               VALUES (?, 1, 0, ?)""",
            (f"s{i}", f"prompt text {i}"),
        )
    conn.commit()
    conn.close()
    return str(path)


def test_backfill_records_run_and_tags_rows(db_path):
    client = FakeEmbedClient()
    result = backfill(db_path, embed_client=client)

    assert result["updated"] == 3
    assert client.calls == 3

    conn = sqlite3.connect(db_path)
    runs = conn.execute(
        "SELECT run_id, model_name, embedding_dim, target_table, status, row_count,"
        " source_digest, started_at, finished_at FROM embedding_runs"
    ).fetchall()
    assert len(runs) == 1
    run = runs[0]
    assert run[0] == result["run_id"]
    assert run[1] == MODEL_NAME
    assert run[2] == EMBEDDING_DIM
    assert run[3] == "sessions"
    assert run[4] == "complete"
    assert run[5] == 3
    assert len(run[6]) == 64  # sha256 hex
    assert run[7] and run[8]

    tagged = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE embedding_run_id = ?", (result["run_id"],)
    ).fetchone()[0]
    assert tagged == 3
    conn.close()


def test_backfill_writes_manifest(db_path):
    result = backfill(db_path, embed_client=FakeEmbedClient())
    manifest_path = Path(result["manifest_path"])
    assert manifest_path.exists()
    assert manifest_path.parent.name == "embedding_runs"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "chs.embedding_run.v1"
    assert manifest["run_id"] == result["run_id"]
    assert manifest["model"]["name"] == MODEL_NAME
    assert manifest["model"]["dimensions"] == EMBEDDING_DIM
    assert manifest["source_digest"] == result["source_digest"]
    assert manifest["row_count"] == 3
    assert manifest["status"] == "complete"


def test_dry_run_writes_nothing(db_path):
    client = FakeEmbedClient()
    result = backfill(db_path, dry_run=True, embed_client=client)

    assert result["updated"] == 3
    assert result["run_id"] is None
    assert client.calls == 0

    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM embedding_runs").fetchone()[0] == 0
    assert conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE embedding IS NOT NULL"
    ).fetchone()[0] == 0
    conn.close()
    assert not (Path(db_path).parent / "embedding_runs").exists()


def test_re_embed_covers_all_rows(db_path):
    first = backfill(db_path, embed_client=FakeEmbedClient())
    # Without re_embed, nothing is pending
    assert backfill(db_path, dry_run=True, embed_client=FakeEmbedClient())["updated"] == 0
    # With re_embed, all rows get a new run
    second = backfill(db_path, re_embed=True, embed_client=FakeEmbedClient())
    assert second["updated"] == 3
    assert second["run_id"] != first["run_id"]

    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM embedding_runs").fetchone()[0] == 2
    tagged = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE embedding_run_id = ?", (second["run_id"],)
    ).fetchone()[0]
    assert tagged == 3
    conn.close()


def test_digest_stable_and_content_sensitive(db_path):
    a = backfill(db_path, dry_run=True, embed_client=FakeEmbedClient())["source_digest"]
    b = backfill(db_path, dry_run=True, embed_client=FakeEmbedClient())["source_digest"]
    assert a == b

    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE sessions SET first_prompt = 'changed' WHERE session_key = 's0'")
    conn.commit()
    conn.close()
    c = backfill(db_path, dry_run=True, embed_client=FakeEmbedClient())["source_digest"]
    assert c != a


def test_migration_on_legacy_database(tmp_path):
    """A pre-embedding-run DB gains the table and columns idempotently."""
    path = tmp_path / "legacy.db"
    conn = sqlite3.connect(path)
    conn.execute(
        """CREATE TABLE sessions (
            id INTEGER PRIMARY KEY, session_key TEXT, project_id INTEGER,
            started_at INTEGER, first_prompt TEXT, summary_short TEXT,
            embedding BLOB, embedding_model TEXT, embedding_dim INTEGER)"""
    )
    conn.execute(
        """CREATE TABLE turns (
            id INTEGER PRIMARY KEY, content TEXT,
            embedding BLOB, embedding_model TEXT, embedding_dim INTEGER)"""
    )
    conn.commit()

    ensure_embedding_run_schema(conn)
    ensure_embedding_run_schema(conn)  # idempotent

    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "embedding_runs" in tables
    for table in ("sessions", "turns"):
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        assert "embedding_run_id" in cols
    conn.close()
