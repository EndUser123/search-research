#!/usr/bin/env python3
"""
Enforcement Tier Validator

Validates that SKILL.md files have the valid `enforcement` field in frontmatter.

Purpose: Prevent new skills from being created without an enforcement tier,
which would default to undefined behavior.

Valid tiers: strict, advisory, none
Default: strict (safer default)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from posttooluse.base import PostToolUseHook

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())

VALID_TIERS = ("strict", "advisory", "none")
DEFAULT_TIER = "strict"

# Pattern to match enforcement field in YAML frontmatter
ENFORCEMENT_PATTERN = re.compile(
    r"^enforcement:\s*['\"]?(strict|advisory|none)['\"]?\s*$", re.MULTILINE
)

# Pattern to match workflow_steps field in YAML frontmatter
WORKFLOW_STEPS_PATTERN = re.compile(
    r"^workflow_steps:\s*$", re.MULTILINE
)


def validate_enforcement_tier(skill_path: str, content: str) -> dict:
    """
    Validate that a SKILL.md file has a valid enforcement tier.

    Args:
        skill_path: Path to the SKILL.md file
        content: Content of the SKILL.md file

    Returns:
        Dict with 'valid', 'tier', 'warning' fields
    """
    warnings = []

    # Check if enforcement field exists
    match = ENFORCEMENT_PATTERN.search(content)

    if not match:
        warnings.append(
            f"SKILL.md at {skill_path} is missing 'enforcement' field in frontmatter. "
            f"Valid values: {', '.join(VALID_TIERS)}. "
            f"Default will be '{DEFAULT_TIER}' if not specified."
        )

    tier = match.group(1) if match else None
    if tier and tier not in VALID_TIERS:
        warnings.append(
            f"SKILL.md at {skill_path} has invalid enforcement tier '{tier}'. "
            f"Valid values: {', '.join(VALID_TIERS)}."
        )

    # Check if workflow_steps field exists (required per skill-frontmatter-fields.md)
    workflow_match = WORKFLOW_STEPS_PATTERN.search(content)
    if not workflow_match:
        warnings.append(
            f"SKILL.md at {skill_path} is missing 'workflow_steps' field in frontmatter. "
            f"This field is required per skill-frontmatter-fields.md spec."
        )

    if warnings:
        return {
            "valid": False,
            "tier": tier,
            "warning": "\n\n".join(warnings),
        }

    return {"valid": True, "tier": tier, "warning": None}


class EnforcementTierValidator(PostToolUseHook):
    """
    PostToolUse hook to validate enforcement tier in SKILL.md files.

    Only runs for Write/Edit operations on SKILL.md files.
    """

    # Only run for Write/Edit tools
    tool_matcher = {"Write", "Edit"}

    def process(self, tool_name: str, tool_input: dict, tool_response: dict) -> dict:
        """Validate enforcement tier after SKILL.md Write/Edit operations."""
        file_path = tool_input.get("file_path", "")

        # Only check SKILL.md files
        if not file_path.endswith("SKILL.md"):
            return {"passed": True}

        # Read the file content
        try:
            path = Path(file_path)
            if not path.exists():
                return {"passed": True}

            content = path.read_text(encoding="utf-8")
        except OSError:
            return {"passed": True}

        # Validate enforcement tier
        result = validate_enforcement_tier(file_path, content)

        if not result["valid"]:
            return {
                "passed": False,
                "injection": (f"\n\n⚠️ ENFORCEMENT TIER VALIDATION:\n{result['warning']}\n"),
            }

        return {"passed": True}


# Legacy main() for standalone execution (backward compatibility)
def main():
    """Legacy entry point for direct script execution."""
    import json
    import sys

    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return

    hook = EnforcementTierValidator()
    result = hook.run(data)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
