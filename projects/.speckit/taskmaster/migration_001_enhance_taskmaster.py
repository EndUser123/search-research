"""
Comprehensive Database Migration for TaskMaster Enhancement and Atomic Task Decomposition

This migration implements:
1. Schema enhancements for existing tables (automation_rules, evidence, task, tsk)
2. New tables for atomic task decomposition
3. New tables for TaskMaster enhancement
4. Performance optimizations with proper indexes
5. CWO12 compliance and data integrity safeguards

Migration ID: 001
Author: Claude Code
Date: 2025-12-02
"""

import logging
import os
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TaskMasterMigration:
    """Comprehensive migration for TaskMaster enhancement."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.migration_version = "001"
        self.migration_name = "enhance_taskmaster_and_atomic_decomposition"

    def connect(self):
        """Establish database connection with safety settings."""
        self.conn = sqlite3.connect(self.db_path)
        # Enable foreign key constraints
        self.conn.execute("PRAGMA foreign_keys = ON")
        # Set WAL mode for better concurrent access
        self.conn.execute("PRAGMA journal_mode = WAL")
        # Optimize for performance
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.conn.execute("PRAGMA cache_size = 10000")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def backup_database(self) -> str:
        """Create a backup of the current database."""
        backup_path = (
            f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        logger.info(f"Creating backup at: {backup_path}")

        # Create backup
        source = sqlite3.connect(self.db_path)
        backup = sqlite3.connect(backup_path)
        source.backup(backup)
        source.close()
        backup.close()

        return backup_path

    def create_migration_table(self):
        """Create migration tracking table if it doesn't exist."""
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                executed_at TEXT NOT NULL,
                backup_path TEXT,
                checksum TEXT
            )
        """
        )

    def check_migration_applied(self) -> bool:
        """Check if this migration has already been applied."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM schema_migrations WHERE version = ?",
            (self.migration_version,),
        )
        return cursor.fetchone() is not None

    def record_migration(self, backup_path: str):
        """Record the migration execution."""
        checksum = self.calculate_migration_checksum()
        self.conn.execute(
            """
            INSERT INTO schema_migrations
            (version, name, executed_at, backup_path, checksum)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                self.migration_version,
                self.migration_name,
                datetime.now().isoformat(),
                backup_path,
                checksum,
            ),
        )
        self.conn.commit()

    def calculate_migration_checksum(self) -> str:
        """Calculate a checksum for migration verification."""
        # In a real implementation, this would be a proper hash
        # For now, using a simple checksum based on version and timestamp
        return f"{self.migration_version}_{datetime.now().strftime('%Y%m%d')}"

    def enhance_existing_tables(self):
        """Enhance existing tables with new columns."""
        logger.info("Enhancing existing tables...")

        # 1. Enhance automation_rules table
        automation_rules_enhancements = [
            "ALTER TABLE automation_rules ADD COLUMN github_triggers TEXT",
            "ALTER TABLE automation_rules ADD COLUMN webhook_config TEXT",
            "ALTER TABLE automation_rules ADD COLUMN auto_cwo12_validation INTEGER DEFAULT 0",
            "ALTER TABLE automation_rules ADD COLUMN ai_priority_score REAL DEFAULT 0.0",
        ]

        # 2. Enhance evidence table
        evidence_enhancements = [
            "ALTER TABLE evidence ADD COLUMN auto_generated INTEGER DEFAULT 0",
            "ALTER TABLE evidence ADD COLUMN verification_score REAL DEFAULT 0.0",
            "ALTER TABLE evidence ADD COLUMN git_commit_hash TEXT",
            "ALTER TABLE evidence ADD COLUMN artifact_path TEXT",
            "ALTER TABLE evidence ADD COLUMN ai_verified INTEGER DEFAULT 0",
        ]

        # 3. Enhance task table
        task_enhancements = [
            "ALTER TABLE task ADD COLUMN ai_complexity_score REAL DEFAULT 0.0",
            "ALTER TABLE task ADD COLUMN predicted_duration REAL DEFAULT 0.0",
            "ALTER TABLE task ADD COLUMN github_pr_number INTEGER",
            "ALTER TABLE task ADD COLUMN evidence_count INTEGER DEFAULT 0",
        ]

        # 4. Enhance tsk table
        tsk_enhancements = [
            "ALTER TABLE tsk ADD COLUMN cross_project_dependencies TEXT DEFAULT '[]'",
            "ALTER TABLE tsk ADD COLUMN unified_compliance_score REAL DEFAULT 0.0",
            "ALTER TABLE tsk ADD COLUMN ai_optimization_suggestions TEXT DEFAULT '[]'",
        ]

        # Apply enhancements safely
        all_enhancements = [
            (automation_rules_enhancements, "automation_rules"),
            (evidence_enhancements, "evidence"),
            (task_enhancements, "task"),
            (tsk_enhancements, "tsk"),
        ]

        for enhancements, table_name in all_enhancements:
            for enhancement in enhancements:
                try:
                    self.conn.execute(enhancement)
                    logger.info(f"Applied enhancement to {table_name}: {enhancement}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        logger.warning(
                            f"Column already exists in {table_name}: {enhancement}"
                        )
                    else:
                        raise e

        self.conn.commit()

    def create_atomic_decomposition_tables(self):
        """Create tables for atomic task decomposition."""
        logger.info("Creating atomic task decomposition tables...")

        # atomic_task_patterns table
        self.conn.execute(
            """
            CREATE TABLE atomic_task_patterns (
                id TEXT PRIMARY KEY,
                pattern_name TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                complexity_indicators TEXT NOT NULL,
                success_criteria TEXT NOT NULL,
                common_pitfalls TEXT NOT NULL,
                training_examples TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # task_decomposition_history table
        self.conn.execute(
            """
            CREATE TABLE task_decomposition_history (
                id TEXT PRIMARY KEY,
                original_task_id TEXT NOT NULL,
                decomposition_result TEXT NOT NULL,
                performance_metrics TEXT NOT NULL,
                user_feedback TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (original_task_id) REFERENCES task(id) ON DELETE CASCADE
            )
        """
        )

        logger.info("Created atomic task decomposition tables")

    def create_taskmaster_enhancement_tables(self):
        """Create tables for TaskMaster enhancement."""
        logger.info("Creating TaskMaster enhancement tables...")

        # task_predictions table
        self.conn.execute(
            """
            CREATE TABLE task_predictions (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                model_version TEXT NOT NULL,
                predicted_completion_time REAL NOT NULL,
                confidence_score REAL NOT NULL,
                features_used TEXT NOT NULL,
                training_data_period TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE CASCADE
            )
        """
        )

        # cross_project_dependencies table
        self.conn.execute(
            """
            CREATE TABLE cross_project_dependencies (
                id TEXT PRIMARY KEY,
                source_tsk TEXT NOT NULL,
                target_tsk TEXT NOT NULL,
                dependency_type TEXT NOT NULL,
                dependency_details TEXT NOT NULL,
                risk_score REAL DEFAULT 0.0,
                resolution_status TEXT DEFAULT 'pending',
                resolution_notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT,
                resolved_by TEXT,
                FOREIGN KEY (source_tsk) REFERENCES tsk(id) ON DELETE CASCADE,
                FOREIGN KEY (target_tsk) REFERENCES tsk(id) ON DELETE CASCADE
            )
        """
        )

        # ai_analytics table
        self.conn.execute(
            """
            CREATE TABLE ai_analytics (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                tsk_id TEXT,
                analysis_type TEXT NOT NULL,
                analysis_version TEXT NOT NULL,
                insights TEXT NOT NULL,
                confidence_level REAL NOT NULL,
                actionable_items TEXT NOT NULL,
                performance_metrics TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE CASCADE,
                FOREIGN KEY (tsk_id) REFERENCES tsk(id) ON DELETE CASCADE
            )
        """
        )

        logger.info("Created TaskMaster enhancement tables")

    def create_performance_indexes(self):
        """Create indexes for performance optimization."""
        logger.info("Creating performance indexes...")

        # Indexes for enhanced existing tables
        existing_table_indexes = [
            # automation_rules indexes
            "CREATE INDEX IF NOT EXISTS idx_automation_rules_ai_priority ON automation_rules(ai_priority_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_automation_rules_cwo12_validation ON automation_rules(auto_cwo12_validation)",
            # evidence indexes
            "CREATE INDEX IF NOT EXISTS idx_evidence_auto_generated ON evidence(auto_generated)",
            "CREATE INDEX IF NOT EXISTS idx_evidence_verification_score ON evidence(verification_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_evidence_ai_verified ON evidence(ai_verified)",
            "CREATE INDEX IF NOT EXISTS idx_evidence_git_commit ON evidence(git_commit_hash)",
            # task indexes
            "CREATE INDEX IF NOT EXISTS idx_task_ai_complexity ON task(ai_complexity_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_task_predicted_duration ON task(predicted_duration)",
            "CREATE INDEX IF NOT EXISTS idx_task_github_pr ON task(github_pr_number)",
            "CREATE INDEX IF NOT EXISTS idx_task_evidence_count ON task(evidence_count DESC)",
            # tsk indexes
            "CREATE INDEX IF NOT EXISTS idx_tsk_compliance_score ON tsk(unified_compliance_score DESC)",
        ]

        # Indexes for new tables
        new_table_indexes = [
            # atomic_task_patterns indexes
            "CREATE INDEX IF NOT EXISTS idx_atomic_patterns_type ON atomic_task_patterns(pattern_type)",
            "CREATE INDEX IF NOT EXISTS idx_atomic_patterns_created ON atomic_task_patterns(created_at DESC)",
            # task_decomposition_history indexes
            "CREATE INDEX IF NOT EXISTS idx_decomp_history_task ON task_decomposition_history(original_task_id)",
            "CREATE INDEX IF NOT EXISTS idx_decomp_history_timestamp ON task_decomposition_history(timestamp DESC)",
            # task_predictions indexes
            "CREATE INDEX IF NOT EXISTS idx_predictions_task ON task_predictions(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_confidence ON task_predictions(confidence_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_model ON task_predictions(model_version)",
            # cross_project_dependencies indexes
            "CREATE INDEX IF NOT EXISTS idx_deps_source_tsk ON cross_project_dependencies(source_tsk)",
            "CREATE INDEX IF NOT EXISTS idx_deps_target_tsk ON cross_project_dependencies(target_tsk)",
            "CREATE INDEX IF NOT EXISTS idx_deps_status ON cross_project_dependencies(resolution_status)",
            "CREATE INDEX IF NOT EXISTS idx_deps_risk_score ON cross_project_dependencies(risk_score DESC)",
            # ai_analytics indexes
            "CREATE INDEX IF NOT EXISTS idx_analytics_task ON ai_analytics(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_tsk ON ai_analytics(tsk_id)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_type ON ai_analytics(analysis_type)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_confidence ON ai_analytics(confidence_level DESC)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_expires ON ai_analytics(expires_at)",
        ]

        all_indexes = existing_table_indexes + new_table_indexes

        for index_sql in all_indexes:
            try:
                self.conn.execute(index_sql)
                logger.info(
                    f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}"
                )
            except sqlite3.OperationalError as e:
                if "already exists" not in str(e):
                    logger.warning(f"Index creation issue: {e}")

        self.conn.commit()

    def create_triggers(self):
        """Create triggers for data consistency."""
        logger.info("Creating data consistency triggers...")

        # Trigger to update evidence_count when evidence is added/removed
        self.conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS update_task_evidence_count_insert
            AFTER INSERT ON evidence
            FOR EACH ROW
            WHEN NEW.task_id IS NOT NULL
            BEGIN
                UPDATE task
                SET evidence_count = (
                    SELECT COUNT(*) FROM evidence WHERE task_id = NEW.task_id
                )
                WHERE id = NEW.task_id;
            END
        """
        )

        self.conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS update_task_evidence_count_delete
            AFTER DELETE ON evidence
            FOR EACH ROW
            WHEN OLD.task_id IS NOT NULL
            BEGIN
                UPDATE task
                SET evidence_count = (
                    SELECT COUNT(*) FROM evidence WHERE task_id = OLD.task_id
                )
                WHERE id = OLD.task_id;
            END
        """
        )

        # Trigger to update atomic_task_patterns updated_at
        self.conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS update_atomic_pattern_timestamp
            AFTER UPDATE ON atomic_task_patterns
            FOR EACH ROW
            BEGIN
                UPDATE atomic_task_patterns
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END
        """
        )

        # Trigger to update task_predictions updated_at
        self.conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS update_task_prediction_timestamp
            AFTER UPDATE ON task_predictions
            FOR EACH ROW
            BEGIN
                UPDATE task_predictions
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END
        """
        )

        logger.info("Created data consistency triggers")

    def validate_migration(self) -> tuple[bool, list[str]]:
        """Validate that migration was successful."""
        logger.info("Validating migration...")

        if not self.conn:
            raise Exception("Database connection not established")

        validation_errors = []

        # Check all expected tables exist
        expected_tables = {
            "tsk",
            "task",
            "evidence",
            "task_state_transitions",
            "task_automation_queue",
            "automation_executions",
            "automated_tasks",
            "automation_rules",
            "atomic_task_patterns",
            "task_decomposition_history",
            "task_predictions",
            "cross_project_dependencies",
            "ai_analytics",
            "schema_migrations",
        }

        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        missing_tables = expected_tables - existing_tables
        if missing_tables:
            validation_errors.append(f"Missing tables: {missing_tables}")

        # Check enhanced columns exist
        enhanced_columns = {
            "automation_rules": [
                "github_triggers",
                "webhook_config",
                "auto_cwo12_validation",
                "ai_priority_score",
            ],
            "evidence": [
                "auto_generated",
                "verification_score",
                "git_commit_hash",
                "artifact_path",
                "ai_verified",
            ],
            "task": [
                "ai_complexity_score",
                "predicted_duration",
                "github_pr_number",
                "evidence_count",
            ],
            "tsk": [
                "cross_project_dependencies",
                "unified_compliance_score",
                "ai_optimization_suggestions",
            ],
        }

        for table, columns in enhanced_columns.items():
            cursor.execute(f"PRAGMA table_info({table})")
            existing_columns = {row[1] for row in cursor.fetchall()}

            missing_columns = set(columns) - existing_columns
            if missing_columns:
                validation_errors.append(
                    f"Missing columns in {table}: {missing_columns}"
                )

        # Test basic data integrity
        try:
            # Test foreign key constraints
            cursor.execute("PRAGMA foreign_key_check")
            fk_violations = cursor.fetchall()
            if fk_violations:
                validation_errors.append(f"Foreign key violations: {fk_violations}")

        except sqlite3.Error as e:
            validation_errors.append(f"Data integrity check failed: {e}")

        success = len(validation_errors) == 0
        if success:
            logger.info("Migration validation successful")
        else:
            logger.error(f"Migration validation failed: {validation_errors}")

        return success, validation_errors

    def execute_migration(self) -> tuple[bool, str]:
        """Execute the complete migration."""
        try:
            logger.info(
                f"Starting migration {self.migration_version}: {self.migration_name}"
            )

            # Check if migration already applied
            if self.check_migration_applied():
                logger.warning("Migration already applied")
                return True, "Migration already applied"

            # Create backup
            backup_path = self.backup_database()

            # Connect to database
            self.connect()

            # Create migration tracking table
            self.create_migration_table()

            # Execute migration steps
            self.enhance_existing_tables()
            self.create_atomic_decomposition_tables()
            self.create_taskmaster_enhancement_tables()
            self.create_performance_indexes()
            self.create_triggers()

            # Validate migration
            success, errors = self.validate_migration()
            if not success:
                raise Exception(f"Migration validation failed: {errors}")

            # Record migration
            self.record_migration(backup_path)

            logger.info(f"Migration {self.migration_version} completed successfully")
            return True, f"Migration completed successfully. Backup at: {backup_path}"

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False, f"Migration failed: {str(e)}"

        finally:
            self.close()

    def rollback_migration(self) -> tuple[bool, str]:
        """Rollback the migration by restoring from backup."""
        try:
            logger.info("Starting migration rollback...")

            # Find the most recent backup
            backup_files = [
                f
                for f in os.listdir(os.path.dirname(self.db_path))
                if f.startswith(os.path.basename(self.db_path) + ".backup_")
            ]

            if not backup_files:
                return False, "No backup files found for rollback"

            # Sort backups by timestamp (most recent first)
            backup_files.sort(reverse=True)
            latest_backup = os.path.join(os.path.dirname(self.db_path), backup_files[0])

            # Restore from backup
            if os.path.exists(latest_backup):
                # Close any existing connections
                if self.conn:
                    self.close()

                # Replace current database with backup
                os.remove(self.db_path)
                os.rename(latest_backup, self.db_path)

                logger.info(f"Rollback completed using backup: {latest_backup}")
                return (
                    True,
                    f"Rollback completed successfully using backup: {backup_files[0]}",
                )
            else:
                return False, f"Backup file not found: {latest_backup}"

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False, f"Rollback failed: {str(e)}"


def main():
    """Main execution function."""
    db_path = r"P:\.speckit\taskmaster\tasks.db"

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    migration = TaskMasterMigration(db_path)

    # Execute migration
    success, message = migration.execute_migration()

    if success:
        print("[SUCCESS] Migration completed successfully!")
        print(f"[INFO] {message}")
    else:
        print("[ERROR] Migration failed!")
        print(f"[INFO] {message}")

        # Offer rollback option
        response = input("Would you like to rollback? (y/n): ").lower().strip()
        if response == "y":
            rollback_success, rollback_message = migration.rollback_migration()
            if rollback_success:
                print("[SUCCESS] Rollback completed successfully!")
                print(f"[INFO] {rollback_message}")
            else:
                print("[ERROR] Rollback failed!")
                print(f"[INFO] {rollback_message}")


if __name__ == "__main__":
    main()
