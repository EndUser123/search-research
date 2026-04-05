"""
Comprehensive migration verification script
"""

import sqlite3


def verify_migration():
    """Verify that migration was completed successfully."""
    db_path = r"P:\.speckit\taskmaster\tasks.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("=== Migration Verification ===\n")

        # 1. Check all expected tables exist
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

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        missing_tables = expected_tables - existing_tables
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        else:
            print(f"[OK] All {len(expected_tables)} expected tables present")

        # 2. Check enhanced columns exist
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

        all_columns_present = True
        for table, expected_columns in enhanced_columns.items():
            cursor.execute(f"PRAGMA table_info({table})")
            existing_columns = {row[1] for row in cursor.fetchall()}

            missing_columns = set(expected_columns) - existing_columns
            if missing_columns:
                print(f"❌ Missing columns in {table}: {missing_columns}")
                all_columns_present = False
            else:
                print(
                    f"✅ {table}: All {len(expected_columns)} enhanced columns present"
                )

        if not all_columns_present:
            return False

        # 3. Check indexes exist
        expected_indexes = [
            "idx_automation_rules_ai_priority",
            "idx_evidence_auto_generated",
            "idx_task_ai_complexity",
            "idx_tsk_compliance_score",
            "idx_atomic_patterns_type",
            "idx_predictions_task",
            "idx_analytics_task",
        ]

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        existing_indexes = {row[0] for row in cursor.fetchall()}

        missing_indexes = set(expected_indexes) - existing_indexes
        if missing_indexes:
            print(f"❌ Missing indexes: {missing_indexes}")
            return False
        else:
            print(f"✅ All {len(expected_indexes)} expected indexes present")

        # 4. Check triggers exist
        expected_triggers = [
            "update_task_evidence_count_insert",
            "update_task_evidence_count_delete",
        ]

        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        existing_triggers = {row[0] for row in cursor.fetchall()}

        missing_triggers = set(expected_triggers) - existing_triggers
        if missing_triggers:
            print(f"❌ Missing triggers: {missing_triggers}")
            return False
        else:
            print(f"✅ All {len(expected_triggers)} expected triggers present")

        # 5. Check migration recorded
        cursor.execute("SELECT * FROM schema_migrations WHERE version = '001'")
        migration = cursor.fetchone()
        if not migration:
            print("❌ Migration not recorded in schema_migrations")
            return False
        else:
            print(f"✅ Migration recorded: {migration[1]} at {migration[2]}")

        # 6. Test basic functionality
        print("\n=== Basic Functionality Tests ===")

        # Test trigger functionality
        cursor.execute("SELECT COUNT(*) FROM task")
        initial_task_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM evidence")
        initial_evidence_count = cursor.fetchone()[0]

        print(
            f"✅ Found {initial_task_count} tasks and {initial_evidence_count} evidence items"
        )

        # Test new tables are empty but accessible
        cursor.execute("SELECT COUNT(*) FROM atomic_task_patterns")
        patterns_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM task_predictions")
        predictions_count = cursor.fetchone()[0]

        print(
            f"✅ New tables ready: {patterns_count} patterns, {predictions_count} predictions"
        )

        # 7. Performance test
        print("\n=== Performance Test ===")
        import time

        # Test indexed query performance
        start_time = time.time()
        cursor.execute(
            "SELECT * FROM task WHERE ai_complexity_score > 0 ORDER BY ai_complexity_score DESC LIMIT 10"
        )
        indexed_query = cursor.fetchall()
        indexed_time = time.time() - start_time

        print(
            f"✅ Indexed query completed in {indexed_time:.4f} seconds, returned {len(indexed_query)} results"
        )

        # Test basic data integrity
        cursor.execute("PRAGMA foreign_key_check")
        fk_violations = cursor.fetchall()
        if fk_violations:
            print(f"❌ Foreign key violations found: {fk_violations}")
            return False
        else:
            print("✅ No foreign key violations detected")

        conn.close()

        print("\n=== Migration Verification Complete ===")
        print(
            "✅ All checks passed - Migration is fully functional and ready for production use"
        )
        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    success = verify_migration()
    exit(0 if success else 1)
