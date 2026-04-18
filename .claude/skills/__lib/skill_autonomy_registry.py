"""Skill autonomy classification registry for consultation pattern fix.

Classifies skill invocations into execution tiers:
- PRE_AUTHORIZED: Execute immediately (sufficient deterministic context)
- AMBIGUOUS: Ask one question max (missing or conflicting signals)
- BLOCKING: Route to approval gate (high-risk operation)

Used by PreToolUse_context_sufficiency_gate to determine whether
a skill invocation should proceed without consultation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Tier(Enum):
    """Execution tier for skill invocation."""

    PRE_AUTHORIZED = "pre_authorized"
    AMBIGUOUS = "ambiguous"
    BLOCKING = "blocking"


@dataclass(frozen=True)
class SkillClassification:
    """Classification result for a skill invocation."""

    tier: Tier
    reason: str


# ---------------------------------------------------------------------------
# Classification rules
# ---------------------------------------------------------------------------

#: Regex pattern to detect an ADR path in skill arguments
_ADR_ARG_PATTERN = re.compile(
    r"(?:ADR|adr)[-_](\d{8})[-_][a-zA-Z0-9_-]+\.md",
    re.IGNORECASE,
)

#: Skills that are blocking ONLY when paired with destructive args (not on name alone)
_BLOCKING_SKILLS = frozenset({
    "cleanup",
    "purge",
    "destroy",
    "reset",
    "wipe",
})


def _is_adr_path_in_args(args: dict) -> bool:
    """Return True if arguments contain an ADR path."""
    for val in args.values():
        if isinstance(val, str):
            # Match ADR filename pattern
            if _ADR_ARG_PATTERN.search(val):
                return True
            # Match explicit __csf/design_decisions/... paths
            if "arch_decisions" in val and val.endswith(".md"):
                return True
    return False


def _is_planning_skill(skill_name: str) -> bool:
    """Return True if this is a planning-adjacent skill."""
    return skill_name in ("planning", "plan", "planner")


def _is_verify_skill(skill_name: str) -> bool:
    """Return True if this is a verification skill."""
    return skill_name in ("verify", "v", "validate", "spec-compliance")


def _is_blocking_operation(skill_name: str, args: dict) -> bool:
    """Return True if this describes a high-risk operation.

    Blocking requires BOTH a blocking-skill name AND destructive-sounding args.
    A bare blocking skill (e.g. 'cleanup' with no args) is AMBIGUOUS,
    not BLOCKING — the user might be asking what the skill does.
    """
    skill_lower = skill_name.lower()
    if skill_lower not in _BLOCKING_SKILLS:
        return False
    # Check for destructive-sounding args (required for blocking)
    for val in args.values():
        if isinstance(val, str):
            lower = val.lower()
            if any(kw in lower for kw in ("delete", "destroy", "purge", "wipe", "reset", "hard", "deep")):
                return True
    return False


# ---------------------------------------------------------------------------
# Main classification function
# ---------------------------------------------------------------------------

def classify_skill_invocation(skill_name: str, args: dict) -> SkillClassification:
    """Classify a skill invocation into an execution tier.

    Args:
        skill_name: Name of the skill being invoked (e.g. "planning")
        args: Dictionary of arguments passed to the skill

    Returns:
        SkillClassification with tier and reason

    Examples:
        >>> classify_skill_invocation("planning", {"adr_path": "ADR-20260329-foo.md"})
        SkillClassification(tier=Tier.PRE_AUTHORIZED, reason='ADR path detected')
        >>> classify_skill_invocation("planning", {})
        SkillClassification(tier=Tier.AMBIGUOUS, reason='No deterministic context')
    """
    # Blocking tier: high-risk operations
    if _is_blocking_operation(skill_name, args):
        return SkillClassification(
            tier=Tier.BLOCKING,
            reason="High-risk operation requires approval gate",
        )

    # PRE_AUTHORIZED rules
    if _is_planning_skill(skill_name) and _is_adr_path_in_args(args):
        return SkillClassification(
            tier=Tier.PRE_AUTHORIZED,
            reason="ADR path detected — sufficient deterministic context",
        )

    if _is_verify_skill(skill_name) and _is_adr_path_in_args(args):
        return SkillClassification(
            tier=Tier.PRE_AUTHORIZED,
            reason="File path detected — sufficient deterministic context",
        )

    # Default: ambiguous (one question is permitted)
    return SkillClassification(
        tier=Tier.AMBIGUOUS,
        reason="No deterministic context — ambiguous invocation",
    )


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    test_cases = [
        # (skill_name, args, expected_tier)
        ("planning", {"adr_path": "ADR-20260329-foo.md"}, Tier.PRE_AUTHORIZED),
        ("planning", {}, Tier.AMBIGUOUS),
        ("planning", {"path": "__csf/design_decisions/ADR-20260329-bar.md"}, Tier.PRE_AUTHORIZED),
        ("verify", {"file": "foo.md"}, Tier.AMBIGUOUS),  # No arch_decisions
        ("verify", {"file": "__csf/design_decisions/ADR-20260329-baz.md"}, Tier.PRE_AUTHORIZED),
        ("cleanup", {"scope": "delete everything"}, Tier.BLOCKING),  # Destructive args
        ("cleanup", {}, Tier.AMBIGUOUS),  # No destructive args
        ("planning", {"type": "cleanup"}, Tier.AMBIGUOUS),  # Not destructive, just planning
        ("destroy", {"target": "delete_all"}, Tier.BLOCKING),  # Named blocking skill + destructive
        ("reset", {}, Tier.AMBIGUOUS),  # Named blocking skill, no destructive args
    ]

    passed = 0
    failed = 0
    for skill_name, args, expected_tier in test_cases:
        result = classify_skill_invocation(skill_name, args)
        status = "PASS" if result.tier == expected_tier else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        print(f"[{status}] {skill_name!r} + {args!r} -> {result.tier.value} (expected {expected_tier.value})", file=sys.stderr)

    print(f"\n{passed}/{passed+failed} passed", file=sys.stderr)
    sys.exit(0 if failed == 0 else 1)
