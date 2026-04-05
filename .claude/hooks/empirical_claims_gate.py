#!/usr/bin/env python3
"""
Empirical Claims Gate — Stop hook

Catches assertions about implementation status that are backed only by document
metadata (ADR status fields, plan status, ticket state) instead of code-level
evidence (file reads, grep results, function definitions).

Motivating incident: "lazy again.txt" — MiniMax reported an ADR as
"NOT fully implemented" because its Status field said "Proposed", without
ever reading the actual code files.

Document metadata is NOT code evidence:
  - "Status: Proposed" → does not mean code doesn't exist
  - "Status: Accepted" → does not mean code does exist
  - "Plan: pending" → does not prove nothing is implemented

Required evidence for implementation claims:
  - A file path with code content referenced
  - A Grep/Read tool result showing code
  - An explicit line-number citation in source code

Known architectural limitation (RISK-004):
  CODE_EVIDENCE_PATTERNS matches text in the response, not actual tool
  execution. A response containing "orchestrator.py:243" is exempted even
  if no Grep/Read tool actually produced that citation. Verifying actual
  tool execution would require Stop_router to pass tool_events to the gate.
"""

from __future__ import annotations

import re

# ── Document metadata proxy patterns ────────────────────────────────────────
# Detects when the response cites a document status field as the basis for an
# implementation claim.
DOC_STATUS_PATTERNS = [
    # ADR / architecture decision record status (supports straight + curly quotes)
    r"Status[:\s]+['\"\u201c\u201d]?(?:Proposed|Draft|Pending|Superseded|Rejected)['\"\u201c\u201d]?"
    r".{0,120}(?:not|hasn.t|hasn't|un)\s*(?:been\s+)?implemented",

    r"(?:not|hasn.t|hasn't|un)\s*(?:been\s+)?implemented"
    r".{0,120}Status[:\s]+['\"\u201c\u201d]?(?:Proposed|Draft|Pending)['\"\u201c\u201d]?",

    # "Status is Proposed, meaning..." pattern (exact phrasing from the incident)
    r"Status\s+is\s+['\"\u201c\u201d]?(?:Proposed|Draft|Pending|Rejected)['\"\u201c\u201d]?"
    r".{0,80}(?:meaning|which\s+means|indicating|so\s+it)",

    # Status + incomplete/unfinished (RISK-005: separate variant not covered by "not implemented")
    r"Status[:\s]+['\"\u201c\u201d]?(?:Proposed|Draft|Pending)['\"\u201c\u201d]?"
    r".{0,80}(?:incomplete|unfinished)",

    # Plan / ticket status proxy
    r"(?:task|plan|ticket|story|issue)\s+(?:is\s+)?(?:pending|open|backlog)"
    r".{0,80}(?:not|hasn.t|un)\s*(?:been\s+)?implemented",

    # Uncommitted / unfinalised document framing
    r"(?:uncommitted|unfinalised|unfinished|incomplete)\s+architectural\s+decision",
]

# ── Verification language patterns ─────────────────────────────────────────────
# Detects when response uses verification language without providing actual evidence.
# "I'll verify", "empirical evidence", "verified against" = claim without proof.
VERIFICATION_LANGUAGE_PATTERNS = [
    r"\bverify\b.{0,40}(?:against|by|with)\b",
    r"\bempirical\s+(?:evidence|proof|verification)\b",
    r"\bverified\b.{0,60}?(?:but|without|not)\b",
    r"\bverify\b.{0,40}?(?:but|without|not)\b",
    r"\bTier\s*[134]\b.{0,80}?(?:evidence|sufficient|inadequate)\b",
    r"\bnot\s+Tier\s*4\b",
    r"\bcode\s+evidence\b",
    r"\bRead/Grep\b",
    r"\bfile:\d+\b",
    r"\b(Tier\s+1|[Tt]ier\s+[1234]).{0,60}required\b",
    r"\bevidence\s+hierarchy\b",
]

# ── Implementation claim patterns ────────────────────────────────────────────
IMPL_CLAIM_PATTERNS = [
    r"\bNOT\s+(?:fully\s+)?implemented\b",
    r"\bnot\s+yet\s+implemented\b",
    r"\bfully\s+implemented\b",
    r"\bcompletely\s+implemented\b",
    r"\balready\s+implemented\b",
    r"\bis\s+(?:not\s+)?implemented\b",
    r"\bhas\s+(?:not\s+been|been)\s+implemented\b",
    r"\bimplementation\s+(?:is\s+)?(?:complete|incomplete|done|missing)\b",
    r"\bcode\s+(?:exists?|doesn.t\s+exist|is\s+(?:not\s+)?(?:present|there))\b",
]

# ── Code-level evidence markers ──────────────────────────────────────────────
# If ANY of these appear, the claim is backed by code evidence and we allow it.
CODE_EVIDENCE_PATTERNS = [
    r"[\w/_-]+\.(?:[a-z]{1,10})(?::\d+)?",  # file.py:N (extensible)
    r"\bRead\s+\d+\s+file",           # "Read 2 files"
    r"(?i)\bSearched\s+for\b",         # Grep tool marker (case-insensitive)
    r"\bline\s+\d{1,5}\b",            # "line 243"
    r"\bat\s+\w[\w/_-]*\.(?:py|ts|js|go|rs):\d+",  # at path/file.py:N
    r"(?:grep|glob)\s+[\w/\"']",      # grep/glob invocation with argument
    r"\bimport\s+\w",                 # code snippet showing import
    r"\bdef\s+\w",                    # Python def
    r"\bfunction\s+\w",               # JS/TS function
    r"\bclass\s+\w",                  # class definition
    r"Searched\s+\d+\s+pattern",      # Grep results summary
]

_DOC_STATUS = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in DOC_STATUS_PATTERNS]
_IMPL_CLAIM = [re.compile(p, re.IGNORECASE) for p in IMPL_CLAIM_PATTERNS]
_CODE_EVIDENCE = [re.compile(p, re.IGNORECASE) for p in CODE_EVIDENCE_PATTERNS]
_VERIFICATION_LANG = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in VERIFICATION_LANGUAGE_PATTERNS]


def _has_doc_status_proxy(text: str) -> bool:
    return any(p.search(text) for p in _DOC_STATUS)


def _has_impl_claim(text: str) -> bool:
    return any(p.search(text) for p in _IMPL_CLAIM)


def _has_code_evidence(text: str) -> bool:
    return any(p.search(text) for p in _CODE_EVIDENCE)


def _has_verification_language(text: str) -> bool:
    return any(p.search(text) for p in _VERIFICATION_LANG)


def _has_verif_near_claim(text: str) -> bool:
    """
    Check if verification language and claim language appear within
    WINDOW chars of each other — indicating an unverified claim rather
    than a discussion ABOUT the concepts.
    """
    # 200 chars: natural language with long intervening clauses between
    # verification language and implementation claim. Chosen to capture
    # "I will verify [explanation] X is implemented" patterns.
    WINDOW = 200
    for vp in _VERIFICATION_LANG:
        vmatch = vp.search(text)
        if not vmatch:
            continue
        v_start, v_end = vmatch.start(), vmatch.end()
        window_start = max(0, v_start - WINDOW)
        window_end = min(len(text), v_end + WINDOW)
        window = text[window_start:window_end]
        if _has_impl_claim(window):
            return True
    return False


def check_empirical_claims(response_text: str) -> dict | None:
    """
    Return a violation dict if the response uses document metadata as
    implementation evidence, or verification language without actual code evidence,
    or None if the response is clean.
    """
    if not response_text or not response_text.strip():
        return None

    has_proxy = _has_doc_status_proxy(response_text)
    has_claim = _has_impl_claim(response_text)
    has_verif_near = _has_verif_near_claim(response_text)
    has_code = _has_code_evidence(response_text)

    # Violation 1: implementation claim AND document status proxy, no code evidence
    # requires BOTH claim AND doc-status patterns (not just any claim)
    if has_proxy and has_claim and not has_code:
        return {
                "violation": "DOC-PROXY: Implementation claim + document metadata (no code)",
                "suggestion": (
                    "Document status fields (ADR 'Status: Proposed', plan 'pending', "
                    "ticket 'open') are NOT code evidence. "
                    "Verify by reading the actual source files with Grep or Read tools "
                    "before claiming something is or is not implemented."
                ),
            }

    # Violation 2: verification language near claim language, without code evidence
    if has_verif_near and not has_code:
        return {
            "violation": "VERIFICATION-LANGUAGE: Claim of verification without code evidence",
            "suggestion": (
                "Your response mentions verification, evidence tiers, or empirical proof "
                "but provides no actual code evidence (no file:line citations, Read/Grep output). "
                "Show the actual tool output (Read file, Grep results) in this same response "
                "to back your claim, or restate the claim as a question without presenting it as fact."
            ),
        }
    return None


def run(data: dict) -> dict | None:
    """In-process validator protocol for Stop_router."""
    response_text = str(
        data.get("assistant_response")
        or data.get("response")
        or ""
    )

    result = check_empirical_claims(response_text)
    if not result:
        return None

    reason_lines = [
        "EMPIRICAL CLAIMS GATE: Document Metadata Proxy Detected",
        "",
        f"Violation: {result['violation']}",
        "",
        f"Fix: {result['suggestion']}",
        "",
        "Evidence hierarchy for implementation claims:",
        "  Tier 1 (required): Read/Grep output showing code at file:line",
        "  Tier 4 (insufficient): ADR status, plan state, ticket status",
    ]
    return {
        "block": True,
        "reason": "\n".join(reason_lines),
        "blocking_hook": "empirical_claims_gate.py",
    }


# ── Self-test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # SHOULD detect (doc-proxy violations — requires BOTH doc-status AND claim)
    incident = (
        'ADR-20260403-gemma-vision-provider.md — NOT fully implemented. '
        'Status is "Proposed" (not Accepted), meaning it\'s an uncommitted '
        'architectural decision.'
    )
    assert check_empirical_claims(incident) is not None, "Incident replay should be caught"

    adr_status = 'Status: Proposed not implemented'
    assert check_empirical_claims(adr_status) is not None, "ADR status proxy should be caught"

    plan_pending = "plan pending not implemented"
    assert check_empirical_claims(plan_pending) is not None, "Pending task proxy should be caught"

    # SHOULD pass (has code evidence)
    with_grep = (
        "Searched for 'select_provider' — found at orchestrator.py:243. "
        "The provider IS implemented."
    )
    assert check_empirical_claims(with_grep) is None, "Grep evidence should exempt"

    with_read = (
        "Read 2 files: lm_studio_provider.py exists. "
        "LocalModelProvider is fully implemented."
    )
    assert check_empirical_claims(with_read) is None, "Read evidence should exempt"

    with_file_line = (
        "local_model is wired into select_provider() at orchestrator.py:243. "
        "The feature is implemented."
    )
    assert check_empirical_claims(with_file_line) is None, "file:line citation should exempt"

    # SHOULD pass (no impl claim, just description)
    no_claim = "The ADR has status Proposed and needs review."
    assert check_empirical_claims(no_claim) is None, "Doc status without impl claim should pass"

    empty = ""
    assert check_empirical_claims(empty) is None, "Empty response should pass"

    # SHOULD pass (verification language without claim nearby — discussion, not assertion)
    verif_no_claim = (
        "The VERIFICATION-LANGUAGE trigger fires when verify appears "
        "without a nearby implementation assertion."
    )
    assert check_empirical_claims(verif_no_claim) is None, \
        "Verification terms without nearby claim should pass"

    discussion = (
        "Patterns involving evidence tiers and verification claims "
        "should not trigger when no actual assertion is made."
    )
    assert check_empirical_claims(discussion) is None, \
        "Discussion of evidence concepts without assertion should not trigger"

    # SHOULD detect (verification language WITH claim nearby — actual assertion)
    verif_near_impl = (
        "X is implemented — verify against actual code."
    )
    assert check_empirical_claims(verif_near_impl) is not None, \
        "Verification near implementation claim without evidence should be caught"

    verif_near_not_impl = (
        "X is not implemented — we need Tier 1 evidence."
    )
    assert check_empirical_claims(verif_near_not_impl) is not None, \
        "Verification near non-implementation claim should be caught"

    # SHOULD pass (verification language WITH code evidence)
    verif_with_code = (
        "Searched for 'empirical_claims_gate' — found at hooks/empirical_claims_gate.py:54. "
        "The verification language patterns ARE implemented."
    )
    assert check_empirical_claims(verif_with_code) is None, \
        "Verification language with code evidence should exempt"

    print("✅ All empirical_claims_gate self-tests passed")
