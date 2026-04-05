"""Structured telemetry layer for yt-fts debugging."""
import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from yt_fts.core.database import get_db_path


def _get_db_path() -> Path:
    """Return the path to the telemetry database."""
    base_path = Path(get_db_path())
    telemetry_path = base_path.parent / "telemetry.db"
    return telemetry_path


# Telemetry configuration
_telemetry_enabled: bool = False
_telemetry_level: str = "debug"
_telemetry_lock = threading.Lock()

VALID_LEVELS = ["basic", "verbose", "debug"]


def get_telemetry_enabled() -> bool:
    """Check if telemetry is currently enabled."""
    global _telemetry_enabled
    with _telemetry_lock:
        return _telemetry_enabled


def set_telemetry_enabled(enabled: bool) -> None:
    """Enable or disable telemetry collection."""
    global _telemetry_enabled
    with _telemetry_lock:
        _telemetry_enabled = enabled


def get_telemetry_level() -> str:
    """Get the current telemetry verbosity level."""
    global _telemetry_level
    with _telemetry_lock:
        return _telemetry_level


def set_telemetry_level(level: str) -> None:
    """Set the telemetry verbosity level."""
    global _telemetry_level
    if level not in VALID_LEVELS:
        raise ValueError(f"Invalid telemetry level: {level!r}. Must be one of {VALID_LEVELS}")
    with _telemetry_lock:
        _telemetry_level = level


def _should_persist_event(level: str) -> bool:
    """Check if an event should be persisted based on telemetry level."""
    if not get_telemetry_enabled():
        return False
    
    telemetry_level = get_telemetry_level()
    if telemetry_level == "basic":
        return level in ("ERROR", "WARNING")
    elif telemetry_level == "verbose":
        return level in ("ERROR", "WARNING", "INFO")
    elif telemetry_level == "debug":
        return True
    return False


def rotate_telemetry_data(max_days: int = 7, max_size_mb: float = 100.0) -> None:
    """Rotate telemetry data by deleting old or oversized data."""
    db_path = _get_db_path()
    if not db_path.exists():
        return
    
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        conn.execute("PRAGMA busy_timeout = 5000")
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='debug_events'")
        if cursor.fetchone() is None:
            conn.close()
            return
        
        # Delete old events
        cutoff_time = (datetime.now(timezone.utc) - timedelta(days=max_days)).isoformat()
        cursor.execute("DELETE FROM debug_events WHERE timestamp < ?", (cutoff_time,))
        
        # Check size
        file_size_bytes = db_path.stat().st_size if db_path.exists() else 0
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size_bytes > max_size_bytes:
            cursor.execute("SELECT COUNT(*) FROM debug_events")
            total_count = cursor.fetchone()[0]
            delete_count = max(1, total_count // 4)
            cursor.execute(f"""
                DELETE FROM debug_events
                WHERE event_id IN (
                    SELECT event_id FROM debug_events
                    ORDER BY timestamp ASC
                    LIMIT {delete_count}
                )
            """)
        
        conn.commit()
        conn.close()
    except Exception:
        pass


@dataclass
class DebugEvent:
    """A single debug event with full context."""
    event_id: str
    timestamp: str
    session_id: str
    level: str
    component: str
    event_type: str
    data: dict[str, Any]
    traceback: str | None = None

    def to_json(self) -> str:
        """Serialize event to JSON string."""
        return json.dumps(asdict(self))


class DebugSession:
    """Manages a debug session with persistent event storage."""

    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.events: list[DebugEvent] = []
        self.start_time = datetime.now(timezone.utc)

    def emit(self, level: str, component: str, event_type: str, **data: Any) -> None:
        """Emit a debug event to this session."""
        event = DebugEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self.session_id,
            level=level,
            component=component,
            event_type=event_type,
            data=data
        )
        self.events.append(event)
        self._persist(event)

    def query(self, **filters: Any) -> list[DebugEvent]:
        """Query events in this session by any field."""
        results = self.events
        for key, value in filters.items():
            results = [e for e in results if getattr(e, key, None) == value]
        return results

    def summary(self) -> dict[str, Any]:
        """Return session summary statistics."""
        duration = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        by_level: dict[str, int] = {}
        by_component: dict[str, int] = {}
        by_type: dict[str, int] = {}
        errors: list[DebugEvent] = []

        for event in self.events:
            by_level[event.level] = by_level.get(event.level, 0) + 1
            by_component[event.component] = by_component.get(event.component, 0) + 1
            by_type[event.event_type] = by_type.get(event.event_type, 0) + 1
            if event.level == "ERROR":
                errors.append(event)

        return {
            "session_id": self.session_id,
            "duration_sec": duration,
            "total_events": len(self.events),
            "by_level": by_level,
            "by_component": by_component,
            "by_type": by_type,
            "errors": errors,
        }

    def _persist(self, event: DebugEvent) -> None:
        """Persist an event to the telemetry database."""
        if not _should_persist_event(event.level):
            return

        db_path = _get_db_path()
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(db_path, timeout=5.0)
            conn.execute("PRAGMA busy_timeout = 5000")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS debug_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    session_id TEXT,
                    level TEXT,
                    component TEXT,
                    event_type TEXT,
                    data TEXT,
                    traceback TEXT
                )
            """)
            conn.execute("""
                INSERT INTO debug_events (
                    event_id, timestamp, session_id, level,
                    component, event_type, data, traceback
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id, event.timestamp, event.session_id,
                event.level, event.component, event.event_type,
                json.dumps(event.data), event.traceback
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass


_thread_local = threading.local()


def get_debug_session() -> DebugSession:
    """Get or create the current thread's debug session."""
    if not hasattr(_thread_local, "session"):
        _thread_local.session = DebugSession()
    return _thread_local.session


def clear_debug_session() -> None:
    """Clear the current thread's debug session."""
    _thread_local.session = DebugSession()
