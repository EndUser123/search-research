"""
Database Migration for TaskMaster PRD Integration

Migration ID: 002
Author: Claude Code
Date: 2025-12-25

Creates PRD-related tables and columns for traceability:
- prd_requirements table (FR-XXX, NF-XXX requirements)
- success_metrics table (tracking PRD completion)
- PRD traceability columns in tasks table
"""

import logging
import sqlite3

from migration_base import TaskMasterMigration

logger = logging.getLogger(__name__)


class PRDIntegrationMigration(TaskMasterMigration):
    """Migration for PRD integration tables and columns."""

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.migration_version = "002"
        self.migration_name = "add_prd_integration"

    def create_prd_tables(self):
        """Create PRD-related tables."""
        logger.info("Creating PRD integration tables...")

        # prd_requirements table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS prd_requirements (
                id TEXT PRIMARY KEY,
                prd_name TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT,
                description TEXT,
                acceptance_criteria TEXT,
                success_metrics TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # success_metrics table (for tracking PRD completion)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS success_metrics (
                id TEXT PRIMARY KEY,
                prd_requirement_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                target_value REAL,
                current_value REAL DEFAULT 0.0,
                unit TEXT,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (prd_requirement_id) REFERENCES prd_requirements(id) ON DELETE CASCADE
            )
        """)

        self.conn.commit()
        logger.info("Created PRD tables")

    def add_prd_columns_to_tasks(self):
        """Add PRD traceability columns to tasks table."""
        logger.info("Adding PRD columns to tasks table...")

        prd_columns = [
            "ALTER TABLE tasks ADD COLUMN source TEXT",
            "ALTER TABLE tasks ADD COLUMN source_id TEXT",
            "ALTER TABLE tasks ADD COLUMN prd_requirement_id TEXT",
        ]

        for column_sql in prd_columns:
            try:
                self.conn.execute(column_sql)
                logger.info(f"Added column: {column_sql}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    logger.warning(f"Column already exists: {column_sql}")
                else:
                    raise e

        self.conn.commit()
        logger.info("Added PRD traceability columns")

    def create_prd_indexes(self):
        """Create indexes for PRD queries."""
        logger.info("Creating PRD indexes...")

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_prd_requirements_name ON prd_requirements(prd_name)",
            "CREATE INDEX IF NOT EXISTS idx_prd_requirements_category ON prd_requirements(category)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_prd_requirement_id ON tasks(prd_requirement_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_source ON tasks(source)",
            "CREATE INDEX IF NOT EXISTS idx_success_metrics_prd_id ON success_metrics(prd_requirement_id)",
            "CREATE INDEX IF NOT EXISTS idx_success_metrics_status ON success_metrics(status)",
        ]

        for index_sql in indexes:
            try:
                self.conn.execute(index_sql)
            except sqlite3.OperationalError as e:
                logger.warning(f"Index creation issue: {e}")

        self.conn.commit()
        logger.info("Created PRD indexes")

    def create_prd_triggers(self):
        """Create triggers for PRD data consistency."""
        logger.info("Creating PRD triggers...")

        # Update prd_requirements.updated_at on change
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_prd_requirement_timestamp
            AFTER UPDATE ON prd_requirements
            FOR EACH ROW
            BEGIN
                UPDATE prd_requirements
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END
        """)

        logger.info("Created PRD triggers")

    def validate_prd_migration(self) -> tuple[bool, list[str]]:
        """Validate PRD migration.

        Returns:
            Tuple of (is_valid, list of errors)
        """
        logger.info("Validating PRD migration...")

        validation_errors = []

        # Check tables exist
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        prd_tables = {"prd_requirements", "success_metrics"}
        missing_tables = prd_tables - existing_tables
        if missing_tables:
            validation_errors.append(f"Missing PRD tables: {missing_tables}")

        # Check columns exist in tasks table
        cursor.execute("PRAGMA table_info(tasks)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        prd_columns = {"source", "source_id", "prd_requirement_id"}
        missing_columns = prd_columns - existing_columns
        if missing_columns:
            validation_errors.append(f"Missing columns in tasks: {missing_columns}")

        success = len(validation_errors) == 0
        if success:
            logger.info("PRD migration validation successful")
        else:
            logger.error(f"PRD migration validation failed: {validation_errors}")

        return success, validation_errors

    def execute_migration(self) -> tuple[bool, str]:
        """Execute the complete PRD migration.

        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info(f"Starting PRD migration {self.migration_version}")

            # Connect to database first (needed for check_migration_applied)
            self.connect()

            # Create migration tracking table (needed for check_migration_applied)
            self.create_migration_table()

            # Check if already applied
            if self.check_migration_applied():
                logger.warning("Migration already applied")
                return True, "Migration already applied"

            # Close and reopen to create backup (avoid locking issues)
            self.close()
            backup_path = self.backup_database()
            self.connect()

            # Execute migration steps
            self.create_prd_tables()
            self.add_prd_columns_to_tasks()
            self.create_prd_indexes()
            self.create_prd_triggers()

            # Validate migration
            success, errors = self.validate_prd_migration()
            if not success:
                raise Exception(f"Migration validation failed: {errors}")

            # Record migration (inherited from parent)
            self.record_migration(backup_path)

            logger.info(f"PRD migration {self.migration_version} completed successfully")
            return True, f"PRD migration completed successfully. Backup at: {backup_path}"

        except Exception as e:
            logger.error(f"PRD migration failed: {e}")
            return False, f"PRD migration failed: {str(e)}"

        finally:
            self.close()


def main():
    """Main execution function."""
    db_path = r"P:\.speckit\taskmaster\tasks.db"

    migration = PRDIntegrationMigration(db_path)

    # Execute migration
    success, message = migration.execute_migration()

    if success:
        print(f"[SUCCESS] {message}")
    else:
        print(f"[ERROR] {message}")

        # Offer rollback (inherited from parent)
        response = input("Would you like to rollback? (y/n): ").lower().strip()
        if response == "y":
            rollback_success, rollback_message = migration.rollback_migration()
            if rollback_success:
                print(f"[SUCCESS] {rollback_message}")
            else:
                print(f"[ERROR] {rollback_message}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
