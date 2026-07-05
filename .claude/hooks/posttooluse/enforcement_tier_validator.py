#!/usr/bin/env python3
"""
Enforcement Tier Validator

Validates that SKILL.md files declare the required frontmatter fields.

The contract is defined entirely by ``_REQUIRED_FIELDS`` below — each entry is
the single source of truth for one field's pattern, valid values, and rationale.
There is no external spec file; the dataclass ``why`` field IS the spec, so the
human-readable contract and the enforced contract cannot drift apart. Adding a
new required field = one tuple entry.

(Single-Source Dataclass Pattern, per hooks/CLAUDE.md.)
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path

from posttooluse.base import PostToolUseHook

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())


@dataclass(frozen=True)
class FrontmatterField:
    """Single-source contract for one required SKILL.md frontmatter field.

    Co-locates the field's regex, valid values, and rationale so they cannot
    drift apart. ``why`` is the inline spec — there is no external spec file.
    """

    name: str
    pattern: re.Pattern
    # None = presence-only (any value, including empty list, is valid).
    # A tuple = the field's capture group 1 must be one of these values.
    valid_values: tuple[str, ...] | None
    why: str


_REQUIRED_FIELDS: tuple[FrontmatterField, ...] = (
    FrontmatterField(
        name="enforcement",
        pattern=re.compile(
            r"^enforcement:\s*['\"]?(strict|advisory|none)['\"]?\s*$",
            re.MULTILINE,
        ),
        valid_values=("strict", "advisory", "none"),
        why=(
            "Determines whether bypassing the skill's workflow blocks (strict), "
            "warns (advisory), or does nothing (none). Defaults to strict if absent."
        ),
    ),
    FrontmatterField(
        name="workflow_steps",
        # Presence-only: matches `workflow_steps:` followed by anything (or
        # nothing) on that line — `workflow_steps: []`, `workflow_steps: [a, b]`,
        # `workflow_steps:` (block form), or `workflow_steps: '...'`. Empty list
        # is valid; it means "no workflow to enforce" (see _load_workflow_steps
        # in skill_execution_tracker.py).
        pattern=re.compile(r"^workflow_steps:.*$", re.MULTILINE),
        valid_values=None,
        why=(
            "Declares the workflow the skill enforces. Empty (`workflow_steps: []`) "
            "is valid and means no workflow to enforce."
        ),
    ),
)

DEFAULT_TIER = "strict"


def _field_label(field: FrontmatterField) -> str:
    """Human-readable label for the missing-field warning."""
    if field.valid_values is None:
        return f"'{field.name}' field (presence required; empty is valid)"
    return f"'{field.name}' field (one of: {', '.join(field.valid_values)})"


def validate_enforcement_tier(skill_path: str, content: str) -> dict:
    """
    Validate that a SKILL.md file declares all required frontmatter fields.

    Iterates ``_REQUIRED_FIELDS``. Each field is checked for presence (and value
    validity where applicable). Warnings cite the field's inline ``why`` rather
    than an external spec — the dataclass is the single source of truth.

    Args:
        skill_path: Path to the SKILL.md file (for warning text).
        content:    Full text of the SKILL.md file.

    Returns:
        Dict with 'valid', 'tier', 'warning'. 'tier' is the captured enforcement
        value, or None if the field is absent.
    """
    warnings: list[str] = []
    tier: str | None = None

    for field in _REQUIRED_FIELDS:
        match = field.pattern.search(content)
        if not match:
            warnings.append(
                f"SKILL.md at {skill_path} is missing {_field_label(field)}. "
                f"{field.why}"
            )
            continue
        # For fields with enumerated values, the regex captures the value in
        # group 1 and only matches when it's one of valid_values — so a match
        # here is already valid by construction. We still surface it as `tier`
        # for the enforcement field, which is the only enumerated field today.
        if field.name == "enforcement" and match.lastindex:
            tier = match.group(1)

    if warnings:
        return {"valid": False, "tier": tier, "warning": "\n\n".join(warnings)}
    return {"valid": True, "tier": tier, "warning": None}


class EnforcementTierValidator(PostToolUseHook):
    """
    PostToolUse hook to validate required frontmatter in SKILL.md files.

    Only runs for Write/Edit operations on SKILL.md files.
    """

    tool_matcher = {"Write", "Edit"}

    def process(self, tool_name: str, tool_input: dict, tool_response: dict) -> dict:
        """Validate required frontmatter after SKILL.md Write/Edit operations."""
        file_path = tool_input.get("file_path", "")

        if not file_path.endswith("SKILL.md"):
            return {"passed": True}

        path = Path(file_path)
        if not path.exists():
            return {"passed": True}

        # Enforcement field's pattern, for the filesystem-sync retry check below.
        enforcement = next(f for f in _REQUIRED_FIELDS if f.name == "enforcement")

        # Read with retry: Edit may not have flushed to disk yet on Windows,
        # so re-read until the enforcement field is actually parseable.
        content = None
        for _attempt in range(3):
            try:
                content = path.read_text(encoding="utf-8")
                if enforcement.pattern.search(content):
                    break
                time.sleep(0.05)
            except OSError:
                break

        if content is None:
            return {"passed": True}

        result = validate_enforcement_tier(file_path, content)

        if not result["valid"]:
            return {
                "passed": False,
                "injection": (
                    f"\n\n⚠️ ENFORCEMENT TIER VALIDATION:\n{result['warning']}\n"
                ),
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
