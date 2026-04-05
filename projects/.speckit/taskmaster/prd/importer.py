#!/usr/bin/env python3
"""
PRD Importer for TaskMaster

Imports PRD requirements as TaskMaster tasks with full traceability.
Links tasks to PRD via source, source_id, and prd_requirement_id.

Author: Claude Code
Version: 1.0.0
"""

from __future__ import annotations

import logging
import sqlite3

# Import core tools for task creation
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Import PRD parser
from .parser import PRDParser, PRDValidationError

sys.path.insert(0, str(Path(__file__).parent.parent))
from db import get_connection
from tools.core_tools import create_task

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    """Result of PRD import operation."""
    prd_path: str
    prd_name: str
    total_requirements: int
    tasks_created: int
    tasks_skipped: int
    errors: list[str] = field(default_factory=list)
    created_task_ids: list[str] = field(default_factory=list)
    import_time: datetime = field(default_factory=datetime.now)


class PRDImporter:
    """
    Import PRD requirements as TaskMaster tasks.

    Features:
    - Parses PRD files using PRDParser
    - Creates tasks with PRD traceability
    - Skips duplicates (tasks already linked to same requirement)
    - Supports dry-run mode
    """

    def __init__(self, db_path: str | None = None):
        """Initialize the PRD importer.

        Args:
            db_path: Optional database path (uses default if not provided)
        """
        self.parser = PRDParser()
        self.logger = logging.getLogger(__name__)

        # Track imports for this session
        self._imported_prds: dict[str, ImportResult] = {}

    def import_prd(
        self,
        prd_path: str,
        dry_run: bool = False,
        filter_ids: list[str] | None = None,
        import_type: str = "all"  # 'all', 'functional', 'non_functional'
    ) -> ImportResult:
        """Import requirements from a PRD file as tasks.

        Args:
            prd_path: Path to the PRD file
            dry_run: If True, don't actually create tasks
            filter_ids: Only import specific requirement IDs (e.g., ['FR-1', 'FR-3'])
            import_type: Type of requirements to import

        Returns:
            ImportResult with details of what was imported
        """
        self.logger.info(f"Starting PRD import: {prd_path}")

        result = ImportResult(
            prd_path=prd_path,
            prd_name="",
            total_requirements=0,
            tasks_created=0,
            tasks_skipped=0
        )

        try:
            # Parse the PRD
            parsed_prd = self.parser.parse_prd_file(prd_path)
            result.prd_name = parsed_prd.prd_name

            # Gather requirements to import
            requirements = []
            if import_type in ('all', 'functional'):
                requirements.extend(parsed_prd.functional_requirements)
            if import_type in ('all', 'non_functional'):
                requirements.extend(parsed_prd.non_functional_requirements)

            # Apply filters
            if filter_ids:
                requirements = [r for r in requirements if r.id in filter_ids]

            result.total_requirements = len(requirements)

            self.logger.info(
                f"Importing {len(requirements)} requirements from {parsed_prd.prd_name}"
            )

            # Check for existing tasks from this PRD
            existing_req_ids = self._get_existing_requirement_ids(prd_path)

            # Import each requirement
            for req in requirements:
                # Skip if already imported
                if req.id in existing_req_ids:
                    self.logger.info(f"Skipping {req.id} - already imported")
                    result.tasks_skipped += 1
                    continue

                # Build task title
                task_title = f"{req.id}: {req.title}"

                # Build description from acceptance criteria
                description_parts = []
                if req.acceptance_criteria:
                    description_parts.append("Acceptance Criteria:")
                    for ac in req.acceptance_criteria:
                        description_parts.append(f"  - {ac}")

                if req.success_metrics:
                    description_parts.append("Success Metrics:")
                    for sm in req.success_metrics:
                        description_parts.append(f"  - {sm}")

                description = "\n".join(description_parts) if description_parts else None

                # Create the task
                if not dry_run:
                    task_id = create_task(
                        title=task_title,
                        description=description,
                        status='pending',
                        context_type='csf_nip',
                        source='prd',
                        source_id=prd_path,
                        prd_requirement_id=req.id
                    )

                    if task_id:
                        result.created_task_ids.append(task_id)
                        result.tasks_created += 1
                        self.logger.info(f"Created task {task_id} for {req.id}")
                    else:
                        result.errors.append(f"Failed to create task for {req.id}")
                else:
                    # Dry run - just log what would be created
                    self.logger.info(f"[DRY RUN] Would create task for {req.id}")
                    result.tasks_created += 1

            # Cache result
            self._imported_prds[prd_path] = result

            self.logger.info(
                f"PRD import complete: {result.tasks_created} created, "
                f"{result.tasks_skipped} skipped"
            )

        except PRDValidationError as e:
            result.errors.append(f"PRD validation error: {e}")
            self.logger.error(f"PRD validation failed: {e}")
        except Exception as e:
            result.errors.append(f"Import error: {e}")
            self.logger.error(f"Import failed: {e}")

        return result

    def _get_existing_requirement_ids(self, prd_path: str) -> set:
        """Get requirement IDs already imported from this PRD.

        Args:
            prd_path: Path to the PRD file

        Returns:
            Set of requirement IDs that already have tasks
        """
        try:
            conn = get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT prd_requirement_id FROM tasks WHERE source = ? AND source_id = ?",
                ('prd', prd_path)
            )
            rows = cursor.fetchall()
            conn.close()

            return {row['prd_requirement_id'] for row in rows if row['prd_requirement_id']}
        except Exception as e:
            self.logger.warning(f"Failed to check existing tasks: {e}")
            return set()

    def _get_prd_tasks(self, prd_path: str) -> list[dict[str, Any]]:
        """Get all tasks from a PRD.

        Args:
            prd_path: Path to the PRD file

        Returns:
            List of task dictionaries
        """
        try:
            conn = get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM tasks WHERE source = ? AND source_id = ?",
                ('prd', prd_path)
            )
            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.warning(f"Failed to get PRD tasks: {e}")
            return []

    def get_prd_completion_status(self, prd_path: str) -> dict[str, Any]:
        """Get completion status for all requirements from a PRD.

        Args:
            prd_path: Path to the PRD file

        Returns:
            Dictionary with completion status by requirement ID
        """
        try:
            # Parse PRD to get all requirements
            parsed_prd = self.parser.parse_prd_file(prd_path)

            # Get all tasks from this PRD
            tasks = self._get_prd_tasks(prd_path)

            # Build status map
            status_map = {}
            for task in tasks:
                req_id = task.get('prd_requirement_id')
                if req_id:
                    status_map[req_id] = {
                        'task_id': task['task_id'],
                        'status': task['status'],
                        'title': task['title']
                    }

            # Build full status report
            report = {
                'prd_name': parsed_prd.prd_name,
                'prd_path': prd_path,
                'total_requirements': parsed_prd.total_requirements,
                'completed': 0,
                'in_progress': 0,
                'pending': 0,
                'not_imported': 0,
                'requirements': []
            }

            # Process functional requirements
            for req in parsed_prd.functional_requirements:
                req_status = status_map.get(req.id)
                if req_status:
                    status = req_status['status']
                    if status == 'completed':
                        report['completed'] += 1
                    elif status == 'in_progress':
                        report['in_progress'] += 1
                    else:
                        report['pending'] += 1

                    report['requirements'].append({
                        'id': req.id,
                        'title': req.title,
                        'status': status,
                        'task_id': req_status['task_id']
                    })
                else:
                    report['not_imported'] += 1
                    report['requirements'].append({
                        'id': req.id,
                        'title': req.title,
                        'status': 'not_imported',
                        'task_id': None
                    })

            # Process non-functional requirements
            for req in parsed_prd.non_functional_requirements:
                req_status = status_map.get(req.id)
                if req_status:
                    status = req_status['status']
                    if status == 'completed':
                        report['completed'] += 1
                    elif status == 'in_progress':
                        report['in_progress'] += 1
                    else:
                        report['pending'] += 1

                    report['requirements'].append({
                        'id': req.id,
                        'title': req.title,
                        'status': status,
                        'task_id': req_status['task_id']
                    })
                else:
                    report['not_imported'] += 1
                    report['requirements'].append({
                        'id': req.id,
                        'title': req.title,
                        'status': 'not_imported',
                        'task_id': None
                    })

            return report

        except Exception as e:
            self.logger.error(f"Failed to get PRD completion status: {e}")
            return {
                'prd_path': prd_path,
                'error': str(e)
            }

    def list_imported_prds(self) -> list[dict[str, Any]]:
        """List all PRDs that have been imported.

        Returns:
            List of PRD info dictionaries
        """
        try:
            conn = get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all tasks with PRD source
            cursor.execute(
                "SELECT * FROM tasks WHERE source = ? ORDER BY created_at DESC",
                ('prd',)
            )
            tasks = [dict(row) for row in cursor.fetchall()]
            conn.close()

            # Group by source_id (PRD path)
            prd_map: dict[str, list[dict]] = {}
            for task in tasks:
                source_id = task.get('source_id')
                if source_id:
                    if source_id not in prd_map:
                        prd_map[source_id] = []
                    prd_map[source_id].append(task)

            # Build PRD list
            prd_list = []
            for prd_path, prd_tasks in prd_map.items():
                # Try to get PRD name from first task or parse file
                prd_name = Path(prd_path).stem
                completed = sum(1 for t in prd_tasks if t['status'] == 'completed')
                in_progress = sum(1 for t in prd_tasks if t['status'] == 'in_progress')

                prd_list.append({
                    'prd_path': prd_path,
                    'prd_name': prd_name,
                    'total_tasks': len(prd_tasks),
                    'completed': completed,
                    'in_progress': in_progress,
                    'pending': len(prd_tasks) - completed - in_progress
                })

            return sorted(prd_list, key=lambda x: x['prd_name'])

        except Exception as e:
            self.logger.error(f"Failed to list imported PRDs: {e}")
            return []


# Convenience functions

def import_prd(
    prd_path: str,
    dry_run: bool = False,
    filter_ids: list[str] | None = None
) -> ImportResult:
    """Import a PRD file as TaskMaster tasks.

    Args:
        prd_path: Path to the PRD file
        dry_run: If True, don't actually create tasks
        filter_ids: Only import specific requirement IDs

    Returns:
        ImportResult with details of what was imported

    Example:
        >>> result = import_prd("P:/projects/auth/PRD.md")
        >>> print(f"Imported {result.tasks_created} tasks")
    """
    importer = PRDImporter()
    return importer.import_prd(prd_path, dry_run=dry_run, filter_ids=filter_ids)


def get_prd_status(prd_path: str) -> dict[str, Any]:
    """Get completion status for a PRD.

    Args:
        prd_path: Path to the PRD file

    Returns:
        Dictionary with completion status

    Example:
        >>> status = get_prd_status("P:/projects/auth/PRD.md")
        >>> print(f"Completed: {status['completed']}/{status['total_requirements']}")
    """
    importer = PRDImporter()
    return importer.get_prd_completion_status(prd_path)


def list_prds() -> list[dict[str, Any]]:
    """List all imported PRDs.

    Returns:
        List of PRD info dictionaries

    Example:
        >>> prds = list_prds()
        >>> for prd in prds:
        ...     print(f"{prd['prd_name']}: {prd['completed']}/{prd['total_tasks']} complete")
    """
    importer = PRDImporter()
    return importer.list_imported_prds()


# Example usage
if __name__ == "__main__":
    import sys

    # Test import
    if len(sys.argv) > 1:
        test_prd = sys.argv[1]
        result = import_prd(test_prd)

        print(f"\nPRD Import Result: {result.prd_name}")
        print(f"  Path: {result.prd_path}")
        print(f"  Total requirements: {result.total_requirements}")
        print(f"  Tasks created: {result.tasks_created}")
        print(f"  Tasks skipped: {result.tasks_skipped}")

        if result.created_task_ids:
            print("\nCreated task IDs:")
            for tid in result.created_task_ids:
                print(f"  - {tid}")

        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  - {error}")
    else:
        print("Usage: python importer.py <path_to_prd>")
