"""CHS v2 Database Initialization CLI.

Initialize the CHS v2 database from schema.sql.

Usage:
    python -m core.chs.scripts.init_db
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    """Initialize database from schema.sql.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(description="Initialize CHS v2 database from schema")
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to database file (default: from CHS_DB_PATH env var or P:\\\\__csf/data/chat_history.db)",
    )
    parser.add_argument(
        "--schema-path",
        type=str,
        default=None,
        help="Path to schema.sql file (default: <script_dir>/../schema.sql)",
    )
    args = parser.parse_args()
    script_dir = Path(__file__).parent
    if args.schema_path:
        schema_path = Path(args.schema_path).expanduser()
    else:
        schema_path = script_dir.parent / "schema.sql"
    if not schema_path.exists():
        print(f"ERROR: schema.sql not found at {schema_path}", file=sys.stderr)
        return 1
    if args.db_path:
        db_path = Path(args.db_path).expanduser()
    else:
        import os

        db_path = Path(os.getenv("CHS_DB_PATH", "P:\\\\__csf/data/chat_history.db")).expanduser()
    try:
        from core.chs.db import get_connection

        schema_sql = schema_path.read_text()
        conn = get_connection(db_path)
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        print(f"Database initialized successfully at: {db_path}")
        return 0
    except Exception as e:
        print(f"ERROR: Failed to initialize database: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
