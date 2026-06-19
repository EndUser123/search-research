#!/usr/bin/env python3
"""
Hook Observability Rollup — P:/.claude/hooks/hook_observability_rollup.py

Ingests existing hook telemetry from multiple sources and produces a unified
hook_events_rollup SQLite table plus a human-readable health summary.

=== SOURCE INVENTORY ===

diagnostics.db (SQLite, ~48MB):
  - importer_diagnostics table: id, timestamp, hook_name, phase, session_id,
    terminal_id, tool_name, input_hash, input_bytes, error_text, traceback
  - phase values: load, stderr, execute, timeout (execute is run; stderr is
    captured hook output; load is import failure)
  - good for: load-error rates, stderr counts, timeout events

pretooluse_blocks.jsonl (~557KB):
  - schema=pretooluse_block, version=2
  - fields: event_id, ts, event_kind (child_hook_block | router_final_block),
    tool_name, blocking_hook, source_hook, child_exit_code, session_id,
    terminal_id, prompt_id, cwd, active_turn_id, artifact_path
  - event_kind=routing decision: block
  - good for: block rate per hook, repeated file_path blocks

hook_runner_stderr.jsonl (~525KB):
  - fields: ts, hook, hook_path, session_id, terminal_id, prompt_id, tool_name,
    cwd, command_preview, file_path, event_kind, stderr_len, stderr, exit_code
  - event_kind values: (not shown — infer from exit_code and stderr content)
  - good for: stderr errors per hook, error decision

ups_execution_trace.jsonl (~590KB):
  - UserPromptSubmit hook execution trace
  - fields: ts, session_id, terminal_id, hook_name, result (dict), duration_ms,
    transcript_path
  - result.is_empty + tokens_added
  - good for: UPS hook latency percentiles

epistemic_telemetry.jsonl (~404KB):
  - epistemic gate decisions per turn
  - fields: timestamp (epoch), gate, decision (allow|warn|block), issue_count,
    issue_types (list), has_format_issues, has_unsupported_fact,
    has_causal_issues, has_comparative_issues, mode, responseMode, session_id
  - good for: epistemic block rate, issue type breakdown

behavior_audit_telemetry.jsonl (~340KB):
  - fields: timestamp (epoch), session_id, terminal_id, decision (allow|block),
    reason, missing_claims
  - good for: behavior audit block rate

stop_router_timing.log (~6KB, plain text):
  - Format: "2026-05-01 08:28:26,092 INFO hook=unified_claim_verifier.py
    dispatch=inprocess elapsed_ms=0.0 timeout_s=5.0"
  - Also: "route_stop total_elapsed_ms=0.2 terminal_id=term-1 turn_id=turn-1 warnings=0"
  - good for: Stop hook latency percentiles

skill_first_enforcement.jsonl (~424KB):
  - PreToolUse and Stop skill-first enforcement events
  - fields: timestamp (epoch), hook, event, reason_code, session_id, tool_name,
    skill_name, mode (hard_block|monitor)
  - good for: skill-first block rate per hook

deletion_verification_guard.log (~103KB, plain text):
  - Mixed format: some JSON lines ({"error":..., "event":..., "level":...})
    plus plain text INFO/DEBUG lines
  - Hardest to parse reliably — TODO for structured ingestion

cross_validator.log (~3KB, JSON per line):
  - {"error": "DB error", "event": "evidence_load_failed", "level": "warning",
    "timestamp": "..."}
  - good for: cross-validator error rates

unverified_stance.log (~8KB, JSON per line):
  - Same structure as cross_validator.log
  - good for: unverified-stance error rates

auth_blocks.jsonl: MISSING (path does not exist)

=== UNIFIED EVENT SCHEMA ===

Each row in hook_events_rollup has:
  timestamp       TEXT    — ISO 8601
  session_id      TEXT    — may be NULL
  terminal_id     TEXT    — may be NULL
  hook_name       TEXT    — e.g. "pretooluse_blocks", "epistemic_contract"
  hook_phase      TEXT    — UserPromptSubmit | PreToolUse | PostToolUse | Stop |
                            Importer | Other
  decision        TEXT    — allow | warn | block | error | unknown
  reason_category TEXT    — tdd | epistemic | sequential_thinking | deletion |
                            skill_first | claim_verification | timeout | stderr |
                            import_error | other | unknown
  latency_ms      REAL    — may be NULL
  tool_name       TEXT    — may be NULL
  file_path       TEXT    — may be NULL
  detail          TEXT    — raw snippet or JSON summary of original event
  source          TEXT    — which file this row came from

Run:
  python hook_observability_rollup.py ingest   # build rollup DB
  python hook_observability_rollup.py summary  # write health summary

Current coverage:
  INGESTED: diagnostics.db (importer_diagnostics), pretooluse_blocks.jsonl,
            hook_runner_stderr.jsonl, ups_execution_trace.jsonl,
            epistemic_telemetry.jsonl, behavior_audit_telemetry.jsonl,
            stop_router_timing.log, skill_first_enforcement.jsonl,
            cross_validator.log, unverified_stance.log
  TODO:     deletion_verification_guard.log (mixed text+JSON format too irregular
            to parse safely without per-event parsing rules)
"""

import sqlite3
import json
import re
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

HOOKS_DIR = Path(__file__).resolve().parent
LOGS_DIR = HOOKS_DIR / "logs"
STATE_LOGS = HOOKS_DIR / "state" / "logs"
ROLLUP_DB = LOGS_DIR / "hook_observability.db"
SUMMARY_MD = LOGS_DIR / "hook-health-summary.md"

SOURCES = {
    "diagnostics_db": LOGS_DIR / "diagnostics" / "diagnostics.db",
    "pretooluse_blocks": LOGS_DIR / "diagnostics" / "pretooluse_blocks.jsonl",
    "hook_runner_stderr": LOGS_DIR / "diagnostics" / "hook_runner_stderr.jsonl",
    "ups_execution_trace": LOGS_DIR / "diagnostics" / "ups_execution_trace.jsonl",
    "epistemic_telemetry": LOGS_DIR / "diagnostics" / "epistemic_telemetry.jsonl",
    "behavior_audit_telemetry": LOGS_DIR / "diagnostics" / "behavior_audit_telemetry.jsonl",
    "stop_router_timing": STATE_LOGS / "stop_router_timing.log",
    "skill_first_enforcement": LOGS_DIR / "skill_first_enforcement.jsonl",
    "cross_validator": STATE_LOGS / "cross_validator.log",
    "unverified_stance": STATE_LOGS / "unverified_stance.log",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ts_to_iso(ts_val, is_epoch=False) -> str:
    """Convert epoch float or ISO string to ISO string."""
    if is_epoch:
        try:
            return datetime.fromtimestamp(float(ts_val), tz=timezone.utc).isoformat()
        except (ValueError, OSError):
            return str(ts_val)
    s = str(ts_val)
    if "T" in s or "+" in s or "-" in s[:4]:
        return s.replace(" ", "T") if "T" not in s else s
    return s


def ensure_db(conn: sqlite3.Connection) -> None:
    """Create hook_events_rollup table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hook_events_rollup (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT,
            session_id      TEXT,
            terminal_id     TEXT,
            hook_name       TEXT,
            hook_phase      TEXT,
            decision        TEXT,
            reason_category TEXT,
            latency_ms      REAL,
            tool_name       TEXT,
            file_path       TEXT,
            detail          TEXT,
            source          TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_her_timestamp ON hook_events_rollup(timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_her_hook_name ON hook_events_rollup(hook_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_her_session ON hook_events_rollup(session_id)")
    conn.commit()


def insert_row(conn: sqlite3.Connection, row: dict) -> None:
    keys = [
        "timestamp", "session_id", "terminal_id", "hook_name", "hook_phase",
        "decision", "reason_category", "latency_ms", "tool_name", "file_path",
        "detail", "source",
    ]
    placeholders = ",".join(["?"] * len(keys))
    conn.execute(
        f"INSERT INTO hook_events_rollup ({','.join(keys)}) VALUES ({placeholders})",
        [row.get(k) for k in keys],
    )


def reason_from_error_text(err_text: str) -> str:
    """Classify reason_category from error text snippets."""
    if not err_text:
        return "unknown"
    t = err_text.lower()
    if "tdd" in t or "test" in t:
        return "tdd"
    if "epistemic" in t or "unverified" in t or "claim" in t:
        return "epistemic"
    if "sequential" in t or "thinking" in t:
        return "sequential_thinking"
    if "deletion" in t or "delete" in t:
        return "deletion"
    if "skill" in t and ("first" in t or "pending" in t):
        return "skill_first"
    if "timeout" in t:
        return "timeout"
    if "stderr" in t or len(err_text) < 200:
        return "stderr"
    if "import" in t or "no module named" in t:
        return "import_error"
    return "other"


def decision_from_event_kind(event_kind: str, hook: str = "") -> str:
    """Map event_kind string to decision."""
    if not event_kind:
        return "unknown"
    ek = event_kind.lower()
    if "block" in ek or "deny" in ek or "reject" in ek:
        return "block"
    if "warn" in ek:
        return "warn"
    if "allow" in ek or "pass" in ek or "ok" in ek:
        return "allow"
    if "error" in ek or "fail" in ek:
        return "error"
    return "unknown"


# ---------------------------------------------------------------------------
# Ingest: diagnostics.db → importer_diagnostics
# ---------------------------------------------------------------------------

def ingest_diagnostics_db(conn: sqlite3.Connection) -> int:
    """Ingest importer_diagnostics rows into rollup."""
    db_path = SOURCES["diagnostics_db"]
    if not db_path.exists():
        return 0
    count = 0
    diag_conn = sqlite3.connect(str(db_path))
    diag_conn.execute("PRAGMA journal_mode=WAL")
    diag_conn.execute("PRAGMA busy_timeout=5000")
    try:
        cur = diag_conn.execute(
            "SELECT id, timestamp, hook_name, phase, session_id, "
            "terminal_id, tool_name, input_hash, input_bytes, "
            "error_text, traceback FROM importer_diagnostics"
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    finally:
        diag_conn.close()
    for row in rows:
        d = dict(zip(cols, row))
        ts = ts_to_iso(d["timestamp"])
        phase = d["phase"] or "Unknown"
        hook = d["hook_name"] or "unknown"

        # Classify decision from phase
        if phase == "load":
            decision = "error" if d["error_text"] else "allow"
        elif phase == "stderr":
            decision = "error"
        elif phase == "timeout":
            decision = "error"
        else:
            decision = "allow"

        reason_cat = reason_from_error_text(d.get("error_text", ""))

        insert_row(conn, {
            "timestamp": ts,
            "session_id": d.get("session_id"),
            "terminal_id": d.get("terminal_id"),
            "hook_name": hook,
            "hook_phase": "Importer",
            "decision": decision,
            "reason_category": reason_cat,
            "latency_ms": None,
            "tool_name": d.get("tool_name"),
            "file_path": None,
            "detail": (d.get("error_text") or "")[:500],
            "source": "diagnostics_db.importer_diagnostics",
        })
        count += 1
    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Ingest: pretooluse_blocks.jsonl
# ---------------------------------------------------------------------------

def ingest_pretooluse_blocks(conn: sqlite3.Connection) -> int:
    """Ingest pretooluse_blocks.jsonl block events."""
    path = SOURCES["pretooluse_blocks"]
    if not path.exists():
        return 0
    count = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = ts_to_iso(obj.get("ts", ""))
            event_kind = obj.get("event_kind", "")
            blocking_hook = obj.get("blocking_hook", obj.get("source_hook", "unknown"))
            tool_name = obj.get("tool_name")

            decision = "block" if "block" in event_kind.lower() else "unknown"

            # reason_category: use field from entry if present, else derive from hook name
            raw_rc = obj.get("reason_category")
            hook_lower = blocking_hook.lower()
            reason_cat = raw_rc if raw_rc and raw_rc != "other" else (
                "tdd" if "tdd" in hook_lower else
                "epistemic" if "epistemic" in hook_lower or "claim" in hook_lower else
                "skill_first" if "skill" in hook_lower and "pattern" in hook_lower else
                "deletion" if "deletion" in hook_lower or "delete" in hook_lower else
                "sequential_thinking" if "sequential" in hook_lower or "thinking" in hook_lower else
                "other"
            )

            insert_row(conn, {
                "timestamp": ts,
                "session_id": obj.get("session_id"),
                "terminal_id": obj.get("terminal_id"),
                "hook_name": blocking_hook,
                "hook_phase": "PreToolUse",
                "decision": decision,
                "reason_category": reason_cat,
                "latency_ms": obj.get("latency_ms"),
                "tool_name": tool_name,
                "file_path": None,
                "detail": json.dumps({"event_kind": event_kind, "exit_code": obj.get("child_exit_code")})[:300],
                "source": "pretooluse_blocks.jsonl",
            })
            count += 1
    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Ingest: hook_runner_stderr.jsonl
# ---------------------------------------------------------------------------

def ingest_hook_runner_stderr(conn: sqlite3.Connection) -> int:
    """Ingest hook_runner_stderr.jsonl events."""
    path = SOURCES["hook_runner_stderr"]
    if not path.exists():
        return 0
    count = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = ts_to_iso(obj.get("ts", ""))
            hook = obj.get("hook", "unknown")
            event_kind = obj.get("event_kind", "")
            stderr = obj.get("stderr", "")
            exit_code = obj.get("exit_code")

            decision = "error" if (event_kind == "stderr" or stderr) else "allow"

            insert_row(conn, {
                "timestamp": ts,
                "session_id": obj.get("session_id"),
                "terminal_id": obj.get("terminal_id"),
                "hook_name": hook,
                "hook_phase": infer_phase_from_hook_name(hook),
                "decision": decision,
                "reason_category": "stderr" if stderr else "other",
                "latency_ms": None,
                "tool_name": obj.get("tool_name"),
                "file_path": obj.get("file_path"),
                "detail": (stderr or event_kind or "")[:300],
                "source": "hook_runner_stderr.jsonl",
            })
            count += 1
    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Ingest: ups_execution_trace.jsonl
# ---------------------------------------------------------------------------

def ingest_ups_execution_trace(conn: sqlite3.Connection) -> int:
    """Ingest ups_execution_trace.jsonl — UserPromptSubmit hook timing."""
    path = SOURCES["ups_execution_trace"]
    if not path.exists():
        return 0
    count = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = ts_to_iso(obj.get("ts", ""))
            hook = obj.get("hook_name", "unknown")
            duration_ms = obj.get("duration_ms")

            insert_row(conn, {
                "timestamp": ts,
                "session_id": obj.get("session_id"),
                "terminal_id": obj.get("terminal_id"),
                "hook_name": hook,
                "hook_phase": "UserPromptSubmit",
                "decision": "allow",
                "reason_category": "other",
                "latency_ms": float(duration_ms) if duration_ms is not None else None,
                "tool_name": None,
                "file_path": None,
                "detail": json.dumps(obj.get("result", {}))[:200],
                "source": "ups_execution_trace.jsonl",
            })
            count += 1
    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Ingest: epistemic_telemetry.jsonl
# ---------------------------------------------------------------------------

def ingest_epistemic_telemetry(conn: sqlite3.Connection) -> int:
    """Ingest epistemic_telemetry.jsonl."""
    path = SOURCES["epistemic_telemetry"]
    if not path.exists():
        return 0
    count = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = ts_to_iso(obj.get("timestamp", ""), is_epoch=True)
            gate = obj.get("gate", "unknown")
            decision = obj.get("decision", "unknown")
            issue_types = obj.get("issue_types", [])

            reason_cat = "epistemic"
            if issue_types:
                reason_cat = f"epistemic:{issue_types[0]}"

            insert_row(conn, {
                "timestamp": ts,
                "session_id": obj.get("session_id"),
                "terminal_id": None,
                "hook_name": f"epistemic:{gate}",
                "hook_phase": "Stop",
                "decision": decision,
                "reason_category": reason_cat,
                "latency_ms": None,
                "tool_name": None,
                "file_path": None,
                "detail": f"issue_count={obj.get('issue_count')} types={issue_types}",
                "source": "epistemic_telemetry.jsonl",
            })
            count += 1
    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Ingest: behavior_audit_telemetry.jsonl
# ---------------------------------------------------------------------------

def ingest_behavior_audit_telemetry(conn: sqlite3.Connection) -> int:
    """Ingest behavior_audit_telemetry.jsonl."""
    path = SOURCES["behavior_audit_telemetry"]
    if not path.exists():
        return 0
    count = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = ts_to_iso(obj.get("timestamp", ""), is_epoch=True)
            decision = obj.get("decision", "unknown")
            reason = obj.get("reason", "")

            insert_row(conn, {
                "timestamp": ts,
                "session_id": obj.get("session_id"),
                "terminal_id": obj.get("terminal_id"),
                "hook_name": "behavior_audit",
                "hook_phase": "Stop",
                "decision": decision,
                "reason_category": "other",
                "latency_ms": None,
                "tool_name": None,
                "file_path": None,
                "detail": (reason or "")[:300],
                "source": "behavior_audit_telemetry.jsonl",
            })
            count += 1
    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Ingest: stop_router_timing.log
# ---------------------------------------------------------------------------

STOP_TIMING_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) "
    r"(?P<level>\w+)\s+"
    r"(?:hook=(?P<hook>[\w./]+(?:\.py)?)\s+)?"
    r"(?:dispatch=(\w+)\s+)?"
    r"(?:elapsed_ms=(?P<elapsed_ms>[\d.]+)\s+)?"
    r"(?:timeout_s=[\d.]+\s+)?"
    r"(?:total_elapsed_ms=(?P<total_ms>[\d.]+)\s+)?"
    r"(?:terminal_id=(\S+)\s+)?"
    r"(?:turn_id=(\S+)\s+)?"
    r"(?:warnings=(\d+))?",
    re.IGNORECASE,
)

def ingest_stop_router_timing(conn: sqlite3.Connection) -> int:
    """Ingest stop_router_timing.log — per-hook timing lines."""
    path = SOURCES["stop_router_timing"]
    if not path.exists():
        return 0
    count = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            m = STOP_TIMING_RE.search(line)
            if not m:
                continue
            gd = m.groupdict()

            ts_str = gd.get("date", "")
            try:
                dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")
                ts = dt.strftime("%Y-%m-%dT%H:%M:%S") + dt.strftime(".%f")[:4] + "Z"
            except ValueError:
                ts = ts_str

            hook = gd.get("hook") or "unknown"
            elapsed = gd.get("elapsed_ms") or gd.get("total_ms")

            insert_row(conn, {
                "timestamp": ts,
                "session_id": None,
                "terminal_id": gd.get("terminal_id"),
                "hook_name": hook,
                "hook_phase": "Stop",
                "decision": "allow",
                "reason_category": "other",
                "latency_ms": float(elapsed) if elapsed else None,
                "tool_name": None,
                "file_path": None,
                "detail": f"dispatch={gd.get('dispatch')} warnings={gd.get('warnings')}",
                "source": "stop_router_timing.log",
            })
            count += 1
    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Ingest: skill_first_enforcement.jsonl
# ---------------------------------------------------------------------------

def ingest_skill_first_enforcement(conn: sqlite3.Connection) -> int:
    """Ingest skill_first_enforcement.jsonl."""
    path = SOURCES["skill_first_enforcement"]
    if not path.exists():
        return 0
    count = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = ts_to_iso(obj.get("timestamp", ""), is_epoch=True)
            hook_phase = obj.get("hook", "PreToolUse")
            event = obj.get("event", "")
            mode = obj.get("mode", "")

            decision = "block" if "tool_before_skill" in event else "allow"
            if mode == "monitor":
                decision = "warn"

            insert_row(conn, {
                "timestamp": ts,
                "session_id": obj.get("session_id"),
                "terminal_id": None,
                "hook_name": "skill_first_enforcement",
                "hook_phase": hook_phase,
                "decision": decision,
                "reason_category": "skill_first",
                "latency_ms": None,
                "tool_name": obj.get("tool_name"),
                "file_path": None,
                "detail": f"event={event} reason_code={obj.get('reason_code')} skill={obj.get('skill_name')}",
                "source": "skill_first_enforcement.jsonl",
            })
            count += 1
    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Ingest: cross_validator.log (JSON per line)
# ---------------------------------------------------------------------------

def ingest_cross_validator(conn: sqlite3.Connection) -> int:
    """Ingest cross_validator.log — JSON per line."""
    path = SOURCES["cross_validator"]
    if not path.exists():
        return 0
    count = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = ts_to_iso(obj.get("timestamp", ""))
            level = obj.get("level", "")

            decision = "error" if level in ("error", "warning") else "allow"

            insert_row(conn, {
                "timestamp": ts,
                "session_id": None,
                "terminal_id": None,
                "hook_name": "cross_validator",
                "hook_phase": "Stop",
                "decision": decision,
                "reason_category": "other",
                "latency_ms": None,
                "tool_name": None,
                "file_path": None,
                "detail": (obj.get("error", "") or obj.get("event", ""))[:200],
                "source": "cross_validator.log",
            })
            count += 1
    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Ingest: unverified_stance.log (JSON per line)
# ---------------------------------------------------------------------------

def ingest_unverified_stance(conn: sqlite3.Connection) -> int:
    """Ingest unverified_stance.log — JSON per line."""
    path = SOURCES["unverified_stance"]
    if not path.exists():
        return 0
    count = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = ts_to_iso(obj.get("timestamp", ""))
            level = obj.get("level", "")

            decision = "error" if level in ("error", "warning") else "allow"

            insert_row(conn, {
                "timestamp": ts,
                "session_id": None,
                "terminal_id": None,
                "hook_name": "unverified_stance",
                "hook_phase": "Stop",
                "decision": decision,
                "reason_category": "epistemic",
                "latency_ms": None,
                "tool_name": None,
                "file_path": None,
                "detail": (obj.get("error", "") or obj.get("event", ""))[:200],
                "source": "unverified_stance.log",
            })
            count += 1
    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Phase inference helper
# ---------------------------------------------------------------------------

_HOOK_PHASE_MAP = {
    "PreToolUse": "PreToolUse",
    "PostToolUse": "PostToolUse",
    "UserPromptSubmit": "UserPromptSubmit",
    "Stop": "Stop",
    "SessionStart": "SessionStart",
}

def infer_phase_from_hook_name(hook: str) -> str:
    for prefix, phase in _HOOK_PHASE_MAP.items():
        if prefix in hook:
            return phase
    return "Other"


# ---------------------------------------------------------------------------
# Ingest dispatcher
# ---------------------------------------------------------------------------

def ingest(conn: sqlite3.Connection) -> dict:
    """Run all ingestors and return a dict of source -> row_count."""
    counts = {}
    ensure_db(conn)

    ingestors = [
        ("diagnostics_db.importer_diagnostics", ingest_diagnostics_db),
        ("pretooluse_blocks.jsonl", ingest_pretooluse_blocks),
        ("hook_runner_stderr.jsonl", ingest_hook_runner_stderr),
        ("ups_execution_trace.jsonl", ingest_ups_execution_trace),
        ("epistemic_telemetry.jsonl", ingest_epistemic_telemetry),
        ("behavior_audit_telemetry.jsonl", ingest_behavior_audit_telemetry),
        ("stop_router_timing.log", ingest_stop_router_timing),
        ("skill_first_enforcement.jsonl", ingest_skill_first_enforcement),
        ("cross_validator.log", ingest_cross_validator),
        ("unverified_stance.log", ingest_unverified_stance),
    ]

    for name, fn in ingestors:
        try:
            n = fn(conn)
            counts[name] = n
        except Exception as e:
            counts[name] = f"ERROR: {e}"

    return counts


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------

MIN_EVENTS_THRESHOLD = 5  # minimum events for a hook to appear in block-rate table

def compute_metrics(conn: sqlite3.Connection) -> dict:
    """Compute inefficiency metrics from hook_events_rollup."""
    metrics = {}

    # --- Per-hook block rate ---
    cur = conn.execute("""
        SELECT hook_name,
               COUNT(*) AS total,
               SUM(CASE WHEN decision = 'block' THEN 1 ELSE 0 END) AS blocks,
               SUM(CASE WHEN decision = 'error' THEN 1 ELSE 0 END) AS errors
        FROM hook_events_rollup
        GROUP BY hook_name
        HAVING COUNT(*) >= ?
        ORDER BY blocks DESC
    """, (MIN_EVENTS_THRESHOLD,))
    metrics["block_rates"] = [
        {"hook": r[0], "total": r[1], "blocks": r[2], "errors": r[3],
         "block_rate": round(r[2]/r[1]*100, 1) if r[1] else 0}
        for r in cur.fetchall()
    ]

    # --- Per-hook latency percentiles (p50, p95, p99) ---
    cur = conn.execute("""
        SELECT hook_name,
               COUNT(*) AS n,
               AVG(latency_ms) AS avg_ms,
               MIN(latency_ms) AS min_ms,
               MAX(latency_ms) AS max_ms
        FROM hook_events_rollup
        WHERE latency_ms IS NOT NULL
        GROUP BY hook_name
        HAVING COUNT(*) >= ?
        ORDER BY avg_ms DESC
    """, (MIN_EVENTS_THRESHOLD,))
    latency_metrics = []
    for (hook, n, avg_ms, min_ms, max_ms) in cur.fetchall():
        # Compute p50, p95, p99 inline
        rows = conn.execute("""
            SELECT latency_ms FROM hook_events_rollup
            WHERE hook_name = ? AND latency_ms IS NOT NULL
            ORDER BY latency_ms
        """, (hook,)).fetchall()
        lats = [r[0] for r in rows]
        if not lats:
            continue
        p50 = lats[int(len(lats) * 0.50)] if len(lats) > 1 else lats[0]
        p95 = lats[int(len(lats) * 0.95)] if len(lats) > 1 else lats[0]
        p99 = lats[int(len(lats) * 0.99)] if len(lats) > 1 else lats[0]
        latency_metrics.append({
            "hook": hook, "n": n, "avg_ms": round(avg_ms, 2),
            "p50": round(p50, 2), "p95": round(p95, 2), "p99": round(p99, 2),
            "min_ms": round(min_ms, 2), "max_ms": round(max_ms, 2),
        })
    metrics["latency"] = sorted(latency_metrics, key=lambda x: x["p95"], reverse=True)[:10]

    # --- Repeat block patterns (same hook + same tool/file 3+ times per session) ---
    cur = conn.execute("""
        SELECT session_id, hook_name, tool_name, file_path, COUNT(*) AS cnt
        FROM hook_events_rollup
        WHERE decision = 'block'
          AND session_id IS NOT NULL
          AND (tool_name IS NOT NULL OR file_path IS NOT NULL)
        GROUP BY session_id, hook_name,
                 COALESCE(tool_name, '__none__'),
                 COALESCE(file_path, '__none__')
        HAVING COUNT(*) >= 3
        ORDER BY cnt DESC
        LIMIT 30
    """)
    metrics["repeat_blocks"] = [
        {"hook": r[1], "session": r[0], "tool": r[2], "file": r[3], "count": r[4]}
        for r in cur.fetchall()
    ]

    # --- Error/stderr rates per hook ---
    cur = conn.execute("""
        SELECT hook_name,
               SUM(CASE WHEN decision = 'error' THEN 1 ELSE 0 END) AS err_cnt,
               SUM(CASE WHEN reason_category = 'stderr' THEN 1 ELSE 0 END) AS stderr_cnt
        FROM hook_events_rollup
        GROUP BY hook_name
        HAVING SUM(CASE WHEN decision = 'error' THEN 1 ELSE 0 END) +
               SUM(CASE WHEN reason_category = 'stderr' THEN 1 ELSE 0 END) > 0
        ORDER BY err_cnt DESC, stderr_cnt DESC
    """)
    metrics["error_rates"] = [
        {"hook": r[0], "errors": r[1], "stderr_events": r[2]}
        for r in cur.fetchall()
    ]

    # --- Overall totals ---
    cur = conn.execute("""
        SELECT
            COUNT(*) AS total_events,
            COUNT(DISTINCT hook_name) AS unique_hooks,
            SUM(CASE WHEN decision = 'block' THEN 1 ELSE 0 END) AS total_blocks,
            SUM(CASE WHEN decision = 'error' THEN 1 ELSE 0 END) AS total_errors,
            MIN(timestamp) AS earliest,
            MAX(timestamp) AS latest
        FROM hook_events_rollup
    """)
    row = cur.fetchone()
    metrics["totals"] = {
        "total_events": row[0],
        "unique_hooks": row[1],
        "total_blocks": row[2],
        "total_errors": row[3],
        "earliest": row[4],
        "latest": row[5],
    }

    return metrics


# ---------------------------------------------------------------------------
# Render summary markdown
# ---------------------------------------------------------------------------

def render_summary(metrics: dict, counts: dict) -> str:
    """Render human-readable markdown summary."""
    lines = []
    lines.append("# Hook Health Summary")
    lines.append(f"\n*Generated: {iso_now()}*\n")

    totals = metrics.get("totals", {})
    lines.append("## Overview")
    lines.append(f"- Total events ingested: {totals.get('total_events', '?')}")
    lines.append(f"- Unique hooks seen: {totals.get('unique_hooks', '?')}")
    lines.append(f"- Total blocks: {totals.get('total_blocks', '?')}")
    lines.append(f"- Total errors: {totals.get('total_errors', '?')}")
    lines.append(f"- Data window: {totals.get('earliest', '?')[:10]} → {totals.get('latest', '?')[:10]}")

    lines.append("\n## Ingestion Coverage")
    for src, n in counts.items():
        label = n if isinstance(n, int) else n
        lines.append(f"- {src}: {label:,} rows" if isinstance(n, int) else f"- {src}: {n}")

    # Top blocking hooks
    block_rates = metrics.get("block_rates", [])
    if block_rates:
        lines.append("\n## Top Blocking Hooks")
        lines.append("| Hook | Total Events | Blocks | Block Rate |")
        lines.append("|------|-------------|-------|------------|")
        for item in block_rates[:20]:
            lines.append(
                f"| `{item['hook']}` | {item['total']} | {item['blocks']} | "
                f"{item['block_rate']}% |"
            )
    else:
        lines.append("\n## Top Blocking Hooks — (no data)")

    # Slowest hooks
    latency = metrics.get("latency", [])
    if latency:
        lines.append("\n## Slowest Hooks (by p95 latency, ms)")
        lines.append("| Hook | Count | p50 | p95 | p99 | max |")
        lines.append("|------|-------|-----|-----|-----|-----|")
        for item in latency:
            lines.append(
                f"| `{item['hook']}` | {item['n']} | "
                f"{item['p50']} | **{item['p95']}** | {item['p99']} | {item['max_ms']} |"
            )
    else:
        lines.append("\n## Slowest Hooks — (no latency data)")

    # Repeat block hotspots
    repeat_blocks = metrics.get("repeat_blocks", [])
    if repeat_blocks:
        lines.append("\n## Repeat Block Hotspots (≥3 blocks same hook+tool/session)")
        for item in repeat_blocks[:15]:
            target = item["tool"] or item["file"] or "(unknown)"
            lines.append(
                f"- `{item['hook']}` blocked *{target}* **{item['count']}x** "
                f"in session `{str(item['session'])[:20]}...`"
            )
    else:
        lines.append("\n## Repeat Block Hotspots — (none detected)")

    # Errors and stderr
    error_rates = metrics.get("error_rates", [])
    if error_rates:
        lines.append("\n## Errors and Stderr")
        lines.append("| Hook | Errors | Stderr Events |")
        lines.append("|------|--------|---------------|")
        for item in error_rates[:20]:
            lines.append(
                f"| `{item['hook']}` | {item['errors']} | {item['stderr_events']} |"
            )
    else:
        lines.append("\n## Errors and Stderr — (none detected)")

    lines.append(f"\n*Report generated: {iso_now()}*")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Hook observability rollup")
    sub = parser.add_subparsers(dest="command", required=True)

    ing = sub.add_parser("ingest", help="Ingest telemetry sources into rollup DB")
    ing.add_argument("--reset", action="store_true",
                      help="Truncate hook_events_rollup before ingesting")

    smry = sub.add_parser("summary", help="Generate hook-health-summary.md from rollup DB")

    args = parser.parse_args()

    if args.command == "ingest":
        # Open or create rollup DB
        conn = sqlite3.connect(str(ROLLUP_DB))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        try:
            if args.reset:
                conn.execute("DELETE FROM hook_events_rollup")
                conn.commit()
                print("Truncated hook_events_rollup.")
            counts = ingest(conn)
            total = sum(v for v in counts.values() if isinstance(v, int))
            print(f"\nIngest complete — {total:,} total rows written:")
            for src, n in counts.items():
                print(f"  {src}: {n}")
        finally:
            conn.close()

    elif args.command == "summary":
        if not ROLLUP_DB.exists():
            print(f"Rollup DB not found at {ROLLUP_DB}")
            print("Run: python hook_observability_rollup.py ingest")
            sys.exit(1)

        conn = sqlite3.connect(str(ROLLUP_DB))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        try:
            cur = conn.execute("SELECT COUNT(*) FROM hook_events_rollup")
            total = cur.fetchone()[0]
            if total == 0:
                print("Rollup DB is empty. Run 'ingest' first.")
                sys.exit(1)

            metrics = compute_metrics(conn)

            # Also rebuild counts from what's actually in DB
            cur = conn.execute("""
                SELECT source, COUNT(*) FROM hook_events_rollup
                GROUP BY source
                ORDER BY COUNT(*) DESC
            """)
            counts = {r[0]: r[1] for r in cur.fetchall()}

            md = render_summary(metrics, counts)
            SUMMARY_MD.write_text(md, encoding="utf-8")
            print(f"Summary written to {SUMMARY_MD}")

            # Also print to stdout
            print("\n" + md)
        finally:
            conn.close()


if __name__ == "__main__":
    main()