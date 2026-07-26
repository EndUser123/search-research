#!/usr/bin/env python3
"""
wiki_search.py — shim layer over qmd for wiki search/index operations.

ARCHITECTURAL RATIONALE (subprocess-as-degradation-boundary):
This shim exists because direct `from qmd import connect` in every consumer
tightens coupling at the moment when qmd's long-term viability is in question
(qmd pinned at 0.1.x, upstream dead since ~2026-07-20, patch count growing).

By routing all qmd access through this single module:
  - Consumers import wiki_search, NOT qmd directly
  - If qmd is ever replaced (vendored / raw sqlite-fts5 / in-house rewrite),
    only THIS FILE changes — every consumer keeps working
  - The shim is the replacement boundary

This is the structural fix for the CLI-drift failure class documented in
~/.grok/skills/crawl4ai/crawl_to_qmd.py (lines 100-104, 528) where hardcoded
subprocess calls assumed a qmd API that doesn't match the installed version.

Source insight: /tp critique session 019f9bfe (2026-07-25) — "subprocess was
wrong-on-syntax but right-on-architecture; direct import is right-on-syntax
but wrong-on-architecture at this moment."

USAGE:
  from wiki_search import WikiSearch
  ws = WikiSearch(collection="wiki")
  ws.add_document(doc_id, markdown_path)
  results = ws.search(query, top_k=5)
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class WikiSearchError(Exception):
    """Raised when wiki search/index operations fail."""


class WikiSearch:
    """Shim over qmd providing search and index operations.

    Isolates qmd's Python API behind a stable interface so consumers don't
    import qmd directly. If qmd is replaced, only this class changes.

    Lazy-imports qmd so importing this module doesn't fail when qmd is absent
    (preserves the degradable-failure property of the old subprocess pattern).
    """

    def __init__(self, collection: str = "wiki"):
        self.collection_name = collection
        self._client = None
        self._collection = None

    def _connect(self):
        """Lazy-connect to qmd. Raises WikiSearchError with actionable message on failure."""
        if self._collection is not None:
            return self._collection
        try:
            from qmd import connect
        except ImportError as e:
            raise WikiSearchError(
                f"qmd not importable in this Python ({sys.executable}). "
                f"This shim requires qmd installed in the same environment. "
                f"Original error: {e}"
            ) from e
        try:
            self._client = connect()
            self._collection = self._client.collection(self.collection_name)
        except Exception as e:
            raise WikiSearchError(
                f"Failed to connect to qmd collection '{self.collection_name}': {e}"
            ) from e
        return self._collection

    def search(
        self,
        query: str,
        top_k: int = 5,
        exclude_doc_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Hybrid search the collection. Returns list of {doc_id, text, score}.

        Args:
            query: search query
            top_k: max results
            exclude_doc_id: if set, drop results with this document_id (self-exclusion)

        Returns:
            List of dicts with keys: doc_id, text, score, bm25_score, vector_score.
            Deduplicated by doc_id (first chunk wins).
        """
        col = self._connect()
        try:
            raw = col.hybrid_search(query=query, top_k=top_k + 5)
        except Exception as e:
            raise WikiSearchError(f"hybrid_search failed: {e}") from e

        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for r in raw:
            cref = getattr(r, "chunk_ref", None)
            doc_id = getattr(cref, "document_id", None) if cref else None
            if not doc_id:
                # fallback for dict-shaped results
                if isinstance(r, dict):
                    cref = r.get("chunk_ref", {})
                    doc_id = cref.get("document_id", "?")
                else:
                    continue
            if exclude_doc_id and doc_id == exclude_doc_id:
                continue
            if doc_id in seen:
                continue
            seen.add(doc_id)
            text = getattr(r, "text", None) or (r.get("text", "") if isinstance(r, dict) else "")
            results.append({
                "doc_id": doc_id,
                "text": text,
                "score": getattr(r, "score", None) or (r.get("score") if isinstance(r, dict) else None),
                "bm25_score": getattr(r, "bm25_score", None),
                "vector_score": getattr(r, "vector_score", None),
            })
            if len(results) >= top_k:
                break
        return results

    def add_document(self, doc_id: str, markdown_path: str, metadata: dict | None = None) -> None:
        """Index a markdown file into the collection. Replaces bulk `qmd update`."""
        col = self._connect()
        path = Path(markdown_path)
        if not path.exists():
            raise WikiSearchError(f"markdown file not found: {markdown_path}")
        try:
            # qmd 0.1.2 API: takes `markdown` (content string), not `markdown_file` (path)
            markdown_content = path.read_text(encoding="utf-8")
            kwargs: dict[str, Any] = {
                "document_id": doc_id,
                "markdown": markdown_content,
            }
            if metadata:
                kwargs["metadata"] = metadata
            col.add_document(**kwargs)
        except Exception as e:
            raise WikiSearchError(f"add_document failed for '{doc_id}': {e}") from e

    def list_documents(self) -> list[str]:
        """List all document_ids in the collection."""
        col = self._connect()
        try:
            docs = col.list_documents()
            out: list[str] = []
            for d in docs:
                # qmd 0.1.2 returns list[str]; older versions may return objects/dicts.
                # Short-circuit on str before any attribute access — getattr()'s
                # default is evaluated eagerly, so d.get() on a str raises AttributeError.
                if isinstance(d, str):
                    out.append(d)
                elif isinstance(d, dict):
                    out.append(d.get("document_id", "?"))
                else:
                    out.append(getattr(d, "document_id", "?"))
            return out
        except Exception as e:
            raise WikiSearchError(f"list_documents failed: {e}") from e

    def info(self) -> dict[str, Any]:
        """Return collection info (doc count, chunk count, embedding dim)."""
        col = self._connect()
        try:
            info = col.info()
            if isinstance(info, dict):
                return info
            # info() may return a CollectionInfo object
            return {
                "name": getattr(info, "name", self.collection_name),
                "document_count": getattr(info, "document_count", None),
                "chunk_count": getattr(info, "chunk_count", None),
                "embedding_dim": getattr(info, "embedding_dim", None),
            }
        except Exception as e:
            raise WikiSearchError(f"info failed: {e}") from e


# --- CLI for smoke testing --------------------------------------------------

def _smoke_test():
    """Quick smoke test: connect, search, info."""
    ws = WikiSearch("wiki")
    print("info:", ws.info())
    results = ws.search("qmd semantic search", top_k=3)
    print(f"\nsearch 'qmd semantic search' → {len(results)} results:")
    for r in results:
        print(f"  {r['doc_id']}  score={r['score']}")


if __name__ == "__main__":
    _smoke_test()
