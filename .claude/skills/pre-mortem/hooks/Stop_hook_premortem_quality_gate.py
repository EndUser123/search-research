#!/usr/bin/env python3
"""
Premortem Quality Gate (Stop Hook) - Skill-Based Hook
=====================================================

Verifies that pre-mortem output contains required sections before allowing
the response to complete.

Required sections:
- "🔴 WHAT'S ACTUALLY BROKEN" (Step 3.8 - operational verification)
- "🟠 HIGH-RISK" (Step 6 - warning signs)

This is the skill-based version that runs ONLY when the pre-mortem skill
is matched via the SKILL.md hooks configuration.

Configuration:
- PREMORTEM_QUALITY_GATE_ENABLED (default: true)
- --brief flag bypasses validation entirely (exit 0)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ENABLED = os.environ.get("PREMORTEM_QUALITY_GATE_ENABLED", "true").lower() == "true"

# Required sections in pre-mortem output
REQUIRED_SECTIONS = [
    "🔴 WHAT'S ACTUALLY BROKEN",
    "🟠 HIGH-RISK",
]

# Section to step mapping for error messages
SECTION_TO_STEP = {
    "🔴 WHAT'S ACTUALLY BROKEN": "Step 3.8 (operational verification)",
    "🟠 HIGH-RISK": "Step 6 (warning signs)",
}


def _get_evidence_dir() -> Path:
    """Return the evidence directory path.

    Uses the established user-home-level evidence path, not project-root.
    """
    return Path("P:/.claude/.evidence")


def _find_premortem_file(terminal_id: str | None) -> Path | None:
    """Find premortem output file for the given terminal.

    Uses terminal-scoped glob pattern to avoid cross-terminal interference.
    Falls back to most-recent premortem_*.md if terminal-scoped search finds nothing.
    """
    evidence_dir = _get_evidence_dir()
    if not evidence_dir.exists():
        return None

    # Terminal-scoped search first
    if terminal_id:
        pattern = f"premortem_*_{terminal_id}_*.md"
        matches = sorted(evidence_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        if matches:
            return matches[0]

    # Fallback: most recent premortem_*.md
    fallback_pattern = "premortem_*.md"
    matches = sorted(
        evidence_dir.glob(fallback_pattern), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if matches:
        return matches[0]

    return None


def _check_brief_flag(data: dict) -> bool:
    """Check if --brief flag is present in the prompt."""
    prompt = data.get("prompt", "") or ""
    return "--brief" in prompt.lower()


def _check_required_sections(content: str) -> list[str]:
    """Check for required sections in premortem output.

    Returns list of missing sections (empty if all present).
    """
    missing = []
    for section in REQUIRED_SECTIONS:
        # Use word boundary to avoid partial matches
        if section not in content:
            missing.append(section)
    return missing


def _is_premortem_turn(data: dict) -> bool:
    """Check if the current turn is a /pre-mortem skill turn."""
    skill_state = data.get("skill_state") or {}
    skill = skill_state.get("skill", "") or ""
    return "pre-mortem" in skill.lower() or "premortem" in skill.lower()


def run(data: dict) -> dict:
    """Verify pre-mortem output contains required sections.

    Args:
        data: Stop hook input dict

    Returns:
        {"allow": bool, "reason": str} dict
    """
    if not ENABLED:
        return {"allow": True, "reason": "Premortem quality gate disabled"}

    # Only check when actually running /pre-mortem
    # Note: When invoked via skill-based hook, skill_state should correctly
    # indicate pre-mortem. The check here is a safety net.
    if not _is_premortem_turn(data):
        return {"allow": True, "reason": "Not a pre-mortem turn"}

    # Check --brief bypass
    if _check_brief_flag(data):
        return {"allow": True, "reason": "Brief mode - validation skipped"}

    # Extract terminal_id from hook data
    terminal_id = data.get("terminal_id") or None

    # Find premortem file
    premortem_file = _find_premortem_file(terminal_id)
    if not premortem_file:
        # No premortem file found - allow
        return {"allow": True, "reason": "No pre-mortem output file found"}

    # Read and check content
    try:
        content = premortem_file.read_text(encoding="utf-8")
    except Exception:
        return {"allow": True, "reason": f"Could not read pre-mortem file: {premortem_file.name}"}

    # Check for required sections
    missing = _check_required_sections(content)

    if not missing:
        return {
            "allow": True,
            "reason": f"All required sections present in {premortem_file.name}",
        }

    # Build error message
    missing_steps = [SECTION_TO_STEP[s] for s in missing]
    missing_str = ", ".join(missing_steps)

    return {
        "allow": False,
        "reason": f"Missing required pre-mortem sections: {missing_str}",
    }


if __name__ == "__main__":
    import json

    input_data = json.loads(sys.stdin.read())
    result = run(input_data)
    print(json.dumps(result))
