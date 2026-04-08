# Pre-Mortem Target: skill_metadata_advisory.py

## Type
Hook (UserPromptSubmit module)

## Description
UserPromptSubmit hook that injects frontmatter advisories when skills are invoked without proper workflow_steps/enforcement in their SKILL.md.

## Files
- Primary: `P:\.claude/hooks/UserPromptSubmit_modules/skill_metadata_advisory.py`
- Registration: `P:\.claude/hooks/UserPromptSubmit_modules/registry.py` (line 634: added to core_hook_modules)

## Source Code

```python
#!/usr/bin/env python3
"""
Skill Metadata Advisory Hook
===========================

UserPromptSubmit hook that warns when skills are invoked without
proper frontmatter (workflow_steps, enforcement) in their SKILL.md.

This is where advisories belong - UserPromptSubmit can inject content
into the conversation that users will actually see.
"""

from __future__ import annotations

import re
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Patterns that indicate skill invocation
SKILL_INVOCATION_PATTERNS = [
    r"(?:^|\s)/[a-zA-Z][a-zA-Z0-9_-]*\b",  # /skill-name pattern (start of string or after whitespace)
]


def _load_skill_metadata(skill_name: str) -> dict:
    """Load workflow_steps and enforcement from skill's SKILL.md frontmatter."""
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
            f"⚠️ **Skill /{skill_name}** is missing both `workflow_steps` AND `enforcement` in SKILL.md frontmatter"
        )
        warnings.append("- Add `workflow_steps:` to define the skill's execution workflow")
        warnings.append("- Add `enforcement: strict|advisory|none` to enable enforcement")
    elif not has_steps:
        warnings.append(f"⚠️ **Skill /{skill_name}** is missing `workflow_steps` in SKILL.md frontmatter")
        warnings.append("- Add `workflow_steps:` to define the skill's execution workflow")
    elif not has_enforcement:
        warnings.append(f"⚠️ **Skill /{skill_name}** is missing `enforcement` in SKILL.md frontmatter")
        warnings.append("- Add `enforcement: strict|advisory|none` to enable enforcement")

    if warnings:
        warnings.append("")
        warnings.append("**Why this matters**:")
        warnings.append("- Skills with proper metadata enable breadcrumb tracking")
        warnings.append("- Constitutional enforcement (strict/advisory/none tiers)")
        warnings.append("- Skill-first gate enforcement")

    return "\n".join(warnings)


@register_hook("skill_metadata_advisory", priority=3.0)
def skill_metadata_advisory_hook(context: HookContext) -> HookResult:
    """Hook function that injects frontmatter advisory when skills are invoked.

    Args:
        context: Hook context containing user message

    Returns:
        HookResult with advisory injection if skill missing metadata
    """
    user_message = context.data.get("userMessage", "")

    # Check if user is invoking a skill
    skill_match = None
    for pattern in SKILL_INVOCATION_PATTERNS:
        match = re.search(pattern, user_message)
        if match:
            skill_match = match.group(0).lstrip("/")
            break

    if not skill_match:
        return HookResult.empty()

    # Load metadata from SKILL.md
    metadata = _load_skill_metadata(skill_match)

    # Build warning if metadata is missing
    if not metadata["workflow_steps"] or not metadata["enforcement"]:
        warning = _build_warning(skill_match, metadata)
        return HookResult(context=warning, tokens=len(warning.split()) * 1.3)

    return HookResult.empty()


# For testing
if __name__ == "__main__":
    import sys

    test_cases = [
        ("/rns", True),
        ("/arch", True),
        ("not a skill invocation", False),
    ]

    print("Skill Metadata Advisory Self-Test")
    print("=" * 50)

    for msg, should_trigger in test_cases:
        context = HookContext(prompt=msg, data={"userMessage": msg})
        result = skill_metadata_advisory_hook(context)
        has_output = result.context is not None and len(result.context) > 0

        status = "✓" if has_output == should_trigger else "✗"
        print(f"{status} '{msg}' -> triggered={has_output} (expected {should_trigger})")
```

## Test Cases from Session
- `/rns` -> triggered=True (missing workflow_steps) ✓
- `/arch` -> triggered=False (has workflow_steps + enforcement) ✓
- "not a skill invocation" -> triggered=False ✓

## Implementation Notes
- Regex pattern fixed to handle `/` character (not a word character)
- HookContext requires `prompt` argument (fixed in tests)
- Registration added to `core_hook_modules` list in registry.py line 634
- Uses UserPromptSubmit event type for content injection (PreToolUse doesn't display to users)
