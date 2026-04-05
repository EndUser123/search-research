#!/usr/bin/env python3
"""
PreToolUse_skill_metadata_advisory.py
=====================================

Advisory hook that warns when skills are invoked without workflow_steps
or enforcement in their SKILL.md frontmatter.

This is an ADVISORY hook - it warns but never blocks. It helps identify
skills that need metadata enrichment.

ADVISORY: Non-blocking - emits warnings via hookSpecificOutput.advisory
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Import hook base
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from __lib.hook_base import hook_main


def _load_skill_metadata(skill_name: str) -> dict:
    """Load workflow_steps and enforcement from skill's SKILL.md frontmatter.

    Args:
        skill_name: Skill name (without slash)

    Returns:
        Dict with 'workflow_steps' (list) and 'enforcement' (str) keys.
    """
    import yaml

    result = {"workflow_steps": [], "enforcement": None}
    skill_dir = Path("P:/.claude/skills") / skill_name.lower()
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.exists():
        return result

    try:
        content = skill_file.read_text(encoding="utf-8", errors="replace")
        parts = content.split("---")
        if len(parts) < 3:
            return result
        fm_data = yaml.safe_load(parts[1])
        if not isinstance(fm_data, dict):
            return result

        wf_steps = fm_data.get("workflow_steps", [])
        if isinstance(wf_steps, list):
            result["workflow_steps"] = wf_steps

        enforcement = fm_data.get("enforcement")
        if enforcement:
            result["enforcement"] = str(enforcement).lower()

    except Exception:
        pass

    return result


def _build_warning(skill_name: str, metadata: dict) -> str:
    """Build advisory warning message for missing metadata."""
    warnings = []

    has_steps = len(metadata["workflow_steps"]) > 0
    has_enforcement = metadata["enforcement"] is not None

    if not has_steps and not has_enforcement:
        warnings.append(
            f"⚠️ Skill /{skill_name} is missing both workflow_steps AND enforcement in SKILL.md frontmatter"
        )
        warnings.append("  Add workflow_steps to define the skill's execution workflow")
        warnings.append("  Add enforcement: strict|advisory|none to enable enforcement")
    elif not has_steps:
        warnings.append(f"⚠️ Skill /{skill_name} is missing workflow_steps in SKILL.md frontmatter")
        warnings.append("  Add workflow_steps to define the skill's execution workflow")
    elif not has_enforcement:
        warnings.append(f"⚠️ Skill /{skill_name} is missing enforcement in SKILL.md frontmatter")
        warnings.append("  Add enforcement: strict|advisory|none to enable enforcement")

    if warnings:
        warnings.append("")
        warnings.append("Skills with proper metadata enable:")
        warnings.append("  • Breadcrumb tracking for workflow progress")
        warnings.append("  • Constitutional enforcement (strict/advisory/none)")
        warnings.append("  • Skill-first gate enforcement")

    return "\n".join(warnings)


def handle_pre_tool_use(data: dict) -> dict:
    """Check if Skill tool is invoked and warn about missing metadata.

    Args:
        data: Hook input dict with tool_name, input, etc.

    Returns:
        Dict with hookSpecificOutput.advisory when skill is missing metadata.
    """
    tool_name = data.get("tool_name", "")
    tool_input = data.get("input", {})

    # Only check Skill tool invocations
    if tool_name != "Skill":
        return {}

    # Get skill name from input
    skill_name = tool_input.get("skill", "")
    if not skill_name:
        return {}

    # Normalize skill name
    skill_name = skill_name.lstrip("/").strip()

    # Load metadata from SKILL.md
    metadata = _load_skill_metadata(skill_name)

    # Build warning if metadata is missing
    if not metadata["workflow_steps"] or not metadata["enforcement"]:
        warning = _build_warning(skill_name, metadata)
        return {
            "decision": "allow",
            "hookSpecificOutput": {"advisory": warning},
        }

    return {}


@hook_main
def main() -> None:
    """Hook entry point - handles JSON input from stdin."""
    try:
        payload = json.loads(sys.stdin.read())
        result = handle_pre_tool_use(payload)
        print(json.dumps(result))
        sys.exit(0)

    except json.JSONDecodeError:
        print(json.dumps({}))
        sys.exit(0)

    except Exception:
        # Fail open - advisory should never block
        print(json.dumps({}))
        sys.exit(0)


if __name__ == "__main__":
    main()
