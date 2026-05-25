"""Deterministic claim decomposition for compound/aggregate SILENT claims.

Breaks compound claims into atomic sub-obligations using regex splitting.
Only activates for SILENT/weak verdicts — well-supported claims are never decomposed.

No LLM, no subprocess, no external API calls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

__all__ = [
    "SubClaim",
    "DecompositionResult",
    "should_decompose",
    "decompose_claim",
]

# ---------------------------------------------------------------------------
# Trigger patterns
# ---------------------------------------------------------------------------

_COMPOUND_CONJUNCTION = re.compile(
    r"\b(?:and|while|but|whereas|although|as well as|along with)\b",
    re.IGNORECASE,
)

_AGGREGATE_QUANTIFIER = re.compile(
    r"\b(?:all|every|each|both|none of)\b",
    re.IGNORECASE,
)

# Comma-separated list of >=2 items followed by a shared predicate
_COMMA_LIST_PREDICATE = re.compile(
    r"(\w+(?:\s*,\s*\w+){1,})\s+"
    r"(?:is|are|was|were|has|have|pass|fail|work|run)\b",
    re.IGNORECASE,
)

# Indirect evidence: "based on X, therefore Y"
_INDIRECT_EVIDENCE = re.compile(
    r"\b(?:based on|according to|given that|since)\b"
    r".*\b(?:then|therefore|so|implies)\b",
    re.IGNORECASE,
)

# Splitting pattern — conjunctions that separate distinct predicates
_SPLIT_CONJUNCTION = re.compile(
    r"\s+(?:and|while|but|whereas)\s+",
    re.IGNORECASE,
)

# Comma list extraction
_COMMA_LIST = re.compile(r"\s*,\s*(?:and\s+)?")

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SubClaim:
    """A single atomic obligation decomposed from a compound claim."""

    text: str
    obligation_type: str  # "atomic_positive" | "atomic_negative" | "aggregate_element"
    targets: tuple[str, ...]
    conjunction: str | None
    position: int


@dataclass(frozen=True)
class DecompositionResult:
    """Result of decomposing a single claim."""

    original_claim_id: str | int
    is_compound: bool
    trigger_reason: str  # "conjunction" | "aggregate" | "comma_list" | "indirect" | ""
    sub_claims: tuple[SubClaim, ...]
    confidence: float


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def should_decompose(claim: Any, verdict: Any) -> bool:
    """Return True if this claim+verdict pair warrants decomposition.

    Triggers on SILENT verdicts that contain compound/aggregate/indirect language.

    Args:
        claim: Claim object with .text attribute.
        verdict: VerificationVerdict with .status (VerificationStatus enum).
    """
    status_value = _status_value(verdict)
    if status_value != "SILENT":
        return False

    claim_text = getattr(claim, "text", "")
    return bool(
        _COMPOUND_CONJUNCTION.search(claim_text)
        or _AGGREGATE_QUANTIFIER.search(claim_text)
        or _COMMA_LIST_PREDICATE.search(claim_text)
        or _INDIRECT_EVIDENCE.search(claim_text)
    )


def decompose_claim(claim: Any) -> DecompositionResult:
    """Split a compound claim into atomic sub-obligations.

    Pure regex-based. Strategy:
    1. Split on conjunction boundaries ("X and Y")
    2. Expand aggregate+lists ("all of A, B, C")
    3. Split comma-separated predicates sharing a verb

    Returns is_compound=False with empty sub_claims if no split found.

    Args:
        claim: Claim object with .id, .text, .targets attributes.
    """
    claim_id = getattr(claim, "id", "")
    claim_text = getattr(claim, "text", "")
    claim_targets = list(getattr(claim, "targets", []))

    # Strategy 1: Conjunction split
    parts = _split_conjunctions(claim_text)
    if len(parts) > 1:
        subs = tuple(
            SubClaim(
                text=part.strip(),
                obligation_type="atomic_positive",
                targets=tuple(_extract_targets(part.strip(), claim_targets)),
                conjunction="and",
                position=i,
            )
            for i, part in enumerate(parts)
            if part.strip()
        )
        return DecompositionResult(
            original_claim_id=claim_id,
            is_compound=True,
            trigger_reason="conjunction",
            sub_claims=subs,
            confidence=0.9,
        )

    # Strategy 2: Aggregate + comma list
    agg_match = _AGGREGATE_QUANTIFIER.search(claim_text)
    comma_match = _COMMA_LIST_PREDICATE.search(claim_text)
    if agg_match and comma_match:
        items = _COMMA_LIST.split(comma_match.group(1))
        predicate = claim_text[comma_match.end():].strip()
        subs = tuple(
            SubClaim(
                text=f"{item.strip()} {predicate}",
                obligation_type="aggregate_element",
                targets=tuple(_extract_targets(item.strip(), claim_targets)),
                conjunction=None,
                position=i,
            )
            for i, item in enumerate(items)
            if item.strip()
        )
        return DecompositionResult(
            original_claim_id=claim_id,
            is_compound=True,
            trigger_reason="aggregate",
            sub_claims=subs,
            confidence=0.85,
        )

    # Strategy 3: Indirect evidence
    if _INDIRECT_EVIDENCE.search(claim_text):
        for marker in ("therefore", "so", "implies"):
            if marker in claim_text.lower():
                idx = claim_text.lower().index(marker)
                conclusion = claim_text[idx + len(marker):].strip()
                if conclusion:
                    return DecompositionResult(
                        original_claim_id=claim_id,
                        is_compound=True,
                        trigger_reason="indirect",
                        sub_claims=(
                            SubClaim(
                                text=conclusion,
                                obligation_type="atomic_positive",
                                targets=tuple(_extract_targets(conclusion, claim_targets)),
                                conjunction=marker,
                                position=0,
                            ),
                        ),
                        confidence=0.7,
                    )

    # Not compound
    return DecompositionResult(
        original_claim_id=claim_id,
        is_compound=False,
        trigger_reason="",
        sub_claims=(),
        confidence=0.0,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _status_value(verdict: Any) -> str:
    """Extract status string from a verdict (enum or string)."""
    status = getattr(verdict, "status", None)
    if status is None:
        return ""
    if isinstance(status, str):
        return status
    return str(status.value) if hasattr(status, "value") else str(status)


def _split_conjunctions(text: str) -> list[str]:
    """Split claim text at conjunction boundaries."""
    return _SPLIT_CONJUNCTION.split(text)


def _extract_targets(part_text: str, parent_targets: list[str]) -> list[str]:
    """Extract entity references from a sub-claim, falling back to parent targets."""
    targets = [t for t in parent_targets if t.lower() in part_text.lower()]
    return targets if targets else parent_targets
