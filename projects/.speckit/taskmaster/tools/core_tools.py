#!/usr/bin/env python3
"""
Core TaskMaster Tools

7 essential tools for task management.
Connects to existing TaskMaster database (db.py).

Author: Claude Code
Version: 1.0.0
"""

from __future__ import annotations

import logging
import sqlite3

# Import TaskMaster database module
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_connection

logger = logging.getLogger(__name__)


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a database row to a dictionary."""
    return dict(row) if row else {}


def get_tasks(
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
    order_by: str = 'created_at',
    order: str = 'DESC',
) -> list[dict[str, Any]]:
    """List tasks with optional filtering.

    Args:
        status: Filter by status ('pending', 'in_progress', 'completed')
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        order_by: Column to sort by
        order: Sort direction ('ASC' or 'DESC')

    Returns:
        List of task dictionaries

    Example:
        >>> tasks = get_tasks(status='pending', limit=10)
        >>> print(f"Found {len(tasks)} pending tasks")
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query
        query = "SELECT * FROM tasks"
        params = []

        if status:
            query += " WHERE status = ?"
            params.append(status)

        query += f" ORDER BY {order_by} {order}"
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        tasks = [_row_to_dict(row) for row in cursor.fetchall()]
        conn.close()

        logger.info(f"Retrieved {len(tasks)} tasks (status={status})")
        return tasks

    except sqlite3.Error as e:
        logger.error(f"Failed to retrieve tasks: {e}")
        return []


def next_task() -> dict[str, Any] | None:
    """Get the next pending task.

    Returns:
        Next pending task dictionary or None if no pending tasks

    Example:
        >>> task = next_task()
        >>> if task:
        ...     print(f"Next task: {task['title']}")
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            task = _row_to_dict(row)
            logger.info(f"Next task: {task['task_id']} - {task['title']}")
            return task

        logger.info("No pending tasks")
        return None

    except sqlite3.Error as e:
        logger.error(f"Failed to get next task: {e}")
        return None


def set_task_status(task_id: str, status: str) -> bool:
    """Update task status.

    Args:
        task_id: Task ID
        status: New status ('pending', 'in_progress', 'completed')

    Returns:
        True if successful, False otherwise

    Example:
        >>> success = set_task_status('TSK-123', 'in_progress')
    """
    valid_statuses = ('pending', 'in_progress', 'completed')
    if status not in valid_statuses:
        logger.warning(f"Invalid status: {status}. Valid: {valid_statuses}")
        return False

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE tasks SET status = ? WHERE task_id = ?",
            (status, task_id)
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected > 0:
            logger.info(f"Updated task {task_id} status to {status}")
            return True
        else:
            logger.warning(f"Task not found: {task_id}")
            return False

    except sqlite3.Error as e:
        logger.error(f"Failed to update task status: {e}")
        return False


def create_task(
    title: str,
    description: str | None = None,
    status: str = 'pending',
    context_type: str | None = None,
    source: str | None = None,
    source_id: str | None = None,
    prd_requirement_id: str | None = None,
) -> str | None:
    """Create a new task.

    Args:
        title: Task title
        description: Task description (stored as extended title for now)
        status: Initial status (default: 'pending')
        context_type: Context type (default: 'csf_nip')
        source: Source of task (e.g., 'prd', 'manual')
        source_id: Source identifier
        prd_requirement_id: PRD requirement ID if from PRD

    Returns:
        Created task ID or None if failed

    Example:
        >>> task_id = create_task(
        ...     title='Implement PRD parser',
        ...     description='Parse PRD.md files',
        ...     source='prd',
        ...     prd_requirement_id='FR-1'
        ... )
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Generate task_id if not provided
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        task_id = f"TSK-{timestamp}-{hash(title) % 10000:04d}"

        # Combine title and description if description provided
        full_title = title
        if description:
            full_title = f"{title}: {description}"

        cursor.execute(
            """INSERT INTO tasks
               (task_id, title, status, context_type, source, source_id, prd_requirement_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                task_id,
                full_title[:500],  # Limit title length
                status,
                context_type or 'csf_nip',
                source,
                source_id,
                prd_requirement_id
            )
        )
        conn.commit()
        conn.close()

        logger.info(f"Created task {task_id}: {title}")
        return task_id

    except sqlite3.Error as e:
        logger.error(f"Failed to create task: {e}")
        return None


def delete_task(task_id: str) -> bool:
    """Delete a task.

    Args:
        task_id: Task ID to delete

    Returns:
        True if successful, False otherwise

    Example:
        >>> success = delete_task('TSK-123')
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected > 0:
            logger.info(f"Deleted task {task_id}")
            return True
        else:
            logger.warning(f"Task not found: {task_id}")
            return False

    except sqlite3.Error as e:
        logger.error(f"Failed to delete task: {e}")
        return False


def expand_task(task_id: str) -> dict[str, Any] | None:
    """Expand task with additional details.

    Args:
        task_id: Task ID

    Returns:
        Expanded task dictionary with metadata or None

    Example:
        >>> task = expand_task('TSK-123')
        >>> if task:
        ...     print(f"Task: {task['title']}")
        ...     print(f"Source: {task.get('source', 'manual')}")
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            task = _row_to_dict(row)

            # Add PRD requirement info if linked
            if task.get('prd_requirement_id'):
                # Could fetch PRD details here
                task['prd_linked'] = True

            logger.info(f"Expanded task {task_id}")
            return task

        logger.warning(f"Task not found: {task_id}")
        return None

    except sqlite3.Error as e:
        logger.error(f"Failed to expand task: {e}")
        return None


def get_task(task_id: str) -> dict[str, Any] | None:
    """Get a single task by ID.

    Args:
        task_id: Task ID

    Returns:
        Task dictionary or None if not found

    Example:
        >>> task = get_task('TSK-123')
        >>> if task:
        ...     print(f"Task: {task['title']}")
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            task = _row_to_dict(row)
            logger.info(f"Retrieved task {task_id}")
            return task

        logger.warning(f"Task not found: {task_id}")
        return None

    except sqlite3.Error as e:
        logger.error(f"Failed to get task: {e}")
        return None


def search_tasks(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search tasks by title or task_id.

    Args:
        query: Search query string
        limit: Maximum results to return

    Returns:
        List of matching task dictionaries
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        search_pattern = f"%{query}%"
        cursor.execute(
            """SELECT * FROM tasks
               WHERE task_id LIKE ? OR title LIKE ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (search_pattern, search_pattern, limit)
        )
        tasks = [_row_to_dict(row) for row in cursor.fetchall()]
        conn.close()

        logger.info(f"Search for '{query}' found {len(tasks)} tasks")
        return tasks

    except sqlite3.Error as e:
        logger.error(f"Failed to search tasks: {e}")
        return []


def complete_task(task_id: str) -> bool:
    """Mark a task as completed.

    Args:
        task_id: Task ID to complete

    Returns:
        True if successful, False otherwise
    """
    return set_task_status(task_id, 'completed')


# Tool definitions for registry
TOOLS = {
    'get_tasks': get_tasks,
    'next_task': next_task,
    'set_task_status': set_task_status,
    'create_task': create_task,
    'delete_task': delete_task,
    'expand_task': expand_task,
    'get_task': get_task,
    'task_search': search_tasks,
    'task_complete': complete_task,
}

TOOL_NAMES = list(TOOLS.keys())


# Metadata for tool registry
TOOL_METADATA = {
    'get_tasks': {
        'description': 'List tasks with optional filtering',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 50,
    },
    'next_task': {
        'description': 'Get the next pending task',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 30,
    },
    'set_task_status': {
        'description': 'Update task status',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 40,
    },
    'create_task': {
        'description': 'Create a new task',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 60,
    },
    'delete_task': {
        'description': 'Delete a task',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 40,
    },
    'expand_task': {
        'description': 'Expand task with additional details',
        'category': 'core',
        'complexity': 'moderate',
        'token_cost': 100,
    },
    'get_task': {
        'description': 'Get a single task by ID',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 30,
    },
    'task_search': {
        'description': 'Search tasks by title or ID',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 50,
    },
    'task_complete': {
        'description': 'Mark a task as completed',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 40,
    },
}


def get_tool(tool_name: str):
    """Get a core tool by name.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool function or None
    """
    return TOOLS.get(tool_name)


def list_tools() -> dict[str, Any]:
    """List all core tools.

    Returns:
        Dictionary of tool_name -> tool_function
    """
    return TOOLS.copy()


def list_tool_names() -> list[str]:
    """List core tool names.

    Returns:
        List of tool names
    """
    return TOOL_NAMES.copy()
