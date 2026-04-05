#!/usr/bin/env python3
"""Helper script for /ralph-loop skill to demonstrate plan resolution.

This script demonstrates how the /ralph-loop skill resolves plan paths
using the 4-tier priority system. It's primarily for testing and
documentation purposes.

Usage:
    python scripts/ralph_loop_entry.py [--plan PATH] [--terminal-id ID]

Examples:
    # Auto-resolve plan path
    python scripts/ralph_loop_entry.py

    # Explicit plan path
    python scripts/ralph_loop_entry.py --plan custom.md

    # Specify terminal ID
    python scripts/ralph_loop_entry.py --terminal-id console_abc123
"""

import argparse
import shutil
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.plan_resolution import (
    PlanResolutionError,
    resolve_plan_path_with_validation,
)
from scripts.state_paths import get_terminal_state_dir
from scripts.terminal_detection import get_terminal_id


def clone_plan_for_terminal(plan_path: Path, terminal_id: str) -> Path:
    """Clone shared plan to per-terminal state directory for isolation.

    This function implements TASK-013 per-terminal plan cloning, enabling
    multiple terminals to operate on isolated plan files without overwriting
    each other's task state.

    Cloning Behavior:
    - Only clones once per terminal (detects existing clone)
    - Preserves original plan content exactly
    - Creates terminal state directory if needed
    - Returns path to cloned plan (or existing clone if already cloned)

    Args:
        plan_path: Path to shared plan file (e.g., .claude/loop/plan.md)
        terminal_id: Terminal identifier for terminal-scoped state

    Returns:
        Path to cloned plan file in terminal state directory

    Raises:
        FileNotFoundError: If source plan_path doesn't exist

    Examples:
        >>> # Clone default plan for terminal
        >>> shared_plan = Path(".claude/loop/plan.md")
        >>> cloned = clone_plan_for_terminal(shared_plan, "console_abc123")
        >>> # Returns: .claude/state/terminals/console_abc123/plan.md

        >>> # Clone root plan for terminal
        >>> root_plan = Path("plan.md")
        >>> cloned = clone_plan_for_terminal(root_plan, "console_xyz789")
        >>> # Returns: .claude/state/terminals/console_xyz789/plan.md

    Implementation Notes:
        - Uses get_terminal_state_dir() for consistent terminal state paths
        - Idempotent: safe to call multiple times for same terminal
        - Checks if clone exists before copying (prevents overwriting)
        - Uses shutil.copy2 to preserve file metadata and permissions
    """
    # Validate source plan exists
    if not plan_path.exists():
        raise FileNotFoundError(
            f"Source plan file not found: {plan_path}"
        )

    # Get terminal state directory (creates if needed)
    terminal_state_dir = get_terminal_state_dir(terminal_id)

    # Path to cloned plan
    cloned_plan = terminal_state_dir / "plan.md"

    # Clone only if doesn't already exist (idempotent)
    if not cloned_plan.exists():
        # Create terminal state directory if needed
        terminal_state_dir.mkdir(parents=True, exist_ok=True)

        # Copy plan preserving metadata and permissions
        shutil.copy2(plan_path, cloned_plan)

    return cloned_plan


def main() -> int:
    """Main entry point for plan resolution demonstration."""
    parser = argparse.ArgumentParser(
        description="Demonstrate plan path resolution for /ralph-loop skill"
    )
    parser.add_argument(
        "--plan",
        type=str,
        default=None,
        help="Explicit plan path (overrides auto-resolution)",
    )
    parser.add_argument(
        "--terminal-id",
        type=str,
        default=None,
        help="Terminal ID for per-terminal plan resolution",
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed resolution process",
    )

    args = parser.parse_args()

    # Get terminal ID
    terminal_id = args.terminal_id or get_terminal_id()

    # Get project root
    project_root = Path(args.project_root).resolve()

    if args.verbose:
        print(f"Terminal ID: {terminal_id}")
        print(f"Project root: {project_root}")
        print(f"Explicit plan: {args.plan or 'None'}")
        print()

    # Resolve plan path with validation
    try:
        resolved_path, is_valid, diagnostic = resolve_plan_path_with_validation(
            explicit_arg=args.plan,
            terminal_id=terminal_id,
            project_root=project_root,
        )

        if resolved_path:
            print(f"Resolved plan: {resolved_path}")
            print(f"Valid: {is_valid}")
            print(f"Diagnostic: {diagnostic}")

            if not is_valid:
                print()
                print("Warning: Plan file validation failed")
                print("The loop may not execute correctly")
                return 1

            return 0
        else:
            print("Error: No plan file found")
            print()
            print("Searched locations (in priority order):")
            print(f"  1. {project_root / '.claude' / 'loop' / 'plan.md'}")
            print(f"  2. {project_root / f'plan.{terminal_id}.md'}")
            print(f"  3. {project_root / 'plan.md'}")
            print()
            print("Solution: Create a plan file or use --plan argument")
            return 1

    except PlanResolutionError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
