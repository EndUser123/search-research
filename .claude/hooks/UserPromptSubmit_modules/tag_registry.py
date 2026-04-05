"""Tag Registry - Canonical definitions for framework-specific cognitive tags.

This module provides the single source of truth for all cognitive framework tags,
preventing tag staleness and LLM hallucination of non-existent tags.

Tag Governance Process:
1. Proposal: Create issue describing new tag's purpose and use case
2. Review: Tag must pass 3-question review:
   - Does this tag solve a real problem? (Evidence required)
   - Is this tag distinct from existing tags? (No overlap)
   - Will this tag be used frequently? (Base rate > 20% of relevant prompts)
3. Merge: Add to FRAMEWORK_TAGS dict after approval

See CKS entry "tag_governance" for detailed governance process.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# =============================================================================
# TAG CONSTANTS
# =============================================================================

# Cognitive framework tags (framework-specific, 2-4 chars)
TAG_ASUM = "ASUM"  # Assumption Surfacing
TAG_ANCH = "ANCH"  # Outcome Anchoring
TAG_INV = "INV"  # Inversion Prompting
TAG_FENC = "FENC"  # Chesterton's Fence
TAG_CAL = "CAL"  # Calibrated Confidence
TAG_DISC = "DISC"  # Named Artifact Discovery
TAG_SOC = "SOC"  # Socratic Decomposition
TAG_CYNE = "CYNE"  # Cynefin Classification
TAG_RAZR = "RAZR"  # Hanlon's Razor
TAG_DADV = "DADV"  # Devil's Advocate
TAG_COMP = "COMP"  # Comparative Analysis

# Legacy COG tag (deprecated - use framework-specific tags)
TAG_COG = "COG"  # DEPRECATED: Use framework-specific tags instead
DEPRECATED_TAG_COG = TAG_COG  # Alias for clarity

# Reasoning mode tags
TAG_SEQ = "SEQ"  # Sequential reasoning
TAG_MAS = "MAS"  # Multi-agent reasoning
TAG_GRA = "GRA"  # Graph reasoning
TAG_2ST = "2ST"  # Two-stage reasoning

# Think profile tags
TAG_THINK = "THINK"  # Active think profiles

# Synergy detection tags
TAG_SYNERGY = "SYNERGY"  # Framework+mode combinations

# Performance monitoring tags
TAG_PERF = "PERF"  # Performance timing data

# Questioning pattern tags
TAG_QUESTIONING = "QUESTIONING"  # Questioning pattern matches

# =============================================================================
# FRAMEWORK TAG DEFINITIONS (Canonical Source)
# =============================================================================

FRAMEWORK_TAGS: dict[str, dict[str, Any]] = {
    TAG_ASUM: {
        "name": "Assumption Surfacing",
        "description": "Surface unstated assumptions before work begins",
        "enhancer": "assumption_surfacing",
    },
    TAG_ANCH: {
        "name": "Outcome Anchoring",
        "description": "Define 'done' before starting",
        "enhancer": "outcome_anchoring",
    },
    TAG_INV: {
        "name": "Inversion Prompting",
        "description": "What would make this fail?",
        "enhancer": "inversion_prompting",
    },
    TAG_FENC: {
        "name": "Chesterton's Fence",
        "description": "Understand existing code before changing it",
        "enhancer": "chestertons_fence",
    },
    TAG_CAL: {
        "name": "Calibrated Confidence",
        "description": "Force confidence labeling on claims",
        "enhancer": "calibrated_confidence",
    },
    TAG_DISC: {
        "name": "Named Artifact Discovery",
        "description": "Find named systems before analyzing",
        "enhancer": "named_artifact_discovery",
    },
    TAG_SOC: {
        "name": "Socratic Decomposition",
        "description": "Break vague mega-prompts into sub-questions",
        "enhancer": "socratic_decomposition",
    },
    TAG_CYNE: {
        "name": "Cynefin Classification",
        "description": "Problem domain classification",
        "enhancer": "cynefin_classification",
    },
    TAG_RAZR: {
        "name": "Hanlon's Razor",
        "description": "Distinguish malice from stupidity",
        "enhancer": "hanlons_razor",
    },
    TAG_DADV: {
        "name": "Devil's Advocate",
        "description": "Stress-test proposals with counterarguments",
        "enhancer": "devils_advocate",
    },
    TAG_COMP: {
        "name": "Comparative Analysis",
        "description": "Search → Evaluate → Implement before committing",
        "enhancer": "comparative_analysis",
    },
}

# Tag format regex: [TAGTYPE] with uppercase letters, numbers, underscore
TAG_PATTERN = re.compile(r"^[A-Z0-9_]+$")

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================


@dataclass(frozen=True)
class TagDefinition:
    """Framework tag definition with metadata."""

    tag_type: str
    name: str
    description: str
    enhancer: str | None = None
    deprecated: bool = False


def get_tag_definition(tag_type: str) -> TagDefinition | None:
    """Get tag definition from registry.

    Args:
        tag_type: Tag identifier (e.g., "ASUM", "COG")

    Returns:
        TagDefinition or None if tag not found

    Examples:
        >>> get_tag_definition("ASUM")
        TagDefinition(tag_type='ASUM', name='Assumption Surfacing', ...)
        >>> get_tag_definition("INVALID")
        None
    """
    if tag_type == TAG_COG:
        return TagDefinition(
            tag_type=TAG_COG,
            name="Cognitive Frameworks (Deprecated)",
            description="Use framework-specific tags instead",
            deprecated=True,
        )

    if tag_type in FRAMEWORK_TAGS:
        info = FRAMEWORK_TAGS[tag_type]
        return TagDefinition(
            tag_type=tag_type,
            name=info["name"],
            description=info["description"],
            enhancer=info.get("enhancer"),
        )

    return None


def validate_tag(tag_type: str) -> bool:
    """Validate tag format and existence in registry.

    Args:
        tag_type: Tag identifier to validate

    Returns:
        True if tag is valid, False otherwise

    Examples:
        >>> validate_tag("ASUM")
        True
        >>> validate_tag("COG")  # Deprecated but valid
        True
        >>> validate_tag("INVALID")
        False
    """
    # Check format first (fast path)
    if not TAG_PATTERN.match(tag_type):
        return False

    # Check if tag exists in registry
    if tag_type == TAG_COG:
        return True  # Deprecated but valid

    return tag_type in FRAMEWORK_TAGS


def validate_tag_emission(tag_type: str, content: str | None = None) -> tuple[bool, str | None]:
    """Validate tag emission with deprecation warnings.

    This is the primary validation function for hook boundary checks.
    Returns (is_valid, warning_message) tuple.

    Args:
        tag_type: Tag identifier to validate
        content: Optional tag content

    Returns:
        (is_valid, warning_message) tuple

    Examples:
        >>> validate_tag_emission("ASUM")
        (True, None)
        >>> validate_tag_emission("COG")
        (True, "[COG] tag is deprecated - use framework-specific tags")
        >>> validate_tag_emission("INVALID")
        (False, "Unknown tag type: INVALID")
    """
    # Check format first
    if not TAG_PATTERN.match(tag_type):
        return (False, f"Invalid tag format: {tag_type}")

    # Check for deprecated tags
    if tag_type == TAG_COG:
        warning = (
            f"[{tag_type}] tag is deprecated - use framework-specific tags "
            f"({', '.join(list(FRAMEWORK_TAGS.keys())[:3])}, ...)"
        )
        return (True, warning)

    # Check if tag exists in registry
    if tag_type not in FRAMEWORK_TAGS:
        return (False, f"Unknown tag type: {tag_type}")

    return (True, None)


def get_all_framework_tags() -> list[str]:
    """Get list of all framework tag types.

    Returns:
        List of tag type strings (e.g., ["ASUM", "ANCH", ...])
    """
    return list(FRAMEWORK_TAGS.keys())


def get_framework_tags_for_enhancer(enhancer_name: str) -> list[str]:
    """Get framework tags that map to a specific enhancer.

    Args:
        enhancer_name: Name of the cognitive enhancer (e.g., "assumption_surfacing")

    Returns:
        List of tag types for this enhancer

    Examples:
        >>> get_framework_tags_for_enhancer("assumption_surfacing")
        ["ASUM"]
        >>> get_framework_tags_for_enhancer("nonexistent")
        []
    """
    return [
        tag_type
        for tag_type, info in FRAMEWORK_TAGS.items()
        if info.get("enhancer") == enhancer_name
    ]


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

# Validate module on import (fail fast if registry is misconfigured)
if __debug__:
    # Check for duplicate tag types
    all_tags = [TAG_COG] + get_all_framework_tags()
    if len(all_tags) != len(set(all_tags)):
        duplicate_tags = [tag for tag in all_tags if all_tags.count(tag) > 1]
        raise AssertionError(f"Tag registry has duplicate definitions: {duplicate_tags}")

    # Check that all framework tags have required fields
    for tag_type, info in FRAMEWORK_TAGS.items():
        if "name" not in info or "description" not in info:
            raise AssertionError(f"Tag {tag_type} is missing required fields (name, description)")
