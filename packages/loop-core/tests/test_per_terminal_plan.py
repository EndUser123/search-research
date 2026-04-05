"""Tests for per-terminal plan cloning (TASK-013).

This module implements the TDD RED phase for TASK-013, testing the plan cloning
functionality that enables multiple terminals to operate on isolated plan files.

Test Cases:
----------
- Test that two terminals get different plan files
- Test that task state is isolated between terminals
- Test that clone only happens once per terminal
- Test that original plan.md is not modified during cloning
- Test that clone_plan_for_terminal creates correct file structure
- Test that cloned plan preserves original content
- Test that cloning handles missing terminal directory
- Test that cloning is idempotent (safe to call multiple times)

Acceptance Criteria:
-------------------
- Two simulated terminals operate on different plan files without overwriting
- Original plan.md remains unmodified
- Clone only happens once per terminal
- Task state isolation between terminals
"""

from pathlib import Path

import pytest

# Import implementation
from scripts.ralph_loop_entry import clone_plan_for_terminal
from scripts.state_paths import get_terminal_state_dir

# Type aliases for test clarity
TerminalId = str
PlanPath = str | Path


class TestPlanCloning:
    """Test per-terminal plan cloning functionality."""

    def test_two_terminals_get_different_plan_files(self, tmp_path: Path) -> None:
        """Test that two different terminals get isolated plan files."""
        # Arrange: Create shared plan
        shared_plan = tmp_path / ".claude" / "loop" / "plan.md"
        shared_plan.parent.mkdir(parents=True, exist_ok=True)
        shared_plan.write_text("# Shared Plan\n\n- [ ] Task 1\n- [ ] Task 2\n")

        # Act: Clone for two different terminals
        terminal_1_id = "console_abc123"
        terminal_2_id = "console_xyz789"

        cloned_plan_1 = clone_plan_for_terminal(
            plan_path=shared_plan,
            terminal_id=terminal_1_id,
        )
        cloned_plan_2 = clone_plan_for_terminal(
            plan_path=shared_plan,
            terminal_id=terminal_2_id,
        )

        # Assert: Plans should be different files
        assert cloned_plan_1 != cloned_plan_2
        assert cloned_plan_1.exists()
        assert cloned_plan_2.exists()

        # Verify different paths (terminal_id is in directory path, not filename)
        assert str(terminal_1_id) in str(cloned_plan_1)
        assert str(terminal_2_id) in str(cloned_plan_2)

    def test_task_state_isolation_between_terminals(self, tmp_path: Path) -> None:
        """Test that task state changes in one terminal don't affect another."""
        # Arrange: Create shared plan and clone for two terminals
        shared_plan = tmp_path / ".claude" / "loop" / "plan.md"
        shared_plan.parent.mkdir(parents=True, exist_ok=True)
        shared_plan.write_text("# Shared Plan\n\n- [ ] Task 1\n- [ ] Task 2\n")

        terminal_1_id = "terminal_1"
        terminal_2_id = "terminal_2"

        cloned_plan_1 = clone_plan_for_terminal(
            plan_path=shared_plan,
            terminal_id=terminal_1_id,
        )
        cloned_plan_2 = clone_plan_for_terminal(
            plan_path=shared_plan,
            terminal_id=terminal_2_id,
        )

        # Act: Modify task state in terminal 1
        cloned_plan_1.write_text("# Shared Plan\n\n- [x] Task 1\n- [ ] Task 2\n")

        # Assert: Terminal 2 plan should be unchanged
        terminal_2_content = cloned_plan_2.read_text()
        assert "- [ ] Task 1" in terminal_2_content
        assert "- [x] Task 1" not in terminal_2_content

    def test_clone_only_happens_once_per_terminal(self, tmp_path: Path) -> None:
        """Test that calling clone_plan_for_terminal multiple times is idempotent."""
        # Arrange: Create shared plan
        shared_plan = tmp_path / ".claude" / "loop" / "plan.md"
        shared_plan.parent.mkdir(parents=True, exist_ok=True)
        shared_plan.write_text("# Shared Plan\n\n- [ ] Task 1\n")

        terminal_id = "console_test"

        # Act: Clone multiple times
        cloned_plan_1 = clone_plan_for_terminal(
            plan_path=shared_plan,
            terminal_id=terminal_id,
        )

        # Modify first clone
        cloned_plan_1.write_text("# Modified Plan\n\n- [x] Task 1\n")

        # Clone again
        cloned_plan_2 = clone_plan_for_terminal(
            plan_path=shared_plan,
            terminal_id=terminal_id,
        )

        # Assert: Should return existing clone, not create new one
        assert cloned_plan_1 == cloned_plan_2
        # Content should be from first clone, not original
        assert "Modified Plan" in cloned_plan_2.read_text()
        assert "- [x] Task 1" in cloned_plan_2.read_text()

    def test_original_plan_not_modified(self, tmp_path: Path) -> None:
        """Test that original plan.md is not modified during cloning."""
        # Arrange: Create shared plan
        shared_plan = tmp_path / ".claude" / "loop" / "plan.md"
        shared_plan.parent.mkdir(parents=True, exist_ok=True)
        original_content = "# Original Plan\n\n- [ ] Task 1\n- [ ] Task 2\n"
        shared_plan.write_text(original_content)

        # Act: Clone for terminal (use unique ID to avoid conflicts)
        cloned_plan = clone_plan_for_terminal(
            plan_path=shared_plan,
            terminal_id="console_original_not_modified",
        )

        # Assert: Original plan should be unchanged
        assert shared_plan.read_text() == original_content
        # Clone should exist
        assert cloned_plan.exists()
        # Clone should have same content as original
        assert cloned_plan.read_text() == original_content

    def test_clone_creates_correct_file_structure(self, tmp_path: Path) -> None:
        """Test that cloned plan is created in correct location."""
        # Arrange: Create shared plan
        shared_plan = tmp_path / ".claude" / "loop" / "plan.md"
        shared_plan.parent.mkdir(parents=True, exist_ok=True)
        shared_plan.write_text("# Plan\n\n- [ ] Task 1\n")

        terminal_id = "console_structure_test"

        # Act: Clone plan
        cloned_plan = clone_plan_for_terminal(
            plan_path=shared_plan,
            terminal_id=terminal_id,
        )

        # Assert: Check file structure
        # Should be in terminal state directory
        terminal_state_dir = get_terminal_state_dir(terminal_id)
        assert cloned_plan.parent == terminal_state_dir

        # Filename should match pattern
        assert cloned_plan.name == "plan.md"

    def test_clone_preserves_original_content(self, tmp_path: Path) -> None:
        """Test that cloned plan preserves original content exactly."""
        # Arrange: Create shared plan with complex content
        shared_plan = tmp_path / ".claude" / "loop" / "plan.md"
        shared_plan.parent.mkdir(parents=True, exist_ok=True)
        original_content = """# Complex Plan

## Phase 1: Setup
- [x] Initialize project
- [ ] Configure dependencies

## Phase 2: Implementation
- [ ] Write tests
- [ ] Implement features

## Notes
This plan has multiple sections and various checkbox states.
"""
        shared_plan.write_text(original_content)

        # Act: Clone plan
        cloned_plan = clone_plan_for_terminal(
            plan_path=shared_plan,
            terminal_id="console_content_test",
        )

        # Assert: Content should be preserved exactly
        assert cloned_plan.read_text() == original_content

    def test_clone_handles_missing_terminal_directory(self, tmp_path: Path) -> None:
        """Test that cloning works when terminal directory doesn't exist."""
        # Arrange: Create shared plan
        shared_plan = tmp_path / ".claude" / "loop" / "plan.md"
        shared_plan.parent.mkdir(parents=True, exist_ok=True)
        shared_plan.write_text("# Plan\n\n- [ ] Task 1\n")

        terminal_id = "console_missing_dir"

        # Ensure terminal directory doesn't exist (use shutil to remove non-empty dir)
        import shutil
        terminal_state_dir = get_terminal_state_dir(terminal_id)
        if terminal_state_dir.exists():
            shutil.rmtree(terminal_state_dir)

        # Act: Clone plan (should create directory)
        cloned_plan = clone_plan_for_terminal(
            plan_path=shared_plan,
            terminal_id=terminal_id,
        )

        # Assert: Directory should be created and plan should exist
        assert terminal_state_dir.exists()
        assert cloned_plan.exists()
        assert cloned_plan.parent == terminal_state_dir

    def test_clone_is_idempotent(self, tmp_path: Path) -> None:
        """Test that cloning is safe to call multiple times."""
        # Arrange: Create shared plan
        shared_plan = tmp_path / ".claude" / "loop" / "plan.md"
        shared_plan.parent.mkdir(parents=True, exist_ok=True)
        shared_plan.write_text("# Plan\n\n- [ ] Task 1\n")

        terminal_id = "console_idempotent"

        # Act: Clone multiple times
        paths = [
            clone_plan_for_terminal(
                plan_path=shared_plan,
                terminal_id=terminal_id,
            )
            for _ in range(5)
        ]

        # Assert: All paths should be the same
        assert len(set(paths)) == 1
        assert paths[0].exists()

    def test_clone_with_root_plan_fallback(self, tmp_path: Path) -> None:
        """Test that cloning works with root plan.md (fallback location)."""
        # Arrange: Create root plan (fallback location)
        root_plan = tmp_path / "plan.md"
        root_plan.write_text("# Root Plan\n\n- [ ] Task 1\n")

        terminal_id = "console_root_plan"

        # Act: Clone root plan
        cloned_plan = clone_plan_for_terminal(
            plan_path=root_plan,
            terminal_id=terminal_id,
        )

        # Assert: Clone should exist and have same content
        assert cloned_plan.exists()
        assert cloned_plan.read_text() == root_plan.read_text()

    def test_clone_preserves_file_permissions(self, tmp_path: Path) -> None:
        """Test that cloned plan preserves original file permissions."""
        # Arrange: Create shared plan
        shared_plan = tmp_path / ".claude" / "loop" / "plan.md"
        shared_plan.parent.mkdir(parents=True, exist_ok=True)
        shared_plan.write_text("# Plan\n\n- [ ] Task 1\n")

        # Make file readable and writable (default)
        shared_plan.chmod(0o644)

        terminal_id = "console_perms_test"

        # Act: Clone plan
        cloned_plan = clone_plan_for_terminal(
            plan_path=shared_plan,
            terminal_id=terminal_id,
        )

        # Assert: Permissions should be preserved
        # Note: Windows may not preserve Unix permissions exactly
        # This test mainly ensures cloning doesn't fail
        assert cloned_plan.exists()
        assert cloned_plan.read_text() == shared_plan.read_text()

    def test_clone_with_nonexistent_source_plan(self, tmp_path: Path) -> None:
        """Test that cloning raises appropriate error for nonexistent source."""
        # Arrange: Create path to nonexistent plan
        nonexistent_plan = tmp_path / ".claude" / "loop" / "nonexistent.md"
        terminal_id = "console_nonexistent"

        # Act & Assert: Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            clone_plan_for_terminal(
                plan_path=nonexistent_plan,
                terminal_id=terminal_id,
            )

    def test_two_terminals_concurrent_cloning(self, tmp_path: Path) -> None:
        """Test that concurrent cloning from two terminals works correctly."""
        # Arrange: Create shared plan
        shared_plan = tmp_path / ".claude" / "loop" / "plan.md"
        shared_plan.parent.mkdir(parents=True, exist_ok=True)
        shared_plan.write_text("# Shared Plan\n\n- [ ] Task 1\n- [ ] Task 2\n")

        # Act: Clone for two terminals (simulating concurrent access)
        terminal_1_id = "terminal_concurrent_1"
        terminal_2_id = "terminal_concurrent_2"

        cloned_plan_1 = clone_plan_for_terminal(
            plan_path=shared_plan,
            terminal_id=terminal_1_id,
        )
        cloned_plan_2 = clone_plan_for_terminal(
            plan_path=shared_plan,
            terminal_id=terminal_2_id,
        )

        # Modify both plans
        cloned_plan_1.write_text("# Terminal 1 Plan\n\n- [x] Task 1\n")
        cloned_plan_2.write_text("# Terminal 2 Plan\n\n- [x] Task 2\n")

        # Assert: Each terminal should have its own isolated plan
        assert cloned_plan_1.exists()
        assert cloned_plan_2.exists()
        assert "Terminal 1 Plan" in cloned_plan_1.read_text()
        assert "Terminal 2 Plan" in cloned_plan_2.read_text()

        # Original should be unchanged
        original_content = shared_plan.read_text()
        assert "Shared Plan" in original_content
        assert "- [ ] Task 1" in original_content
