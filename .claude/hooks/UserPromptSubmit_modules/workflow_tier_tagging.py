"""
UserPromptSubmit module: Tier tagging for PROCEDURE skills

When a PROCEDURE skill is invoked via Skill() tool, this hook reads the skill's
workflow_steps from frontmatter and injects a directive requesting the model to
tag its responses with [Tier N] as it completes each step.

This makes the output self-documenting: the presence of [Tier N] tags proves
that workflow_step N was completed.

Implementation: TASK-???
Created: 2026-03-11
"""

import re
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# PROCEDURE skills that should use tier-tagging enforcement
# (Skills where Claude reads SKILL.md and executes manually, not delegated)
PROCEDURE_SKILLS = {
    "debugRCA",  # Root cause analysis with evidence tiers
    "p",  # Code maturation pipeline
    "arch",  # Architecture advisor
    # Add other PROCEDURE skills as needed
}

SKILL_NAME_ALIASES = {
    "debugRCA": ("debugRCA", "rca"),
}


def _find_skill_file(skill_name: str) -> Path | None:
    """Find skill SKILL.md file by name."""
    module_file = Path(__file__).resolve()
    project_root = module_file.parents[3]

    candidate_names = SKILL_NAME_ALIASES.get(skill_name, (skill_name,))
    candidate_paths: list[Path] = []

    for candidate_name in candidate_names:
        candidate_paths.extend(
            [
                project_root / ".claude" / "skills" / candidate_name / "SKILL.md",
                project_root / "packages" / candidate_name / "skill" / "SKILL.md",
                project_root / "packages" / candidate_name / "skills" / candidate_name / "SKILL.md",
            ]
        )

    for skill_path in candidate_paths:
        if skill_path.exists():
            return skill_path

    return None


def _parse_workflow_steps(skill_file: Path) -> list[str]:
    """Extract workflow_steps list from YAML frontmatter."""
    content = skill_file.read_text()

    # Match YAML frontmatter (between --- delimiters)
    frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not frontmatter_match:
        return []

    frontmatter_text = frontmatter_match.group(1)

    # Extract workflow_steps list
    # Match: workflow_steps:\n  - step1\n  - step2
    steps_match = re.search(r"workflow_steps:\s*\n((?:\s*-\s+\S+\n?)*)", frontmatter_text)
    if not steps_match:
        return []

    steps_text = steps_match.group(1)
    steps = re.findall(r"-\s+(\S+)", steps_text)

    return steps


def _generate_tier_directive(skill_name: str, workflow_steps: list[str]) -> str:
    """Generate workflow step directive from workflow_steps."""
    steps_listing = "\n".join(f"  [{step.upper()}]" for step in workflow_steps)

    directive = f"""**METHODOLOGY COMPLIANCE FOR {skill_name}**:

This skill has {len(workflow_steps)} documented workflow steps that must be completed:

{steps_listing}

**Required**: As you complete each workflow step, mark it with a section header using the exact step name above.

**Completion**: Only use [COMPLETE] after ALL workflow steps are documented in your output.

**Self-Audit**: Before finalizing, verify your output contains ALL {len(workflow_steps)} workflow step headers."""

    return directive


@register_hook("workflow_tier_tagging", priority=3.0)
def workflow_tier_tagging_hook(context: HookContext) -> HookResult:
    """
    Inject tier-tagging directive for PROCEDURE skills.

    Reads workflow_steps from skill frontmatter, generates directive requesting
    model to tag responses with [Tier N] as each step completes.

    Priority 3.0 (early) - runs before most other hooks to establish methodology
    expectations before other context injections.
    """
    # Check if Skill() tool is being invoked
    # Context data structure: {"tool_name": "Skill", "tool_input": {"skill": "debugRCA", ...}}
    data = context.data
    tool_name = data.get("tool_name")

    if tool_name != "Skill":
        return HookResult.empty()

    # Extract skill name from tool_input
    tool_input = data.get("tool_input", {})
    if not tool_input or "skill" not in tool_input:
        return HookResult.empty()

    skill_name = tool_input["skill"]

    # Only apply to known PROCEDURE skills
    if skill_name not in PROCEDURE_SKILLS:
        return HookResult.empty()

    # Find and read the skill file
    skill_file = _find_skill_file(skill_name)
    if not skill_file or not skill_file.exists():
        return HookResult.empty()

    # Parse frontmatter for workflow_steps
    workflow_steps = _parse_workflow_steps(skill_file)
    if not workflow_steps:
        # No workflow_steps declared - nothing to enforce
        return HookResult.empty()

    # Generate tier-tagging directive
    directive = _generate_tier_directive(skill_name, workflow_steps)

    # Log for transparency
    import sys

    print(
        f"[Tier-Tagging] Injected directive for {skill_name}: {len(workflow_steps)} workflow steps",
        file=sys.stderr,
    )

    # Return directive as additional context
    return HookResult(context=directive)
