"""
Migration script for dnld_telegram - JSON to SQLite conversion

This script migrates existing JSON data files to the new SQLite database structure.
It preserves all existing data and supports both full migration and incremental updates.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from .schema import ensure_channel_exists
from .storage import DatabaseStorage


class DataMigrator:
    """Handles migration from JSON files to SQLite database."""

    def __init__(self, base_path: str = "channels"):
        self.base_path = Path(base_path)

    def find_channels_to_migrate(self) -> list[str]:
        """Find all channels with JSON data files."""
        channels: list[str] = []

        if not self.base_path.exists():
            logger.warning(f"Channels directory '{self.base_path}' does not exist")
            return channels

        for channel_dir in self.base_path.iterdir():
            if channel_dir.is_dir():
                # Check for JSON files
                enumerated_files = channel_dir / "enumerated_files.json"
                downloaded_files = channel_dir / "downloaded_files.json"
                metadata_files = channel_dir / "enumeration_metadata.json"

                if any(
                    f.exists()
                    for f in [enumerated_files, downloaded_files, metadata_files]
                ):
                    channels.append(channel_dir.name)
                    logger.info(f"Found channel with JSON data: {channel_dir.name}")

        return channels

    def load_json_file(self, file_path: Path) -> dict[str, Any]:
        """Safely load a JSON file."""
        if not file_path.exists():
            return {}

        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load JSON file {file_path}: {e}")
            return {}

    def extract_telegram_channel_id(
        self, enumerated_data: dict[str, Any]
    ) -> int | None:
        """Extract Telegram channel ID from enumerated data or metadata."""
        # Try to extract from any message data
        for msg_data in enumerated_data.values():
            if isinstance(msg_data, dict) and "channel_id" in msg_data:
                return int(msg_data["channel_id"])

        # If not found, we'll need to use a placeholder or ask the user
        return None

    def migrate_enumerated_files(
        self, channel_name: str, storage: DatabaseStorage
    ) -> int:
        """Migrate enumerated_files.json to database."""
        json_path = self.base_path / channel_name / "enumerated_files.json"
        enumerated_data = self.load_json_file(json_path)

        if not enumerated_data:
            logger.info(f"No enumerated files data for channel '{channel_name}'")
            return 0

        # Extract telegram channel ID (this might need manual intervention)
        telegram_channel_id = self.extract_telegram_channel_id(enumerated_data)
        if telegram_channel_id is None:
            # Use a placeholder - this should be updated with real data
            telegram_channel_id = int(
                hash(channel_name) % 1000000
            )  # Generate consistent ID
            logger.warning(
                f"Could not extract telegram_channel_id for '{channel_name}', using placeholder: {telegram_channel_id}"
            )

        # Save to database
        try:
            import asyncio

            asyncio.run(
                storage.save_enumerated_messages(enumerated_data, telegram_channel_id)
            )
            logger.info(
                f"Migrated {len(enumerated_data)} enumerated messages for channel '{channel_name}'"
            )
            return len(enumerated_data)
        except Exception as e:
            logger.error(
                f"Failed to migrate enumerated files for '{channel_name}': {e}"
            )
            return 0

    def migrate_downloaded_files(
        self, channel_name: str, storage: DatabaseStorage
    ) -> int:
        """Migrate downloaded_files.json to database."""
        json_path = self.base_path / channel_name / "downloaded_files.json"
        downloaded_data = self.load_json_file(json_path)

        if not downloaded_data:
            logger.info(f"No downloaded files data for channel '{channel_name}'")
            return 0

        try:
            import asyncio

            asyncio.run(storage.save_downloaded_files(downloaded_data))
            logger.info(
                f"Migrated {len(downloaded_data)} downloaded file records for channel '{channel_name}'"
            )
            return len(downloaded_data)
        except Exception as e:
            logger.error(
                f"Failed to migrate downloaded files for '{channel_name}': {e}"
            )
            return 0

    def migrate_enumeration_metadata(
        self, channel_name: str, storage: DatabaseStorage
    ) -> int:
        """Migrate enumeration_metadata.json to database."""
        json_path = self.base_path / channel_name / "enumeration_metadata.json"
        metadata = self.load_json_file(json_path)

        if not metadata:
            logger.info(f"No enumeration metadata for channel '{channel_name}'")
            return 0

        try:
            import asyncio

            asyncio.run(storage.save_enumeration_metadata(metadata))
            logger.info(f"Migrated enumeration metadata for channel '{channel_name}'")
            return 1
        except Exception as e:
            logger.error(
                f"Failed to migrate enumeration metadata for '{channel_name}': {e}"
            )
            return 0

    def migrate_channel(
        self, channel_name: str, backup_json: bool = True
    ) -> dict[str, int]:
        """Migrate all data for a specific channel."""
        logger.info(f"Starting migration for channel: {channel_name}")

        # Initialize database and storage
        try:
            storage = DatabaseStorage(channel_name)

            # Get telegram channel ID from enumerated files if possible
            json_path = self.base_path / channel_name / "enumerated_files.json"
            enumerated_data = self.load_json_file(json_path)
            telegram_channel_id = self.extract_telegram_channel_id(enumerated_data)

            if telegram_channel_id is None:
                telegram_channel_id = int(hash(channel_name) % 1000000)
                logger.warning(
                    f"Using placeholder telegram_channel_id: {telegram_channel_id}"
                )

            # Ensure channel exists in database
            ensure_channel_exists(
                channel_name, telegram_channel_id, f"Migrated channel: {channel_name}"
            )

            # Perform migrations
            results = {
                "enumerated_files": self.migrate_enumerated_files(
                    channel_name, storage
                ),
                "downloaded_files": self.migrate_downloaded_files(
                    channel_name, storage
                ),
                "metadata": self.migrate_enumeration_metadata(channel_name, storage),
            }

            # Create backup if requested
            if backup_json:
                self.backup_json_files(channel_name)

            logger.info(f"Migration completed for channel '{channel_name}': {results}")
            return results

        except Exception as e:
            logger.error(f"Migration failed for channel '{channel_name}': {e}")
            return {"error": str(e)}

    def backup_json_files(self, channel_name: str) -> None:
        """Create backup copies of JSON files before migration."""
        channel_dir = self.base_path / channel_name
        backup_dir = channel_dir / "json_backup"
        backup_dir.mkdir(exist_ok=True)

        json_files = [
            "enumerated_files.json",
            "downloaded_files.json",
            "enumeration_metadata.json",
        ]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for json_file in json_files:
            source = channel_dir / json_file
            if source.exists():
                backup_name = f"{json_file}.{timestamp}.bak"
                backup_path = backup_dir / backup_name

                try:
                    import shutil

                    shutil.copy2(source, backup_path)
                    logger.info(f"Backed up {json_file} to {backup_path}")
                except Exception as e:
                    logger.error(f"Failed to backup {json_file}: {e}")

    def migrate_all_channels(self, backup_json: bool = True) -> dict[str, Any]:
        """Migrate all channels with JSON data."""
        channels = self.find_channels_to_migrate()

        if not channels:
            logger.info("No channels found with JSON data to migrate")
            return {"migrated_channels": 0, "results": {}}

        logger.info(f"Found {len(channels)} channels to migrate: {', '.join(channels)}")

        results = {}
        successful_migrations = 0

        for channel_name in channels:
            try:
                channel_results = self.migrate_channel(channel_name, backup_json)
                results[channel_name] = channel_results

                if "error" not in channel_results:
                    successful_migrations += 1

            except Exception as e:
                logger.error(f"Failed to migrate channel '{channel_name}': {e}")
                results[channel_name] = {"error": str(e)}

        summary = {
            "migrated_channels": successful_migrations,
            "total_channels": len(channels),
            "results": results,
        }

        logger.info(
            f"Migration summary: {successful_migrations}/{len(channels)} channels migrated successfully"
        )
        return summary

    def verify_migration(self, channel_name: str) -> dict[str, Any]:
        """Verify that migration was successful by comparing counts."""
        try:
            storage = DatabaseStorage(channel_name)
            db_stats = storage.get_channel_statistics()

            # Load JSON counts
            json_enumerated = self.load_json_file(
                self.base_path / channel_name / "enumerated_files.json"
            )
            json_downloaded = self.load_json_file(
                self.base_path / channel_name / "downloaded_files.json"
            )
            json_metadata = self.load_json_file(
                self.base_path / channel_name / "enumeration_metadata.json"
            )

            verification = {
                "channel_name": channel_name,
                "database_stats": db_stats,
                "json_counts": {
                    "enumerated_files": len(json_enumerated),
                    "downloaded_files": len(json_downloaded),
                    "metadata_entries": len(json_metadata),
                },
                "matches": {
                    "enumerated_files": db_stats.get("media_messages", 0)
                    == len(json_enumerated),
                    "downloaded_files": db_stats.get("downloaded", 0)
                    == len(json_downloaded),
                },
            }

            return verification

        except Exception as e:
            logger.error(f"Verification failed for channel '{channel_name}': {e}")
            return {"error": str(e)}


def main():
    """Main migration function - can be run standalone."""
    logger.info("Starting JSON to SQLite migration")

    migrator = DataMigrator()

    # Find and migrate all channels
    results = migrator.migrate_all_channels(backup_json=True)

    logger.info(
        f"Migration completed: {results['migrated_channels']}/{results['total_channels']} channels"
    )

    # Verify migrations
    for channel_name in results["results"].keys():
        if "error" not in results["results"][channel_name]:
            verification = migrator.verify_migration(channel_name)
            logger.info(
                f"Verification for {channel_name}: {verification.get('matches', {})}"
            )


if __name__ == "__main__":
    main()
