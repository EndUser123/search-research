"""Unified tag emission standard for cognitive & reasoning systems.

Standardizes tag format across all systems:

Cognitive Framework Tags (framework-specific, 2-4 chars):
- [ASUM] Assumption Surfacing
- [ANCH] Outcome Anchoring
- [INV] Inversion Prompting
- [FENC] Chesterton's Fence
- [CAL] Calibrated Confidence
- [DISC] Named Artifact Discovery
- [SOC] Socratic Decomposition
- [CYNE] Cynefin Classification
- [RAZR] Hanlon's Razor
- [DADV] Devil's Advocate

Reasoning Mode Tags:
- [SEQ] Sequential reasoning
- [MAS] Multi-agent reasoning
- [GRA] Graph reasoning
- [2ST] Two-stage reasoning

Other Tags:
- [THINK] Think profiles
- [SYNERGY] Framework+mode combinations
- [PERF] Performance timing data
- [QUESTIONING] Questioning pattern matches

All tags follow format: [TAGTYPE]
- No spaces within brackets
- Consistent uppercase casing
- Backward compatible with existing tags

Usage:
    from tag_emission import emit_tags, validate_tag

    # Single tag
    tag = emit_tags("SOC")

    # Multiple tags
    tags = emit_tags([("SOC", None), ("CAL", None), ("CYNE", None)])
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
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

# Legacy COG tag (deprecated - use framework-specific tags)
TAG_COG = "COG"  # DEPRECATED: Use framework-specific tags instead

# Reasoning mode tags
TAG_SEQ = "SEQ"  # Sequential reasoning
TAG_MAS = "MAS"  # Multi-agent reasoning
TAG_GRA = "GRA"  # Graph reasoning (NEW - was missing from original)
TAG_2ST = "2ST"  # Two-stage reasoning

# Think profile tags
TAG_THINK = "THINK"  # Active think profiles (NEW)

# Synergy detection tags
TAG_SYNERGY = "SYNERGY"  # Framework+mode combinations (NEW)

# Performance monitoring tags
TAG_PERF = "PERF"  # Performance timing data (NEW)

# Questioning pattern tags
TAG_QUESTIONING = "QUESTIONING"  # Questioning pattern matches (NEW)

# All valid tags (for validation)
VALID_TAGS = {
    # Cognitive framework tags
    TAG_ASUM,
    TAG_ANCH,
    TAG_INV,
    TAG_FENC,
    TAG_CAL,
    TAG_DISC,
    TAG_SOC,
    TAG_CYNE,
    TAG_RAZR,
    TAG_DADV,
    TAG_COG,  # Legacy, deprecated
    # Reasoning mode tags
    TAG_SEQ,
    TAG_MAS,
    TAG_GRA,
    TAG_2ST,
    # Other tags
    TAG_THINK,
    TAG_SYNERGY,
    TAG_PERF,
    TAG_QUESTIONING,
}

# Tag format regex: [TAGTYPE] with uppercase letters, numbers, underscore
TAG_PATTERN = re.compile(r"^[A-Z0-9_]+$")

# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass(frozen=True)
class Tag:
    """A single tag with optional content.

    Attributes:
        tag_type: Tag identifier (e.g., "COG", "SEQ")
        content: Optional content string (e.g., framework names, timing data)
        metadata: Optional metadata dict (e.g., confidence scores, counts)
    """

    tag_type: str
    content: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate tag format on creation."""
        if not TAG_PATTERN.match(object.__getattribute__(self, "tag_type")):
            raise ValueError(
                f"Invalid tag type: {self.tag_type!r}. "
                f"Tag types must be uppercase letters, numbers, or underscore only."
            )

    def format(self) -> str:
        """Format tag as [TAGTYPE] with optional content.

        Examples:
            Tag("COG").format() → "[COG]"
            Tag("COG", "Assumption Surfacing").format() → "[COG] Assumption Surfacing"
            Tag("PERF", "0.15ms", {"mean": "0.11ms"}).format() → "[PERF] 0.15ms"
        """
        tag = f"[{self.tag_type}]"
        if self.content:
            return f"{tag} {self.content}"
        return tag


@dataclass(frozen=True)
class TagCollection:
    """Collection of multiple tags with aggregation support.

    Attributes:
        tags: List of Tag objects
        separator: Separator between tags (default: " ")
    """

    tags: list[Tag] = field(default_factory=list)
    separator: str = " "

    def format(self) -> str:
        """Format all tags as a single string.

        Examples:
            TagCollection([
                Tag("COG", "Assumption Surfacing"),
                Tag("SEQ"),
                Tag("THINK", "debug_rca"),
            ]).format() → "[COG] Assumption Surfacing [SEQ] [THINK] debug_rca"
        """
        return self.separator.join(tag.format() for tag in self.tags)

    def add_tag(self, tag: Tag) -> TagCollection:
        """Add a tag to the collection (returns new instance)."""
        return TagCollection(tags=self.tags + [tag], separator=self.separator)

    def filter_by_type(self, tag_type: str) -> list[Tag]:
        """Get all tags of a specific type."""
        return [tag for tag in self.tags if tag.tag_type == tag_type]


# =============================================================================
# TAG EMISSION FUNCTIONS
# =============================================================================


def validate_tag(tag_type: str) -> bool:
    """Validate tag format.

    Args:
        tag_type: Tag identifier to validate

    Returns:
        True if tag is valid, False otherwise

    Examples:
        >>> validate_tag("COG")
        True
        >>> validate_tag("cog")  # lowercase invalid
        False
        >>> validate_tag("COG-TEST")  # hyphen invalid
        False
        >>> validate_tag("COG_TEST")  # underscore valid
        True
    """
    return TAG_PATTERN.match(tag_type) is not None


def emit_tag(
    tag_type: str,
    content: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Emit a single formatted tag.

    Args:
        tag_type: Tag identifier (e.g., "COG", "SEQ", "THINK")
        content: Optional content string
        metadata: Optional metadata dict

    Returns:
        Formatted tag string

    Raises:
        ValueError: If tag_type is invalid

    Examples:
        >>> emit_tag("COG")
        '[COG]'
        >>> emit_tag("COG", "Assumption Surfacing")
        '[COG] Assumption Surfacing'
        >>> emit_tag("PERF", "0.15ms", {"mean": "0.11ms"})
        '[PERF] 0.15ms'
    """
    if not validate_tag(tag_type):
        raise ValueError(
            f"Invalid tag type: {tag_type!r}. Tag types must match pattern: {TAG_PATTERN.pattern}"
        )

    tag = Tag(tag_type=tag_type, content=content, metadata=metadata or {})
    return tag.format()


def emit_tags(
    tags: str | tuple[str, str | None] | list[tuple[str, str | None]] | list[Tag],
    separator: str = " ",
) -> str:
    """Emit one or more formatted tags.

    Args:
        tags: Tag specification(s):
            - str: Tag type only (e.g., "COG")
            - tuple: (tag_type, content) (e.g., ("COG", "Assumption Surfacing"))
            - list of tuples: Multiple tags
            - list of Tag: Tag objects
        separator: Separator between tags (default: " ")

    Returns:
        Formatted tag string(s)

    Raises:
        ValueError: If any tag_type is invalid

    Examples:
        >>> emit_tags("COG")
        '[COG]'
        >>> emit_tags(("COG", "Assumption Surfacing"))
        '[COG] Assumption Surfacing'
        >>> emit_tags([("COG", "Assumption Surfacing"), ("SEQ", None)])
        '[COG] Assumption Surfacing [SEQ]'
        >>> emit_tags([Tag("COG"), Tag("SEQ")])
        '[COG] [SEQ]'
    """
    # Convert single tag type to Tag
    if isinstance(tags, str):
        tag = Tag(tag_type=tags)
        return tag.format()

    # Convert tuple to Tag
    if isinstance(tags, tuple):
        tag_type, content = tags
        tag = Tag(tag_type=tag_type, content=content)
        return tag.format()

    # Convert list of tuples or Tag objects
    if isinstance(tags, list):
        tag_list = []
        for item in tags:
            if isinstance(item, Tag):
                tag_list.append(item)
            elif isinstance(item, tuple):
                tag_type, content = item
                tag_list.append(Tag(tag_type=tag_type, content=content))
            else:
                raise ValueError(f"Invalid tag item: {item!r}")

        collection = TagCollection(tags=tag_list, separator=separator)
        return collection.format()

    raise ValueError(f"Invalid tags specification: {tags!r}")


# =============================================================================
# INTEGRATION WITH UNIFIED DETECTION
# =============================================================================


def emit_detection_tags(
    matched_frameworks: list[str] | None = None,
    matched_modes: list[str] | None = None,
    matched_profiles: list[str] | None = None,
    synergy_candidates: list[tuple[str, str]] | None = None,
    timing_ms: float | None = None,
    questioning_patterns: list[str] | None = None,
) -> str:
    """Emit tags from unified detection results.

    This is the primary integration point with unified_detection.py.
    Converts UnifiedDetectionResult to tag string.

    Args:
        matched_frameworks: List of matched cognitive framework names
        matched_modes: List of matched reasoning mode names
        matched_profiles: List of matched think profile names
        synergy_candidates: List of (framework, mode) synergy tuples
        timing_ms: Detection timing in milliseconds
        questioning_patterns: List of matched questioning pattern names

    Returns:
        Formatted tag string with all detected tags

    Examples:
        >>> emit_detection_tags(
        ...     matched_frameworks=["assumption_surfacing"],
        ...     matched_modes=["sequential"],
        ...     timing_ms=0.15,
        ... )
        '[COG] assumption_surfacing [SEQ] [PERF] 0.15ms'
    """
    tags = []

    # Cognitive frameworks tag
    if matched_frameworks:
        # Format framework names: assumption_surfacing → "Assumption Surfacing"
        formatted_names = [
            " ".join(word.title() for word in fw.split("_")) for fw in matched_frameworks
        ]
        content = ", ".join(formatted_names)
        tags.append(("COG", content))

    # Reasoning modes tag (map mode names to tags)
    mode_tag_map = {
        "sequential": "SEQ",
        "multi_agent": "MAS",
        "graph": "GRA",
        "two_stage": "2ST",
    }
    for mode in matched_modes or []:
        if mode in mode_tag_map:
            tags.append((mode_tag_map[mode], None))

    # Think profiles tag
    if matched_profiles:
        content = ", ".join(matched_profiles)
        tags.append(("THINK", content))

    # Synergy detection tag
    if synergy_candidates:
        # Format: "framework+mode (score)" pairs
        # Note: If synergy_candidates contains tuples, we use default score 0.0
        # If it's used with synergy_detector.py, it will provide scores
        pairs = []
        for item in synergy_candidates[:3]:
            if isinstance(item, dict):
                fw = item.get("framework")
                mode = item.get("mode")
                score = item.get("score", 0.0)
                pairs.append(f"{fw}+{mode} ({score})")
            else:
                fw, mode = item
                pairs.append(f"{fw}+{mode}")

        content = ", ".join(pairs)
        if len(synergy_candidates) > 3:
            content += f" (+{len(synergy_candidates) - 3} more)"
        tags.append(("SYNERGY", content))

    # Performance timing tag
    if timing_ms is not None:
        content = f"{timing_ms:.2f}ms"
        tags.append(("PERF", content))

    # Questioning patterns tag
    if questioning_patterns:
        content = ", ".join(questioning_patterns[:3])  # Limit to first 3
        if len(questioning_patterns) > 3:
            content += f" (+{len(questioning_patterns) - 3} more)"
        tags.append(("QUESTIONING", content))

    # Emit all tags
    if tags:
        return emit_tags(tags)

    return ""


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================


def parse_legacy_tag(tag_string: str) -> tuple[str, str | None] | None:
    """Parse legacy tag strings for backward compatibility.

    Args:
        tag_string: Legacy tag string (e.g., "[COG] Assumption Surfacing")

    Returns:
        (tag_type, content) tuple or None if invalid

    Examples:
        >>> parse_legacy_tag("[COG] Assumption Surfacing")
        ('COG', 'Assumption Surfacing')
        >>> parse_legacy_tag("[SEQ]")
        ('SEQ', None)
        >>> parse_legacy_tag("invalid")
        None
    """
    match = re.match(r"^\[([A-Z0-9_]+)\](?:\s+(.+))?$", tag_string)
    if not match:
        return None

    tag_type = match.group(1)
    content = match.group(2) if match.lastindex >= 2 else None
    return (tag_type, content)
