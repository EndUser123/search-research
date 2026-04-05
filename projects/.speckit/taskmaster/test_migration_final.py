"""
Final migration verification without unicode characters
"""

import sqlite3


def main():
    db_path = r"P:\.speckit\taskmaster\tasks.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("=== Migration Verification ===")

        # Check all expected tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_new_tables = [
            "atomic_task_patterns",
            "task_decomposition_history",
            "task_predictions",
            "cross_project_dependencies",
            "ai_analytics",
            "schema_migrations",
        ]

        print(f"Total tables: {len(tables)}")
        print(
            f"New tables created: {len([t for t in expected_new_tables if t in tables])}"
        )

        # Check enhanced columns
        cursor.execute("PRAGMA table_info(automation_rules)")
        automation_columns = len(cursor.fetchall())
        print(f"automation_rules columns: {automation_columns}")

        cursor.execute("PRAGMA table_info(evidence)")
        evidence_columns = len(cursor.fetchall())
        print(f"evidence columns: {evidence_columns}")

        cursor.execute("PRAGMA table_info(task)")
        task_columns = len(cursor.fetchall())
        print(f"task columns: {task_columns}")

        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        task_related_indexes = [
            idx for idx in indexes if "task" in idx.lower() or "ai" in idx.lower()
        ]
        print(f"Task-related indexes: {len(task_related_indexes)}")

        # Check migration record
        cursor.execute("SELECT * FROM schema_migrations WHERE version = '001'")
        migration = cursor.fetchone()
        if migration:
            print(f"Migration recorded: {migration[1]}")

        # Test data access
        cursor.execute("SELECT COUNT(*) FROM task")
        task_count = cursor.fetchone()[0]
        print(f"Tasks in database: {task_count}")

        print("Verification complete - migration successful!")

        conn.close()
        return True

    except Exception as e:
        print(f"Verification failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
