"""Tier 0: Checklist-based verification.

Provides quick checklist-based verification for skills, hooks, and features.
This is the fastest verification tier using structured checklists.
"""

import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Add verification package to path
# verification is at P:/.claude/skills/verification
# verify is at P:/.claude/skills/verify/tiers
# There's a namespace collision with P:/.claude/hooks/verification, so add the full path
verification_path = Path(__file__).parent.parent.parent / "verification"
sys.path.insert(0, str(verification_path))

from checklists import FeatureChecklist, HookChecklist, SkillChecklist


@dataclass
class ChecklistResult:
    """Result of checklist verification.

    Attributes:
        status: Overall status ("pass", "partial", "fail")
        items_checked: Total number of checklist items checked
        items_passed: Number of items that passed
        findings: List of detailed findings for each item
    """

    status: str
    items_checked: int
    items_passed: int
    findings: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


def run_checklist_verification(target_type: str, target_path: str) -> dict[str, Any]:
    """
    Run checklist-based verification for a target.

    Args:
        target_type: Type of target ("skill", "hook", or "feature")
        target_path: Path to the target (directory or file)

    Returns:
        Dictionary with checklist verification results:
        {
            "status": "pass" | "partial" | "fail",
            "items_checked": int,
            "items_passed": int,
            "findings": List[str]
        }

    Raises:
        ValueError: If target_type is invalid
    """
    # Select appropriate checklist based on target_type
    if target_type == "skill":
        checklist = SkillChecklist()
    elif target_type == "hook":
        checklist = HookChecklist()
    elif target_type == "feature":
        checklist = FeatureChecklist()
    elif target_type == "code":
        # Code targets don't have SKILL.md structure to check against
        # Return skip status to allow subsequent tiers to run
        return {
            "status": "skip",
            "items_checked": 0,
            "items_passed": 0,
            "findings": ["Code target - checklist verification skipped"],
        }
    else:
        raise ValueError(
            f"Invalid target type: {target_type}. Must be 'skill', 'hook', 'feature', or 'code'."
        )

    # Run verification
    result_dict = checklist.verify_target(target_path)

    # Return dict format (checklist already returns dict)
    return result_dict
