"""Watch queue module for yt-fts.

This module provides:
- Queue management (add, list, remove)
- Queue ordering (promote, demote)
- Queue persistence (save, load)
- Queue statistics
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from yt_fts.db.infra import get_db_connection
from yt_fts.utils.config import get_db_path

# Priority levels
PRIORITY_LEVELS = {
    "low": 0,
    "normal": 1,
    "high": 2,
}

PRIORITY_NAMES = {v: k for k, v in PRIORITY_LEVELS.items()}


def ensure_queue_tables() -> None:
    """Ensure watch_queue table exists in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create watch_queue table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watch_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            priority INTEGER DEFAULT 1,
            position INTEGER NOT NULL,
            added_at TEXT NOT NULL,
            notes TEXT
        )
    """)

    # Create indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_watch_queue_position
        ON watch_queue(position)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_watch_queue_priority
        ON watch_queue(priority)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_watch_queue_video_id
        ON watch_queue(video_id)
    """)

    conn.commit()
    conn.close()


def queue_add(
    video_id: str,
    priority: Literal["low", "normal", "high"] = "normal",
    notes: str | None = None,
) -> dict[str, Any]:
    """Add a video to the watch queue.

    Args:
        video_id: YouTube video ID
        priority: Priority level (low, normal, high)
        notes: Optional notes

    Returns:
        Dictionary with added item details

    Raises:
        ValueError: If video not found or already in queue
    """
    ensure_queue_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify video exists
    cursor.execute("SELECT video_id FROM Videos WHERE video_id = ?", (video_id,))
    if not cursor.fetchone():
        conn.close()
        msg = f"Video '{video_id}' not found in database"
        raise ValueError(msg)

    # Check if already in queue
    cursor.execute("SELECT id FROM watch_queue WHERE video_id = ?", (video_id,))
    if cursor.fetchone():
        conn.close()
        msg = f"Video '{video_id}' is already in queue"
        raise ValueError(msg)

    # Get next position
    cursor.execute("SELECT COALESCE(MAX(position), 0) + 1 FROM watch_queue")
    next_position = cursor.fetchone()[0]

    # Add to queue
    added_at = datetime.now(timezone.utc).isoformat()
    priority_value = PRIORITY_LEVELS.get(priority, 1)

    cursor.execute(
        """INSERT INTO watch_queue (video_id, priority, position, added_at, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (video_id, priority_value, next_position, added_at, notes)
    )

    item_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": item_id,
        "video_id": video_id,
        "priority": priority,
        "position": next_position,
        "added_at": added_at,
        "notes": notes,
    }


def queue_list(
    filter_priority: Literal["all", "low", "normal", "high"] = "all",
) -> list[dict[str, Any]]:
    """List all items in the watch queue.

    Args:
        filter_priority: Filter by priority level

    Returns:
        List of queue items with video metadata
    """
    ensure_queue_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build query with optional filter
    if filter_priority == "all":
        query = """
            SELECT
                q.id,
                q.video_id,
                q.priority,
                q.position,
                q.added_at,
                q.notes,
                v.video_title
            FROM watch_queue q
            LEFT JOIN Videos v ON q.video_id = v.video_id
            ORDER BY q.position
        """
        cursor.execute(query)
    else:
        priority_value = PRIORITY_LEVELS.get(filter_priority, 1)
        query = """
            SELECT
                q.id,
                q.video_id,
                q.priority,
                q.position,
                q.added_at,
                q.notes,
                v.video_title
            FROM watch_queue q
            LEFT JOIN Videos v ON q.video_id = v.video_id
            WHERE q.priority = ?
            ORDER BY q.position
        """
        cursor.execute(query, (priority_value,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "video_id": row[1],
            "priority": PRIORITY_NAMES.get(row[2], "normal"),
            "position": row[3],
            "added_at": row[4],
            "notes": row[5],
            "video_title": row[6],
        }
        for row in rows
    ]


def queue_remove(position: int) -> dict[str, Any]:
    """Remove an item from the queue by position.

    Args:
        position: Position number (1-based)

    Returns:
        Dictionary with removal results

    Raises:
        ValueError: If position is invalid
    """
    ensure_queue_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get item at position
    cursor.execute(
        """SELECT id, video_id FROM watch_queue WHERE position = ?""",
        (position,)
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        msg = f"Invalid position: {position}"
        raise ValueError(msg)

    item_id, video_id = row

    # Delete the item
    cursor.execute("DELETE FROM watch_queue WHERE position = ?", (position,))

    # Shift positions down
    cursor.execute(
        """UPDATE watch_queue SET position = position - 1
           WHERE position > ?""",
        (position,)
    )

    conn.commit()
    conn.close()

    return {
        "removed_id": item_id,
        "video_id": video_id,
        "position": position,
    }


def queue_promote(position: int, to_position: int | None = None) -> dict[str, Any]:
    """Promote an item in the queue (move it up).

    Args:
        position: Current position (1-based)
        to_position: Target position (default: one position up)

    Returns:
        Dictionary with new position details

    Raises:
        ValueError: If positions are invalid
    """
    ensure_queue_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get queue size
    cursor.execute("SELECT COUNT(*) FROM watch_queue")
    queue_size = cursor.fetchone()[0]

    if position < 1 or position > queue_size:
        conn.close()
        msg = f"Invalid position: {position}"
        raise ValueError(msg)

    # Default: promote by one position
    if to_position is None:
        to_position = max(1, position - 1)

    if to_position < 1 or to_position > queue_size:
        conn.close()
        msg = f"Invalid target position: {to_position}"
        raise ValueError(msg)

    if to_position == position:
        conn.close()
        return {"position": position, "target": position, "moved": False}

    # Get the item to move
    cursor.execute(
        "SELECT id, video_id, priority, added_at, notes FROM watch_queue WHERE position = ?",
        (position,)
    )
    item = cursor.fetchone()

    if not item:
        conn.close()
        msg = f"No item at position: {position}"
        raise ValueError(msg)

    item_id, video_id, _priority, _added_at, _notes = item

    # Update positions
    if to_position < position:
        # Moving up: shift items between to_position and position-1 down by 1
        cursor.execute(
            """UPDATE watch_queue SET position = position + 1
               WHERE position >= ? AND position < ?""",
            (to_position, position)
        )
    else:
        # Moving down: shift items between position+1 and to_position up by 1
        cursor.execute(
            """UPDATE watch_queue SET position = position - 1
               WHERE position > ? AND position <= ?""",
            (position, to_position)
        )

    # Move item to new position
    cursor.execute(
        "UPDATE watch_queue SET position = ? WHERE id = ?",
        (to_position, item_id)
    )

    conn.commit()
    conn.close()

    return {
        "video_id": video_id,
        "from_position": position,
        "to_position": to_position,
        "moved": True,
    }


def queue_demote(position: int, to_position: int | None = None) -> dict[str, Any]:
    """Demote an item in the queue (move it down).

    Args:
        position: Current position (1-based)
        to_position: Target position (default: one position down)

    Returns:
        Dictionary with new position details

    Raises:
        ValueError: If positions are invalid
    """
    ensure_queue_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get queue size
    cursor.execute("SELECT COUNT(*) FROM watch_queue")
    queue_size = cursor.fetchone()[0]

    if position < 1 or position > queue_size:
        conn.close()
        msg = f"Invalid position: {position}"
        raise ValueError(msg)

    # Default: demote by one position
    if to_position is None:
        to_position = min(queue_size, position + 1)

    if to_position < 1 or to_position > queue_size:
        conn.close()
        msg = f"Invalid target position: {to_position}"
        raise ValueError(msg)

    if to_position == position:
        conn.close()
        return {"position": position, "target": position, "moved": False}

    # Reuse promote logic (it works bidirectionally)
    conn.close()
    return queue_promote(position, to_position)


def queue_clear(confirmed: bool = False) -> int:
    """Clear all items from the queue.

    Args:
        confirmed: Whether user confirmed the clear operation

    Returns:
        Number of items cleared
    """
    if not confirmed:
        return 0

    ensure_queue_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get count before clearing
    cursor.execute("SELECT COUNT(*) FROM watch_queue")
    count = cursor.fetchone()[0]

    # Clear all
    cursor.execute("DELETE FROM watch_queue")

    conn.commit()
    conn.close()

    return count


def queue_stats() -> dict[str, Any]:
    """Get statistics about the watch queue.

    Returns:
        Dictionary with queue statistics
    """
    ensure_queue_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total count
    cursor.execute("SELECT COUNT(*) FROM watch_queue")
    total = cursor.fetchone()[0]

    # Count by priority
    stats = {
        "total": total,
        "by_priority": {},
    }

    for priority_name, priority_value in PRIORITY_LEVELS.items():
        cursor.execute(
            "SELECT COUNT(*) FROM watch_queue WHERE priority = ?",
            (priority_value,)
        )
        stats["by_priority"][priority_name] = cursor.fetchone()[0]

    # Oldest and newest items
    cursor.execute("SELECT MIN(added_at), MAX(added_at) FROM watch_queue")
    row = cursor.fetchone()
    stats["oldest_at"] = row[0]
    stats["newest_at"] = row[1]

    conn.close()

    return stats


def queue_save(file_path: str | None = None) -> dict[str, Any]:
    """Save queue to a JSON file.

    Args:
        file_path: Path to save file (defaults to queue.json in config dir)

    Returns:
        Dictionary with save results
    """
    ensure_queue_tables()

    if file_path is None:
        file_path = get_default_queue_path()

    items = queue_list(filter_priority="all")

    data = {
        "version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "items": [
            {
                "video_id": item["video_id"],
                "priority": item["priority"],
                "added_at": item["added_at"],
                "notes": item["notes"],
            }
            for item in items
        ]
    }

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        "file": str(path),
        "items_saved": len(items),
    }


def queue_load(
    file_path: str | None = None,
    replace: bool = False,
) -> dict[str, Any]:
    """Load queue from a JSON file.

    Args:
        file_path: Path to load file (defaults to queue.json in config dir)
        replace: If True, replace existing queue. If False, merge.

    Returns:
        Dictionary with load results

    Raises:
        ValueError: If file not found or invalid JSON
    """
    ensure_queue_tables()

    if file_path is None:
        file_path = get_default_queue_path()

    path = Path(file_path)
    if not path.exists():
        msg = f"Queue file not found: {file_path}"
        raise ValueError(msg)

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON in queue file: {e}"
        raise ValueError(msg)

    # Validate schema
    if "items" not in data:
        msg = "Invalid queue schema: missing 'items'"
        raise ValueError(msg)

    # Clear existing queue if replace is True
    if replace:
        from yt_fts.db.infra import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watch_queue")
            conn.commit()

    added = []
    duplicates = []
    errors = []

    for item in data["items"]:
        video_id = item.get("video_id")
        if not video_id:
            continue

        priority = item.get("priority", "normal")
        if priority not in PRIORITY_LEVELS:
            priority = "normal"

        notes = item.get("notes")

        try:
            queue_add(video_id, priority, notes)
            added.append(video_id)
        except ValueError as e:
            if "already in queue" in str(e):
                duplicates.append(video_id)
            else:
                errors.append({"video_id": video_id, "error": str(e)})

    return {
        "file": str(path),
        "added": added,
        "duplicates": duplicates,
        "errors": errors,
    }


def get_default_queue_path() -> str:
    """Get the default queue file path.

    Returns:
        Path to queue.json in config directory
    """
    config_dir = Path(get_db_path()).parent
    return str(config_dir / "queue.json")
