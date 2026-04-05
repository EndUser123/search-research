#!/usr/bin/env python3
"""
SessionStart Constraint Display Hook

Displays active project constraints when a Claude Code session starts.

This makes documentation visible to the agent before any coding begins.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Import auto-logging decorator
from __lib.hook_base import hook_main

# Add project root to path for imports
project_root = Path("P:/__csf")
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def display_constraints_banner() -> None:
    """Display constraint banner if constraints are available."""
    try:
        # Try to load from current directory or P:/__csf
        import os

        from features.constraints import load_constraints
        cwd = Path(os.getcwd())

        # Check if we're in a project with CLAUDE.md
        if (cwd / ".claude" / "CLAUDE.md").exists():
            constraints = load_constraints(cwd)
        else:
            # Try P:/__csf as fallback
            constraints = load_constraints(Path("P:/__csf"))

        # Only show banner if we have meaningful constraints
        has_constraints = (
            constraints.tdd_required
            or constraints.coverage_minimum
            or constraints.language_rules
            or constraints.forbidden_patterns
        )

        if has_constraints:
            banner = format_constraint_banner(constraints)
            # Note: Banner suppressed - any stderr is treated as "hook error" by Claude Code
            # To display constraints, use hook JSON output instead
            # print(banner, file=sys.stderr)  # REMOVED: causes false "hook error" messages

    except Exception:
        # Silently fail - this is a display enhancement only
        pass


def format_constraint_banner(constraints) -> str:
    """Format constraints as a display banner."""
    lines = []
    lines.append("")
    lines.append("════════════════════════════════════════════════════════════")
    lines.append("📋 PROJECT CONSTRAINTS ACTIVE (from CLAUDE.md)")
    lines.append("════════════════════════════════════════════════════════════")

    if constraints.tdd_required:
        lines.append("☑ TDD: RED → GREEN → REFACTOR required")

    if constraints.coverage_minimum:
        lines.append(f"☑ Coverage: {constraints.coverage_minimum}% minimum")

    if constraints.language_rules:
        lines.append("☑ Language Rules:")
        for rule in constraints.language_rules[:5]:  # Limit display
            lines.append(f"   • {rule}")

    if constraints.validation_commands:
        lines.append("☑ Validation:")
        for cmd in constraints.validation_commands[:3]:
            lines.append(f"   • {cmd}")

    lines.append("════════════════════════════════════════════════════════════")
    lines.append("")

    return "\n".join(lines)


@hook_main
def main() -> None:
    """Hook entry point."""
    display_constraints_banner()


if __name__ == "__main__":
    main()
