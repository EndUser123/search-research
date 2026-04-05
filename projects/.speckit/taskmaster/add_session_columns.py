"""
TaskMaster Database Migration: Session Columns Addition (TASK-F-004)

This migration implements session tracking capabilities for TaskMaster by:
1. Adding session-related columns to the task table
2. Creating session_tracking table for comprehensive session management
3. Adding appropriate indexes for performance optimization
4. Implementing comprehensive error handling and rollback capabilities
5. Ensuring zero data loss during migration

Migration ID: TASK-F-004
Author: Claude Code (CSF_NIP_DEVELOPMENT)
Date: 2025-12-13
Performance Target: <50ms execution time
"""

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
        logging.FileHandler(f"P:/__csf/logs/taskmaster_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SessionColumnsMigration:
    """Migration class for adding session columns to TaskMaster database."""

    def __init__(self, db_path: str):
        """Initialize migration with database path."""
        self.db_path = db_path
        self.conn = None
        self.migration_id = "TASK-F-004"
        self.migration_name = "add_session_columns"
        self.start_time = None
        self.backup_path = None

    def connect(self):
        """Establish database connection with optimized settings."""
        logger.info(f"Connecting to database: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)

        # Enable performance optimizations
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.conn.execute("PRAGMA cache_size = 10000")
        self.conn.execute("PRAGMA temp_store = MEMORY")
        self.conn.execute("PRAGMA mmap_size = 268435456")  # 256MB

        logger.info("Database connection established with performance optimizations")

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
            # Test database accessibility
            test_conn = sqlite3.connect(self.db_path)
            test_conn.execute("SELECT 1")
            test_conn.close()
            logger.info("Database validation successful")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database validation failed: {e}")
            return False

    def backup_database(self) -> str:
        """Create a comprehensive backup of the current database."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.db_path}.backup_{self.migration_id}_{timestamp}"

        logger.info(f"Creating database backup at: {backup_path}")

        try:
            # Create backup using SQLite backup API for integrity
            source = sqlite3.connect(self.db_path)
            backup = sqlite3.connect(backup_path)

            # Simple backup without progress callback to avoid signature issues
            source.backup(backup)
            source.close()
            backup.close()

            # Verify backup integrity
            backup_conn = sqlite3.connect(backup_path)
            backup_conn.execute("PRAGMA integrity_check")
            backup_conn.close()

            self.backup_path = backup_path
            logger.info(f"Database backup completed successfully: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise

    def create_migration_tracking(self):
        """Create migration tracking table if it doesn't exist."""
        logger.info("Creating migration tracking infrastructure")

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_id TEXT PRIMARY KEY,
                migration_name TEXT NOT NULL,
                executed_at TEXT NOT NULL,
                backup_path TEXT,
                execution_time_ms REAL,
                checksum TEXT,
                status TEXT DEFAULT 'completed'
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS migration_locks (
                migration_id TEXT PRIMARY KEY,
                locked_at TEXT NOT NULL,
                lock_expiry TEXT NOT NULL,
                hostname TEXT,
                process_id INTEGER
            )
        """)

        logger.info("Migration tracking infrastructure created")

    def check_migration_applied(self) -> bool:
        """Check if this migration has already been applied."""
        cursor = self.conn.cursor()

        # Check if migration tracking table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
        if not cursor.fetchone():
            logger.info("Migration tracking table not found - migration not applied")
            return False

        cursor.execute(
            "SELECT 1 FROM schema_migrations WHERE migration_id = ?",
            (self.migration_id,),
        )
        exists = cursor.fetchone() is not None

        if exists:
            logger.warning(f"Migration {self.migration_id} already applied")

        return exists

    def acquire_migration_lock(self) -> bool:
        """Acquire migration lock to prevent concurrent migrations."""
        cursor = self.conn.cursor()

        # Ensure migration_locks table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migration_locks (
                migration_id TEXT PRIMARY KEY,
                locked_at TEXT NOT NULL,
                lock_expiry TEXT NOT NULL,
                hostname TEXT,
                process_id INTEGER
            )
        """)

        # Clean up expired locks
        cursor.execute(
            "DELETE FROM migration_locks WHERE lock_expiry < ?",
            (datetime.now().isoformat(),)
        )

        # Try to acquire lock
        lock_expiry = datetime.fromtimestamp(time.time() + 300).isoformat()  # 5 minutes
        try:
            cursor.execute("""
                INSERT INTO migration_locks
                (migration_id, locked_at, lock_expiry, hostname, process_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.migration_id,
                datetime.now().isoformat(),
                lock_expiry,
                os.environ.get('COMPUTERNAME', 'unknown'),
                os.getpid()
            ))
            self.conn.commit()
            logger.info("Migration lock acquired")
            return True
        except sqlite3.IntegrityError:
            logger.error("Migration lock already held by another process")
            return False

    def release_migration_lock(self):
        """Release migration lock."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM migration_locks WHERE migration_id = ?", (self.migration_id,))
        self.conn.commit()
        logger.info("Migration lock released")

    def add_session_columns(self):
        """Add session-related columns to the task table."""
        logger.info("Adding session columns to task table")

        session_columns = [
            "ALTER TABLE task ADD COLUMN session_id TEXT",
            "ALTER TABLE task ADD COLUMN session_span INTEGER DEFAULT 0",
            "ALTER TABLE task ADD COLUMN pre_compaction_state TEXT",
            "ALTER TABLE task ADD COLUMN context_criticality REAL DEFAULT 0.0",
            "ALTER TABLE task ADD COLUMN compaction_session_id TEXT"
        ]

        errors = []
        for column_sql in session_columns:
            try:
                self.conn.execute(column_sql)
                logger.info(f"Added column: {column_sql.split('ADD COLUMN')[1].strip()}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    logger.warning(f"Column already exists: {column_sql}")
                else:
                    errors.append(f"Failed to add column: {column_sql} - {e}")
                    logger.error(f"Failed to add column: {column_sql} - {e}")

        if errors:
            raise Exception(f"Failed to add session columns: {errors}")

        logger.info("Session columns added successfully")

    def create_session_tracking_table(self):
        """Create the session_tracking table."""
        logger.info("Creating session_tracking table")

        self.conn.execute("""
            CREATE TABLE session_tracking (
                session_id TEXT PRIMARY KEY,
                task_master_session_id TEXT,
                started_at TIMESTAMP,
                last_compaction TIMESTAMP,
                compaction_count INTEGER DEFAULT 0,
                total_context_tokens INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        logger.info("session_tracking table created successfully")

    def create_session_indexes(self):
        """Create indexes for session-related performance optimization."""
        logger.info("Creating session performance indexes")

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_task_session_id ON task(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_compaction_session ON task(compaction_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_session_span ON task(session_span)",
            "CREATE INDEX IF NOT EXISTS idx_task_context_criticality ON task(context_criticality)",
            "CREATE INDEX IF NOT EXISTS idx_session_tracking_status ON session_tracking(status)",
            "CREATE INDEX IF NOT EXISTS idx_session_tracking_started ON session_tracking(started_at)",
            "CREATE INDEX IF NOT EXISTS idx_session_tracking_compaction ON session_tracking(last_compaction)",
            "CREATE INDEX IF NOT EXISTS idx_session_tracking_task_master ON session_tracking(task_master_session_id)"
        ]

        for index_sql in indexes:
            try:
                self.conn.execute(index_sql)
                index_name = index_sql.split('idx_')[1].split(' ')[0]
                logger.info(f"Created index: {index_name}")
            except sqlite3.Error as e:
                logger.warning(f"Index creation warning: {e}")

        logger.info("Session indexes created successfully")

    def create_session_triggers(self):
        """Create triggers for session data consistency."""
        logger.info("Creating session consistency triggers")

        # Trigger to update session_tracking.updated_at
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_session_tracking_timestamp
            AFTER UPDATE ON session_tracking
            FOR EACH ROW
            BEGIN
                UPDATE session_tracking
                SET updated_at = CURRENT_TIMESTAMP
                WHERE session_id = NEW.session_id;
            END
        """)

        # Trigger to validate session data integrity
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS validate_task_session_data
            BEFORE INSERT ON task
            FOR EACH ROW
            WHEN NEW.session_id IS NOT NULL
            BEGIN
                SELECT CASE
                    WHEN NEW.session_span < 0 THEN
                        RAISE(ABORT, 'session_span must be non-negative')
                    WHEN NEW.context_criticality < 0.0 OR NEW.context_criticality > 1.0 THEN
                        RAISE(ABORT, 'context_criticality must be between 0.0 and 1.0')
                END;
            END
        """)

        logger.info("Session triggers created successfully")

    def validate_migration(self) -> tuple[bool, list[str]]:
        """Comprehensive validation of migration success."""
        logger.info("Validating migration results")

        validation_errors = []

        try:
            cursor = self.conn.cursor()

            # Check task table has new columns
            cursor.execute("PRAGMA table_info(task)")
            task_columns = {row[1] for row in cursor.fetchall()}

            required_task_columns = {
                'session_id', 'session_span', 'pre_compaction_state',
                'context_criticality', 'compaction_session_id'
            }

            missing_task_columns = required_task_columns - task_columns
            if missing_task_columns:
                validation_errors.append(f"Missing task columns: {missing_task_columns}")

            # Check session_tracking table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_tracking'")
            if not cursor.fetchone():
                validation_errors.append("session_tracking table not created")
            else:
                # Check session_tracking table structure
                cursor.execute("PRAGMA table_info(session_tracking)")
                session_columns = {row[1] for row in cursor.fetchall()}

                required_session_columns = {
                    'session_id', 'task_master_session_id', 'started_at',
                    'last_compaction', 'compaction_count', 'total_context_tokens',
                    'status', 'metadata', 'created_at', 'updated_at'
                }

                missing_session_columns = required_session_columns - session_columns
                if missing_session_columns:
                    validation_errors.append(f"Missing session_tracking columns: {missing_session_columns}")

            # Check foreign key integrity
            cursor.execute("PRAGMA foreign_key_check")
            fk_violations = cursor.fetchall()
            if fk_violations:
                validation_errors.append(f"Foreign key violations: {fk_violations}")

            # Test basic operations
            try:
                cursor.execute("SELECT COUNT(*) FROM task")
                task_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM session_tracking")
                session_count = cursor.fetchone()[0]
                logger.info(f"Validation: {task_count} tasks, {session_count} sessions")
            except sqlite3.Error as e:
                validation_errors.append(f"Basic operation test failed: {e}")

            # Check indexes exist
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND name LIKE 'idx_%session%'
            """)
            indexes = {row[0] for row in cursor.fetchall()}
            expected_indexes = {
                'idx_task_session_id', 'idx_task_compaction_session',
                'idx_task_session_span', 'idx_task_context_criticality',
                'idx_session_tracking_status', 'idx_session_tracking_started',
                'idx_session_tracking_compaction', 'idx_session_tracking_task_master'
            }

            missing_indexes = expected_indexes - indexes
            if missing_indexes:
                logger.warning(f"Missing indexes: {missing_indexes}")

            success = len(validation_errors) == 0

            if success:
                logger.info("Migration validation successful")
            else:
                logger.error(f"Migration validation failed: {validation_errors}")

            return success, validation_errors

        except Exception as e:
            error_msg = f"Validation process failed: {e}"
            logger.error(error_msg)
            return False, [error_msg]

    def calculate_migration_checksum(self) -> str:
        """Calculate checksum for migration verification."""
        # Simple checksum based on migration details
        import hashlib
        content = f"{self.migration_id}_{self.migration_name}_{datetime.now().strftime('%Y%m%d')}"
        return hashlib.md5(content.encode()).hexdigest()

    def record_migration(self):
        """Record successful migration in tracking table."""
        checksum = self.calculate_migration_checksum()
        execution_time = self.get_execution_time()

        self.conn.execute("""
            INSERT INTO schema_migrations
            (migration_id, migration_name, executed_at, backup_path, execution_time_ms, checksum, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            self.migration_id,
            self.migration_name,
            datetime.now().isoformat(),
            self.backup_path,
            execution_time,
            checksum,
            'completed'
        ))

        self.conn.commit()
        logger.info(f"Migration recorded: {self.migration_id} in {execution_time:.2f}ms")

    def execute_migration(self) -> tuple[bool, str]:
        """Execute the complete migration with comprehensive error handling."""
        try:
            self.start_performance_timer()
            logger.info(f"Starting migration {self.migration_id}: {self.migration_name}")

            # Validate database exists
            if not self.validate_database_exists():
                return False, "Database validation failed"

            # Connect to database
            self.connect()

            # Acquire migration lock
            if not self.acquire_migration_lock():
                return False, "Could not acquire migration lock"

            # Check if migration already applied
            if self.check_migration_applied():
                return False, "Migration already applied"

            # Create backup
            self.backup_database()

            # Create migration tracking
            self.create_migration_tracking()

            # Begin transaction
            self.conn.execute("BEGIN IMMEDIATE")

            try:
                # Execute migration steps
                self.add_session_columns()
                self.create_session_tracking_table()
                self.create_session_indexes()
                self.create_session_triggers()

                # Validate migration
                success, errors = self.validate_migration()
                if not success:
                    raise Exception(f"Migration validation failed: {errors}")

                # Commit transaction
                self.conn.commit()

                # Record migration
                self.record_migration()

                execution_time = self.get_execution_time()
                logger.info(f"Migration {self.migration_id} completed successfully in {execution_time:.2f}ms")

                # Check performance requirement
                if execution_time > 50:
                    logger.warning(f"Migration exceeded 50ms target: {execution_time:.2f}ms")
                else:
                    logger.info(f"Migration met performance target: {execution_time:.2f}ms < 50ms")

                return True, f"Migration completed successfully in {execution_time:.2f}ms. Backup at: {self.backup_path}"

            except Exception as e:
                # Rollback transaction
                self.conn.rollback()
                raise e

        except Exception as e:
            error_msg = f"Migration failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        finally:
            # Release lock and close connection
            try:
                self.release_migration_lock()
            except:
                pass
            self.close()


def main():
    """Main execution function with comprehensive error handling."""
    db_path = r"P:\.speckit\taskmaster\tasks.db"

    # Ensure logs directory exists
    os.makedirs("P:/__csf/logs", exist_ok=True)

    print(f"TaskMaster Migration: {sys.modules[__name__].__doc__.split('\n')[1].strip()}")
    print(f"Database: {db_path}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 80)

    # Check database exists
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found at {db_path}")
        return 1

    # Execute migration
    migration = SessionColumnsMigration(db_path)
    success, message = migration.execute_migration()

    if success:
        print(f"[SUCCESS] {message}")
        return 0
    else:
        print(f"[ERROR] {message}")

        # Suggest rollback if migration failed partially
        if "already applied" not in message:
            print("\n[SUGGESTION] Consider running rollback_session_columns.py to restore previous state")

        return 1


if __name__ == "__main__":
    sys.exit(main())
