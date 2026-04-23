"""Task projections — open-task view from normalized event log."""

from __future__ import annotations

from .db import get_connection
from pathlib import Path

DB_PATH = Path("P:/__csf/data/chat_history.db")


def open_tasks(provider_id: str | None = None) -> list[dict]:
    """Return open (unresolved) tasks.

    A task is open if it has no resolved_at timestamp.
    Optionally filtered by provider_id.
    """
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()

    if provider_id:
        cursor.execute(
            "SELECT * FROM tasks WHERE provider_id = ? AND resolved_at IS NULL ORDER BY opened_at DESC",
            (provider_id,),
        )
    else:
        cursor.execute("SELECT * FROM tasks WHERE resolved_at IS NULL ORDER BY opened_at DESC")

    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row, strict=True)) for row in cursor.fetchall()]


def resolve_task(task_id: str, resolved_at: str | None = None) -> bool:
    """Mark a task as resolved with a timestamp.

    Args:
        task_id: The task to resolve
        resolved_at: ISO 8601 timestamp; defaults to current UTC time

    Returns:
        True if a row was updated, False if task not found.
    """
    if resolved_at is None:
        from datetime import UTC, datetime
        resolved_at = datetime.now(UTC).isoformat()

    conn = get_connection(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET resolved_at = ?, status = 'resolved' WHERE task_id = ? AND resolved_at IS NULL",
        (resolved_at, task_id),
    )
    conn.commit()
    return cursor.rowcount > 0
