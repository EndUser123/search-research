"""Normalized event operations — upsert and query for the multi-provider history layer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.chs.db import get_connection

DB_PATH = Path("P:/__csf/data/chat_history.db")


def upsert_event(event: dict[str, Any]) -> bool:
    """Insert or ignore a normalized event. Returns True if inserted, False if duplicate.

    event dict must have: provider_id, source_id, event_id, content_hash,
    occurred_at, raw_payload_path, plus optional conversation_id, session_id,
    terminal_id, turn_id, metadata_json.
    """
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO events (
            provider_id, source_id, event_id, content_hash,
            conversation_id, session_id, terminal_id, turn_id,
            occurred_at, raw_payload_path, cached_at, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event.get("provider_id"),
        event.get("source_id"),
        event.get("event_id"),
        event.get("content_hash"),
        event.get("conversation_id"),
        event.get("session_id"),
        event.get("terminal_id"),
        event.get("turn_id"),
        event.get("occurred_at"),
        event.get("raw_payload_path"),
        datetime.now(timezone.utc).isoformat(),
        json.dumps(event.get("metadata", {})) if event.get("metadata") else "{}",
    ))
    conn.commit()
    return cursor.rowcount > 0


def query_tasks(provider_id: str | None = None, since: str | None = None, until: str | None = None) -> list[dict]:
    """Query tasks with optional filters."""
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if provider_id:
        query += " AND provider_id = ?"
        params.append(provider_id)
    if since:
        query += " AND opened_at >= ?"
        params.append(since)
    if until:
        query += " AND opened_at <= ?"
        params.append(until)
    cursor.execute(query, params)
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row, strict=True)) for row in cursor.fetchall()]


def query_opportunities(provider_id: str | None = None, since: str | None = None, until: str | None = None) -> list[dict]:
    """Query opportunity events (opportunity_detected)."""
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT * FROM event_log WHERE event_type = 'opportunity_detected'"
    params = []
    if provider_id:
        query += " AND task_id LIKE ?"
        params.append(f"{provider_id}%")
    if since:
        query += " AND occurred_at >= ?"
        params.append(since)
    if until:
        query += " AND occurred_at <= ?"
        params.append(until)
    cursor.execute(query, params)
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row, strict=True)) for row in cursor.fetchall()]


def get_events_by_hash(provider_id: str, source_id: str, content_hash: str) -> list[dict]:
    """Get all versions of an event by content_hash."""
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM events WHERE provider_id = ? AND source_id = ? AND content_hash = ?",
        (provider_id, source_id, content_hash),
    )
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row, strict=True)) for row in cursor.fetchall()]
