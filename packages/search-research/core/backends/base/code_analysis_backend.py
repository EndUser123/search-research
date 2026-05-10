"""Code Analysis Backend - Base class for code analysis backends.

Provides common functionality for dependency analysis, impact assessment,
and relationship tracking across different code analysis implementations.

Migrated from: P:\\\\\\__csf/src/search/backends/code_analysis_backend.py
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class CodeAnalysisBackend(ABC):
    """Abstract base class for code analysis backends.

    Defines the common interface for code analysis operations including:
    - Dependency tracking (dependents, dependencies)
    - Impact analysis (risk assessment, change safety)
    - Relationship discovery (related entities, control flow)
    - Entity querying (search, retrieval)

    Implementations can use different storage mechanisms (SQLite, in-memory, etc.)
    and parsing strategies (CPG, AST, tree-sitter) while providing a consistent API.
    """

    # =========================================================================
    # ABSTRACT METHODS - Must be implemented by subclasses
    # =========================================================================

    @abstractmethod
    def get_dependents(self, entity_id: str, limit: int = 0) -> list[str]:
        """Find entities that depend on this entity.

        Args:
            entity_id: Unique identifier for the entity to analyze.
            limit: Maximum number of results to return (0 = no limit).

        Returns:
            List of entity IDs that depend on this entity.
            Empty list if no dependents or entity not found.
        """
        pass

    @abstractmethod
    def get_dependencies(self, entity_id: str, limit: int = 0) -> list[str]:
        """Find entities that this entity depends on.

        Args:
            entity_id: Unique identifier for the entity to analyze.
            limit: Maximum number of results to return (0 = no limit).

        Returns:
            List of entity IDs that this entity depends on (imports, calls, etc.).
            Empty list if no dependencies or entity not found.
        """
        pass

    @abstractmethod
    def get_control_flow(self, entity_id: str) -> dict[str, list[dict[str, Any]]]:
        """Get control flow branches for an entity.

        Extracts conditional branches, loops, and exception handling blocks.

        Args:
            entity_id: Unique identifier for the entity to analyze.

        Returns:
            Dictionary mapping branch types to lists of branch information:
            {
                "if": [{"condition": "x > 0", "line": 42}, ...],
                "loop": [{"type": "for", "line": 50}, ...],
                "exception": [{"type": "try-catch", "line": 60}, ...]
            }
            Empty dict if entity not found or no control flow.
        """
        pass

    @abstractmethod
    def get_entity(self, entity_id: str) -> dict[str, Any] | None:
        """Get a single entity by ID.

        Args:
            entity_id: Unique identifier for the entity to retrieve.

        Returns:
            Entity dictionary with fields like:
            {
                "id": str,
                "type": str,  # function, class, method, etc.
                "name": str,
                "file_path": str,
                "line": int,
                "language": str,  # python, typescript, etc.
                ...
            }
            None if entity not found.
        """
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 10, **kwargs) -> list[dict[str, Any]]:
        """Search for entities matching a query.

        Args:
            query: Search query string (semantic, name-based, or pattern).
            limit: Maximum number of results to return.
            **kwargs: Additional backend-specific search parameters.

        Returns:
            List of search results, each containing:
            {
                "id": str,
                "title": str,
                "content": str,
                "score": float,
                "metadata": dict
            }
            Empty list if no matches or search unavailable.
        """
        pass

    # =========================================================================
    # CONCRETE METHODS - Shared implementation
    # =========================================================================

    def get_related(self, entity_id: str, limit: int = 20) -> list[str]:
        """Find all related entities within 1 hop in the dependency graph.

        Combines dependents and dependencies to provide a complete picture
        of entities related to this one.

        Args:
            entity_id: Unique identifier for the entity to analyze.
            limit: Maximum number of related entities to return.

        Returns:
            List of related entity IDs (both dependents and dependencies).
            May contain duplicates if an entity is both a dependent and dependency.
            Returns at most `limit` results.
        """
        dependents = self.get_dependents(entity_id)
        dependencies = self.get_dependencies(entity_id)

        # Combine using set for uniqueness, then convert back to list
        related = set(dependents) | set(dependencies)

        # Apply limit
        if limit > 0:
            return list(related)[:limit]
        return list(related)

    def impact_analysis(self, entity_id: str) -> dict[str, Any]:
        """Analyze impact of changing this entity.

        Provides risk assessment for code changes by analyzing:
        - Number of dependents (entities that would be affected)
        - Number of dependencies (entities this relies on)
        - Control flow complexity (branches, loops, exceptions)

        Args:
            entity_id: Unique identifier for the entity to analyze.

        Returns:
            Dictionary with impact assessment:
            {
                "entity_id": str,
                "dependents": list[str],  # Actual dependent entity IDs
                "dependents_count": int,
                "dependencies": list[str],  # Actual dependency entity IDs
                "dependencies_count": int,
                "control_flow_branches": int,  # Total branch count
                "risk_level": str,  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
                "is_safe": bool  # True if no dependents
            }

        Risk Levels:
        - LOW: 0-1 dependents
        - MEDIUM: 2-5 dependents
        - HIGH: 6-10 dependents
        - CRITICAL: 11+ dependents
        """
        # Gather data
        dependents = self.get_dependents(entity_id)
        dependencies = self.get_dependencies(entity_id)
        control_flow = self.get_control_flow(entity_id)

        # Calculate control flow complexity
        branch_count = sum(len(branches) for branches in control_flow.values())

        # Determine risk level based on dependent count
        dependent_count = len(dependents)
        if dependent_count > 10:
            risk = "CRITICAL"
        elif dependent_count > 5:
            risk = "HIGH"
        elif dependent_count > 1:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        return {
            "entity_id": entity_id,
            "dependents": dependents,
            "dependents_count": dependent_count,
            "dependencies": dependencies,
            "dependencies_count": len(dependencies),
            "control_flow_branches": branch_count,
            "risk_level": risk,
            "is_safe": dependent_count == 0,
        }

    def get_related_multi_hop(
        self,
        entity_id: str,
        depth: int = 2,
        limit: int = 50,
    ) -> dict[str, list[str]]:
        """Find related entities within N hops (multi-level dependency traversal).

        Extends get_related() to explore deeper relationships in the dependency graph.

        Args:
            entity_id: Unique identifier for the starting entity.
            depth: Maximum number of hops to traverse (default: 2).
            limit: Maximum number of entities to return per level.

        Returns:
            Dictionary mapping distance to entity IDs:
            {
                "1": [entity_ids_at_distance_1],
                "2": [entity_ids_at_distance_2],
                ...
            }
        """
        result = {str(d): [] for d in range(1, depth + 1)}
        visited = {entity_id}
        current_level = {entity_id}

        for d in range(1, depth + 1):
            next_level = set()

            for eid in current_level:
                # Get related entities at this level
                related = set(self.get_dependents(eid)) | set(self.get_dependencies(eid))

                # Filter out already visited entities
                new_entities = related - visited
                next_level.update(new_entities)
                visited.update(new_entities)

            # Store results for this level (with limit)
            result[str(d)] = list(next_level)[:limit] if limit > 0 else list(next_level)
            current_level = next_level

            # Stop if no more entities to explore
            if not current_level:
                break

        return result

    def get_impact_summary(self, entity_ids: list[str]) -> dict[str, Any]:
        """Get aggregate impact analysis for multiple entities.

        Useful for batch operations or analyzing entire modules/files.

        Args:
            entity_ids: List of entity IDs to analyze.

        Returns:
            Dictionary with aggregate statistics:
            {
                "total_entities": int,
                "safe_to_change": int,  # Count of entities with is_safe=True
                "risky_changes": int,  # Count of entities with risk_level != "LOW"
                "risk_distribution": {  # Count by risk level
                    "LOW": int,
                    "MEDIUM": int,
                    "HIGH": int,
                    "CRITICAL": int
                },
                "details": {entity_id: impact_result, ...}
            }
        """
        risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        details: dict[str, Any] = {}
        safe_count = 0
        risky_count = 0

        for entity_id in entity_ids:
            impact = self.impact_analysis(entity_id)
            details[entity_id] = impact

            risk = impact["risk_level"]
            risk_distribution[risk] += 1

            if impact["is_safe"]:
                safe_count += 1
            if risk != "LOW":
                risky_count += 1

        return {
            "total_entities": len(entity_ids),
            "safe_to_change": safe_count,
            "risky_changes": risky_count,
            "risk_distribution": risk_distribution,
            "details": details,
        }

    def find_common_dependencies(
        self,
        entity_ids: list[str],
        limit: int = 10,
    ) -> list[tuple[str, int]]:
        """Find dependencies shared by multiple entities.

        Useful for identifying shared utilities, common imports, or
        coupling between modules.

        Args:
            entity_ids: List of entity IDs to analyze.
            limit: Maximum number of common dependencies to return.

        Returns:
            List of (dependency_id, count) tuples sorted by frequency.
            Dependencies that appear in more entities are listed first.
        """
        dependency_counts: dict[str, int] = {}

        for entity_id in entity_ids:
            dependencies = self.get_dependencies(entity_id)
            for dep in dependencies:
                dependency_counts[dep] = dependency_counts.get(dep, 0) + 1

        # Filter to dependencies shared by multiple entities
        common = {dep: count for dep, count in dependency_counts.items() if count > 1}

        # Sort by frequency (descending)
        sorted_common = sorted(common.items(), key=lambda x: x[1], reverse=True)

        return sorted_common[:limit] if limit > 0 else sorted_common

    def validate_entity_exists(self, entity_id: str) -> bool:
        """Check if an entity exists in the index.

        Convenience method that wraps get_entity() with existence check.

        Args:
            entity_id: Unique identifier for the entity to validate.

        Returns:
            True if entity exists, False otherwise.
        """
        return self.get_entity(entity_id) is not None

    def get_entity_context(
        self,
        entity_id: str,
        include_depth: int = 1,
    ) -> dict[str, Any]:
        """Get comprehensive context for an entity.

        Combines entity metadata with dependency information and impact analysis.

        Args:
            entity_id: Unique identifier for the entity.
            include_depth: Number of hops to include for related entities.

        Returns:
            Dictionary with complete context:
            {
                "entity": dict,  # Entity metadata
                "impact": dict,  # Impact analysis
                "direct_related": list[str],  # Related entities at distance 1
                "extended_related": dict,  # Related entities at distance > 1 (if include_depth > 1)
            }
        """
        entity = self.get_entity(entity_id)
        if not entity:
            return {"error": f"Entity not found: {entity_id}"}

        impact = self.impact_analysis(entity_id)
        direct_related = self.get_related(entity_id, limit=0)

        result: dict[str, Any] = {
            "entity": entity,
            "impact": impact,
            "direct_related": direct_related,
        }

        if include_depth > 1:
            result["extended_related"] = self.get_related_multi_hop(
                entity_id,
                depth=include_depth,
            )

        return result


__all__ = [
    "CodeAnalysisBackend",
]
