#!/usr/bin/env python3
from __future__ import annotations
from hooks_resolver import get_hooks_dir as _get_hooks_dir

"""
Session-scoped evidence store for hook verification.

This module provides:
1. Durable session context (session_id, terminal_id)
2. Durable tool event storage (SQLite WAL)
3. Session-scoped reads for Stop-time validators
"""

import json
import os
import re
import sqlite3
import time
from datetime import UTC, datetime, timedelta
from hashlib import sha1
from pathlib import Path
from typing import Any

HOOKS_DIR = _get_hooks_dir()
STATE_DIR = HOOKS_DIR / "state"
SESSION_DATA_DIR = Path(os.environ.get("FRAMEGUARD_SESSION_DATA_DIR", HOOKS_DIR / "session_data"))
EVIDENCE_DB_PATH = Path(
    os.environ.get("FRAMEGUARD_EVIDENCE_DB_PATH", SESSION_DATA_DIR / "evidence.db")
)
EVIDENCE_SPOOL_DIR = SESSION_DATA_DIR / "evidence_spool"
EVIDENCE_SPOOL_IMPORT_LOCK = EVIDENCE_SPOOL_DIR / ".import.lock"

SESSION_ID_RE = re.compile(r"^[a-f0-9\-]{36}$")
TERMINAL_ID_SANITIZE_RE = re.compile(r"[^A-Za-z0-9._-]+")

try:
    from __lib.file_lock import FileLock

    FILE_LOCK_AVAILABLE = True
except Exception:
    try:
        from file_lock import FileLock  # type: ignore

        FILE_LOCK_AVAILABLE = True
    except Exception:
        FILE_LOCK_AVAILABLE = False


def _ensure_dir() -> None:
    SESSION_DATA_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_SPOOL_DIR.mkdir(parents=True, exist_ok=True)


def normalize_session_id(value: str) -> str:
    """Return normalized UUID-like session id or empty string."""
    session_id = (value or "").strip().lower()
    if SESSION_ID_RE.fullmatch(session_id):
        return session_id
    return ""


def _connect() -> sqlite3.Connection:
    _ensure_dir()
    conn = sqlite3.connect(EVIDENCE_DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    requested_mode = (os.environ.get("EVIDENCE_DB_JOURNAL_MODE", "WAL") or "WAL").upper()
    if requested_mode not in {"WAL", "DELETE", "TRUNCATE", "PERSIST", "MEMORY", "OFF"}:
        requested_mode = "WAL"
    try:
        conn.execute(f"PRAGMA journal_mode={requested_mode}")
    except sqlite3.DatabaseError:
        # Fail open to a simpler mode when WAL is not available.
        try:
            conn.execute("PRAGMA journal_mode=DELETE")
        except sqlite3.DatabaseError:
            pass
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db() -> None:
    """Initialize database schema if missing."""
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS session_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                terminal_id TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                pid INTEGER NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}'
            );

            CREATE INDEX IF NOT EXISTS idx_session_context_updated
                ON session_context(updated_at);

            CREATE TABLE IF NOT EXISTS turns (
                turn_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                terminal_id TEXT NOT NULL DEFAULT '',
                prompt TEXT NOT NULL DEFAULT '',
                transcript_path TEXT NOT NULL DEFAULT '',
                started_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                start_event_id INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active'
            );

            CREATE INDEX IF NOT EXISTS idx_turns_session_terminal_started
                ON turns(session_id, terminal_id, started_at);

            CREATE TABLE IF NOT EXISTS active_turns (
                terminal_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                turn_id TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tool_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                terminal_id TEXT NOT NULL DEFAULT '',
                ts TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                command TEXT NOT NULL DEFAULT '',
                cwd TEXT NOT NULL DEFAULT '',
                output_excerpt TEXT NOT NULL DEFAULT '',
                success INTEGER NOT NULL DEFAULT 1,
                entities_json TEXT NOT NULL DEFAULT '[]',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                event_key TEXT NOT NULL DEFAULT '',
                artifact_kind TEXT NOT NULL DEFAULT '',
                artifact_path TEXT NOT NULL DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_tool_events_session_ts
                ON tool_events(session_id, id);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_tool_events_event_key
                ON tool_events(event_key)
                WHERE event_key <> '';

            CREATE TABLE IF NOT EXISTS frameguard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sessionid TEXT NOT NULL,
                terminalid TEXT NOT NULL DEFAULT '',
                turn_id TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                needs_systemic_frame INTEGER NOT NULL DEFAULT 0,
                trigger_reason TEXT NOT NULL DEFAULT '',
                latent_questions_json TEXT NOT NULL DEFAULT '[]',
                handled INTEGER NOT NULL DEFAULT 0,
                handled_reason TEXT NOT NULL DEFAULT ''
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_frameguard_session_turn
                ON frameguard(sessionid, turn_id);

            CREATE INDEX IF NOT EXISTS idx_frameguard_session_terminal_turn
                ON frameguard(sessionid, terminalid, turn_id);

            CREATE TABLE IF NOT EXISTS epistemic_commitments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                terminal_id TEXT NOT NULL DEFAULT '',
                turn_id TEXT NOT NULL,
                claim_type TEXT NOT NULL,
                content TEXT NOT NULL,
                artifact_path TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_epistemic_commitments_session_turn
                ON epistemic_commitments(session_id, turn_id);
            CREATE INDEX IF NOT EXISTS idx_epistemic_commitments_claim_type
                ON epistemic_commitments(claim_type);

            CREATE TABLE IF NOT EXISTS epistemic_bindings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                commitment_id INTEGER NOT NULL,
                tool_event_id INTEGER NOT NULL,
                binding_kind TEXT NOT NULL,
                state_hash TEXT NOT NULL,
                is_stale INTEGER NOT NULL DEFAULT 0,
                invalidated_by_tool_event_id INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                invalidated_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_epistemic_bindings_commitment
                ON epistemic_bindings(commitment_id);
            CREATE INDEX IF NOT EXISTS idx_epistemic_bindings_tool_event
                ON epistemic_bindings(tool_event_id);
            CREATE INDEX IF NOT EXISTS idx_epistemic_bindings_is_stale
                ON epistemic_bindings(is_stale);

            CREATE UNIQUE INDEX IF NOT EXISTS idx_epistemic_bindings_unique
                ON epistemic_bindings(commitment_id, tool_event_id)
                WHERE is_stale = 0;

            CREATE TABLE IF NOT EXISTS file_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                invalidated INTEGER NOT NULL DEFAULT 0,
                invalidated_at TEXT NOT NULL,
                session_id TEXT NOT NULL,
                terminal_id TEXT NOT NULL DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_file_metadata_path
                ON file_metadata(file_path);
            """
        )
        # Lightweight schema migration for existing DBs.
        try:
            conn.execute("ALTER TABLE tool_events ADD COLUMN event_key TEXT NOT NULL DEFAULT ''")
        except sqlite3.OperationalError:
            pass


def _load_current_max_event_id(
    conn: sqlite3.Connection,
    session_id: str,
    terminal_id: str,
) -> int:
    row = conn.execute(
        """
        SELECT COALESCE(MAX(id), 0) AS max_id
        FROM tool_events
        WHERE session_id = ? AND terminal_id = ?
        """,
        (session_id, terminal_id),
    ).fetchone()
    if not row:
        return 0
    return int(row["max_id"] or 0)


def start_turn(
    session_id: str,
    terminal_id: str,
    prompt: str = "",
    transcript_path: str = "",
) -> str:
    """Create and activate a new turn for the session/terminal."""
    normalized = normalize_session_id(session_id)
    terminal = sanitize_terminal_id(terminal_id)
    if not normalized or not terminal:
        return generate_turn_id()

    turn_id = generate_turn_id()
    now_iso = datetime.now(UTC).isoformat()

    try:
        init_db()
        with _connect() as conn:
            start_event_id = _load_current_max_event_id(conn, normalized, terminal)
            conn.execute(
                """
                INSERT INTO turns (
                    turn_id, session_id, terminal_id, prompt, transcript_path,
                    started_at, updated_at, start_event_id, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
                """,
                (
                    turn_id,
                    normalized,
                    terminal,
                    str(prompt or ""),
                    str(transcript_path or ""),
                    now_iso,
                    now_iso,
                    start_event_id,
                ),
            )
            conn.execute(
                """
                INSERT INTO active_turns (terminal_id, session_id, turn_id, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(terminal_id) DO UPDATE SET
                    session_id = excluded.session_id,
                    turn_id = excluded.turn_id,
                    updated_at = excluded.updated_at
                """,
                (terminal, normalized, turn_id, now_iso),
            )
            conn.execute(
                """
                UPDATE turns
                SET status = CASE WHEN turn_id = ? THEN 'active' ELSE 'superseded' END,
                    updated_at = ?
                WHERE terminal_id = ? AND turn_id <> ? AND status = 'active'
                """,
                (turn_id, now_iso, terminal, turn_id),
            )
        return turn_id
    except (sqlite3.DatabaseError, OSError, ValueError):
        return turn_id


def get_active_turn(session_id: str, terminal_id: str) -> str | None:
    """Return active turn_id for session/terminal if present."""
    normalized = normalize_session_id(session_id)
    terminal = sanitize_terminal_id(terminal_id)
    if not normalized or not terminal:
        return None

    try:
        init_db()
        with _connect() as conn:
            row = conn.execute(
                """
                SELECT turn_id
                FROM active_turns
                WHERE terminal_id = ? AND session_id = ?
                """,
                (terminal, normalized),
            ).fetchone()
        if not row:
            return None
        return str(row["turn_id"] or "") or None
    except (sqlite3.DatabaseError, OSError, ValueError, TypeError):
        return None


def write_session_context(
    session_id: str,
    terminal_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Persist current session context for cross-hook lookup."""
    normalized = normalize_session_id(session_id)
    if not normalized:
        return False

    try:
        init_db()
    except (sqlite3.DatabaseError, OSError, ValueError):
        return False
    now_iso = datetime.now(UTC).isoformat()
    payload_metadata = metadata or {}
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO session_context (
                    session_id, terminal_id, updated_at, pid, metadata_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    normalized,
                    (terminal_id or "").strip(),
                    now_iso,
                    os.getpid(),
                    json.dumps(payload_metadata, separators=(",", ":")),
                ),
            )
        return True
    except (sqlite3.DatabaseError, OSError, ValueError):
        return False


def read_session_context() -> dict[str, Any]:
    """Read persisted session context. Returns empty dict on failure."""
    try:
        init_db()
    except (sqlite3.DatabaseError, OSError, ValueError):
        return {}
    try:
        with _connect() as conn:
            row = conn.execute(
                """
                SELECT session_id, terminal_id, updated_at, pid, metadata_json
                FROM session_context
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
        if not row:
            return {}
        metadata = {}
        raw_metadata = row["metadata_json"]
        if isinstance(raw_metadata, str) and raw_metadata:
            try:
                metadata = json.loads(raw_metadata)
            except ValueError:
                metadata = {}
        return {
            "session_id": str(row["session_id"] or ""),
            "terminal_id": str(row["terminal_id"] or ""),
            "updated_at": str(row["updated_at"] or ""),
            "pid": int(row["pid"] or 0),
            "metadata": metadata,
        }
    except (sqlite3.DatabaseError, OSError, ValueError, TypeError):
        pass
    return {}


def resolve_session_id(explicit: str = "") -> str:
    """
    Resolve session id with stable precedence:
    explicit arg > env > persisted context.
    """
    normalized = normalize_session_id(explicit)
    if normalized:
        return normalized

    env_id = normalize_session_id(os.environ.get("CLAUDE_SESSION_ID", ""))
    if env_id:
        return env_id

    ctx = read_session_context()
    return normalize_session_id(str(ctx.get("session_id", "")))


def _extract_entities(command: str, cwd: str, output_excerpt: str) -> list[str]:
    text = " ".join([command or "", cwd or "", output_excerpt or ""])
    tokens = re.findall(r"[A-Za-z0-9_./\\-]{3,}", text)
    entities: list[str] = []
    seen: set[str] = set()
    for tok in tokens:
        t = tok.strip().lower()
        if t in seen:
            continue
        seen.add(t)
        entities.append(t)
        if len(entities) >= 128:
            break
    return entities


def _safe_terminal_key(terminal_id: str) -> str:
    value = (terminal_id or "").strip()
    if not value:
        value = "unknown"
    return TERMINAL_ID_SANITIZE_RE.sub("_", value)[:80]


def _event_key(payload: dict[str, Any]) -> str:
    material = "|".join(
        [
            str(payload.get("session_id", "")),
            str(payload.get("terminal_id", "")),
            str(payload.get("ts", "")),
            str(payload.get("tool_name", "")),
            str(payload.get("command", "")),
            str(payload.get("cwd", "")),
            str(payload.get("output_excerpt", "")),
            str(payload.get("success", 1)),
        ]
    )
    return sha1(material.encode("utf-8")).hexdigest()


def _append_spool_record(record: dict[str, Any]) -> bool:
    """
    Append a tool event record to the spool file.

    This is the fallback path when SQLite writes fail. Spool files are
    imported into SQLite at stop time via import_spool_events().

    Thread-safety: Uses FileLock to prevent concurrent writes to the same
    spool file. If FileLock is unavailable or times out, falls back to a
    unique temporary file to avoid race conditions.

    Critical fix (TASK-010): When FileLock times out, do NOT fall through
    to a lock-free write. This was the race condition that could corrupt
    spool files. Instead, use a unique temp file.
    """
    _ensure_dir()
    terminal_key = _safe_terminal_key(str(record.get("terminal_id", "")))
    spool_path = EVIDENCE_SPOOL_DIR / f"events_{terminal_key}.jsonl"
    line = json.dumps(record, separators=(",", ":"), ensure_ascii=True) + "\n"
    lock_path = spool_path.with_suffix(spool_path.suffix + ".lock")

    # Try FileLock-protected write first
    if FILE_LOCK_AVAILABLE:
        try:
            with FileLock(lock_path, timeout=0.5):
                with spool_path.open("a", encoding="utf-8", newline="\n") as fh:
                    fh.write(line)
                return True
        except TimeoutError:
            # FileLock timed out - unique temp file fallback is safe because
            # no lock was held. Concurrent callers each get their own temp file.
            pass
        # Do NOT catch Exception here - OSError/PermissionError from FileLock
        # means the lock mechanism failed, not that it's unavailable. Propagating
        # is correct: we fail fast rather than silently losing spool events.

    # Fallback: unique temp file (NOT shared spool with lock-free write)
    # ONLY reachable when FILE_LOCK_AVAILABLE == False (lock never attempted).
    # When FileLock was attempted and threw, we propagate the error above.
    # This prevents the race condition where concurrent callers could
    # corrupt a shared spool file by writing without holding a lock.
    if not FILE_LOCK_AVAILABLE:
        fallback = EVIDENCE_SPOOL_DIR / f"event_{int(time.time() * 1000)}_{os.getpid()}.jsonl"
        try:
            with fallback.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(line)
            return True
        except Exception:
            return False


def _build_event_record(
    *,
    session_id: str,
    terminal_id: str,
    tool_name: str,
    command: str,
    cwd: str,
    output_excerpt: str,
    success: bool,
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    entities = _extract_entities(command, cwd, output_excerpt)
    payload_metadata = metadata or {}
    ts = datetime.now(UTC).isoformat()
    record: dict[str, Any] = {
        "session_id": session_id,
        "terminal_id": (terminal_id or "").strip(),
        "ts": ts,
        "tool_name": str(tool_name or ""),
        "command": str(command or ""),
        "cwd": str(cwd or ""),
        "output_excerpt": str(output_excerpt or ""),
        "success": 1 if success else 0,
        "entities_json": json.dumps(entities, separators=(",", ":")),
        "metadata_json": json.dumps(payload_metadata, separators=(",", ":")),
    }
    record["event_key"] = _event_key(record)
    return record


def _insert_event_row(conn: sqlite3.Connection, record: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO tool_events (
            session_id, terminal_id, ts, tool_name, command, cwd,
            output_excerpt, success, entities_json, metadata_json, event_key
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(record.get("session_id", "")),
            str(record.get("terminal_id", "")),
            str(record.get("ts", "")),
            str(record.get("tool_name", "")),
            str(record.get("command", "")),
            str(record.get("cwd", "")),
            str(record.get("output_excerpt", "")),
            int(record.get("success", 1)),
            str(record.get("entities_json", "[]")),
            str(record.get("metadata_json", "{}")),
            str(record.get("event_key", "")),
        ),
    )


def append_tool_event(
    session_id: str,
    terminal_id: str,
    tool_name: str,
    command: str = "",
    cwd: str = "",
    output_excerpt: str = "",
    success: bool = True,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Append one tool event to the durable evidence store."""
    normalized = normalize_session_id(session_id)
    if not normalized:
        return False

    record = _build_event_record(
        session_id=normalized,
        terminal_id=terminal_id,
        tool_name=tool_name,
        command=command,
        cwd=cwd,
        output_excerpt=output_excerpt,
        success=success,
        metadata=metadata,
    )
    try:
        init_db()
    except (sqlite3.DatabaseError, OSError, ValueError):
        return _append_spool_record(record)

    for _ in range(3):
        try:
            with _connect() as conn:
                _insert_event_row(conn, record)
            return True
        except sqlite3.OperationalError:
            time.sleep(0.02)
        except (sqlite3.DatabaseError, OSError, ValueError):
            break
    return _append_spool_record(record)


def load_tool_events(
    session_id: str, limit: int = 500, within_seconds: int | None = None
) -> list[dict[str, Any]]:
    """Load tool events for a session in chronological order.

    Args:
        session_id: Session UUID to filter by
        limit: Maximum number of events to return
        within_seconds: Optional TTL in seconds. Events older than this are ignored.

    Returns:
        List of tool event dictionaries
    """
    normalized = normalize_session_id(session_id)
    if not normalized:
        return []

    try:
        init_db()
    except (sqlite3.DatabaseError, OSError, ValueError):
        return []

    where_clause = "session_id = ?"
    params = [normalized]

    if within_seconds is not None:
        cutoff = (datetime.now(UTC) - timedelta(seconds=within_seconds)).isoformat()
        where_clause += " AND ts >= ?"
        params.append(cutoff)

    try:
        with _connect() as conn:
            # Build static SQL with conditional WHERE clause
            if within_seconds is not None:
                sql = """
                    SELECT id, session_id, terminal_id, ts, tool_name, command, cwd,
                           output_excerpt, success, entities_json, metadata_json
                    FROM tool_events
                    WHERE session_id = ? AND ts >= ?
                    ORDER BY id DESC
                    LIMIT ?
                """
            else:
                sql = """
                    SELECT id, session_id, terminal_id, ts, tool_name, command, cwd,
                           output_excerpt, success, entities_json, metadata_json
                    FROM tool_events
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                """
            rows = conn.execute(sql, (*params, max(1, int(limit)))).fetchall()
    except (sqlite3.DatabaseError, OSError, ValueError):
        return []

    rows = list(reversed(rows))
    events: list[dict[str, Any]] = []
    for row in rows:
        events.append(
            {
                "id": int(row["id"]),
                "name": str(row["tool_name"] or ""),
                "timestamp": str(row["ts"] or ""),
                "command": str(row["command"] or ""),
                "cwd": str(row["cwd"] or ""),
                "output": str(row["output_excerpt"] or ""),
                "session_id": str(row["session_id"] or ""),
                "terminal_id": str(row["terminal_id"] or ""),
                "success": bool(row["success"]),
            }
        )
    return events


def load_tool_events_for_context(
    session_id: str,
    terminal_id: str,
    limit: int = 500,
    within_seconds: int | None = None,
    use_turn_scoping: bool | None = None,
) -> list[dict[str, Any]]:
    """
    Load tool events filtered by BOTH session_id AND terminal_id.

    This is a terminal-aware variant of load_tool_events() for multi-terminal safety.
    Returns empty list if terminal_id is empty (no terminal context available).

    When use_turn_scoping=True, only returns events from the current turn
    (events with id > turn start event id from the active turn record).
    When use_turn_scoping is None, falls back to VERIFICATION_USE_TURN_SCOPING.

    Args:
        session_id: Session identifier to filter by
        terminal_id: Terminal identifier to filter by (required)
        limit: Maximum number of events to return (default 500)
        within_seconds: Only return events within this many seconds (optional)
        use_turn_scoping: Explicit turn-scoping override. None = env-controlled.

    Returns:
        List of tool event dictionaries with keys:
        - id: Event ID
        - name: Tool name
        - timestamp: ISO timestamp
        - command: Bash command (if applicable)
        - cwd: Working directory
        - output: Tool output excerpt
        - session_id: Session identifier
        - terminal_id: Terminal identifier
        - success: Whether the tool succeeded
    """
    if not terminal_id:
        return []

    try:
        init_db()
        conn = _connect()
        cur = conn.cursor()

        sql = """
            SELECT id, tool_name, ts, command, cwd, output_excerpt, session_id, terminal_id, success
            FROM tool_events
            WHERE session_id = ? AND terminal_id = ?
        """
        params: list[Any] = [session_id, terminal_id]

        if use_turn_scoping is None:
            use_turn_scoping = (
                os.environ.get("VERIFICATION_USE_TURN_SCOPING", "false").lower() == "true"
            )
        if use_turn_scoping:
            turn_start_id = _load_turn_start_event_id(session_id, terminal_id)
            if turn_start_id is not None and turn_start_id >= 0:
                sql += " AND id > ?"
                params.append(turn_start_id)

        if within_seconds is not None:
            cutoff = (datetime.now(UTC) - timedelta(seconds=within_seconds)).isoformat()
            sql += " AND ts >= ?"
            params.append(cutoff)

        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        cur.execute(sql, params)
        rows = cur.fetchall()
    except (sqlite3.DatabaseError, OSError, ValueError):
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass

    events = []
    for row in reversed(rows):  # Chronological order (oldest first)
        events.append(
            {
                "id": int(row["id"]),
                "name": str(row["tool_name"]),
                "timestamp": str(row["ts"]),
                "command": str(row["command"] or ""),
                "cwd": str(row["cwd"] or ""),
                "output": str(row["output_excerpt"] or ""),
                "session_id": str(row["session_id"] or ""),
                "terminal_id": str(row["terminal_id"] or ""),
                "success": bool(row["success"]),
            }
        )
    return events


def read_events_for_file(
    session_id: str,
    terminal_id: str,
    file_path: str,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """
    Load Read tool events for a specific file, scoped by session and terminal.

    This is the primary API for Phase 1 citation verification. When the model
    claims "the document says X", this function verifies whether a Read tool
    event exists for that file in the current session/terminal.

    Args:
        session_id: Session UUID to filter by
        terminal_id: Terminal identifier to filter by (required per D2)
        file_path: Canonical file path to filter by (uses os.path.realpath)
        limit: Maximum number of events to return (default 500)

    Returns:
        List of Read tool event dictionaries with keys:
        - id: Event ID
        - name: Tool name ('Read')
        - timestamp: ISO timestamp
        - command: The file path that was read
        - cwd: Working directory
        - output: Tool output excerpt
        - session_id: Session identifier
        - terminal_id: Terminal identifier
        - success: Whether the tool succeeded
    """
    normalized = normalize_session_id(session_id)
    if not normalized:
        return []

    if not terminal_id:
        return []

    if not file_path:
        return []

    # Canonical path for comparison (D6: os.path.realpath())
    import os

    canonical_file = os.path.realpath(file_path)

    try:
        init_db()
    except (sqlite3.DatabaseError, OSError, ValueError):
        return []

    try:
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT id, tool_name, ts, command, cwd, output_excerpt,
                       session_id, terminal_id, success
                FROM tool_events
                WHERE session_id = ? AND terminal_id = ? AND tool_name = 'Read'
                ORDER BY id DESC
                LIMIT ?
                """,
                (normalized, terminal_id, max(1, int(limit))),
            ).fetchall()
    except (sqlite3.DatabaseError, OSError, ValueError):
        return []

    events: list[dict[str, Any]] = []
    for row in rows:
        # Canonical path comparison (D6)
        stored_path = os.path.realpath(str(row["command"] or ""))
        if stored_path == canonical_file:
            events.append(
                {
                    "id": int(row["id"]),
                    "name": str(row["tool_name"] or ""),
                    "timestamp": str(row["ts"] or ""),
                    "command": str(row["command"] or ""),
                    "cwd": str(row["cwd"] or ""),
                    "output": str(row["output_excerpt"] or ""),
                    "session_id": str(row["session_id"] or ""),
                    "terminal_id": str(row["terminal_id"] or ""),
                    "success": bool(row["success"]),
                }
            )

    return list(reversed(events))  # Chronological order


def _load_turn_start_event_id(session_id: str, terminal_id: str) -> int | None:
    """Load turn_start_event_id from the active DB-backed turn record."""

    try:
        normalized = normalize_session_id(session_id)
        terminal = sanitize_terminal_id(terminal_id)
        if normalized and terminal:
            init_db()
            with _connect() as conn:
                row = conn.execute(
                    """
                    SELECT t.start_event_id
                    FROM active_turns a
                    JOIN turns t ON t.turn_id = a.turn_id
                    WHERE a.session_id = ? AND a.terminal_id = ?
                    """,
                    (normalized, terminal),
                ).fetchone()
            if row is not None:
                return int(row["start_event_id"] or 0)
    except (sqlite3.DatabaseError, OSError, ValueError, TypeError):
        return None
    return None


def import_spool_events(
    max_files: int = 120,
    time_budget_ms: int | None = None,
) -> dict[str, int]:
    """
    Best-effort importer from JSONL spool files into SQLite.

    Intended for Stop-time invocation. Never raises.
    """
    stats = {
        "imported": 0,
        "skipped": 0,
        "failed": 0,
        "files": 0,
        "deduped": 0,
        "timed_out": 0,
    }
    if time_budget_ms is None:
        raw_budget = os.environ.get("EVIDENCE_SPOOL_IMPORT_BUDGET_MS", "120")
        try:
            time_budget_ms = max(10, int(raw_budget))
        except Exception:
            time_budget_ms = 120
    started = time.perf_counter()
    try:
        _ensure_dir()
        spool_files = sorted(EVIDENCE_SPOOL_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
        if not spool_files:
            return stats
        spool_files = spool_files[: max(1, int(max_files))]
    except Exception:
        return stats

    def _run_import() -> dict[str, int]:
        try:
            init_db()
        except (sqlite3.DatabaseError, OSError, ValueError):
            return stats
        for spool_path in spool_files:
            if ((time.perf_counter() - started) * 1000.0) >= float(time_budget_ms):
                stats["timed_out"] = 1
                break
            stats["files"] += 1
            lock_path = spool_path.with_suffix(spool_path.suffix + ".lock")

            def _process_file() -> None:
                try:
                    lines = spool_path.read_text(encoding="utf-8").splitlines()
                except Exception:
                    stats["failed"] += 1
                    return
                malformed: list[str] = []
                parsed_records: list[dict[str, Any]] = []
                for line in lines:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        if not isinstance(record, dict):
                            malformed.append(line)
                            continue
                        if "event_key" not in record:
                            record["event_key"] = _event_key(record)
                        parsed_records.append(record)
                    except Exception:
                        malformed.append(line)

                inserted = 0
                if parsed_records:
                    try:
                        with _connect() as conn:
                            for record in parsed_records:
                                before = int(conn.total_changes)
                                _insert_event_row(conn, record)
                                after = int(conn.total_changes)
                                if after > before:
                                    inserted += 1
                        stats["imported"] += inserted
                        stats["deduped"] += max(0, len(parsed_records) - inserted)
                    except Exception:
                        stats["failed"] += len(parsed_records)
                        return
                stats["skipped"] += len(malformed)
                try:
                    if malformed:
                        spool_path.write_text("\n".join(malformed) + "\n", encoding="utf-8")
                    else:
                        spool_path.unlink(missing_ok=True)
                except Exception:
                    pass

            try:
                if FILE_LOCK_AVAILABLE:
                    with FileLock(lock_path, timeout=0.05):
                        _process_file()
                else:
                    _process_file()
            except TimeoutError:
                # Another writer/importer is using this file; retry next Stop run.
                continue
            except Exception:
                stats["failed"] += 1
        return stats

    if FILE_LOCK_AVAILABLE:
        try:
            with FileLock(EVIDENCE_SPOOL_IMPORT_LOCK, timeout=0.2):
                return _run_import()
        except TimeoutError:
            return stats
        except Exception:
            return stats
    return _run_import()


def write_artifact_event(
    artifact_kind: str,
    path: str,
    content_snippet: str,
    session_id: str = "",
    terminal_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> bool:
    """
    Write a task/skill artifact event directly to evidence spool.

    This complements tool_events which are written by PostToolUse hooks.
    Artifacts include: review results (*.review.result.json), skill outputs,
    test results, etc.

    Args:
        artifact_kind: Type of artifact ('review_result', 'skill_output', 'test_run', 'task_artifact')
        path: Path to artifact file
        content_snippet: Content excerpt (max 2000 chars)
        session_id: Session UUID
        terminal_id: Optional terminal ID
        metadata: Optional additional metadata

    Returns:
        True if successful, False otherwise
    """
    normalized = normalize_session_id(session_id)
    if not normalized:
        return False

    timestamp = datetime.now(UTC).isoformat()

    # Build event record in same format as spool entries
    base_metadata = {
        "artifact_kind": artifact_kind,
        "artifact_path": path,
    }
    base_metadata.update(metadata or {})

    event = {
        "session_id": normalized,
        "terminal_id": (terminal_id or "").strip(),
        "ts": timestamp,
        "tool_name": "artifact",
        "command": "",
        "cwd": "",
        "output_excerpt": (content_snippet or "")[:2000],
        "success": True,
        "entities_json": "[]",
        "metadata_json": json.dumps(base_metadata),
        "event_key": _event_key(
            {
                "session_id": normalized,
                "terminal_id": (terminal_id or "").strip(),
                "ts": timestamp,
                "tool_name": "artifact",
            }
        ),
    }

    # Write to spool file for Stop hook to import
    try:
        _ensure_dir()

        # Create spool filename with timestamp for uniqueness
        spool_filename = f"artifact_{timestamp.replace(':', '-').replace('+', '')}.jsonl"
        spool_path = EVIDENCE_SPOOL_DIR / spool_filename

        # Write as JSONL (same format as tool spool entries)
        with open(spool_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

        return True
    except (OSError, ValueError):
        return False


# === FrameGuard Helper Functions ===


def generate_turn_id() -> str:
    """Generate a unique turn ID using timestamp + random.

    Returns:
        A unique turn ID string (format: timestamp_random)
    """
    import uuid

    return f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


def sanitize_terminal_id(terminal_id: str) -> str:
    """Sanitize terminal_id for safe file/database usage.

    Args:
        terminal_id: The terminal ID to sanitize

    Returns:
        Sanitized terminal_id safe for filesystem/database use
    """
    if not terminal_id:
        return "unknown"
    return TERMINAL_ID_SANITIZE_RE.sub("_", str(terminal_id))[:80]


def validate_latent_questions(questions: list) -> bool:
    """Validate latent_questions structure.

    Args:
        questions: List of latent question dictionaries

    Returns:
        True if structure is valid, False otherwise
    """
    if not isinstance(questions, list):
        return False
    for q in questions:
        if not isinstance(q, dict):
            return False
        if "id" not in q or "question" not in q:
            return False
    return True


def get_or_create_turn(session_id: str, terminal_id: str) -> str:
    """Get existing turn_id or generate new one.

    Checks evidence_store for an existing active turn, generates new ID if none found.

    Args:
        session_id: Current session ID
        terminal_id: Current terminal ID

    Returns:
        A turn ID string
    """
    existing_turn = get_active_turn(session_id, terminal_id)
    if existing_turn:
        return existing_turn
    return start_turn(session_id=session_id, terminal_id=terminal_id)


def record_frameguard_trigger(
    session_id: str,
    terminal_id: str,
    turn_id: str,
    needs_systemic_frame: bool,
    trigger_reason: str,
    latent_questions: list,
) -> bool:
    """Record FrameGuard trigger in evidence store.

    Args:
        session_id: Current session ID
        terminal_id: Current terminal ID
        turn_id: Current turn ID
        needs_systemic_frame: Whether systemic frame is required
        trigger_reason: Reason for the trigger
        latent_questions: List of latent question dictionaries

    Returns:
        True on success, False on failure (fail-open)
    """
    # Validate inputs
    if not validate_latent_questions(latent_questions):
        latent_questions = []

    terminal = sanitize_terminal_id(terminal_id)
    session = normalize_session_id(session_id)
    turn = str(turn_id)

    if not session or not turn:
        return False

    try:
        init_db()
        with _connect() as conn:
            # Use INSERT OR IGNORE to prevent silent overwrites
            # If a record already exists for this session/turn, preserve it
            conn.execute(
                """
                INSERT OR IGNORE INTO frameguard (
                    sessionid, terminalid, turn_id, created_at,
                    needs_systemic_frame, trigger_reason, latent_questions_json
                ) VALUES (?, ?, ?, datetime('now'), ?, ?, ?)
                """,
                (
                    session,
                    terminal,
                    turn,
                    1 if needs_systemic_frame else 0,
                    trigger_reason,
                    json.dumps(latent_questions),
                ),
            )
        return True
    except sqlite3.Error:
        # Log warning but don't fail (fail-open pattern)
        return False


def mark_frameguard_handled(
    session_id: str,
    terminal_id: str,
    turn_id: str,
    handled: bool,
    handled_reason: str,
) -> bool:
    """Mark FrameGuard state as handled.

    Args:
        session_id: Current session ID
        terminal_id: Current terminal ID
        turn_id: Current turn ID
        handled: Whether the frame was handled
        handled_reason: Reason for the handling status

    Returns:
        True on success, False on failure (fail-open)
    """
    terminal = sanitize_terminal_id(terminal_id)
    session = normalize_session_id(session_id)
    turn = str(turn_id)

    if not session or not turn:
        return False

    try:
        init_db()
        with _connect() as conn:
            # Add WHERE handled = 0 to prevent overwriting already-handled state
            # This prevents race conditions where multiple turns try to mark the same state
            conn.execute(
                """
                UPDATE frameguard
                SET handled = ?, handled_reason = ?
                WHERE sessionid = ? AND terminalid = ? AND turn_id = ? AND handled = 0
                """,
                (1 if handled else 0, handled_reason, session, terminal, turn),
            )
        return True
    except sqlite3.Error:
        return False  # Fail open


def load_frameguard_state(
    session_id: str,
    terminal_id: str,
    turn_id: str,
) -> dict | None:
    """Load FrameGuard state for a turn.

    Args:
        session_id: Current session ID
        terminal_id: Current terminal ID
        turn_id: Current turn ID

    Returns:
        FrameGuard state dict, or None if not found or on error (fail-open)
    """
    terminal = sanitize_terminal_id(terminal_id)
    session = normalize_session_id(session_id)
    turn = str(turn_id)

    if not session or not turn:
        return None

    try:
        init_db()
        with _connect() as conn:
            row = conn.execute(
                """
                SELECT id, sessionid, terminalid, turn_id, created_at,
                       needs_systemic_frame, trigger_reason, latent_questions_json,
                       handled, handled_reason
                FROM frameguard
                WHERE sessionid = ? AND terminalid = ? AND turn_id = ?
                """,
                (session, terminal, turn),
            ).fetchone()

        if not row:
            return None

        return {
            "id": int(row["id"]),
            "session_id": str(row["sessionid"] or ""),
            "terminal_id": str(row["terminalid"] or ""),
            "turn_id": str(row["turn_id"] or ""),
            "created_at": str(row["created_at"] or ""),
            "needs_systemic_frame": bool(row["needs_systemic_frame"]),
            "trigger_reason": str(row["trigger_reason"] or ""),
            "latent_questions": json.loads(row["latent_questions_json"] or "[]"),
            "handled": bool(row["handled"]),
            "handled_reason": str(row["handled_reason"] or ""),
        }
    except (sqlite3.Error, ValueError, json.JSONDecodeError):
        return None  # Fail open


# ----------------------------------------------------------------------
# Epistemic Commitments and Bindings CRUD functions
# ----------------------------------------------------------------------


def write_epistemic_commitment(
    session_id: str,
    terminal_id: str,
    turn_id: str,
    claim_type: str,
    content: str,
    artifact_path: str = "",
) -> bool:
    """Write an epistemic commitment to the evidence store.

    Args:
        session_id: Session identifier
        terminal_id: Terminal identifier
        turn_id: Turn identifier
        claim_type: Type of commitment (e.g., "Evidence", "Root Cause")
        content: Commitment content text
        artifact_path: Associated artifact path (optional)

    Returns:
        True on success, False on failure (fail-open)
    """
    session = normalize_session_id(session_id)
    if not session:
        return False

    try:
        init_db()
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO epistemic_commitments
                (session_id, terminal_id, turn_id, claim_type, content, artifact_path)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session, terminal_id or "", turn_id, claim_type, content, artifact_path or ""),
            )
            conn.commit()  # Explicit commit for raw sqlite3.Connection
        return True
    except sqlite3.Error as e:
        import sys

        print(f"DEBUG: write_epistemic_commitment sqlite3.Error: {e}", file=sys.stderr)
        return False  # Fail open


def load_epistemic_commitments(
    session_id: str,
    terminal_id: str,
    turn_id: str | None = None,
    claim_type: str | None = None,
) -> list[dict[str, Any]]:
    """Load epistemic commitments for a session/turn.

    Args:
        session_id: Session identifier
        terminal_id: Terminal identifier
        turn_id: Optional turn identifier to filter by
        claim_type: Optional claim type to filter by

    Returns:
        List of commitment dictionaries with keys:
        - id: Commitment ID
        - session_id: Session identifier
        - terminal_id: Terminal identifier
        - turn_id: Turn identifier
        - claim_type: Type of commitment
        - content: Commitment content
        - artifact_path: Associated artifact path
        - created_at: Creation timestamp
    """
    session = normalize_session_id(session_id)
    if not session:
        return []

    try:
        init_db()
        with _connect() as conn:
            sql = """
                SELECT id, session_id, terminal_id, turn_id, claim_type, content, artifact_path, created_at
                FROM epistemic_commitments
                WHERE session_id = ? AND terminal_id = ?
            """
            params: list[Any] = [session, terminal_id or ""]

            if turn_id:
                sql += " AND turn_id = ?"
                params.append(turn_id)

            if claim_type:
                sql += " AND claim_type = ?"
                params.append(claim_type)

            sql += " ORDER BY id ASC"

            cur = conn.execute(sql, params)
            rows = cur.fetchall()

            return [
                {
                    "id": int(row["id"]),
                    "session_id": str(row["session_id"] or ""),
                    "terminal_id": str(row["terminal_id"] or ""),
                    "turn_id": str(row["turn_id"] or ""),
                    "claim_type": str(row["claim_type"] or ""),
                    "content": str(row["content"] or ""),
                    "artifact_path": str(row["artifact_path"] or ""),
                    "created_at": str(row["created_at"] or ""),
                }
                for row in rows
            ]
    except sqlite3.Error:
        return []  # Fail open


def create_epistemic_binding(
    commitment_id: int,
    tool_event_id: int,
    binding_kind: str,
    state_hash: str,
) -> bool:
    """Create an epistemic binding between a commitment and tool event.

    Args:
        commitment_id: ID of the epistemic commitment
        tool_event_id: ID of the tool event that provides evidence
        binding_kind: Kind of binding (e.g., "supports", "contradicts", "unrelated")
        state_hash: Hash of the artifact state for staleness detection

    Returns:
        True on success, False on failure (fail-open)
    """
    try:
        init_db()
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO epistemic_bindings
                (commitment_id, tool_event_id, binding_kind, state_hash)
                VALUES (?, ?, ?, ?)
                """,
                (commitment_id, tool_event_id, binding_kind, state_hash),
            )
            conn.commit()  # Explicit commit for raw sqlite3.Connection
        return True
    except sqlite3.Error as e:
        import sys

        print(f"DEBUG: create_epistemic_binding sqlite3.Error: {e}", file=sys.stderr)
        return False  # Fail open


def load_epistemic_bindings(
    commitment_id: int | None = None,
    session_id: str | None = None,
    terminal_id: str | None = None,
    include_stale: bool = False,
) -> list[dict[str, Any]]:
    """Load epistemic bindings, optionally filtering by commitment or session.

    Args:
        commitment_id: Optional commitment ID to filter by
        session_id: Optional session ID to filter by
        terminal_id: Optional terminal ID to filter by
        include_stale: Whether to include stale bindings (default False)

    Returns:
        List of binding dictionaries with keys:
        - id: Binding ID
        - commitment_id: Commitment ID
        - tool_event_id: Tool event ID
        - binding_kind: Kind of binding
        - state_hash: State hash for staleness detection
        - is_stale: Whether binding is marked stale
        - invalidated_by_tool_event_id: Tool event ID that invalidated this (if stale)
        - created_at: Creation timestamp
        - invalidated_at: Invalid timestamp (if stale)
    """
    try:
        init_db()
        with _connect() as conn:
            sql = """
                SELECT
                    id, commitment_id, tool_event_id, binding_kind, state_hash,
                    is_stale, invalidated_by_tool_event_id, created_at, invalidated_at
                FROM epistemic_bindings
                WHERE 1=1
            """
            params: list[Any] = []

            if commitment_id is not None:
                sql += " AND commitment_id = ?"
                params.append(commitment_id)

            if session_id:
                # Join with commitments table to filter by session
                sql += """
                AND commitment_id IN (
                    SELECT id FROM epistemic_commitments
                    WHERE session_id = ?
                )
                """
                params.append(normalize_session_id(session_id) or "")

            if terminal_id:
                # Join with commitments table to filter by terminal
                sql += """
                AND commitment_id IN (
                    SELECT id FROM epistemic_commitments
                    WHERE terminal_id = ?
                )
                """
                params.append(terminal_id or "")

            if not include_stale:
                sql += " AND is_stale = 0"

            sql += " ORDER BY id ASC"

            cur = conn.execute(sql, params)
            rows = cur.fetchall()

            return [
                {
                    "id": int(row["id"]),
                    "commitment_id": int(row["commitment_id"]),
                    "tool_event_id": int(row["tool_event_id"]),
                    "binding_kind": str(row["binding_kind"] or ""),
                    "state_hash": str(row["state_hash"] or ""),
                    "binding_value": str(row["state_hash"] or ""),  # Alias for clarity
                    "is_stale": bool(row["is_stale"]),
                    "invalidated_by_tool_event_id": int(row["invalidated_by_tool_event_id"])
                    if row["invalidated_by_tool_event_id"]
                    else None,
                    "created_at": str(row["created_at"] or ""),
                    "invalidated_at": str(row["invalidated_at"] or "")
                    if row["invalidated_at"]
                    else None,
                }
                for row in rows
            ]
    except sqlite3.Error:
        return []  # Fail open


def mark_binding_stale(
    binding_id: int,
    invalidated_by_tool_event_id: int,
) -> bool:
    """Mark an epistemic binding as stale due to state mutation.

    Args:
        binding_id: ID of the binding to mark stale
        invalidated_by_tool_event_id: Tool event ID that caused invalidation

    Returns:
        True on success, False on failure (fail-open)
    """
    try:
        init_db()
        with _connect() as conn:
            conn.execute(
                """
                UPDATE epistemic_bindings
                SET is_stale = 1,
                    invalidated_by_tool_event_id = ?,
                    invalidated_at = (datetime('now'))
                WHERE id = ?
                """,
                (invalidated_by_tool_event_id, binding_id),
            )
            conn.commit()  # Explicit commit for raw sqlite3.Connection
        return True
    except sqlite3.Error:
        return False  # Fail open


def mark_bindings_stale_for_artifact(
    session_id: str,
    terminal_id: str,
    artifact_path: str,
    invalidated_by_tool_event_id: int,
) -> int:
    """Mark all bindings for an artifact as stale (mutation invalidation).

    Args:
        session_id: Session identifier
        terminal_id: Terminal identifier
        artifact_path: Path of the artifact that was mutated
        invalidated_by_tool_event_id: Tool event ID that caused invalidation

    Returns:
        Number of bindings marked stale (0 on error)
    """
    session = normalize_session_id(session_id)
    if not session:
        return 0

    try:
        init_db()
        with _connect() as conn:
            # Find all commitments related to this artifact
            # Then mark their bindings as stale
            cursor = conn.execute(
                """
                UPDATE epistemic_bindings
                SET is_stale = 1,
                    invalidated_by_tool_event_id = ?,
                    invalidated_at = (datetime('now'))
                WHERE commitment_id IN (
                    SELECT id FROM epistemic_commitments
                    WHERE session_id = ? AND terminal_id = ? AND artifact_path = ?
                )
                """,
                (invalidated_by_tool_event_id, session, terminal_id or "", artifact_path),
            )
            return cursor.rowcount
    except sqlite3.Error:
        return 0  # Fail open


def mark_file_invalidated(
    path: str,
    session_id: str = "",
    terminal_id: str = "",
) -> bool:
    """Mark a file as invalidated in the file_metadata table.

    Uses INSERT OR REPLACE to upsert the invalidation record.

    Args:
        path: Absolute file path to mark as invalidated
        session_id: Session that performed the invalidation
        terminal_id: Terminal that performed the invalidation

    Returns:
        True on success, False on failure (fail-open)
    """
    if not path:
        return False
    try:
        init_db()
        now_iso = datetime.now(UTC).isoformat()
        session = normalize_session_id(session_id) if session_id else ""
        with _connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO file_metadata (
                    file_path, invalidated, invalidated_at, session_id, terminal_id
                ) VALUES (?, 1, ?, ?, ?)
                """,
                (str(path), now_iso, session, (terminal_id or "").strip()),
            )
        return True
    except (sqlite3.Error, OSError, ValueError):
        return False  # Fail open


def is_file_invalidated(path: str) -> bool:
    """Check if a file has been marked as invalidated.

    Args:
        path: Absolute file path to check

    Returns:
        True if file is marked invalidated, False otherwise
    """
    if not path:
        return False
    try:
        init_db()
        with _connect() as conn:
            row = conn.execute(
                """
                SELECT invalidated FROM file_metadata
                WHERE file_path = ? AND invalidated = 1
                LIMIT 1
                """,
                (str(path),),
            ).fetchone()
        return row is not None
    except (sqlite3.Error, OSError, ValueError):
        return False  # Fail open
