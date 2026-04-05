"""Telemetry query helper for debugging and RCA."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from yt_fts.core.database import get_db_path


def _get_db_path() -> Path:
    """Return the path to the telemetry database."""
    base_path = Path(get_db_path())
    telemetry_path = base_path.parent / "telemetry.db"
    return telemetry_path


def _query_db(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Execute a query and return results as list of dicts."""
    db_path = _get_db_path()
    if not db_path.exists():
        return []
    
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception:
        return []


def query_recent_events(limit: int = 20) -> list[dict[str, Any]]:
    """Get the most recent telemetry events."""
    return _query_db(
        """SELECT event_id, timestamp, session_id, level, component, event_type, data, traceback
           FROM debug_events
           ORDER BY timestamp DESC
           LIMIT ?""",
        (limit,)
    )


def query_by_level(level: str, limit: int = 20) -> list[dict[str, Any]]:
    """Get events filtered by level."""
    return _query_db(
        """SELECT event_id, timestamp, session_id, level, component, event_type, data, traceback
           FROM debug_events
           WHERE level = ?
           ORDER BY timestamp DESC
           LIMIT ?""",
        (level.upper(), limit)
    )


def query_by_component(component: str, limit: int = 20) -> list[dict[str, Any]]:
    """Get events filtered by component."""
    return _query_db(
        """SELECT event_id, timestamp, session_id, level, component, event_type, data, traceback
           FROM debug_events
           WHERE component = ?
           ORDER BY timestamp DESC
           LIMIT ?""",
        (component, limit)
    )


def get_error_summary() -> list[dict[str, Any]]:
    """Get summary of errors grouped by component."""
    return _query_db(
        """SELECT component, COUNT(*) as count
           FROM debug_events
           WHERE level = 'ERROR'
           GROUP BY component
           ORDER BY count DESC"""
    )


def get_recent_errors(limit: int = 10) -> list[dict[str, Any]]:
    """Get recent error events."""
    return query_by_level("ERROR", limit=limit)


def get_telemetry_stats() -> dict[str, Any]:
    """Get overall telemetry statistics."""
    events = _query_db("SELECT level, component, session_id FROM debug_events")
    
    by_level: dict[str, int] = {}
    by_component: dict[str, int] = {}
    session_ids: set[str] = set()
    
    for event in events:
        level = event.get("level", "UNKNOWN")
        component = event.get("component", "UNKNOWN")
        session_id = event.get("session_id", "")
        
        by_level[level] = by_level.get(level, 0) + 1
        by_component[component] = by_component.get(component, 0) + 1
        if session_id:
            session_ids.add(session_id)
    
    return {
        "total_events": len(events),
        "by_level": by_level,
        "by_component": dict(sorted(by_component.items(), key=lambda x: x[1], reverse=True)),
        "session_count": len(session_ids),
    }


def format_events_for_display(events: list[dict[str, Any]], verbose: bool = False) -> str:
    """Format events for console display."""
    if not events:
        return "No events found."
    
    output = []
    for e in events[:20]:
        ts = e.get("timestamp", "")[:19]
        level = e.get("level", "?").ljust(7)
        comp = e.get("component", "?").ljust(20)
        etype = e.get("event_type", "?")
        output.append(f"{ts} | {level} | {comp} | {etype}")
        
        if verbose:
            data = e.get("data")
            if data:
                try:
                    parsed = json.loads(data) if isinstance(data, str) else data
                    output.append(f"    Data: {json.dumps(parsed, indent=6)[:100]}")
                except (json.JSONDecodeError, TypeError, ValueError):
                    output.append(f"    Data: {str(data)[:100]}")
            
            tb = e.get("traceback")
            if tb:
                output.append(f"    Traceback: {tb[:100]}...")
    
    return chr(10).join(output)
