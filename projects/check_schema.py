import sqlite3

db_path = "projects/yt-fts/yt_fts.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute(
    "SELECT sql FROM sqlite_master WHERE name IN ('Subtitles', 'Subtitles_fts')"
)
for row in cursor.fetchall():
    print(row[0])
conn.close()
