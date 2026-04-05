import sqlite3

conn = sqlite3.connect(r"p:\projects\yt-fts\data\subtitles.db")
c = conn.cursor()
c.execute("SELECT rowid, channel_id, channel_name FROM Channels LIMIT 20")
for r in c.fetchall():
    print(r)
conn.close()
