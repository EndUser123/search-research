import os
import sqlite3

project_root = r"p:\projects\yt-fts"
found_dbs = []
for root, dirs, files in os.walk(project_root):
    for file in files:
        if file.endswith(".db"):
            found_dbs.append(os.path.join(root, file))

results = []
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

        results.append(
            {"path": path, "size": size, "tables": tables, "count": count, "row9": row9}
        )
        conn.close()
    except Exception as e:
        results.append({"path": path, "size": size, "error": str(e)})

for r in results:
    print(f"DB: {r['path']}")
    print(f"  Size: {r['size']} bytes")
    if "error" in r:
        print(f"  Error: {r['error']}")
    else:
        print(f"  Tables: {r['tables']}")
        if r["count"] != -1:
            print(f"  Channels Count: {r['count']}")
            print(f"  RowID 9: {r['row9']}")
    print("-" * 50)
