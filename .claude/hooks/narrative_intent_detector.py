#!/usr/bin/env python3
from __future__ import annotations

"""
Narrative Intent Detector — Phase 1 (warn-only)
================================================

Detects un-hedged design-intent / author-motivation narratives
that are presented as fact without evidence citations.

This module is called as a second pass AFTER unified_claim_verifier,
which handles code-state claims. This module handles a distinct class:

    "The author included X because users might forget to Y."
    "This was designed to prevent Z."
    "The plugin exists so that W."

These are *rationale claims* — statements about WHY code/config exists.
They require either:
  (a) explicit evidence (file path + line, doc quote, commit ref), OR
  (b) hedging language marking them as speculation.

If neither is present, the detector returns a warning (Phase 1) or
block (Phase 2+) verdict.

Design principles:
- Scoped ONLY to author/design intent, not code-behavior reasoning
- Subject must be an agent (author, designer, plugin, system) or
  artifact (feature, config, matcher, hook) with a purpose/intention verb
- "This function crashes because it mutates state" is code reasoning → skip
- "The author added this because users forget" is intent narrative → check
"""

import re
from typing import Any

from __lib.shared_helpers import is_question, strip_non_claim_lines
from evidence_store import load_tool_events, resolve_session_id

# ── Intent/rationale sentence patterns ──────────────────────────
# These detect sentences where someone explains WHY code/design exists
# by attributing purpose or motivation to an author/system/feature.

INTENT_PATTERNS = (
    # Agent + intention verb: "the author wanted", "they probably intended"
    r"\b(?:the\s+)?(?:author|developer|designer|creator|maintainer|contributor|"
    r"plugin\s+author|original\s+author|team)\s+"
    r"(?:\w+\s+)?(?:wanted|intended|designed|chose|decided|included|added|built|created|"
    r"wrote|introduced|implemented|put)\b",

    # Passive purpose: "was added so that", "was designed to", "was included to"
    r"\b(?:was|were|is|are)\s+(?:added|designed|included|introduced|created|"
    r"built|implemented|written|put\s+there|placed)\s+"
    r"(?:so\s+that|to\s+(?:prevent|ensure|allow|enable|avoid|handle|support|"
    r"make|help|keep|give|provide)|in\s+order\s+to|because|for\s+the\s+purpose)\b",

    # "exists to/for/because": "the matcher exists because", "the hook exists because"
    r"\b(?:this|the|that|it)\s+(?:\w+\s+)?(?:exists?|is\s+there|is\s+present|is\s+included)\s+"
    r"(?:to\s+|for\s+|because\s+|so\s+that\s+|in\s+order\s+to\s+)",

    # "the goal/purpose/intent of X is": design rationale framing
    r"\b(?:the\s+)?(?:goal|purpose|intent|intention|motivation|reason|rationale|"
    r"point)\s+(?:of\s+|for\s+|behind\s+)(?:this|the|that)\b",

    # "this is for/meant to": artifact purpose attribution
    r"\b(?:this|it)\s+(?:is\s+(?:meant|intended|designed|supposed)|was\s+(?:meant|"
    r"intended|designed|supposed))\s+to\b",

    # "they wanted/needed": anonymous agent intent
    r"\b(?:they|someone)\s+(?:wanted|needed|decided|chose|preferred)\s+(?:to|this|that)\b",
)
INTENT_RE = re.compile("|".join(f"(?:{p})" for p in INTENT_PATTERNS), re.IGNORECASE)


# ── Hedging markers ─────────────────────────────────────────────
# If a sentence contains one of these, the speaker is marking it
# as uncertain/speculative, which is acceptable.

HEDGE_PATTERNS = (
    r"\bprobably\b",
    r"\blikely\b",
    r"\bunlikely\b",
    r"\bperhaps\b",
    r"\bpossibly\b",
    r"\bplausib(?:le|ly)\b",
    r"\bit\s+seems?\s+(?:like|that)\b",
    r"\b(?:my|a)\s+(?:speculation|hypothesis|guess|reading|interpretation)\b",
    r"\bi\s+(?:suspect|believe|think|assume|imagine|speculate)\b",
    r"\bone\s+(?:plausible|possible)\s+(?:reason|explanation)\b",
    r"\b(?:might|may|could)\s+(?:be|have\s+been)\b",
    r"\bnot\s+(?:certain|sure)\b",
    r"\bunclear\b",
    r"\bapparently\b",
    r"\bseemingly\b",
    r"\bmy\s+best\s+guess\b",
    r"\bI'm\s+not\s+(?:certain|sure)\b",
    r"\bI\s+don'?t\s+(?:know|have\s+evidence)\b",
)
HEDGE_RE = re.compile("|".join(f"(?:{p})" for p in HEDGE_PATTERNS), re.IGNORECASE)


# ── Evidence citation patterns ──────────────────────────────────
# If the sentence (or its immediate predecessor) cites a concrete source,
# the rationale claim is backed by evidence.

CITATION_PATTERNS = (
    # File path references: "in file X, line Y" or "from X.py"
    r"(?:in|from|at|see)\s+(?:file\s+)?(?:[A-Za-z]:)?[\\/]?[\w./\\-]+\.(?:py|js|ts|md|json|yaml|yml|toml)",
    # Line references: "line 42", "lines 10-20"
    r"\blines?\s+\d+",
    # Doc/section references: "the README states", "according to the docs"
    r"\b(?:the\s+)?(?:README|CHANGELOG|docs?|documentation|comments?|docstring|"
    r"commit\s+message|issue\s+#?\d+|PR\s+#?\d+)\s+(?:says?|states?|mentions?|"
    r"explains?|notes?|describes?|indicates?|shows?)\b",
    # "according to X"
    r"\baccording\s+to\b",
    # Explicit quote markers
    r'["\u201c].{5,}["\u201d]',
    # Commit hash references
    r"\b(?:commit|sha)\s+[a-f0-9]{7,}\b",
)
CITATION_RE = re.compile("|".join(f"(?:{p})" for p in CITATION_PATTERNS), re.IGNORECASE)


# ── Code-behavior reasoning exclusion ───────────────────────────
# These indicate the sentence is explaining code BEHAVIOR, not design INTENT.
# "This crashes because it mutates state" → code reasoning, not intent.

CODE_BEHAVIOR_PATTERNS = (
    r"\b(?:crashes?|throws?|raises?|returns?|outputs?|prints?|logs?|calls?|"
    r"invokes?|executes?|evaluates?|computes?|calculates?)\s+(?:because|when|if|since)\b",
    r"\b(?:the\s+)?(?:function|method|class|loop|condition|variable|parameter)\s+"
    r"(?:crashes?|throws?|raises?|returns?|fails?|succeeds?)\b",
    r"\b(?:because|since)\s+(?:the\s+)?(?:variable|parameter|argument|value|type|"
    r"state|buffer|pointer|reference|index)\b",
)
CODE_BEHAVIOR_RE = re.compile("|".join(f"(?:{p})" for p in CODE_BEHAVIOR_PATTERNS), re.IGNORECASE)


# ── Path extraction for evidence matching ───────────────────────

PATH_RE = re.compile(
    r"(?:[A-Za-z]:)?[\\/][\w./\\-]+|[\w./\\-]+\.(?:py|js|ts|md|json|yaml|yml|toml|ini|cfg|txt)"
)


def detect_intent_narratives(response_text: str) -> list[str]:
    """Find sentences that make rationale/intent claims about code/design."""
    if not response_text.strip():
        return []

    cleaned = strip_non_claim_lines(response_text)
    narratives: list[str] = []

    for line in cleaned.splitlines():
        text = line.strip()
        if not text or len(text) < 20:
            continue
        if is_question(text):
            continue
        # Must match an intent pattern
        if not INTENT_RE.search(text):
            continue
        # Exclude pure code-behavior reasoning
        if CODE_BEHAVIOR_RE.search(text):
            continue
        narratives.append(text)

    return narratives[:20]


def _sentence_has_hedge(sentence: str) -> bool:
    """Check if a sentence contains hedging language."""
    return bool(HEDGE_RE.search(sentence))


def _sentence_has_citation(sentence: str) -> bool:
    """Check if a sentence contains an explicit evidence citation."""
    return bool(CITATION_RE.search(sentence))


def _citation_backed_by_evidence(sentence: str, evidence_entities: set[str]) -> bool:
    """Check if cited paths in the sentence were actually read (in evidence store)."""
    cited_paths = set()
    for m in PATH_RE.finditer(sentence):
        raw = m.group(0).strip().lower().replace("\\", "/")
        cited_paths.add(raw)
        # Also add basename for fuzzy matching
        if "/" in raw:
            cited_paths.add(raw.split("/")[-1])

    if not cited_paths:
        # Citation is non-path (e.g., "according to the README") — accept if
        # there's any evidence at all (we can't match abstract citations to
        # specific tool events without more context)
        return bool(evidence_entities)

    # Check if any cited path overlaps with evidence entities
    evidence_lower = {e.lower().replace("\\", "/") for e in evidence_entities}
    evidence_basenames = set()
    for e in evidence_lower:
        if "/" in e:
            evidence_basenames.add(e.split("/")[-1])
        else:
            evidence_basenames.add(e)

    for cited in cited_paths:
        if cited in evidence_lower:
            return True
        basename = cited.split("/")[-1] if "/" in cited else cited
        if basename in evidence_basenames:
            return True

    return False


def _build_evidence_entities(events: list[dict[str, Any]]) -> set[str]:
    """Extract path/identifier entities from tool events."""
    entities: set[str] = set()
    for event in events:
        for field in ("command", "cwd", "output"):
            value = str(event.get(field, "")).strip()
            for m in PATH_RE.finditer(value):
                entities.add(m.group(0).strip().lower().replace("\\", "/"))
    return entities


def evaluate_narratives(
    response_text: str,
    session_id: str = "",
    tool_sequence: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Evaluate response for un-hedged, un-evidenced intent/rationale narratives.

    Returns:
        dict with keys:
          - decision: "allow" | "warn"  (Phase 1 is warn-only)
          - reason: str
          - narratives: list of detected narrative sentences
          - unhedged: list of sentences that are neither hedged nor cited
          - systemMessage: str (only if decision == "warn")
    """
    narratives = detect_intent_narratives(response_text)

    if not narratives:
        return {
            "decision": "allow",
            "reason": "NO_INTENT_NARRATIVES",
            "narratives": [],
            "unhedged": [],
        }

    # Build evidence from tool events
    if tool_sequence is not None:
        events = []
        for tool in tool_sequence:
            events.append({
                "name": tool.get("name") or tool.get("tool_name", ""),
                "command": tool.get("command", ""),
                "output": tool.get("output", ""),
                "cwd": "",
            })
    else:
        sid = resolve_session_id(session_id)
        events = load_tool_events(sid, limit=500) if sid else []

    evidence_entities = _build_evidence_entities(events)

    unhedged: list[str] = []

    for sentence in narratives:
        # Check 1: Does the sentence hedge?
        if _sentence_has_hedge(sentence):
            continue  # Speculation is labeled → OK

        # Check 2: Does the sentence cite evidence?
        if _sentence_has_citation(sentence):
            # Further check: was the cited source actually read?
            if _citation_backed_by_evidence(sentence, evidence_entities):
                continue  # Evidence-backed → OK
            # Citation present but source not in evidence store
            # Still allow in Phase 1 — citation shows good intent

        # Check 3: Are there ANY evidence entities that overlap with
        # entities mentioned in the sentence? (Loose match — the speaker
        # at least investigated the area they're explaining)
        sentence_paths = set()
        for m in PATH_RE.finditer(sentence):
            sentence_paths.add(m.group(0).strip().lower().replace("\\", "/"))

        if sentence_paths:
            evidence_lower = {e.lower().replace("\\", "/") for e in evidence_entities}
            evidence_basenames = {e.split("/")[-1] for e in evidence_lower if "/" in e}
            sentence_basenames = {p.split("/")[-1] for p in sentence_paths if "/" in p}
            if sentence_paths & evidence_lower or sentence_basenames & evidence_basenames:
                continue  # Investigated the relevant files → OK

        # No hedge, no citation, no evidence overlap → flag it
        unhedged.append(sentence)

    if not unhedged:
        return {
            "decision": "allow",
            "reason": "NARRATIVES_HEDGED_OR_CITED",
            "narratives": narratives,
            "unhedged": [],
        }

    # Phase 1: warn (systemMessage), not block
    truncated = [s[:200] for s in unhedged[:3]]
    return {
        "decision": "warn",
        "reason": "UNHEDGED_INTENT_NARRATIVE",
        "narratives": narratives,
        "unhedged": unhedged,
        "systemMessage": (
            "Your response contains design-intent or author-motivation "
            "explanations that are neither backed by evidence nor marked "
            "as speculation. Re-examine these statements and either cite "
            "a source (file, doc, comment, commit) or add hedging language "
            "(\"likely\", \"probably\", \"I believe\", \"a plausible reason is\"):\n\n"
            + "\n".join(f"  - {s}" for s in truncated)
        ),
    }
