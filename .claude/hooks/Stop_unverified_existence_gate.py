#!/usr/bin/env python3
"""
Stop_unverified_existence_gate.py - Negative Existence Claim Detector
======================================================================

Blocks responses that assert an external resource does not exist
(URL, repo, API endpoint) WITHOUT a corresponding tool call that
actually verified the claim THIS TURN.

WHY THIS EXISTS:
  LLMs claim "I couldn't find X" or "X doesn't exist" without ever
  calling WebFetch, WebSearch, or any API tool. Existing hooks only
  fire *after* tool use -- they can't detect the *absence* of an
  expected tool call.

FAILURE MODE CAUGHT:
  "haddock-development/claude-reflect-system doesn't exist"
  -> No WebSearch or WebFetch in turn events for that resource.
  -> Gate blocks and demands verification.

TURN SCOPING (stale-data-immune, no TTL):
  Uses the shared turn-scoped evidence helper. Real Claude sessions load
  `turn_strict` evidence, while test-mode/non-UUID sessions use the same
  marker-aware spool fallback shared by the other Stop guards.

FAIL-WARN POLICY:
  Unlike most hooks, this gate does NOT fail-open silently.
  When the evidence system is unavailable AND the response contains
  suspicious external non-existence claims, the gate WARNS (injects
  advisory) rather than silently allowing. Rationale: the cost of a
  false block ("LLM must verify before claiming") is far lower than
  the cost of a false pass ("LLM confidently lies about external
  resources").

LIFECYCLE: Stop (blocking gate -- exits with code 2 to block)
"""

from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
LOG_DIR = HOOKS_DIR / "state" / "logs"
sys.path.insert(0, str(HOOKS_DIR))

# --- Logging ----------------------------------------------------------------

LOG_DIR.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("existence_gate")
_handler = logging.FileHandler(LOG_DIR / "existence_gate.log", encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(logging.DEBUG)


try:
    from turn_scoped_evidence import load_turn_scoped_events
    EVIDENCE_AVAILABLE = True
except ImportError as exc:
    EVIDENCE_AVAILABLE = False
    _logger.warning("evidence_store import failed: %s", exc)


# --- Patterns: Negative Existence Claims ------------------------------------

NEGATIVE_EXISTENCE_PHRASES = re.compile(
    r"doesn't\s+exist"
    r"|does\s+not\s+exist"
    r"|not\s+found"
    r"|couldn't\s+find"
    r"|could\s+not\s+(?:be\s+)?found"
    r"|no\s+results?\s+(?:for|found)"
    r"|(?:repo|repository|package|url|site)\s+(?:does\s+not|doesn't)\s+exist"
    r"|failed\s+to\s+(?:load|fetch|reach|find|access)"
    r"|returns?\s+(?:404|not\s+found)"
    # "web search couldn't find" / "search returned nothing"
    r"|(?:web\s+)?search\s+(?:couldn't|could\s+not|didn't|did\s+not)\s+find"
    r"|search\s+returned\s+(?:nothing|no\s+results?|empty)",
    re.IGNORECASE,
)

EXTERNAL_RESOURCE_PATTERNS = [
    re.compile(r"github\.com/[\w.-]+/[\w.-]+", re.IGNORECASE),
    re.compile(r"[\w.-]+/[\w.-]+\s+(?:repo|repository)", re.IGNORECASE),
    re.compile(r"https?://\S+", re.IGNORECASE),
    re.compile(r"(?:npm|pypi|pip)\s+package\s+[\w.-]+", re.IGNORECASE),
    # Bare owner/repo (e.g. "haddock-development/claude-reflect-system")
    # Negative lookbehind/lookahead avoids matching inside URLs or file paths
    re.compile(r"(?<![./])\b[\w-]{2,}/[\w-]{2,}\b(?![./])", re.IGNORECASE),
]

VERIFICATION_TOOLS = {
    "WebFetch", "WebSearch", "web_fetch", "web_search",
    "mcp__webReader", "mcp__zread", "mcp__plugin_context7",
    "Bash",
}

LOCAL_QUALIFIERS = re.compile(
    r"\b(?:local(?:ly)?|on\s+disk|in\s+the\s+(?:repo|codebase|project"
    r"|directory|file(?:s)?))\b",
    re.IGNORECASE,
)


# --- Segment splitting (newline-first, then sentence) ----------------------

_URL_RE = re.compile(r"https?://", re.IGNORECASE)


def _segments(text: str) -> list[str]:
    """Split into analysable segments.

    Strategy:
    1. Split on newlines first (preserves URLs intact).
    2. For non-URL lines, further split on sentence terminators.
    This prevents URLs containing ".com." from being split mid-URL.
    """
    result = []
    for line in re.split(r"\r?\n", text):
        line = line.strip()
        if not line:
            continue
        if _URL_RE.search(line):
            result.append(line)
        else:
            result.extend(
                s.strip()
                for s in re.split(r"(?<=[.!?])\s+", line)
                if s.strip()
            )
    return result


def _find_suspicious_sentences(response: str) -> list[tuple[str, str]]:
    results = []
    for segment in _segments(response):
        if not NEGATIVE_EXISTENCE_PHRASES.search(segment):
            continue
        if LOCAL_QUALIFIERS.search(segment):
            continue
        for pattern in EXTERNAL_RESOURCE_PATTERNS:
            m = pattern.search(segment)
            if m:
                results.append((segment.strip(), m.group(0)))
                break
    return results


# --- Tool history verification ---------------------------------------------

def _load_turn_events(session_id: str, terminal_id: str) -> list[dict] | None:
    """Load tool events for the current turn only (id > turn_start_event_id).

    Returns None when the evidence system is unavailable (caller handles
    fail-warn instead of fail-open).
    Returns [] when evidence IS available but no matching events exist this turn.
    """
    if not EVIDENCE_AVAILABLE:
        _logger.warning("FAIL-WARN: evidence_store not importable")
        return None

    if not session_id:
        _logger.warning("FAIL-WARN: session_id empty/missing")
        return None

    all_events = load_turn_scoped_events(
        session_id=session_id,
        terminal_id=terminal_id,
        limit=200,
    )
    if all_events is None:
        _logger.warning("FAIL-WARN: load_turn_scoped_events returned unavailable")
        return None

    _logger.debug("loaded %d events for session=%s", len(all_events), session_id[:16])
    return all_events


def _resource_was_fetched(resource: str, tool_events: list[dict]) -> bool:
    resource_lower = resource.lower().rstrip("/")

    for event in tool_events:
        tool_name = event.get("name", "")
        if tool_name not in VERIFICATION_TOOLS:
            continue

        command = (event.get("command", "") or "").lower()
        output = (event.get("output", "") or "").lower()

        # Bash: check the command string contains the resource
        if tool_name == "Bash":
            if resource_lower in command:
                return True
            continue

        if resource_lower in command or resource_lower in output:
            return True

        # Partial match: github.com/owner/repo -> check owner/repo substring
        parts = resource_lower.split("/")
        if len(parts) >= 2:
            owner_repo = "/".join(parts[-2:])
            if owner_repo in command or owner_repo in output:
                return True

    return False


# --- Public API (for Stop.py inline call) ----------------------------------

def check(data: dict) -> dict | None:
    """Core gate logic. Returns block/warn dict or None (allow).

    FAIL-WARN POLICY: When suspicious claims are detected but evidence
    system is unavailable, returns a warning (non-blocking advisory)
    instead of silently passing. This prevents confident lies about
    external resources from slipping through infra failures.
    """
    response = data.get("response", "")
    if not response:
        return None

    suspicious = _find_suspicious_sentences(response)
    if not suspicious:
        return None

    _logger.info(
        "found %d suspicious claim(s): %s",
        len(suspicious),
        [(s, r) for s, r in suspicious],
    )

    session_id = (
        data.get("session_id")
        or data.get("sessionId")
        or (data.get("session") or {}).get("id", "")
        or ""
    ).strip()

    terminal_id = (
        data.get("terminal_id")
        or data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
        or ""
    ).strip()

    tool_events = _load_turn_events(session_id, terminal_id)

    if tool_events is None:
        # FAIL-WARN: evidence unavailable but claims look suspicious.
        # Don't block (could be false positive), but inject warning.
        resources = [r for _, r in suspicious]
        _logger.warning(
            "FAIL-WARN triggered: evidence unavailable, suspicious resources: %s",
            resources,
        )
        lines = ["**\u26a0\ufe0f Unverified External Existence Claim (evidence system unavailable)**\n"]
        lines.append(
            "The response appears to claim external resource(s) don't exist, "
            "but the evidence system could not verify whether fetch/search "
            "tools were actually used this turn.\n"
        )
        for sentence, resource in suspicious:
            lines.append(f'- Suspicious: `{resource}` -- "{sentence}"')
        lines.append("")
        lines.append(
            "Verify before trusting: use WebFetch, WebSearch, or `gh` "
            "to confirm the resource actually doesn't exist."
        )
        return {"decision": "warn", "reason": "\n".join(lines)}

    # Evidence IS available -- check each claim
    unverified: list[tuple[str, str]] = []
    for sentence, resource in suspicious:
        if not _resource_was_fetched(resource, tool_events):
            unverified.append((sentence, resource))

    if not unverified:
        _logger.info("all %d claims verified against tool events", len(suspicious))
        return None

    _logger.warning("BLOCK: %d unverified claim(s): %s", len(unverified), unverified)

    lines = ["**Unverified External Existence Claim Detected**\n"]
    lines.append(
        "The response asserts that external resource(s) don't exist "
        "without evidence of a fetch/search tool call this turn.\n"
    )
    for sentence, resource in unverified:
        lines.append(f'- Claimed: `{resource}` -- "{sentence}"')
    lines.append("")
    lines.append(
        "Before claiming something doesn't exist, verify it: "
        "use WebFetch, WebSearch, or the appropriate API tool first."
    )
    return {
        "decision": "block",
        "reason": "\n".join(lines),
        "blocking_hook": "Stop_unverified_existence_gate.py",
    }


# --- Main ------------------------------------------------------------------

def main() -> None:
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            sys.exit(0)
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    result = check(data)
    if result:
        print(json.dumps(result))
        if result.get("decision") == "block":
            sys.exit(2)
        # warn -> exit 0 (non-blocking, but message is injected)


if __name__ == "__main__":
    main()
