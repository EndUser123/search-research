"""
Database-Filesystem Synchronization Module

This module provides functions to synchronize the database download status
with the actual files present on the filesystem. This fixes issues where
files exist on disk but are still marked as 'pending' in the database.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .download import _log_with_progress  # Import _log_with_progress
from .reverse_sync import match_file_to_database_record
from .storage import get_storage


def get_file_hash(file_path: str, chunk_size: int = 8192) -> str | None:
    pass


def sync_channel_database_with_filesystem(
    channel_name: str, dry_run: bool = False, progress: Any | None = None
) -> dict[str, int]:
    """
    Synchronize database download status with filesystem for a specific channel.

    Args:
        channel_name: Name of the channel to sync
        dry_run: If True, only report what would be changed without making changes

    Returns:
        Dictionary with sync statistics
    """

    stats = {
        "files_on_disk": 0,
        "database_pending": 0,
        "matches_found": 0,
        "updated_to_completed": 0,
        "unmatched_files": 0,
        "errors": 0,
    }

    _log_with_progress(
        f"  ✨ Starting database-filesystem sync (dry_run={dry_run})", progress
    )

    try:
        # Get database storage instance
        storage = get_storage(channel_name)

        # Get media directory path
        media_dir = Path(f"channels/{channel_name}/_media")

        if not media_dir.exists():
            _log_with_progress(
                f"Media directory does not exist: {media_dir}",
                progress,
                level="warning",
            )
            return stats

        # Scan filesystem for actual files
        _log_with_progress("        Scanning filesystem directory...", progress)
        actual_files = []
        file_count = 0

        # Use os.listdir for better performance on large directories
        import os

        try:
            filenames = os.listdir(media_dir)
            total_files = len(filenames)
            _log_with_progress(
                f"        Found {total_files} items in directory", progress
            )

            # Process files in batches for large directories
            batch_size = 1000 if total_files > 5000 else total_files

            for i, filename in enumerate(filenames):
                file_path = media_dir / filename
                if file_path.is_file():
                    try:
                        file_size = file_path.stat().st_size
                        actual_files.append(
                            {
                                "filename": filename,
                                "full_path": str(file_path),
                                "size": file_size,
                            }
                        )
                        file_count += 1

                        # Progress update for large directories
                        if file_count % batch_size == 0 and total_files > 1000:
                            _log_with_progress(
                                f"        Processed {file_count}/{total_files} files...",
                                progress,
                            )

                    except Exception as e:
                        logger.error(f"Error reading file {file_path}: {e}")
                        stats["errors"] += 1

        except Exception as e:
            logger.error(f"Error listing directory {media_dir}: {e}")
            stats["errors"] += 1
            return stats

        stats["files_on_disk"] = len(actual_files)
        _log_with_progress(
            f"        Filesystem scan completed: {stats['files_on_disk']} files",
            progress,
        )

        # Match files to database records
        _log_with_progress(
            f"        Starting database matching for {stats['files_on_disk']} files...",
            progress,
        )
        unmatched_files = []

        # Progress tracking for database matching
        match_batch_size = 500

        for i, file_info in enumerate(actual_files):
            # Progress update for large numbers of files
            if i > 0 and i % match_batch_size == 0:
                _log_with_progress(
                    f"        Matched {i}/{stats['files_on_disk']} files...", progress
                )

            match = match_file_to_database_record(
                file_info["filename"],
                file_info["full_path"],
                file_info["size"],
                storage,  # Pass the storage object directly
            )

            if match:
                stats["matches_found"] += 1

                # Only update if the status is not already 'completed'
                if match.get("download_status") != "completed":
                    if not dry_run:
                        # Update database status to 'completed'
                        try:
                            storage.update_download_status(
                                telegram_id=match["id"],
                                status="completed",
                                filename=file_info["filename"],
                            )
                            stats["updated_to_completed"] += 1
                            _log_with_progress(
                                f"✅ Updated message {match['id']} to completed (file: {file_info['filename']})",
                                progress,
                            )
                        except Exception as e:
                            logger.error(
                                f"Failed to update status for message {match['id']}: {e}"
                            )
                            stats["errors"] += 1
                    else:
                        _log_with_progress(
                            f"[DRY RUN] Would update message {match['id']} to completed (file: {file_info['filename']})",
                            progress,
                        )
                        stats["updated_to_completed"] += 1
            else:
                unmatched_files.append(file_info)
                stats["unmatched_files"] += 1

        # Report unmatched files
        if unmatched_files:
            unmatched_files_str = "\n".join(
                [
                    f"          - {file_info['full_path']}"
                    for file_info in unmatched_files[:10]
                ]
            )
            if len(unmatched_files) > 10:
                unmatched_files_str += (
                    f"\n          ... and {len(unmatched_files) - 10} more"
                )
            _log_with_progress(
                f"        Found {len(unmatched_files)} files on disk in channel '{channel_name}' with no database match:",
                progress,
                level="warning",
            )
            _log_with_progress(f"{unmatched_files_str}", progress, level="warning")

    except Exception as e:
        logger.error(f"Error during database-filesystem sync: {e}")
        stats["errors"] += 1

    # === FILESYSTEM SECTION: Files on Disk ===
    _log_with_progress("  💽 Filesystem Status", progress)
    _log_with_progress(f"        Files on disk: {stats['files_on_disk']}", progress)

    # Add file type breakdown for files on disk
    if actual_files:
        file_types = {"Video": 0, "Image": 0, "Audio": 0, "Txt/PDF": 0, "Other": 0}

        for file_info in actual_files:
            filename = file_info["filename"].lower()
            # Categorize by file extension
            if any(
                ext in filename
                for ext in [".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".gif"]
            ):
                file_types["Video"] += 1
            elif any(
                ext in filename
                for ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]
            ):
                file_types["Image"] += 1
            elif any(
                ext in filename
                for ext in [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"]
            ):
                file_types["Audio"] += 1
            elif any(
                ext in filename for ext in [".pdf", ".txt", ".doc", ".docx", ".rtf"]
            ):
                file_types["Txt/PDF"] += 1
            else:
                file_types["Other"] += 1

        # Display file type breakdown with proper indentation
        for file_type, count in file_types.items():
            _log_with_progress(f"            {file_type}: {count}", progress)
    else:
        # Show empty categories
        for file_type in ["Video", "Image", "Audio", "Txt/PDF", "Other"]:
            _log_with_progress(f"            {file_type}: 0", progress)

    _log_with_progress(
        f"        Database pending: {stats['database_pending']}", progress
    )
    _log_with_progress(f"        Matches found: {stats['matches_found']}", progress)
    _log_with_progress(
        f"        Updated to completed: {stats['updated_to_completed']}", progress
    )
    _log_with_progress(f"        Unmatched files: {stats['unmatched_files']}", progress)
    _log_with_progress(f"        Errors: {stats['errors']}", progress)

    return stats


def sync_all_channels_databases_with_filesystem(
    dry_run: bool = False, progress: Any | None = None
) -> dict[str, dict[str, int]]:
    """
    Synchronize all channel databases with their respective filesystems.

    Args:
        dry_run: If True, only report what would be changed without making changes

    Returns:
        Dictionary mapping channel names to their sync statistics
    """

    results: dict[str, Any] = {}

    # Find all channel directories
    channels_dir = Path("channels")
    if not channels_dir.exists():
        _log_with_progress("Channels directory does not exist", progress, level="error")
        return results

    for channel_dir in channels_dir.iterdir():
        if channel_dir.is_dir():
            channel_name = channel_dir.name
            media_dir = channel_dir / "_media"

            # Only sync channels that have a media directory with files
            if media_dir.exists() and any(media_dir.iterdir()):
                _log_with_progress(f"Syncing channel: {channel_name}", progress)
                results[channel_name] = sync_channel_database_with_filesystem(
                    channel_name, dry_run, progress
                )
            else:
                _log_with_progress(
                    f"Skipping channel {channel_name} - no media directory or files",
                    progress,
                    level="debug",
                )

    # Report overall summary
    _log_with_progress("Overall sync summary:", progress)
    total_files = sum(stats["files_on_disk"] for stats in results.values())
    total_pending = sum(stats["database_pending"] for stats in results.values())
    total_updated = sum(stats["updated_to_completed"] for stats in results.values())

    _log_with_progress(f"  Channels processed: {len(results)}", progress)
    _log_with_progress(f"  Total files on disk: {total_files}", progress)
    _log_with_progress(f"  Total database pending: {total_pending}", progress)
    _log_with_progress(f"  Total updated to completed: {total_updated}", progress)

    return results


def verify_database_filesystem_consistency(
    channel_name: str, progress: Any | None = None
) -> dict[str, int]:
    """
    Verify the consistency between database and filesystem without making changes.

    Args:
        channel_name: Name of the channel to verify

    Returns:
        Dictionary with consistency statistics
    """

    _log_with_progress(
        f"Verifying database-filesystem consistency for channel '{channel_name}'",
        progress,
    )
    return sync_channel_database_with_filesystem(
        channel_name, dry_run=True, progress=progress
    )


if __name__ == "__main__":
    # Example usage - can be run as a standalone script
    import sys

    if len(sys.argv) > 1:
        channel_name = sys.argv[1]
        dry_run = "--dry-run" in sys.argv

        if channel_name == "all":
            sync_all_channels_databases_with_filesystem(dry_run=dry_run)
        else:
            sync_channel_database_with_filesystem(channel_name, dry_run=dry_run)
    else:
        print("Usage: python sync_database.py <channel_name|all> [--dry-run]")
        print("Example: python sync_database.py jcexclusive --dry-run")
