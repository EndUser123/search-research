"""CHS projections — query the normalized events table for search and analytics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.chs.db import get_connection
from core.chs.providers import discover_all

DB_PATH = Path("P:/__csf/data/chat_history.db")


def health_check() -> dict[str, bool]:
    """Ping each registered provider. Returns {provider_id: is_healthy}."""
    result: dict[str, bool] = {}
    for provider in discover_all():
        try:
            # Simple discover call to check provider is reachable
            provider.discover()
            result[provider.provider_id] = True
        except Exception:
            result[provider.provider_id] = False
    return result


def query_events(
    provider_id: str | None = None,
    source_id: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Query normalized events with optional filters."""
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT * FROM events WHERE 1=1"
    params: list[Any] = []
    if provider_id:
        query += " AND provider_id = ?"
        params.append(provider_id)
    if source_id:
        query += " AND source_id = ?"
        params.append(source_id)
    if since:
        query += " AND occurred_at >= ?"
        params.append(since)
    if until:
        query += " AND occurred_at <= ?"
        params.append(until)
    query += " ORDER BY occurred_at ASC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row, strict=True)) for row in cursor.fetchall()]


def query_events_by_session(
    provider_id: str,
    source_id: str,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """Get all events for a session, ordered by occurred_at."""
    return query_events(provider_id=provider_id, source_id=source_id, limit=limit)
