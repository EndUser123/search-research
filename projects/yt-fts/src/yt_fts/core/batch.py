"""Batch operations module for yt-fts.

This module provides:
- Batch delete functionality for videos
- Batch export functionality (txt, srt, json formats)
- Progress tracking for batch operations
"""
from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from yt_fts.db.infra import get_db_connection
from yt_fts.utils.config import get_db_path


def ensure_batch_tables() -> None:
    """Ensure batch-related tables exist in the database.

    Creates the batch_jobs table for tracking batch operations.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create batch_jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_type TEXT NOT NULL,
            total_items INTEGER NOT NULL,
            completed_items INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            started_at TEXT,
            completed_at TEXT,
            error_message TEXT
        )
    """)

    # Create indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_batch_jobs_status
        ON batch_jobs(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_batch_jobs_started_at
        ON batch_jobs(started_at)
    """)

    conn.commit()
    conn.close()


def batch_delete_videos(
    video_ids: list[str],
    confirmed: bool = False,
) -> dict[str, Any]:
    """Delete multiple videos from the database.

    Args:
        video_ids: List of video IDs to delete
        confirmed: Whether deletion was confirmed by user

    Returns:
        Dictionary with deletion results including:
        - deleted: List of successfully deleted video IDs
        - not_found: List of video IDs that were not in database
        - count: Number of videos deleted
    """
    ensure_batch_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    deleted = []
    not_found = []

    for video_id in video_ids:
        # Check if video exists
        cursor.execute("SELECT video_id FROM Videos WHERE video_id = ?", (video_id,))
        if not cursor.fetchone():
            not_found.append(video_id)
            continue

        # Delete from Subtitles first (cascade)
        cursor.execute("DELETE FROM Subtitles WHERE video_id = ?", (video_id,))
        # Delete from Videos
        cursor.execute("DELETE FROM Videos WHERE video_id = ?", (video_id,))
        deleted.append(video_id)

    conn.commit()
    conn.close()

    return {
        "deleted": deleted,
        "not_found": not_found,
        "count": len(deleted),
    }


def batch_export_videos(
    video_ids: list[str],
    format: Literal["txt", "srt", "json"] = "txt",
    output_dir: str | None = None,
    zip_output: bool = False,
    zip_path: str | None = None,
) -> dict:
    """Export multiple videos to files.

    Args:
        video_ids: List of video IDs to export
        format: Export format (txt, srt, or json)
        output_dir: Directory to save exports (defaults to current directory)
        zip_output: Whether to create a zip file
        zip_path: Path for zip file (required if zip_output=True)

    Returns:
        Dictionary with export results including:
        - exported: List of successfully exported video IDs
        - not_found: List of video IDs that were not in database
        - failed: List of video IDs that failed to export
        - files: List of created file paths
        - count: Number of videos exported
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Determine output directory
    out_path = Path(output_dir) if output_dir else Path.cwd()

    # Create output directory if needed
    out_path.mkdir(parents=True, exist_ok=True)

    exported = []
    not_found = []
    failed = []
    created_files = []

    for video_id in video_ids:
        # Get video metadata
        cursor.execute(
            "SELECT video_title FROM Videos WHERE video_id = ?",
            (video_id,)
        )
        video_row = cursor.fetchone()

        if not video_row:
            not_found.append(video_id)
            continue

        video_title = video_row[0] or video_id

        # Get subtitles
        cursor.execute(
            """SELECT start_time, stop_time, text
               FROM Subtitles
               WHERE video_id = ?
               ORDER BY start_time""",
            (video_id,)
        )
        subtitles = cursor.fetchall()

        if not subtitles:
            failed.append(video_id)
            continue

        # Generate filename
        safe_title = "".join(
            c for c in video_title
            if c.isalnum() or c in (" ", "-", "_", ".")
        ).strip() or video_id
        filename = f"{safe_title}.{format}"

        try:
            file_path = out_path / filename
            _write_export_file(file_path, subtitles, format, video_title, video_id)
            exported.append(video_id)
            created_files.append(str(file_path))
        except Exception:
            failed.append(video_id)

    conn.close()

    # Create zip file if requested
    if zip_output and created_files and zip_path:
        zip_file = Path(zip_path)
        with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in created_files:
                zf.write(file_path, Path(file_path).name)
        # Remove individual files after zipping
        for file_path in created_files:
            Path(file_path).unlink()

    return {
        "exported": exported,
        "not_found": not_found,
        "failed": failed,
        "files": created_files,
        "zip_file": str(zip_path) if zip_output and zip_path else None,
        "count": len(exported),
    }


def _write_export_file(
    file_path: Path,
    subtitles: list[tuple],
    format: Literal["txt", "srt", "json"],
    video_title: str,
    video_id: str,
) -> None:
    """Write export file in the specified format.

    Args:
        file_path: Path to write the file
        subtitles: List of (start_time, stop_time, text) tuples
        format: Export format
        video_title: Video title
        video_id: Video ID
    """
    with open(file_path, "w", encoding="utf-8") as f:
        if format == "txt":
            f.write(f"Video: {video_title}\n")
            f.write(f"Video ID: {video_id}\n")
            f.write(f"Exported: {datetime.now(timezone.utc).isoformat()}\n")
            f.write("=" * 60 + "\n\n")
            for start, stop, text in subtitles:
                f.write(f"[{start}] {text}\n")

        elif format == "srt":
            for i, (start, stop, text) in enumerate(subtitles, 1):
                f.write(f"{i}\n")
                f.write(f"{_format_srt_time(start)} --> {_format_srt_time(stop)}\n")
                f.write(f"{text}\n\n")

        elif format == "json":
            data = {
                "video_id": video_id,
                "title": video_title,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "subtitles": [
                    {
                        "start": start,
                        "stop": stop,
                        "text": text,
                    }
                    for start, stop, text in subtitles
                ]
            }
            json.dump(data, f, ensure_ascii=False, indent=2)


def _format_srt_time(time_str: str) -> str:
    """Convert database time format to SRT time format.

    Args:
        time_str: Time in seconds (e.g., "123.5")

    Returns:
        SRT format time (e.g., "00:02:03,500")
    """
    try:
        seconds = float(time_str)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    except (ValueError, TypeError):
        return "00:00:00,000"


def batch_add_to_playlist(
    playlist_name: str,
    video_ids: list[str],
) -> dict:
    """Add multiple videos to a playlist.

    Args:
        playlist_name: Name of the playlist
        video_ids: List of video IDs to add

    Returns:
        Dictionary with results including:
        - added: List of successfully added video IDs
        - not_found: List of video IDs not in database
        - already_in_playlist: List of video IDs already in playlist
        - count: Number of videos added
    """
    from .playlists import add_video_to_playlist, get_playlist_by_name

    # Check if playlist exists
    playlist = get_playlist_by_name(playlist_name)
    if not playlist:
        msg = f"Playlist '{playlist_name}' not found"
        raise ValueError(msg)

    conn = get_db_connection()
    cursor = conn.cursor()

    added = []
    not_found = []
    already_in_playlist = []

    for video_id in video_ids:
        # Check if video exists
        cursor.execute("SELECT video_id FROM Videos WHERE video_id = ?", (video_id,))
        if not cursor.fetchone():
            not_found.append(video_id)
            continue

        # Check if already in playlist
        cursor.execute(
            """SELECT pv.id
               FROM playlist_videos pv
               JOIN playlists p ON pv.playlist_id = p.id
               WHERE p.name = ? AND pv.video_id = ?""",
            (playlist_name, video_id)
        )
        if cursor.fetchone():
            already_in_playlist.append(video_id)
            continue

        try:
            add_video_to_playlist(playlist_name, video_id)
            added.append(video_id)
        except Exception:
            pass

    conn.close()

    return {
        "added": added,
        "not_found": not_found,
        "already_in_playlist": already_in_playlist,
        "count": len(added),
    }
