#!/usr/bin/env python3
"""Add missing event_key column to tool_events table."""
import sqlite3

DB_PATH = r"P:\.claude\hooks\session_data\evidence.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("PRAGMA table_info(tool_events)")
    columns = [row[1] for row in cursor.fetchall()]

    if "event_key" not in columns:
        print("Adding event_key column to tool_events table...")
        conn.execute('ALTER TABLE tool_events ADD COLUMN event_key TEXT NOT NULL DEFAULT ""')
        conn.commit()
        print("Migration successful")
    else:
        print("Column event_key already exists")

    # Verify
    cursor = conn.execute("PRAGMA table_info(tool_events)")
    print("Updated schema:", [row[1] for row in cursor.fetchall()])

if __name__ == "__main__":
    migrate()
