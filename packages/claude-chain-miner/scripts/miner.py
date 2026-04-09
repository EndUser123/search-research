"""Miner module — LLM/pattern-based mining of session chain content."""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

# Resolve package root once
_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pattern-based mining
# ---------------------------------------------------------------------------

# Patterns matching structured session summary blocks
# These match the bugfix.md / retrospective format used in this codebase
_MINING_PATTERNS: dict[str, list[str]] = {
    "problem": [
        r"\*\*What was the problem\?\*\*[:\s]*(.+)",
        r"Problem: (.+)",
        r"#+\s*Problem[:\s]*(.+)",
    ],
    "fix": [
        r"\*\*What was the fix\?\*\*[:\s]*(.+)",
        r"Fix: (.+)",
        r"#+\s*Fix[:\s]*(.+)",
    ],
    "action": [
        r"\*\*What did we do\?\*\*[:\s]*(.+)",
        r"Action: (.+)",
        r"#+\s*Action[:\s]*(.+)",
    ],
    "decision": [
        r"\*\*Decision[:\s]*(.+)",
        r"Decision: (.+)",
    ],
    "outcome": [
        r"\*\*Outcome[:\s]*(.+)",
        r"Outcome: (.+)",
    ],
}


def mine_patterns(text: str) -> dict[str, str]:
    """Extract structured pattern matches from a block of text.

    Returns dict mapping pattern name → matched value.
    Only the first match per pattern is returned.
    """
    results: dict[str, str] = {}
    for pattern_name, pattern_list in _MINING_PATTERNS.items():
        for pat in pattern_list:
            m = re.search(pat, text, re.MULTILINE | re.IGNORECASE | re.DOTALL)
            if m:
                results[pattern_name] = m.group(1).strip()
                break
    return results


def mine_transcript_chain(
    transcript_paths: list[Path],
    query: str | None = None,
    use_llm: bool = False,
) -> dict[str, Any]:
    """Mine a chain of transcripts for patterns.

    Args:
        transcript_paths: List of transcript .jsonl paths (oldest first)
        query: Optional natural-language query for LLM mining
        use_llm: Whether to use LLM (requires ANTHROPIC_API_KEY)

    Returns:
        dict with 'entries' (per-session pattern dict) and optionally 'llm_response'
    """
    results: dict[str, Any] = {"entries": {}, "query": query}

    for tp in transcript_paths:
        from scripts.exporter import extract_messages, parse_transcript_jsonl

        entries = parse_transcript_jsonl(tp)
        messages = extract_messages(entries)

        full_text = "\n".join(f"[{m['role']}]: {m['content']}" for m in messages)

        if query and use_llm:
            results["entries"][tp.stem] = {"text_length": len(full_text)}
            continue

        patterns = mine_patterns(full_text)
        if patterns:
            results["entries"][tp.stem] = patterns
        else:
            # Fallback: just record length if no patterns found
            results["entries"][tp.stem] = {"text_length": len(full_text), "note": "no patterns matched"}

    if query and use_llm:
        combined_text = ""
        for tp in transcript_paths:
            from scripts.exporter import extract_messages, parse_transcript_jsonl

            entries = parse_transcript_jsonl(tp)
            messages = extract_messages(entries)
            combined_text += f"\n\n=== {tp.stem} ===\n\n"
            combined_text += "\n".join(f"[{m['role']}]: {m['content'][:500]}" for m in messages[:20])

        try:
            from anthropic import Anthropic

            client = Anthropic()
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1536,
                messages=[
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nSession chain content:\n{combined_text[:8000]}",
                    }
                ],
            )
            results["llm_response"] = response.content[0].text
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM mining failed: %s", exc)
            results["llm_error"] = str(exc)

    return results


# ---------------------------------------------------------------------------
# Skill integration
# ---------------------------------------------------------------------------

MINING_PROMPT_TEMPLATE = """You are analyzing a Claude Code session chain.

Given the following session transcript excerpts, answer the query:
"{query}"

---

{context}

---

Provide a structured response with:
1. Direct answer to the query
2. Supporting evidence from the sessions
3. Any gaps or uncertainties noted"""


def build_llm_prompt(query: str, context: str) -> str:
    """Build an LLM prompt for chain mining."""
    return MINING_PROMPT_TEMPLATE.format(query=query, context=context)
