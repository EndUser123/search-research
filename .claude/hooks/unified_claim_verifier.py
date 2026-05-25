#!/usr/bin/env python3
from __future__ import annotations

"""
Unified claim verifier.

Single source of truth for Stop-time claim verification:
- Strategy A: Detect state/existence/equivalence claims, match entities against session evidence
- Strategy B: Detect negative external-resource claims, verify fetch/search tool was called (turn-scoped)
- Strategy C: Detect action claims ("I grepped/fetched/ran"), verify implied tool was called (turn-scoped)

Principle enforced: "Never assert the result of an action you didn't take."
"""

import json
import os
import re
import sys
from typing import Any

from __lib.shared_helpers import is_question, strip_non_claim_lines
from evidence_scope import (
    SCOPE_SESSION_FRESH_MUTATION_SAFE,
    SCOPE_TURN_STRICT,
    load_scoped_tool_events,
)
from evidence_store import resolve_session_id

OBSERVATION_TOOLS = frozenset({"Read", "Bash", "Grep", "Glob", "Search", "WebFetch"})
STATE_CHANGING_TOOLS = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit", "Task"})

CLAIM_PATTERNS = (
    r"\b(?:file|module|class|function|method)\s+(?:is|are|was|were|contains|returns|raises|exists)\b",
    r"\b(?:file|module|class|function|method)\b.{0,80}\b(?:exists|missing|found|not found)\b",
    # Generic absence/non-existence patterns
    r"\b(?:does|do)\s+not\s+exist\b",
    r"\b(?:doesn't|don't)\s+exist\b",
    r"\b(?:not found|missing|absent)\b",
    # "not implemented / not configured / not integrated / not enabled"
    r"\bnot\s+(?:yet\s+)?(?:implemented|configured|integrated|added|enabled|set\s+up)\b",
    # "don't have / doesn't have / haven't / hasn't" — "we don't have API keys"
    r"\b(?:don't|doesn't|didn't|won't|haven't|hasn't)\s+have\b",
    # "no [tech noun]" — "No skill integration", "No Claude Code Skill", "No API key handling"
    r"\bno\b.{0,60}\b(?:skill|integration|support|implementation|api\s*key|hook|config(?:uration)?|handling)\b",
    r"\b(?:tests?|pytest)\s+(?:pass|passed|passing|fail|failed|failing|show|shows)\b",
    r"\b(?:is|are|was|were|has been|have been)\s+(?:fixed|resolved|working|correct|verified|confirmed)\b",
    r"\b(?:the\s+)?(?:bug|issue|problem|error)\s+(?:is|was|has been)\s+(?:fixed|resolved|corrected)\b",
    r"\b(?:verified|confirmed)\s+(?:that\s+)?(?:the\s+)?(?:fix|change|solution|behavior)\b",
    r"\b(?:there\s+(?:is|are)|found|identified|discovered)\s+\d+\b",
    # Assertion verbs that indicate claims about state changes
    r"\b(?:is|are|was|were|has been|have been)\s+(?:deleted|removed|added|created|modified|updated|changed)\b",
    # "I found that" pattern - indicates discovery claim
    r"\b(?:i found|found that|i discovered|i located|i identified)\b",
    # Direct state change claims without auxiliary verb
    r"\b(?:was deleted|was removed|was added|was created|was modified|was updated|was changed)\b",
    # Equivalence/alias claims between technical identifiers (e.g. /arch == architectural-validator)
    r"(?:`[^`\n]{2,}`|/?[A-Za-z][A-Za-z0-9]*(?:[._/-][A-Za-z0-9]+)*)\s+"
    r"(?:"
    r"equals?|equal to|equivalent to|same as|same package as|packaged as|known as|called|corresponds to|maps to|mapped to|aka|"
    r"(?:is|are|was|were)(?:\s+(?:(?:an?\s+)?alias\s+for|(?:the\s+)?same\s+as|equal to|equivalent to|called|known as|packaged as|corresponds to|maps to|mapped to))?"
    r")\s+"
    r"(?:`[^`\n]{2,}`|/?[A-Za-z][A-Za-z0-9]*(?:[._/-][A-Za-z0-9]+)*)",
)
CLAIM_RE = re.compile("|".join(f"(?:{p})" for p in CLAIM_PATTERNS), re.IGNORECASE)
ACTION_LANGUAGE_RE = re.compile(r"^\s*(?:i|we|let me|let's|i'll|we'll)\b", re.IGNORECASE)
STATE_CLAIM_SIGNAL_RE = re.compile(
    r"\b(?:"
    r"fixed|resolved|working|correct(?:ly)?|"
    r"exists?|missing|absent|not found|"
    r"pass(?:ed|es|ing)?|fail(?:ed|s|ing)?|"
    r"deleted|removed|added|created|modified|updated|changed|"
    r"implemented|configured|integrated|enabled"
    r")\b",
    re.IGNORECASE,
)
TECHNICAL_ANCHOR_RE = re.compile(
    r"(?:`[^`]+`|[A-Za-z]:[\\/]|https?://|[\w.-]+(?:[./_-][\w.-]+)+|\b\w*\d\w*\b)",
    re.IGNORECASE,
)


def _is_plausible_claim_line(text: str) -> bool:
    """Keep declarative technical claims, skip generic prose and process language."""
    has_state_signal = bool(STATE_CLAIM_SIGNAL_RE.search(text))
    has_technical_anchor = bool(TECHNICAL_ANCHOR_RE.search(text))

    if ACTION_LANGUAGE_RE.search(text) and not (has_state_signal or has_technical_anchor):
        return False
    if has_state_signal:
        return True
    if has_technical_anchor:
        return True
    return False


EQUIVALENCE_LINK_RE = re.compile(
    r"\b(?:"
    r"is|are|was|were|equals?|equal to|equivalent to|same as|same package as|"
    r"packaged as|known as|called|corresponds to|maps to|mapped to|alias(?:ed)? as|alias for|aka"
    r")\b|(?:->|=>|=)",
    re.IGNORECASE,
)
NON_EQUIVALENCE_STATE_RE = re.compile(
    r"\b(?:fixed|resolved|working|passing|correct|deleted|removed|added|created|modified|updated|changed|missing|absent|not found)\b",
    re.IGNORECASE,
)

# Negative Proof: only actual existence/presence absence claims require 2+ strategies.
# This intentionally does NOT match behavioral negations like "does not accept"
# or incidental negation words in non-existence contexts.
ABSENCE_CLAIM_RE = re.compile(
    r"\b(?:"
    # "X does not exist" / "X doesn't exist"
    r"(?:does|do|did)\s+not\s+exist"
    r"|(?:doesn't|don't|didn't)\s+exist"
    # "was not found" / "weren't found" / "cannot be found"
    r"|(?:was|were|is|are)\s+not\s+found"
    r"|(?:wasn't|weren't|isn't|aren't)\s+found"
    r"|(?:cannot|can't|couldn't)\s+(?:be\s+)?found"
    # "no such file/module/function/class/directory"
    r"|no\s+such\s+(?:file|module|function|class|method|directory|folder|package)"
    # "X is missing from" / "X is absent from"
    r"|(?:is|are|was|were)\s+(?:missing|absent)\s+(?:from|in)"
    # "there is no X" / "there are no X"
    r"|there\s+(?:is|are|was|were)\s+no\s+\w+"
    # "don't have / doesn't have / haven't / hasn't" — "we don't have API keys"
    r"|(?:don't|doesn't|didn't|won't|haven't|hasn't)\s+have"
    # "not implemented / not configured / not integrated / not enabled"
    r"|not\s+(?:yet\s+)?(?:implemented|configured|integrated|added|enabled|set\s+up)"
    # "no [tech noun]" — "No skill", "No API key handling", "No Claude Code Skill"
    r"|no\b.{0,60}\b(?:skill|integration|support|implementation|api\s*key|hook|config(?:uration)?|handling)"
    r")\b",
    re.IGNORECASE,
)

PATH_RE = re.compile(r"(?:[A-Za-z]:)?[\\/][\w./\\-]+|[\w./\\-]+\.(?:py|js|ts|md|json|yaml|yml|toml|ini|cfg|txt)")
IDENT_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_-]{2,})`|([A-Za-z_][A-Za-z0-9_-]{2,})")
NOISE = {
    # Articles and pronouns
    "the", "a", "an", "it", "its", "this", "that", "these", "those",
    # Prepositions
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "into",
    # Verbs (common in claims and tech prose)
    "is", "are", "was", "were", "be", "been", "being", "has", "have", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "can", "must", "shall", "get", "got", "set", "run", "ran", "let",
    "add", "use", "used", "using", "make", "made", "find", "found",
    "read", "show", "fix", "fixable", "merge", "split", "filter",
    # Conjunctions
    "and", "or", "but", "if", "then", "else", "when", "while", "not",
    # Common nouns in tech context (too generic to be meaningful entities)
    "file", "files", "code", "data", "list", "item", "items", "test", "tests",
    "function", "class", "method", "module", "error", "result", "output",
    "input", "value", "name", "type", "path", "paths", "dir", "directory",
    "line", "lines", "works", "working", "fixed", "resolved", "exists",
}


# =============================================================================
# Strategy B: External resource negative-existence claims (turn-scoped)
# Moved from Stop_unverified_existence_gate.py
# =============================================================================

_NEGATIVE_EXISTENCE_PHRASES = re.compile(
    r"doesn't\s+exist"
    r"|does\s+not\s+exist"
    r"|not\s+found"
    r"|couldn't\s+find"
    r"|could\s+not\s+(?:be\s+)?found"
    r"|no\s+results?\s+(?:for|found)"
    r"|(?:repo|repository|package|url|site)\s+(?:does\s+not|doesn't)\s+exist"
    r"|failed\s+to\s+(?:load|fetch|reach|find|access)"
    r"|returns?\s+(?:404|not\s+found)"
    r"|(?:web\s+)?search\s+(?:couldn't|could\s+not|didn't|did\s+not)\s+find"
    r"|search\s+returned\s+(?:nothing|no\s+results?|empty)",
    re.IGNORECASE,
)

_EXTERNAL_RESOURCE_PATTERNS = [
    re.compile(r"github\.com/[\w.-]+/[\w.-]+", re.IGNORECASE),
    re.compile(r"[\w.-]+/[\w.-]+\s+(?:repo|repository)", re.IGNORECASE),
    re.compile(r"https?://\S+", re.IGNORECASE),
    re.compile(r"(?:npm|pypi|pip)\s+package\s+[\w.-]+", re.IGNORECASE),
    # "requests on PyPI", "foobar on npm", "mycrate on crates.io"
    re.compile(r"\b[\w.-]+\s+(?:package\s+)?on\s+(?:pypi|npm|crates\.io|rubygems|homebrew)\b", re.IGNORECASE),
    re.compile(r"(?<![./])\b[\w-]{2,}/[\w-]{2,}\b(?![./])", re.IGNORECASE),
]

_LOCAL_QUALIFIERS = re.compile(
    r"\b(?:local(?:ly)?|on\s+disk|in\s+the\s+(?:repo|codebase|project"
    r"|directory|file(?:s)?))\b",
    re.IGNORECASE,
)

_EXISTENCE_VERIFICATION_TOOLS = frozenset({
    "WebFetch", "WebSearch", "web_fetch", "web_search",
    "mcp__webReader", "mcp__zread", "mcp__plugin_context7",
    "Bash",
})

_URL_RE_SPLIT = re.compile(r"https?://", re.IGNORECASE)


def _segments(text: str) -> list[str]:
    """Split text into analysable segments (newline-first, then sentence)."""
    result = []
    for line in re.split(r"\r?\n", text):
        line = line.strip()
        if not line:
            continue
        if _URL_RE_SPLIT.search(line):
            result.append(line)
        else:
            result.extend(
                s.strip()
                for s in re.split(r"(?<=[.!?])\s+", line)
                if s.strip()
            )
    return result


def _find_suspicious_existence_sentences(response: str) -> list[tuple[str, str]]:
    """Two-stage: negative phrase + external resource in same segment."""
    results = []
    for segment in _segments(response):
        if not _NEGATIVE_EXISTENCE_PHRASES.search(segment):
            continue
        if _LOCAL_QUALIFIERS.search(segment):
            continue
        for pattern in _EXTERNAL_RESOURCE_PATTERNS:
            m = pattern.search(segment)
            if m:
                results.append((segment.strip(), m.group(0)))
                break
    return results


def _event_matches_target(event: dict, target: str, tool_names: set[str]) -> bool:
    """Check if tool event contains target string in command or output."""
    tool_name = event.get("name", "")
    if tool_name not in tool_names:
        return False

    target_lower = target.lower().rstrip("/")
    command = (event.get("command", "") or "").lower()
    output = (event.get("output", "") or "").lower()

    # Special handling for Bash tool (check command directly)
    if tool_name == "Bash":
        return target_lower in command

    if target_lower in command or target_lower in output:
        return True

    # For GitHub URLs, check owner/repo match
    parts = target_lower.split("/")
    if len(parts) >= 2:
        owner_repo = "/".join(parts[-2:])
        if owner_repo in command or owner_repo in output:
            return True

    return False


def _resource_was_fetched(resource: str, tool_events: list[dict]) -> bool:
    """Check if a verification tool was called with this resource."""
    return any(_event_matches_target(e, resource, _EXISTENCE_VERIFICATION_TOOLS)
               for e in tool_events)


# =============================================================================
# Strategy C: Action claims -- "I grepped/fetched/ran" (turn-scoped)
# =============================================================================

_ACTION_CLAIM_VERB_RE = re.compile(
    r"\b(?:"
    r"i\s+(?:checked|ran|searched|grepped|fetched|queried|looked\s+at|inspected|verified|tested|tried|called|hit|pinged|scanned)"
    r"|(?:grep|search|fetch|query|check)\s+(?:returned|found|showed|revealed|produced|yielded)"
    r"|(?:the\s+)?(?:api|endpoint)\s+returns?"
    r"|(?:running|executing)\s+(?:the\s+)?(?:command|test|script|query)\s+(?:shows?|returns?|gives?|yields?)"
    r")\b",
    re.IGNORECASE,
)

_ACTION_RESULT_RE = re.compile(
    r"\b(?:"
    r"(?:nothing|no\s+results?|empty|zero\s+(?:results?|matches?|hits?))"
    r"|(?:returns?\s+(?:\d{3}|true|false|null|ok|success|error))"
    r"|(?:found\s+(?:no|nothing|\d+))"
    r"|(?:just\s+a?\s*(?:skeleton|placeholder|stub))"
    r"|(?:only\s+(?:a\s+)?(?:skeleton|placeholder|stub))"
    r")\b",
    re.IGNORECASE,
)


def _has_external_resource(segment: str) -> bool:
    """Check if segment mentions an external resource."""
    return any(p.search(segment) for p in _EXTERNAL_RESOURCE_PATTERNS)


def _infer_implied_tool(sentence: str) -> str | None:
    """Map action verb to implied tool. Returns None if ambiguous."""
    s = sentence.lower()
    if any(v in s for v in ("grepped", "grep returned", "grep found", "grep showed")):
        return "Grep"
    if any(v in s for v in ("web search", "searched the web", "search returned", "search found")):
        return "WebSearch"
    if any(v in s for v in ("fetched", "called the api", "hit the api", "hit the endpoint", "api returns")):
        return "WebFetch"
    if any(v in s for v in ("ran the test", "running the test", "tested", "ran pytest", "executed")):
        return "Bash"
    if any(v in s for v in ("read the file", "looked at the file", "inspected the file")):
        return "Read"
    if "checked" in s:
        return None  # Ambiguous
    return None


# Patterns to extract specific target from action claim sentences.
# Order matters: first match wins.
_ACTION_TARGET_PATTERNS = [
    # grepped/searched for X and/but/in ...
    re.compile(r'(?:grepped|searched|looked|grep(?:ped)?)\s+for\s+\W?(\w[\w\s]*\w|\w+)\W?\s+(?:and|but|in)\b', re.IGNORECASE),
    # grepped/searched for X (bare word)
    re.compile(r'(?:grepped|searched|looked|grep(?:ped)?)\s+for\s+(\S+)', re.IGNORECASE),
    # fetched https://...
    re.compile(r'(?:fetched|hit|called|pinged)\s+(https?://\S+)', re.IGNORECASE),
    # fetched the endpoint X
    re.compile(r'(?:fetched|hit|called|pinged)\s+(?:the\s+)?(?:endpoint|url|api)\s+(\S+)', re.IGNORECASE),
    # grep returned nothing for X
    re.compile(r'grep\s+(?:returned|found|showed)\s+\w+\s+for\s+(\S+)', re.IGNORECASE),
    # read the file X / inspected X
    re.compile(r'(?:read|inspected|looked at)\s+(?:the\s+)?(?:file\s+)?([/\w][\w./-]+)', re.IGNORECASE),
]


def _extract_action_target(sentence: str) -> str | None:
    """Extract the specific target (search term, URL, filename) from an action claim.

    Returns None if no specific target is identified (e.g. "I ran the tests").
    When None, only tool-type matching is needed (fail-open for Strategy C).
    """
    for pattern in _ACTION_TARGET_PATTERNS:
        m = pattern.search(sentence)
        if m:
            target = m.group(1).strip().strip("'`\".,;:!?")
            if len(target) >= 2:
                return target
    return None


def _detect_action_claims(response: str) -> list[tuple[str, str | None, str | None]]:
    """Find sentences where LLM claims a tool was run + reports its result.

    Returns list of (sentence, implied_tool_name_or_None, target_or_None) triples.
    The target is the specific search term, URL, or filename mentioned in the claim.
    When target is None, only tool-type matching is required (no specific target).
    """
    results = []
    for segment in _segments(response):
        if not _ACTION_CLAIM_VERB_RE.search(segment):
            continue
        if not _ACTION_RESULT_RE.search(segment) and not _has_external_resource(segment):
            continue
        implied_tool = _infer_implied_tool(segment)
        target = _extract_action_target(segment)
        results.append((segment.strip(), implied_tool, target))
    return results


def _action_tool_was_called(
    implied_tool: str | None,
    turn_events: list[dict],
    target: str | None = None,
) -> bool:
    """Check if the implied tool appears in turn-scoped events.

    When target is provided, also verifies the tool call is RELATED to the
    claim by checking if the target string appears in the tool's command or
    output (same pattern as Strategy B's _resource_was_fetched).

    When target is None (no specific target in claim), only tool-type matching
    is required — fail-open, since Strategy B covers existence claims.
    """
    if implied_tool is None:
        return any(e.get("name") in OBSERVATION_TOOLS for e in turn_events)

    if target is None:
        # No specific target → just check tool was called
        return any(e.get("name") == implied_tool for e in turn_events)

    # Target present → verify content relatedness using helper
    matching_events = [e for e in turn_events if e.get("name") == implied_tool]
    return any(_event_matches_target(e, target, {implied_tool}) for e in matching_events)


def _build_existence_warn_message(warns: list[dict]) -> str:
    """Build systemMessage for fail-warn when evidence is unavailable."""
    lines = [
        "**\u26a0\ufe0f Unverified External Existence Claim (evidence system unavailable)**\n",
        "The response appears to claim external resource(s) don't exist, "
        "but the evidence system could not verify whether fetch/search "
        "tools were actually used this turn.\n",
    ]
    for w in warns:
        lines.append(f'- Suspicious: `{w["resource"]}` -- "{w["claim"]}"')
    lines.append("")
    lines.append(
        "Verify before trusting: use WebFetch, WebSearch, or `gh` "
        "to confirm the resource actually doesn't exist."
    )
    return "\n".join(lines)



def detect_claims(response_text: str) -> list[str]:
    if not response_text.strip():
        return []

    # Strip structural formatting (headers, blockquotes)
    cleaned_text = strip_non_claim_lines(response_text)

    claims: list[str] = []
    for line in cleaned_text.splitlines():
        text = line.strip()
        if not text:
            continue
        if is_question(text):
            continue
        if CLAIM_RE.search(text):
            if not _is_plausible_claim_line(text):
                continue
            claims.append(text)

    # fallback: long prose with success claims but no line split signal
    if (
        not claims
        and CLAIM_RE.search(cleaned_text)
        and not is_question(cleaned_text)
        and _is_plausible_claim_line(cleaned_text)
    ):
        claims = [cleaned_text.strip()]
    return claims[:20]


def _extract_entities(text: str) -> set[str]:
    entities: set[str] = set()
    for m in PATH_RE.finditer(text):
        entities.add(m.group(0).strip().lower())
    for m in IDENT_RE.finditer(text):
        val = (m.group(1) or m.group(2) or "").strip().lower()
        if len(val) >= 3 and val not in NOISE:
            entities.add(val)
    return entities


def _build_evidence_entities(events: list[dict[str, Any]]) -> set[str]:
    entities: set[str] = set()
    for event in events:
        entities |= _extract_entities(str(event.get("command", "")))
        entities |= _extract_entities(str(event.get("cwd", "")))
        entities |= _extract_entities(str(event.get("output", "")))
    return entities


def _build_evidence_chunks(events: list[dict[str, Any]]) -> list[str]:
    chunks: list[str] = []
    for event in events:
        for field in ("command", "cwd", "output"):
            value = str(event.get(field, "")).strip()
            if not value:
                continue
            for line in value.splitlines():
                cleaned = line.strip()
                if cleaned:
                    chunks.append(cleaned[:2000])
    return chunks


def _extract_scope_paths(text: str) -> set[str]:
    paths: set[str] = set()
    for m in PATH_RE.finditer(text or ""):
        raw = m.group(0).strip().lower().replace("\\", "/")
        if raw:
            paths.add(raw)
    return paths


def _build_event_scope(event: dict[str, Any]) -> set[str]:
    """Extract path-like scope markers from an event."""
    # Use path-centric scope for invalidation.
    scope: set[str] = _extract_scope_paths(str(event.get("command", "")))
    if not scope:
        scope |= _extract_scope_paths(str(event.get("cwd", "")))
    return scope


def _paths_overlap(left: set[str], right: set[str]) -> bool:
    """Fuzzy path/token overlap to preserve unrelated evidence across edits."""
    if not left or not right:
        return False
    left_full = {p.replace("\\", "/").lower() for p in left}
    right_full = {p.replace("\\", "/").lower() for p in right}
    if left_full & right_full:
        return True

    left_base = {p.split("/")[-1] for p in left_full}
    right_base = {p.split("/")[-1] for p in right_full}
    if left_base & right_base:
        return True
    return False


def _evidence_window(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep currently-valid observations; invalidate only overlapping paths."""
    window: list[dict[str, Any]] = []
    scopes: list[set[str]] = []
    for event in events:
        name = str(event.get("name", ""))
        if name in STATE_CHANGING_TOOLS:
            change_scope = _build_event_scope(event)
            if not change_scope:
                # Unknown write scope: conservative reset.
                window = []
                scopes = []
                continue

            next_window: list[dict[str, Any]] = []
            next_scopes: list[set[str]] = []
            for existing, existing_scope in zip(window, scopes):
                if _paths_overlap(existing_scope, change_scope):
                    continue
                next_window.append(existing)
                next_scopes.append(existing_scope)
            window = next_window
            scopes = next_scopes
            continue
        if name in OBSERVATION_TOOLS:
            window.append(event)
            scopes.append(_build_event_scope(event))
    return window


def _canonical_token(value: str) -> str:
    token = (value or "").strip().lower()
    if not token:
        return ""
    token = token.replace("\\", "/").split("/")[-1]
    if "." in token:
        token = token.split(".", 1)[0]
    return re.sub(r"[^a-z0-9]+", "", token)


def _match_entities(claim_entities: set[str], evidence_entities: set[str]) -> list[str]:
    """Return matched evidence entities using exact + fuzzy canonical matching."""
    if not claim_entities or not evidence_entities:
        return []
    exact = set(claim_entities & evidence_entities)

    evidence_canon = {}
    for ent in evidence_entities:
        canon = _canonical_token(ent)
        if canon:
            evidence_canon.setdefault(canon, []).append(ent)

    matches: set[str] = set(exact)
    for claim_ent in claim_entities:
        claim_canon = _canonical_token(claim_ent)
        if not claim_canon:
            continue
        for ev_canon, originals in evidence_canon.items():
            if claim_canon == ev_canon:
                matches.update(originals)
            elif len(claim_canon) >= 4 and len(ev_canon) >= 4 and (
                claim_canon in ev_canon or ev_canon in claim_canon
            ):
                matches.update(originals)
    return sorted(list(matches))


def _is_equivalence_claim(claim: str, claim_entities: set[str]) -> bool:
    if len(claim_entities) < 2:
        return False
    if not EQUIVALENCE_LINK_RE.search(claim):
        return False
    if NON_EQUIVALENCE_STATE_RE.search(claim):
        return False
    return True


def _strict_entity_in_chunk(entity: str, chunk_entities: set[str]) -> bool:
    """Check if entity appears in chunk using exact or canonical-equal matching only.

    Unlike _match_entities, this does NOT use substring matching, preventing
    false positives where e.g. "arch" matches "architectural-validator".
    """
    if entity in chunk_entities:
        return True
    canon = _canonical_token(entity)
    if not canon:
        return False
    for ce in chunk_entities:
        if _canonical_token(ce) == canon:
            return True
    return False


def _has_equivalence_cooccurrence(claim_entities: set[str], evidence_chunks: list[str]) -> bool:
    """Check that at least 2 distinct claim entities co-occur in one chunk.

    Uses strict (non-fuzzy) matching to avoid false positives where substring
    overlap (e.g. "arch" inside "architecturalvalidator") makes two genuinely
    different entities appear to be the same.
    """
    if len(claim_entities) < 2:
        return False
    for chunk in evidence_chunks:
        chunk_entities = _extract_entities(chunk)
        matched_claim_count = 0
        for claim_ent in claim_entities:
            if _strict_entity_in_chunk(claim_ent, chunk_entities):
                matched_claim_count += 1
        if matched_claim_count >= 2:
            return True
    return False


def evaluate_claims(response_text: str, tools_used: list[str] | None = None, session_id: str = "", terminal_id: str = "", tool_sequence: list[dict] | None = None, user_entities: set[str] | None = None, extracted_claims: list[str] | None = None) -> dict[str, Any]:
    """
    v2.6.0: Added user_entities parameter. Entities from the user's message
    are subtracted from claim entities before matching, preventing false
    positives when Claude references user-provided content.

    v2.7.0: Added extracted_claims parameter. When provided (e.g. from a Tier 3
    claim-extractor hook), skips detect_claims() and uses the pre-parsed list
    directly. Enables structured per-claim enforcement without regex detection.
    Pass a list of claim strings matching the format detect_claims() produces.
    """
    if user_entities is None:
        user_entities = set()

    # Tier 3 path: caller pre-extracted claims (structured JSON claim extractor).
    # Tier 2 path: detect via regex over response text.
    claims = extracted_claims if extracted_claims is not None else detect_claims(response_text)
    no_strategy_a_claims = not claims

    terminal_id_resolved = (
        terminal_id
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
        or ""
    ).strip()

    # Use provided tool_sequence if available (for testing), otherwise load from shared scope API.
    # (Evidence loading needed for all strategies, not just A)
    if tool_sequence is not None:
        # Convert tool_sequence format to event format for _build_evidence_entities
        events = []
        for tool in tool_sequence:
            events.append({
                "name": tool.get("name") or tool.get("tool_name", ""),
                "command": tool.get("command", ""),
                "output": tool.get("output", ""),
                "cwd": "",
            })
        window = events
    else:
        sid = resolve_session_id(session_id)
        events = (
            load_scoped_tool_events(
                session_id=sid,
                terminal_id=terminal_id_resolved,
                scope=SCOPE_SESSION_FRESH_MUTATION_SAFE,
                limit=500,
            )
            if sid
            else []
        )
        window = _evidence_window(events)

    evidence_entities = _build_evidence_entities(window)
    evidence_chunks = _build_evidence_chunks(window)

    # fallback for same-turn tools when evidence write hasn't happened yet
    fallback_tools = [t for t in (tools_used or []) if t in OBSERVATION_TOOLS]
    has_any_evidence = bool(window) or bool(fallback_tools)

    # Diverse strategy check for absence claims (Negative Proof)
    def _get_strategy_count(events: list[dict[str, Any]]) -> int:
        strategies = set()
        for e in events:
            name = e.get("name") or e.get("tool_name")
            if name:
                strategies.add(name)
        return len(strategies)

    if not has_any_evidence and not no_strategy_a_claims:
        return {
            "decision": "block",
            "reason": "NO_EVIDENCE",
            "claims": claims,
            "missing_claims": claims[:5],
            "evidence_entities": [],
        }

    missing_claims: list[str] = []
    claim_details: list[dict[str, Any]] = []
    verified_claims: list[str] = []

    for claim in claims:  # Only runs if Strategy A found claims
        claim_lower = claim.lower()
        is_absence_claim = bool(ABSENCE_CLAIM_RE.search(claim_lower))

        claim_entities = _extract_entities(claim)
        # v2.6.0: Subtract user-provided entities - not novel claims
        if user_entities:
            claim_entities -= user_entities

        if claim_entities:
            overlap = _match_entities(claim_entities, evidence_entities)
            ok = bool(overlap)

            # If it's an absence claim, enforce diverse strategies (Negative Proof)
            if ok and is_absence_claim:
                strategy_count = _get_strategy_count(window)
                if strategy_count < 2:
                    ok = False
                    overlap = [] # Reset overlap to signal failure
                else:
                    # Success path
                    pass

            if ok and _is_equivalence_claim(claim, claim_entities):
                ok = _has_equivalence_cooccurrence(claim_entities, evidence_chunks)
                if not ok:
                    overlap = []
        else:
            overlap = []
            ok = has_any_evidence

        claim_details.append(
            {
                "claim": claim,
                "claim_entities": sorted(list(claim_entities)),
                "matched_entities": overlap,
                "verified": ok,
            }
        )
        if not ok:
            missing_claims.append(claim)
        else:
            verified_claims.append(claim)

    # Strategy A failures collected — do NOT early-return yet.
    # Strategy B+C must still run so all failures (A + B + C) are reported
    # together in one block. Returning early here meant a B/C lie was only
    # caught on the *second* submit after A was fixed — confusing UX.

    # =========================================================================
    # Strategy B + C: Turn-scoped verification (external existence + action claims)
    # =========================================================================

    # Slice to turn scope using the shared scope API.
    if tool_sequence is not None:
        turn_events = events  # Synthetic test path
    else:
        turn_events = (
            load_scoped_tool_events(
                session_id=sid if sid else session_id,
                terminal_id=terminal_id_resolved,
                scope=SCOPE_TURN_STRICT,
                limit=500,
            )
            if (sid if sid else session_id)
            else None
        )

    # Strategy B: negative external existence claims
    existence_failures: list[dict[str, Any]] = []
    suspicious_existence = _find_suspicious_existence_sentences(response_text)
    for sentence, resource in suspicious_existence:
        if turn_events is None:
            existence_failures.append({
                "type": "existence_warn", "claim": sentence, "resource": resource,
            })
        elif not _resource_was_fetched(resource, turn_events):
            existence_failures.append({
                "type": "existence_block", "claim": sentence, "resource": resource,
            })

    # Strategy C: action claims (first-person tool-result assertions)
    action_failures: list[dict[str, Any]] = []
    if turn_events is not None:
        suspicious_actions = _detect_action_claims(response_text)
        for sentence, implied_tool, target in suspicious_actions:
            if not _action_tool_was_called(implied_tool, turn_events, target):
                action_failures.append({
                    "type": "action_claim", "claim": sentence,
                    "implied_tool": implied_tool or "any_observation",
                })

    existence_blocks = [f for f in existence_failures if f["type"] == "existence_block"]
    existence_warns = [f for f in existence_failures if f["type"] == "existence_warn"]
    all_bc_blocks = existence_blocks + action_failures

    # Combine A + B + C failures into one block (single submit, full picture)
    if missing_claims or all_bc_blocks:
        bc_claims = [f["claim"] for f in all_bc_blocks]
        all_missing = missing_claims + bc_claims
        return {
            "decision": "block",
            "reason": "UNVERIFIED_CLAIMS",
            "claims": claims + bc_claims,
            "missing_claims": all_missing[:5],
            "claim_details": claim_details,
            "existence_failures": existence_blocks,
            "action_claim_failures": action_failures,
            "evidence_entities": sorted(list(evidence_entities))[:100],
        }

    if existence_warns:
        return {
            "decision": "warn",
            "reason": "EXISTENCE_EVIDENCE_UNAVAILABLE",
            "systemMessage": _build_existence_warn_message(existence_warns),
            "claims": claims,
            "verified_claims": verified_claims,
            "claim_details": claim_details,
            "evidence_entities": sorted(list(evidence_entities))[:100],
        }

    if no_strategy_a_claims and not claims:
        return {"decision": "allow", "reason": "NO_CLAIMS", "claims": []}

    return {
        "decision": "allow",
        "reason": "CLAIMS_VERIFIED",
        "claims": claims,
        "verified_claims": verified_claims,
        "claim_details": claim_details,
        "evidence_entities": sorted(list(evidence_entities))[:100],
    }


def _extract_user_entities(prompt_text: str) -> set[str]:
    """Extract entities from the user's prompt so we do not treat user-provided
    identifiers as novel assistant claims.

    This is intentionally conservative: it only subtracts entities the prompt
    clearly names, and it never blocks on its own.
    """
    if not prompt_text or not isinstance(prompt_text, str):
        return set()
    return _extract_entities(prompt_text)


def run(data: dict[str, Any]) -> dict[str, Any]:
    """In-process entry point used by Stop_router.

    The router passes the Stop payload as a dict. This adapter normalizes the
    fields expected by evaluate_claims() and returns the same decision schema.
    """
    if not isinstance(data, dict):
        return {"decision": "allow", "reason": "INVALID_INPUT"}

    response_text = str(
        data.get("response")
        or data.get("assistant_response")
        or data.get("last_assistant_message")
        or ""
    )
    if not response_text.strip():
        return {
            "decision": "warn",
            "reason": "MISSING_RESPONSE",
            "systemMessage": "Unified claim verifier received no response text.",
        }

    prompt_text = str(data.get("prompt") or data.get("user_prompt") or "")
    tool_events = data.get("tool_events")
    tool_sequence = tool_events if isinstance(tool_events, list) else None

    tools_used = data.get("tools_used")
    tools_list = [str(tool) for tool in tools_used if str(tool).strip()] if isinstance(tools_used, list) else None

    extracted_claims = data.get("extracted_claims")
    if not isinstance(extracted_claims, list):
        extracted_claims = None

    user_entities = _extract_user_entities(prompt_text)
    session_id = str(data.get("session_id") or data.get("conversation_id") or "")
    terminal_id = str(data.get("terminal_id") or data.get("terminalId") or "")

    return evaluate_claims(
        response_text=response_text,
        tools_used=tools_list,
        session_id=session_id,
        terminal_id=terminal_id,
        tool_sequence=tool_sequence,
        user_entities=user_entities,
        extracted_claims=extracted_claims,
    )


def main() -> int:
    """CLI fallback for subprocess execution and manual debugging."""
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"decision": "approve"}))
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(
            json.dumps(
                {
                    "decision": "warn",
                    "reason": "INVALID_JSON",
                    "systemMessage": f"Unified claim verifier could not parse input: {exc}",
                }
            )
        )
        return 0

    result = run(payload if isinstance(payload, dict) else {})
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
