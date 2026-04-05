"""
Apply database migration step by step
"""

import sqlite3
import sys


def apply_migration():
    db_path = r"P:\.speckit\taskmaster\tasks.db"

    try:
        print("=== Step 1: Connect to database ===")
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        print("[OK] Connected successfully")

        print("\n=== Step 2: Enhance automation_rules table ===")
        enhancements = [
            "ALTER TABLE automation_rules ADD COLUMN github_triggers TEXT",
            "ALTER TABLE automation_rules ADD COLUMN webhook_config TEXT",
            "ALTER TABLE automation_rules ADD COLUMN auto_cwo12_validation INTEGER DEFAULT 0",
            "ALTER TABLE automation_rules ADD COLUMN ai_priority_score REAL DEFAULT 0.0",
        ]

        for enhancement in enhancements:
            try:
                cursor.execute(enhancement)
                print(f"[OK] {enhancement}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"[OK] {enhancement} (column already exists)")
                else:
                    print(f"[ERROR] {enhancement}: {e}")
                    return False

        print("\n=== Step 3: Enhance evidence table ===")
        evidence_enhancements = [
            "ALTER TABLE evidence ADD COLUMN auto_generated INTEGER DEFAULT 0",
            "ALTER TABLE evidence ADD COLUMN verification_score REAL DEFAULT 0.0",
            "ALTER TABLE evidence ADD COLUMN git_commit_hash TEXT",
            "ALTER TABLE evidence ADD COLUMN artifact_path TEXT",
            "ALTER TABLE evidence ADD COLUMN ai_verified INTEGER DEFAULT 0",
        ]

        for enhancement in evidence_enhancements:
            try:
                cursor.execute(enhancement)
                print(f"[OK] {enhancement}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"[OK] {enhancement} (column already exists)")
                else:
                    print(f"[ERROR] {enhancement}: {e}")
                    return False

        print("\n=== Step 4: Enhance task table ===")
        task_enhancements = [
            "ALTER TABLE task ADD COLUMN ai_complexity_score REAL DEFAULT 0.0",
            "ALTER TABLE task ADD COLUMN predicted_duration REAL DEFAULT 0.0",
            "ALTER TABLE task ADD COLUMN github_pr_number INTEGER",
            "ALTER TABLE task ADD COLUMN evidence_count INTEGER DEFAULT 0",
        ]

        for enhancement in task_enhancements:
            try:
                cursor.execute(enhancement)
                print(f"[OK] {enhancement}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"[OK] {enhancement} (column already exists)")
                else:
                    print(f"[ERROR] {enhancement}: {e}")
                    return False

        print("\n=== Step 5: Enhance tsk table ===")
        tsk_enhancements = [
            "ALTER TABLE tsk ADD COLUMN cross_project_dependencies TEXT DEFAULT '[]'",
            "ALTER TABLE tsk ADD COLUMN unified_compliance_score REAL DEFAULT 0.0",
            "ALTER TABLE tsk ADD COLUMN ai_optimization_suggestions TEXT DEFAULT '[]'",
        ]

        for enhancement in tsk_enhancements:
            try:
                cursor.execute(enhancement)
                print(f"[OK] {enhancement}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"[OK] {enhancement} (column already exists)")
                else:
                    print(f"[ERROR] {enhancement}: {e}")
                    return False

        print("\n=== Step 6: Create atomic_task_patterns table ===")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS atomic_task_patterns (
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
        print("✓ Created atomic_task_patterns table")

        print("\n=== Step 7: Create task_decomposition_history table ===")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS task_decomposition_history (
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
        print("✓ Created task_decomposition_history table")

        print("\n=== Step 8: Create task_predictions table ===")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS task_predictions (
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
        print("✓ Created task_predictions table")

        print("\n=== Step 9: Create cross_project_dependencies table ===")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cross_project_dependencies (
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
        print("✓ Created cross_project_dependencies table")

        print("\n=== Step 10: Create ai_analytics table ===")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_analytics (
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
        print("✓ Created ai_analytics table")

        print("\n=== Step 11: Create migration tracking table ===")
        cursor.execute(
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

        # Record this migration
        cursor.execute(
            """
            INSERT INTO schema_migrations
            (version, name, executed_at, backup_path, checksum)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                "001",
                "enhance_taskmaster_and_atomic_decomposition",
                "2025-12-02T17:08:00",
                "P:\\.speckit\\taskmaster\\tasks.db.backup_20251202_170800",
                "001_20251202",
            ),
        )
        print("✓ Created schema_migrations table and recorded migration")

        print("\n=== Step 12: Create basic indexes ===")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_automation_rules_ai_priority ON automation_rules(ai_priority_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_evidence_auto_generated ON evidence(auto_generated)",
            "CREATE INDEX IF NOT EXISTS idx_task_ai_complexity ON task(ai_complexity_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_tsk_compliance_score ON tsk(unified_compliance_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_atomic_patterns_type ON atomic_task_patterns(pattern_type)",
            "CREATE INDEX IF NOT EXISTS idx_decomp_history_task ON task_decomposition_history(original_task_id)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_task ON task_predictions(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_deps_source_tsk ON cross_project_dependencies(source_tsk)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_task ON ai_analytics(task_id)",
        ]

        for index in indexes:
            cursor.execute(index)
            print(f"✓ {index}")

        conn.commit()
        conn.close()

        print("\n=== Migration Complete! ===")
        print("✓ All tables enhanced and created successfully")
        print("✓ All indexes created")
        print("✓ Migration recorded in schema_migrations")

        return True

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        if "conn" in locals():
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        return False


if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
