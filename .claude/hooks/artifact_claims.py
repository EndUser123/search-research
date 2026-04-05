#!/usr/bin/env python3
"""
artifact_claims.py - Artifact-specific claim extraction and verification
========================================================================

Extracts "strong claims about specific artifacts" from responses and checks
whether concrete observations back them up.

Used by the unverified_artifact_claims gate in Stop.py.

Design decisions:
- Regex-based, stdlib-only, tunable patterns.
- Sentence splitting avoids breaking on file paths and URLs.
- Meta-conversation and self-referential content is excluded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ArtifactClaim:
    """A strong claim about a specific artifact or outcome."""
    text: str                           # The sentence containing the claim
    target_artifact: str | None      # File path / hook / config name, or None for outcome-only
    claim_type: str = ""                # "fix", "root_cause", "characterization"


# ---------------------------------------------------------------------------
# 1. Claim detection patterns
# ---------------------------------------------------------------------------

_FIX_PATTERNS = [
    re.compile(r"\b(?:fixed|resolved|addressed)\b", re.I),
    re.compile(r"\bnow (?:works|working|behaving|correct(?:ly)?|passing)\b", re.I),
    re.compile(r"\bbug (?:is|has been) (?:fixed|resolved)\b", re.I),
]

_ROOT_CAUSE_PATTERNS = [
    re.compile(r"\b(?:root cause (?:is|was)|caused by|due to)\b", re.I),
    re.compile(r"\bthe (?:issue|problem|bug|error) (?:is|was) (?:that|because)\b", re.I),
]

_CHARACTERIZATION_PATTERNS = [
    re.compile(r"\b(?:generic|stock|custom|broken|misconfigured|unused|outdated|stale)\b", re.I),
]

# Agreement prefix: "you're right" near an artifact/claim = treated as a strong claim
_AGREEMENT_PREFIX_RE = re.compile(r"\b(?:you[' ]?re right|you are right|you are correct)\b", re.I)

# ---------------------------------------------------------------------------
# 2. Artifact token extraction
# ---------------------------------------------------------------------------

_ARTIFACT_TOKEN_RE = re.compile(
    r"""
    # File paths with common extensions
    (?P<path>
        (?:[A-Za-z]:)?                          # optional drive letter
        (?:[A-Za-z0-9_\-./\\])+                 # path chars
        \.(?:py|js|ts|tsx|json|yaml|yml|toml|ini|cfg|md|png|jpg|jpeg|svg|gif|css|html|sh|bat)
    )
    |
    # Hook files specifically
    (?P<hook>
        (?:Stop|Pre|Post|Session)[A-Za-z0-9_]+\.py
    )
    |
    # Config-style references
    (?P<config>
        (?:config|settings|\.env|CLAUDE\.md)\b[A-Za-z0-9_.\-]*
    )
    """,
    re.I | re.VERBOSE,
)


# ---------------------------------------------------------------------------
# 3. Sentence splitting (robust against file paths and URLs)
# ---------------------------------------------------------------------------

def _split_sentences(text: str) -> list[str]:
    """Split text into sentences without breaking on file paths or URLs.

    Strategy: split on '. ' / '! ' / '? ' but NOT when the period is preceded
    by a known file extension or is inside a URL-like token.
    """
    # First, protect periods in file extensions and URLs by replacing them
    # with a placeholder, then split, then restore.
    protected = text

    # Protect file extensions: word.ext (where ext is 2-4 alpha chars followed by
    # non-alpha or end)
    def _protect_ext(m: re.Match) -> str:
        return m.group(0).replace(".", "\x00")

    protected = re.sub(
        r"(?<=[A-Za-z0-9_/\\])\."
        r"(?=(?:py|js|ts|tsx|json|yaml|yml|toml|ini|cfg|md|png|jpg|jpeg|svg|gif|css|html|sh|bat|exe|dll|so)"
        r"(?:\b|$))",
        "\x00",
        protected,
    )

    # Protect URLs
    protected = re.sub(r"(https?://\S+)", lambda m: m.group().replace(".", "\x00"), protected)

    # Protect ellipsis
    protected = protected.replace("...", "\x01\x01\x01")

    # Now split on sentence boundaries
    parts = re.split(r"(?<=[.!?])\s+", protected)

    # Restore
    result = []
    for p in parts:
        p = p.replace("\x00", ".").replace("\x01\x01\x01", "...")
        p = p.strip()
        if p:
            result.append(p)
    return result


# ---------------------------------------------------------------------------
# 4. Meta-conversation / self-referential exclusions
# ---------------------------------------------------------------------------

_META_PATTERNS = re.compile(
    r"""
    \b(?:
        if\s+(?:you|we)\s+(?:want|need|decide)|    # hypothetical
        (?:the\s+)?(?:approach|pattern|strategy)\s+(?:is|would\s+be)|  # discussing approaches
        for\s+example|                              # example context
        in\s+general|                               # general discussion
        typically|usually|often|                     # hedged language
        i\s+(?:would|suggest|recommend)|            # recommendations
        want\s+me\s+to|shall\s+i                    # offering to do
    )\b
    """,
    re.I | re.VERBOSE,
)

_SELF_REF_PATTERNS = re.compile(
    r"""
    \b(?:
        i\s+(?:did|made|said|used|wrote)\s+this\s+because|  # explaining own actions
        my\s+(?:reasoning|thinking|mistake)|                 # self-reflection
        i\s+(?:apologize|was\s+wrong|misread|misunderstood)  # corrections
    )\b
    """,
    re.I | re.VERBOSE,
)


def _is_meta_or_self_ref(sentence: str) -> bool:
    """Return True if sentence is meta-discussion or self-referential."""
    return bool(_META_PATTERNS.search(sentence) or _SELF_REF_PATTERNS.search(sentence))


# ---------------------------------------------------------------------------
# 5. Public API
# ---------------------------------------------------------------------------

def extract_artifact_claims(text: str) -> list[ArtifactClaim]:
    """Extract sentences containing strong claims about artifacts or outcomes.

    Returns only claims that are NOT meta-conversation or self-referential.
    """
    sentences = _split_sentences(text)
    claims: list[ArtifactClaim] = []

    for s in sentences:
        if _is_meta_or_self_ref(s):
            continue

        # Classify claim type
        claim_type = ""
        if any(p.search(s) for p in _FIX_PATTERNS):
            claim_type = "fix"
        elif any(p.search(s) for p in _ROOT_CAUSE_PATTERNS):
            claim_type = "root_cause"
        elif any(p.search(s) for p in _CHARACTERIZATION_PATTERNS):
            claim_type = "characterization"

        # "You're right" + artifact reference = agreement-as-claim
        has_agreement = bool(_AGREEMENT_PREFIX_RE.search(s))
        if not claim_type and has_agreement:
            target = _find_artifact_in_text(s)
            if target:
                # Agreement about a specific artifact without independent claim type
                claim_type = "characterization"
            else:
                continue
        elif not claim_type:
            continue

        # Extract artifact reference
        target = _find_artifact_in_text(s)
        claims.append(ArtifactClaim(text=s, target_artifact=target, claim_type=claim_type))

    return claims


def _find_artifact_in_text(text: str) -> str | None:
    """Extract best-guess artifact reference from text."""
    m = _ARTIFACT_TOKEN_RE.search(text)
    if not m:
        return None
    for name in ("path", "hook", "config"):
        val = m.group(name)
        if val:
            return val
    return None


def find_concrete_observation(full_text: str, claim: ArtifactClaim) -> str | None:
    """Check if the response contains a concrete observation about the claimed artifact.

    Requires BOTH:
    - Mention of the artifact (if specified)
    - Detail tokens: line numbers, function names, specific values, error messages

    For outcome-only claims (no target_artifact), requires at least one
    concrete detail about any artifact.
    """
    sentences = _split_sentences(full_text)
    if not sentences:
        return None

    target = (claim.target_artifact or "").lower()

    # Find the claim sentence index
    claim_idx = None
    for idx, s in enumerate(sentences):
        if claim.text.strip() == s.strip():
            claim_idx = idx
            break

    # Check the claim sentence and neighbors (±2) for concrete observations
    if claim_idx is not None:
        window = range(
            max(0, claim_idx - 2),
            min(len(sentences), claim_idx + 3),
        )
    else:
        # Fallback: check all sentences
        window = range(len(sentences))

    for idx in window:
        s = sentences[idx]
        if _has_concrete_detail(s, target):
            return s

    return None


# Detail tokens that indicate a concrete observation (not hand-waving)
_DETAIL_RE = re.compile(
    r"""
    (?:[A-Za-z_][A-Za-z0-9_]*\s*\()          |  # function call: foo(
    (?:line\s+\d+)                             |  # line 42
    (?:column\s+\d+)                           |  # column 5
    (?:error|exception|traceback|stack\s*trace) |  # error indicators
    (?:returns?\s+(?:True|False|None|\d+|`))   |  # concrete return values
    (?:=\s*["`'][^"`']+["`'])                  |  # assignment with value
    (?:assert\s)                               |  # assertion
    (?:output:\s)                              |  # labeled output
    (?:```\w*)                                 |  # code block
    (?:\d+\s+tests?\s+passed)                  |  # test results: 15 tests passed
    (?:all\s+\d+\s+tests?)                        # all 15 tests
    """,
    re.I | re.VERBOSE,
)


def _has_concrete_detail(sentence: str, target: str) -> bool:
    """Check if sentence has concrete detail, optionally about a specific target."""
    # If target specified, sentence must mention it
    if target and target not in sentence.lower():
        return False
    return bool(_DETAIL_RE.search(sentence))
