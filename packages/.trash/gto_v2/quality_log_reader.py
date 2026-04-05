#!/usr/bin/env python3
"""Quality Log Reader for GTO skill.

Provides functions to read and format quality log entries for display
in the "Did You Forget Anything?" checklist.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add hooks lib to path for quality_log import
_hooks_lib = Path("P:/.claude/hooks/__lib")
if str(_hooks_lib) not in sys.path:
    sys.path.insert(0, str(_hooks_lib))

from quality_log import CODE_QUALITY_SKILLS, get_skills_not_run_recently


def format_quality_status(days: int = 7, project_root: str | Path | None = None) -> str:
    """Format quality skill usage status for GTO display.

    Args:
        days: Days threshold for "recently used"
        project_root: Project directory (uses cwd if None)

    Returns:
        Formatted string for display in GTO output, or empty string if all skills used recently
    """
    skills_not_recent = get_skills_not_run_recently(
        days=days, project_root=project_root
    )

    if not skills_not_recent:
        return ""

    # Format the output
    lines = []
    lines.append("  • 🟦 **Code quality skills not recently used**:")

    for skill, last_run in sorted(skills_not_recent.items()):
        if last_run is None:
            lines.append(f"    - {skill}: **Never run**")
        else:
            # Parse timestamp and calculate days ago
            try:
                dt = datetime.fromisoformat(last_run)
                days_ago = (datetime.now(timezone.utc) - dt).days
                lines.append(f"    - {skill}: Last run {days_ago} days ago")
            except (ValueError, OSError):
                lines.append(f"    - {skill}: Last run {last_run}")

    lines.append("")
    lines.append(
        f"  **Recommendation**: Run quality skills if not used within {days} days:"
    )

    # Group skills by category
    verification = ["verify", "trace"]
    inspection = ["uci", "q", "r"]
    improvement = ["simplify", "refactor"]
    adversarial = [k for k in skills_not_recent if k.startswith("adversarial-")]
    tdd = ["tdd"]

    categories = []
    if any(s in skills_not_recent for s in verification):
        categories.append("/verify or /trace (verification)")
    if any(s in skills_not_recent for s in inspection):
        categories.append("/uci, /q, or /r (inspection)")
    if any(s in skills_not_recent for s in improvement):
        categories.append("/simplify or /refactor (improvement)")
    if adversarial:
        categories.append("/adversarial-review (9-agent stress testing)")
    if "tdd" in skills_not_recent:
        categories.append("/tdd (test-driven development)")

    for i, cat in enumerate(categories, 1):
        lines.append(f"  {i}. {cat}")

    return "\n".join(lines)


def get_quality_summary(project_root: str | Path | None = None) -> dict:
    """Get summary of quality skill usage.

    Args:
        project_root: Project directory (uses cwd if None)

    Returns:
        Dict with keys:
        - total_skills: Total number of tracked skills
        - used_recently: Skills used within 7 days
        - not_used_recently: Skills not used within 7 days
        - never_run: Skills that have never been run
    """
    skills_not_recent = get_skills_not_run_recently(days=7, project_root=project_root)

    never_run = [s for s, t in skills_not_recent.items() if t is None]
    used_recently = [s for s in CODE_QUALITY_SKILLS if s not in skills_not_recent]
    not_used_recently = [s for s, t in skills_not_recent.items() if t is not None]

    return {
        "total_skills": len(CODE_QUALITY_SKILLS),
        "used_recently": used_recently,
        "not_used_recently": not_used_recently,
        "never_run": never_run,
    }


if __name__ == "__main__":
    # CLI for testing
    import argparse

    parser = argparse.ArgumentParser(description="Check quality skill usage")
    parser.add_argument(
        "--days", type=int, default=7, help="Days threshold (default: 7)"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.json:
        summary = get_quality_summary()
        print(json.dumps(summary, indent=2))
    else:
        output = format_quality_status(days=args.days)
        if output:
            print(output)
        else:
            print("All quality skills have been used recently.")
