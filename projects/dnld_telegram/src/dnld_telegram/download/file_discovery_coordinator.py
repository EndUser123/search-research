#!/usr/bin/env python3
"""
File Discovery Coordinator - Beautiful Architecture for Unified File Management

This module provides a central coordination point for all file discovery,
database synchronization, and reverse sync decisions. It eliminates the
architectural disconnect between filesystem scanning, database state, and
sync decisions.

Key Design Principles:
1. Single source of truth for file state
2. Information flows in logical order
3. Decisions made with complete context
4. Clean separation of concerns
5. Elegant error handling and recovery
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FileDiscoveryResult:
    """Complete picture of file state for a channel."""

    channel_name: str
    files_on_disk: list[dict[str, Any]]
    database_matched: list[dict[str, Any]]
    database_unmatched: list[dict[str, Any]]  # In DB but not on disk
    filesystem_unmatched: list[dict[str, Any]]  # On disk but not in DB
    total_discoverable: int  # Total files that could be downloaded
    needs_reverse_sync: bool
    reverse_sync_reason: str

    @property
    def requires_action(self) -> bool:
        """True if any sync action is needed."""
        return self.needs_reverse_sync or len(self.database_unmatched) > 0


class FileDiscoveryCoordinator:
    """
    Elegant coordinator that unifies file discovery, database sync, and reverse sync decisions.

    This replaces the fragmented approach where different components made
    independent decisions about file state without full context.
    """

    def __init__(
        self,
        channel_name: str,
        telegram_id: int | None = None,
        client: Any | None = None,
    ):
        from .config.paths import get_channel_media_path, get_channel_path

        self.channel_name = channel_name
        self.telegram_id = telegram_id
        self.client = client
        self.channel_path = get_channel_path(channel_name)
        self.media_path = get_channel_media_path(channel_name)

    async def discover_complete_file_state(self) -> FileDiscoveryResult:
        """
        Perform comprehensive file discovery with complete context.

        This is the beautiful single entry point that coordinates all file
        discovery activities and returns a complete picture of file state.
        """
        logger.info(f"🔍 Discovering complete file state for '{self.channel_name}'")

        # Ensure client connection is healthy before database operations
        if self.client:
            await self._ensure_client_connected()

        # 1. Scan filesystem first to understand ground truth
        files_on_disk = self._scan_filesystem()
        logger.debug(f"Found {len(files_on_disk)} files on disk")

        # 2. Get database state
        database_files = await self._get_database_files()
        logger.debug(f"Found {len(database_files)} files in database")

        # 3. Perform intelligent matching
        matched, db_unmatched, fs_unmatched = self._match_files(
            files_on_disk, database_files
        )

        # 4. Make reverse sync decision with complete context
        needs_reverse_sync, reason = self._should_reverse_sync(
            fs_unmatched, db_unmatched
        )

        # 5. Calculate total discoverable files (existing + potential)
        total_discoverable = (
            len(files_on_disk) + self._estimate_downloadable_from_telegram()
        )

        result = FileDiscoveryResult(
            channel_name=self.channel_name,
            files_on_disk=files_on_disk,
            database_matched=matched,
            database_unmatched=db_unmatched,
            filesystem_unmatched=fs_unmatched,
            total_discoverable=total_discoverable,
            needs_reverse_sync=needs_reverse_sync,
            reverse_sync_reason=reason,
        )

        self._log_discovery_summary(result)
        return result

    async def coordinate_sync_operations(
        self,
        discovery: FileDiscoveryResult,
        dry_run: bool = False,
        progress: Any | None = None,
    ) -> dict[str, Any]:
        """
        Execute all necessary sync operations in correct order with full context.

        This beautiful orchestration ensures operations happen in logical order
        with each step informed by complete file state knowledge.
        """
        logger.info(f"🎼 Coordinating sync operations for '{self.channel_name}'")

        sync_stats = {
            "reverse_sync_performed": False,
            "reverse_sync_created": 0,
            "database_sync_performed": False,
            "database_updated": 0,
            "total_files_ready": 0,
        }

        # 1. Reverse sync first if needed (creates DB entries for unmatched files)
        if discovery.needs_reverse_sync and not dry_run:
            logger.info(f"🔄 Performing reverse sync: {discovery.reverse_sync_reason}")
            reverse_stats = await self._perform_reverse_sync()
            sync_stats["reverse_sync_performed"] = True
            sync_stats["reverse_sync_created"] = reverse_stats.get("created_entries", 0)

            if sync_stats["reverse_sync_created"] > 0:
                logger.info(
                    f"✨ Reverse sync created {sync_stats['reverse_sync_created']} database entries"
                )

        # 2. Database sync to update status of matched files
        if len(discovery.database_matched) > 0 and not dry_run:
            logger.info(
                f"🔄 Updating database status for {len(discovery.database_matched)} matched files"
            )
            db_stats = await self._perform_database_sync(progress)
            sync_stats["database_sync_performed"] = True
            sync_stats["database_updated"] = db_stats.get("updated_to_completed", 0)

            if sync_stats["database_updated"] > 0:
                logger.info(
                    f"✨ Database sync updated {sync_stats['database_updated']} files to completed"
                )

        # 3. Calculate final ready count
        sync_stats["total_files_ready"] = await self._get_final_download_count()

        logger.info(
            f"🎯 Sync coordination complete: {sync_stats['total_files_ready']} files ready for processing"
        )
        return sync_stats

    def _scan_filesystem(self) -> list[dict[str, Any]]:
        """Scan filesystem and return structured file information."""
        if not self.media_path.exists():
            logger.debug(f"Media directory doesn't exist: {self.media_path}")
            return []

        files = []
        for file_path in self.media_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                # Create relative path safely for cross-platform compatibility
                try:
                    rel_path = file_path.relative_to(Path.cwd())
                except ValueError:
                    # Fallback: create relative path from channel directory
                    rel_path = file_path.relative_to(self.channel_path.parent.parent)

                file_info = {
                    "filename": file_path.name,
                    "full_path": str(rel_path).replace(
                        "\\", "/"
                    ),  # Normalize path separators
                    "size": file_path.stat().st_size,
                    "stem": file_path.stem,
                    "extension": file_path.suffix.lower(),
                }
                files.append(file_info)

        return sorted(files, key=lambda x: x["filename"])

    async def _get_database_files(self) -> list[dict[str, Any]]:
        """Get all files from database for this channel."""
        try:
            from .database.schema import get_connection

            # Isolate database operations from any Telethon client context issues
            logger.debug(f"🔍 Getting database files for {self.channel_name}")

            # Get all messages with downloadable content
            async with get_connection(self.channel_name) as conn:
                cursor = await conn.execute(
                    """
                    SELECT id, filename, file_size, media_type, download_status
                    FROM messages
                    WHERE filename IS NOT NULL AND filename != ''
                    ORDER BY id
                """
                )
                messages = []
                async for row in cursor:
                    filename = row[1] or ""
                    # Create filename stem by removing extension
                    filename_stem = Path(filename).stem if filename else ""

                    messages.append(
                        {
                            "id": row[0],
                            "filename": filename,
                            "filename_stem": filename_stem,
                            "file_size": row[2] or 0,
                            "media_type": row[3] or "",
                            "status": row[4] or "pending",
                        }
                    )
                return messages
        except Exception as e:
            logger.warning(f"  ⚠️ Could not get database files: {e}")
            return []

    def _match_files(
        self, fs_files: list[dict], db_files: list[dict]
    ) -> tuple[list[dict], list[dict], list[dict]]:
        """
        Intelligent file matching between filesystem and database.

        Returns: (matched_pairs, db_unmatched, fs_unmatched)
        """
        matched = []
        fs_unmatched = fs_files.copy()
        db_unmatched = []

        # Create lookup indices for efficient matching
        fs_by_name = {f["filename"]: f for f in fs_files}
        fs_by_stem = {f["stem"]: f for f in fs_files}

        for db_file in db_files:
            db_filename = db_file.get("filename", "")
            if not db_filename:
                db_unmatched.append(db_file)
                continue

            # Try exact filename match first
            if db_filename in fs_by_name:
                matched_fs = fs_by_name[db_filename]
                matched.append(
                    {
                        "filesystem": matched_fs,
                        "database": db_file,
                        "match_type": "exact_filename",
                    }
                )
                if matched_fs in fs_unmatched:
                    fs_unmatched.remove(matched_fs)
            # Try stem match (filename without extension)
            elif db_file.get("filename_stem") in fs_by_stem:
                matched_fs = fs_by_stem[db_file["filename_stem"]]
                matched.append(
                    {
                        "filesystem": matched_fs,
                        "database": db_file,
                        "match_type": "stem_match",
                    }
                )
                if matched_fs in fs_unmatched:
                    fs_unmatched.remove(matched_fs)
            else:
                db_unmatched.append(db_file)

        return matched, db_unmatched, fs_unmatched

    def _should_reverse_sync(
        self, fs_unmatched: list[dict], db_unmatched: list[dict]
    ) -> tuple[bool, str]:
        """
        Make intelligent reverse sync decision with complete context.

        This replaces the fragmented decision making in reverse_sync.py that
        didn't have access to filesystem scan results.
        """
        if len(fs_unmatched) > 0:
            return (
                True,
                f"Found {len(fs_unmatched)} files on disk without database entries",
            )

        # Check metadata-based decisions (existing logic)
        metadata_path = Path(f"channels/{self.channel_name}/enumeration_metadata.json")
        if not metadata_path.exists():
            return True, "First time sync - no metadata exists"

        try:
            with open(metadata_path) as f:
                metadata = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load metadata: {e}")
            return True, "Metadata load failed"

        reverse_sync_info = metadata.get("reverse_sync", {})
        if not reverse_sync_info.get("completed", False):
            return True, "Previous reverse sync was incomplete"

        # If we get here, no reverse sync needed
        return False, "All files accounted for in database"

    def _estimate_downloadable_from_telegram(self) -> int:
        """Estimate how many additional files could be downloaded from Telegram."""
        # This is a placeholder - in full implementation, this would use
        # Telegram API to get approximate message count or use cached metadata
        try:
            metadata_path = Path(
                f"channels/{self.channel_name}/enumeration_metadata.json"
            )
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
                return metadata.get("estimated_downloadable_files", 0)
        except Exception:
            pass
        return 0

    async def _perform_reverse_sync(
        self, progress: Any | None = None
    ) -> dict[str, Any]:
        """Perform reverse sync operation."""
        try:
            from .reverse_sync import sync_channel_database_with_filesystem

            return (
                await sync_channel_database_with_filesystem(
                    self.channel_name, dry_run=False
                )
                or {}
            )
        except Exception as e:
            logger.error(f"Reverse sync failed: {e}")
            return {}

    async def _perform_database_sync(
        self, progress: Any | None = None
    ) -> dict[str, Any]:
        """Perform database sync operation."""
        try:
            from .reverse_sync import sync_channel_database_with_filesystem

            return (
                await sync_channel_database_with_filesystem(
                    self.channel_name, dry_run=False
                )
                or {}
            )
        except Exception as e:
            logger.error(f"Database sync failed: {e}")
            return {}

    async def _get_final_download_count(self) -> int:
        """Get final count of files ready for download processing."""
        try:
            from .storage import get_messages_to_download

            messages = await get_messages_to_download(
                self.channel_name, telegram_id=self.telegram_id
            )
            return len(messages)
        except Exception as e:
            logger.error(f"Could not get final download count: {e}")
            return 0

    def _log_discovery_summary(self, result: FileDiscoveryResult) -> None:
        """Log beautiful summary of discovery results."""
        logger.info(f"📊 File Discovery Summary for '{result.channel_name}':")
        logger.info(f"   📁 Files on disk: {len(result.files_on_disk)}")
        logger.info(f"   ✅ Database matched: {len(result.database_matched)}")
        logger.info(f"   🔄 Filesystem unmatched: {len(result.filesystem_unmatched)}")
        logger.info(f"   📋 Database unmatched: {len(result.database_unmatched)}")
        logger.info(f"   🎯 Total discoverable: {result.total_discoverable}")

        if result.needs_reverse_sync:
            logger.info(f"   🔄 Reverse sync needed: {result.reverse_sync_reason}")
        else:
            logger.info(f"   ✅ No reverse sync needed: {result.reverse_sync_reason}")

    async def _ensure_client_connected(self) -> None:
        """
        Ensure the Telethon client is connected and healthy before database operations.

        This prevents the 'no active connection' error from propagating into
        async database operations.
        """
        if not self.client:
            return

        try:
            # Check if client is connected
            if not self.client.is_connected():
                logger.warning(
                    f"🔌 Client disconnected for {self.channel_name}, reconnecting..."
                )
                await self.client.connect()

            # Verify client is authorized and responsive
            if not await self.client.is_user_authorized():
                raise RuntimeError(f"Client not authorized for {self.channel_name}")

            # Test client responsiveness with a lightweight operation
            await self.client.get_me()
            logger.debug(f"✅ Client connection verified for {self.channel_name}")

        except Exception as e:
            logger.error(
                f"❌ Client connection verification failed for {self.channel_name}: {e}"
            )
            # Don't raise - allow database operations to continue
            # The error will be handled appropriately in the calling context
