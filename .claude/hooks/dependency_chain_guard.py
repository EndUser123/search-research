#!/usr/bin/env python3
"""Dependency-chain guard for comparative and end-to-end conclusions.

Blocks responses that rank, compare, or claim a workflow "bypasses" something
while ignoring prerequisite dependencies already established in the prompt or
recent transcript context.

Primary failure mode:
  "Whisper is the most reliable option" when prior context established that
  Whisper still depends on yt-dlp succeeding first.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

RANKING_RE = re.compile(
    r"\b("
    r"most|least|best|better|worse|worst|rank(?:ed|ing)?|reorder(?:\s+this)?|"
    r"top\s+\d+|by\s+(?:reliability|speed|risk|practicality|throughput)|"
    r"highest[- ]throughput|lowest[- ]risk|most\s+reliable|least\s+reliable|"
    r"most\s+practical|least\s+practical|fastest|slowest"
    r")\b",
    re.IGNORECASE,
)

BYPASS_RE = re.compile(
    r"\b(bypass(?:es|ing)?|doesn['’]t\s+need|does\s+not\s+need|independent\s+of)\b",
    re.IGNORECASE,
)

DEPENDENCY_ACK_RE = re.compile(
    r"\b(depends?\s+on|requires|must\s+first|still\s+needs?|upstream|prerequisite|"
    r"before\s+.*\s+can|if\s+.*\s+fails?,?\s+.*(?:can['’]?t|cannot|won['’]?t|never))\b",
    re.IGNORECASE,
)

TOKEN_RE = re.compile(r"`([^`\n]+)`|([A-Za-z][A-Za-z0-9_.+#/-]{1,40})")

DEPENDENCY_PATTERNS = [
    re.compile(
        r"to\s+use\s+(?P<child>[^,.;\n]{1,80}?),\s*(?P<parent>[^,.;\n]{1,80}?)\s+"
        r"must(?:\s+\w+){0,3}\s+(?:work|succeed|get|obtain|fetch|download|run)",
        re.IGNORECASE,
    ),
    re.compile(
        r"if\s+(?P<parent>[^,.;\n]{1,80}?)\s+(?:can['’]?t|cannot|fails?|doesn['’]?t|does\s+not)\b"
        r"[^,.;\n]{0,100}?,\s*(?P<child>[^,.;\n]{1,80}?)\s+"
        r"(?:never|can['’]?t|cannot|won['’]?t|doesn['’]?t|does\s+not)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?P<child>[^,.;\n]{1,80}?)\s+(?:still\s+)?depends?\s+on\s+(?P<parent>[^,.;\n]{1,80}?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?P<child>[^,.;\n]{1,80}?)\s+requires\s+(?P<parent>[^,.;\n]{1,80}?)",
        re.IGNORECASE,
    ),
]

STOPWORDS = {
    "a",
    "an",
    "and",
    "approach",
    "audio",
    "best",
    "bot",
    "browser",
    "by",
    "can",
    "chain",
    "chrome",
    "compare",
    "comparison",
    "content",
    "cookies",
    "dependency",
    "download",
    "end",
    "entirely",
    "fails",
    "first",
    "for",
    "from",
    "get",
    "getting",
    "have",
    "how",
    "if",
    "in",
    "is",
    "it",
    "least",
    "likely",
    "manifest",
    "method",
    "most",
    "need",
    "needs",
    "of",
    "on",
    "option",
    "or",
    "our",
    "path",
    "pipeline",
    "practical",
    "prerequisite",
    "rate",
    "reliable",
    "reliability",
    "risk",
    "session",
    "step",
    "stream",
    "succeed",
    "that",
    "the",
    "throughput",
    "to",
    "tool",
    "transcript",
    "url",
    "use",
    "video",
    "workflow",
    "youtube",
}


def _flatten_transcript(transcript: Any) -> str:
    """Serialize recent transcript entries into plain text."""
    if not isinstance(transcript, list):
        return ""

    parts: list[str] = []
    for entry in transcript[-20:]:
        if isinstance(entry, dict):
            content = entry.get("content", "")
            if isinstance(content, list):
                content_text = " ".join(
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict)
                )
            else:
                content_text = str(content)
            if content_text.strip():
                parts.append(content_text.strip())
        elif isinstance(entry, str) and entry.strip():
            parts.append(entry.strip())

    return "\n".join(parts)


def _build_context_text(data: dict[str, Any]) -> str:
    """Combine prompt and transcript context used to infer dependencies."""
    parts = [
        str(data.get("user_prompt") or ""),
        str(data.get("prompt") or ""),
        str(data.get("message") or ""),
        _flatten_transcript(data.get("transcript")),
    ]
    return "\n".join(part for part in parts if part.strip())


def _normalize_token(token: str) -> str:
    normalized = token.strip().strip("`'\".,:;()[]{}").lower()
    return normalized


def _extract_entities(text: str) -> set[str]:
    """Extract technical-ish identifiers from a phrase."""
    entities: set[str] = set()
    for match in TOKEN_RE.finditer(text):
        token = _normalize_token(match.group(1) or match.group(2) or "")
        if len(token) < 2:
            continue
        if token in STOPWORDS:
            continue
        if token.isdigit():
            continue
        entities.add(token)
    return entities


def _extract_dependency_pairs(text: str) -> list[dict[str, Any]]:
    """Extract prerequisite pairs from prompt/transcript context."""
    pairs: list[dict[str, Any]] = []
    seen: set[tuple[tuple[str, ...], tuple[str, ...]]] = set()

    for pattern in DEPENDENCY_PATTERNS:
        for match in pattern.finditer(text):
            child_text = match.group("child")
            parent_text = match.group("parent")
            child_tokens = _extract_entities(child_text)
            parent_tokens = _extract_entities(parent_text)
            if not child_tokens or not parent_tokens:
                continue
            key = (tuple(sorted(child_tokens)), tuple(sorted(parent_tokens)))
            if key in seen:
                continue
            seen.add(key)
            pairs.append(
                {
                    "child_tokens": child_tokens,
                    "parent_tokens": parent_tokens,
                    "source": match.group(0).strip(),
                }
            )

    return pairs


def _mentions_any(text: str, tokens: set[str]) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in tokens)


def _first_position(text: str, tokens: set[str]) -> int | None:
    lowered = text.lower()
    positions = [lowered.find(token) for token in tokens if lowered.find(token) >= 0]
    if not positions:
        return None
    return min(positions)


def _looks_like_conclusion(response: str) -> bool:
    return bool(RANKING_RE.search(response) or BYPASS_RE.search(response))


def _format_tokens(tokens: set[str]) -> str:
    return ", ".join(f"`{token}`" for token in sorted(tokens))


def check(data: dict[str, Any]) -> dict[str, Any] | None:
    """Return a block payload when a response ignores an established dependency."""
    response = str(data.get("assistant_response") or data.get("response") or "")
    if not response.strip():
        return None

    if not _looks_like_conclusion(response):
        return None

    context_text = _build_context_text(data)
    if not context_text.strip():
        return None

    dependency_pairs = _extract_dependency_pairs(context_text)
    if not dependency_pairs:
        return None

    violations: list[str] = []
    has_bypass = bool(BYPASS_RE.search(response))

    for pair in dependency_pairs:
        child_tokens = pair["child_tokens"]
        parent_tokens = pair["parent_tokens"]

        if not _mentions_any(response, child_tokens):
            continue

        response_mentions_parent = _mentions_any(response, parent_tokens)
        response_acknowledges_dependency = bool(DEPENDENCY_ACK_RE.search(response))
        child_pos = _first_position(response, child_tokens)
        parent_pos = _first_position(response, parent_tokens)

        if has_bypass and not (response_mentions_parent and response_acknowledges_dependency):
            violations.append(
                f"Response claims or implies a bypass for {_format_tokens(child_tokens)} "
                f"without reconciling prerequisite {_format_tokens(parent_tokens)}."
            )
            continue

        if RANKING_RE.search(response):
            if not response_mentions_parent:
                violations.append(
                    f"Response ranks {_format_tokens(child_tokens)} without mentioning upstream "
                    f"dependency {_format_tokens(parent_tokens)} established earlier."
                )
                continue

            if (
                child_pos is not None
                and parent_pos is not None
                and child_pos < parent_pos
                and not response_acknowledges_dependency
            ):
                violations.append(
                    f"Response places {_format_tokens(child_tokens)} ahead of prerequisite "
                    f"{_format_tokens(parent_tokens)} without explaining the dependency."
                )

    if not violations:
        return None

    reason_lines = [
        "DEPENDENCY CHAIN VIOLATION: Comparative or end-to-end conclusion ignored an established prerequisite.",
        "",
    ]
    for violation in violations:
        reason_lines.append(f"- {violation}")
    reason_lines.extend(
        [
            "",
            "Fix:",
            "1. State the ranking criterion explicitly.",
            "2. Acknowledge upstream prerequisites before ranking downstream steps.",
            "3. If a step depends on another tool or fetch succeeding first, say that in the answer.",
        ]
    )

    return {
        "decision": "block",
        "reason": "\n".join(reason_lines),
        "blocking_hook": "dependency_chain_guard.py",
    }


def run(data: dict[str, Any]) -> dict[str, Any] | None:
    """Stop-router entry point."""
    return check(data)


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
        sys.exit(2)


if __name__ == "__main__":
    main()
