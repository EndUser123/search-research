import sqlite3

conn = sqlite3.connect(r"p:\projects\yt-fts\data\subtitles.db")
c = conn.cursor()
c.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
for name, sql in c.fetchall():
    if name.lower() in ["channels", "videos", "subtitles"]:
        print(f"Table: {name}")
        print(f"SQL: {sql}")
        print("-" * 20)
conn.close()
