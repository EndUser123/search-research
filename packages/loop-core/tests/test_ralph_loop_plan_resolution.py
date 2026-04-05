"""Tests for /ralph-loop skill plan path resolution logic.

This module implements the TDD GREEN phase for TASK-012, testing the plan path
resolution logic implemented in scripts/plan_resolution.py.

Plan Resolution Priority:
1. Explicit plan path argument (highest priority)
2. .claude/loop/plan.md (default location)
3. plan.{terminal_id}.md (per-terminal plan)
4. plan.md in project root (fallback)

Test Cases:
----------
- Test explicit path takes priority
- Test default .claude/loop/plan.md when no argument
- Test per-terminal plan.{terminal_id}.md resolution
- Test fallback to plan.md in project root
- Test missing plan returns None with appropriate error
- Test per-terminal plan isolation between terminals
"""

from pathlib import Path

import pytest

# Import actual implementation
from scripts.plan_resolution import resolve_plan_path

# Type aliases for test clarity
TerminalId = str
PlanPath = str | None


class TestPlanPathResolution:
    """Test plan path resolution logic for /ralph-loop skill."""

    def test_explicit_path_takes_highest_priority(self, tmp_path: Path) -> None:
        """Test that explicit plan path argument overrides all other resolution methods."""
        # Arrange: Create multiple plan files
        explicit_plan = tmp_path / "explicit.md"
        default_plan = tmp_path / ".claude" / "loop" / "plan.md"
        terminal_plan = tmp_path / "plan.console_abc123.md"
        root_plan = tmp_path / "plan.md"

        # Create all plans
        explicit_plan.write_text("# Explicit Plan")
        default_plan.parent.mkdir(parents=True, exist_ok=True)
        default_plan.write_text("# Default Plan")
        terminal_plan.write_text("# Terminal Plan")
        root_plan.write_text("# Root Plan")

        # Act: Resolve with explicit path
        result = resolve_plan_path(
            explicit_arg=str(explicit_plan),
            terminal_id="console_abc123",
            project_root=tmp_path,
        )

        # Assert: Should return explicit path
        assert result == str(explicit_plan)

    def test_default_claude_loop_plan_when_no_explicit_path(self, tmp_path: Path) -> None:
        """Test that .claude/loop/plan.md is used when no explicit path provided."""
        # Arrange: Create default plan
        default_plan = tmp_path / ".claude" / "loop" / "plan.md"
        default_plan.parent.mkdir(parents=True, exist_ok=True)
        default_plan.write_text("# Default Plan")

        # Act: Resolve without explicit path
        result = resolve_plan_path(
            explicit_arg=None,
            terminal_id="console_abc123",
            project_root=tmp_path,
        )

        # Assert: Should return default plan path
        assert result == str(default_plan)

    def test_per_terminal_plan_resolution(self, tmp_path: Path) -> None:
        """Test that plan.{terminal_id}.md is resolved correctly."""
        # Arrange: Create per-terminal plan
        terminal_id = "console_xyz789"
        terminal_plan = tmp_path / f"plan.{terminal_id}.md"
        terminal_plan.write_text("# Terminal-specific Plan")

        # Act: Resolve with terminal ID
        result = resolve_plan_path(
            explicit_arg=None,
            terminal_id=terminal_id,
            project_root=tmp_path,
        )

        # Assert: Should return terminal-specific plan
        assert result == str(terminal_plan)

    def test_fallback_to_root_plan_when_no_default_or_terminal(self, tmp_path: Path) -> None:
        """Test fallback to plan.md in project root when other options unavailable."""
        # Arrange: Create only root plan
        root_plan = tmp_path / "plan.md"
        root_plan.write_text("# Root Plan")

        # Act: Resolve without other plans present
        result = resolve_plan_path(
            explicit_arg=None,
            terminal_id="console_abc123",
            project_root=tmp_path,
        )

        # Assert: Should fall back to root plan
        assert result == str(root_plan)

    def test_returns_none_when_no_plan_found(self, tmp_path: Path) -> None:
        """Test that None is returned when no plan file exists."""
        # Arrange: Empty project directory
        # Act: Resolve with no plans present
        result = resolve_plan_path(
            explicit_arg=None,
            terminal_id="console_abc123",
            project_root=tmp_path,
        )

        # Assert: Should return None
        assert result is None

    def test_per_terminal_plan_isolation(self, tmp_path: Path) -> None:
        """Test that different terminals get different plan paths."""
        # Arrange: Create plans for two terminals
        terminal_a = "console_aaa111"
        terminal_b = "console_bbb222"

        plan_a = tmp_path / f"plan.{terminal_a}.md"
        plan_b = tmp_path / f"plan.{terminal_b}.md"

        plan_a.write_text("# Plan A")
        plan_b.write_text("# Plan B")

        # Act: Resolve for each terminal
        result_a = resolve_plan_path(
            explicit_arg=None,
            terminal_id=terminal_a,
            project_root=tmp_path,
        )
        result_b = resolve_plan_path(
            explicit_arg=None,
            terminal_id=terminal_b,
            project_root=tmp_path,
        )

        # Assert: Each terminal should get its own plan
        assert result_a == str(plan_a)
        assert result_b == str(plan_b)
        assert result_a != result_b

    def test_explicit_nonexistent_path_returns_path_anyway(self, tmp_path: Path) -> None:
        """Test that explicit path is returned even if file doesn't exist (validation happens later)."""
        # Arrange: Define explicit path that doesn't exist
        nonexistent = tmp_path / "nonexistent.md"

        # Act: Resolve with explicit path
        result = resolve_plan_path(
            explicit_arg=str(nonexistent),
            terminal_id="console_abc123",
            project_root=tmp_path,
        )

        # Assert: Should return explicit path regardless of existence
        assert result == str(nonexistent)

    def test_priority_order_explicit_over_default_over_terminal_over_root(
        self, tmp_path: Path
    ) -> None:
        """Test complete priority order: explicit > default > terminal > root."""
        # Arrange: Create all plan types
        explicit_plan = tmp_path / "explicit.md"
        default_plan = tmp_path / ".claude" / "loop" / "plan.md"
        terminal_plan = tmp_path / "plan.console_abc123.md"
        root_plan = tmp_path / "plan.md"

        explicit_plan.write_text("# Explicit")
        default_plan.parent.mkdir(parents=True, exist_ok=True)
        default_plan.write_text("# Default")
        terminal_plan.write_text("# Terminal")
        root_plan.write_text("# Root")

        # Test 1: Explicit overrides everything
        result = resolve_plan_path(
            explicit_arg=str(explicit_plan),
            terminal_id="console_abc123",
            project_root=tmp_path,
        )
        assert result == str(explicit_plan)

        # Test 2: Default overrides terminal and root
        result = resolve_plan_path(
            explicit_arg=None,
            terminal_id="console_abc123",
            project_root=tmp_path,
        )
        assert result == str(default_plan)

        # Test 3: Terminal overrides root
        default_plan.unlink()  # Remove default
        result = resolve_plan_path(
            explicit_arg=None,
            terminal_id="console_abc123",
            project_root=tmp_path,
        )
        assert result == str(terminal_plan)

        # Test 4: Root is fallback
        terminal_plan.unlink()  # Remove terminal
        result = resolve_plan_path(
            explicit_arg=None,
            terminal_id="console_abc123",
            project_root=tmp_path,
        )
        assert result == str(root_plan)

    def test_empty_string_explicit_arg_treated_as_none(self, tmp_path: Path) -> None:
        """Test that empty string for explicit arg is treated as None (auto-resolve)."""
        # Arrange: Create default plan
        default_plan = tmp_path / ".claude" / "loop" / "plan.md"
        default_plan.parent.mkdir(parents=True, exist_ok=True)
        default_plan.write_text("# Default Plan")

        # Act: Resolve with empty string explicit arg
        result = resolve_plan_path(
            explicit_arg="",
            terminal_id="console_abc123",
            project_root=tmp_path,
        )

        # Assert: Should resolve to default plan, not empty string
        assert result == str(default_plan)


class TestPlanResolutionIntegration:
    """Integration tests for plan resolution with loop-core components."""

    def test_plan_resolution_with_state_manager(self, tmp_path: Path) -> None:
        """Test that resolved plan path works with TerminalStateManager."""
        from scripts.state_manager import TerminalStateManager

        # Arrange: Create a plan file
        plan = tmp_path / "plan.md"
        plan.write_text("# Test Plan\n\n- [ ] TASK-001 Test task")

        # Act: Resolve plan path and initialize state manager
        resolved = resolve_plan_path(
            explicit_arg=None,
            terminal_id="test_terminal",
            project_root=tmp_path,
        )

        # Assert: Should successfully initialize state manager with resolved plan
        assert resolved is not None
        manager = TerminalStateManager(terminal_id="test_terminal")
        assert manager is not None


class TestPlanResolutionErrorHandling:
    """Test error handling and edge cases for plan path resolution."""

    def test_handles_symlinks_correctly(self, tmp_path: Path) -> None:
        """Test that symlinks are resolved correctly."""
        # This test is platform-dependent and may be skipped on Windows
        # without proper permissions
        try:
            # Arrange: Create symlink to plan
            real_plan = tmp_path / "real_plan.md"
            real_plan.write_text("# Real Plan")
            symlink_plan = tmp_path / "link_plan.md"

            # Create symlink (may fail on Windows without admin)
            symlink_plan.symlink_to(real_plan)

            # Act: Resolve plan
            result = resolve_plan_path(
                explicit_arg=str(symlink_plan),
                terminal_id="console_abc123",
                project_root=tmp_path,
            )

            # Assert: Should resolve symlink
            assert result == str(symlink_plan)

        except OSError:
            pytest.skip("Symlink creation not supported (Windows permissions)")

    def test_handles_relative_paths(self, tmp_path: Path) -> None:
        """Test that relative paths are handled correctly."""
        # Arrange: Create plan and use relative path
        plan = tmp_path / "subdir" / "plan.md"
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text("# Relative Plan")

        # Act: Resolve with relative path
        result = resolve_plan_path(
            explicit_arg="subdir/plan.md",
            terminal_id="console_abc123",
            project_root=tmp_path,
        )

        # Assert: Should return relative path as-is
        assert result == "subdir/plan.md"

    def test_handles_absolute_paths(self, tmp_path: Path) -> None:
        """Test that absolute paths are handled correctly."""
        # Arrange: Create plan with absolute path
        plan = tmp_path / "absolute.md"
        plan.write_text("# Absolute Plan")

        # Act: Resolve with absolute path
        result = resolve_plan_path(
            explicit_arg=str(plan.absolute()),
            terminal_id="console_abc123",
            project_root=tmp_path,
        )

        # Assert: Should return absolute path
        assert result == str(plan.absolute())

    def test_terminal_id_sanitization(self, tmp_path: Path) -> None:
        """Test that special characters in terminal ID are sanitized."""
        # Arrange: Create plan with sanitized terminal ID
        terminal_id = "console:with/special"
        sanitized_id = "console_with_special"  # Expected sanitized version

        plan = tmp_path / f"plan.{sanitized_id}.md"
        plan.write_text("# Sanitized Terminal Plan")

        # Act: Resolve with unsanitized terminal ID
        result = resolve_plan_path(
            explicit_arg=None,
            terminal_id=terminal_id,
            project_root=tmp_path,
        )

        # Assert: Should find sanitized plan
        assert result == str(plan)
