#!/usr/bin/env python3
"""
Stop_self_reflection_gate.py - Self-Reflection Quality Gate

Advisory-only. Detects three categories of potentially low-quality responses:
  1. Unsupported definitive claims (only in prose-only responses with no evidence)
  2. Within-paragraph contradictions about system facts (high-signal pairs only)
  3. Structured promises that deliver exactly 1 item when multiple were implied

Never blocks. Prints to stdout only. Exits 0 always.

Design principle: never trigger on a word being merely present.
  - Factual claims: gated behind full-response evidence check first
  - Contradictions: paragraph-scoped + comparison/temporal context exemption
  - Promises: only flag exactly-1-item (0=cutoff, ≥2=fine)

Noise reduction (2026-05-05):
  - Deduplicates near-identical contradiction text
  - Skips contradictions from known documentation headings
  - Caps user-visible contradictions at 5 (full details logged)
"""

from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import os
import re
import sys
from typing import Any

SELF_REFLECTION_ENABLED = os.environ.get("SELF_REFLECTION_ENABLED", "true").lower() == "true"

# ── 1. Response-level evidence gate ──────────────────────────────────────────

def _response_has_evidence(text: str) -> bool:
    """True if the response contains hard evidence anchors.

    A response with code fences, file-path references, or explicit verification
    markers is evidence-grounded and exempt from factual-claim checks.
    """
    if "```" in text:
        return True
    # ≥2 file/path refs → response is reading actual artifacts
    path_refs = len(re.findall(
        r'(?:[A-Z]:[/\\]|\.claude/|packages/|\.git/|\w+\.py:\d+|\w+\.json:\d+)',
        text,
    ))
    if path_refs >= 2:
        return True
    if re.search(
        r'\b(?:STATUS:\s*(?:TESTED|VERIFIED)|Verified:|confirmed\s+via|tool\s+output)\b',
        text,
        re.I,
    ):
        return True
    return False

# ── 2. Unsupported definitive claim detection ─────────────────────────────────

# Sentence makes a definitive assertion about a named system artifact
_DEFINITIVE_CLAIM = re.compile(
    r'\b(?:the\s+)?(?:hook|file|function|module|system|router|script)\s+'
    r'(?:\w+\s+)?'
    r'(?:is|does|does\s+not|will|never|always|must|cannot|works?|fails?|runs?|fires?)\b',
    re.IGNORECASE,
)

# Sentence is already hedged — exempt from flagging
_QUALIFIER = re.compile(
    r'\b(?:might|may|could|seems?|appears?|likely|probably|possibly|'
    r'I\s+think|I\s+believe|suspect|unclear|unverified|inferred|unconfirmed|'
    r'sufficient|appropriate|adequate|acceptable)\b',
    re.IGNORECASE,
)

def _extract_unsupported_claims(response: str, has_evidence: bool = False) -> list[dict[str, Any]]:
    """Find definitive unhedged claims in prose-only (no-evidence) responses."""
    if has_evidence:
        return []  # Evidence-grounded — skip entirely

    claims: list[dict[str, Any]] = []
    for sentence in re.split(r'(?<=[.!?])\s+', response):
        sentence = sentence.strip()
        if len(sentence) < 20:
            continue
        if _QUALIFIER.search(sentence):
            continue  # Already hedged
        if _DEFINITIVE_CLAIM.search(sentence):
            claims.append({"type": "unsupported_claim", "text": sentence[:120]})

    return claims[:3]  # Cap — prevent noise flooding

# ── 3. Within-paragraph contradiction detection ───────────────────────────────

# High-signal pairs: each asserts a fact about system behavior and its negation.
# Deliberately narrow — generic word pairs (never/always) excluded.
_CONTRADICTION_PAIRS: list[tuple[re.Pattern[str], re.Pattern[str]]] = [
    # Existence
    (re.compile(r'\bexists?\b', re.I),
     re.compile(r'\bdoes\s+not\s+exist\b|\bnot\s+found\b|\bmissing\b', re.I)),
    # Registration
    (re.compile(r'\bregistered\b', re.I),
     re.compile(r'\bnot\s+registered\b|\bunregistered\b|\borphaned\b', re.I)),
    # Execution
    (re.compile(r'\b(?:runs?|fires?|executes?|active)\b', re.I),
     re.compile(r'\b(?:does\s+not\s+run|never\s+fires?|never\s+runs?|inactive|disabled)\b', re.I)),
    # Correctness
    (re.compile(r'\bworks?\b', re.I),
     re.compile(r'\b(?:broken|fails?|does\s+not\s+work|doesn\'t\s+work)\b', re.I)),
    # Pass/block
    (re.compile(r'\bblocks?\b', re.I),
     re.compile(r'\b(?:allows?|never\s+blocks?|pass(?:es)?\s+through)\b', re.I)),
]

# Paragraph contexts where opposing terms are intentional (not errors)
_EXEMPT_CONTEXT = re.compile(
    r'\b(?:previously|used\s+to|before|was\s+changed|now\s+(?:it|they|we)|'
    r'vs\.?|versus|compared\s+to|on\s+the\s+other\s+hand|alternatively|'
    r'option\s+[ab12]|if\s+\w+\s+(?:is|are|was)|unless|whereas|'
    r'instead\s+of|rather\s+than)\b',
    re.IGNORECASE,
)

def _find_contradictions(response: str) -> list[dict[str, Any]]:
    """Find genuine within-paragraph contradictions about system facts."""
    found: list[dict[str, Any]] = []
    for para in response.split('\n\n'):
        para = para.strip()
        if len(para) < 40:
            continue
        if _EXEMPT_CONTEXT.search(para):
            continue  # Comparison / temporal / conditional — intentional
        for pos_pat, neg_pat in _CONTRADICTION_PAIRS:
            pm = re.search(pos_pat, para, re.IGNORECASE)
            nm = re.search(neg_pat, para, re.IGNORECASE)
            if pm and nm:
                # Skip if pos match is contained within neg match span
                # (e.g. "exist" inside "does not exist")
                if nm.start() <= pm.start() <= nm.end():
                    continue
                if pm.start() <= nm.start() <= pm.end():
                    continue
                found.append({
                    "type": "contradiction",
                    "text": f"Same paragraph: '{pm.group()}' and '{nm.group()}'",
                })
                break  # One finding per paragraph
    return found

# ── 4. Incomplete promise detection ──────────────────────────────────────────

_PROMISE = re.compile(
    # "steps:" already contains the colon so is a separate alternative
    r'(?:here\s+are|the\s+following|these\s+are|I\s+will\s+(?:do|fix|address|handle))\s*:'
    r'|steps?\s*:',
    re.IGNORECASE,
)
_LIST_ITEM = re.compile(r'^\s*[-*\d+\.]\s+\S', re.MULTILINE)

def _find_incomplete_promises(response: str) -> list[dict[str, Any]]:
    """Flag promises followed by exactly 1 item (0=cutoff, ≥2=delivered)."""
    incomplete: list[dict[str, Any]] = []
    for match in _PROMISE.finditer(response):
        window = response[match.end(): match.end() + 400]
        if len(_LIST_ITEM.findall(window)) == 1:
            incomplete.append({
                "type": "incomplete",
                "text": f"'{match.group().strip()}' followed by only 1 item",
            })
    return incomplete

# ── 5. Noise reduction ─────────────────────────────────────────────────────────

# Documentation headings whose content frequently produces spurious contradictions.
# Entries from these headings (GOOD/BAD examples, code blocks, etc.) should not
# generate contradiction findings when they appear in the model's own response text.
_SKIP_HEADINGS = {
    "UNCERTAINTY EXPRESSION",
    "SPECIFIC LIMITATION + NEXT STEP",
    "HOW TO EXPRESS UNCERTAINTY",
    "GOOD:",
    "BAD:",
    "EXAMPLE:",
}
_MAX_VISIBLE_CONTRADICTIONS = 5

def _normalize(text: str) -> str:
    """Normalize text for deduplication: lowercase, whitespace-collapse."""
    return re.sub(r'\s+', ' ', text.lower().strip())

def _is_from_doc_block(text: str, heading: str) -> bool:
    """Return True if text is near a documentation heading."""
    if heading.upper() in text.upper():
        return True
    # Heuristic: if the normalized text starts with the same words as the heading
    heading_words = heading.lower().split()
    text_words = text.lower().split()
    if len(heading_words) >= 2 and len(text_words) >= 2:
        if text_words[:2] == heading_words[:2]:
            return True
    return False

def _deduplicate_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate near-identical findings, skip doc-block contradictions, cap."""
    seen_normalized: set[str] = set()
    doc_skip_count = 0
    deduped: list[dict[str, Any]] = []

    for f in findings:
        if f["type"] != "contradiction":
            deduped.append(f)
            continue

        norm = _normalize(f["text"])

        # Skip if normalized text already seen
        if norm in seen_normalized:
            continue

        # Skip if text appears to be from a documentation example block
        if any(_is_from_doc_block(f["text"], h) for h in _SKIP_HEADINGS):
            doc_skip_count += 1
            continue

        seen_normalized.add(norm)
        deduped.append(f)

    # Cap contradictions at _MAX_VISIBLE_CONTRADICTIONS
    contradictions = [f for f in deduped if f["type"] == "contradiction"]
    non_contradictions = [f for f in deduped if f["type"] != "contradiction"]

    if len(contradictions) > _MAX_VISIBLE_CONTRADICTIONS:
        excess = len(contradictions) - _MAX_VISIBLE_CONTRADICTIONS
        contradictions = contradictions[:_MAX_VISIBLE_CONTRADICTIONS]

    return non_contradictions + contradictions

# ── Entry point ───────────────────────────────────────────────────────────────

def run(data: dict) -> dict | None:
    if not SELF_REFLECTION_ENABLED:
        return {"decision": "approve"}

    response = data.get("response", "")
    if not response or len(response) < 20:
        return {"decision": "approve"}

    has_evidence = _response_has_evidence(response)
    # Contradiction detection is only meaningful in prose-only responses
    # — responses with code fences, file refs, or verification markers
    # are evidence-grounded and contradictions don't apply.
    contradictions = [] if has_evidence else _find_contradictions(response)
    # Skip per-sentence unsupported-claim check when a contradiction already
    # covers those sentences — avoids double-reporting the same problem.
    claims = [] if contradictions else _extract_unsupported_claims(response, has_evidence)
    incomplete = _find_incomplete_promises(response)

    findings: list[dict[str, Any]] = claims + contradictions + incomplete

    # Noise reduction: dedupe, skip doc-block contradictions, cap visible list
    findings = _deduplicate_findings(findings)

    if not findings:
        return {"decision": "approve"}

    visible = findings[:10]  # Keep full list for logging, show first 10 to user
    lines = [f"Self-reflection ({len(findings)} finding(s)):"]
    for f in visible:
        lines.append(f"  [{f['type']}] {f['text'][:100]}")
    lines.append("Consider adding evidence or hedging unverified claims.")
    _logger.warning("\n".join(lines))

    counts = {
        t: sum(1 for f in findings if f["type"] == t)
        for t in ("unsupported_claim", "contradiction", "incomplete")
    }
    return {
        "decision": "approve",
        "reason": (
            f"advisory: {counts['unsupported_claim']} unsupported, "
            f"{counts['contradiction']} contradictions, "
            f"{counts['incomplete']} incomplete"
        ),
    }

if __name__ == "__main__":
    import json
    try:
        result = run(json.loads(sys.stdin.read()))
        print(json.dumps(result, indent=2))
    except json.JSONDecodeError:
        print("{}")