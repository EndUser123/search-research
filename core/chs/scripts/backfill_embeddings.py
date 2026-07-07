"""Backfill or re-embed session embeddings with run-level provenance.

Every run records a row in the embedding_runs table AND a JSON manifest
next to the database (<db_dir>/embedding_runs/<run_id>.json), capturing
model, dimensions, source digest, params, timestamps, and row count.
Each updated row is tagged with the run's embedding_run_id, so mixed
embedding states are detectable and re-embeds are auditable.

Usage:
    python -m core.chs.scripts.backfill_embeddings
    python -m core.chs.scripts.backfill_embeddings --dry-run
    python -m core.chs.scripts.backfill_embeddings --re-embed   # all rows, e.g. model swap
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from ..config import get_chs_db_path
from ..db import ensure_embedding_run_schema, get_connection
from ..embeddings import get_embed_client

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
DISTANCE = "cosine"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _source_digest(rows: list[tuple]) -> str:
    """Digest of (id, sha256(text)) pairs: identifies exactly what was embedded."""
    hasher = hashlib.sha256()
    for row_id, text in rows:
        text_sha = hashlib.sha256((text or "").encode("utf-8")).hexdigest()
        hasher.update(f"{row_id}:{text_sha}\n".encode("utf-8"))
    return hasher.hexdigest()


def _write_manifest(db_path: str, manifest: dict) -> Path | None:
    """Write the run manifest JSON next to the database. Returns path or None for :memory:."""
    if db_path == ":memory:":
        return None
    out_dir = Path(db_path).parent / "embedding_runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{manifest['run_id']}.json"
    tmp_path = out_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    tmp_path.replace(out_path)
    return out_path


def backfill(
    db_path: str,
    dry_run: bool = False,
    re_embed: bool = False,
    embed_client=None,
) -> dict:
    """Backfill (or re-embed) session embeddings with run provenance.

    Args:
        db_path: Path to the SQLite database
        dry_run: If True, count but don't write anything (no run row, no manifest)
        re_embed: If True, embed ALL sessions, not only those missing embeddings.
            Use for model swaps; point --db at a copy for side-by-side cutover.
        embed_client: Injectable embedding client (tests); defaults to daemon client.

    Returns:
        dict with run_id, updated count, source_digest, manifest_path
    """
    conn = get_connection(db_path)
    ensure_embedding_run_schema(conn)
    if embed_client is None:
        embed_client = get_embed_client()

    where = "" if re_embed else "WHERE embedding IS NULL"
    cursor = conn.execute(
        f"SELECT id, COALESCE(summary_short, first_prompt) AS text FROM sessions {where}"
    )
    rows = [(row_id, text) for row_id, text in cursor.fetchall() if text]

    if dry_run:
        conn.close()
        return {"run_id": None, "updated": len(rows), "source_digest": _source_digest(rows),
                "manifest_path": None}

    run_id = f"{MODEL_NAME}-{int(time.time())}"
    digest = _source_digest(rows)
    params = {"re_embed": re_embed, "target": "sessions.embedding",
              "text_source": "COALESCE(summary_short, first_prompt)"}
    started_at = _utcnow()

    conn.execute(
        """INSERT INTO embedding_runs
           (run_id, model_name, embedding_dim, distance, target_table,
            source_digest, params_json, started_at, status)
           VALUES (?, ?, ?, ?, 'sessions', ?, ?, ?, 'running')""",
        (run_id, MODEL_NAME, EMBEDDING_DIM, DISTANCE, digest, json.dumps(params), started_at),
    )
    conn.commit()

    updated = 0
    status = "complete"
    try:
        for row_id, text in rows:
            embedding = embed_client.embed_texts([text])[0]
            conn.execute(
                """UPDATE sessions
                   SET embedding = ?, embedding_model = ?, embedding_dim = ?, embedding_run_id = ?
                   WHERE id = ?""",
                (embedding, MODEL_NAME, EMBEDDING_DIM, run_id, row_id),
            )
            updated += 1
        conn.commit()
    except Exception:
        conn.rollback()
        status = "failed"
        raise
    finally:
        finished_at = _utcnow()
        conn.execute(
            "UPDATE embedding_runs SET finished_at = ?, row_count = ?, status = ? WHERE run_id = ?",
            (finished_at, updated, status, run_id),
        )
        conn.commit()
        manifest = {
            "schema_version": "chs.embedding_run.v1",
            "run_id": run_id,
            "model": {"provider": "local", "name": MODEL_NAME,
                      "dimensions": EMBEDDING_DIM, "distance": DISTANCE},
            "target_table": "sessions",
            "db_path": db_path,
            "source_digest": digest,
            "params": params,
            "started_at": started_at,
            "finished_at": finished_at,
            "row_count": updated,
            "status": status,
        }
        manifest_path = _write_manifest(db_path, manifest)
        conn.close()

    return {"run_id": run_id, "updated": updated, "source_digest": digest,
            "manifest_path": str(manifest_path) if manifest_path else None}


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill session embeddings with run provenance")
    parser.add_argument("--dry-run", action="store_true", help="Count pending but don't write")
    parser.add_argument("--re-embed", action="store_true",
                        help="Re-embed ALL sessions (model swap); consider pointing --db at a copy")
    parser.add_argument("--db", default=None, help="Path to database (default: from db config)")
    args = parser.parse_args()

    db_path = args.db or get_chs_db_path()
    result = backfill(db_path, dry_run=args.dry_run, re_embed=args.re_embed)
    action = "Would update" if args.dry_run else "Updated"
    print(f"{action} {result['updated']} sessions")
    if result["run_id"]:
        print(f"Run: {result['run_id']}  digest: {result['source_digest'][:16]}…")
        print(f"Manifest: {result['manifest_path']}")


if __name__ == "__main__":
    main()
