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

with open("p:\\audit_results.txt", "w") as f:
    for r in results:
        f.write(f"DB: {r['path']}\n")
        f.write(f"  Size: {r['size']} bytes\n")
        if "error" in r:
            f.write(f"  Error: {r['error']}\n")
        else:
            f.write(f"  Tables: {r['tables']}\n")
            if r["count"] != -1:
                f.write(f"  Channels Count: {r['count']}\n")
                f.write(f"  RowID 9: {r['row9']}\n")
        f.write("-" * 50 + "\n")
