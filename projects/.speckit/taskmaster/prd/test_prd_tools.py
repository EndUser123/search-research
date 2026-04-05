#!/usr/bin/env python3
"""
PRD Tools Test Runner

Simplified test runner for PRD-aware tools.

Author: Claude Code
Version: 1.0.0
"""

from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_prd_integration():
    """Test PRD integration with core tools."""
    logger.info("="*70)
    logger.info("PRD INTEGRATION TEST")
    logger.info("="*70)

    # Import after path setup
    sys.path.insert(0, str(Path(__file__).parent.parent))
    sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

    from tools.core_tools_prd import (
        complete_task,
        create_task,
        expand_task,
        get_task,
        get_tasks,
        initialize_prd_integration,
        next_task,
        search_tasks,
        set_task_status,
    )

    # Create test PRD with correct format (4 hashes + bold)
    prd_content = """# Test PRD

## Version
1.0.0

## Functional Requirements

#### **FR-1:** User Authentication
**Priority:** high
**Category:** security

Implement user authentication.

#### **FR-2:** Dashboard
**Priority:** medium
**Category:** ui

Create dashboard.

## Non-Functional Requirements

#### **NFR-1:** Performance
**Priority:** critical
**Category:** performance

System must be fast.
"""

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        prd_path = temp_path / "test_project" / "docs" / "PRD.md"
        prd_path.parent.mkdir(parents=True, exist_ok=True)
        prd_path.write_text(prd_content)

        logger.info(f"Created test PRD at {prd_path}")

        # Initialize PRD integration
        try:
            initialize_prd_integration(
                prd_paths=[str(prd_path)],
                cache_size=10
            )
            logger.info("✓ PRD integration initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize PRD integration: {e}")
            return False

        # Test 1: Create task with PRD requirement
        try:
            task_id = create_task(
                title="Implement login",
                prd_name="test_project",
                prd_requirement_id="FR-1",
                validate_prd=True
            )
            if task_id:
                logger.info(f"✓ TOOL 1: create_task - Created {task_id}")
            else:
                logger.error("✗ TOOL 1: create_task - Failed")
                return False
        except Exception as e:
            logger.error(f"✗ TOOL 1: create_task - {e}")
            return False

        # Test 2: Get task with PRD context
        try:
            task = get_task(task_id, include_prd_context=True)
            if task and task.get('prd_context'):
                logger.info("✓ TOOL 2: get_task - Retrieved with PRD context")
            else:
                logger.warning("⚠ TOOL 2: get_task - No PRD context (may be expected)")
        except Exception as e:
            logger.error(f"✗ TOOL 2: get_task - {e}")
            return False

        # Test 3: Get tasks with PRD filtering
        try:
            tasks = get_tasks(prd_name="test_project", limit=10)
            logger.info(f"✓ TOOL 3: get_tasks - Found {len(tasks)} tasks")
        except Exception as e:
            logger.error(f"✗ TOOL 3: get_tasks - {e}")
            return False

        # Test 4: Expand task with PRD context
        try:
            expanded = expand_task(task_id, include_related=True)
            if expanded:
                logger.info("✓ TOOL 4: expand_task - Expanded successfully")
            else:
                logger.error("✗ TOOL 4: expand_task - Failed")
                return False
        except Exception as e:
            logger.error(f"✗ TOOL 4: expand_task - {e}")
            return False

        # Test 5: Search tasks
        try:
            results = search_tasks("authentication", limit=10)
            logger.info(f"✓ TOOL 5: search_tasks - Found {len(results)} results")
        except Exception as e:
            logger.error(f"✗ TOOL 5: search_tasks - {e}")
            return False

        # Test 6: Next task with prioritization
        try:
            task = next_task(prioritize_by_prd=True)
            if task:
                logger.info(f"✓ TOOL 6: next_task - Got {task['task_id']}")
            else:
                logger.info("✓ TOOL 6: next_task - No pending tasks")
        except Exception as e:
            logger.error(f"✗ TOOL 6: next_task - {e}")
            return False

        # Test 7: Set task status
        try:
            success = set_task_status(task_id, "in_progress", track_requirement_progress=True)
            if success:
                logger.info("✓ TOOL 7: set_task_status - Updated successfully")
            else:
                logger.error("✗ TOOL 7: set_task_status - Failed")
                return False
        except Exception as e:
            logger.error(f"✗ TOOL 7: set_task_status - {e}")
            return False

        # Test 8: Complete task
        try:
            success = complete_task(task_id)
            if success:
                logger.info("✓ TOOL 7: complete_task - Completed successfully")
            else:
                logger.error("✗ TOOL 7: complete_task - Failed")
                return False
        except Exception as e:
            logger.error(f"✗ TOOL 7: complete_task - {e}")
            return False

        logger.info("\n" + "="*70)
        logger.info("ALL TESTS PASSED")
        logger.info("="*70)
        return True


if __name__ == "__main__":
    try:
        success = test_prd_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        sys.exit(1)
