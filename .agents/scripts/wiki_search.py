#!/usr/bin/env python3
"""
wiki_search.py — FTS5-only wiki search (stdlib, no qmd dependency).

Replaces the qmd-backed shim with direct SQLite FTS5 queries against the
existing qmd.db. Drops vector search, RRF, query expansion, and reranking
(evaluated as marginal-or-negative for ~1200 wiki concepts). The per-token
FTS5 query-quoting fix is ported verbatim from qmd_fts5_patch.py.

The existing qmd.db at ~/.config/qmd/qmd.db is reused read-only. No new
indexer is needed — the FTS5 table (documents_fts) is a standard SQLite
virtual table that stdlib sqlite3 can query directly.

USAGE:
  from wiki_search import WikiSearch
  ws = WikiSearch(collection="wiki")
  results = ws.search("model routing", top_k=5)

  # CLI:
  python wiki_search.py search --collection wiki --query "model routing" --top-k 5
  python wiki_search.py info --collection wiki
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any


def _sanitize_fts5_query(query: str) -> str:
    """Escape FTS5 MATCH query-syntax by per-token quoting.

    FTS5 MATCH interprets -, :, ^, ", *, (, ) as query-syntax operators.
    Quotes each token individually to disable syntax interpretation while
    preserving implicit-AND semantics.

    Ported verbatim from qmd_fts5_patch.py:72-88.
    """
    if not query or not query.strip():
        return '""'
    tokens = query.split()
    quoted = []
    for token in tokens:
        escaped = token.replace('"', '""')
        quoted.append(f'"{escaped}"')
    return " ".join(quoted)


class WikiSearchError(Exception):
    """Raised when wiki search/index operations fail."""


class WikiSearch:
    """FTS5-only search over the existing qmd.db. No qmd dependency.

    Public API matches the previous qmd-backed shim so consumers need no
    changes. Uses stdlib sqlite3 only.
    """

    def __init__(self, collection: str = "wiki"):
        self.collection_name = collection
        self._conn: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        """Open read-only connection to the qmd.db SQLite database."""
        if self._conn is not None:
            return self._conn
        db_path = os.path.expanduser("~/.config/qmd/qmd.db")
        if not os.path.exists(db_path):
            raise WikiSearchError(
                f"Database not found at {db_path}. "
                f"Run qmd index at least once, or point WIKI_SEARCH_DB "
                f"to an existing FTS5-enabled SQLite database."
            )
        try:
            self._conn = sqlite3.connect(
                f"file:{db_path}?mode=ro", uri=True
            )
            self._conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            raise WikiSearchError(f"Failed to open database {db_path}: {e}") from e
        return self._conn

    def search(
        self,
        query: str,
        top_k: int = 5,
        exclude_doc_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """FTS5 BM25 search. Returns list of {doc_id, text, score}.

        Uses per-token quoting to prevent FTS5 syntax errors on hyphens,
        colons, and other special characters. Implicit-AND is preserved
        for multi-word queries (each whitespace-separated token is quoted
        individually).
        """
        conn = self._connect()
        cur = conn.cursor()
        fts_query = _sanitize_fts5_query(query)
        try:
            cur.execute(
                "SELECT d.id, d.path, d.title, d.collection, "
                "snippet(documents_fts, 2, '<<', '>>', '...', 20) as snippet, "
                "bm25(documents_fts) as score "
                "FROM documents_fts "
                "JOIN documents d ON d.id = documents_fts.rowid "
                "WHERE documents_fts MATCH ? "
                "AND d.collection = ? "
                "AND d.active = 1 "
                "ORDER BY bm25(documents_fts) "
                "LIMIT ?",
                (fts_query, self.collection_name, top_k + 10),
            )
            rows = cur.fetchall()
        except sqlite3.OperationalError as e:
            raise WikiSearchError(f"FTS5 search failed: {e}") from e

        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for r in rows:
            doc_id = r["path"] or str(r["id"])
            if exclude_doc_id and doc_id == exclude_doc_id:
                continue
            if doc_id in seen:
                continue
            seen.add(doc_id)
            results.append(
                {
                    "doc_id": doc_id,
                    "text": r["snippet"] or "",
                    "score": r["score"],
                    "bm25_score": r["score"],
                    "vector_score": None,
                    "title": r["title"],
                    "path": r["path"],
                }
            )
            if len(results) >= top_k:
                break
        return results

    def add_document(self, doc_id: str, markdown_path: str, metadata: dict | None = None) -> None:
        """Index a markdown file. Inserts into documents + documents_fts + content.

        Requires read-write access to the database (opens in rw mode, not ro).
        """
        db_path = os.path.expanduser("~/.config/qmd/qmd.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        path = Path(markdown_path)
        if not path.exists():
            raise WikiSearchError(f"markdown file not found: {markdown_path}")
        try:
            markdown_content = path.read_text(encoding="utf-8")
            import hashlib
            import json
            from datetime import datetime, timezone

            doc_hash = hashlib.sha256(markdown_content.encode()).hexdigest()
            now = datetime.now(timezone.utc).isoformat()
            meta_str = json.dumps(metadata) if metadata else "{}"

            cur.execute(
                "INSERT OR REPLACE INTO content (hash, doc, created_at) VALUES (?, ?, ?)",
                (doc_hash, markdown_content, now),
            )
            cur.execute(
                "INSERT OR REPLACE INTO documents "
                "(collection, path, title, hash, created_at, modified_at, active, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
                (self.collection_name, doc_id, path.stem, doc_hash, now, now, meta_str),
            )
            doc_rowid = cur.lastrowid
            cur.execute(
                "INSERT OR REPLACE INTO documents_fts (rowid, filepath, title, body) "
                "VALUES (?, ?, ?, ?)",
                (doc_rowid, str(path), path.stem, markdown_content),
            )
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise WikiSearchError(f"add_document failed for '{doc_id}': {e}") from e
        finally:
            conn.close()

    def list_documents(self) -> list[str]:
        """List all document paths in the collection."""
        conn = self._connect()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT path FROM documents WHERE collection = ? AND active = 1 ORDER BY path",
                (self.collection_name,),
            )
            return [r["path"] for r in cur.fetchall()]
        except sqlite3.Error as e:
            raise WikiSearchError(f"list_documents failed: {e}") from e

    def info(self) -> dict[str, Any]:
        """Return collection info (doc count, chunk count, embedding dim)."""
        conn = self._connect()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT COUNT(*) as cnt FROM documents WHERE collection = ? AND active = 1",
                (self.collection_name,),
            )
            doc_count = cur.fetchone()["cnt"]
            cur.execute(
                "SELECT COUNT(*) as cnt FROM documents_fts "
                "WHERE rowid IN (SELECT id FROM documents WHERE collection = ? AND active = 1)",
                (self.collection_name,),
            )
            fts_count = cur.fetchone()["cnt"]
            return {
                "name": self.collection_name,
                "document_count": doc_count,
                "chunk_count": fts_count,
                "embedding_dim": None,
                "engine": "sqlite-fts5 (stdlib, no qmd)",
            }
        except sqlite3.Error as e:
            raise WikiSearchError(f"info failed: {e}") from e


# --- CLI --------------------------------------------------------------------

def _cli_search(args):
    ws = WikiSearch(collection=args.collection)
    results = ws.search(args.query, top_k=args.top_k)
    print(f"Search '{args.query}' in '{args.collection}': {len(results)} results")
    for r in results:
        print(f"  {r['title'][:60]} | score={r['score']:.4f}")
        if r["text"]:
            print(f"    {r['text'][:120]}")
        print(f"    path: {r['path']}")


def _cli_info(args):
    ws = WikiSearch(collection=args.collection)
    info = ws.info()
    print(f"Collection: {info['name']}")
    print(f"  Documents: {info['document_count']}")
    print(f"  FTS entries: {info['chunk_count']}")
    print(f"  Engine: {info['engine']}")


def _cli_smoke(args):
    """Quick smoke test: info + search."""
    _cli_info(args)
    print()
    args.query = "model routing"
    args.top_k = 3
    _cli_search(args)


def main():
    parser = argparse.ArgumentParser(description="FTS5-only wiki search (no qmd)")
    parser.add_argument("--collection", default="wiki", help="collection name")
    sub = parser.add_subparsers(dest="command")

    p_search = sub.add_parser("search", help="Search the wiki")
    p_search.add_argument("--query", required=True, help="search query")
    p_search.add_argument("--top-k", type=int, default=5, help="max results")
    p_search.set_defaults(func=_cli_search)

    p_info = sub.add_parser("info", help="Show collection info")
    p_info.set_defaults(func=_cli_info)

    p_smoke = sub.add_parser("smoke", help="Quick smoke test")
    p_smoke.set_defaults(func=_cli_smoke)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
