from dataclasses import field
from datetime import datetime
from pathlib import Path
import asyncio
import json
import logging
import os
import re
import statistics
import sys

from pydantic import BaseModel, ValidationError

import shutil
import sqlite3
import structlog




"""
CKS Migration to 2025 Python Standards

Migration script to upgrade existing Cognitive Knowledge System installations
to 2025 Python development standards.

Features:
- Automatic database schema updates
- Data validation and cleanup
- Configuration migration
- Backup creation
- Rollback capability
- Comprehensive logging and audit trail

Constitutional Requirements:
- Solo developer optimization (clear progress, easy rollback)
- Evidence-based operations (comprehensive logging, validation)
- Force multiplier integration (performance optimization)
- No enterprise bloat (direct script, minimal dependencies)
"""



# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class MigrationConfig(BaseModel):
    """Configuration for migration process."""

    source_db_path: str
    target_db_path: str
    backup_dir: str = "backups"
    enable_fts: bool = True
    dry_run: bool = False
    validate_data: bool = True
    create_backup: bool = True


class LegacyEntry(BaseModel):
    """Model for legacy knowledge entries."""

    id: int | None
    timestamp: str
    category: str
    title: str
    content: str
    tags: str


class CKSMigrator:
    """
    Migrates CKS installations to 2025 standards.

    Handles database schema updates, data validation,
    configuration migration, and maintains audit trails.
    """

    def __init__(self, config: MigrationConfig) -> None:
        self.config = config
        self.backup_path = None
        self.migration_log = []

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logger.bind(
            component="CKSMigrator",
            source_db=config.source_db_path,
            target_db=config.target_db_path,
            dry_run=config.dry_run,
        )

    async def migrate(self) -> bool:
        """
        Execute complete migration process.

        Returns:
            True if migration successful, False otherwise
        """
        try:
            self.logger.info(
                "Starting CKS migration to 2025 standards",
                config=self.config.model_dump(),
            )

            # Step 1: Pre-migration checks
            await self._pre_migration_checks()

            # Step 2: Create backup
            if self.config.create_backup:
                await self._create_backup()

            # Step 3: Migrate database schema
            await self._migrate_schema()

            # Step 4: Migrate data with validation
            await self._migrate_data()

            # Step 5: Post-migration validation
            await self._post_migration_validation()

            # Step 6: Create migration report
            await self._create_migration_report()

            self.logger.info("CKS migration completed successfully")
            return True

        except Exception as e:
            self.logger.error("Migration failed", error=str(e))
            await self._rollback()
            return False

    async def _pre_migration_checks(self) -> None:
        """Perform pre-migration validation and checks."""
        self.logger.info("Performing pre-migration checks")

        source_path = Path(self.config.source_db_path)
        target_path = Path(self.config.target_db_path)

        # Check source database exists
        if not source_path.exists():
            raise FileNotFoundError(f"Source database not found: {source_path}")

        # Check target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Check source database is readable
        try:
            with sqlite3.connect(self.config.source_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                self.logger.info("Source database tables", tables=tables)
        except sqlite3.Error as e:
            raise RuntimeError(f"Cannot read source database: {e}")

        # Check if source has legacy schema
        await self._check_legacy_schema()

    async def _check_legacy_schema(self) -> None:
        """Check if source database uses legacy schema."""
        with sqlite3.connect(self.config.source_db_path) as conn:
            cursor = conn.cursor()

            # Check for legacy knowledge table structure
            cursor.execute(
                """
                SELECT sql FROM sqlite_master
                WHERE type='table' AND name='knowledge'
            """
            )
            result = cursor.fetchone()

            if result:
                create_sql = result[0].lower()
                has_legacy_fields = all(
                    field in create_sql
                    for field in [
                        "id",
                        "timestamp",
                        "category",
                        "title",
                        "content",
                        "tags",
                    ]
                )

                if has_legacy_fields:
                    self.logger.info("Legacy schema detected", compatible=True)
                else:
                    self.logger.warning("Unknown schema detected", compatible=False)
            else:
                # No knowledge table - will create new one
                self.logger.info("No existing knowledge table found")

    async def _create_backup(self) -> None:
        """Create backup of source database."""
        self.logger.info("Creating database backup")

        backup_dir = Path(self.config.backup_dir)
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"cks_backup_{timestamp}.db"
        backup_path = backup_dir / backup_name

        # Copy database file
        shutil.copy2(self.config.source_db_path, backup_path)
        self.backup_path = backup_path

        self.logger.info("Backup created", backup_path=str(backup_path))

    async def _migrate_schema(self) -> None:
        """Migrate database schema to 2025 standards."""
        self.logger.info("Migrating database schema")

        if self.config.dry_run:
            self.logger.info("DRY RUN: Would migrate schema")
            return

        # Create new database with modern schema
        with sqlite3.connect(self.config.target_db_path) as target_conn:
            # Enable modern SQLite features
            target_conn.execute("PRAGMA foreign_keys = ON")
            target_conn.execute("PRAGMA journal_mode = WAL")
            target_conn.execute("PRAGMA synchronous = NORMAL")
            target_conn.execute("PRAGMA cache_size = 10000")

            # Create modern knowledge table
            target_conn.execute(
                """
                CREATE TABLE knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes
            target_conn.execute("CREATE INDEX idx_category ON knowledge(category)")
            target_conn.execute("CREATE INDEX idx_timestamp ON knowledge(timestamp)")
            target_conn.execute("CREATE INDEX idx_title ON knowledge(title)")

            # Enable FTS if configured
            if self.config.enable_fts:
                target_conn.execute(
                    """
                    CREATE VIRTUAL TABLE knowledge_fts USING fts5(
                        title,
                        content,
                        tags,
                        content='knowledge',
                        content_rowid='id'
                    )
                """
                )

                # Create FTS triggers
                target_conn.execute(
                    """
                    CREATE TRIGGER knowledge_fts_insert
                    AFTER INSERT ON knowledge
                    BEGIN
                        INSERT INTO knowledge_fts(rowid, title, content, tags)
                        VALUES (new.id, new.title, new.content, new.tags);
                    END
                """
                )

                target_conn.execute(
                    """
                    CREATE TRIGGER knowledge_fts_update
                    AFTER UPDATE ON knowledge
                    BEGIN
                        UPDATE knowledge_fts
                        SET title = new.title, content = new.content, tags = new.tags
                        WHERE rowid = new.id;
                    END
                """
                )

                target_conn.execute(
                    """
                    CREATE TRIGGER knowledge_fts_delete
                    AFTER DELETE ON knowledge
                    BEGIN
                        DELETE FROM knowledge_fts WHERE rowid = old.id;
                    END
                """
                )

            target_conn.commit()

        self.logger.info(
            "Schema migration completed", fts_enabled=self.config.enable_fts
        )

    async def _migrate_data(self) -> None:
        """Migrate data from source to target database with validation."""
        self.logger.info("Migrating data with validation")

        # Check if source has data to migrate
        try:
            with sqlite3.connect(self.config.source_db_path) as source_conn:
                cursor = source_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM knowledge")
                count = cursor.fetchone()[0]
                self.logger.info("Found entries to migrate", count=count)

                if count == 0:
                    self.logger.info("No data to migrate")
                    return

                # Read all data from source
                cursor.execute(
                    """
                    SELECT id, timestamp, category, title, content, tags
                    FROM knowledge
                    ORDER BY id
                """
                )

                rows = cursor.fetchall()
                self.logger.info("Read entries from source", total_rows=len(rows))

        except sqlite3.Error as e:
            self.logger.warning("No existing data found", error=str(e))
            return

        if self.config.dry_run:
            self.logger.info("DRY RUN: Would migrate entries", count=len(rows))
            return

        # Validate and migrate data
        migrated_count = 0
        validation_errors = []

        with sqlite3.connect(self.config.target_db_path) as target_conn:
            target_conn.execute("PRAGMA foreign_keys = ON")

            for row in rows:
                try:
                    # Create legacy entry model for validation
                    legacy_entry = LegacyEntry(
                        id=row[0],
                        timestamp=row[1],
                        category=row[2],
                        title=row[3],
                        content=row[4],
                        tags=row[5],
                    )

                    # Validate data quality
                    if self.config.validate_data:
                        await self._validate_entry(legacy_entry)

                    # Insert into target database
                    target_conn.execute(
                        """
                        INSERT INTO knowledge (timestamp, category, title, content, tags)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            legacy_entry.timestamp,
                            legacy_entry.category,
                            legacy_entry.title,
                            legacy_entry.content,
                            legacy_entry.tags,
                        ),
                    )

                    migrated_count += 1

                    # Log progress every 100 entries
                    if migrated_count % 100 == 0:
                        self.logger.info(
                            "Migration progress",
                            migrated=migrated_count,
                            total=len(rows),
                        )

                except ValidationError as e:
                    validation_errors.append(
                        {"id": row[0], "title": row[3], "error": str(e)}
                    )
                    self.logger.warning(
                        "Entry validation failed", id=row[0], title=row[3], error=str(e)
                    )

                except Exception as e:
                    self.logger.error("Entry migration failed", id=row[0], error=str(e))
                    raise

            target_conn.commit()

        self.logger.info(
            "Data migration completed",
            migrated=migrated_count,
            total=len(rows),
            validation_errors=len(validation_errors),
        )

        if validation_errors:
            self.logger.warning(
                "Some entries failed validation", errors=validation_errors
            )

    async def _validate_entry(self, entry: LegacyEntry) -> None:
        """Validate individual entry data quality."""
        # Check required fields
        if not entry.category.strip():
            raise ValueError("Category cannot be empty")
        if not entry.title.strip():
            raise ValueError("Title cannot be empty")
        if not entry.content.strip():
            raise ValueError("Content cannot be empty")

        # Validate timestamp format
        try:
            datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
        except ValueError:
            # Invalid timestamp, will use current time
            entry.timestamp = datetime.utcnow().isoformat()

        # Normalize tags
        if entry.tags:
            tags = [tag.strip() for tag in entry.tags.split(",") if tag.strip()]
            entry.tags = ",".join(tags)

    async def _post_migration_validation(self) -> None:
        """Validate migrated data and schema."""
        self.logger.info("Performing post-migration validation")

        if self.config.dry_run:
            self.logger.info("DRY RUN: Would validate migration")
            return

        with sqlite3.connect(self.config.target_db_path) as conn:
            cursor = conn.cursor()

            # Check table structure
            cursor.execute(
                """
                SELECT name FROM sqlite_master WHERE type='table'
            """
            )
            tables = [row[0] for row in cursor.fetchall()]
            expected_tables = ["knowledge"]
            if self.config.enable_fts:
                expected_tables.append("knowledge_fts")

            for table in expected_tables:
                if table not in tables:
                    raise ValueError(f"Expected table {table} not found")

            # Check data integrity
            cursor.execute("SELECT COUNT(*) FROM knowledge")
            entry_count = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*) FROM knowledge
                WHERE category IS NOT NULL AND category != ''
                AND title IS NOT NULL AND title != ''
                AND content IS NOT NULL AND content != ''
            """
            )
            valid_count = cursor.fetchone()[0]

            self.logger.info(
                "Data validation completed",
                total_entries=entry_count,
                valid_entries=valid_count,
                invalid_entries=entry_count - valid_count,
            )

            # Test FTS if enabled
            if self.config.enable_fts:
                cursor.execute("SELECT COUNT(*) FROM knowledge_fts")
                fts_count = cursor.fetchone()[0]

                if fts_count != entry_count:
                    self.logger.warning(
                        "FTS count mismatch",
                        fts_entries=fts_count,
                        total_entries=entry_count,
                    )

    async def _create_migration_report(self) -> None:
        """Create comprehensive migration report."""
        self.logger.info("Creating migration report")

        report = {
            "migration_timestamp": datetime.utcnow().isoformat(),
            "source_database": self.config.source_db_path,
            "target_database": self.config.target_db_path,
            "backup_location": str(self.backup_path) if self.backup_path else None,
            "configuration": self.config.model_dump(),
            "migration_log": self.migration_log,
        }

        # Add database statistics
        try:
            with sqlite3.connect(self.config.target_db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM knowledge")
                total_entries = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT category, COUNT(*) FROM knowledge GROUP BY category
                """
                )
                category_stats = dict(cursor.fetchall())

                report["statistics"] = {
                    "total_entries": total_entries,
                    "categories": category_stats,
                    "fts_enabled": self.config.enable_fts,
                }

        except Exception as e:
            report["statistics"] = {"error": str(e)}

        # Save report
        report_path = (
            Path(self.config.target_db_path).parent / "migration_report_2025.json"
        )
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info("Migration report created", report_path=str(report_path))

    async def _rollback(self) -> None:
        """Rollback migration if possible."""
        self.logger.error("Initiating migration rollback")

        if self.backup_path and self.backup_path.exists():
            try:
                # Restore from backup
                shutil.copy2(self.backup_path, self.config.target_db_path)
                self.logger.info("Rollback completed", backup=str(self.backup_path))
            except Exception as e:
                self.logger.error("Rollback failed", error=str(e))
        else:
            self.logger.warning("No backup available for rollback")


async def main() -> int:
    """Main migration CLI interface."""
    if len(sys.argv) < 3:
        print("Usage: python migrate_to_2025.py <source_db> <target_db> [options]")
        print("\nOptions:")
        print("  --dry-run              Show what would be migrated")
        print("  --no-backup            Skip backup creation")
        print("  --disable-fts          Disable full-text search")
        print("  --no-validation        Skip data validation")
        print("\nExample:")
        print("  python migrate_to_2025.py data/knowledge.db data/knowledge_2025.db")
        return 1

    source_db = sys.argv[1]
    target_db = sys.argv[2]

    # Parse options
    dry_run = "--dry-run" in sys.argv
    no_backup = "--no-backup" in sys.argv
    disable_fts = "--disable-fts" in sys.argv
    no_validation = "--no-validation" in sys.argv

    config = MigrationConfig(
        source_db_path=source_db,
        target_db_path=target_db,
        dry_run=dry_run,
        create_backup=not no_backup,
        enable_fts=not disable_fts,
        validate_data=not no_validation,
    )

    print("CKS Migration to 2025 Python Standards")
    print(f"Source: {source_db}")
    print(f"Target: {target_db}")
    print(
        f"Configuration: {config.model_dump(exclude={'source_db_path', 'target_db_path'})}"
    )

    if dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***")

    # Execute migration
    migrator = CKSMigrator(config)
    success = await migrator.migrate()

    if success:
        print("\n✅ Migration completed successfully!")
        if not dry_run:
            print(f"✨ New database: {target_db}")
        print("📊 Migration report: migration_report_2025.json")
        return 0
    else:
        print("\n❌ Migration failed!")
        print("🔄 Rollback attempted if backup was available")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
