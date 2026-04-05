import os
import sqlite3

db_paths = ["projects/yt-fts/yt_fts.db", "projects/yt-fts/data/yt_fts.db"]

for db_path in db_paths:
    if not os.path.exists(db_path):
        print(f"\n--- Database not found at {db_path} ---")
        continue

    print(f"\n--- Checking {db_path} ---")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"Tables: {tables}")

        if "Channels" in tables or "channels" in tables:
            t_name = "Channels" if "Channels" in tables else "channels"
            print(f"Querying table: {t_name}")
            cursor.execute(
                f"SELECT rowid, channel_id, channel_name, channel_url FROM {t_name} WHERE channel_name LIKE '%PythonProgrammer%'"
            )
            for row in cursor.fetchall():
                print(f"Found by name: {row}")

            print("\nRowID 9 check:")
            cursor.execute(
                f"SELECT rowid, channel_id, channel_name, channel_url FROM {t_name} WHERE rowid = 9"
            )
            for row in cursor.fetchall():
                print(f"Found by rowid 9: {row}")
        else:
            print("No channels table found.")
    except Exception as e:
        print(f"Error checking {db_path}: {e}")

    conn.close()
