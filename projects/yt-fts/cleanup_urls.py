"""Clean up malformed channel URLs with trailing whitespace."""
import sqlite3

from yt_fts.core.database import get_db_path

conn = sqlite3.connect(get_db_path())
cursor = conn.cursor()

# Find URLs with trailing tab
cursor.execute("SELECT rowid, channel_id, channel_url FROM Channels WHERE channel_url LIKE '%' || char(9)")
malformed = cursor.fetchall()

print(f"Found {len(malformed)} channel URLs with trailing tabs")
for rowid, channel_id, url in malformed:
    clean_url = url.rstrip()
    print(f"Fixing: {channel_id}")
    print(f"  Before: {url!r}")
    print(f"  After:  {clean_url!r}")
    cursor.execute("UPDATE Channels SET channel_url = ? WHERE rowid = ?", (clean_url, rowid))

conn.commit()
conn.close()
print("\n✓ Cleaned up malformed URLs")
