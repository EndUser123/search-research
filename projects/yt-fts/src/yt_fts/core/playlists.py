"""
Playlist and bookmark database schema and management.

This module provides functions for creating and managing the database
schema for playlists and bookmarks.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from yt_fts.db.infra import get_db_connection
from yt_fts.utils.config import get_db_path


def ensure_playlist_tables() -> None:
    """Create playlists, playlist_videos, and bookmarks tables if they don't exist.

    Tables created:
    - playlists: Stores playlist metadata (id, name, description, created_at)
    - playlist_videos: Many-to-many relationship between playlists and videos
                       (id, playlist_id, video_id, position, added_at)
    - bookmarks: User bookmarks for specific timestamps in videos
                 (id, video_id, timestamp, note, created_at)

    Also creates indexes for optimal query performance.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create playlists table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)

    # Create playlist_videos table for many-to-many relationship
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlist_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            video_id TEXT NOT NULL,
            position INTEGER NOT NULL,
            added_at TEXT NOT NULL,
            FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
            UNIQUE (playlist_id, video_id)
        )
    """)

    # Create bookmarks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (video_id) REFERENCES Videos(video_id) ON DELETE CASCADE
        )
    """)

    # Create indexes for performance
    # Playlists indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_playlists_name
        ON playlists(name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_playlists_created_at
        ON playlists(created_at)
    """)

    # Playlist videos indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_playlist_videos_playlist_id
        ON playlist_videos(playlist_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_playlist_videos_video_id
        ON playlist_videos(video_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_playlist_videos_position
        ON playlist_videos(playlist_id, position)
    """)

    # Bookmarks indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bookmarks_video_id
        ON bookmarks(video_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bookmarks_created_at
        ON bookmarks(created_at)
    """)

    conn.commit()
    conn.close()


def get_playlist_by_name(name: str) -> dict | None:
    """Get a playlist by name.

    Args:
        name: The playlist name

    Returns:
        Dictionary with playlist data or None if not found
    """
    ensure_playlist_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, description, created_at FROM playlists WHERE name = ?",
        (name,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "created_at": row[3],
        }
    return None


def create_playlist(name: str, description: str = "") -> dict:
    """Create a new playlist.

    Args:
        name: The playlist name (must be unique)
        description: Optional description

    Returns:
        Dictionary with the created playlist data

    Raises:
        ValueError: If playlist name already exists or is empty
    """
    ensure_playlist_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    if not name or not name.strip():
        conn.close()
        msg = "Playlist name cannot be empty"
        raise ValueError(msg)

    # Check for duplicate name
    cursor.execute("SELECT id FROM playlists WHERE name = ?", (name,))
    if cursor.fetchone():
        conn.close()
        msg = f"Playlist '{name}' already exists"
        raise ValueError(msg)

    created_at = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO playlists (name, description, created_at) VALUES (?, ?, ?)",
        (name, description, created_at)
    )

    playlist_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": playlist_id,
        "name": name,
        "description": description,
        "created_at": created_at,
    }


def list_playlists(sort_by: str = "name") -> list[dict]:
    """List all playlists with video counts.

    Args:
        sort_by: Sort order - 'name', 'date', or 'count'

    Returns:
        List of dictionaries with playlist data and video counts
    """
    ensure_playlist_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Map sort options to SQL clauses
    order_clauses = {
        "name": "p.name ASC",
        "date": "p.created_at DESC",
        "count": "video_count DESC, p.name ASC",
    }
    order_clause = order_clauses.get(sort_by, "p.name ASC")

    query = f"""
        SELECT
            p.id,
            p.name,
            p.description,
            p.created_at,
            COUNT(pv.video_id) as video_count
        FROM playlists p
        LEFT JOIN playlist_videos pv ON p.id = pv.playlist_id
        GROUP BY p.id
        ORDER BY {order_clause}
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "created_at": row[3],
            "video_count": row[4],
        }
        for row in rows
    ]


def get_playlist_videos(playlist_id: int) -> list[dict]:
    """Get all videos in a playlist with their metadata.

    Args:
        playlist_id: The playlist ID

    Returns:
        List of dictionaries with video data ordered by position
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check which tables exist
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('Videos', 'Channels')"
    )
    existing_tables = {row[0] for row in cursor.fetchall()}
    channels_exists = "Channels" in existing_tables

    if channels_exists:
        query = """
            SELECT
                pv.position,
                pv.video_id,
                v.video_title,
                v.video_url,
                v.channel_id,
                c.channel_name,
                pv.added_at
            FROM playlist_videos pv
            JOIN Videos v ON pv.video_id = v.video_id
            LEFT JOIN Channels c ON v.channel_id = c.channel_id
            WHERE pv.playlist_id = ?
            ORDER BY pv.position
        """
    else:
        query = """
            SELECT
                pv.position,
                pv.video_id,
                v.video_title,
                v.video_url,
                v.channel_id,
                NULL as channel_name,
                pv.added_at
            FROM playlist_videos pv
            JOIN Videos v ON pv.video_id = v.video_id
            WHERE pv.playlist_id = ?
            ORDER BY pv.position
        """

    cursor.execute(query, (playlist_id,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "position": row[0],
            "video_id": row[1],
            "video_title": row[2],
            "video_url": row[3],
            "channel_id": row[4],
            "channel_name": row[5],
            "added_at": row[6],
        }
        for row in rows
    ]


def add_video_to_playlist(playlist_name: str, video_id: str, position: int | None = None) -> dict:
    """Add a video to a playlist.

    Args:
        playlist_name: The playlist name
        video_id: The video ID to add
        position: Optional position (1-based). If None, appends to end.

    Returns:
        Dictionary with the entry data

    Raises:
        ValueError: If playlist doesn't exist, video not found, or duplicate entry
    """
    ensure_playlist_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get playlist
    playlist = get_playlist_by_name(playlist_name)
    if not playlist:
        conn.close()
        msg = f"Playlist '{playlist_name}' not found"
        raise ValueError(msg)

    playlist_id = playlist["id"]

    # Verify video exists
    cursor.execute("SELECT video_id FROM Videos WHERE video_id = ?", (video_id,))
    if not cursor.fetchone():
        conn.close()
        msg = f"Video '{video_id}' not found in database"
        raise ValueError(msg)

    # Check for duplicate
    cursor.execute(
        "SELECT id FROM playlist_videos WHERE playlist_id = ? AND video_id = ?",
        (playlist_id, video_id)
    )
    if cursor.fetchone():
        conn.close()
        msg = f"Video '{video_id}' is already in playlist '{playlist_name}'"
        raise ValueError(msg)

    # Determine position
    if position is None:
        # Append to end
        cursor.execute(
            "SELECT COALESCE(MAX(position), 0) + 1 FROM playlist_videos WHERE playlist_id = ?",
            (playlist_id,)
        )
        position = cursor.fetchone()[0]
    else:
        # Insert at position, shifting existing videos
        cursor.execute(
            """UPDATE playlist_videos
               SET position = position + 1
               WHERE playlist_id = ? AND position >= ?""",
            (playlist_id, position)
        )

    added_at = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO playlist_videos (playlist_id, video_id, position, added_at) VALUES (?, ?, ?, ?)",
        (playlist_id, video_id, position, added_at)
    )

    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": entry_id,
        "playlist_id": playlist_id,
        "video_id": video_id,
        "position": position,
        "added_at": added_at,
    }


def remove_video_from_playlist(playlist_name: str, video_id: str) -> bool:
    """Remove a video from a playlist.

    Args:
        playlist_name: The playlist name
        video_id: The video ID to remove

    Returns:
        True if removed, False if not found

    Raises:
        ValueError: If playlist doesn't exist
    """
    ensure_playlist_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get playlist
    playlist = get_playlist_by_name(playlist_name)
    if not playlist:
        conn.close()
        msg = f"Playlist '{playlist_name}' not found"
        raise ValueError(msg)

    playlist_id = playlist["id"]

    # Get the position before deletion
    cursor.execute(
        "SELECT position FROM playlist_videos WHERE playlist_id = ? AND video_id = ?",
        (playlist_id, video_id)
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return False

    removed_position = row[0]

    # Delete the entry
    cursor.execute(
        "DELETE FROM playlist_videos WHERE playlist_id = ? AND video_id = ?",
        (playlist_id, video_id)
    )

    # Shift positions down
    cursor.execute(
        """UPDATE playlist_videos
           SET position = position - 1
           WHERE playlist_id = ? AND position > ?""",
        (playlist_id, removed_position)
    )

    conn.commit()
    conn.close()
    return True


def delete_playlist(name: str) -> bool:
    """Delete a playlist and all its entries.

    Args:
        name: The playlist name

    Returns:
        True if deleted, False if not found

    Raises:
        ValueError: If playlist name doesn't exist
    """
    ensure_playlist_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check exists
    cursor.execute("SELECT id FROM playlists WHERE name = ?", (name,))
    if not cursor.fetchone():
        conn.close()
        msg = f"Playlist '{name}' not found"
        raise ValueError(msg)

    # Delete (CASCADE will delete playlist_videos entries)
    cursor.execute("DELETE FROM playlists WHERE name = ?", (name,))

    conn.commit()
    conn.close()
    return True


def create_bookmark(video_id: str, timestamp: str, note: str) -> dict:
    """Create a bookmark for a video.

    Args:
        video_id: The video ID
        timestamp: Timestamp string (e.g., "1:23", "83", "1:23:45")
        note: The bookmark note

    Returns:
        Dictionary with the created bookmark data

    Raises:
        ValueError: If video not found
    """
    ensure_playlist_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify video exists
    cursor.execute("SELECT video_id FROM Videos WHERE video_id = ?", (video_id,))
    if not cursor.fetchone():
        conn.close()
        msg = f"Video '{video_id}' not found in database"
        raise ValueError(msg)

    created_at = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO bookmarks (video_id, timestamp, note, created_at) VALUES (?, ?, ?, ?)",
        (video_id, timestamp, note, created_at)
    )

    bookmark_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": bookmark_id,
        "video_id": video_id,
        "timestamp": timestamp,
        "note": note,
        "created_at": created_at,
    }


def list_bookmarks(video_id: str | None = None) -> list[dict]:
    """List bookmarks with video metadata.

    Args:
        video_id: Optional video ID to filter by

    Returns:
        List of dictionaries with bookmark data
    """
    ensure_playlist_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    if video_id:
        query = """
            SELECT
                b.id,
                b.video_id,
                b.timestamp,
                b.note,
                b.created_at,
                v.video_title
            FROM bookmarks b
            JOIN Videos v ON b.video_id = v.video_id
            WHERE b.video_id = ?
            ORDER BY b.created_at DESC
        """
        cursor.execute(query, (video_id,))
    else:
        query = """
            SELECT
                b.id,
                b.video_id,
                b.timestamp,
                b.note,
                b.created_at,
                v.video_title
            FROM bookmarks b
            JOIN Videos v ON b.video_id = v.video_id
            ORDER BY b.created_at DESC
        """
        cursor.execute(query)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "video_id": row[1],
            "timestamp": row[2],
            "note": row[3],
            "created_at": row[4],
            "video_title": row[5],
        }
        for row in rows
    ]


def delete_bookmark(bookmark_id: int) -> bool:
    """Delete a bookmark by ID.

    Args:
        bookmark_id: The bookmark ID

    Returns:
        True if deleted, False if not found
    """
    ensure_playlist_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return deleted


def export_playlist(name: str) -> dict | None:
    """Export a playlist to a dict format (for JSON serialization).

    Args:
        name: The playlist name

    Returns:
        Dictionary with playlist data and videos, or None if not found

    Raises:
        ValueError: If playlist doesn't exist
    """
    playlist = get_playlist_by_name(name)
    if not playlist:
        msg = f"Playlist '{name}' not found"
        raise ValueError(msg)

    videos = get_playlist_videos(playlist["id"])

    return {
        "name": playlist["name"],
        "description": playlist["description"],
        "created_at": playlist["created_at"],
        "videos": [
            {
                "video_id": v["video_id"],
                "position": v["position"],
            }
            for v in videos
        ]
    }


def import_playlist(data: dict, rename_if_duplicate: bool = False) -> dict:
    """Import a playlist from a dict.

    Args:
        data: Dictionary with playlist data (name, description, created_at, videos)
        rename_if_duplicate: If True, append " (N)" to name if duplicate

    Returns:
        Dictionary with the created playlist data

    Raises:
        ValueError: If data is invalid or import fails
    """
    ensure_playlist_tables()

    # Validate required fields
    if "name" not in data or not data["name"]:
        msg = "Playlist data must include a 'name' field"
        raise ValueError(msg)

    name = data["name"]
    description = data.get("description", "")
    videos = data.get("videos", [])

    # Handle duplicate names
    original_name = name
    counter = 1
    while get_playlist_by_name(name):
        if not rename_if_duplicate:
            msg = f"Playlist '{name}' already exists"
            raise ValueError(msg)
        name = f"{original_name} ({counter})"
        counter += 1

    # Create playlist (use original created_at if provided)
    conn = get_db_connection()
    cursor = conn.cursor()

    created_at = data.get("created_at", datetime.now(timezone.utc).isoformat())
    cursor.execute(
        "INSERT INTO playlists (name, description, created_at) VALUES (?, ?, ?)",
        (name, description, created_at)
    )

    playlist_id = cursor.lastrowid

    # Add videos
    added_count = 0
    for video_data in videos:
        video_id = video_data.get("video_id")
        if not video_id:
            continue

        # Check if video exists
        cursor.execute("SELECT video_id FROM Videos WHERE video_id = ?", (video_id,))
        if cursor.fetchone():
            position = video_data.get("position", added_count + 1)
            added_at = datetime.now(timezone.utc).isoformat()

            try:
                cursor.execute(
                    "INSERT INTO playlist_videos (playlist_id, video_id, position, added_at) VALUES (?, ?, ?, ?)",
                    (playlist_id, video_id, position, added_at)
                )
                added_count += 1
            except sqlite3.IntegrityError:
                # Duplicate video in playlist, skip
                pass

    conn.commit()
    conn.close()

    return {
        "id": playlist_id,
        "name": name,
        "description": description,
        "created_at": created_at,
        "videos_added": added_count,
    }
