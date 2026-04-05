"""
Reverse Synchronization Module

This module provides functions to synchronize the database download status
with the actual files present on the filesystem. This fixes issues where
files exist on disk but are still marked as 'pending' in the database.
"""

import hashlib
import re  # Added for regex
from pathlib import Path

from loguru import logger

from .database.schema import get_connection
from .database.storage import DatabaseStorage, get_storage


def get_file_hash(file_path: str, chunk_size: int = 8192) -> str | None:
    """Calculate MD5 hash of a file for verification."""
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.debug(f"Could not calculate hash for {file_path}: {e}")
        return None


async def reconcile_orphaned_files(
    channel_name: str,
    unmatched_files: list,
    storage: "DatabaseStorage",
    dry_run: bool = False,
) -> int:
    """
    Auto-reconcile orphaned files by creating database records for them.

    Args:
        channel_name: Name of the channel
        unmatched_files: List of file info dicts for orphaned files
        storage: Database storage instance
        dry_run: If True, only simulate reconciliation without making changes

    Returns:
        Number of files successfully reconciled
    """
    logger.info(
        f"🔧 Starting auto-reconciliation for {len(unmatched_files)} orphaned files in '{channel_name}'"
    )

    reconciled_count = 0
    failed_count = 0

    # Get channel ID for record creation
    try:
        channel_id = await storage.get_channel_id()
    except Exception as e:
        logger.error(f"❌ Cannot get channel ID for reconciliation: {e}")
        return 0

    # Process each unmatched file
    for i, file_info in enumerate(unmatched_files):
        try:
            # Skip if too many failures (prevent infinite loop)
            if (
                failed_count > 50 and failed_count / max(i, 1) > 0.5
            ):  # More than 50% failure rate
                logger.warning(
                    "⚠️  Too many reconciliation failures - stopping to prevent cascade"
                )
                break

            # Extract file information
            file_path = Path(file_info["full_path"])
            filename = file_path.name
            file_size = file_info["size"]

            # Skip if file no longer exists
            if not file_path.exists():
                continue

            # Create a synthetic database record for this orphaned file
            # This marks it as "completed" since it already exists on disk
            if not dry_run:
                try:
                    # Create a minimal record that marks this file as completed
                    # This prevents the system from trying to download it again
                    await storage.create_orphaned_file_record(
                        channel_id=channel_id,
                        filename=filename,
                        file_size=file_size,
                        file_path=str(file_path),
                    )
                    reconciled_count += 1

                    # Log progress every 100 files
                    if reconciled_count % 100 == 0:
                        logger.info(
                            f"   🔄 Reconciled {reconciled_count}/{len(unmatched_files)} orphaned files..."
                        )

                except Exception as e:
                    failed_count += 1
                    logger.debug(f"   ⚠️  Could not reconcile {filename}: {e}")
                    # Continue with other files - don't fail the entire operation
            else:
                # Dry run - just count what would be reconciled
                reconciled_count += 1

        except Exception as e:
            failed_count += 1
            logger.debug(
                f"   ⚠️  Error processing orphaned file {file_info.get('filename', 'unknown')}: {e}"
            )
            # Continue with other files

    logger.info(
        f"🔧 Auto-reconciliation completed: {reconciled_count} files reconciled, {failed_count} failed"
    )
    return reconciled_count


async def match_file_to_database_record(
    filename: str, file_path: str, file_size: int, storage: DatabaseStorage
) -> dict | None:
    """
    Match a filesystem file to a database record using multiple strategies, querying the database directly.

    Args:
        filename: Name of the file on disk
        file_path: Full path to the file
        file_size: Size of the file in bytes
        storage: An instance of DatabaseStorage to query the database

    Returns:
        Matching database record or None
    """
    channel_id = await storage.get_channel_id()

    # Strategy 1: Exact filename match
    async with get_connection(storage.channel_name) as conn:
        cursor = await conn.execute(
            "SELECT * FROM messages WHERE channel_id = ? AND filename = ?",
            (channel_id, filename),
        )
        record = await cursor.fetchone()
        if record:
            logger.debug(f"Matched {filename} by exact filename")
            return dict(record)

    # Strategy 2: Filename contains Telegram ID (e.g., "123_video.mp4" matches message ID 123)
    # Attempt to extract a numerical ID from the filename
    potential_id = None
    try:
        # Look for a sequence of digits at the beginning or after a common separator
        match = re.match(r"^\d+", filename) or re.search(r"[\-_](\d+)", filename)
        if match:
            potential_id = int(
                match.group(1) if match.groups() else match.group(0)
            )  # Use group(1) if a capturing group was used
    except ValueError:
        pass  # Not a valid integer

    if potential_id:
        async with get_connection(storage.channel_name) as conn:
            cursor = await conn.execute(
                "SELECT * FROM messages WHERE channel_id = ? AND telegram_id = ?",
                (channel_id, potential_id),
            )
            record = await cursor.fetchone()
            if record:
                logger.debug(f"Matched {filename} by message ID {potential_id}")
                return dict(record)

    # Strategy 3: Similar file size (within 5% tolerance) and filename similarity
    min_size = int(file_size * 0.95)
    max_size = int(file_size * 1.05)
    base_filename_lower = filename.lower()
    async with get_connection(storage.channel_name) as conn:
        cursor = await conn.execute(
            "SELECT * FROM messages WHERE channel_id = ? AND file_size BETWEEN ? AND ? AND LOWER(filename) LIKE ?",
            (channel_id, min_size, max_size, f"%{base_filename_lower}%"),
        )
        record = await cursor.fetchone()
        if record:
            logger.debug(
                f"Matched {filename} by similar file size and filename similarity"
            )
            return dict(record)

    # Strategy 4: Base filename match (ignoring prefixes/suffixes) - as a fallback if size match fails
    async with get_connection(storage.channel_name) as conn:
        cursor = await conn.execute(
            "SELECT * FROM messages WHERE channel_id = ? AND LOWER(filename) LIKE ?",
            (channel_id, f"%{base_filename_lower}%"),
        )
        record = await cursor.fetchone()
        if record:
            logger.debug(f"Matched {filename} by base filename similarity")
            return dict(record)

    logger.debug(f"No database match found for {filename}")
    return None


async def sync_channel_database_with_filesystem(
    channel_name: str, dry_run: bool = False
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

    logger.info(
        f"Starting database-filesystem sync for channel '{channel_name}' (dry_run={dry_run})"
    )

    try:
        # Get database storage instance
        storage = get_storage(channel_name)

        # Get media directory path
        from .config.paths import get_channel_media_path

        media_dir = get_channel_media_path(channel_name)

        if not media_dir.exists():
            logger.warning(f"Media directory does not exist: {media_dir}")
            return stats

        # Scan filesystem for actual files
        actual_files = []
        for file_path in media_dir.iterdir():
            if file_path.is_file():
                try:
                    file_size = file_path.stat().st_size
                    actual_files.append(
                        {
                            "filename": file_path.name,
                            "full_path": str(file_path),
                            "size": file_size,
                        }
                    )
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {e}")
                    stats["errors"] += 1

        stats["files_on_disk"] = len(actual_files)
        logger.info(f"Found {len(actual_files)} files on disk in {media_dir}")

        # Get ALL database records for matching (not just pending!)
        channel_id = await storage.get_channel_id()
        async with get_connection(storage.channel_name) as conn:
            # First check if we have ANY records at all
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM messages WHERE channel_id = ?",
                (channel_id,),
            )
            total_count = (await cursor.fetchone())[0]

        if total_count == 0:
            logger.warning(
                f"🚨 Database has no records for channel '{storage.channel_name}', but {len(actual_files)} files exist on disk!"
            )
            logger.info(
                "📡 MAINTENANCE AUTO-FIX: Triggering channel enumeration to populate database records..."
            )

            # Return special status to indicate enumeration is needed
            stats["enumeration_needed"] = True
            stats["unmatched_files"] = len(actual_files)
            logger.info(
                f"🔄 Will enumerate {storage.channel_name} channel from Telegram to match existing files"
            )
            return stats
        else:
            # Get ALL database records for analysis
            async with get_connection(storage.channel_name) as conn:
                cursor = await conn.execute(
                    """SELECT id, telegram_id, filename, file_size, download_status
                       FROM messages WHERE channel_id = ?""",
                    (channel_id,),
                )
                all_records = await cursor.fetchall()

            logger.info(
                f"🔍 STATE-AWARE SYNC: Analyzing {len(actual_files)} files against {len(all_records)} database records..."
            )

            # Build lookup for ALL records with their current state
            filename_to_record = {}
            size_to_records = {}

            for record in all_records:
                record_id, telegram_id, filename, file_size, download_status = record
                if filename:
                    filename_to_record[filename] = {
                        "id": record_id,
                        "telegram_id": telegram_id,
                        "filename": filename,
                        "file_size": file_size,
                        "download_status": download_status,
                    }
                if file_size:
                    if file_size not in size_to_records:
                        size_to_records[file_size] = []
                    size_to_records[file_size].append(
                        {
                            "id": record_id,
                            "telegram_id": telegram_id,
                            "filename": filename,
                            "file_size": file_size,
                            "download_status": download_status,
                        }
                    )

            # STATE-AWARE MATCHING: Categorize files into three buckets
            needs_update = []  # Files with matching records that need status update
            already_synced = []  # Files with matching records already completed
            unmatched_files = []  # Files with no matching database records

            for i, file_info in enumerate(actual_files):
                if i % 1000 == 0:  # Progress indicator
                    logger.info(f"📊 Processing file {i + 1}/{len(actual_files)}")

                match = None

                # Strategy 1: Exact filename match (O(1))
                if file_info["filename"] in filename_to_record:
                    match = filename_to_record[file_info["filename"]]
                    logger.debug(
                        f"✅ Exact match: {file_info['filename']} (status: {match['download_status']})"
                    )

                # Strategy 2: File size match (fallback)
                elif file_info["size"] in size_to_records:
                    candidates = size_to_records[file_info["size"]]
                    if len(candidates) == 1:
                        match = candidates[0]
                        logger.debug(
                            f"✅ Size match: {file_info['filename']} -> {match['filename']} (status: {match['download_status']})"
                        )

                # CRITICAL: State-aware categorization
                if match:
                    stats["matches_found"] += 1

                    # Check if record ACTUALLY needs updating
                    if match["download_status"] != "completed":
                        # Record exists but is not completed - this needs updating
                        needs_update.append(
                            {
                                "id": match["id"],
                                "telegram_id": match["telegram_id"],
                                "filename": file_info["filename"],
                                "current_status": match["download_status"],
                            }
                        )
                        logger.debug(
                            f"🔄 NEEDS UPDATE: {file_info['filename']} (status: {match['download_status']} -> completed)"
                        )
                    else:
                        # Record exists and is already completed - no action needed
                        already_synced.append(
                            {"filename": file_info["filename"], "id": match["id"]}
                        )
                        logger.debug(
                            f"✅ ALREADY SYNCED: {file_info['filename']} (status: completed)"
                        )
                else:
                    # No matching record found - this is truly orphaned
                    unmatched_files.append(file_info)
                    logger.debug(
                        f"❓ ORPHANED: {file_info['filename']} (no database record)"
                    )

            # Update statistics with correct counts
            stats["unmatched_files"] = len(unmatched_files)
            stats["already_synced"] = len(already_synced)
            stats["needs_update"] = len(needs_update)

            # Log the categorization results
            logger.info("📊 SYNC ANALYSIS RESULTS:")
            logger.info(f"   🔄 Needs Update: {len(needs_update)} records")
            logger.info(f"   ✅ Already Synced: {len(already_synced)} records")
            logger.info(f"   ❓ Orphaned Files: {len(unmatched_files)} files")

            # ONLY update records that actually need updating
            if needs_update:
                if not dry_run:
                    logger.info(
                        f"🔄 Batch updating {len(needs_update)} records that need status change..."
                    )
                    try:
                        async with get_connection(storage.channel_name) as conn:
                            for update in needs_update:
                                await conn.execute(
                                    "UPDATE messages SET download_status = 'completed', filename = ? WHERE id = ?",
                                    (update["filename"], update["id"]),
                                )
                            await conn.commit()
                            stats["updated_to_completed"] = len(needs_update)
                            logger.info(
                                f"✅ Successfully updated {len(needs_update)} records from {[u['current_status'] for u in needs_update[:3]]}... to completed"
                            )
                    except Exception as e:
                        logger.error(f"Error batch updating records: {e}")
                        stats["errors"] += len(needs_update)
                else:
                    # Dry run - just report what would be updated
                    stats["updated_to_completed"] = len(needs_update)
                    for update in needs_update:
                        logger.info(
                            f"[DRY RUN] Would update message {update['id']} from '{update['current_status']}' to 'completed' (file: {update['filename']})"
                        )
            else:
                logger.info(
                    "🎉 NO UPDATES NEEDED - All matching records are already in sync!"
                )
                stats["updated_to_completed"] = 0

        # Report unmatched files
        if unmatched_files:
            unmatched_files_str = "\n".join(
                [f"  - {file_info['full_path']}" for file_info in unmatched_files[:10]]
            )
            if len(unmatched_files) > 10:
                unmatched_files_str += f"\n  ... and {len(unmatched_files) - 10} more"
            logger.warning(
                f"Found {len(unmatched_files)} files on disk in channel '{channel_name}' with no database match:\n{unmatched_files_str}"
            )

            # 🔧 AUTO-DETECTION & AUTO-FIX: Handle large numbers of orphaned files
            if len(unmatched_files) > 1000:  # Threshold for auto-reconciliation
                logger.info(
                    f"🔧 AUTO-DETECT: Large number of orphaned files ({len(unmatched_files)}) detected - triggering auto-reconciliation..."
                )

                # Attempt to reconcile orphaned files by creating database records
                try:
                    reconciled_count = await reconcile_orphaned_files(
                        channel_name, unmatched_files, storage, dry_run
                    )
                    stats["auto_reconciled"] = reconciled_count
                    if reconciled_count > 0:
                        logger.info(
                            f"✅ AUTO-FIX: Successfully reconciled {reconciled_count} orphaned files"
                        )
                    else:
                        logger.info(
                            "ℹ️  AUTO-FIX: No orphaned files could be automatically reconciled"
                        )
                except Exception as e:
                    logger.error(
                        f"❌ AUTO-FIX FAILED: Could not reconcile orphaned files: {e}"
                    )
                    # Continue with graceful degradation - don't fail the entire operation

    except KeyboardInterrupt:
        logger.info(
            f"Database-filesystem sync interrupted by user for '{channel_name}' - this is normal"
        )
        stats["user_interrupted"] = True
        # Re-raise to allow proper cleanup
        raise
    except Exception as e:
        # Check if this is a user interruption disguised as another exception
        error_str = str(e).lower()
        if any(
            term in error_str
            for term in ["interrupted", "cancelled", "keyboard", "sigint"]
        ):
            logger.info(
                f"Database-filesystem sync interrupted by user for '{channel_name}': {e}"
            )
            stats["user_interrupted"] = True
        else:
            logger.error(f"Error during database-filesystem sync: {e}")
            stats["errors"] += 1

    # Report final statistics
    if stats.get("user_interrupted"):
        logger.info(
            f"Database-filesystem sync interrupted for '{channel_name}' (user requested):"
        )
    else:
        logger.info(f"Database-filesystem sync completed for '{channel_name}':")
    logger.info(f"  Files on disk: {stats['files_on_disk']}")
    logger.info(f"  Database pending: {stats['database_pending']}")
    logger.info(f"  Matches found: {stats['matches_found']}")
    logger.info(f"  Updated to completed: {stats['updated_to_completed']}")
    logger.info(f"  Unmatched files: {stats['unmatched_files']}")
    logger.info(f"  Errors: {stats['errors']}")

    if stats.get("user_interrupted"):
        logger.info("  Status: Gracefully interrupted by user (Ctrl+C)")

    return stats


async def sync_all_channels_databases_with_filesystem(
    dry_run: bool = False,
) -> dict[str, dict[str, int]]:
    """
    Synchronize all channel databases with their respective filesystems.

    Args:
        dry_run: If True, only report what would be changed without making changes

    Returns:
        Dictionary mapping channel names to their sync statistics
    """

    results = {}

    # Find all channel directories
    from .config.paths import get_channels_base_path

    channels_dir = get_channels_base_path()
    if not channels_dir.exists():
        logger.error(f"Channels directory does not exist: {channels_dir}")
        return results

    for channel_dir in channels_dir.iterdir():
        if channel_dir.is_dir():
            channel_name = channel_dir.name
            media_dir = channel_dir / "_media"

            # Only sync channels that have a media directory with files
            if media_dir.exists() and any(media_dir.iterdir()):
                logger.info(f"Syncing channel: {channel_name}")
                results[channel_name] = await sync_channel_database_with_filesystem(
                    channel_name, dry_run
                )
            else:
                logger.debug(
                    f"Skipping channel {channel_name} - no media directory or files"
                )

    # Report overall summary
    total_files = sum(stats["files_on_disk"] for stats in results.values())
    total_pending = sum(stats["database_pending"] for stats in results.values())
    total_updated = sum(stats["updated_to_completed"] for stats in results.values())

    logger.info("Overall sync summary:")
    logger.info(f"  Channels processed: {len(results)}")
    logger.info(f"  Total files on disk: {total_files}")
    logger.info(f"  Total database pending: {total_pending}")
    logger.info(f"  Total updated to completed: {total_updated}")

    return results


async def verify_database_filesystem_consistency(channel_name: str) -> dict[str, int]:
    """
    Verify the consistency between database and filesystem without making changes.

    Args:
        channel_name: Name of the channel to verify

    Returns:
        Dictionary with consistency statistics
    """

    logger.info(
        f"Verifying database-filesystem consistency for channel '{channel_name}'"
    )
    return await sync_channel_database_with_filesystem(channel_name, dry_run=True)


def files_match_by_size(
    file_path: Path, expected_size: int, tolerance: float = 0.02
) -> bool:
    """Check if file size matches within tolerance."""
    try:
        actual_size = file_path.stat().st_size
        if expected_size == 0:
            return actual_size == 0
        return abs(actual_size - expected_size) / expected_size <= tolerance
    except Exception as e:
        logger.debug(f"Could not get file size for {file_path}: {e}")
        return False


async def find_file_for_database_record(record: dict, media_dir: Path) -> Path | None:
    """Try to find actual file for a database record using similar strategies."""

    # Strategy 1: Look for files with telegram_id prefix
    telegram_id = record["telegram_id"]
    for file_path in media_dir.iterdir():
        if file_path.is_file() and file_path.name.startswith(f"{telegram_id}_"):
            if files_match_by_size(file_path, record["file_size"]):
                logger.debug(
                    f"Found file for record {record['id']} using telegram_id prefix: {file_path.name}"
                )
                return file_path

    # Strategy 2: Look for files with similar size and partial name match
    base_name = Path(record["filename"]).stem.lower()
    for file_path in media_dir.iterdir():
        if file_path.is_file() and base_name in file_path.stem.lower():
            if files_match_by_size(file_path, record["file_size"], tolerance=0.05):
                logger.debug(
                    f"Found file for record {record['id']} using name similarity: {file_path.name}"
                )
                return file_path

    logger.debug(
        f"No file found for database record {record['id']} ({record['filename']})"
    )
    return None


async def find_missing_files_from_database(
    channel_name: str, dry_run: bool = False
) -> tuple[dict[str, int], list[dict]]:
    """Find database records that have no corresponding files on disk."""

    stats = {
        "database_completed": 0,
        "files_missing": 0,
        "potential_matches": 0,
        "filename_updates": 0,
        "errors": 0,
    }

    logger.info(
        f"Starting database-to-filesystem verification for channel '{channel_name}' (dry_run={dry_run})"
    )

    try:
        # Get database storage instance
        storage = get_storage(channel_name)

        # Get media directory path
        from .config.paths import get_channel_media_path

        media_dir = get_channel_media_path(channel_name)

        if not media_dir.exists():
            logger.warning(f"Media directory does not exist: {media_dir}")
            return stats, []

        # Get all "completed" records from database
        channel_id = await storage.get_channel_id()
        async with get_connection(storage.channel_name) as conn:
            cursor = await conn.execute(
                "SELECT id, telegram_id, filename, file_size FROM messages "
                "WHERE channel_id = ? AND download_status = 'completed'",
                (channel_id,),
            )
            completed_records = await cursor.fetchall()

        # Convert to list of dicts for easier handling
        completed_records = [dict(record) for record in completed_records]
        stats["database_completed"] = len(completed_records)

        logger.info(f"Found {len(completed_records)} completed records in database")

        # For each completed record, verify file exists
        missing_records = []
        for record in completed_records:
            # Skip records with missing filename
            if not record["filename"]:
                logger.warning(
                    f"Skipping database record {record['id']} with no filename"
                )
                stats["errors"] += 1
                continue

            expected_path = media_dir / record["filename"]

            if not expected_path.exists():
                # Try to find the file with different name
                potential_match = await find_file_for_database_record(record, media_dir)

                if potential_match:
                    stats["potential_matches"] += 1
                    if not dry_run:
                        # Update database with actual filename
                        try:
                            await storage.update_download_status(
                                telegram_id=record["telegram_id"],
                                status="completed",
                                filename=potential_match.name,
                            )
                            stats["filename_updates"] += 1
                            logger.info(
                                f"✅ Updated database record {record['id']} filename from '{record['filename']}' to '{potential_match.name}'"
                            )
                        except Exception as e:
                            logger.error(
                                f"Failed to update filename for record {record['id']}: {e}"
                            )
                            stats["errors"] += 1
                    else:
                        logger.info(
                            f"[DRY RUN] Would update record {record['id']} filename from '{record['filename']}' to '{potential_match.name}'"
                        )
                        stats["filename_updates"] += 1
                else:
                    # True missing file
                    missing_records.append(record)
                    stats["files_missing"] += 1

        # Report missing files
        if missing_records:
            missing_files_str = "\n".join(
                [
                    f"  - ID {record['id']}: {record['filename']} ({record['file_size']} bytes)"
                    for record in missing_records[:10]
                ]
            )
            if len(missing_records) > 10:
                missing_files_str += f"\n  ... and {len(missing_records) - 10} more"
            logger.warning(
                f"Found {len(missing_records)} database records marked as 'completed' but files are missing:\n{missing_files_str}"
            )

    except Exception as e:
        logger.error(f"Error during database-to-filesystem verification: {e}")
        stats["errors"] += 1
        missing_records = []

    # Report statistics
    logger.info(f"Database-to-filesystem verification completed for '{channel_name}':")
    logger.info(f"  Database completed records: {stats['database_completed']}")
    logger.info(f"  Files missing: {stats['files_missing']}")
    logger.info(f"  Potential matches found: {stats['potential_matches']}")
    logger.info(f"  Filename updates: {stats['filename_updates']}")
    logger.info(f"  Errors: {stats['errors']}")

    return stats, missing_records


async def complete_database_filesystem_sync(
    channel_name: str, dry_run: bool = False
) -> dict[str, dict]:
    """Complete bidirectional sync: files→DB and DB→files."""

    logger.info(
        f"Starting complete bidirectional sync for channel '{channel_name}' (dry_run={dry_run})"
    )

    results = {}

    try:
        # Phase 1: Files → Database (existing functionality)
        logger.info("Phase 1: Syncing files to database records...")
        file_stats = await sync_channel_database_with_filesystem(channel_name, dry_run)
        results["file_to_db"] = file_stats

        # Phase 2: Database → Files (new functionality)
        logger.info("Phase 2: Verifying database records have corresponding files...")
        db_stats, missing_records = await find_missing_files_from_database(
            channel_name, dry_run
        )
        results["db_to_file"] = db_stats
        results["missing_records"] = missing_records

        # Summary statistics
        total_files_on_disk = file_stats.get("files_on_disk", 0)
        total_db_completed = db_stats.get("database_completed", 0)
        total_orphaned = file_stats.get("unmatched_files", 0)
        total_missing = db_stats.get("files_missing", 0)
        total_reconciled = file_stats.get("updated_to_completed", 0) + db_stats.get(
            "filename_updates", 0
        )

        results["summary"] = {
            "files_on_disk": total_files_on_disk,
            "database_completed": total_db_completed,
            "orphaned_files": total_orphaned,
            "missing_files": total_missing,
            "reconciled_total": total_reconciled,
        }

        logger.info("Complete bidirectional sync summary:")
        logger.info(f"  Files on disk: {total_files_on_disk}")
        logger.info(f"  Database completed records: {total_db_completed}")
        logger.info(f"  Orphaned files (no DB record): {total_orphaned}")
        logger.info(
            f"  Missing files (DB says completed but file missing): {total_missing}"
        )
        logger.info(f"  Total reconciled: {total_reconciled}")

    except Exception as e:
        logger.error(f"Error during complete bidirectional sync: {e}")
        results["error"] = str(e)

    return results


async def fix_null_filename_records(channel_name: str) -> dict[str, int]:
    """Fix database records marked 'completed' but with null/empty filenames."""

    stats = {
        "null_filename_records": 0,
        "reset_to_pending": 0,
        "errors": 0,
    }

    logger.info(
        f"Checking for invalid 'completed' records with null filenames in '{channel_name}'"
    )

    try:
        # Get database storage instance
        storage = get_storage(channel_name)
        channel_id = await storage.get_channel_id()

        async with get_connection(storage.channel_name) as conn:
            # Count records with null/empty filenames marked as completed
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM messages "
                "WHERE channel_id = ? AND download_status = 'completed' AND (filename IS NULL OR filename = '')",
                (channel_id,),
            )
            count_result = await cursor.fetchone()
            stats["null_filename_records"] = count_result[0]

            logger.info(
                f"Found {stats['null_filename_records']} completed records with null/empty filenames"
            )

            if stats["null_filename_records"] > 0:
                # Reset these records to 'pending' status
                cursor = await conn.execute(
                    "UPDATE messages "
                    "SET download_status = 'pending' "
                    "WHERE channel_id = ? AND download_status = 'completed' AND (filename IS NULL OR filename = '')",
                    (channel_id,),
                )
                stats["reset_to_pending"] = cursor.rowcount
                await conn.commit()

                logger.info(
                    f"✅ Reset {stats['reset_to_pending']} invalid records to 'pending' status"
                )
            else:
                logger.info("✅ No invalid completed records found")

    except Exception as e:
        logger.error(f"Error fixing null filename records: {e}")
        stats["errors"] += 1

    return stats


if __name__ == "__main__":
    # Example usage - can be run as a standalone script
    import sys

    if len(sys.argv) > 1:
        channel_name = sys.argv[1]
        dry_run = "--dry-run" in sys.argv
        bidirectional = "--bidirectional" in sys.argv or "--complete" in sys.argv

        if channel_name == "all":
            import asyncio

            if bidirectional:
                logger.warning(
                    "Bidirectional sync not supported for 'all' channels yet"
                )
            asyncio.run(sync_all_channels_databases_with_filesystem(dry_run=dry_run))
        else:
            import asyncio

            if bidirectional:
                asyncio.run(
                    complete_database_filesystem_sync(channel_name, dry_run=dry_run)
                )
            else:
                asyncio.run(
                    sync_channel_database_with_filesystem(channel_name, dry_run=dry_run)
                )
    else:
        print(
            "Usage: python sync_database.py <channel_name|all> [--dry-run] [--bidirectional]"
        )
        print("Example: python sync_database.py jcexclusive --dry-run")
        print("Example: python sync_database.py jcexclusive --bidirectional --dry-run")
