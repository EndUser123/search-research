#!/usr/bin/env python3
"""
Tool Registration Module for TaskMaster

Integrates core tools and PRD tools with the ToolRegistry.
Auto-registers all available tools on import.

Author: Claude Code
Version: 1.0.0
"""

from __future__ import annotations

import logging

from registry import get_tool_registry, register_tool

logger = logging.getLogger(__name__)


def register_core_tools() -> int:
    """Register all core task management tools with the ToolRegistry.

    Returns:
        Number of tools registered
    """
    # Import core tools
    from tools.core_tools import (
        complete_task,
        create_task,
        delete_task,
        expand_task,
        get_task,
        get_tasks,
        next_task,
        search_tasks,
        set_task_status,
    )

    tools_registered = 0

    # Register each core tool
    core_tools = [
        {
            'tool_id': 'get_tasks',
            'name': 'get_tasks',
            'description': 'List tasks with optional filtering by status, limit, offset',
            'function': get_tasks,
            'category': 'core',
            'complexity': 'simple',
            'token_cost': 50,
            'tags': ['read', 'list', 'filter'],
        },
        {
            'tool_id': 'next_task',
            'name': 'next_task',
            'description': 'Get the next pending task by creation time',
            'function': next_task,
            'category': 'core',
            'complexity': 'simple',
            'token_cost': 30,
            'tags': ['read', 'workflow'],
        },
        {
            'tool_id': 'set_task_status',
            'name': 'set_task_status',
            'description': 'Update task status (pending/in_progress/completed)',
            'function': set_task_status,
            'category': 'core',
            'complexity': 'simple',
            'token_cost': 40,
            'tags': ['write', 'status'],
        },
        {
            'tool_id': 'create_task',
            'name': 'create_task',
            'description': 'Create a new task with optional PRD traceability',
            'function': create_task,
            'category': 'core',
            'complexity': 'simple',
            'token_cost': 60,
            'tags': ['write', 'create'],
        },
        {
            'tool_id': 'delete_task',
            'name': 'delete_task',
            'description': 'Delete a task by task_id',
            'function': delete_task,
            'category': 'core',
            'complexity': 'simple',
            'token_cost': 40,
            'tags': ['write', 'delete'],
        },
        {
            'tool_id': 'expand_task',
            'name': 'expand_task',
            'description': 'Expand task with additional details and PRD link status',
            'function': expand_task,
            'category': 'core',
            'complexity': 'moderate',
            'token_cost': 100,
            'tags': ['read', 'details'],
        },
        {
            'tool_id': 'get_task',
            'name': 'get_task',
            'description': 'Get a single task by ID',
            'function': get_task,
            'category': 'core',
            'complexity': 'simple',
            'token_cost': 30,
            'tags': ['read'],
        },
        {
            'tool_id': 'search_tasks',
            'name': 'search_tasks',
            'description': 'Search tasks by title or task_id with pattern matching',
            'function': search_tasks,
            'category': 'core',
            'complexity': 'simple',
            'token_cost': 50,
            'tags': ['read', 'search'],
        },
        {
            'tool_id': 'complete_task',
            'name': 'complete_task',
            'description': 'Mark a task as completed',
            'function': complete_task,
            'category': 'core',
            'complexity': 'simple',
            'token_cost': 40,
            'tags': ['write', 'status'],
        },
    ]

    for tool_def in core_tools:
        try:
            if register_tool(**tool_def):
                tools_registered += 1
                logger.info(f"Registered core tool: {tool_def['tool_id']}")
        except Exception as e:
            logger.error(f"Failed to register {tool_def['tool_id']}: {e}")

    return tools_registered


def register_prd_tools() -> int:
    """Register all PRD-related tools with the ToolRegistry.

    Returns:
        Number of tools registered
    """
    # Import PRD tools
    from prd.cwo12_integration import cwo12_check_and_import, detect_prd
    from prd.importer import get_prd_status, import_prd, list_prds

    tools_registered = 0

    # PRD importer tools
    prd_tools = [
        {
            'tool_id': 'import_prd',
            'name': 'import_prd',
            'description': 'Import PRD requirements as TaskMaster tasks with full traceability',
            'function': import_prd,
            'category': 'standard',
            'complexity': 'moderate',
            'token_cost': 200,
            'tags': ['prd', 'import', 'write'],
        },
        {
            'tool_id': 'get_prd_status',
            'name': 'get_prd_status',
            'description': 'Get completion status for all requirements from a PRD',
            'function': get_prd_status,
            'category': 'standard',
            'complexity': 'moderate',
            'token_cost': 150,
            'tags': ['prd', 'read', 'status'],
        },
        {
            'tool_id': 'list_prds',
            'name': 'list_prds',
            'description': 'List all PRDs that have been imported with task counts',
            'function': list_prds,
            'category': 'standard',
            'complexity': 'simple',
            'token_cost': 50,
            'tags': ['prd', 'read', 'list'],
        },
        {
            'tool_id': 'detect_prd',
            'name': 'detect_prd',
            'description': 'Detect if current work has an associated PRD file',
            'function': detect_prd,
            'category': 'standard',
            'complexity': 'simple',
            'token_cost': 30,
            'tags': ['prd', 'detection'],
        },
        {
            'tool_id': 'cwo12_check_and_import',
            'name': 'cwo12_check_and_import',
            'description': 'CWO12 integration: auto-detect and import PRDs during workflow',
            'function': cwo12_check_and_import,
            'category': 'advanced',
            'complexity': 'moderate',
            'token_cost': 250,
            'tags': ['prd', 'cwo12', 'automation'],
        },
    ]

    for tool_def in prd_tools:
        try:
            if register_tool(**tool_def):
                tools_registered += 1
                logger.info(f"Registered PRD tool: {tool_def['tool_id']}")
        except Exception as e:
            logger.error(f"Failed to register {tool_def['tool_id']}: {e}")

    return tools_registered


def register_all_tools() -> dict:
    """Register all TaskMaster tools with the ToolRegistry.

    This is the main entry point for tool registration.
    Call this during application startup to ensure all tools are available.

    Returns:
        Dictionary with registration statistics
    """
    logger.info("Starting tool registration...")

    stats = {
        'core': 0,
        'prd': 0,
        'total': 0,
        'errors': []
    }

    # Register core tools
    try:
        stats['core'] = register_core_tools()
    except Exception as e:
        stats['errors'].append(f"Core tools: {e}")
        logger.error(f"Failed to register core tools: {e}")

    # Register PRD tools
    try:
        stats['prd'] = register_prd_tools()
    except Exception as e:
        stats['errors'].append(f"PRD tools: {e}")
        logger.error(f"Failed to register PRD tools: {e}")

    stats['total'] = stats['core'] + stats['prd']

    logger.info(f"Tool registration complete: {stats['total']} tools registered")

    if stats['errors']:
        logger.warning(f"Registration errors: {stats['errors']}")

    return stats


def get_registered_tool_ids(category: str | None = None) -> list[str]:
    """Get list of registered tool IDs.

    Args:
        category: Optional category filter ('core', 'standard', 'advanced')

    Returns:
        List of tool IDs
    """
    from registry import list_tools
    return list_tools(category=category or 'all')


def get_registry_summary() -> dict:
    """Get a summary of the tool registry state.

    Returns:
        Dictionary with registry summary
    """

    registry = get_tool_registry()
    stats = registry.get_statistics()

    # Add tool list by category
    summary = {
        'statistics': stats,
        'tools_by_category': {},
    }

    for category in ['core', 'standard', 'advanced']:
        tools = registry.list(category=category)
        summary['tools_by_category'][category] = [
            {'tool_id': t.tool_id, 'name': t.name}
            for t in tools
        ]

    return summary


# Auto-register on import (can be disabled with environment variable)
import os

if not os.getenv('TASKMASTER_SKIP_AUTO_REGISTER'):
    _registration_stats = register_all_tools()
else:
    logger.info("Skipping auto-registration (TASKMASTER_SKIP_AUTO_REGISTER set)")
    _registration_stats = None


__all__ = [
    'register_core_tools',
    'register_prd_tools',
    'register_all_tools',
    'get_registered_tool_ids',
    'get_registry_summary',
]
