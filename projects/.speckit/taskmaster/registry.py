#!/usr/bin/env python3
"""
Tool Registry for TaskMaster

Adapted from QuadletRegistry (CSF NIP)
Provides CRUD operations for tool definitions with in-memory caching.

Author: Claude Code
Version: 1.0.0
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of a TaskMaster tool."""
    tool_id: str
    name: str
    description: str
    category: str  # 'core', 'standard', 'advanced'
    complexity: str  # 'simple', 'moderate', 'complex'
    function: Callable
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    token_cost: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class ToolValidationError(Exception):
    """Raised when tool validation fails."""


class ToolDependencyError(Exception):
    """Raised when tool dependency resolution fails."""


class ToolRegistry:
    """
    Registry for managing TaskMaster tools with caching.

    Provides:
    - In-memory caching for fast access
    - CRUD operations for tool definitions
    - Dependency tracking and resolution
    - Mode-based tool listing (core/standard/all)
    """

    def __init__(self):
        """Initialize the tool registry."""
        self.logger = logging.getLogger(__name__)

        # In-memory cache
        self._cache: dict[str, ToolDefinition] = {}
        self._dependencies: dict[str, list[str]] = {}
        self._reverse_dependencies: dict[str, set] = {}

        # Thread safety
        self._lock = threading.RLock()

        # Cache statistics
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_operations = 0

        self.logger.info("ToolRegistry initialized")

    def register(self, tool: ToolDefinition, validate: bool = True) -> bool:
        """
        Register a new tool definition.

        Args:
            tool: The tool definition to register
            validate: Whether to validate the tool before registration

        Returns:
            True if registration successful, False otherwise

        Raises:
            ToolValidationError: If validation fails and validate=True
        """
        if validate:
            self._validate_tool(tool)

        with self._lock:
            self._total_operations += 1

            # Check if tool already exists
            if tool.tool_id in self._cache:
                existing = self._cache[tool.tool_id]
                if tool.updated_at <= existing.updated_at:
                    self.logger.warning(f"Tool {tool.name} already exists with newer version")
                    return False

            # Add to cache
            self._cache[tool.tool_id] = tool
            tool.updated_at = datetime.now()

            # Update dependencies
            self._update_dependencies(tool)

            self.logger.info(f"Registered tool: {tool.name} ({tool.tool_id})")
            return True

    def get(self, tool_id: str) -> ToolDefinition | None:
        """
        Get a tool definition by ID.

        Args:
            tool_id: The ID of the tool to retrieve

        Returns:
            The tool definition if found, None otherwise
        """
        with self._lock:
            self._total_operations += 1

            if tool_id in self._cache:
                self._cache_hits += 1
                return self._cache[tool_id]

            self._cache_misses += 1
            return None

    def get_by_name(self, name: str) -> ToolDefinition | None:
        """
        Get a tool definition by name.

        Args:
            name: The name of the tool to retrieve

        Returns:
            The tool definition if found, None otherwise
        """
        with self._lock:
            for tool in self._cache.values():
                if tool.name == name:
                    self._cache_hits += 1
                    return tool

            self._cache_misses += 1
            return None

    def list(self,
             category: str | None = None,
             tags: list[str] | None = None,
             limit: int | None = None) -> list[ToolDefinition]:
        """
        List tool definitions with optional filtering.

        Args:
            category: Filter by category ('core', 'standard', 'advanced')
            tags: Filter by tags (must match all provided tags)
            limit: Maximum number of results to return

        Returns:
            List of matching tool definitions
        """
        with self._lock:
            self._total_operations += 1
            results = []

            # Filter from cache
            for tool in self._cache.values():
                if category and tool.category != category:
                    continue
                if tags and not all(tag in tool.tags for tag in tags):
                    continue

                results.append(tool)

            # Apply limit
            if limit:
                results = results[:limit]

            return results

    def update(self, tool: ToolDefinition, validate: bool = True) -> bool:
        """
        Update an existing tool definition.

        Args:
            tool: The updated tool definition
            validate: Whether to validate the tool before update

        Returns:
            True if update successful, False otherwise

        Raises:
            ToolValidationError: If validation fails and validate=True
        """
        if validate:
            self._validate_tool(tool)

        with self._lock:
            self._total_operations += 1

            # Check if tool exists
            if tool.tool_id not in self._cache:
                self.logger.warning(f"Tool {tool.tool_id} not found for update")
                return False

            # Update in cache
            tool.updated_at = datetime.now()
            self._cache[tool.tool_id] = tool

            # Update dependencies
            self._clear_dependencies(tool.tool_id)
            self._update_dependencies(tool)

            self.logger.info(f"Updated tool: {tool.name} ({tool.tool_id})")
            return True

    def delete(self, tool_id: str) -> bool:
        """
        Delete a tool definition.

        Args:
            tool_id: The ID of the tool to delete

        Returns:
            True if deletion successful, False otherwise
        """
        with self._lock:
            self._total_operations += 1

            # Check if tool exists
            if tool_id not in self._cache:
                self.logger.warning(f"Tool {tool_id} not found for deletion")
                return False

            # Check for dependent tools
            if tool_id in self._reverse_dependencies:
                dependents = self._reverse_dependencies[tool_id]
                if dependents:
                    self.logger.error(f"Cannot delete tool {tool_id}: has dependents {dependents}")
                    return False

            # Remove from cache
            del self._cache[tool_id]
            self._clear_dependencies(tool_id)

            self.logger.info(f"Deleted tool: {tool_id}")
            return True

    def resolve_dependencies(self, tool_id: str) -> list[str]:
        """
        Resolve and validate dependencies for a tool.

        Args:
            tool_id: The ID of the tool

        Returns:
            List of resolved dependency tool IDs

        Raises:
            ToolDependencyError: If dependency resolution fails
        """
        with self._lock:
            self._total_operations += 1

            if tool_id not in self._cache:
                raise ToolDependencyError(f"Tool {tool_id} not found")

            tool = self._cache[tool_id]
            resolved_deps = []

            for dep_name in tool.dependencies:
                # Find dependency by name or ID
                dep_tool = self.get(dep_name) or self.get_by_name(dep_name)

                if not dep_tool:
                    raise ToolDependencyError(f"Dependency {dep_name} not found")

                resolved_deps.append(dep_tool.tool_id)

            return resolved_deps

    def get_statistics(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry statistics
        """
        with self._lock:
            total_tools = len(self._cache)
            by_category = {}
            for tool in self._cache.values():
                category_name = tool.category
                by_category[category_name] = by_category.get(category_name, 0) + 1

            cache_hit_rate = (
                self._cache_hits / (self._cache_hits + self._cache_misses) * 100
                if (self._cache_hits + self._cache_misses) > 0 else 0
            )

            return {
                "total_tools": total_tools,
                "by_category": by_category,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_hit_rate_percent": round(cache_hit_rate, 2),
                "total_operations": self._total_operations,
                "dependency_count": len(self._dependencies),
            }

    def get_tools_by_mode(self, mode: str = 'all') -> list[ToolDefinition]:
        """
        Get tools by loading mode.

        Args:
            mode: 'core' (core tools), 'standard' (core+standard), 'all' (all tools)

        Returns:
            List of tool definitions for the mode
        """
        with self._lock:
            if mode == 'core':
                return self.list(category='core')
            elif mode == 'standard':
                return self.list(category='core') + self.list(category='standard')
            else:  # all
                return list(self._cache.values())

    # Private helper methods

    def _validate_tool(self, tool: ToolDefinition) -> None:
        """Validate a tool definition."""
        if not tool.name:
            raise ToolValidationError("Tool name is required")

        if not tool.tool_id:
            raise ToolValidationError("Tool ID is required")

        if not tool.description:
            raise ToolValidationError("Tool description is required")

        if tool.category not in ('core', 'standard', 'advanced'):
            raise ToolValidationError("Tool category must be 'core', 'standard', or 'advanced'")

        if not tool.function:
            raise ToolValidationError("Tool function is required")

        if tool.complexity not in ('simple', 'moderate', 'complex'):
            raise ToolValidationError("Tool complexity must be 'simple', 'moderate', or 'complex'")

    def _update_dependencies(self, tool: ToolDefinition) -> None:
        """Update dependency tracking for a tool."""
        self._dependencies[tool.tool_id] = tool.dependencies.copy()

        for dep_name in tool.dependencies:
            # Update reverse dependencies
            if dep_name not in self._reverse_dependencies:
                self._reverse_dependencies[dep_name] = set()
            self._reverse_dependencies[dep_name].add(tool.tool_id)

    def _clear_dependencies(self, tool_id: str) -> None:
        """Clear dependency tracking for a tool."""
        if tool_id in self._dependencies:
            for dep in self._dependencies[tool_id]:
                if dep in self._reverse_dependencies:
                    self._reverse_dependencies[dep].discard(tool_id)
                    if not self._reverse_dependencies[dep]:
                        del self._reverse_dependencies[dep]

            del self._dependencies[tool_id]


# Global registry instance
_registry_instance: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance (singleton pattern)."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ToolRegistry()
    return _registry_instance


# Convenience functions for common operations

def register_tool(
    tool_id: str,
    name: str,
    description: str,
    function: Callable,
    category: str = 'standard',
    complexity: str = 'moderate',
    dependencies: list[str] = None,
    tags: list[str] = None,
    token_cost: int = 0,
) -> bool:
    """
    Register a tool using simplified parameters.

    Args:
        tool_id: Unique tool identifier
        name: Tool name
        description: Tool description
        function: Tool function/callable
        category: Tool category ('core', 'standard', 'advanced')
        complexity: Tool complexity ('simple', 'moderate', 'complex')
        dependencies: List of tool dependencies
        tags: List of tags
        token_cost: Estimated token cost

    Returns:
        True if registration successful
    """
    registry = get_tool_registry()
    tool = ToolDefinition(
        tool_id=tool_id,
        name=name,
        description=description,
        category=category,
        complexity=complexity,
        function=function,
        dependencies=dependencies or [],
        tags=tags or [],
        token_cost=token_cost,
    )
    return registry.register(tool)


def get_tool(tool_id: str) -> Callable | None:
    """
    Get a tool function by ID.

    Args:
        tool_id: Tool ID

    Returns:
        Tool function or None
    """
    registry = get_tool_registry()
    tool = registry.get(tool_id)
    return tool.function if tool else None


def list_tools(category: str = 'all', tags: list[str] = None) -> list[str]:
    """
    List available tool IDs.

    Args:
        category: Filter by category
        tags: Filter by tags

    Returns:
        List of tool IDs
    """
    registry = get_tool_registry()
    category_filter = None if category == 'all' else category
    tools = registry.list(category=category_filter, tags=tags)
    return [t.tool_id for t in tools]
