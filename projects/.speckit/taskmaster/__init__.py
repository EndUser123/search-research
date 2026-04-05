"""
TaskMaster - Unified Task Management System

Canonical location for all TaskMaster functionality.
"""

from .db import (
    get_active_project,
    get_connection,
    get_db_path,
    health_check,
    set_active_project,
)

__all__ = [
    "get_connection",
    "get_db_path",
    "get_active_project",
    "set_active_project",
    "health_check",
]
