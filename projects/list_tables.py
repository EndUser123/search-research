import sqlite3

db_path = r"p:\projects\yt-fts\yt_fts.db"
print(f"Checking {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", [t[0] for t in cursor.fetchall()])
conn.close()
