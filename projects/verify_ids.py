import sqlite3

conn = sqlite3.connect(r"p:\projects\yt-fts\data\subtitles.db")
c = conn.cursor()
ids = ["UC2sekS462J7_QCtcuy0uGxw", "UCX6OQ3DkcsbYNE6H8uQQuVA"]
for cid in ids:
    c.execute(
        "SELECT rowid, channel_id, channel_name FROM Channels WHERE channel_id = ?",
        (cid,),
    )
    print(f"ID {cid}: {c.fetchone()}")

c.execute(
    "SELECT rowid, channel_id, channel_name FROM Channels WHERE channel_name LIKE '%PythonProgrammer%'"
)
print(f"Name match: {c.fetchall()}")
conn.close()
