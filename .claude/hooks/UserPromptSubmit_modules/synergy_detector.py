r"""Synergy detection for cognitive frameworks and reasoning modes.

Detects when cognitive framework + reasoning mode combinations create synergistic
effects greater than their individual contributions.

Synergy Matrix:
- assumption_surfacing + sequential → 0.9 (Surface assumptions before step-by-step)
- socratic_decomposition + multi_agent → 0.85 (Decompose for multiple perspectives)
- inversion_prompting + two_stage → 0.8 (Pre-mortem in reasoning phase)
- first_principles + multi_agent → 0.75 (Different foundations revealed through debate)
- assumption_surfacing + multi_agent → 0.7 (Make implicit assumptions explicit for group)
- devil_advocate + sequential → 0.65 (Challenge assumptions before committing)
- socratic_decomposition + sequential → 0.6 (Question decomposition aligns with step-by-step)

Scoring:
- 0.9-1.0: Exceptional synergy (strongly prefer combination)
- 0.7-0.9: High synergy (prefer combination)
- 0.5-0.7: Moderate synergy (neutral preference)
- <0.5: Low synergy (no special handling)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

if TYPE_CHECKING:
    pass


# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass(frozen=True)
class SynergyRule:
    """Single-source definition for a framework+mode synergy.

    Attributes:
        framework: Cognitive framework name (e.g., "assumption_surfacing")
        mode: Reasoning mode name (e.g., "sequential")
        score: Synergy strength in [0.0, 1.0] range
        rationale: Why this combination is synergistic
    """

    framework: str
    mode: str
    score: float
    rationale: str


@dataclass(frozen=True)
class SynergyMatch:
    """Result from synergy detection.

    Attributes:
        synergies: All detected framework+mode synergies
        top_synergies: Top 3 synergies sorted by score (descending)
        total_score: Sum of all synergy scores
    """

    synergies: list[dict] = field(default_factory=list)
    top_synergies: list[dict] = field(default_factory=list)
    total_score: float = 0.0


# =============================================================================
# SYNERGY MATRIX (DEFAULT)
# =============================================================================

# Pre-computed lookup for O(1) combination detection
# Key: (framework, mode) tuple → Value: SynergyRule
_SYNERGY_LOOKUP: dict[tuple[str, str], SynergyRule] = {}

_DEFAULT_SYNERGY_MATRIX: list[SynergyRule] = [
    # Exceptional synergies (0.9+)
    SynergyRule(
        framework="assumption_surfacing",
        mode="sequential",
        score=0.9,
        rationale=(
            "Surface unstated assumptions before step-by-step reasoning "
            "prevents blind spots and false premises in the logical chain"
        ),
    ),
    # High synergies (0.7-0.9)
    SynergyRule(
        framework="socratic_decomposition",
        mode="multi_agent",
        score=0.85,
        rationale=(
            "Break vague mega-prompts into sub-questions for multiple "
            "perspectives enables richer debate and comprehensive analysis"
        ),
    ),
    SynergyRule(
        framework="inversion_prompting",
        mode="two_stage",
        score=0.8,
        rationale=(
            "Pre-mortem thinking in reasoning phase catches flaws early "
            "before implementation commitment"
        ),
    ),
    SynergyRule(
        framework="first_principles",
        mode="multi_agent",
        score=0.75,
        rationale=(
            "Different foundational assumptions revealed through multi-agent "
            "debate prevent groupthink and surface hidden constraints"
        ),
    ),
    SynergyRule(
        framework="assumption_surfacing",
        mode="multi_agent",
        score=0.7,
        rationale=(
            "Make implicit assumptions explicit for group discussion improves "
            "shared understanding and reduces miscommunication"
        ),
    ),
    # Moderate synergies (0.5-0.7)
    SynergyRule(
        framework="devil_advocate",
        mode="sequential",
        score=0.65,
        rationale=(
            "Challenge assumptions before committing to reasoning path strengthens "
            "logical chain and exposes weak arguments"
        ),
    ),
    SynergyRule(
        framework="socratic_decomposition",
        mode="sequential",
        score=0.6,
        rationale=(
            "Question decomposition aligns naturally with step-by-step "
            "reasoning process for methodical analysis"
        ),
    ),
]

# Build lookup table at module load time (one-time O(n) cost)
for rule in _DEFAULT_SYNERGY_MATRIX:
    # Validate score range
    if not 0.0 <= rule.score <= 1.0:
        raise ValueError(
            f"Invalid synergy score {rule.score} for "
            f"{rule.framework}+{rule.mode}, must be in [0.0, 1.0] range"
        )

    key = (rule.framework, rule.mode)
    if key in _SYNERGY_LOOKUP:
        raise ValueError(f"Duplicate synergy rule: {key}")

    _SYNERGY_LOOKUP[key] = rule


# =============================================================================
# PUBLIC API
# =============================================================================


def detect_synergies(
    frameworks: str | list[str] | set[str] | None,
    modes: str | list[str] | set[str] | None,
) -> SynergyMatch:
    """Detect synergistic framework+mode combinations.

    Args:
        frameworks: Detected cognitive frameworks (list, set, or None)
        modes: Detected reasoning modes (list, set, or None)

    Returns:
        SynergyMatch with all detected synergies and top 3 sorted by score

    Examples:
        >>> detect_synergies(["assumption_surfacing"], ["sequential"])
        SynergyMatch(synergies=[...], top_synergies=[...], total_score=0.9)

        >>> detect_synergies(None, None)
        SynergyMatch(synergies=[], top_synergies=[], total_score=0.0)
    """
    # Normalize inputs to lists (handle None, str, or iterable)
    if frameworks is None:
        frameworks = []
    elif isinstance(frameworks, str):
        frameworks = [frameworks]
    else:
        frameworks = list(frameworks) if not isinstance(frameworks, list) else frameworks

    if modes is None:
        modes = []
    elif isinstance(modes, str):
        modes = [modes]
    else:
        modes = list(modes) if not isinstance(modes, list) else modes

    # Detect synergies via O(1) lookup for each combination
    detected = []

    for framework in frameworks:
        for mode in modes:
            key = (framework, mode)
            rule = _SYNERGY_LOOKUP.get(key)

            if rule is not None and rule.score >= 0.5:
                # Convert to dict for JSON serialization
                detected.append(
                    {
                        "framework": rule.framework,
                        "mode": rule.mode,
                        "score": rule.score,
                        "rationale": rule.rationale,
                    }
                )

    # Sort by score (descending) and extract top 3
    detected.sort(key=lambda s: s["score"], reverse=True)
    top_synergies = detected[:3]

    # Calculate total score
    total_score = sum(s["score"] for s in detected)

    return SynergyMatch(
        synergies=detected,
        top_synergies=top_synergies,
        total_score=total_score,
    )


# =============================================================================
# HOOK INTEGRATION
# =============================================================================


@register_hook("synergy_detector", priority=12.0)
def synergy_detector_hook(context: HookContext) -> HookResult:
    """Hook to detect and report framework+mode synergies.

    Runs after unified_injector (11.0) to avoid double-injection.
    Uses unified_detection_result from context.data if available.

    Priority: 12.0 (runs after unified_detection and unified_injector)
    """
    # Extract frameworks and modes from context data (set by unified_detection hook)
    data = context.data
    result = data.get("unified_detection_result")

    if result:
        frameworks = result.matched_frameworks
        modes = result.matched_modes
    else:
        # Fallback: use ensure_unified_detection_result which passes through
        # the envelope-aware outer_text path (preferred over direct
        # detect_prompt which cannot see the envelope). This should rarely
        # fire in production because unified_detection_hook (priority 1.0)
        # caches its result before this hook runs.
        try:
            from UserPromptSubmit_modules.unified_detection import ensure_unified_detection_result
            result = ensure_unified_detection_result(context)
            frameworks = result.matched_frameworks
            modes = result.matched_modes
        except Exception:
            # Last resort: direct detection with raw prompt (no envelope).
            # Marked as legacy/test path — real production runs always
            # have the cached detection result.
            from UserPromptSubmit_modules.unified_detection import detect_prompt
            detection = detect_prompt(context.prompt)
            frameworks = detection.matched_frameworks
            modes = detection.matched_modes

    # Detect synergies using the matrix defined in this module
    match = detect_synergies(frameworks, modes)

    if not match.top_synergies:
        return HookResult.empty()

    # Emit tags: [SYNERGY: framework+mode (score)]
    # Limit to top 3 by score
    tags = []
    for synergy in match.top_synergies:
        framework = synergy["framework"]
        mode = synergy["mode"]
        score = synergy["score"]
        # Format: [SYNERGY: framework+mode (score)]
        tags.append(f"[SYNERGY: {framework}+{mode} ({score})]")

    combined_tags = " ".join(tags)

    # Return tags as additional context injection
    return HookResult(
        context=combined_tags,
        tokens=len(combined_tags.split()),
    )
