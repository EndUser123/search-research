"""Scan session transcripts for routing failures, frustration signals, and work patterns.

Called by /aar (session end) and /dream (offline consolidation).
Writes harvestable suggestions to P:/.data/harvest/pending/analyze_session_patterns.json.

Usage:
    python analyze_session_patterns.py [--sessions N] [--output <path>]

Defaults: scan last 20 sessions, print summary, write pending suggestions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from collections import Counter

SESSIONS_ROOT = Path.home() / ".grok" / "sessions"
HARVEST_PENDING = Path("P:/.data/harvest/pending")

# Frustration / routing-correction signals (from transcript analysis 2026-07-29)
FRUSTRATION_PATTERNS = [
    re.compile(r"(?i)I wasn.t looking for"),
    re.compile(r"(?i)I didn.t ask"),
    re.compile(r"(?i)stop doing"),
    re.compile(r"(?i)I meant\b"),
    re.compile(r"(?i)not what I asked"),
    re.compile(r"(?i)you.re doing it again"),
    re.compile(r"(?i)just tell me"),
    re.compile(r"(?i)don.t implement"),
    re.compile(r"(?i)I want ideas"),
    re.compile(r"(?i)looking for ideas"),
    re.compile(r"(?i)thought partner"),
    re.compile(r"(?i)what should we change"),
    re.compile(r"(?i)what can we add"),
]

# Exploration vs execution language
EXPLORATION_RE = re.compile(
    r"(?i)(ideas|thought partner|what should|what can|explore|"
    r"should we|what else|what would|looking for|help me think)"
)
EXECUTION_RE = re.compile(
    r"(?i)(fix|implement|add|remove|build|install|create|run|"
    r"do it|execute|ship|migrate|please do)"
)


def extract_user_messages(chat_file: Path) -> list[str]:
    """Extract user messages from a chat_history.jsonl file."""
    messages = []
    try:
        for line in chat_file.read_text(encoding="utf-8").splitlines():
            if '"type":"user"' in line:
                # Try multiple extraction patterns
                for pattern in [
                    r'user_query[^>]*>(.{0,500})',
                    r'"text":"([^"]{5,300})"',
                    r'"content":\[.*?"text":"([^"]{5,300})"',
                ]:
                    m = re.search(pattern, line)
                    if m:
                        messages.append(m.group(1))
                        break
    except (OSError, UnicodeDecodeError):
        pass
    return messages


def classify_session(messages: list[str]) -> dict:
    """Classify a session's work pattern."""
    frustration_hits = []
    exploration_count = 0
    execution_count = 0

    for msg in messages:
        for pattern in FRUSTRATION_PATTERNS:
            if pattern.search(msg):
                frustration_hits.append(msg[:120])
                break

        if EXPLORATION_RE.search(msg):
            exploration_count += 1
        if EXECUTION_RE.search(msg):
            execution_count += 1

    return {
        "message_count": len(messages),
        "frustration_hits": frustration_hits,
        "frustration_count": len(frustration_hits),
        "exploration_signals": exploration_count,
        "execution_signals": execution_count,
        "pattern": (
            "exploration-heavy" if exploration_count > execution_count
            else "execution-heavy" if execution_count > exploration_count
            else "mixed"
        ),
    }


def scan_sessions(n: int = 20) -> list[dict]:
    """Scan the last N sessions."""
    if not SESSIONS_ROOT.exists():
        return []

    # Sessions are nested: sessions/<encoded-cwd>/<session-id>/chat_history.jsonl
    # Walk two levels deep and collect all chat_history.jsonl files
    chat_files = []
    for session_dir in SESSIONS_ROOT.rglob("chat_history.jsonl"):
        chat_files.append(session_dir)
    chat_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    sessions = []
    for chat_file in chat_files[:n]:
        messages = extract_user_messages(chat_file)
        if not messages:
            continue
        analysis = classify_session(messages)
        analysis["session_id"] = chat_file.parent.name
        analysis["cwd"] = chat_file.parent.parent.name
        sessions.append(analysis)

    return sessions


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions", type=int, default=20, help="number of sessions to scan")
    parser.add_argument("--output", default="", help="output JSON path (default: stdout)")
    args = parser.parse_args()

    results = scan_sessions(args.sessions)

    # Aggregate
    total_frustration = sum(s["frustration_count"] for s in results)
    total_exploration = sum(s["exploration_signals"] for s in results)
    total_execution = sum(s["execution_signals"] for s in results)

    print(f"=== Session Pattern Analysis ({len(results)} sessions) ===\n")
    print(f"Total frustration/routing signals: {total_frustration}")
    print(f"  Avg per session: {total_frustration / max(len(results), 1):.1f}")
    print(f"Exploration signals: {total_exploration}")
    print(f"Execution signals: {total_execution}")
    print()

    # Surface sessions with high frustration
    high_frustration = [s for s in results if s["frustration_count"] >= 2]
    if high_frustration:
        print(f"High-frustration sessions (≥2 signals): {len(high_frustration)}")
        for s in high_frustration[:5]:
            print(f"  {s['session_id']}: {s['frustration_count']} signals")
            for hit in s["frustration_hits"][:2]:
                print(f"    → {hit}")
        print()

    # Pattern distribution
    patterns = Counter(s["pattern"] for s in results)
    print(f"Pattern distribution: {dict(patterns)}")

    # Write harvest suggestions if frustration is high
    suggestions = []
    if total_frustration >= 5:
        suggestions.append({
            "title": f"Routing-correct pattern: {total_frustration} frustration signals across {len(results)} sessions",
            "obligation": "Operator repeatedly corrects routing — the exploration-vs-execution rule should be reviewed for effectiveness",
            "operation": "GENERALIZE",
            "hint": "grep session transcripts for 'I wasn't looking for' to track recurrence",
        })

    if suggestions:
        HARVEST_PENDING.mkdir(parents=True, exist_ok=True)
        output_path = Path(args.output) if args.output else HARVEST_PENDING / "analyze_session_patterns.json"
        output_path.write_text(json.dumps(suggestions, indent=2), encoding="utf-8")
        print(f"\nHarvest suggestions written to: {output_path}")
    else:
        print("\nNo harvest suggestions (frustration below threshold)")

    if args.output:
        Path(args.output).write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Full results: {args.output}")


if __name__ == "__main__":
    main()
