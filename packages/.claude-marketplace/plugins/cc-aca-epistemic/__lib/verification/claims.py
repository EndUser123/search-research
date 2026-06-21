"""Verification claims module.

Provides Claim dataclass and extract_claims() function for detecting
and representing verification claims in LLM responses.

FIELD ALIGNMENT (from RawClaim in hypothesis_as_fact_detector.py):
- RawClaim.text → Claim.text (same)
- RawClaim.subject_entity → Claim.targets[0] (rename+list wrapper)
- RawClaim.claim_type → Claim.type (rename)
- RawClaim.confidence → Claim.confidence (same)
- RawClaim.has_hedge → Claim.has_hedge (same)
- RawClaim.risk_domain → Claim.risk_domain (same)

This alignment ensures Phase 2 is a rename+move operation, not a redesign.

EXTENSION: OUTCOME_ATTRIBUTION and FOLDER_CREATE claim types are detected by
scanning for overconfidence patterns not covered by HypothesisAsFactDetector.
These patterns are unified here so all claims go through build_verdicts().
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import List

from anti_sycophancy.hypothesis_as_fact_detector import (
    ClaimType,
    HypothesisAsFactDetector,
    RawClaim,
)


# OUTCOME_ATTRIBUTION patterns — from overconfidence_detector OUTCOME_ATTRIBUTION_PHRASES
# These emit claims that go through build_verdicts() rather than string-search exemptions.
_OUTCOME_ATTRIBUTION_PATTERNS = [
    (re.compile(r"\bcorrectly\s+(?:blocked|handled|triggered|prevented|caught)\b", re.IGNORECASE), "correctly_outcome"),
    (re.compile(r"\bsuccessfully\s+(?:blocked|handled|triggered|prevented|caught)\b", re.IGNORECASE), "successfully_outcome"),
    (re.compile(r"\b(?:blocked|handled|triggered|prevented|caught)\s+by\b", re.IGNORECASE), "by_outcome"),
    (re.compile(r"\bis\s+responsible\s+for\b", re.IGNORECASE), "responsible"),
    (re.compile(r"\b(?:owned|handled)\s+by\b", re.IGNORECASE), "owned_handled"),
]

# FOLDER_CREATE patterns — "made an [X]" for folder/file creation claims
# REQUIRE forward slash (/) or dot-extension (.md, .py, .toml) in captured path
# This prevents matching analytical prose like "made an problem", "made an impact"
_FOLDER_CREATE_PATTERNS = [
    # "made an skills/..." or "made an hooks/docs/..." — paths with slashes
    (re.compile(r"\bmade\s+an?\s+(\S+/\S*)", re.IGNORECASE), "folder_path"),
    # "made an something.md" or "made an package.toml" — paths with dot-extensions
    (re.compile(r"\bmade\s+an?\s+(\S*\.\w+)", re.IGNORECASE), "folder_path"),
]

# PONYTAIL_TAG_PATTERNS — audit tool findings with specific verification requirements
# Map Ponytail tags to ClaimType values
_PONYTAIL_TAG_PATTERNS = [
    (re.compile(r"\bdelete:\s+(.+?)(?=\n|$)", re.IGNORECASE), "delete"),
    (re.compile(r"\byagni:\s+(.+?)(?=\n|$)", re.IGNORECASE), "yagni"),
    (re.compile(r"\bstdlib:\s+(.+?)(?=\n|$)", re.IGNORECASE), "stdlib"),
    (re.compile(r"\bnative:\s+(.+?)(?=\n|$)", re.IGNORECASE), "native"),
    (re.compile(r"\bshrink:\s+(.+?)(?=\n|$)", re.IGNORECASE), "shrink"),
]


# ASCII art strip: remove box-drawing characters before pattern matching.
# These characters appear in diagrams and cause spurious claim detection.
_ASCII_ART_STRIP = re.compile(
    r"[─━═┄┅┆┇┈┉┊┋┌┍┎┏┐┑┒┓└┕┖┗┘┙┚┛├┝┞┟┠┡┢┣┤┥┦┧┨┩┪┫┬┭┮┯┰┱┲┳┴┵┶┷┸┹┺┻┼┽┾┿╀╁╂╃╄╅╆╇╈╉╊╋╌╍╎╏═║╒╓╔╕╖╗╘╙╚╛╜╝╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬╭╮╯╰╱╲╳╴╵╶╷╸╹╺╻╼╽╾╿➔➘➙➚➛➜➝➞➟➠➡➢➣➤⇄⇅⇆⇇⇈⇉⇊➺]"
)


def _strip_ascii_art(text: str) -> str:
    """Remove ASCII box-drawing characters that trigger false claim detection."""
    return _ASCII_ART_STRIP.sub(" ", text)


@dataclass
class Claim:
    """Verification claim with targets and metadata.

    This is the Phase 2 unified claim representation that replaces
    RawClaim from Phase 1. Field alignment ensures smooth migration.
    """

    id: str
    text: str
    targets: List[str]
    type: str
    confidence: float
    risk_domain: str
    has_hedge: bool
    decomposition_eligible: bool = False


def _detect_outcome_attribution_claims(response_text: str) -> List[Claim]:
    """Scan for outcome attribution patterns not covered by HypothesisAsFactDetector.

    These patterns (from overconfidence_detector) detect claims about who or what
    handled, blocked, triggered, or caused an outcome. They go through
    build_verdicts() to verify against tool output rather than string-search exemptions.
    """
    claims: List[Claim] = []
    stripped = _strip_ascii_art(response_text)
    sentences = _split_sentences(stripped)

    for sentence in sentences:
        if len(sentence.strip()) < 10:
            continue
        for pattern, _pattern_name in _OUTCOME_ATTRIBUTION_PATTERNS:
            match = pattern.search(sentence)
            if match:
                # Extract the actor (what followed "by")
                actor = None
                by_match = re.search(r"\bby\s+(\S+)", sentence, re.IGNORECASE)
                if by_match:
                    actor = by_match.group(1)

                claim = Claim(
                    id=str(uuid.uuid4()),
                    text=sentence,
                    targets=[actor] if actor else [],
                    type="OUTCOME_ATTRIBUTION",
                    confidence=0.75,
                    risk_domain="SYSTEM",
                    has_hedge=False,
                )
                claims.append(claim)
                break  # One claim per sentence
    return claims


def _detect_folder_create_claims(response_text: str) -> List[Claim]:
    """Scan for folder/file creation claims via 'made an [X]' pattern.

    Claims like "made an inference gap folder" are checked against Glob/Read
    tool output to verify the folder actually exists.
    """
    claims: List[Claim] = []
    stripped = _strip_ascii_art(response_text)
    sentences = _split_sentences(stripped)

    for sentence in sentences:
        if len(sentence.strip()) < 10:
            continue
        for pattern, _pattern_name in _FOLDER_CREATE_PATTERNS:
            match = pattern.search(sentence)
            if match:
                folder_path = match.group(1)
                claim = Claim(
                    id=str(uuid.uuid4()),
                    text=sentence,
                    targets=[folder_path],
                    type="FOLDER_CREATE",
                    confidence=0.7,
                    risk_domain="FS_CRITICAL",
                    has_hedge=False,
                )
                claims.append(claim)
                break
    return claims


def _detect_ponytail_claims(response_text: str) -> List[Claim]:
    """Detect Ponytail audit findings with specific verification requirements.

    Ponytail tags map to ClaimType enum values and require specialized
    verification logic (consumer counts, stdlib checks, platform features).

    delete: → USAGE_VERIFICATION → consumer-count check
    yagni: → USAGE_VERIFICATION → single-consumer check
    stdlib: → COMPARISON_VERIFICATION → stdlib equivalence (advisory)
    native: → COMPARISON_VERIFICATION → platform-native equivalence (advisory)
    shrink: → TRANSFORMATION_VERIFICATION → semantic preservation (advisory)
    """
    claims: List[Claim] = []
    stripped = _strip_ascii_art(response_text)

    for pattern, tag_type in _PONYTAIL_TAG_PATTERNS:
        for match in pattern.finditer(stripped):
            claim_text = match.group(0).strip()
            targets = [match.group(1).strip()] if match.group(1) else []

            # Map Ponytail tag to ClaimType
            claim_type_map = {
                "delete": "USAGE_VERIFICATION",
                "yagni": "USAGE_VERIFICATION",
                "stdlib": "COMPARISON_VERIFICATION",
                "native": "COMPARISON_VERIFICATION",
                "shrink": "TRANSFORMATION_VERIFICATION",
            }
            claim_type = claim_type_map.get(tag_type, "UNKNOWN")

            claim = Claim(
                id=str(uuid.uuid4()),
                text=claim_text,
                targets=targets,
                type=claim_type,
                confidence=0.8,
                risk_domain="FS_CRITICAL",
                has_hedge=False,
            )
            claims.append(claim)

    return claims


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences for per-sentence claim detection."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def extract_claims(response_text: str) -> List[Claim]:
    """Extract verification claims from response text.

    This function wraps the Phase 1 HypothesisAsFactDetector and converts
    RawClaim objects to Phase 2 Claim objects with aligned fields.

    It also scans for OUTCOME_ATTRIBUTION patterns that
    HypothesisAsFactDetector does not cover, so all claims go through
    build_verdicts() rather than standalone string-search exemptions.

    FOLDER_CREATE is NOT included here — it is handled by Phase 2's standalone
    check in StopHook_unverified_stance.py, which runs independently.

    Args:
        response_text: The LLM response text to analyze

    Returns:
        List of Claim objects representing detected claims

    Examples:
        >>> text = "Package has no skill/ directory"
        >>> claims = extract_claims(text)
        >>> assert len(claims) > 0
        >>> assert claims[0].type == "ABSENCE"
    """
    detector = HypothesisAsFactDetector()
    raw_claims: List[RawClaim] = detector.detect_claims(response_text)

    # Convert RawClaim to Claim with field alignment
    claims: List[Claim] = []
    for raw in raw_claims:
        claim = _raw_claim_to_claim(raw)
        if claim:
            claims.append(claim)

    # OUTCOME_ATTRIBUTION claims: from overconfidence patterns (not in HypothesisAsFactDetector)
    claims.extend(_detect_outcome_attribution_claims(response_text))

    # Ponytail tags: audit tool findings with specific verification requirements
    claims.extend(_detect_ponytail_claims(response_text))

    return claims


def _raw_claim_to_claim(raw: RawClaim) -> Claim | None:
    """Convert RawClaim to Claim with field alignment.

    Field mapping:
    - text → text (same)
    - subject_entity → targets[0] (rename+list wrapper)
    - claim_type → type (rename, strip "entity_" prefix)
    - confidence → confidence (same)
    - has_hedge → has_hedge (same)
    - risk_domain → risk_domain (same)

    Args:
        raw: RawClaim object from Phase 1 detector

    Returns:
        Claim object with aligned fields, or None if conversion fails
    """
    try:
        # Generate unique ID for claim
        claim_id = str(uuid.uuid4())

        # Map claim_type: "entity_absence" → "ABSENCE", "rule" → "RULE", etc.
        claim_type = raw.claim_type
        if claim_type.startswith("entity_"):
            claim_type = claim_type.replace("entity_", "").upper()
        else:
            claim_type = claim_type.upper()

        # Wrap subject_entity in targets list (RawClaim has single string)
        targets = [raw.subject_entity] if raw.subject_entity else []

        return Claim(
            id=claim_id,
            text=raw.text,
            targets=targets,
            type=claim_type,
            confidence=raw.confidence,
            risk_domain=raw.risk_domain,
            has_hedge=raw.has_hedge,
        )
    except (AttributeError, ValueError):
        # Fail gracefully on malformed RawClaim
        return None


# ---------------------------------------------------------------------------
# Claim classification for decomposition routing
# ---------------------------------------------------------------------------

# Mapping from claim type prefixes to functional categories.
# These align with pattern categories in __lib/claim_patterns.py.
_CLASSIFICATION_MAP: dict[str, str] = {
    # extraction — standard claim detection
    "ABSENCE": "extraction",
    "RULE": "extraction",
    "OUTCOME_ATTRIBUTION": "extraction",
    "FOLDER_CREATE": "extraction",
    # escalation — high-risk, strict enforcement
    "ACTION": "escalation",
    "BEHAVIORAL": "escalation",
    "ERROR": "escalation",
    # coverage_signal — evidence quality check needed
    "TENTATIVE": "coverage_signal",
    "VERIFICATION": "coverage_signal",
}

# Compound/aggregate language triggers for decomposition
_COMPOUND_INDICATORS = re.compile(
    r"\b(?:all|every|each|both|and|while|but|as well as|along with)\b",
    re.IGNORECASE,
)


def classify_claim(claim: Claim) -> str:
    """Return the functional category for pattern routing.

    Categories:
    - "extraction" — standard claim detection (existing behavior)
    - "decomposition_trigger" — should be decomposed before verification
    - "escalation" — high-risk, strict enforcement needed
    - "coverage_signal" — evidence quality check needed

    Deterministic, regex-based.

    Args:
        claim: Claim object to classify.

    Returns:
        Category string.
    """
    # Check for decomposition trigger first (overrides base classification)
    if _COMPOUND_INDICATORS.search(claim.text):
        return "decomposition_trigger"

    # Map from claim type prefix
    claim_type_upper = claim.type.upper()
    for prefix, category in _CLASSIFICATION_MAP.items():
        if prefix in claim_type_upper:
            return category

    return "extraction"


# __debug__ invariant: verify ClaimType enum values are lowercase (matching the pattern
# 'session_behavior', 'analysis', etc.) and that _raw_claim_to_claim uppercases them.
# This catches the case-mismatch bug where _is_self_verified_claim checked
# "session_behavior" but _raw_claim_to_claim produces "SESSION_BEHAVIOR".
if __debug__:
    import sys as _sys

    _ct_mod = _sys.modules.get("anti_sycophancy.hypothesis_as_fact_detector")
    if _ct_mod is not None:
        _mismatches = sorted(
            f"  ClaimType.{e.name} = {e.value!r}  (expected lowercase: {e.name.lower()!r})"
            for e in _ct_mod.ClaimType
            if e.value != e.name.lower()
        )
        if _mismatches:
            raise AssertionError(
                f"ClaimType enum values must be lowercase names in "
                f"hypothesis_as_fact_detector.py:\n"
                + "\n".join(_mismatches)
                + "\n"
                + "  _raw_claim_to_claim() uppercases these to produce Claim.type values,\n"
                + "  so _is_self_verified_claim() must check the uppercase form."
            )
