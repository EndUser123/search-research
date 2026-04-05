"""Add missing columns to Videos table."""
import sqlite3
import sys
sys.path.insert(0, 'src')
from yt_fts.utils.config import get_db_path

db_path = get_db_path()
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Add missing columns
migrations = [
    'ALTER TABLE Videos ADD COLUMN duration INTEGER DEFAULT 0',
    'ALTER TABLE Videos ADD COLUMN thumbnail_url TEXT DEFAULT ""',
    'ALTER TABLE Videos ADD COLUMN view_count INTEGER DEFAULT 0',
    'ALTER TABLE Videos ADD COLUMN is_short INTEGER DEFAULT 0',
]

for migration in migrations:
    try:
        cur.execute(migration)
        print(f'Applied: {migration}')
    except sqlite3.OperationalError as e:
        if 'duplicate column' in str(e).lower():
            print(f'Skipped (already exists): {migration[:50]}...')
        else:
            print(f'Error: {e}')

conn.commit()
conn.close()
print('Done')
