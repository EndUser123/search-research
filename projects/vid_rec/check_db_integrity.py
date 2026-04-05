import sqlite3
import sys


def check_db_integrity(db_path):
    """Check SQLite database integrity and return results"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchall()
        conn.close()
        return result
    except sqlite3.Error as e:
        return [("ERROR", str(e))]


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "vidrec_state.db"
    results = check_db_integrity(db_path)

    print("Database Integrity Check Results:")
    for row in results:
        print(row[0])

    if any("error" in str(row).lower() for row in results):
        print("\n⚠️ Database integrity issues detected!")
        sys.exit(1)
    else:
        print("\n✅ Database integrity verified")
        sys.exit(0)
