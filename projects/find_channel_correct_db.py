import os
import sqlite3

project_root = r"p:\projects\yt-fts"
channel_handle = "@PythonProgrammer"

for root, dirs, files in os.walk(project_root):
    for file in files:
        if file.endswith(".db"):
            db_path = os.path.join(root, file)
            print(f"\nScanning: {db_path}")
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [t[0] for t in cursor.fetchall()]
                print(f"  Tables: {tables}")

                # Check for standard tables
                for t_name in ["Channels", "channels"]:
                    if t_name in tables:
                        cursor.execute(
                            f"SELECT rowid, channel_name, channel_id FROM {t_name} WHERE channel_name LIKE ?",
                            (f"%{channel_handle}%",),
                        )
                        rows = cursor.fetchall()
                        if rows:
                            print(f"  *** FOUND IN {t_name} ***: {rows}")
                conn.close()
            except Exception as e:
                print(f"  Error: {e}")
