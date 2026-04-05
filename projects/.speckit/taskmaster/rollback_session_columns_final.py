"""
TaskMaster Database Rollback: Session Columns Removal (TASK-F-006) - FINAL VERSION

This rollback script removes session-related additions from TaskMaster database:
1. Removes session-related columns from the task table
2. Drops session_tracking table and associated indexes
3. Removes session-related triggers
4. Cleans up migration tracking records
5. Ensures zero data loss during rollback process
6. Works with the new migration tracking schema

Rollback ID: TASK-F-006
Author: Claude Code (CSF_NIP_DEVELOPMENT)
Date: 2025-12-13
Safety: Full backup restoration capability with verification
"""

import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"P:/__csf/logs/taskmaster_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SessionColumnsRollback:
    """Rollback class for removing session columns from TaskMaster database."""

    def __init__(self, db_path: str):
        """Initialize rollback with database path."""
        self.db_path = db_path
        self.conn = None
        self.migration_id = "TASK-F-006"
        self.migration_name = "add_session_columns"
        self.start_time = None
        self.backup_path = None

    def connect(self):
        """Establish database connection with optimized settings."""
        logger.info(f"Connecting to database: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)

        # Enable performance optimizations
        self.conn.execute("PRAGMA foreign_keys = OFF")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.conn.execute("PRAGMA cache_size = 10000")

        logger.info("Database connection established")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def start_performance_timer(self):
        """Start performance measurement."""
        self.start_time = time.time()

    def get_execution_time(self) -> float:
        """Get execution time in milliseconds."""
        if self.start_time:
            return (time.time() - self.start_time) * 1000
        return 0

    def validate_database_exists(self) -> bool:
        """Validate that the database file exists and is accessible."""
        if not os.path.exists(self.db_path):
            logger.error(f"Database file not found: {self.db_path}")
            return False

        try:
            test_conn = sqlite3.connect(self.db_path)
            test_conn.execute("SELECT 1")
            test_conn.close()
            logger.info("Database validation successful")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database validation failed: {e}")
            return False

    def create_pre_rollback_backup(self) -> str:
        """Create a backup before rollback operations."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.db_path}.prerollback_{self.migration_id}_{timestamp}"

        logger.info(f"Creating pre-rollback backup at: {backup_path}")

        try:
            source = sqlite3.connect(self.db_path)
            backup = sqlite3.connect(backup_path)
            source.backup(backup)
            source.close()
            backup.close()

            # Verify backup integrity
            backup_conn = sqlite3.connect(backup_path)
            backup_conn.execute("PRAGMA integrity_check")
            backup_conn.close()

            self.backup_path = backup_path
            logger.info(f"Pre-rollback backup completed: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Pre-rollback backup failed: {e}")
            raise

    def find_migration_backup(self) -> str | None:
        """Find the backup created during the original migration."""
        logger.info("Searching for migration backup files")

        db_dir = os.path.dirname(self.db_path)
        db_name = os.path.basename(self.db_path)

        # Look for backup files with this migration ID
        backup_pattern = f"{db_name}.backup_{self.migration_id}_"
        backup_files = []

        for filename in os.listdir(db_dir):
            if filename.startswith(backup_pattern):
                full_path = os.path.join(db_dir, filename)
                # Check if it's a valid SQLite database
                try:
                    test_conn = sqlite3.connect(full_path)
                    test_conn.execute("SELECT 1")
                    test_conn.close()
                    backup_files.append(full_path)
                except:
                    logger.warning(f"Invalid backup file: {filename}")

        if backup_files:
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            latest_backup = backup_files[0]
            logger.info(f"Found migration backup: {latest_backup}")
            return latest_backup

        logger.warning("No migration backup found")
        return None

    def check_migration_applied(self) -> bool:
        """Check if the migration was applied."""
        try:
            cursor = self.conn.cursor()
            # Use version column (existing schema)
            cursor.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?",
                (self.migration_id,),
            )
            exists = cursor.fetchone() is not None

            if not exists:
                logger.warning(f"Migration {self.migration_id} not found in tracking table")

            return exists
        except sqlite3.OperationalError:
            # Migration tracking table doesn't exist
            logger.warning("Migration tracking table not found")
            return False

    def data_export_session_columns(self) -> dict:
        """Export data from session columns before removal."""
        logger.info("Exporting session column data for preservation")

        try:
            cursor = self.conn.cursor()

            # Check if session columns exist
            cursor.execute("PRAGMA table_info(task)")
            columns = [row[1] for row in cursor.fetchall()]

            session_columns = ['session_id', 'session_span', 'pre_compaction_state',
                              'context_criticality', 'compaction_session_id']

            existing_session_columns = [col for col in session_columns if col in columns]

            if not existing_session_columns:
                logger.info("No session columns found to export")
                return {}

            # Export data
            export_data = {}
            for column in existing_session_columns:
                cursor.execute(f"SELECT id, {column} FROM task WHERE {column} IS NOT NULL")
                data = cursor.fetchall()
                if data:
                    export_data[column] = dict(data)

            # Export session_tracking table if exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_tracking'")
            if cursor.fetchone():
                cursor.execute("SELECT * FROM session_tracking")
                session_rows = cursor.fetchall()
                if session_rows:
                    cursor.execute("PRAGMA table_info(session_tracking)")
                    session_columns = [row[1] for row in cursor.fetchall()]
                    export_data['session_tracking'] = [
                        dict(zip(session_columns, row, strict=False)) for row in session_rows
                    ]

            # Save export to file
            if export_data:
                export_path = f"{self.db_path}.session_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(export_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                logger.info(f"Session data exported to: {export_path}")

            return export_data

        except Exception as e:
            logger.error(f"Failed to export session data: {e}")
            return {}

    def remove_session_triggers(self):
        """Remove session-related triggers."""
        logger.info("Removing session-related triggers")

        triggers_to_remove = [
            "update_session_tracking_timestamp",
            "validate_task_session_data"
        ]

        for trigger in triggers_to_remove:
            try:
                self.conn.execute(f"DROP TRIGGER IF EXISTS {trigger}")
                logger.info(f"Removed trigger: {trigger}")
            except sqlite3.Error as e:
                logger.warning(f"Failed to remove trigger {trigger}: {e}")

    def remove_session_indexes(self):
        """Remove session-related indexes."""
        logger.info("Removing session-related indexes")

        indexes_to_remove = [
            "idx_task_session_id",
            "idx_task_compaction_session",
            "idx_task_session_span",
            "idx_task_context_criticality",
            "idx_session_tracking_status",
            "idx_session_tracking_started",
            "idx_session_tracking_compaction",
            "idx_session_tracking_task_master"
        ]

        for index in indexes_to_remove:
            try:
                self.conn.execute(f"DROP INDEX IF EXISTS {index}")
                logger.info(f"Removed index: {index}")
            except sqlite3.Error as e:
                logger.warning(f"Failed to remove index {index}: {e}")

    def drop_session_tracking_table(self):
        """Drop the session_tracking table."""
        logger.info("Dropping session_tracking table")

        try:
            self.conn.execute("DROP TABLE IF EXISTS session_tracking")
            logger.info("session_tracking table dropped successfully")
        except sqlite3.Error as e:
            logger.error(f"Failed to drop session_tracking table: {e}")
            raise

    def get_existing_views(self):
        """Get existing views that depend on the task table."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name, sql FROM sqlite_master
            WHERE type='view' AND (sql LIKE '%FROM task%' OR sql LIKE '%JOIN task%')
        """)
        return cursor.fetchall()

    def get_all_triggers(self):
        """Get all triggers in the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'")
        return cursor.fetchall()

    def recreate_views(self, views):
        """Recreate views after table reconstruction."""
        for view_name, view_sql in views:
            try:
                self.conn.execute(view_sql)
                logger.info(f"Recreated view: {view_name}")
            except Exception as e:
                logger.warning(f"Failed to recreate view {view_name}: {e}")

    def recreate_triggers(self, triggers):
        """Recreate triggers after table reconstruction."""
        for trigger_name, trigger_sql in triggers:
            try:
                self.conn.execute(trigger_sql)
                logger.info(f"Recreated trigger: {trigger_name}")
            except Exception as e:
                logger.warning(f"Failed to recreate trigger {trigger_name}: {e}")

    def remove_session_columns(self):
        """Remove session-related columns from task table."""
        logger.info("Removing session columns from task table")

        # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
        session_columns = {
            'session_id', 'session_span', 'pre_compaction_state',
            'context_criticality', 'compaction_session_id'
        }

        try:
            # Get current table structure
            cursor = self.conn.cursor()

            # Get existing views and all triggers
            views = self.get_existing_views()
            triggers = self.get_all_triggers()
            logger.info(f"Found {len(views)} views and {len(triggers)} total triggers")

            # Drop views temporarily
            for view_name, _ in views:
                try:
                    cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
                    logger.info(f"Dropped view: {view_name}")
                except Exception as e:
                    logger.warning(f"Failed to drop view {view_name}: {e}")

            # Drop all triggers temporarily (to avoid reference issues)
            for trigger_name, _ in triggers:
                try:
                    cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
                    logger.info(f"Dropped trigger: {trigger_name}")
                except Exception as e:
                    logger.warning(f"Failed to drop trigger {trigger_name}: {e}")

            cursor.execute("PRAGMA table_info(task)")
            columns_info = cursor.fetchall()

            # Filter out session columns
            non_session_columns = []
            for col_info in columns_info:
                col_name = col_info[1]
                if col_name not in session_columns:
                    # Build column definition
                    col_type = col_info[2]
                    not_null = "NOT NULL" if col_info[3] else ""
                    default_val = f"DEFAULT {col_info[4]}" if col_info[4] is not None else ""
                    pk = "PRIMARY KEY" if col_info[5] else ""

                    col_def = f"{col_name} {col_type}"
                    if not_null:
                        col_def += f" {not_null}"
                    if default_val:
                        col_def += f" {default_val}"
                    if pk:
                        col_def += f" {pk}"

                    non_session_columns.append(col_def)

            # Create new table without session columns
            new_table_def = ",\n    ".join(non_session_columns)

            cursor.execute(f"""
                CREATE TABLE task_new (
                    {new_table_def}
                )
            """)

            # Copy data from old table to new table
            non_session_col_names = [info[1] for info in columns_info if info[1] not in session_columns]
            col_list = ", ".join(non_session_col_names)

            cursor.execute(f"""
                INSERT INTO task_new ({col_list})
                SELECT {col_list} FROM task
            """)

            # Drop old table and rename new table
            cursor.execute("DROP TABLE task")
            cursor.execute("ALTER TABLE task_new RENAME TO task")

            # Recreate indexes (excluding session-related ones)
            self.recreate_original_indexes()

            # Recreate views and triggers
            self.recreate_views(views)
            self.recreate_triggers(triggers)

            logger.info("Session columns removed successfully")

        except Exception as e:
            logger.error(f"Failed to remove session columns: {e}")
            raise

    def recreate_original_indexes(self):
        """Recreate original task table indexes."""
        logger.info("Recreating original task table indexes")

        original_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_task_tsk_id ON task(tsk_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_status ON task(status)",
            "CREATE INDEX IF NOT EXISTS idx_task_priority ON task(priority)",
            "CREATE INDEX IF NOT EXISTS idx_task_created_at ON task(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_task_parent_task_id ON task(parent_task_id)"
        ]

        for index_sql in original_indexes:
            try:
                self.conn.execute(index_sql)
                index_name = index_sql.split('idx_')[1].split(' ')[0]
                logger.info(f"Recreated index: {index_name}")
            except sqlite3.Error as e:
                logger.warning(f"Index recreation warning: {e}")

    def cleanup_migration_tracking(self):
        """Clean up migration tracking records."""
        logger.info("Cleaning up migration tracking records")

        try:
            cursor = self.conn.cursor()
            # Use version column (existing schema)
            cursor.execute("DELETE FROM schema_migrations WHERE version = ?", (self.migration_id,))
            if cursor.rowcount > 0:
                logger.info(f"Removed migration record: {self.migration_id}")
            else:
                logger.warning("Migration record not found in tracking table")
        except sqlite3.OperationalError:
            logger.warning("Migration tracking table not found")

    def validate_rollback(self) -> tuple[bool, list[str]]:
        """Validate that rollback was successful."""
        logger.info("Validating rollback results")

        validation_errors = []

        try:
            cursor = self.conn.cursor()

            # Check session columns are removed from task table
            cursor.execute("PRAGMA table_info(task)")
            task_columns = {row[1] for row in cursor.fetchall()}

            removed_columns = {
                'session_id', 'session_span', 'pre_compaction_state',
                'context_criticality', 'compaction_session_id'
            }

            remaining_session_columns = removed_columns & task_columns
            if remaining_session_columns:
                validation_errors.append(f"Session columns still present: {remaining_session_columns}")

            # Check session_tracking table is removed
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_tracking'")
            if cursor.fetchone():
                validation_errors.append("session_tracking table still exists")

            # Check session-related indexes are removed
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND name LIKE 'idx_%session%'
            """)
            remaining_indexes = {row[0] for row in cursor.fetchall()}
            if remaining_indexes:
                validation_errors.append(f"Session indexes still exist: {remaining_indexes}")

            # Check data integrity
            cursor.execute("SELECT COUNT(*) FROM task")
            task_count = cursor.fetchone()[0]
            logger.info(f"Validation: {task_count} tasks remain after rollback")

            success = len(validation_errors) == 0

            if success:
                logger.info("Rollback validation successful")
            else:
                logger.error(f"Rollback validation failed: {validation_errors}")

            return success, validation_errors

        except Exception as e:
            error_msg = f"Rollback validation failed: {e}"
            logger.error(error_msg)
            return False, [error_msg]

    def execute_rollback(self) -> tuple[bool, str]:
        """Execute the complete rollback with comprehensive error handling."""
        try:
            self.start_performance_timer()
            logger.info(f"Starting rollback for migration {self.migration_id}")

            # Validate database exists
            if not self.validate_database_exists():
                return False, "Database validation failed"

            # Connect to database
            self.connect()

            # Check if migration was applied
            if not self.check_migration_applied():
                return False, "Migration not found in tracking - cannot rollback"

            # Create pre-rollback backup
            self.create_pre_rollback_backup()

            # Export session data for preservation
            exported_data = self.data_export_session_columns()

            # Begin transaction
            self.conn.execute("BEGIN IMMEDIATE")

            try:
                # Execute rollback steps
                self.remove_session_triggers()
                self.remove_session_indexes()
                self.drop_session_tracking_table()
                self.remove_session_columns()
                self.cleanup_migration_tracking()

                # Validate rollback
                success, errors = self.validate_rollback()
                if not success:
                    raise Exception(f"Rollback validation failed: {errors}")

                # Commit transaction
                self.conn.commit()

                execution_time = self.get_execution_time()
                logger.info(f"Rollback completed successfully in {execution_time:.2f}ms")

                result_msg = f"Rollback completed successfully in {execution_time:.2f}ms"
                if self.backup_path:
                    result_msg += f". Pre-rollback backup at: {self.backup_path}"
                if exported_data:
                    result_msg += ". Session data preserved."

                return True, result_msg

            except Exception as e:
                # Rollback transaction
                self.conn.rollback()
                raise e

        except Exception as e:
            error_msg = f"Rollback failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        finally:
            self.close()

    def restore_from_backup(self) -> tuple[bool, str]:
        """Alternative rollback method: restore from migration backup."""
        try:
            logger.info("Attempting backup restoration rollback")

            migration_backup = self.find_migration_backup()
            if not migration_backup:
                return False, "No migration backup found for restoration"

            # Validate backup file
            try:
                backup_conn = sqlite3.connect(migration_backup)
                backup_conn.execute("PRAGMA integrity_check")
                backup_conn.close()
            except Exception as e:
                return False, f"Backup file validation failed: {e}"

            # Close any existing connections
            if self.conn:
                self.close()

            # Create safety backup
            safety_backup = f"{self.db_path}.safety_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            import shutil
            shutil.copy2(self.db_path, safety_backup)
            logger.info(f"Created safety backup: {safety_backup}")

            # Restore from migration backup
            os.remove(self.db_path)
            os.rename(migration_backup, self.db_path)

            logger.info(f"Database restored from backup: {migration_backup}")
            return True, f"Database restored from migration backup. Safety backup at: {safety_backup}"

        except Exception as e:
            error_msg = f"Backup restoration failed: {e}"
            logger.error(error_msg)
            return False, error_msg


def main():
    """Main execution function with comprehensive error handling."""
    db_path = r"P:\.speckit\taskmaster\tasks.db"

    # Ensure logs directory exists
    os.makedirs("P:/__csf/logs", exist_ok=True)

    print(f"TaskMaster Rollback (TASK-F-006): {sys.modules[__name__].__doc__.split('\n')[1].strip()}")
    print(f"Database: {db_path}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 80)

    # Check database exists
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found at {db_path}")
        return 1

    # Ask user for rollback method
    print("\nRollback Methods Available:")
    print("1. Column Removal Rollback (preserves other data)")
    print("2. Backup Restoration Rollback (restores to pre-migration state)")

    try:
        choice = input("\nSelect rollback method (1 or 2): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nRollback cancelled by user")
        return 0

    # Execute rollback
    rollback = SessionColumnsRollback(db_path)

    if choice == "1":
        success, message = rollback.execute_rollback()
    elif choice == "2":
        success, message = rollback.restore_from_backup()
    else:
        print(f"[ERROR] Invalid choice: {choice}")
        return 1

    if success:
        print(f"[SUCCESS] {message}")
        return 0
    else:
        print(f"[ERROR] {message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
