"""Skill Compliance Indicator Module.

⚠️  DEPRECATED 2026-03-11: Pre-run indicator redundant with step headers

This module showed breadcrumb status before skill execution, but:
- workflow_tier_tagging.py now directs skills to emit step headers in output
- StopHook_step_header_verifier.py verifies those headers
- Output itself provides visibility during execution

Original documentation:

Provides pre-execution visibility into skill workflow compliance:
- Enforcement level (STRICT/STANDARD/MINIMAL)
- Workflow steps declared
- Current breadcrumb progress
- Historical completion rate
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Constants
SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "skills"

# State directory for breadcrumb history
HOOKS_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = HOOKS_DIR / "state"
FALLBACK_STATE_DIR = Path.home() / ".claude_hooks" / "state"


def _extract_skill_name(prompt: str) -> str | None:
    """Extract skill name from slash command prompt.

    Args:
        prompt: User prompt text

    Returns:
        Skill name (without slash) or None
    """
    # Normalize leading terminal prompt glyphs
    stripped = prompt.strip()
    stripped = re.sub(r'^\s*(?:[❯›»>$#]+\s*)+', '', stripped)

    # Match slash command
    match = re.match(r'^/([a-z0-9-]+)', stripped, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _read_skill_frontmatter(skill_name: str) -> dict:
    """Read skill's SKILL.md frontmatter.

    Args:
        skill_name: Name of the skill (without slash)

    Returns:
        Frontmatter dict with enforcement_level and workflow_steps
    """
    skill_md = SKILLS_DIR / skill_name / "SKILL.md"

    if not skill_md.exists():
        return {}

    try:
        content = skill_md.read_text(encoding="utf-8")

        # Remove UTF-8 BOM if present
        if content.startswith("\ufeff"):
            content = content[1:]

        # Extract YAML frontmatter
        frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
        if not frontmatter_match:
            return {}

        frontmatter_text = frontmatter_match.group(1)

        # Parse key fields
        result = {}
        in_workflow_steps = False

        for line in frontmatter_text.split("\n"):
            line = line.strip()

            # Parse enforcement_level
            if line.startswith("enforcement_level:"):
                result["enforcement_level"] = line.split(":", 1)[1].strip().upper()

            # Parse workflow_steps
            elif line.startswith("workflow_steps:"):
                result["workflow_steps"] = []
                in_workflow_steps = True
                continue

            # Collect workflow step names
            if in_workflow_steps and line.startswith("- "):
                step = line[2:].strip()
                if "workflow_steps" in result:
                    result["workflow_steps"].append(step)
            elif in_workflow_steps and line and not line.startswith(" "):
                in_workflow_steps = False

        return result

    except Exception:
        return {}


def _get_breadcrumb_trail(skill_name: str) -> dict:
    """Get current breadcrumb trail for skill.

    Args:
        skill_name: Name of the skill

    Returns:
        Breadcrumb trail dict or empty dict
    """
    try:
        from skill_guard.breadcrumb import get_breadcrumb_trail
        trail = get_breadcrumb_trail(skill_name)
        return trail if trail is not None else {}
    except Exception:
        return {}


def _get_historical_completion_rate(skill_name: str, days: int = 7) -> float | None:
    """Calculate historical completion rate from breadcrumb logs.

    Args:
        skill_name: Name of the skill
        days: Number of days to look back

    Returns:
        Completion rate (0.0 to 1.0) or None if no history
    """
    try:
        from skill_guard.breadcrumb.log import BreadcrumbLog

        log = BreadcrumbLog()
        cutoff = datetime.now() - timedelta(days=days)

        # Get completed and incomplete runs
        completed = 0
        incomplete = 0

        for entry in log.get_history(skill_name, since=cutoff):
            if entry.get("status") == "complete":
                completed += 1
            elif entry.get("status") == "incomplete":
                incomplete += 1

        total = completed + incomplete
        if total == 0:
            return None

        return completed / total

    except Exception:
        return None


def _format_compliance_indicator(skill_name: str, frontmatter: dict, trail: dict, completion_rate: float | None) -> str:
    """Format compliance indicator for display.

    Args:
        skill_name: Name of the skill
        frontmatter: Skill frontmatter data
        trail: Current breadcrumb trail
        completion_rate: Historical completion rate

    Returns:
        Formatted indicator string
    """
    lines = []

    # Enforcement level
    enforcement_level = frontmatter.get("enforcement_level", "STANDARD")
    lines.append(f"📍 **/{skill_name}** [{enforcement_level} enforcement]")

    # Workflow steps
    workflow_steps = frontmatter.get("workflow_steps", [])
    if workflow_steps:
        total_steps = len(workflow_steps)
        lines.append(f"   **Workflow**: {total_steps} steps declared")
    else:
        lines.append("   **Workflow**: No workflow steps declared")

    # Current progress
    if trail and workflow_steps:
        completed_steps = trail.get("completed_steps", [])
        completed_count = len(completed_steps)
        progress = f"{completed_count}/{total_steps}"

        if completed_count > 0:
            lines.append(f"   **Current**: {progress} steps active")
        else:
            lines.append(f"   **Current**: {progress} - No active trail")

    # Historical completion rate
    if completion_rate is not None:
        percentage = int(completion_rate * 100)
        lines.append(f"   **History**: {percentage}% completion rate (last 7 days)")

    return "\n".join(lines) + "\n"


# Hook registration for UserPromptSubmit event
# Priority 6.0 runs after skill_enforcer (1.0) but before main processing
@register_hook("skill_compliance_indicator", priority=6.0)
def skill_compliance_indicator_hook(context: HookContext) -> HookResult:
    """Show skill compliance indicator on slash command invocation.

    This hook provides visibility into:
    - Enforcement level (STRICT/STANDARD/MINIMAL)
    - Workflow steps declared
    - Current breadcrumb progress
    - Historical completion rate

    Only triggers on slash commands; silently skips non-command prompts.
    """
    # Skip if not a slash command
    skill_name = _extract_skill_name(context.prompt)
    if not skill_name:
        return HookResult.empty()

    # Read skill frontmatter
    frontmatter = _read_skill_frontmatter(skill_name)

    # Get current breadcrumb trail
    trail = _get_breadcrumb_trail(skill_name)

    # Calculate historical completion rate
    completion_rate = _get_historical_completion_rate(skill_name)

    # Format and return indicator
    indicator = _format_compliance_indicator(skill_name, frontmatter, trail, completion_rate)

    # Estimate tokens (rough estimate: ~4 chars per token)
    token_count = len(indicator) // 4

    return HookResult(
        context=indicator,
        tokens=token_count,
        priority=6.0
    )
