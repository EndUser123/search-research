#!/usr/bin/env python3
"""
Stop hook: recommendation-negation observer (ADVISORY — logs only, never blocks).

Purpose: gather the corpus of "recommend X → immediately negate X" patterns so a
future gate decision has TP/FP data. This session (2026-07-08) exhibited the pattern:
"I recommend building the observer" → next sentence → "however, should wait."

Detection signal: a recommendation phrase followed within N sentences by a
negation/hedge of that same action. The observer logs candidates (broad match);
a human reviews to classify TP (real self-contradiction) vs FP (legitimate nuance
like "recommend A, however B also works" which is a comparison, not a negation).

This is the corpus-gatherer, not the gate. Per feedback_gate_discrimination_rule:
ship no gate until TP/FP is measured on a real corpus.

Output: P:/.claude/hooks/.state/negation_hits_{terminal}.jsonl
  {"ts","recommendation_phrase","negation_phrase","distance_sentences","snippet"}

No stdout on success (Stop allow = silence). Never exit non-zero.
"""

from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

HOOKS_DIR = Path(__file__).resolve().parent
STATE_DIR = HOOKS_DIR / ".state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Recommendation phrases (preceding the negation)
RECO_PATTERNS = [
    r"\b(?:i\s+)?recommend\b",
    r"\b(?:my|the)\s+recommendation\b",
    r"\b(?:i\s+)?(?:would|'d)\s+(?:choose|pick|go\s+with|build|start)\b",
    r"\byes,?\s+(?:build|do|create|ship|implement)\b",
    r"\bdo\s+it\b",
    r"\bbuild\s+it\b",
    r"\b(?:go\s+ahead|proceed|ship\s+it)\b",
]

# Negation/hedge phrases (following the recommendation)
NEGATION_PATTERNS = [
    r"\bhowever,?\s+(?:don'?t|should\s+not|shouldn'?t|wait|hold)\b",
    r"\bbut\s+(?:then|actually|on\s+second\s+thought|you\s+should\s+wait)\b",
    r"\b(?:don'?t|should\s+not|shouldn'?t)\s+(?:build|do|create|ship|implement|add)\b",
    r"\b(?:should\s+wait|wait\s+unless|hold\s+off)\b",
    r"\b(?:on\s+second\s+thought|actually,?\s+(?:don'?t|no))\b",
    r"\bunless\s+you\s+want\b",
    r"\bnot\s+(?:today|now|yet)\b",
    r"\b(?:stand\s+down|hold\s+off|skip\s+it)\b",
]
_RECO = [re.compile(p, re.IGNORECASE) for p in RECO_PATTERNS]
_NEG = [re.compile(p, re.IGNORECASE) for p in NEGATION_PATTERNS]

MAX_SENTENCE_DISTANCE = 5  # negation must be within N sentences of recommendation


def _log_path() -> Path:
    tid = os.environ.get("WT_SESSION") or os.environ.get("CLAUDE_SESSION_ID") or "shared"
    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", tid)[:48]
    return STATE_DIR / f"negation_hits_{safe}.jsonl"


def _split_sentences(text: str) -> list[str]:
    # Simple sentence splitter — good enough for corpus gathering
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def _extract_response(payload: dict) -> str:
    # Try transcript_path first (authoritative)
    tp = payload.get("transcript_path")
    if tp and os.path.exists(tp):
        try:
            lines = open(tp, encoding="utf-8", errors="replace").read().splitlines()
            # Find the last assistant message
            for line in reversed(lines):
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("type") == "assistant" or (
                    isinstance(d.get("message"), dict)
                    and d["message"].get("role") == "assistant"
                ):
                    msg = d.get("message", {})
                    content = msg.get("content", [])
                    texts = []
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                texts.append(block.get("text", ""))
                    elif isinstance(content, str):
                        texts.append(content)
                    return " ".join(texts)
        except Exception:
            pass
    # Fallback: response field
    return payload.get("response") or payload.get("text") or ""


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        payload = json.loads(raw)
    except Exception:
        return 0

    text = _extract_response(payload)
    if not text or len(text) < 50:
        return 0

    sentences = _split_sentences(text)
    if len(sentences) < 2:
        return 0

    hits = []
    for i, sent in enumerate(sentences):
        # Check if this sentence has a recommendation
        reco_match = None
        for rx in _RECO:
            m = rx.search(sent)
            if m:
                reco_match = m
                break
        if not reco_match:
            continue

        # Look ahead within MAX_SENTENCE_DISTANCE for a negation
        for j in range(i + 1, min(i + 1 + MAX_SENTENCE_DISTANCE, len(sentences))):
            for nx in _NEG:
                nm = nx.search(sentences[j])
                if nm:
                    window = " ".join(sentences[i : j + 1])
                    hits.append({
                        "recommendation_phrase": reco_match.group(0),
                        "negation_phrase": nm.group(0),
                        "distance_sentences": j - i,
                        "snippet": window[:300],
                    })
                    break  # one negation per recommendation is enough
            if hits and hits[-1]["distance_sentences"] == j - i:
                break  # already found for this reco at this distance

    if not hits:
        return 0

    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hits": hits,
    }
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        return 0

    return 0  # advisory: always allow


if __name__ == "__main__":
    sys.exit(main())
