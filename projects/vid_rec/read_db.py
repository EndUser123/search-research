import sqlite3

db_path = "C:/_Python/_Projects/Vid_ReC/vidrec_state.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables in database: {tables}")

    cursor.execute("PRAGMA table_info(jobs);")
    columns = cursor.fetchall()
    print(f"Columns in 'jobs' table: {columns}")

    cursor.execute("SELECT * FROM jobs;")
    rows = cursor.fetchall()
    print(f"Rows in 'jobs' table: {rows}")

    conn.close()
except sqlite3.Error as e:
    print(f"Database error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
