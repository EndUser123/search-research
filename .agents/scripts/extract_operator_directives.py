#!/usr/bin/env python3
"""Extract operator-stated directives/preferences from prior session transcripts.

Scans ~/.grok/sessions/*/*/chat_history.jsonl for user messages that contain
preference/directive language about models, tools, providers, or workflow.
Outputs a deduplicated, date-sorted markdown file for review and promotion
to permanent wiki concepts.

WHY THIS EXISTS
---------------
Session 019fa48a: the operator said "I told you that before" when I recommended
OpenRouter for Nemotron routing. The preference (use opencode/PI, avoid OpenRouter)
was stated in a prior session but never promoted to a durable artifact. This
script is the structural fix: it mechanically surfaces prior directives from
transcripts so they can be captured before they're needed again.

Usage:
    python P:/.agents/scripts/extract_operator_directives.py [--days 90] [--min-score 2]

Output: P:/tmp/operator-directive-candidates.md (review file for promotion)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

SESSIONS_ROOT = Path.home() / ".grok" / "sessions"
OUTPUT = Path("P:/tmp/operator-directive-candidates.md")

# --- Scoring system: a message is a "directive candidate" if score >= min_score ---

# Preference verbs (1 point each — signal intent)
PREFERENCE_SIGNALS = [
    (r"\bprefer\b", "prefer"),
    (r"\brather\b", "rather"),
    (r"\binstead(?:\s+of)?\b", "instead"),
    (r"\bavoid\b", "avoid"),
    (r"\bdon['']t use\b", "don't use"),
    (r"\bnever use\b", "never use"),
    (r"\balways use\b", "always use"),
    (r"\blast resort\b", "last resort"),
    (r"\bnot tied to\b", "not tied to"),
    (r"\bexplicit(?:ly)?\s+(?:ask|request|approve)\b", "explicit-only"),
    (r"\bI want\b", "I want"),
    (r"\bwe should\b", "we should"),
    (r"\bwe need\b", "we need"),
    (r"\bfrom now on\b", "from now on"),
    (r"\bgoing forward\b", "going forward"),
    (r"\bmake sure\b", "make sure"),
    (r"\bpolicy\b", "policy"),
    (r"\bdirective\b", "directive"),
    (r"\bstanding rule\b", "standing rule"),
]

# Model/tool/provider names (1 point each — provides routing context)
CONTEXT_SIGNALS = [
    (r"\bopencode\b", "opencode"),
    (r"\bopenrouter\b", "openrouter"),
    (r"\bopen router\b", "openrouter"),
    (r"\bor-nemotron\b", "or-nemotron"),
    (r"\bPI\b(?!\s*[,\.])", "PI"),  # PI as standalone word, not sentence punctuation
    (r"\bpi -p\b", "PI-CLI"),
    (r"\bnemotron\b", "nemotron"),
    (r"\bglm\b", "glm"),
    (r"\bmimo\b", "mimo"),
    (r"\bkimi\b", "kimi"),
    (r"\bdeepseek\b", "deepseek"),
    (r"\bqwen\b", "qwen"),
    (r"\bgemma\b", "gemma"),
    (r"\bspawn_subagent\b", "spawn_subagent"),
    (r"\bspawn subagent\b", "spawn_subagent"),
    (r"\bzen-\w+", "zen-pool"),
    (r"\bgo-kimi\b", "go-kimi"),
    (r"\bgo-mimo\b", "go-mimo"),
    (r"\bccr\b", "ccr"),
    (r"\bornith\b", "ornith"),
    (r"\bnvidia\b", "nvidia"),
    (r"\bzai\b", "zai"),
    (r"\bminimax\b", "minimax"),
    (r"\bmmx\b", "mmx"),
    (r"\bclaude\b", "claude"),
    (r"\bgrok\b", "grok"),
    (r"\bcodex\b", "codex"),
    (r"\bagy\b", "agy"),
    (r"\bmodel\b", "model"),
    (r"\brouting\b", "routing"),
    (r"\bprovider\b", "provider"),
    (r"\binference\b", "inference"),
    (r"\btransport\b", "transport"),
]


def extract_user_text(obj: dict) -> str | None:
    """Extract text from a user-type JSONL record. Returns None if synthetic/empty."""
    if obj.get("type") != "user":
        return None
    if obj.get("synthetic_reason"):
        return None  # skip injected project_instructions etc.
    content = obj.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for blk in content:
            if isinstance(blk, dict):
                t = blk.get("text")
                if isinstance(t, str):
                    parts.append(t)
        return "\n".join(parts) if parts else None
    return None


def score_message(text: str) -> tuple[int, list[str]]:
    """Score a user message for directive-ness. Returns (score, matched_signals)."""
    if not text or len(text.strip()) < 10:
        return 0, []
    low = text.lower()
    matched: list[str] = []
    score = 0
    has_preference = False
    has_context = False

    for pattern, label in PREFERENCE_SIGNALS:
        if re.search(pattern, low):
            score += 1
            matched.append(label)
            has_preference = True

    for pattern, label in CONTEXT_SIGNALS:
        if re.search(pattern, low):
            score += 1
            matched.append(label)
            has_context = True

    # Require BOTH a preference signal AND a context signal for high precision
    # A message with only context ("nemotron is broken") is informational, not directive
    # A message with only preference ("I prefer that") is too vague
    if not (has_preference and has_context):
        return 0, []

    return score, matched


def scan_session(jsonl_path: Path) -> list[dict]:
    """Scan one session's chat_history.jsonl for directive candidates."""
    candidates = []
    try:
        text = jsonl_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        user_text = extract_user_text(obj)
        if not user_text:
            continue
        score, matched = score_message(user_text)
        if score >= 2:  # at least 1 preference + 1 context
            candidates.append({
                "text": user_text[:500],  # truncate very long messages
                "score": score,
                "signals": matched,
                "session_id": jsonl_path.parent.name,
                "source": str(jsonl_path).replace("\\", "/"),
            })
    return candidates


def deduplicate(candidates: list[dict]) -> list[dict]:
    """Deduplicate by first 80 chars (fuzzy — same directive stated differently)."""
    seen: dict[str, dict] = {}
    for c in sorted(candidates, key=lambda x: -x["score"]):
        key = c["text"][:80].lower().strip()
        if key not in seen:
            seen[key] = c
        else:
            # keep the higher-scoring version
            if c["score"] > seen[key]["score"]:
                seen[key] = c
    return list(seen.values())


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract operator directives from session transcripts")
    parser.add_argument("--days", type=int, default=90, help="How many days back to scan")
    parser.add_argument("--min-score", type=int, default=2, help="Minimum score to include")
    args = parser.parse_args()

    if not SESSIONS_ROOT.exists():
        print(f"ERROR: sessions root not found: {SESSIONS_ROOT}", file=sys.stderr)
        return 1

    cutoff = datetime.now() - timedelta(days=args.days)
    jsonl_files = []
    for jsonl in SESSIONS_ROOT.rglob("chat_history.jsonl"):
        try:
            mtime = datetime.fromtimestamp(jsonl.stat().st_mtime)
        except OSError:
            continue
        if mtime >= cutoff:
            jsonl_files.append((mtime, jsonl))

    jsonl_files.sort(key=lambda x: x[0], reverse=True)
    print(f"Scanning {len(jsonl_files)} sessions (last {args.days} days)...", file=sys.stderr)

    all_candidates: list[dict] = []
    for i, (mtime, jsonl) in enumerate(jsonl_files):
        hits = scan_session(jsonl)
        for h in hits:
            h["date"] = mtime.strftime("%Y-%m-%d %H:%M")
        all_candidates.extend(hits)
        if (i + 1) % 20 == 0:
            print(f"  scanned {i+1}/{len(jsonl_files)} sessions, {len(all_candidates)} candidates so far", file=sys.stderr)

    all_candidates = [c for c in all_candidates if c["score"] >= args.min_score]
    all_candidates = deduplicate(all_candidates)
    all_candidates.sort(key=lambda x: x["date"], reverse=True)

    # Write output
    lines = [
        "# Operator directive candidates (auto-extracted from session transcripts)",
        "",
        f"> Generated by `extract_operator_directives.py` on {datetime.now().strftime('%Y-%m-%d %H:%M')}.",
        f"> Scanned {len(jsonl_files)} sessions from the last {args.days} days.",
        f"> Found {len(all_candidates)} directive candidates (min-score={args.min_score}).",
        f"> **Review and promote confirmed directives to a wiki concept.**",
        "",
        "| Date | Score | Signals | Message (truncated) | Session |",
        "|------|-------|---------|---------------------|---------|",
    ]
    for c in all_candidates:
        msg = c["text"].replace("|", "\\|").replace("\n", " ")[:120]
        signals = ", ".join(c["signals"][:5])
        lines.append(f"| {c['date']} | {c['score']} | {signals} | {msg} | {c['session_id'][:8]} |")

    lines.append("")
    lines.append("## Full text of high-score candidates (score >= 4)")
    lines.append("")
    for c in all_candidates:
        if c["score"] >= 4:
            lines.append(f"### {c['date']} — session {c['session_id'][:8]} (score: {c['score']})")
            lines.append(f"**Signals:** {', '.join(c['signals'])}")
            lines.append("")
            lines.append(f"> {c['text']}")
            lines.append("")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK: {len(all_candidates)} candidates written to {OUTPUT}", file=sys.stderr)
    print(f"    {sum(1 for c in all_candidates if c['score'] >= 4)} high-score (>=4) candidates with full text", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
