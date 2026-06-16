#!/usr/bin/env python3
"""Terminal + turn scoped hook ledger.

Authoritative hook state for multi-terminal isolation and stale-data immunity.

Design:
- SQLite WAL is the primary store
- JSONL spool is fallback when SQLite is unavailable
- terminal_id + turn_id is the correctness boundary
- session_id is diagnostic metadata only
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

STATE_DIR = Path("P:/.claude/state")
LOG_DIR = Path("P:/.claude/logs")
DB_PATH = STATE_DIR / "hook_ledger.db"
SPOOL_DIR = STATE_DIR / "hook_ledger_spool"
TURN_MARKERS_DIR = STATE_DIR / "turn_markers"
ANOMALY_LOG = LOG_DIR / "hook_ledger_anomalies.jsonl"

# Feature flag for turn scoping (default: disabled for safety)
VERIFICATION_USE_TURN_SCOPING = (
    os.environ.get("VERIFICATION_USE_TURN_SCOPING", "false").lower() == "true"
)

OBSERVATION_TOOL_NAMES = frozenset(
    {
        "Read",
        "Grep",
        "Glob",
        "Bash",
        "View",
        "WebFetch",
    }
)

DEFAULT_TRANSCRIPT_TAIL_BYTES = 8 * 1024 * 1024
_SYSTEM_REMINDER_RE = re.compile(r"<system-reminder\b[^>]*>.*?</system-reminder>", re.IGNORECASE | re.DOTALL)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _safe_terminal_key(terminal_id: str) -> str:
    text = (terminal_id or "").strip() or "unknown"
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in text)[:96]


def _log_anomaly(event: str, payload: dict[str, Any]) -> None:
    try:
        ANOMALY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ANOMALY_LOG.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "ts": _utcnow(),
                        "event": event,
                        **payload,
                    },
                    ensure_ascii=True,
                )
                + "\n"
            )
    except OSError:
        pass


def _write_turn_marker(
    session_id: str,
    terminal_id: str,
    event_id: int,
) -> bool:
    """Write JSON turn marker file for turn-scoped context filtering.

    Args:
        session_id: Session identifier
        terminal_id: Terminal identifier
        event_id: The event_id from the turn_events table

    Returns:
        True if write succeeded, False otherwise
    """
    if not VERIFICATION_USE_TURN_SCOPING:
        return True  # Skip if feature flag disabled

    try:
        TURN_MARKERS_DIR.mkdir(parents=True, exist_ok=True)
        safe_terminal = _safe_terminal_key(terminal_id)
        safe_session = _safe_terminal_key(session_id)
        marker_path = TURN_MARKERS_DIR / f"turn_start_{safe_session}__{safe_terminal}.json"
        marker_data = {
            "turn_start_event_id": event_id,
            "session_id": session_id,
            "terminal_id": terminal_id,
        }
        with marker_path.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps(marker_data, ensure_ascii=True, separators=(",", ":")))
        return True
    except OSError:
        _log_anomaly(
            "turn_marker_write_failed", {"session_id": session_id, "terminal_id": terminal_id}
        )
        return False


def _canonical_json(payload: Any) -> str:
    try:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except TypeError:
        return json.dumps(str(payload), separators=(",", ":"), ensure_ascii=True)


def _transcript_tail_bytes() -> int:
    raw = os.environ.get("HOOK_LEDGER_TRANSCRIPT_TAIL_BYTES", "").strip()
    if not raw:
        return DEFAULT_TRANSCRIPT_TAIL_BYTES
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_TRANSCRIPT_TAIL_BYTES
    return max(64 * 1024, value)


def _read_recent_transcript_lines(path: Path) -> list[str]:
    """Read only the recent JSONL tail needed for Stop-time extraction.

    Transcript files can grow into hundreds of MB or more. Stop hooks only need
    the latest user/assistant exchange, so scanning the full file creates
    latency proportional to transcript size. Reading the tail keeps runtime
    bounded while preserving the most recent entries.
    """
    try:
        size = path.stat().st_size
    except OSError:
        return []

    initial_tail_bytes = _transcript_tail_bytes()
    if size <= initial_tail_bytes:
        try:
            return path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []

    read_bytes = min(size, initial_tail_bytes)
    chunk = b""
    while read_bytes <= size:
        try:
            with path.open("rb") as fh:
                fh.seek(max(0, size - read_bytes))
                chunk = fh.read()
        except OSError:
            return []

        if not chunk:
            return []

        if read_bytes >= size:
            break

        # Stop once the window includes a real line boundary before the latest
        # records. If the last JSONL line is itself very large, keep expanding
        # until we reach the newline that starts it.
        trimmed = chunk.rstrip(b"\r\n")
        newline_index = trimmed.find(b"\n")
        if newline_index >= 0:
            chunk = trimmed[newline_index + 1 :]
            break

        if read_bytes == size:
            break
        read_bytes = min(size, read_bytes * 2)

    if not chunk:
        return []

    return chunk.decode("utf-8", errors="ignore").splitlines()


def _classify_assistant_text(message_content: object) -> tuple[str, str]:
    """Return normalized assistant text plus a coarse message kind.

    Kinds:
    - assistant: substantive assistant response text
    - system_reminder: reminder-only wrapper with no substantive content
    - empty: no text content present
    """
    if isinstance(message_content, list):
        raw_text = " ".join(
            block.get("text", "")
            for block in message_content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    elif isinstance(message_content, str):
        raw_text = message_content
    else:
        raw_text = ""

    raw_text = str(raw_text).strip()
    if not raw_text:
        return "", "empty"

    normalized = _SYSTEM_REMINDER_RE.sub(" ", raw_text)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if normalized:
        return normalized, "assistant"
    if _SYSTEM_REMINDER_RE.search(raw_text):
        return "", "system_reminder"
    return "", "empty"


def _extract_text_content(message_content: object) -> str:
    if isinstance(message_content, list):
        return " ".join(
            block.get("text", "")
            for block in message_content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    if isinstance(message_content, str):
        return message_content
    return ""


def _event_key(
    terminal_id: str,
    turn_id: str,
    phase: str,
    event_type: str,
    payload: dict[str, Any],
) -> str:
    material = "|".join(
        (
            terminal_id,
            turn_id,
            phase,
            event_type,
            _canonical_json(payload),
        )
    )
    return hashlib.sha1(material.encode("utf-8")).hexdigest()


def _connect() -> sqlite3.Connection:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.DatabaseError:
        conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS turns (
                turn_id TEXT PRIMARY KEY,
                terminal_id TEXT NOT NULL,
                session_id TEXT NOT NULL DEFAULT '',
                prompt TEXT NOT NULL DEFAULT '',
                transcript_path TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'open',
                outcome_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_turns_terminal_status
                ON turns(terminal_id, status, updated_at);

            CREATE TABLE IF NOT EXISTS active_turns (
                terminal_id TEXT PRIMARY KEY,
                turn_id TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS turn_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                terminal_id TEXT NOT NULL,
                turn_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                event_type TEXT NOT NULL,
                ts TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                event_key TEXT NOT NULL DEFAULT ''
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_turn_events_event_key
                ON turn_events(event_key)
                WHERE event_key <> '';

            CREATE INDEX IF NOT EXISTS idx_turn_events_turn
                ON turn_events(turn_id, id);

            CREATE INDEX IF NOT EXISTS idx_turn_events_terminal
                ON turn_events(terminal_id, id);
            """
        )


def _build_spool_record(
    terminal_id: str,
    turn_id: str,
    phase: str,
    event_type: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "terminal_id": terminal_id,
        "turn_id": turn_id,
        "phase": phase,
        "event_type": event_type,
        "ts": _utcnow(),
        "payload": payload,
        "event_key": _event_key(terminal_id, turn_id, phase, event_type, payload),
    }


def _append_spool_record(record: dict[str, Any]) -> bool:
    try:
        SPOOL_DIR.mkdir(parents=True, exist_ok=True)
        spool_path = (
            SPOOL_DIR / f"events_{_safe_terminal_key(str(record.get('terminal_id', '')))}.jsonl"
        )
        with spool_path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n")
        return True
    except OSError:
        return False


def _insert_event_row(conn: sqlite3.Connection, record: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO turn_events (
            terminal_id, turn_id, phase, event_type, ts, payload_json, event_key
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(record.get("terminal_id", "")),
            str(record.get("turn_id", "")),
            str(record.get("phase", "")),
            str(record.get("event_type", "")),
            str(record.get("ts", "")),
            _canonical_json(record.get("payload", {})),
            str(record.get("event_key", "")),
        ),
    )


def _scan_spool(
    *,
    terminal_id: str = "",
    turn_id: str = "",
    limit: int = 500,
) -> list[dict[str, Any]]:
    try:
        if not SPOOL_DIR.exists():
            return []
        paths = sorted(SPOOL_DIR.glob("events_*.jsonl"), key=lambda p: p.stat().st_mtime)
    except OSError:
        return []

    events: list[dict[str, Any]] = []
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines[-limit:]:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if terminal_id and str(record.get("terminal_id", "")) != terminal_id:
                continue
            if turn_id and str(record.get("turn_id", "")) != turn_id:
                continue
            events.append(record)
    events.sort(key=lambda item: (str(item.get("ts", "")), str(item.get("event_key", ""))))
    return events[-limit:]


def import_spool_records(max_files: int = 200) -> dict[str, int]:
    stats = {"files": 0, "imported": 0, "skipped": 0}
    try:
        if not SPOOL_DIR.exists():
            return stats
        paths = sorted(SPOOL_DIR.glob("events_*.jsonl"), key=lambda p: p.stat().st_mtime)[
            :max_files
        ]
        if not paths:
            return stats
        init_db()
    except Exception:
        return stats

    for path in paths:
        stats["files"] += 1
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        malformed: list[str] = []
        try:
            with _connect() as conn:
                for line in lines:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        malformed.append(line)
                        continue
                    before = int(conn.total_changes)
                    _insert_event_row(conn, record)
                    after = int(conn.total_changes)
                    if after > before:
                        stats["imported"] += 1
                    else:
                        stats["skipped"] += 1
        except Exception:
            continue
        try:
            if malformed:
                path.write_text("\n".join(malformed) + "\n", encoding="utf-8")
            else:
                path.unlink(missing_ok=True)
        except OSError:
            pass
    return stats


def detect_terminal_id_from_payload(data: dict[str, Any] | None = None) -> str:
    payload = data or {}
    for key in ("terminal_id", "terminalId", "CLAUDE_TERMINAL_ID"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    env_value = os.environ.get("CLAUDE_TERMINAL_ID", "").strip()
    if env_value:
        return env_value

    try:
        skill_guard_src = Path("P:/packages/.claude-marketplace/plugins/skill-guard/src")
        if skill_guard_src.exists() and str(skill_guard_src) not in sys.path:
            sys.path.insert(0, str(skill_guard_src))
        from __lib.terminal_detection import detect_terminal_id

        detected = str(detect_terminal_id() or "").strip()
        if detected:
            return detected
    except Exception:
        pass
    return ""


def start_turn(
    terminal_id: str,
    prompt: str,
    session_id: str = "",
    transcript_path: str = "",
) -> str:
    terminal = (terminal_id or "").strip()
    if not terminal:
        _log_anomaly("start_turn_missing_terminal", {"session_id": session_id})
        return ""

    turn_id = str(uuid.uuid4())
    now = _utcnow()
    payload = {
        "prompt": prompt or "",
        "session_id": session_id or "",
        "transcript_path": transcript_path or "",
    }

    prior_turn = get_active_turn(terminal)
    if prior_turn and prior_turn != turn_id:
        close_turn(terminal, prior_turn, {"status": "superseded"})

    try:
        init_db()
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO turns (
                    turn_id, terminal_id, session_id, prompt, transcript_path,
                    status, outcome_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'open', '{}', ?, ?)
                """,
                (
                    turn_id,
                    terminal,
                    session_id or "",
                    prompt or "",
                    transcript_path or "",
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO active_turns (terminal_id, turn_id, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(terminal_id) DO UPDATE SET
                    turn_id = excluded.turn_id,
                    updated_at = excluded.updated_at
                """,
                (terminal, turn_id, now),
            )
            _insert_event_row(
                conn,
                _build_spool_record(
                    terminal,
                    turn_id,
                    "UserPromptSubmit",
                    "turn_started",
                    payload,
                ),
            )
            # Write turn marker for turn-scoped context filtering
            if VERIFICATION_USE_TURN_SCOPING:
                event_id_row = conn.execute("SELECT last_insert_rowid()").fetchone()
                if event_id_row:
                    event_id = int(event_id_row[0])
                    _write_turn_marker(session_id or "", terminal, event_id)
        return turn_id
    except Exception:
        record = _build_spool_record(terminal, turn_id, "UserPromptSubmit", "turn_started", payload)
        if _append_spool_record(record):
            return turn_id
        _log_anomaly("start_turn_failed", {"terminal_id": terminal, "session_id": session_id})
        return ""


def append_event(
    terminal_id: str,
    turn_id: str,
    phase: str,
    event_type: str,
    payload: dict[str, Any],
) -> bool:
    terminal = (terminal_id or "").strip()
    turn = (turn_id or "").strip()
    if not terminal or not turn:
        _log_anomaly(
            "append_event_missing_scope",
            {
                "terminal_id": terminal,
                "turn_id": turn,
                "phase": phase,
                "event_type": event_type,
            },
        )
        return False

    record = _build_spool_record(terminal, turn, phase, event_type, payload)
    try:
        init_db()
        with _connect() as conn:
            _insert_event_row(conn, record)
            conn.execute(
                "UPDATE turns SET updated_at = ? WHERE turn_id = ?",
                (_utcnow(), turn),
            )
        return True
    except Exception:
        return _append_spool_record(record)


def get_active_turn(terminal_id: str) -> str | None:
    terminal = (terminal_id or "").strip()
    if not terminal:
        return None

    try:
        import_spool_records()
        init_db()
        with _connect() as conn:
            row = conn.execute(
                """
                SELECT turn_id
                FROM active_turns
                WHERE terminal_id = ?
                LIMIT 1
                """,
                (terminal,),
            ).fetchone()
        if row:
            return str(row["turn_id"] or "")
    except Exception:
        pass

    open_turn = ""
    for record in _scan_spool(terminal_id=terminal):
        if record.get("event_type") == "turn_started":
            open_turn = str(record.get("turn_id", ""))
        elif (
            record.get("event_type") == "turn_closed"
            and str(record.get("turn_id", "")) == open_turn
        ):
            open_turn = ""
    return open_turn or None


def close_turn(terminal_id: str, turn_id: str, outcome: dict[str, Any]) -> None:
    terminal = (terminal_id or "").strip()
    turn = (turn_id or "").strip()
    if not terminal or not turn:
        return

    outcome = outcome or {}
    status = str(outcome.get("status", "")).strip().lower()
    # The final turn state is persisted in `turns`; avoid duplicating the hot-path
    # close event for routine allow outcomes.
    if status and status != "allowed":
        append_event(terminal, turn, "Stop", "turn_closed", {"outcome": outcome})
    now = _utcnow()
    try:
        init_db()
        with _connect() as conn:
            conn.execute(
                """
                UPDATE turns
                SET status = 'closed', outcome_json = ?, updated_at = ?
                WHERE turn_id = ?
                """,
                (_canonical_json(outcome), now, turn),
            )
            conn.execute(
                "DELETE FROM active_turns WHERE terminal_id = ? AND turn_id = ?",
                (terminal, turn),
            )
    except Exception:
        pass


def _load_db_skill_events(terminal_id: str) -> list[dict[str, Any]]:
    """Load all skill_loaded events for a terminal across all turns.

    Used as a fallback when transcript-based tool tracking fails (e.g., after
    compaction resets turn context). This lets the Stop hook detect that a skill
    was loaded in a prior turn even when the current turn's transcript is empty.

    Unlike _load_db_events which is scoped to a single turn, this queries across
    all turns for the terminal.
    """
    terminal = (terminal_id or "").strip()
    if not terminal:
        return []
    try:
        import_spool_records()
        init_db()
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT id, terminal_id, turn_id, phase, event_type, ts, payload_json, event_key
                FROM turn_events
                WHERE terminal_id = ? AND event_type = 'skill_loaded'
                ORDER BY id ASC
                """,
                (terminal,),
            ).fetchall()
        events = []
        for row in rows:
            try:
                payload = json.loads(str(row["payload_json"] or "{}"))
            except ValueError:
                payload = {}
            events.append(
                {
                    "id": int(row["id"]),
                    "terminal_id": str(row["terminal_id"] or ""),
                    "turn_id": str(row["turn_id"] or ""),
                    "phase": str(row["phase"] or ""),
                    "event_type": str(row["event_type"] or ""),
                    "ts": str(row["ts"] or ""),
                    "payload": payload,
                    "event_key": str(row["event_key"] or ""),
                }
            )
        return events
    except Exception:
        return []


def _load_db_events(turn_id: str) -> list[dict[str, Any]]:
    try:
        import_spool_records()
        init_db()
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT id, terminal_id, turn_id, phase, event_type, ts, payload_json, event_key
                FROM turn_events
                WHERE turn_id = ?
                ORDER BY id ASC
                """,
                (turn_id,),
            ).fetchall()
        events = []
        for row in rows:
            try:
                payload = json.loads(str(row["payload_json"] or "{}"))
            except ValueError:
                payload = {}
            events.append(
                {
                    "id": int(row["id"]),
                    "terminal_id": str(row["terminal_id"] or ""),
                    "turn_id": str(row["turn_id"] or ""),
                    "phase": str(row["phase"] or ""),
                    "event_type": str(row["event_type"] or ""),
                    "ts": str(row["ts"] or ""),
                    "payload": payload,
                    "event_key": str(row["event_key"] or ""),
                }
            )
        return events
    except Exception:
        return _scan_spool(turn_id=turn_id)


def materialize_turn(terminal_id: str, turn_id: str) -> dict[str, Any]:
    terminal = (terminal_id or "").strip()
    turn = (turn_id or "").strip()
    snapshot: dict[str, Any] = {
        "terminal_id": terminal,
        "turn_id": turn,
        "session_id": "",
        "user_prompt": "",
        "assistant_response": "",
        "assistant_message_kind": "empty",
        "transcript_path": "",
        "tools_used": [],
        "tool_events": [],
        "governance": {},
        "observations": [],
        "skill_state": None,
        "status": "open",
        "outcome": {},
    }
    if not terminal or not turn:
        return snapshot

    try:
        init_db()
        with _connect() as conn:
            row = conn.execute(
                """
                SELECT session_id, prompt, transcript_path, status, outcome_json
                FROM turns
                WHERE turn_id = ? AND terminal_id = ?
                LIMIT 1
                """,
                (turn, terminal),
            ).fetchone()
        if row:
            snapshot["session_id"] = str(row["session_id"] or "")
            snapshot["user_prompt"] = str(row["prompt"] or "")
            snapshot["transcript_path"] = str(row["transcript_path"] or "")
            snapshot["status"] = str(row["status"] or "open")
            raw_outcome = str(row["outcome_json"] or "{}")
            try:
                snapshot["outcome"] = json.loads(raw_outcome)
            except ValueError:
                snapshot["outcome"] = {}
    except Exception:
        pass

    skill_state: dict[str, Any] | None = None
    assistant_tools: list[str] = []
    tool_events: list[dict[str, Any]] = []

    for record in _load_db_events(turn):
        payload = record.get("payload", {})
        event_type = str(record.get("event_type", ""))
        phase = str(record.get("phase", ""))

        if event_type == "turn_started":
            snapshot["session_id"] = str(payload.get("session_id", snapshot["session_id"]))
            snapshot["user_prompt"] = str(payload.get("prompt", snapshot["user_prompt"]))
            snapshot["transcript_path"] = str(
                payload.get("transcript_path", snapshot["transcript_path"])
            )
        elif event_type == "tool_used":
            tool_event = {
                "name": str(payload.get("name", "")),
                "command": str(payload.get("command", "")),
                "cwd": str(payload.get("cwd", "")),
                "output": str(payload.get("output", "")),
                "success": bool(payload.get("success", True)),
                "timestamp": str(record.get("ts", "")),
                "session_id": str(payload.get("session_id", snapshot["session_id"])),
                "terminal_id": terminal,
            }
            tool_events.append(tool_event)
            if tool_event["name"]:
                assistant_tools.append(tool_event["name"])
                if tool_event["name"] in OBSERVATION_TOOL_NAMES:
                    snapshot["observations"].append(tool_event)
        elif event_type == "skill_loaded":
            skill_state = {
                **payload,
                "tools_used": [],
                "commands_run": [],
                "execution_satisfied": False,
                "first_tool_validated": False,
            }
        elif event_type == "skill_tool_used" and skill_state is not None:
            tool_name = str(payload.get("tool_name", ""))
            if tool_name:
                skill_state["tools_used"].append(tool_name)
            command = str(payload.get("command", ""))
            if command:
                skill_state["commands_run"].append(command)
        elif event_type == "skill_first_tool_validated" and skill_state is not None:
            skill_state["first_tool_validated"] = True
        elif event_type == "skill_phase_transition" and skill_state is not None:
            skill_state["phase"] = payload.get("phase", "")
        elif event_type == "skill_workflow_stage_update" and skill_state is not None:
            ws = skill_state.get("workflow_stage", {})
            for key in ("active_step", "step_definition", "done_criteria", "do_not_distract", "step_index", "total_steps"):
                if key in payload:
                    ws[key] = payload[key]
            skill_state["workflow_stage"] = ws
        elif event_type == "governance_expected":
            snapshot["governance"] = payload
        elif event_type == "response_snapshot":
            snapshot["assistant_response"] = str(
                payload.get("assistant_response", snapshot["assistant_response"])
            )
            snapshot["assistant_message_kind"] = str(
                payload.get("assistant_message_kind", snapshot["assistant_message_kind"])
            )
            snapshot["user_prompt"] = str(payload.get("user_prompt", snapshot["user_prompt"]))
            tools = payload.get("tools_used", [])
            if isinstance(tools, list):
                snapshot["tools_used"] = [str(tool) for tool in tools if str(tool).strip()]
        elif event_type == "turn_closed":
            snapshot["status"] = "closed"
            snapshot["outcome"] = payload.get("outcome", {})
        elif phase == "Stop" and event_type == "validator_result":
            # Observability only; no snapshot mutation needed.
            pass

    snapshot["tool_events"] = tool_events
    if not snapshot["tools_used"]:
        snapshot["tools_used"] = assistant_tools
    if skill_state is not None:
        required_tools = skill_state.get("required_tools", []) or []
        commands_run = skill_state.get("commands_run", []) or []
        pattern = str(skill_state.get("pattern", "") or "")
        execution_tool_used = any(
            tool in required_tools for tool in skill_state.get("tools_used", [])
        )
        pattern_matched = True
        if pattern:
            try:
                import re

                pattern_matched = any(
                    re.search(pattern, command, re.IGNORECASE) for command in commands_run
                )
            except re.error:
                pattern_matched = False
        skill_state["execution_satisfied"] = bool(execution_tool_used and pattern_matched)
    snapshot["skill_state"] = skill_state
    return snapshot


def build_response_snapshot(
    input_data: dict[str, Any],
    default_prompt: str = "",
) -> dict[str, Any]:
    snapshot = {
        "user_prompt": default_prompt or "",
        "assistant_response": "",
        "assistant_message_kind": "empty",
        "tools_used": [],
        "transcript_path": str(input_data.get("transcript_path", "") or ""),
    }

    def _extract_tools(message_content: object) -> list[str]:
        if not isinstance(message_content, list):
            return []
        tools: list[str] = []
        for block in message_content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                name = str(block.get("name", "")).strip()
                if name:
                    tools.append(name)
        return tools

    transcript_path = snapshot["transcript_path"]
    if transcript_path:
        try:
            path = Path(transcript_path)
            if path.exists():
                found_user = False
                found_assistant = False
                for line in reversed(_read_recent_transcript_lines(path)):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    role = entry.get("role", "")
                    msg_type = entry.get("type", "")
                    message = entry.get("message", entry)
                    message_content = message.get("content", entry.get("content", ""))
                    if not found_assistant and (
                        (msg_type == "message" and role == "assistant")
                        or msg_type == "assistant"
                        or role == "assistant"
                    ):
                        assistant_text, message_kind = _classify_assistant_text(message_content)
                        snapshot["assistant_response"] = assistant_text
                        snapshot["assistant_message_kind"] = message_kind
                        snapshot["tools_used"] = _extract_tools(message_content)
                        found_assistant = True
                    if not found_user and (
                        role == "user" or (msg_type == "message" and role == "user")
                    ):
                        snapshot["user_prompt"] = _extract_text_content(message_content).strip()
                        found_user = True
                    if found_user and found_assistant:
                        break
        except Exception:
            pass

    if (
        not snapshot["assistant_response"]
        and snapshot.get("assistant_message_kind") != "system_reminder"
    ):
        response = (
            input_data.get("assistant_response")
            or input_data.get("last_assistant_message")
            or input_data.get("response")
            or ""
        )
        snapshot["assistant_response"] = str(response)
        if snapshot["assistant_response"].strip():
            snapshot["assistant_message_kind"] = "assistant"

    if not snapshot["user_prompt"]:
        prompt = input_data.get("prompt") or input_data.get("message") or default_prompt or ""
        snapshot["user_prompt"] = str(prompt)

    tools_used = input_data.get("tools_used")
    if isinstance(tools_used, list) and tools_used:
        snapshot["tools_used"] = [str(tool) for tool in tools_used if str(tool).strip()]

    return snapshot


def ingest_stop_payload(
    terminal_id: str, turn_id: str, input_data: dict[str, Any]
) -> dict[str, Any]:
    turn_snapshot = materialize_turn(terminal_id, turn_id)
    response_snapshot = build_response_snapshot(
        input_data, default_prompt=str(turn_snapshot.get("user_prompt", ""))
    )
    append_event(
        terminal_id,
        turn_id,
        "Stop",
        "response_snapshot",
        response_snapshot,
    )
    return materialize_turn(terminal_id, turn_id)
