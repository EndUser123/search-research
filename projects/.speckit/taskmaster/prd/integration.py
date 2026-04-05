#!/usr/bin/env python3
"""
PRD Integration Layer for TaskMaster Tools

Provides PRD-aware functionality for core TaskMaster tools.
Bridges the gap between task operations and PRD requirements.

Author: Claude Code
Version: 1.0.0
"""

from __future__ import annotations

import logging
from typing import Any

from registry import PRDRegistry

logger = logging.getLogger(__name__)


class PRDIntegrationError(Exception):
    """Raised when PRD integration fails."""
    pass


class PRDIntegration:
    """
    Integration layer for PRD-aware TaskMaster tools.

    Provides:
    - PRD requirement validation
    - Task-requirement linking
    - PRD context retrieval
    - Requirement search capabilities
    - Progress tracking per requirement

    Usage:
        integration = PRDIntegration(prd_registry)

        # Validate requirement ID
        is_valid = integration.validate_requirement('yt_sync', 'FR-1')

        # Get requirement details
        req = integration.get_requirement('yt_sync', 'FR-1')

        # Create task with PRD validation
        task_data = integration.prepare_task_data(
            title='Implement feature',
            prd_name='yt_sync',
            requirement_id='FR-1'
        )
    """

    def __init__(self, prd_registry: PRDRegistry):
        """Initialize PRD integration.

        Args:
            prd_registry: PRD registry instance
        """
        self.registry = prd_registry
        self.logger = logging.getLogger(__name__)

    def validate_requirement(
        self,
        prd_name: str,
        requirement_id: str
    ) -> bool:
        """Validate that a requirement exists in a PRD.

        Args:
            prd_name: Name of the PRD
            requirement_id: Requirement ID (e.g., 'FR-1', 'NFR-2')

        Returns:
            True if requirement exists, False otherwise
        """
        try:
            prd = self.registry.get(prd_name)
            if not prd:
                self.logger.warning(f"PRD not found: {prd_name}")
                return False

            # Check functional requirements
            for req in prd.functional_requirements:
                if req.id == requirement_id:
                    return True

            # Check non-functional requirements
            for req in prd.non_functional_requirements:
                if req.id == requirement_id:
                    return True

            self.logger.warning(
                f"Requirement {requirement_id} not found in {prd_name}"
            )
            return False

        except Exception as e:
            self.logger.error(f"Error validating requirement: {e}")
            return False

    def get_requirement(
        self,
        prd_name: str,
        requirement_id: str
    ) -> dict[str, Any] | None:
        """Get requirement details from PRD.

        Args:
            prd_name: Name of the PRD
            requirement_id: Requirement ID

        Returns:
            Requirement dictionary or None if not found
        """
        try:
            prd = self.registry.get(prd_name)
            if not prd:
                return None

            # Search functional requirements
            for req in prd.functional_requirements:
                if req.id == requirement_id:
                    return {
                        'id': req.id,
                        'title': req.title,
                        'description': req.description,
                        'category': req.category,
                        'priority': req.priority,
                        'acceptance_criteria': req.acceptance_criteria,
                        'type': 'functional'
                    }

            # Search non-functional requirements
            for req in prd.non_functional_requirements:
                if req.id == requirement_id:
                    return {
                        'id': req.id,
                        'title': req.title,
                        'description': req.description,
                        'category': req.category,
                        'priority': req.priority,
                        'type': 'non_functional'
                    }

            return None

        except Exception as e:
            self.logger.error(f"Error getting requirement: {e}")
            return None

    def prepare_task_data(
        self,
        title: str,
        description: str | None = None,
        prd_name: str | None = None,
        requirement_id: str | None = None,
        validate: bool = True,
    ) -> dict[str, Any]:
        """Prepare task data with PRD validation and context.

        Args:
            title: Task title
            description: Task description
            prd_name: PRD name
            requirement_id: Requirement ID
            validate: Whether to validate requirement exists

        Returns:
            Dictionary with prepared task data

        Raises:
            PRDIntegrationError: If validation fails
        """
        task_data = {
            'title': title,
            'description': description,
            'prd_name': prd_name,
            'prd_requirement_id': requirement_id,
            'source': 'prd' if prd_name else 'manual',
            'source_id': f"{prd_name}:{requirement_id}" if prd_name and requirement_id else None,
        }

        # Validate requirement if provided
        if validate and prd_name and requirement_id:
            if not self.validate_requirement(prd_name, requirement_id):
                raise PRDIntegrationError(
                    f"Invalid requirement: {prd_name}/{requirement_id}"
                )

            # Enrich task data with requirement context
            req = self.get_requirement(prd_name, requirement_id)
            if req:
                task_data['requirement_context'] = req

                # Append requirement info to description if not already present
                if description:
                    task_data['description'] = (
                        f"{description}\n\n"
                        f"PRD Requirement: {req['id']} - {req['title']}\n"
                        f"{req['description']}"
                    )
                else:
                    task_data['description'] = (
                        f"PRD Requirement: {req['id']} - {req['title']}\n"
                        f"{req['description']}"
                    )

        return task_data

    def get_requirement_context(
        self,
        prd_name: str,
        requirement_id: str
    ) -> dict[str, Any] | None:
        """Get full context for a requirement including PRD metadata.

        Args:
            prd_name: Name of the PRD
            requirement_id: Requirement ID

        Returns:
            Context dictionary with PRD and requirement details
        """
        try:
            prd = self.registry.get(prd_name)
            if not prd:
                return None

            req = self.get_requirement(prd_name, requirement_id)
            if not req:
                return None

            return {
                'prd_name': prd.prd_name,
                'prd_version': prd.version,
                'prd_title': prd.title,
                'requirement': req,
                'related_requirements': self._find_related_requirements(
                    prd, requirement_id
                ),
            }

        except Exception as e:
            self.logger.error(f"Error getting requirement context: {e}")
            return None

    def search_requirements(
        self,
        query: str,
        prd_name: str | None = None,
        limit: int = 20
    ) -> list[tuple[str, str, str]]:
        """Search for requirements across PRDs.

        Args:
            query: Search query
            prd_name: Optional PRD name to limit search
            limit: Maximum results

        Returns:
            List of (prd_name, req_id, title) tuples
        """
        try:
            if prd_name:
                # Search single PRD
                prd = self.registry.get(prd_name)
                if not prd:
                    return []

                return self._search_prd(prd, query, limit)
            else:
                # Search all PRDs
                return self.registry.search_requirements(
                    query=query,
                    search_titles=True,
                    search_descriptions=True,
                    case_sensitive=False,
                    loaded_only=False,
                )[:limit]

        except Exception as e:
            self.logger.error(f"Error searching requirements: {e}")
            return []

    def get_prd_summary(self, prd_name: str) -> dict[str, Any] | None:
        """Get summary of a PRD.

        Args:
            prd_name: Name of the PRD

        Returns:
            PRD summary dictionary
        """
        try:
            prd = self.registry.get(prd_name)
            if not prd:
                return None

            return {
                'name': prd.prd_name,
                'version': prd.version,
                'title': prd.title,
                'total_requirements': prd.total_requirements,
                'functional_count': len(prd.functional_requirements),
                'non_functional_count': len(prd.non_functional_requirements),
                'categories': self._get_categories(prd),
            }

        except Exception as e:
            self.logger.error(f"Error getting PRD summary: {e}")
            return None

    def get_task_requirements(
        self,
        prd_name: str,
        status_filter: str | None = None
    ) -> list[dict[str, Any]]:
        """Get all requirements from a PRD optionally filtered by status.

        Args:
            prd_name: Name of the PRD
            status_filter: Optional status filter

        Returns:
            List of requirement dictionaries
        """
        try:
            prd = self.registry.get(prd_name)
            if not prd:
                return []

            requirements = []

            # Add functional requirements
            for req in prd.functional_requirements:
                req_dict = {
                    'id': req.id,
                    'title': req.title,
                    'description': req.description,
                    'category': req.category,
                    'priority': req.priority,
                    'type': 'functional',
                }

                if status_filter is None or req.status == status_filter:
                    requirements.append(req_dict)

            # Add non-functional requirements
            for req in prd.non_functional_requirements:
                req_dict = {
                    'id': req.id,
                    'title': req.title,
                    'description': req.description,
                    'category': req.category,
                    'priority': req.priority,
                    'type': 'non_functional',
                }

                if status_filter is None or req.status == status_filter:
                    requirements.append(req_dict)

            return requirements

        except Exception as e:
            self.logger.error(f"Error getting task requirements: {e}")
            return []

    def prioritize_requirements(
        self,
        prd_name: str,
        requirement_ids: list[str]
    ) -> list[tuple[str, int]]:
        """Prioritize requirements based on PRD metadata.

        Args:
            prd_name: Name of the PRD
            requirement_ids: List of requirement IDs

        Returns:
            List of (requirement_id, priority_score) tuples, sorted by score
        """
        try:
            prd = self.registry.get(prd_name)
            if not prd:
                return []

            scored_reqs = []

            for req_id in requirement_ids:
                req = self.get_requirement(prd_name, req_id)
                if not req:
                    continue

                # Calculate priority score
                score = self._calculate_priority_score(req)
                scored_reqs.append((req_id, score))

            # Sort by score (descending)
            scored_reqs.sort(key=lambda x: x[1], reverse=True)
            return scored_reqs

        except Exception as e:
            self.logger.error(f"Error prioritizing requirements: {e}")
            return []

    # Private helper methods

    def _search_prd(
        self,
        prd: Any,
        query: str,
        limit: int
    ) -> list[tuple[str, str, str]]:
        """Search a single PRD for matching requirements."""
        results = []
        query_lower = query.lower()

        all_reqs = (
            prd.functional_requirements +
            prd.non_functional_requirements
        )

        for req in all_reqs:
            if len(results) >= limit:
                break

            # Search title and description
            if (
                (req.title and query_lower in req.title.lower()) or
                (req.description and query_lower in req.description.lower())
            ):
                results.append((prd.prd_name, req.id, req.title))

        return results

    def _find_related_requirements(
        self,
        prd: Any,
        requirement_id: str
    ) -> list[dict[str, str]]:
        """Find related requirements in the same PRD."""
        target_req = self.get_requirement(prd.prd_name, requirement_id)
        if not target_req:
            return []

        related = []
        category = target_req.get('category')

        # Find requirements in same category
        all_reqs = (
            prd.functional_requirements +
            prd.non_functional_requirements
        )

        for req in all_reqs:
            if req.id == requirement_id:
                continue

            if req.category == category:
                related.append({
                    'id': req.id,
                    'title': req.title,
                    'relation': 'same_category'
                })

        return related[:5]  # Limit to 5 related requirements

    def _get_categories(self, prd: Any) -> list[str]:
        """Get unique categories from a PRD."""
        categories = set()

        for req in prd.functional_requirements:
            if req.category:
                categories.add(req.category)

        for req in prd.non_functional_requirements:
            if req.category:
                categories.add(req.category)

        return sorted(list(categories))

    def _calculate_priority_score(self, req: dict[str, Any]) -> int:
        """Calculate priority score for a requirement.

        Higher score = higher priority
        """
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


# Convenience function

def create_prd_integration(
    prd_registry: PRDRegistry
) -> PRDIntegration:
    """Create PRD integration instance.

    Args:
        prd_registry: PRD registry instance

    Returns:
        PRDIntegration instance
    """
    return PRDIntegration(prd_registry)
