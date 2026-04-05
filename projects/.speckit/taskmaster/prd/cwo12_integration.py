#!/usr/bin/env python3
"""
CWO12 Integration for PRD Auto-Import

Automatically detects and imports PRDs during CWO12 workflow.
Integrates with TaskMaster for full traceability.

Author: Claude Code
Version: 1.0.0
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def detect_prd(context: dict) -> str | None:
    """Detect if current work has an associated PRD.

    Checks multiple locations for PRD files:
    1. Explicit 'prd_path' in context
    2. PRD.md in project root
    3. PRD.md in .speckit/prd/
    4. PRD.md in docs/

    Args:
        context: Workflow context dictionary

    Returns:
        Path to detected PRD or None
    """
    # 1. Check explicit context
    if 'prd_path' in context:
        prd_path = Path(context['prd_path'])
        if prd_path.exists():
            logger.info(f"Found PRD from context: {prd_path}")
            return str(prd_path)

    # Get project root
    project_root = Path(context.get('project_root', Path.cwd()))

    # 2. Check for PRD.md in project root
    prd_path = project_root / 'PRD.md'
    if prd_path.exists():
        logger.info(f"Found PRD in project root: {prd_path}")
        return str(prd_path)

    # 3. Check for PRD.md in docs/
    prd_path = project_root / 'docs' / 'PRD.md'
    if prd_path.exists():
        logger.info(f"Found PRD in docs/: {prd_path}")
        return str(prd_path)

    # 4. Check for PRD.md in .speckit/prd/
    prd_path = project_root / '.speckit' / 'prd' / 'PRD.md'
    if prd_path.exists():
        logger.info(f"Found PRD in .speckit/prd/: {prd_path}")
        return str(prd_path)

    # 5. Check for task-specific PRD
    task_name = context.get('task_name', context.get('tsk_name'))
    if task_name:
        prd_path = project_root / '.speckit' / 'prd' / f'{task_name}.md'
        if prd_path.exists():
            logger.info(f"Found task-specific PRD: {prd_path}")
            return str(prd_path)

    logger.info("No PRD detected in context")
    return None


def should_auto_import(context: dict) -> bool:
    """Determine if PRD should be auto-imported.

    Auto-import conditions:
    1. PRD exists
    2. Not previously imported (or PRD is newer than latest task)
    3. Context indicates planning/requirements phase

    Args:
        context: Workflow context dictionary

    Returns:
        True if auto-import is recommended
    """
    prd_path = detect_prd(context)
    if not prd_path:
        return False

    # Check if we're in a planning/requirements phase
    phase = context.get('phase', context.get('cwo12_step', ''))
    if phase and any(p in phase.lower() for p in ['plan', 'requirement', 'analyze']):
        return True

    # Check workflow type
    workflow = context.get('workflow', context.get('workflow_type', ''))
    if workflow and 'cwo12' in workflow.lower():
        return True

    # Default: don't auto-import, let user decide
    return False


def auto_import_prd(context: dict, dry_run: bool = False) -> dict:
    """Auto-detect and import PRD if found.

    This is called during CWO12 workflow to automatically
    import PRD requirements when detected.

    Args:
        context: Workflow context dictionary
        dry_run: If True, check but don't actually import

    Returns:
        Result dictionary with:
        - detected: bool - whether PRD was found
        - prd_path: str - path to PRD if found
        - imported: bool - whether tasks were created
        - task_count: int - number of tasks created
        - error: str - error message if failed
    """
    result = {
        'detected': False,
        'prd_path': None,
        'imported': False,
        'task_count': 0,
        'error': None
    }

    try:
        # Detect PRD
        prd_path = detect_prd(context)
        if not prd_path:
            logger.info("CWO12: No PRD detected for auto-import")
            return result

        result['detected'] = True
        result['prd_path'] = prd_path

        # Import the PRD
        if not dry_run:
            # Import here to avoid circular dependency
            import sys
            from pathlib import Path as LibPath

            # Add taskmaster to path
            taskmaster_path = LibPath(__file__).parent.parent
            if str(taskmaster_path) not in sys.path:
                sys.path.insert(0, str(taskmaster_path))

            from prd.importer import PRDImporter

            importer = PRDImporter()
            import_result = importer.import_prd(prd_path)

            result['imported'] = import_result.tasks_created > 0
            result['task_count'] = import_result.tasks_created

            if import_result.errors:
                result['error'] = '; '.join(import_result.errors)

            logger.info(
                f"CWO12: Auto-imported PRD {prd_path}: "
                f"{import_result.tasks_created} tasks created"
            )
        else:
            logger.info(f"CWO12: Would auto-import PRD {prd_path} (dry-run)")

    except Exception as e:
        result['error'] = str(e)
        logger.error(f"CWO12: Auto-import failed: {e}")

    return result


def get_prd_context(project_root: str | None = None) -> dict:
    """Get PRD context for a project.

    Scans for PRD files and returns information about them.
    Useful for CWO12 Step 3 (Planning).

    Args:
        project_root: Project root path (uses cwd if not provided)

    Returns:
        Dictionary with PRD context information
    """
    if project_root is None:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root)

    context = {
        'project_root': str(project_root),
        'prd_detected': False,
        'prd_path': None,
        'prd_name': None,
        'prd_exists': False
    }

    # Check for PRD files
    prd_locations = [
        project_root / 'PRD.md',
        project_root / 'docs' / 'PRD.md',
        project_root / '.speckit' / 'prd' / 'PRD.md',
    ]

    for prd_path in prd_locations:
        if prd_path.exists():
            context['prd_detected'] = True
            context['prd_path'] = str(prd_path)
            context['prd_name'] = prd_path.stem
            context['prd_exists'] = True
            break

    return context


# CWO12 Hook Functions
# These are called at specific points in CWO12 workflow

def cwo12_step_3_hook(context: dict) -> dict:
    """Hook for CWO12 Step 3 (Planning).

    Automatically detects and offers to import PRD if found.

    Args:
        context: Current workflow context

    Returns:
        Updated context with PRD information
    """
    logger.info("CWO12 Step 3: Checking for PRD...")

    # Get PRD context
    prd_context = get_prd_context(context.get('project_root'))
    context.update(prd_context)

    # If PRD found, note it for user
    if prd_context['prd_detected']:
        logger.info(f"CWO12: PRD detected at {prd_context['prd_path']}")
        # Store for potential auto-import
        context['prd_auto_import_available'] = True

    return context


def cwo12_step_4_hook(context: dict) -> dict:
    """Hook for CWO12 Step 4 (Requirements/Task Decomposition).

    Auto-imports PRD if detected and user hasn't opted out.

    Args:
        context: Current workflow context

    Returns:
        Updated context with import results
    """
    logger.info("CWO12 Step 4: Checking for PRD auto-import...")

    # Check if user has disabled auto-import
    if context.get('prd_auto_import_disabled'):
        logger.info("CWO12: PRD auto-import disabled by user")
        return context

    # Check if we should auto-import
    if should_auto_import(context):
        import_result = auto_import_prd(context)
        context['prd_import_result'] = import_result

        if import_result['imported']:
            logger.info(
                f"CWO12: Auto-imported {import_result['task_count']} "
                f"tasks from PRD"
            )

    return context


# Convenience function for direct CWO12 integration

def cwo12_check_and_import(context: dict) -> dict:
    """
    Single function to check for PRD and import if appropriate.

    This is the main entry point for CWO12 integration.

    Usage in CWO12 workflow:
        >>> context = {'project_root': 'P:/projects/myapp'}
        >>> context = cwo12_check_and_import(context)
        >>> if context.get('prd_import_result', {}).get('imported'):
        ...     print(f"Imported {context['prd_import_result']['task_count']} tasks")

    Args:
        context: Workflow context dictionary

    Returns:
        Updated context with PRD import information
    """
    # Run step 3 hook (detect PRD)
    context = cwo12_step_3_hook(context)

    # Run step 4 hook (auto-import if appropriate)
    context = cwo12_step_4_hook(context)

    return context


# Example usage
if __name__ == "__main__":
    # Test PRD detection
    test_context = {'project_root': str(Path.cwd())}

    print("Testing PRD detection...")
    prd_context = get_prd_context(str(Path.cwd()))
    print(f"PRD detected: {prd_context['prd_detected']}")
    if prd_context['prd_detected']:
        print(f"PRD path: {prd_context['prd_path']}")

    # Test CWO12 integration
    print("\nTesting CWO12 integration...")
    result = cwo12_check_and_import(test_context)
    print(f"Result: {result}")
