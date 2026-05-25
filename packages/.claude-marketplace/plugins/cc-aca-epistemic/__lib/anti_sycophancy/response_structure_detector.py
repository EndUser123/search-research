"""
Response Structure Detector v1.0

Detects response-LEVEL structural waste patterns that phrase-level detectors miss.
All existing detectors are sentence/phrase-level. These are response-level.

PATTERNS DETECTED:
  1. Correction Theater  — self-correction ceremony that doesn't change the conclusion
  2. Recursive Hypocrisy — fabricated specifics inside a correction section

DESIGN CONSTRAINTS:
  - Pure function of response text (no state, no cross-turn dependency)
  - Multi-terminal safe (inherently — no shared state)
  - No TTL (nothing to expire)
  - No stale data risk (analyzes current response only)
  - Warn severity only (systemMessage injection, not block)
  - Min 100 words before any check fires (short responses can't have structural waste)

Usage:
    from anti_sycophancy.response_structure_detector import detect_response_structure

    findings = detect_response_structure(response_text)
    for match in findings:
        print(f"{match.pattern}: {match.matched}")
        print(f"  -> {match.suggestion}")
"""

from __future__ import annotations

import re
from typing import NamedTuple

__all__ = ["detect_response_structure", "build_self_prompt", "StructureMatch"]

MIN_WORD_COUNT = 100


class StructureMatch(NamedTuple):
    """Detection result for a response-level structural waste pattern."""
    pattern: str      # "correction_theater" | "recursive_hypocrisy"
    matched: str      # Human-readable description of what triggered
    suggestion: str   # What the LLM should do instead
    severity: str     # Always "warn" -- starts non-blocking, escalate via logs


# === Pattern 1: Correction Theater ===========================================
#
# Fires when BOTH a correction marker AND an unchanged-conclusion marker appear
# anywhere in the response.
#
# Rationale: The canonical annoying case spans the whole response (correction
# sections + "recommendation still holds" in the summary). Section-scoping
# would miss it. False positives are acceptable (warn only); the self-prompt
# asks the LLM to reason about whether the correction was genuine.

CORRECTION_MARKERS: list[str] = [
    r"\bi was wrong\b",
    r"\bcorrection[:\s]",
    r"\blet me correct\b",
    r"\bi made (?:it |that |this )?up\b",
    r"\brule \d+ violation\b",
    r"\bwhat i should have said\b",
    r"\bi shouldn't have (?:said|claimed|stated)\b",
    r"\bthat was (?:incorrect|wrong|inaccurate|false|a mistake)\b",
    r"\bthat is (?:incorrect|wrong|inaccurate|false)\b",
    r"\bi (?:overstated|understated|misstated|fabricated|invented)\b",
    r"\bmy (?:claim|statement|assertion|number|figure).{0,40}"
    r"(?:was wrong|was incorrect|was made up|was fabricated|was speculation)\b",
    r"\bsummary of corrections\b",
    r"\|\s*my claim\s*\|",            # | My claim | Reality | table
    r"\|\s*what i said\s*\|",
    r"\|\s*claim\s*\|\s*reality\s*\|",
]

UNCHANGED_CONCLUSION_MARKERS: list[str] = [
    r"\brecommendation (?:still |doesn't change\b|remains\b|holds\b)",
    r"\bconclusion (?:still |doesn't change\b|remains\b|holds\b)",
    r"\banswer (?:is |remains |doesn't change\b|stays )(?:the )?same\b",
    r"\bstill recommend (?:the same|this|that|against|not)\b",
    r"\banalysis (?:still )?(?:holds|applies|stands)\b",
    r"\bdoesn't change (?:my|the) (?:recommendation|conclusion|answer|analysis)\b",
    r"\bnet (?:result|outcome).{0,25}(?:same|unchanged|identical)\b",
    r"\bbottom line (?:doesn't change|remains|is still|stays the same)\b",
    r"\bmy advice (?:remains|stays|is still) (?:the )?same\b",
    r"\bstill (?:don't build|avoid building|recommend against)\b",
]

# Evidence-based unchanged markers that are acceptable ("tests still pass" is
# fine; "my recommendation still holds" after a correction ceremony is not).
# SAFETY NET: No current UNCHANGED_CONCLUSION_MARKERS pattern can match these
# phrases, so this list is forward-looking only — it guards against future
# broad additions. Do not remove; use _is_exempt_unchanged_unit tests to verify.
UNCHANGED_EVIDENCE_EXEMPT: list[str] = [
    r"\btests? (?:still )?(?:pass|passes|passing)\b",
    r"\bbuilds? (?:still )?(?:succeed|succeeds|passing)\b",
    r"\bstill (?:compiles?|runs?|works?)\b",
]

_CORRECTION_THEATER_SELF_PROMPT = """\
RESPONSE STRUCTURE CHECK -- Correction Theater

Your response contains self-correction markers AND a "conclusion unchanged" \
statement. This is only acceptable if the correction is genuinely new reasoning \
that reaches the same answer through better logic -- not ceremony.

Ask yourself:
1. Did your correction actually change your answer, or just the justification?
2. If the conclusion is the same, could you have expressed this in ONE sentence \
("I overstated X, but the conclusion holds because Y") instead of this entire \
correction section?
3. Are you performing humility rather than delivering a useful correction?

Rule: Correction ceremony must be proportional to correction impact. If the \
conclusion doesn't change, say so briefly and move on."""


# === Pattern 2: Recursive Hypocrisy ==========================================
#
# Detects fabricated specifics INSIDE a correction section.
# The canonical case: "I made up 1.5s" then immediately "if Tier 2 catches 95%"
# (also made up, inside the very correction).
#
# Approach:
#   - Locate correction sections (paragraphs containing correction markers)
#   - Within those sections, detect round numbers in hypothetical framing
#   - "Round" = multiple of 5 for percentages, or suspiciously clean latencies
#   - "Hypothetical framing" = "if X catches N%", "say N%", "around N%", etc.

# Percentages that are suspiciously round (multiples of 5): 50%, 55%, ..., 95%
_ROUND_PCT_PATTERN = re.compile(
    r"\b(?:if|say|say it|suppose|imagine|around|approximately|maybe|perhaps|"
    r"let['\u2019]s say)\b"
    r".{0,40}"
    r"\b([05][05]?|[1-9][05])\s*%",
    re.IGNORECASE,
)

# Latencies that are suspiciously round
_ROUND_LATENCY_PATTERN = re.compile(
    r"\b(?:if|say|suppose|imagine|around|approximately|maybe|perhaps|"
    r"let['\u2019]s say)\b"
    r".{0,40}"
    r"\b(?:0\.5|1|1\.5|2|5|10|100|200|500|1000|2000)\s*"
    r"(?:ms|milliseconds?|s|seconds?)\b",
    re.IGNORECASE,
)

_RECURSIVE_HYPOCRISY_SELF_PROMPT = """\
RESPONSE STRUCTURE CHECK -- Recursive Hypocrisy

Your response contains {matched!r} -- an ungrounded hypothetical -- inside a \
correction section where you are already apologizing for fabricating numbers.

Ask yourself:
1. Where does {matched!r} come from? Did you measure it, read it, or invent it?
2. If invented: remove it. Correction sections must not introduce new \
ungrounded claims.
3. If genuinely hypothetical: label it explicitly \
("as a hypothetical threshold, not a measured value...").

Rule: Correction sections are held to higher evidentiary standards than \
normal prose, not lower."""


# === Internal helpers =========================================================

def _matches_any(text: str, patterns: list[str]) -> str | None:
    """Return the first matched substring for any pattern, or None."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(0)
    return None


def _find_correction_marker(text: str) -> str | None:
    return _matches_any(text, CORRECTION_MARKERS)


def _is_exempt_unchanged(match_text: str) -> bool:
    """Check if a specific unchanged-marker match is an evidence-based exempt form."""
    for pat in UNCHANGED_EVIDENCE_EXEMPT:
        if re.search(pat, match_text, re.IGNORECASE):
            return True
    return False


def _find_unchanged_marker(text: str) -> str | None:
    # Check each unchanged-conclusion pattern; skip those that are evidence-exempt.
    # This is per-match, not global: "tests still pass" being present must NOT
    # suppress detection of "recommendation still holds" in the same response.
    t = text.lower()
    for pat in UNCHANGED_CONCLUSION_MARKERS:
        m = re.search(pat, t, re.IGNORECASE | re.DOTALL)
        if m:
            matched = m.group(0)
            if not _is_exempt_unchanged(matched):
                return matched
    return None


def _extract_correction_sections(response: str) -> list[str]:
    """
    Return sub-strings of the response that START with a correction marker.

    Splits on blank lines; once a correction paragraph is found, collects
    subsequent paragraphs until a new markdown heading appears.
    This scopes recursive-hypocrisy detection to actual correction prose.
    """
    sections: list[str] = []
    paragraphs = re.split(r"\n\s*\n", response)
    in_correction = False
    current: list[str] = []

    for para in paragraphs:
        if _find_correction_marker(para):
            # Start (or restart) a correction section
            if in_correction and current:
                sections.append("\n\n".join(current))
            in_correction = True
            current = [para]
        elif in_correction:
            if re.match(r"\s*#{1,3}\s+", para):
                # New heading ends the correction section
                sections.append("\n\n".join(current))
                current = []
                in_correction = False
            else:
                current.append(para)

    if current and in_correction:
        sections.append("\n\n".join(current))

    return sections


def _find_fabricated_hypothetical(section: str) -> str | None:
    """Return the first fabricated-in-hypothetical match, or None."""
    m = _ROUND_PCT_PATTERN.search(section)
    if m:
        return m.group(0)
    m = _ROUND_LATENCY_PATTERN.search(section)
    if m:
        return m.group(0)
    return None


# === Public API ===============================================================

def detect_response_structure(response: str) -> list[StructureMatch]:
    """
    Analyze a complete response for structural waste patterns.

    Pure function. No state. No I/O. No side effects.
    Returns an empty list if the response is clean or too short to check.
    """
    if not response:
        return []
    if len(response.split()) < MIN_WORD_COUNT:
        return []

    findings: list[StructureMatch] = []

    # --- Pattern 1: Correction Theater ---------------------------------------
    correction_marker = _find_correction_marker(response)
    if correction_marker:
        unchanged_marker = _find_unchanged_marker(response)
        if unchanged_marker:
            findings.append(StructureMatch(
                pattern="correction_theater",
                matched=(
                    f"Correction ('{correction_marker}') "
                    f"+ unchanged conclusion ('{unchanged_marker}')"
                ),
                suggestion=(
                    "If the conclusion doesn't change, say so in one sentence. "
                    "Don't build a correction ceremony around a stable answer."
                ),
                severity="warn",
            ))

    # --- Pattern 2: Recursive Hypocrisy --------------------------------------
    # Only scan correction sections (no correction marker = no sections to scan)
    if correction_marker:
        for section in _extract_correction_sections(response):
            fabricated = _find_fabricated_hypothetical(section)
            if fabricated:
                findings.append(StructureMatch(
                    pattern="recursive_hypocrisy",
                    matched=(
                        f"Ungrounded hypothetical '{fabricated}' "
                        f"inside correction section"
                    ),
                    suggestion=(
                        "Remove or explicitly label as hypothetical -- "
                        "correction sections must not introduce new ungrounded claims."
                    ),
                    severity="warn",
                ))
                break  # One finding per response is sufficient signal

    return findings


def build_self_prompt(findings: list[StructureMatch]) -> str:
    """
    Compose the systemMessage self-prompt text from findings.
    Called by Stop.py to inject a warning into the next response.
    """
    parts: list[str] = []
    for f in findings:
        if f.pattern == "correction_theater":
            parts.append(_CORRECTION_THEATER_SELF_PROMPT)
        elif f.pattern == "recursive_hypocrisy":
            m = re.search(r"'([^']+)'", f.matched)
            phrase = m.group(1) if m else f.matched
            parts.append(_RECURSIVE_HYPOCRISY_SELF_PROMPT.format(matched=phrase))
    return "\n\n".join(parts)


# === Self-tests (run directly: python response_structure_detector.py) ========

if __name__ == "__main__":
    def _pad(n: int = 100) -> str:
        return " " + " ".join(["filler"] * n)

    # ------------------------------------------------------------------
    # Pattern 1 — should DETECT
    # ------------------------------------------------------------------

    # Canonical annoying conversation
    annoying = (
        "You're right to push back on all three. Let me address each:\n\n"
        "1. I was wrong about what Tier 2 catches.\n\n"
        "2. '1.5s latency' -- where did this number come from?\n"
        "I made it up. Rule 1 violation -- I stated a claim without verification.\n\n"
        "3. I got the burden of proof backwards.\n\n"
        "Summary of corrections:\n"
        "| My claim | Reality |\n"
        "|----------|---------|\n"
        "| Tier 2 only catches absence claims | It catches more |\n"
        "| 1.5s latency | Made up |\n\n"
        "Recommendation still holds (don't build Tier 3), but for better reasons."
        + _pad(10)
    )
    r = detect_response_structure(annoying)
    assert any(f.pattern == "correction_theater" for f in r), \
        f"Should detect correction theater in canonical case, got: {r}"
    print("PASS: canonical annoying conversation -> correction_theater")

    # Simple: "I was wrong" + "still holds"
    simple = "I was wrong about the estimate. The recommendation still holds." + _pad()
    r = detect_response_structure(simple)
    assert any(f.pattern == "correction_theater" for f in r), \
        f"Simple theater not detected: {r}"
    print("PASS: simple correction theater detected")

    # ------------------------------------------------------------------
    # Pattern 1 — should NOT detect
    # ------------------------------------------------------------------

    # Genuine correction with changed conclusion (no unchanged marker)
    genuine = (
        "I was wrong about which endpoint to use. "
        "You should call /v2/auth instead of /v1/auth. "
        "The token format is different -- use Bearer, not Basic. "
        "Update your integration accordingly."
        + _pad()
    )
    r = detect_response_structure(genuine)
    ct = [f for f in r if f.pattern == "correction_theater"]
    assert not ct, f"Genuine correction should not flag: {ct}"
    print("PASS: genuine correction (no unchanged marker) not flagged")

    # Too short to check
    short = "I was wrong. The recommendation still holds."
    r = detect_response_structure(short)
    assert r == [], f"Short response should be skipped: {r}"
    print("PASS: short response skipped")

    # "Tests still pass" is an evidence-exempt unchanged statement
    tests_ok = (
        "I was wrong about the regex pattern. Fixed it. "
        "The full test suite still passes with the corrected implementation."
        + _pad()
    )
    r = detect_response_structure(tests_ok)
    ct = [f for f in r if f.pattern == "correction_theater"]
    assert not ct, f"'Tests still pass' should be exempt: {ct}"
    print("PASS: 'tests still pass' correctly exempted")

    # ------------------------------------------------------------------
    # Pattern 2 — should DETECT
    # ------------------------------------------------------------------

    # Round percentage in hypothetical framing inside correction section
    rh_pct = (
        "I made it up. I should not have stated 1.5s without measurement.\n\n"
        "The correct framing: if Tier 2 catches 95% of absence claims, "
        "that's evidence it's sufficient."
        + _pad()
    )
    r = detect_response_structure(rh_pct)
    rh = [f for f in r if f.pattern == "recursive_hypocrisy"]
    assert rh, f"Should detect 95% hypothetical inside correction: {r}"
    print("PASS: round percentage in hypothetical inside correction detected")

    # Round latency in hypothetical framing inside correction section
    rh_lat = (
        "I was wrong to claim 1.5s. "
        "Say the overhead is around 100ms per call -- that's still significant."
        + _pad()
    )
    r = detect_response_structure(rh_lat)
    rh = [f for f in r if f.pattern == "recursive_hypocrisy"]
    assert rh, f"Should detect round latency hypothetical in correction: {r}"
    print("PASS: round latency in hypothetical inside correction detected")

    # ------------------------------------------------------------------
    # Pattern 2 — should NOT detect
    # ------------------------------------------------------------------

    # Round number in hypothetical but OUTSIDE any correction section
    clean_hyp = (
        "This is a normal response with no corrections. "
        "If the cache hit rate is around 90%, performance should be acceptable. "
        "The tradeoff between consistency and availability is well understood."
        + _pad()
    )
    r = detect_response_structure(clean_hyp)
    rh = [f for f in r if f.pattern == "recursive_hypocrisy"]
    assert not rh, f"Hypothetical outside correction section should not flag: {rh}"
    print("PASS: hypothetical outside correction section not flagged")

    # ------------------------------------------------------------------
    # build_self_prompt smoke test
    # ------------------------------------------------------------------
    r = detect_response_structure(annoying)
    prompt = build_self_prompt(r)
    assert "RESPONSE STRUCTURE CHECK" in prompt, "Self-prompt missing header"
    assert len(prompt) > 50, "Self-prompt too short"
    print("PASS: build_self_prompt returns non-empty prompt")

    print("\nAll tests passed.")
