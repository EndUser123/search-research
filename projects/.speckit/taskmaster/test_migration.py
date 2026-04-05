"""
Simplified test migration to debug issues
"""

import sqlite3


def test_migration():
    db_path = r"P:\.speckit\taskmaster\tasks.db"

    try:
        print("Connecting to database...")
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")

        print("Connection successful")

        cursor = conn.cursor()

        # Test enhancement
        print("Testing table enhancement...")
        try:
            cursor.execute(
                "ALTER TABLE automation_rules ADD COLUMN test_column TEXT DEFAULT 'test'"
            )
            print("Enhancement successful")
            cursor.execute("ALTER TABLE automation_rules DROP COLUMN test_column")
            print("Cleanup successful")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Column already exists - expected")
            else:
                print(f"Enhancement error: {e}")

        # Test new table creation
        print("Testing new table creation...")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS test_table (
                id TEXT PRIMARY KEY,
                test_field TEXT
            )
        """
        )
        print("New table creation successful")

        # Cleanup
        cursor.execute("DROP TABLE IF EXISTS test_table")
        print("Cleanup successful")

        conn.commit()
        conn.close()

        print("All tests passed!")
        return True

    except Exception as e:
        print(f"Migration test failed: {e}")
        return False


if __name__ == "__main__":
    test_migration()
