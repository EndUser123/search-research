"""
TaskMaster Database Migrations

Author: Claude Code
Version: 1.0.0
"""

from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / "tasks.db"

# Migration versions
MIGRATIONS = {
    "001": "enhance_taskmaster",
    "002": "add_prd_integration",
}


def get_db_path() -> Path:
    """Get the database path."""
    return DB_PATH


def list_migrations() -> list:
    """List all available migrations."""
    return list(MIGRATIONS.values())
