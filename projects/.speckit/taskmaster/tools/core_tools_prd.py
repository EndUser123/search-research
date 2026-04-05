#!/usr/bin/env python3
"""
PRD-Enhanced Core TaskMaster Tools

7 essential tools with PRD integration for intelligent task management.
Extends core_tools.py with PRD-aware functionality.

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

# Import PRD integration
sys.path.insert(0, str(Path(__file__).parent.parent / "prd"))
from integration import PRDIntegration, create_prd_integration
from registry import PRDRegistry

logger = logging.getLogger(__name__)


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a database row to a dictionary."""
    return dict(row) if row else {}


# Global PRD integration instance
_prd_integration: PRDIntegration | None = None


def initialize_prd_integration(
    prd_paths: list[str] | None = None,
    cache_size: int = 50
) -> PRDIntegration:
    """Initialize PRD integration for tools.

    Args:
        prd_paths: List of glob patterns to find PRD files
        cache_size: Maximum PRDs to cache

    Returns:
        PRDIntegration instance
    """
    global _prd_integration

    if _prd_integration is None:
        # Default PRD paths
        if prd_paths is None:
            prd_paths = [
                r"P:/projects/*/docs/PRD.md",
                r"P:/projects/*/PRD.md",
            ]

        # Create registry
        registry = PRDRegistry(
            prd_paths=prd_paths,
            cache_size=cache_size,
            ttl_seconds=3600,
            enable_file_watching=True,
        )

        # Discover PRDs
        registry.discover()

        # Create integration
        _prd_integration = create_prd_integration(registry)

        logger.info(f"Initialized PRD integration with {len(registry.list_prds())} PRDs")

    return _prd_integration


def get_prd_integration() -> PRDIntegration | None:
    """Get the global PRD integration instance."""
    return _prd_integration


# ============================================================================
# TOOL 1: create_task - PRD-aware task creation with requirement validation
# ============================================================================

def create_task(
    title: str,
    description: str | None = None,
    status: str = 'pending',
    context_type: str | None = None,
    source: str | None = None,
    source_id: str | None = None,
    prd_requirement_id: str | None = None,
    prd_name: str | None = None,
    validate_prd: bool = True,
) -> str | None:
    """Create a new task with optional PRD integration.

    Args:
        title: Task title
        description: Task description
        status: Initial status (default: 'pending')
        context_type: Context type (default: 'csf_nip')
        source: Source of task (e.g., 'prd', 'manual')
        source_id: Source identifier
        prd_requirement_id: PRD requirement ID if from PRD
        prd_name: PRD name (required if prd_requirement_id provided)
        validate_prd: Whether to validate PRD requirement exists

    Returns:
        Created task ID or None if failed

    Example:
        >>> # Create task linked to PRD requirement
        >>> task_id = create_task(
        ...     title='Implement user authentication',
        ...     prd_name='my_app',
        ...     prd_requirement_id='FR-1',
        ...     validate_prd=True
        ... )
    """
    try:
        # PRD validation and enrichment
        if prd_name and prd_requirement_id and validate_prd:
            integration = get_prd_integration()
            if integration:
                if not integration.validate_requirement(prd_name, prd_requirement_id):
                    logger.error(
                        f"Invalid PRD requirement: {prd_name}/{prd_requirement_id}"
                    )
                    return None

                # Enrich description with requirement context
                req = integration.get_requirement(prd_name, prd_requirement_id)
                if req:
                    req_desc = f"PRD Requirement: {req['id']} - {req['title']}\n{req['description']}"
                    if description:
                        description = f"{description}\n\n{req_desc}"
                    else:
                        description = req_desc

                    logger.info(f"Linked task to PRD requirement: {prd_name}/{prd_requirement_id}")

        conn = get_connection()
        cursor = conn.cursor()

        # Generate task_id
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        task_id = f"TSK-{timestamp}-{hash(title) % 10000:04d}"

        # Combine title and description
        full_title = title
        if description:
            full_title = f"{title}: {description}"

        # Determine source
        if source is None:
            source = 'prd' if prd_name else 'manual'

        cursor.execute(
            """INSERT INTO tasks
               (task_id, title, status, context_type, source, source_id, prd_requirement_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                task_id,
                full_title[:500],
                status,
                context_type or 'csf_nip',
                source,
                source_id or (f"{prd_name}:{prd_requirement_id}" if prd_name and prd_requirement_id else None),
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


# ============================================================================
# TOOL 2: get_task - Retrieve task with PRD requirement details
# ============================================================================

def get_task(task_id: str, include_prd_context: bool = False) -> dict[str, Any] | None:
    """Get a single task by ID with optional PRD context.

    Args:
        task_id: Task ID
        include_prd_context: Whether to include PRD requirement details

    Returns:
        Task dictionary or None if not found

    Example:
        >>> task = get_task('TSK-123', include_prd_context=True)
        >>> if task:
        ...     print(f"Task: {task['title']}")
        ...     if task.get('prd_context'):
        ...         print(f"PRD: {task['prd_context']['requirement']['title']}")
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

            # Add PRD context if requested and available
            if include_prd_context and task.get('prd_requirement_id'):
                integration = get_prd_integration()
                if integration and task.get('source'):
                    # Extract PRD name from source_id or task metadata
                    prd_name = _extract_prd_name(task)
                    if prd_name:
                        context = integration.get_requirement_context(
                            prd_name,
                            task['prd_requirement_id']
                        )
                        if context:
                            task['prd_context'] = context

            logger.info(f"Retrieved task {task_id}")
            return task

        logger.warning(f"Task not found: {task_id}")
        return None

    except sqlite3.Error as e:
        logger.error(f"Failed to get task: {e}")
        return None


def _extract_prd_name(task: dict[str, Any]) -> str | None:
    """Extract PRD name from task metadata."""
    # Try source_id first (format: "prd_name:req_id")
    if task.get('source_id'):
        parts = task['source_id'].split(':')
        if len(parts) >= 2:
            return parts[0]

    # Try to infer from other metadata
    return None


# ============================================================================
# TOOL 3: get_tasks - List tasks with PRD filtering
# ============================================================================

def get_tasks(
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
    order_by: str = 'created_at',
    order: str = 'DESC',
    prd_name: str | None = None,
    prd_requirement_id: str | None = None,
) -> list[dict[str, Any]]:
    """List tasks with optional filtering and PRD filters.

    Args:
        status: Filter by status ('pending', 'in_progress', 'completed')
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        order_by: Column to sort by
        order: Sort direction ('ASC' or 'DESC')
        prd_name: Filter by PRD name
        prd_requirement_id: Filter by PRD requirement ID

    Returns:
        List of task dictionaries

    Example:
        >>> # Get all tasks for a PRD
        >>> tasks = get_tasks(prd_name='my_app', limit=50)

        >>> # Get tasks for a specific requirement
        >>> tasks = get_tasks(prd_requirement_id='FR-1')
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if prd_requirement_id:
            query += " AND prd_requirement_id = ?"
            params.append(prd_requirement_id)

        if prd_name:
            # Filter by source_id containing PRD name
            query += " AND source_id LIKE ?"
            params.append(f"{prd_name}:%")

        query += f" ORDER BY {order_by} {order}"
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        tasks = [_row_to_dict(row) for row in cursor.fetchall()]
        conn.close()

        logger.info(
            f"Retrieved {len(tasks)} tasks "
            f"(status={status}, prd={prd_name}, req={prd_requirement_id})"
        )
        return tasks

    except sqlite3.Error as e:
        logger.error(f"Failed to retrieve tasks: {e}")
        return []


# ============================================================================
# TOOL 4: expand_task - Expand task with full PRD context
# ============================================================================

def expand_task(
    task_id: str,
    include_related: bool = True
) -> dict[str, Any] | None:
    """Expand task with full PRD context and related information.

    Args:
        task_id: Task ID
        include_related: Whether to include related requirements

    Returns:
        Expanded task dictionary with metadata or None

    Example:
        >>> task = expand_task('TSK-123')
        >>> if task:
        ...     print(f"Task: {task['title']}")
        ...     if task.get('prd_context'):
        ...         req = task['prd_context']['requirement']
        ...         print(f"Requirement: {req['title']}")
        ...         print(f"Priority: {req['priority']}")
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
                integration = get_prd_integration()
                if integration:
                    prd_name = _extract_prd_name(task)
                    if prd_name:
                        # Get full requirement context
                        context = integration.get_requirement_context(
                            prd_name,
                            task['prd_requirement_id']
                        )

                        if context:
                            task['prd_context'] = context
                            task['prd_linked'] = True

                            # Add related requirements if requested
                            if include_related and context.get('related_requirements'):
                                task['related_requirements'] = context['related_requirements']

                            # Add PRD summary
                            prd_summary = integration.get_prd_summary(prd_name)
                            if prd_summary:
                                task['prd_summary'] = prd_summary

            logger.info(f"Expanded task {task_id}")
            return task

        logger.warning(f"Task not found: {task_id}")
        return None

    except sqlite3.Error as e:
        logger.error(f"Failed to expand task: {e}")
        return None


# ============================================================================
# TOOL 5: search_tasks - Search tasks with requirement search
# ============================================================================

def search_tasks(
    query: str,
    limit: int = 20,
    search_prd_requirements: bool = False
) -> list[dict[str, Any]]:
    """Search tasks by title, task_id, or PRD requirements.

    Args:
        query: Search query string
        limit: Maximum results to return
        search_prd_requirements: Whether to search PRD requirements too

    Returns:
        List of matching task dictionaries

    Example:
        >>> # Search in task titles
        >>> tasks = search_tasks('authentication')

        >>> # Search in both tasks and PRD requirements
        >>> tasks = search_tasks('API', search_prd_requirements=True)
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

        # Optionally search PRD requirements
        if search_prd_requirements:
            integration = get_prd_integration()
            if integration:
                req_results = integration.search_requirements(query, limit=limit)

                # Find tasks linked to matching requirements
                for prd_name, req_id, req_title in req_results:
                    # Check if we already have tasks for this requirement
                    req_tasks = get_tasks(prd_requirement_id=req_id, limit=5)

                    for task in req_tasks:
                        # Add requirement info to task
                        if not any(t['task_id'] == task['task_id'] for t in tasks):
                            task['matched_requirement'] = {
                                'prd_name': prd_name,
                                'requirement_id': req_id,
                                'requirement_title': req_title,
                            }
                            tasks.append(task)

                            if len(tasks) >= limit:
                                break

                    if len(tasks) >= limit:
                        break

        return tasks

    except sqlite3.Error as e:
        logger.error(f"Failed to search tasks: {e}")
        return []


# ============================================================================
# TOOL 6: next_task - Get next pending task with PRD prioritization
# ============================================================================

def next_task(
    prd_name: str | None = None,
    prioritize_by_prd: bool = False
) -> dict[str, Any] | None:
    """Get the next pending task with optional PRD-based prioritization.

    Args:
        prd_name: Filter to specific PRD
        prioritize_by_prd: Whether to prioritize by PRD requirement priority

    Returns:
        Next pending task dictionary or None if no pending tasks

    Example:
        >>> # Get next task (oldest first)
        >>> task = next_task()

        >>> # Get next high-priority task from PRD
        >>> task = next_task(prioritize_by_prd=True)
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if prioritize_by_prd:
            # Get pending tasks linked to PRDs
            query = """
                SELECT * FROM tasks
                WHERE status = 'pending' AND prd_requirement_id IS NOT NULL
            """
            params = []

            if prd_name:
                query += " AND source_id LIKE ?"
                params.append(f"{prd_name}:%")

            cursor.execute(f"{query} LIMIT 50")  # Get candidates
            candidates = [_row_to_dict(row) for row in cursor.fetchall()]
            conn.close()

            if not candidates:
                # Fall back to non-PRD tasks
                return next_task(prd_name=prd_name, prioritize_by_prd=False)

            # Prioritize by PRD requirement priority
            integration = get_prd_integration()
            if integration:
                # Score tasks based on requirement priority
                scored_tasks = []
                for task in candidates:
                    prd_name_task = _extract_prd_name(task)
                    if prd_name_task and task.get('prd_requirement_id'):
                        req = integration.get_requirement(
                            prd_name_task,
                            task['prd_requirement_id']
                        )
                        if req:
                            # Calculate priority score
                            priority_score = _calculate_priority_score(req)

                            # Add creation time factor (older = higher priority)
                            created_time = datetime.fromisoformat(task['created_at'])
                            age_hours = (datetime.now() - created_time).total_seconds() / 3600
                            age_score = min(age_hours / 24, 10)  # Max 10 points for age

                            total_score = priority_score + age_score
                            scored_tasks.append((task, total_score))

                # Sort by score (descending)
                scored_tasks.sort(key=lambda x: x[1], reverse=True)

                if scored_tasks:
                    task = scored_tasks[0][0]
                    logger.info(
                        f"Next task (PRD-prioritized): {task['task_id']} - {task['title']}"
                    )
                    return task

            # Fall back to first candidate
            if candidates:
                task = candidates[0]
                logger.info(f"Next task: {task['task_id']} - {task['title']}")
                return task

            return None

        else:
            # Standard next task (oldest first)
            query = "SELECT * FROM tasks WHERE status = 'pending'"
            params = []

            if prd_name:
                query += " AND source_id LIKE ?"
                params.append(f"{prd_name}:%")

            query += " ORDER BY created_at ASC LIMIT 1"

            cursor.execute(query, params)
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


def _calculate_priority_score(req: dict[str, Any]) -> int:
    """Calculate priority score for a requirement."""
    score = 0

    # Priority mapping
    priority_map = {
        'critical': 100,
        'high': 75,
        'medium': 50,
        'low': 25,
    }

    priority = req.get('priority') or 'medium'
    if isinstance(priority, str):
        priority = priority.lower()
    score += priority_map.get(priority, 50)

    # Functional requirements get slight boost
    if req.get('type') == 'functional':
        score += 10

    return score


# ============================================================================
# TOOL 7: set_task_status - Update status with requirement tracking
# ============================================================================

def set_task_status(
    task_id: str,
    status: str,
    track_requirement_progress: bool = True
) -> bool:
    """Update task status with optional PRD requirement progress tracking.

    Args:
        task_id: Task ID
        status: New status ('pending', 'in_progress', 'completed')
        track_requirement_progress: Whether to update requirement progress

    Returns:
        True if successful, False otherwise

    Example:
        >>> # Update status and track requirement progress
        >>> success = set_task_status('TSK-123', 'completed', track_requirement_progress=True)
    """
    valid_statuses = ('pending', 'in_progress', 'completed')
    if status not in valid_statuses:
        logger.warning(f"Invalid status: {status}. Valid: {valid_statuses}")
        return False

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get current task data
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            logger.warning(f"Task not found: {task_id}")
            return False

        old_status = row['status']
        prd_requirement_id = row['prd_requirement_id']

        # Update status
        cursor.execute(
            "UPDATE tasks SET status = ? WHERE task_id = ?",
            (status, task_id)
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected > 0:
            logger.info(f"Updated task {task_id} status: {old_status} -> {status}")

            # Track requirement progress
            if track_requirement_progress and prd_requirement_id and status == 'completed':
                _track_requirement_completion(task_id, prd_requirement_id)

            return True
        else:
            logger.warning(f"Task not found: {task_id}")
            return False

    except sqlite3.Error as e:
        logger.error(f"Failed to update task status: {e}")
        return False


def _track_requirement_completion(task_id: str, requirement_id: str) -> None:
    """Track completion of a PRD requirement.

    This is a placeholder for future enhancement where we could:
    - Maintain requirement completion counts
    - Update PRD metadata with completion status
    - Trigger notifications for requirement completion
    """
    integration = get_prd_integration()
    if not integration:
        return

    # Log requirement completion
    logger.info(f"Requirement {requirement_id} completed by task {task_id}")

    # Future: Update requirement tracking in PRD registry
    # Future: Check if all tasks for requirement are complete


# ============================================================================
# Convenience functions
# ============================================================================

def complete_task(task_id: str) -> bool:
    """Mark a task as completed.

    Args:
        task_id: Task ID to complete

    Returns:
        True if successful, False otherwise
    """
    return set_task_status(task_id, 'completed', track_requirement_progress=True)


def delete_task(task_id: str) -> bool:
    """Delete a task.

    Args:
        task_id: Task ID to delete

    Returns:
        True if successful, False otherwise
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


# ============================================================================
# Tool metadata and exports
# ============================================================================

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
        'description': 'List tasks with optional filtering and PRD filters',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 50,
        'prd_aware': True,
    },
    'next_task': {
        'description': 'Get the next pending task with PRD prioritization',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 30,
        'prd_aware': True,
    },
    'set_task_status': {
        'description': 'Update task status with requirement progress tracking',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 40,
        'prd_aware': True,
    },
    'create_task': {
        'description': 'Create a new task with PRD requirement validation',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 60,
        'prd_aware': True,
    },
    'delete_task': {
        'description': 'Delete a task',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 40,
        'prd_aware': False,
    },
    'expand_task': {
        'description': 'Expand task with full PRD context and related requirements',
        'category': 'core',
        'complexity': 'moderate',
        'token_cost': 100,
        'prd_aware': True,
    },
    'get_task': {
        'description': 'Get a single task by ID with PRD context',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 30,
        'prd_aware': True,
    },
    'task_search': {
        'description': 'Search tasks by title, ID, or PRD requirements',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 50,
        'prd_aware': True,
    },
    'task_complete': {
        'description': 'Mark a task as completed with requirement tracking',
        'category': 'core',
        'complexity': 'simple',
        'token_cost': 40,
        'prd_aware': True,
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


def list_prd_aware_tools() -> list[str]:
    """List tools that are PRD-aware.

    Returns:
        List of PRD-aware tool names
    """
    return [
        name for name, meta in TOOL_METADATA.items()
        if meta.get('prd_aware', False)
    ]
