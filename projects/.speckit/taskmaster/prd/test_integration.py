#!/usr/bin/env python3
"""
PRD Integration Test Suite

Comprehensive tests for PRD-aware TaskMaster tools.
Tests all 7 core tools with PRD integration functionality.

Author: Claude Code
Version: 1.0.0
"""

from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path

# Add paths
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_prd(temp_dir: Path) -> Path:
    """Create a test PRD file.

    Args:
        temp_dir: Temporary directory

    Returns:
        Path to created PRD file
    """
    prd_content = """# Test Project PRD

## Version
1.0.0

## Overview
Test project for PRD integration.

## Functional Requirements

### FR-1: User Authentication
**Priority:** high
**Category:** security

Implement user authentication with email and password.

**Acceptance Criteria:**
- Users can register with email/password
- Users can login with email/password
- Sessions are managed securely

### FR-2: Dashboard
**Priority:** medium
**Category:** ui

Create user dashboard with statistics.

**Acceptance Criteria:**
- Dashboard shows user stats
- Dashboard is responsive
- Dashboard loads in < 2s

### FR-3: API Integration
**Priority:** high
**Category:** backend

Integrate with external APIs.

**Acceptance Criteria:**
- API calls are authenticated
- Error handling is robust
- Response caching is implemented

## Non-Functional Requirements

### NFR-1: Performance
**Priority:** high
**Category:** performance

System must handle 1000 concurrent users.

**Acceptance Criteria:**
- Response time < 200ms
- 99.9% uptime
- Efficient database queries

### NFR-2: Security
**Priority:** critical
**Category:** security

All data must be encrypted at rest.

**Acceptance Criteria:**
- AES-256 encryption
- Secure key management
- Compliance with security standards
"""

    prd_path = temp_dir / "test_project" / "docs" / "PRD.md"
    prd_path.parent.mkdir(parents=True, exist_ok=True)
    prd_path.write_text(prd_content)

    logger.info(f"Created test PRD at {prd_path}")
    return prd_path


class TestResults:
    """Track test results."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_pass(self, test_name: str):
        """Record a passing test."""
        self.passed += 1
        self.tests.append((test_name, 'PASS'))
        logger.info(f"✓ PASS: {test_name}")

    def add_fail(self, test_name: str, error: str):
        """Record a failing test."""
        self.failed += 1
        self.tests.append((test_name, f'FAIL: {error}'))
        logger.error(f"✗ FAIL: {test_name} - {error}")

    def summary(self) -> str:
        """Generate test summary."""
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        lines = [
            "\n" + "="*70,
            "TEST SUMMARY",
            "="*70,
            f"Total Tests: {total}",
            f"Passed: {self.passed}",
            f"Failed: {self.failed}",
            f"Pass Rate: {pass_rate:.1f}%",
            "="*70,
        ]

        for test_name, result in self.tests:
            lines.append(f"  {test_name}: {result}")

        return "\n".join(lines)


def run_tests():
    """Run all PRD integration tests."""
    results = TestResults()

    logger.info("="*70)
    logger.info("PRD INTEGRATION TEST SUITE")
    logger.info("="*70)

    # Create temporary directory and PRD
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test PRD
        prd_path = create_test_prd(temp_path)

        # Initialize PRD integration
        try:
            initialize_prd_integration(
                prd_paths=[str(prd_path.parent.parent / "docs" / "PRD.md")],
                cache_size=10
            )
            results.add_pass("Initialize PRD Integration")
        except Exception as e:
            results.add_fail("Initialize PRD Integration", str(e))
            print(results.summary())
            return

        # ====================================================================
        # TEST 1: create_task with PRD requirement
        # ====================================================================
        try:
            task_id = create_task(
                title="Implement user login",
                description="Create login endpoint",
                prd_name="test_project",
                prd_requirement_id="FR-1",
                validate_prd=True
            )

            if task_id and task_id.startswith("TSK-"):
                results.add_pass("TOOL 1: create_task with PRD requirement")
            else:
                results.add_fail("TOOL 1: create_task with PRD requirement", "Invalid task ID")

        except Exception as e:
            results.add_fail("TOOL 1: create_task with PRD requirement", str(e))

        # ====================================================================
        # TEST 2: create_task with invalid PRD requirement (should fail)
        # ====================================================================
        try:
            task_id = create_task(
                title="Invalid requirement",
                prd_name="test_project",
                prd_requirement_id="INVALID-999",
                validate_prd=True
            )

            if task_id is None:
                results.add_pass("TOOL 1: create_task rejects invalid requirement")
            else:
                results.add_fail("TOOL 1: create_task rejects invalid requirement", "Should have failed")

        except Exception:
            # Expected to fail
            results.add_pass("TOOL 1: create_task rejects invalid requirement")

        # ====================================================================
        # TEST 3: get_task with PRD context
        # ====================================================================
        try:
            task = get_task(task_id, include_prd_context=True)

            if task and task.get('prd_context'):
                req = task['prd_context']['requirement']
                if req['id'] == 'FR-1' and 'authentication' in req['title'].lower():
                    results.add_pass("TOOL 2: get_task with PRD context")
                else:
                    results.add_fail("TOOL 2: get_task with PRD context", "Wrong requirement")
            else:
                results.add_fail("TOOL 2: get_task with PRD context", "No PRD context")

        except Exception as e:
            results.add_fail("TOOL 2: get_task with PRD context", str(e))

        # ====================================================================
        # TEST 4: get_tasks with PRD filtering
        # ====================================================================
        try:
            # Create another task
            task_id_2 = create_task(
                title="Create dashboard",
                prd_name="test_project",
                prd_requirement_id="FR-2"
            )

            # Get tasks for PRD
            tasks = get_tasks(prd_name="test_project", limit=10)

            if len(tasks) >= 2:
                results.add_pass("TOOL 3: get_tasks with PRD filtering")
            else:
                results.add_fail("TOOL 3: get_tasks with PRD filtering", f"Expected >=2 tasks, got {len(tasks)}")

        except Exception as e:
            results.add_fail("TOOL 3: get_tasks with PRD filtering", str(e))

        # ====================================================================
        # TEST 5: get_tasks with requirement filtering
        # ====================================================================
        try:
            tasks = get_tasks(prd_requirement_id="FR-1", limit=10)

            if len(tasks) >= 1:
                if all(t.get('prd_requirement_id') == 'FR-1' for t in tasks):
                    results.add_pass("TOOL 3: get_tasks with requirement filter")
                else:
                    results.add_fail("TOOL 3: get_tasks with requirement filter", "Wrong requirement in results")
            else:
                results.add_fail("TOOL 3: get_tasks with requirement filter", "No tasks returned")

        except Exception as e:
            results.add_fail("TOOL 3: get_tasks with requirement filter", str(e))

        # ====================================================================
        # TEST 6: expand_task with full PRD context
        # ====================================================================
        try:
            expanded = expand_task(task_id, include_related=True)

            if expanded:
                has_prd_context = 'prd_context' in expanded
                has_prd_summary = 'prd_summary' in expanded

                if has_prd_context:
                    context = expanded['prd_context']
                    has_requirement = 'requirement' in context
                    has_related = 'related_requirements' in context

                    if has_requirement and has_related:
                        results.add_pass("TOOL 4: expand_task with full PRD context")
                    else:
                        results.add_fail("TOOL 4: expand_task with full PRD context", "Missing requirement/related")
                else:
                    results.add_fail("TOOL 4: expand_task with full PRD context", "No PRD context")
            else:
                results.add_fail("TOOL 4: expand_task with full PRD context", "No task returned")

        except Exception as e:
            results.add_fail("TOOL 4: expand_task with full PRD context", str(e))

        # ====================================================================
        # TEST 7: search_tasks with PRD requirement search
        # ====================================================================
        try:
            # Search in task titles
            tasks_title = search_tasks("authentication", limit=10, search_prd_requirements=False)

            # Search in PRD requirements too
            tasks_prd = search_tasks("authentication", limit=10, search_prd_requirements=True)

            if len(tasks_prd) >= len(tasks_title):
                results.add_pass("TOOL 5: search_tasks with PRD requirement search")
            else:
                results.add_fail("TOOL 5: search_tasks with PRD requirement search", "PRD search didn't find more results")

        except Exception as e:
            results.add_fail("TOOL 5: search_tasks with PRD requirement search", str(e))

        # ====================================================================
        # TEST 8: next_task with PRD prioritization
        # ====================================================================
        try:
            # Get standard next task
            task_standard = next_task(prioritize_by_prd=False)

            # Get PRD-prioritized task
            task_prioritized = next_task(prioritize_by_prd=True)

            if task_standard and task_prioritized:
                results.add_pass("TOOL 6: next_task with PRD prioritization")
            else:
                results.add_fail("TOOL 6: next_task with PRD prioritization", "No tasks returned")

        except Exception as e:
            results.add_fail("TOOL 6: next_task with PRD prioritization", str(e))

        # ====================================================================
        # TEST 9: set_task_status with requirement tracking
        # ====================================================================
        try:
            # Create a task to update
            task_id_3 = create_task(
                title="API integration task",
                prd_name="test_project",
                prd_requirement_id="FR-3"
            )

            # Update status
            success = set_task_status(
                task_id_3,
                "in_progress",
                track_requirement_progress=True
            )

            if success:
                # Verify status was updated
                task = get_task(task_id_3)
                if task and task['status'] == 'in_progress':
                    results.add_pass("TOOL 7: set_task_status with requirement tracking")
                else:
                    results.add_fail("TOOL 7: set_task_status with requirement tracking", "Status not updated")
            else:
                results.add_fail("TOOL 7: set_task_status with requirement tracking", "Update failed")

        except Exception as e:
            results.add_fail("TOOL 7: set_task_status with requirement tracking", str(e))

        # ====================================================================
        # TEST 10: complete_task with requirement tracking
        # ====================================================================
        try:
            # Complete the task
            success = complete_task(task_id_3)

            if success:
                # Verify status was updated
                task = get_task(task_id_3)
                if task and task['status'] == 'completed':
                    results.add_pass("TOOL 7: complete_task with requirement tracking")
                else:
                    results.add_fail("TOOL 7: complete_task with requirement tracking", "Status not completed")
            else:
                results.add_fail("TOOL 7: complete_task with requirement tracking", "Complete failed")

        except Exception as e:
            results.add_fail("TOOL 7: complete_task with requirement tracking", str(e))

        # ====================================================================
        # TEST 11: Integration test - Create and manage requirement workflow
        # ====================================================================
        try:
            # Simulate a complete workflow
            workflow_task_id = create_task(
                title="Implement performance optimization",
                description="Optimize database queries",
                prd_name="test_project",
                prd_requirement_id="NFR-1"
            )

            # Get task with context
            task = get_task(workflow_task_id, include_prd_context=True)
            assert task is not None

            # Update to in_progress
            set_task_status(workflow_task_id, "in_progress")

            # Expand with full context
            expanded = expand_task(workflow_task_id)
            assert expanded is not None

            # Complete task
            complete_task(workflow_task_id)

            # Verify
            final_task = get_task(workflow_task_id)
            assert final_task['status'] == 'completed'

            results.add_pass("Integration: Complete requirement workflow")

        except Exception as e:
            results.add_fail("Integration: Complete requirement workflow", str(e))

        # ====================================================================
        # TEST 12: Error handling - Invalid requirement ID
        # ====================================================================
        try:
            # Should handle gracefully
            task = get_tasks(prd_requirement_id="NONEXISTENT-999")

            # Should return empty list, not error
            if isinstance(task, list):
                results.add_pass("Error handling: Invalid requirement ID")
            else:
                results.add_fail("Error handling: Invalid requirement ID", "Should return list")

        except Exception as e:
            results.add_fail("Error handling: Invalid requirement ID", f"Should not raise: {e}")

        # ====================================================================
        # TEST 13: Error handling - Invalid status
        # ====================================================================
        try:
            # Create a test task
            test_task = create_task(title="Test task")

            # Try invalid status
            success = set_task_status(test_task, "invalid_status")

            # Should fail gracefully
            if not success:
                results.add_pass("Error handling: Invalid status")
            else:
                results.add_fail("Error handling: Invalid status", "Should reject invalid status")

        except Exception as e:
            results.add_fail("Error handling: Invalid status", f"Should not raise: {e}")

    # Print summary
    print(results.summary())

    return results


if __name__ == "__main__":
    results = run_tests()

    # Exit with appropriate code
    sys.exit(0 if results.failed == 0 else 1)
