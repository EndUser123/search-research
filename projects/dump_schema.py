import os
import sqlite3

db_path = r"p:\projects\yt-fts\data\yt_fts.db"
if not os.path.exists(db_path):
    print(f"File {db_path} does not exist.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
for name, sql in cursor.fetchall():
    print(f"\n--- Table: {name} ---")
    print(sql)

# Also check for rowid 9 again specifically in this DB
print("\n--- Checking rowid 9 in 'Channels' ---")
try:
    cursor.execute("SELECT rowid, * FROM Channels WHERE rowid=9")
    print(cursor.fetchone())
except Exception as e:
    print(f"Error checking rowid 9: {e}")

conn.close()
