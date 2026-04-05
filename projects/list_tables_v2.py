import os
import sqlite3

db_paths = [
    r"p:\projects\yt-fts\yt_fts.db",
    r"p:\projects\yt-fts\data\yt_fts.db",
    r"p:\projects\yt-fts\first.db",
]

for db_path in db_paths:
    print(f"\n--- Checking {db_path} ---")
    if not os.path.exists(db_path):
        print("Does not exist.")
        continue

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"Tables: {tables}")

        if "Channels" in tables:
            cursor.execute(
                "SELECT rowid, channel_name FROM Channels WHERE channel_name LIKE '%PythonProgrammer%'"
            )
            for row in cursor.fetchall():
                print(f"Found: {row}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
