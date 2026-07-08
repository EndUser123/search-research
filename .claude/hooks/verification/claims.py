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

try:
    from anti_sycophancy.hypothesis_as_fact_detector import (
        ClaimType,
        HypothesisAsFactDetector,
        RawClaim,
    )
    _HAS_HYPOTHESIS_DETECTOR = True
except ImportError:
    ClaimType = None  # type: ignore[assignment]
    HypothesisAsFactDetector = None  # type: ignore[assignment]
    RawClaim = None  # type: ignore[assignment]
    _HAS_HYPOTHESIS_DETECTOR = False


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


# ---------------------------------------------------------------------------
# External-fact predicate (canonical home — Close-the-Loop Phase 3a/3b)
# ---------------------------------------------------------------------------
# Pure-text detector for claims about EXTERNAL software/world not verifiable
# from the repo: library version assertions, API behavior claims, post-cutoff
# entity existence, citation-free ecosystem facts. Distinct from the
# claim_classifier "external_fact" domain (agent's OWN code). SHADOW/advisory
# until Phase 6 real-corpus TP reseeding (gate-discrimination rule).
# Single source: evals/external_fact_detector.py re-exports these symbols.
from typing import Literal as _Literal

ExternalFactKind = _Literal[
    "version_assertion",      # "library X v2.3", "X version 2.3"
    "api_behavior_claim",     # "X supports Y", "X requires Y", "X's API does Z"
    "entity_existence",       # "X was released", "X is a new framework"
    "ecosystem_fact",         # "the latest X", "npm package X", citation-free
]

# Two name classes: bare-major versions ("React 19") are only credible inside
# an api_behavior_claim where the trailing verb ("supports") disambiguates.
# A capitalized English word + a bare integer ("Phase 2", "Found 6") is the
# dominant FP shape on real prose, so version_assertion requires dotted/v.
_CAP_NAME = r"[A-Z][A-Za-z0-9_-]{1,30}"
_LOW_NAME = r"[a-z][a-z0-9-]{2,30}"
_NAME = f"{_CAP_NAME}|{_LOW_NAME}"
_VERSION_FULL = r"v?\d+(?:\.\d+){1,3}"
_VERSION_MAJOR = r"v?\d+"

# Generic English words that must never serve as "external entity" names.
# Derived from stop_blocks FP shapes. Case-insensitive. The api_behavior verbs
# are listed so _names_only_generic's all() check is meaningful: "claim
# requires" filters (both generic) while "React requires" survives.
_GENERIC_WORDS = frozenset({
    "phase", "step", "stage", "round", "pass", "turn", "session", "cycle",
    "found", "deleted", "removed", "added", "applied", "detected", "fixed",
    "all", "both", "each", "every", "some", "many", "few", "several",
    "claim", "line", "file", "lines", "files", "row", "rows", "issue",
    "issues", "test", "tests", "suite", "hook", "hooks", "gate", "gates",
    "block", "blocks", "warning", "error", "exit", "code", "path", "paths",
    "branch", "commit", "change", "diff", "hunk", "edit", "edits", "write",
    "fix", "bug", "feature", "task", "work", "total", "count", "number",
    "version", "release", "build", "run", "log", "output", "input",
    "result", "results", "response", "message", "model", "system", "tool",
    "the", "this", "that", "these", "those", "with", "across", "over",
    "into", "onto", "just", "only", "also", "first", "second", "third",
    "last", "next", "prior", "previous", "new", "old", "current",
    "supports", "requires", "exposes", "provides", "ships", "api",
    "released", "deprecated", "announced", "launched", "is", "was",
    "has", "been", "version", "of", "the",
})

EXTERNAL_FACT_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "version_assertion": [
        re.compile(rf"\b({_NAME})\s+(?:version\s+)?({_VERSION_FULL})\b"),
        re.compile(rf"\b({_VERSION_FULL})\s+(?:of|release\s+of)\s+({_NAME})\b"),
    ],
    "api_behavior_claim": [
        re.compile(rf"\b({_CAP_NAME})\s+(?:({_VERSION_MAJOR})\s+)?(?:supports|requires|exposes|provides|ships\s+with)\b"),
        re.compile(rf"\b({_LOW_NAME})\s+(?:({_VERSION_FULL})\s+)?(?:supports|requires|exposes|provides|ships\s+with)\b"),
        re.compile(rf"\b({_NAME})['']?s?\s+API\s+\w"),
        re.compile(rf"\bthe\s+({_NAME})\s+API\s+\w"),
    ],
    "entity_existence": [
        re.compile(rf"\b({_NAME})\s+(?:was|has been|is)\s+(?:released|deprecated|announced|launched)\b"),
        re.compile(rf"\bnew\s+({_NAME})\s+(?:framework|library|package|release)\b"),
        re.compile(rf"\bthe\s+latest\s+({_NAME})\b"),
    ],
    "ecosystem_fact": [
        re.compile(rf"\b(?:npm|pip|cargo)\s+(?:install\s+)?({_NAME})\b"),
        re.compile(rf"\b({_NAME})\s+(?:package|crate|module)\s+(?:is|does|has)\b"),
    ],
}

# Exclusions — hypotheticals and meta/process are NOT firm external claims.
EXTERNAL_FACT_HEDGE = re.compile(
    r"\b(?:might|could|may|possibly|perhaps|allegedly|supposedly|"
    r"i believe|i think|likely|roughly|around|about)\b",
    re.IGNORECASE,
)
EXTERNAL_FACT_OWN_CODE = re.compile(
    r"\b(?:the fix|this change|all tests|pytest|my code|this repo|the bug|"
    r"this hook|this plugin|the suite|working tree|this branch)\b",
    re.IGNORECASE,
)
EXTERNAL_FACT_REPO_PATH = re.compile(r"[A-Za-z]:[\\/]|(?:__lib__|hooks|src|tests)[\\/]")


def detect_external_facts(text: str) -> list[dict]:
    """Return one dict per external-world claim match.

    Each dict: {kind, span, snippet, name}. Empty list = no claim detected.
    Excludes hypotheticals and own-code claims (claim_classifier's domain).
    ``name`` is the first name capture group (the external entity), used by
    the evidence join to match against grounding-tool targets.
    """
    if not isinstance(text, str) or not text.strip():
        return []
    if EXTERNAL_FACT_HEDGE.search(text) and not _efd_has_firm_assertion(text):
        return []
    if EXTERNAL_FACT_OWN_CODE.search(text) and not _efd_names_external_entity_outside_repo(text):
        return []
    hits: list[dict] = []
    for kind, pats in EXTERNAL_FACT_PATTERNS.items():
        for p in pats:
            for m in p.finditer(text):
                span = m.group(0)
                if EXTERNAL_FACT_REPO_PATH.search(span):
                    continue
                if _efd_names_only_generic(span):
                    continue
                start, end = m.span()
                snippet = text[max(0, start - 40): min(len(text), end + 40)]
                # group(1) is the name on every pattern; group(2) may be a version.
                name = m.group(1) if m.groups() else span
                hits.append({"kind": kind, "span": span, "snippet": snippet, "name": name})
    seen, out = set(), []
    for h in hits:
        key = (h["kind"], h["span"])
        if key not in seen:
            seen.add(key)
            out.append(h)
    return out


def _efd_has_firm_assertion(text: str) -> bool:
    return bool(re.search(
        r"\b(?:is|are|was|were|has|does|supports|requires|released|deprecated)\b",
        text,
    ))


def _efd_names_only_generic(span: str) -> bool:
    """True if every alphabetic token in the span is a generic English word."""
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]*", span)
    if not tokens:
        return False
    return all(t.lower() in _GENERIC_WORDS for t in tokens)


def _efd_names_external_entity_outside_repo(text: str) -> bool:
    return bool(
        re.search(rf"\b({_NAME})\s+(?:supports|requires|v\d+|version\s+\d)", text)
        and not EXTERNAL_FACT_REPO_PATH.search(text)
    )


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
        for pattern, pattern_name in _OUTCOME_ATTRIBUTION_PATTERNS:
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
        for pattern, pattern_name in _FOLDER_CREATE_PATTERNS:
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


def _detect_external_fact_claims(response_text: str) -> List[Claim]:
    """Detect external-world-fact claims via the canonical predicate.

    Each ``detect_external_facts`` hit becomes a Claim of type EXTERNAL_FACT.
    The matched entity name is the sole target, so the engine's evidence join
    can match it against grounding-tool (WebSearch/WebFetch/API) targets.
    """
    claims: List[Claim] = []
    stripped = _strip_ascii_art(response_text)
    for hit in detect_external_facts(stripped):
        name = hit.get("name") or ""
        targets = [name] if name else []
        claims.append(Claim(
            id=str(uuid.uuid4()),
            text=hit["span"],
            targets=targets,
            type="EXTERNAL_FACT",
            confidence=0.8,
            risk_domain="external_fact",
            has_hedge=bool(EXTERNAL_FACT_HEDGE.search(hit["span"])),
            decomposition_eligible=False,
        ))
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
    claims: List[Claim] = []
    if _HAS_HYPOTHESIS_DETECTOR:
        detector = HypothesisAsFactDetector()
        raw_claims: List[RawClaim] = detector.detect_claims(response_text)

        # Convert RawClaim to Claim with field alignment
        for raw in raw_claims:
            claim = _raw_claim_to_claim(raw)
            if claim:
                claims.append(claim)

    # OUTCOME_ATTRIBUTION claims: from overconfidence patterns (not in HypothesisAsFactDetector)
    claims.extend(_detect_outcome_attribution_claims(response_text))

    # EXTERNAL_FACT claims: post-cutoff / external-world assertions (Close-the-Loop Phase 3b)
    claims.extend(_detect_external_fact_claims(response_text))

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
    "EXTERNAL_FACT": "escalation",
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
