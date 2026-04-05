import os
import sqlite3

db_path = os.path.join("projects", "yt-fts", "yt_fts.db")
print(f"Checking {db_path} (exists: {os.path.exists(db_path)})")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
for name, sql in cursor.fetchall():
    print(f"\n--- Table: {name} ---")
    print(sql)
conn.close()
