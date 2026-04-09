#!/usr/bin/env python3
"""
Step Header Verifier (Stop Hook)
================================

Verifies that skills with declared workflow_steps emit step headers in their output.

This is a simpler alternative to breadcrumb-based enforcement:
- No hidden state files
- No separate breadcrumb logging
- Output itself is the evidence
- Parse actual response for step headers

Shows after skill completion:
1. All documented workflow steps completed
2. Extra steps performed but not documented (opt-in via SHOW_EXTRA)
3. Missing documented steps (blocking or warning based on MODE)

Configuration:
- STEP_HEADER_VERIFIER_ENABLED (default: true)
- STEP_HEADER_VERIFIER_MODE (default: "warn" - can be "block")
- STEP_HEADER_VERIFIER_SHOW_EXTRA (default: false) - Show extra steps performed
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

ENABLED = os.environ.get("STEP_HEADER_VERIFIER_ENABLED", "true").lower() == "true"
MODE = os.environ.get("STEP_HEADER_VERIFIER_MODE", "warn").lower()
SHOW_EXTRA = os.environ.get("STEP_HEADER_VERIFIER_SHOW_EXTRA", "false").lower() == "true"


def _find_skill_file(skill_name: str) -> Path | None:
    """Find skill SKILL.md file by name."""
    # From P:/.claude/hooks/, go up to project root
    hooks_dir = Path(__file__).resolve().parent
    project_root = hooks_dir.parent.parent

    # Try project skills
    skill_path = project_root / ".claude" / "skills" / skill_name / "SKILL.md"
    if skill_path.exists():
        return skill_path

    # Try package skills
    package_path = project_root / "packages" / skill_name / "skill" / "SKILL.md"
    if package_path.exists():
        return package_path

    return None


def _parse_workflow_steps(skill_file: Path) -> list[str]:
    """Extract workflow_steps list from YAML frontmatter."""
    try:
        content = skill_file.read_text(encoding="utf-8")

        # Match YAML frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            return []

        frontmatter_text = frontmatter_match.group(1)

        # Extract workflow_steps list
        steps_match = re.search(r'workflow_steps:\s*\n((?:\s*-\s+\S+\n?)*)', frontmatter_text)
        if not steps_match:
            return []

        steps_text = steps_match.group(1)
        steps = re.findall(r'-\s+(\S+)', steps_text)

        return steps
    except Exception:
        return []


def _extract_skill_name(response: str) -> str | None:
    """Extract invoked skill name from response.

    Looks for pattern like "Invoking debugRCA skill..." or similar.
    """
    # Pattern: "Invoking {skill_name} skill" or similar
    patterns = [
        r'Invoking (\w+) skill',
        r'Skill (\w+) invoked',
        r'Calling /(\w+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def _normalize_step_name(step: str) -> str:
    """Normalize step name for consistent comparison.

    Converts to uppercase and replaces hyphens/spaces with underscores.
    Example: "tier-evidence-tagging" → "TIER_EVIDENCE_TAGGING"

    Args:
        step: Step name in any format

    Returns:
        Normalized step name (uppercase, underscores)
    """
    return step.upper().replace('-', '_').replace(' ', '_')


def _verify_step_headers(response: str, required_steps: list[str]) -> tuple[bool, list[str], list[str]]:
    """Verify that all required step headers are present in response.

    Also detects extra steps performed but not documented.

    Args:
        response: The skill's output text
        required_steps: List of step names that must be present as headers

    Returns:
        (complete, missing_steps, extra_steps) tuple
    """
    missing = []
    found_steps = set()

    # Normalize required steps for comparison
    required_normalized = [_normalize_step_name(s) for s in required_steps]

    # Detect all workflow step headers in response (more specific patterns)
    # Only match actual workflow step patterns to avoid false positives
    all_header_patterns = [
        r'\[([A-Z][A-Z_]+)\]',  # [STEP_NAME] - must start with letter, be all caps
        r'##+\s*([A-Z][A-Z_]+)',  # ## STEP_NAME - must start with letter
    ]

    for pattern in all_header_patterns:
        for match in re.finditer(pattern, response, re.MULTILINE):
            found_step = match.group(1)
            found_steps.add(found_step)

    # Check for missing required steps
    for step in required_steps:
        step_normalized = _normalize_step_name(step)

        # Check if this required step was found (in any format)
        found = False
        for found_step in found_steps:
            if _normalize_step_name(found_step) == step_normalized:
                found = True
                break

        if not found:
            missing.append(step)

    # Detect extra steps (found but not in required list)
    extra = []
    if SHOW_EXTRA:
        required_normalized_set = set(required_normalized)
        for found_step in found_steps:
            found_normalized = _normalize_step_name(found_step)
            if found_normalized not in required_normalized_set:
                extra.append(found_step)

    return (len(missing) == 0, missing, extra)


def run(data: dict) -> dict:
    """Verify step headers for invoked skills.

    Args:
        data: Stop hook input dict

    Returns:
        {"allow": bool, "reason": str} dict
    """
    # Check if enabled
    if not ENABLED:
        return {"allow": True, "reason": "Step header verifier disabled"}

    # Extract response from data
    response = data.get("assistant_response", "") or data.get("response", "")
    if not response:
        return {"allow": True, "reason": "No response to verify"}

    # Try to extract skill name from response
    skill_name = _extract_skill_name(response)
    if not skill_name:
        # Couldn't determine which skill ran - allow
        return {"allow": True, "reason": "No skill detected in response"}

    # Find skill file and parse workflow_steps
    skill_file = _find_skill_file(skill_name)
    if not skill_file:
        # Skill has no SKILL.md or no workflow_steps - allow
        return {"allow": True, "reason": f"Skill {skill_name} has no workflow steps declared"}

    required_steps = _parse_workflow_steps(skill_file)
    if not required_steps:
        # No workflow_steps declared - allow
        return {"allow": True, "reason": f"Skill {skill_name} has no workflow steps declared"}

    # Verify step headers in response
    complete, missing, extra = _verify_step_headers(response, required_steps)

    if complete:
        # All required steps present
        msg = f"All {len(required_steps)} documented workflow steps completed"
        if SHOW_EXTRA and extra:
            msg += f". {len(extra)} extra steps performed: {', '.join(extra)}"
        return {
            "allow": True,
            "reason": msg
        }
    else:
        missing_str = ", ".join(missing)
        extra_msg = ""
        if SHOW_EXTRA and extra:
            extra_msg = f"\nExtra steps performed: {', '.join(extra)}"

        if MODE == "block":
            return {
                "allow": False,
                "reason": f"Missing workflow steps: {missing_str}{extra_msg}"
            }
        else:  # warn mode
            print("\n⚠️  STEP HEADER VERIFICATION WARNING")
            print(f"Skill: {skill_name}")
            print(f"Missing documented steps ({len(missing)}): {missing_str}")
            print(f"Documented steps ({len(required_steps)}): {', '.join(required_steps)}")
            if extra:
                print(f"Extra steps performed ({len(extra)}): {', '.join(extra)}")
            print()

            return {
                "allow": True,
                "reason": f"Warning: Missing steps {missing_str} (allowed in warn mode)"
            }


if __name__ == "__main__":
    # Hook entry point
    import json

    # Read input from stdin
    input_data = json.loads(sys.stdin.read())

    # Run verification
    result = run(input_data)

    # Output result as JSON
    print(json.dumps(result))
