from __future__ import annotations

import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------
# Path resolution and setup
# ---------------------------


def _resolve_db_path(db_path: str | Path | None = None) -> str:
    """
    Resolve the database path for the lightweight results store.

    Precedence:
    - Explicit argument db_path
    - Environment variable ICHS_RESULTS_DB
    - Default: ./.ichs/results.sqlite3
    """
    if isinstance(db_path, Path):
        return str(db_path.expanduser().resolve())
    if isinstance(db_path, str) and db_path.strip():
        return str(Path(db_path).expanduser().resolve())

    env_path = os.environ.get("ICHS_RESULTS_DB")
    if env_path:
        return str(Path(env_path).expanduser().resolve())

    default_dir = Path.cwd() / ".ichs"
    default_dir.mkdir(parents=True, exist_ok=True)
    return str((default_dir / "results.sqlite3").resolve())


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.execute("PRAGMA busy_timeout=5000;")
    finally:
        cur.close()


def init_db(db_path: str | Path | None = None) -> None:
    """
    Initialize the lightweight results database and ensure schema exists.
    Safe to call repeatedly.
    """
    path = _resolve_db_path(db_path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        _apply_pragmas(conn)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    source TEXT,
                    payload TEXT
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_results_created ON results(created_at)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_results_source ON results(source)"
            )
        finally:
            cur.close()
        conn.commit()


# ---------------------------
# Write API
# ---------------------------


def save_result(
    payload: dict[str, Any],
    *,
    source: str | None = None,
    db_path: str | Path | None = None,
) -> int:
    """
    Persist a single result payload into the lightweight results store.

    Args:
        payload: Arbitrary dict (will be JSON-encoded). Should contain keys like:
                 check/name/command, returncode, duration_sec, etc.
        source: Optional label to group results (e.g., 'cli.run').
        db_path: Optional override for database path.

    Returns:
        The inserted row id.
    """
    path = _resolve_db_path(db_path)
    init_db(path)  # Ensure schema exists

    created_at = datetime.now(UTC).isoformat(timespec="seconds")
    try:
        payload_str = json.dumps(payload, ensure_ascii=False)
    except Exception:
        # Best-effort: fallback to string representation on serialization failure
        payload_str = json.dumps(
            {"_serialization_error": True, "raw": str(payload)}, ensure_ascii=False
        )

    with sqlite3.connect(path) as conn:
        _apply_pragmas(conn)
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO results (created_at, source, payload) VALUES (?, ?, ?)",
                (created_at, source, payload_str),
            )
            row_id = int(cur.lastrowid)
        finally:
            cur.close()
        conn.commit()
    return row_id


# ---------------------------
# Read API
# ---------------------------


def get_results(
    *,
    limit: int | None = None,
    db_path: str | Path | None = None,
    source: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch stored results, newest first.

    Args:
        limit: Optional maximum number of rows
        db_path: Optional database path override
        source: Optional source filter

    Returns:
        List of dicts with id, created_at, source, and payload (decoded)
    """
    path = _resolve_db_path(db_path)
    init_db(path)

    with sqlite3.connect(path) as conn:
        _apply_pragmas(conn)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        try:
            if source is not None and limit is not None:
                cur.execute(
                    "SELECT * FROM results WHERE source = ? ORDER BY id DESC LIMIT ?",
                    (source, limit),
                )
            elif source is not None:
                cur.execute(
                    "SELECT * FROM results WHERE source = ? ORDER BY id DESC",
                    (source,),
                )
            elif limit is not None:
                cur.execute("SELECT * FROM results ORDER BY id DESC LIMIT ?", (limit,))
            else:
                cur.execute("SELECT * FROM results ORDER BY id DESC")

            rows = cur.fetchall()
        finally:
            cur.close()

    out: list[dict[str, Any]] = []
    for r in rows:
        try:
            payload = json.loads(r["payload"]) if r["payload"] else {}
        except json.JSONDecodeError:
            payload = {"_decode_error": True, "raw": r["payload"]}
        out.append(
            {
                "id": int(r["id"]),
                "created_at": str(r["created_at"]),
                "source": r["source"],
                "payload": payload,
            }
        )
    return out


__all__ = ["init_db", "save_result", "get_results"]
