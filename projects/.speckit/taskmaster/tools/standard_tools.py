#!/usr/bin/env python3
"""
Standard Tools for TaskMaster

Additional tools for enhanced TaskMaster functionality.

Author: Claude Code
Version: 1.0.0
"""

from __future__ import annotations

from collections.abc import Callable

# Standard tool definitions
# These tools provide additional functionality beyond core

TOOL_NAMES: list[str] = [
    'task_tag',
    'task_priority',
    'task_assign',
    'task_link',
    'task_block',
    'task_dependent',
    'task_comment',
    'task_history',
]

TOOLS: dict[str, Callable] = {
    # Placeholder implementations
    'task_tag': lambda **kwargs: {'tags': []},
    'task_priority': lambda **kwargs: {'priority': 'normal'},
    'task_assign': lambda **kwargs: {'assigned': None},
    'task_link': lambda **kwargs: {'links': []},
    'task_block': lambda **kwargs: {'blocked_by': []},
    'task_dependent': lambda **kwargs: {'dependents': []},
    'task_comment': lambda **kwargs: {'comments': []},
    'task_history': lambda **kwargs: {'history': []},
}


def get_tool(tool_name: str) -> Callable | None:
    """Get a standard tool by name.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool function or None
    """
    return TOOLS.get(tool_name)


def list_tools() -> dict[str, Callable]:
    """List all standard tools.

    Returns:
        Dictionary of tool_name -> tool_function
    """
    return TOOLS.copy()


def list_tool_names() -> list[str]:
    """List standard tool names.

    Returns:
        List of tool names
    """
    return TOOL_NAMES.copy()
