"""Backfill or re-embed session embeddings with run-level provenance.

Every run records a row in the embedding_runs table AND a JSON manifest
next to the database (<db_dir>/embedding_runs/<run_id>.json), capturing
model, dimensions, source digest, params, timestamps, and row count.
Each updated row is tagged with the run's embedding_run_id, so mixed
embedding states are detectable and re-embeds are auditable.

Model resolution order: --model/--dim flags > active embeddings_config row
> defaults. All row updates happen in a single transaction: a crash mid-run
rolls back every row and leaves the embedding_runs row in 'running' status
as the tombstone.

Optionally gate the run on the golden retrieval eval:
    --golden-cases <path> runs the semantic-sessions eval AFTER the backfill
    and exits 1 if mean recall < --min-recall. Nothing cuts over silently.

Usage:
    python -m core.chs.scripts.backfill_embeddings
    python -m core.chs.scripts.backfill_embeddings --dry-run
    python -m core.chs.scripts.backfill_embeddings --re-embed --model bge-small-en-v1.5 --dim 384
    python -m core.chs.scripts.backfill_embeddings --golden-cases core/chs/eval/golden_cases.jsonl
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
from ..db import ensure_embedding_run_schema, get_connection, load_embeddings_config
from ..embeddings import get_embed_client

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_DIM = 384
DISTANCE = "cosine"

# Backward-compatible aliases (tests and callers import these names)
MODEL_NAME = DEFAULT_MODEL_NAME
EMBEDDING_DIM = DEFAULT_EMBEDDING_DIM


def resolve_model(db_path: str, model: str | None = None, dim: int | None = None) -> tuple[str, int]:
    """Resolve embedding model/dim: explicit args > embeddings_config > defaults."""
    if model and dim:
        return model, dim
    config = None
    try:
        config = load_embeddings_config(db_path)
    except Exception:
        pass  # missing table on legacy DB: fall through to defaults
    if config:
        return model or config["model_name"], dim or config["embedding_dim"]
    return model or DEFAULT_MODEL_NAME, dim or DEFAULT_EMBEDDING_DIM


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _source_digest(rows: list[tuple]) -> str:
    """Digest of (id, sha256(text)) pairs: identifies exactly what was embedded.

    Note: this is the EMBED-INPUT digest. It intentionally changes when the
    embedded text changes (e.g. a new summarizer rewrote summary_short) —
    that IS a different embedding input, and the manifest should say so.
    """
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
    model_name: str | None = None,
    embedding_dim: int | None = None,
) -> dict:
    """Backfill (or re-embed) session embeddings with run provenance.

    Args:
        db_path: Path to the SQLite database
        dry_run: If True, count but don't write anything (no run row, no manifest)
        re_embed: If True, embed ALL sessions, not only those missing embeddings.
            Use for model swaps; point --db at a copy for side-by-side cutover.
        embed_client: Injectable embedding client (tests); defaults to daemon client.
        model_name / embedding_dim: Override model resolution (see resolve_model).

    Returns:
        dict with run_id, updated count, source_digest, manifest_path, model, dim

    Raises:
        ValueError: if the embed client returns a vector whose byte length
            does not match embedding_dim * 4 (float32). Fail fast: a dim
            mismatch written to the table poisons cosine similarity silently.
    """
    conn = get_connection(db_path)
    ensure_embedding_run_schema(conn)
    if embed_client is None:
        embed_client = get_embed_client()
    model, dim = resolve_model(db_path, model_name, embedding_dim)

    where = "" if re_embed else "WHERE embedding IS NULL"
    cursor = conn.execute(
        f"SELECT id, COALESCE(summary_short, first_prompt) AS text FROM sessions {where}"
    )
    rows = [(row_id, text) for row_id, text in cursor.fetchall() if text]

    if dry_run:
        conn.close()
        return {"run_id": None, "updated": len(rows), "source_digest": _source_digest(rows),
                "manifest_path": None, "model": model, "dim": dim}

    run_id = f"{model}-{int(time.time())}"
    digest = _source_digest(rows)
    params = {"re_embed": re_embed, "target": "sessions.embedding",
              "text_source": "COALESCE(summary_short, first_prompt)",
              "digest_semantics": "embed_input"}
    started_at = _utcnow()

    conn.execute(
        """INSERT INTO embedding_runs
           (run_id, model_name, embedding_dim, distance, target_table,
            source_digest, params_json, started_at, status)
           VALUES (?, ?, ?, ?, 'sessions', ?, ?, ?, 'running')""",
        (run_id, model, dim, DISTANCE, digest, json.dumps(params), started_at),
    )
    conn.commit()

    expected_bytes = dim * 4  # float32
    updated = 0
    status = "complete"
    try:
        # Single transaction: all row updates commit together or not at all.
        # A crash mid-run rolls back the rows; the 'running' run row remains
        # as the tombstone for the aborted attempt.
        for row_id, text in rows:
            embedding = embed_client.embed_texts([text])[0]
            if len(embedding) != expected_bytes:
                raise ValueError(
                    f"Embedding byte length {len(embedding)} != expected "
                    f"{expected_bytes} (dim {dim} float32) for session {row_id}. "
                    f"Model/dim config is wrong — refusing to write."
                )
            conn.execute(
                """UPDATE sessions
                   SET embedding = ?, embedding_model = ?, embedding_dim = ?, embedding_run_id = ?
                   WHERE id = ?""",
                (embedding, model, dim, run_id, row_id),
            )
            updated += 1
        conn.commit()
    except Exception:
        conn.rollback()
        status = "failed"
        updated = 0
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
            "model": {"provider": "local", "name": model,
                      "dimensions": dim, "distance": DISTANCE},
            "target_table": "sessions",
            "db_path": db_path,
            "source_digest": digest,
            "digest_semantics": "embed_input",
            "params": params,
            "started_at": started_at,
            "finished_at": finished_at,
            "row_count": updated,
            "status": status,
        }
        manifest_path = _write_manifest(db_path, manifest)
        conn.close()

    return {"run_id": run_id, "updated": updated, "source_digest": digest,
            "manifest_path": str(manifest_path) if manifest_path else None,
            "model": model, "dim": dim}


def run_eval_gate(db_path: str, cases_path: str, min_recall: float,
                  embed_client=None, expected_model: str | None = None) -> bool:
    """Run the semantic-sessions golden eval; True when mean recall passes."""
    import sqlite3

    from ..eval.retrieval_eval import evaluate, load_cases, make_semantic_sessions_search, report

    if embed_client is None:
        embed_client = get_embed_client()
    cases = load_cases(Path(cases_path))
    conn = sqlite3.connect(db_path)
    try:
        search_fn = make_semantic_sessions_search(embed_client, expected_model=expected_model)
        results = evaluate(conn, cases, search_fn)
    finally:
        conn.close()
    mean = report(results)
    return mean >= min_recall


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill session embeddings with run provenance")
    parser.add_argument("--dry-run", action="store_true", help="Count pending but don't write")
    parser.add_argument("--re-embed", action="store_true",
                        help="Re-embed ALL sessions (model swap); consider pointing --db at a copy")
    parser.add_argument("--db", default=None, help="Path to database (default: from db config)")
    parser.add_argument("--model", default=None, help="Embedding model name (default: embeddings_config or built-in)")
    parser.add_argument("--dim", type=int, default=None, help="Embedding dimensions (default: embeddings_config or built-in)")
    parser.add_argument("--golden-cases", default=None,
                        help="Golden eval JSONL; run semantic-sessions recall AFTER backfill and gate on it")
    parser.add_argument("--min-recall", type=float, default=0.8,
                        help="Eval gate threshold (with --golden-cases)")
    args = parser.parse_args()

    db_path = args.db or get_chs_db_path()
    result = backfill(db_path, dry_run=args.dry_run, re_embed=args.re_embed,
                      model_name=args.model, embedding_dim=args.dim)
    action = "Would update" if args.dry_run else "Updated"
    print(f"{action} {result['updated']} sessions with {result['model']} (dim {result['dim']})")
    if result["run_id"]:
        print(f"Run: {result['run_id']}  digest: {result['source_digest'][:16]}…")
        print(f"Manifest: {result['manifest_path']}")

    if args.golden_cases and not args.dry_run:
        print("\n-- golden eval gate (semantic-sessions) --")
        if not run_eval_gate(db_path, args.golden_cases, args.min_recall,
                             expected_model=result["model"]):
            print(f"GATE FAILED: mean recall below {args.min_recall}. "
                  f"Do NOT cut over; investigate before switching config.")
            sys.exit(1)
        print(f"Gate passed (>= {args.min_recall}).")


if __name__ == "__main__":
    main()
