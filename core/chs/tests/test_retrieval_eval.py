"""Tests for the golden-case retrieval eval harness.

Uses a synthetic in-memory DB and an injected FTS search function, so the
harness logic (case loading, stable-key matching, recall math, thresholds)
is verified without the semantic daemon or a real chat history.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3]))

from core.chs.eval.retrieval_eval import GoldenCase, evaluate, load_cases

DOCS = {
    "msg-atomic": "Use tmp file plus os.replace for atomic JSON writes",
    "msg-hooks": "Plugin hooks must use the plugin_name_Event naming convention",
    "msg-ports": "Probe localhost ports with raw sockets before HTTP checks",
}


@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """CREATE TABLE messages (
            id INTEGER PRIMARY KEY, message_id TEXT UNIQUE, session_id INTEGER,
            role TEXT, content TEXT)"""
    )
    conn.execute("CREATE VIRTUAL TABLE messages_fts USING fts5(content)")
    for i, (mid, content) in enumerate(DOCS.items(), start=1):
        conn.execute(
            "INSERT INTO messages (id, message_id, session_id, role, content) VALUES (?, ?, 1, 'user', ?)",
            (i, mid, content),
        )
        conn.execute("INSERT INTO messages_fts (rowid, content) VALUES (?, ?)", (i, content))
    conn.commit()
    return conn


def fts_search(conn, query, limit):
    cursor = conn.execute(
        """SELECT m.id, m.session_id, m.role, m.content, -bm25(messages_fts) AS score
           FROM messages m JOIN messages_fts ON m.rowid = messages_fts.rowid
           WHERE messages_fts MATCH ? ORDER BY score DESC LIMIT ?""",
        (" OR ".join(query.split()), limit),
    )
    return [
        {"id": r[0], "session_id": r[1], "role": r[2], "content": r[3], "score": r[4]}
        for r in cursor.fetchall()
    ]


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_perfect_recall_by_message_id(conn):
    cases = [GoldenCase(id="c1", query="atomic JSON writes",
                        required_message_ids={"msg-atomic"})]
    results = evaluate(conn, cases, fts_search)
    assert results[0].recall == 1.0
    assert results[0].missing == []


def test_perfect_recall_by_content_hash(conn):
    cases = [GoldenCase(id="c2", query="naming convention hooks",
                        required_content_sha256={_sha(DOCS["msg-hooks"])})]
    results = evaluate(conn, cases, fts_search)
    assert results[0].recall == 1.0


def test_zero_recall_for_absent_result(conn):
    cases = [GoldenCase(id="c3", query="atomic JSON writes",
                        required_message_ids={"msg-nonexistent"})]
    results = evaluate(conn, cases, fts_search)
    assert results[0].recall == 0.0
    assert "msg-nonexistent" in results[0].missing


def test_partial_recall_mixed_keys(conn):
    cases = [GoldenCase(
        id="c4", query="atomic JSON writes",
        required_message_ids={"msg-atomic"},
        required_content_sha256={_sha("content that is not in the db")},
    )]
    results = evaluate(conn, cases, fts_search)
    assert results[0].recall == 0.5
    assert results[0].found == 1
    assert results[0].required == 2


def test_k_limits_retrieval(conn):
    # k=1 returns only the best match; require a doc that ranks below it
    cases = [GoldenCase(id="c5", query="atomic writes ports sockets", k=1,
                        required_message_ids={"msg-atomic", "msg-ports"})]
    results = evaluate(conn, cases, fts_search)
    assert results[0].recall == 0.5


def test_session_key_matching(conn):
    """Semantic-sessions results (session_id only) match via sessions.session_key."""
    conn.execute(
        "CREATE TABLE sessions (id INTEGER PRIMARY KEY, session_key TEXT)"
    )
    conn.execute("INSERT INTO sessions (id, session_key) VALUES (7, 'sess-alpha')")
    conn.commit()

    def semantic_like_search(conn_, query, limit):
        return [{"id": None, "session_id": 7, "content": "summary text", "score": 0.9}]

    cases = [GoldenCase(id="c6", query="anything",
                        required_session_keys={"sess-alpha"})]
    results = evaluate(conn, cases, semantic_like_search)
    assert results[0].recall == 1.0

    cases = [GoldenCase(id="c7", query="anything",
                        required_session_keys={"sess-missing"})]
    results = evaluate(conn, cases, semantic_like_search)
    assert results[0].recall == 0.0
    assert "sess-missing" in results[0].missing


def test_string_ids_are_stable_message_ids(conn):
    """Current search_fts_messages returns TEXT message_id under 'id'.
    Strings must be treated as the stable key directly (no int lookup)."""

    def new_shape_search(conn_, query, limit):
        return [{"id": "msg-atomic", "session_id": 1,
                 "content": DOCS["msg-atomic"], "score": 1.0}]

    cases = [GoldenCase(id="c8", query="q", required_message_ids={"msg-atomic"})]
    results = evaluate(conn, cases, new_shape_search)
    assert results[0].recall == 1.0


def test_load_cases_rejects_unpinned(tmp_path):
    path = tmp_path / "cases.jsonl"
    path.write_text(json.dumps({"id": "bad", "query": "q"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="pins no required results"):
        load_cases(path)


def test_load_cases_roundtrip(tmp_path):
    path = tmp_path / "cases.jsonl"
    path.write_text(
        json.dumps({"id": "ok", "query": "q", "required_message_ids": ["m1"], "k": 5}) + "\n",
        encoding="utf-8",
    )
    cases = load_cases(path)
    assert cases[0].id == "ok"
    assert cases[0].k == 5
    assert cases[0].required_message_ids == {"m1"}
