import os
import sqlite3

project_root = r"p:\projects\yt-fts"
found_dbs = []
for root, dirs, files in os.walk(project_root):
    for file in files:
        if file.endswith(".db"):
            found_dbs.append(os.path.join(root, file))

for path in found_dbs:
    size = os.path.getsize(path)
    try:
        conn = sqlite3.connect(path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0].lower() for t in c.fetchall()]

        count = -1
        row9 = None

        if "channels" in tables:
            c.execute("SELECT count(*) FROM Channels")
            count = c.fetchone()[0]
            c.execute(
                "SELECT rowid, channel_id, channel_name FROM Channels WHERE rowid=9"
            )
            row9 = c.fetchone()

        print(f"DB: {path}")
        print(f"  Size: {size} bytes")
        print(f"  Tables: {tables}")
        if count != -1:
            print(f"  Channels Count: {count}")
            print(f"  RowID 9: {row9}")
        conn.close()
    except Exception as e:
        print(f"DB: {path} | Size: {size} | Error: {e}")
    print("-" * 30)
