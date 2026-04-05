#!/usr/bin/env python3
"""
TaskMaster Database - Centralized Module

Single source of truth for TaskMaster database access.
"""

import sqlite3
from pathlib import Path

# Canonical TaskMaster database location
TASKMASTER_DIR = Path("P:/.speckit/taskmaster")
TASKMASTER_DB = TASKMASTER_DIR / "tasks.db"
ACTIVE_PROJECT_FILE = TASKMASTER_DIR / "taskmaster_active_project.txt"


def get_connection() -> sqlite3.Connection:
    """
    Get TaskMaster database connection.

    Returns:
        sqlite3.Connection: Database connection

    Raises:
        FileNotFoundError: If database doesn't exist
    """
    if not TASKMASTER_DB.exists():
        raise FileNotFoundError(
            f"TaskMaster database not found at {TASKMASTER_DB}\n"
            f"Please ensure TaskMaster is properly initialized."
        )

    conn = sqlite3.connect(TASKMASTER_DB)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def get_db_path() -> Path:
    """Get TaskMaster database path"""
    return TASKMASTER_DB


def get_active_project() -> str | None:
    """
    Get currently active project ID.

    Returns:
        Project ID if active project set, None otherwise
    """
    if ACTIVE_PROJECT_FILE.exists():
        return ACTIVE_PROJECT_FILE.read_text().strip()
    return None


def set_active_project(project_id: str) -> None:
    """
    Set currently active project.

    Args:
        project_id: Project ID to set as active
    """
    TASKMASTER_DIR.mkdir(parents=True, exist_ok=True)
    ACTIVE_PROJECT_FILE.write_text(project_id)


def health_check() -> dict:
    """
    Perform health check on TaskMaster database.

    Returns:
        dict with health status information
    """
    status = {
        "db_exists": TASKMASTER_DB.exists(),
        "db_size": TASKMASTER_DB.stat().st_size if TASKMASTER_DB.exists() else 0,
        "dir_exists": TASKMASTER_DIR.exists(),
        "active_project": None,
    }

    if status["db_exists"]:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks")
            status["task_count"] = cursor.fetchone()[0]
            # Check if tm_projects table exists before querying
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tm_projects'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM tm_projects")
                status["project_count"] = cursor.fetchone()[0]
            else:
                status["project_count"] = 0
            conn.close()
            status["healthy"] = True
        except Exception as e:
            status["error"] = str(e)
            status["healthy"] = False
    else:
        status["healthy"] = False

    status["active_project"] = get_active_project()

    return status


if __name__ == "__main__":
    # Test database access
    health = health_check()
    print("TaskMaster Database Health Check:")
    print(f"  Database: {'✅' if health['db_exists'] else '❌'}")
    print(f"  Healthy: {'✅' if health.get('healthy') else '❌'}")
    print(f"  Tasks: {health.get('task_count', 0)}")
    print(f"  Projects: {health.get('project_count', 0)}")
    print(f"  Active Project: {health['active_project'] or 'None'}")
