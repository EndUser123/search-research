"""Cross-session transcript scanner: routing failures, obligations, and work patterns.

Generalized 2026-07-29: now extracts ALL open obligations from session
transcripts, not just routing failures. Scans both chat_history.jsonl and
compaction/segment_*.md files for mechanical signals (exit codes, tracebacks,
operator corrections, hook blocks). Writes harvestable obligations to
pending/ for /harvest to discover automatically.

Called by /aar (session end), /dream (offline consolidation), and /tp explore
(pre-step workspace scan).

Usage:
    python analyze_session_patterns.py [--sessions N] [--output <path>] [--obligations-only]

Defaults: scan last 20 sessions, print summary, write pending suggestions.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from collections import Counter, defaultdict

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

# --- Mechanical signal patterns (from /tp transcript scan) ---
# Grounded on mechanical evidence (Huang 2024: intrinsic self-correction fails
# without external signal; mechanical signals are the external signal)

MECHANICAL_SIGNALS = {
    "failed_tool_call": re.compile(r'"exit_code":\s*[1-9]|exit code:\s*[1-9]'),
    "traceback": re.compile(r"Traceback \(most recent|SyntaxError|ImportError|ModuleNotFoundError"),
    "permission_denied": re.compile(r"Denied by permission"),
    "timeout": re.compile(r"timed out after|automatically moved to background"),
    "hook_block": re.compile(r"NO_COVERING_RECEIPT|exit code: 2"),
    "secret_detected": re.compile(r"SECRET DETECTED|gitleaks"),
    "post_verify_mutation": re.compile(r"New code was modified"),
    "file_disappeared": re.compile(r"No such file|can.t open file|FileNotFoundError"),
    "git_conflict": re.compile(r"CONFLICT \(content\)|merge conflict"),
}

# Operator correction patterns (behavioral signals from the human)
OPERATOR_CORRECTIONS = [
    re.compile(r"(?i)I wasn.t looking for|I didn.t ask (you )?to"),
    re.compile(r"(?i)stop doing|don.t do that|I never told you"),
    re.compile(r"(?i)not what I asked|that.s not correct|you.re wrong"),
    re.compile(r"(?i)overconfident|liar|lazy|you keep (doing|making)"),
    re.compile(r"(?i)I meant\b|I was looking for"),
    re.compile(r"(?i)remove it now|undo that"),
]

# Operator command patterns (requests that may not have been completed)
OPERATOR_COMMANDS = [
    re.compile(r"(?i)(go |please )?(fix|implement|add|remove|build|install|create|migrate)"),
    re.compile(r"(?i)do them all|do it now|ship it|proceed"),
    re.compile(r"(?i)/go "),
]


def extract_user_messages(chat_file: Path) -> list[str]:
    """Extract user messages from a chat_history.jsonl file."""
    messages = []
    try:
        # Regex match tolerant of whitespace variations: '"type":"user"' or
        # '"type" : "user"' or '"type": "user"'. This replaces the brittle
        # substring match (F3-05) that failed on format drift.
        _USER_TYPE_RE = re.compile(r'"type"\s*:\s*"user"')
        for line in chat_file.read_text(encoding="utf-8").splitlines():
            if _USER_TYPE_RE.search(line):
                # Try multiple extraction patterns (whitespace-tolerant)
                for pattern in [
                    r'user_query[^>]*>(.{0,500})',
                    r'"text"\s*:\s*"([^"]{1,300})"',
                    r'"content"\s*:\s*\[.*?"text"\s*:\s*"([^"]{1,300})"',
                ]:
                    m = re.search(pattern, line)
                    if m:
                        messages.append(m.group(1))
                        break
    except (OSError, UnicodeDecodeError):
        pass

    # Warn if the file is non-empty but no user messages were extracted.
    # This catches format drift (F3-05 style) silently dropping sessions.
    if not messages:
        try:
            size = chat_file.stat().st_size
            if size > 100:
                print(f"  WARNING: {chat_file.name} ({size}B) had 0 user messages "
                      f"— possible format drift", file=sys.stderr)
        except OSError:
            pass

    return messages


def scan_raw_signals(file_path: Path) -> dict:
    """Scan a chat_history.jsonl or compaction segment for mechanical signals.

    Returns counts per signal type + sample context snippets.

    KNOWN LIMITATION (F3-06): Reads the entire file into memory via read_text()
    rather than streaming line-by-line. Session transcript files can be large
    (segment_004 was ~1.8MB verbose). For a scanner that runs once per session,
    this is acceptable. If this function were called in a hot loop or on files
    exceeding ~50MB, switch to iterative line reading (for line in open(...)).
    """
    counts = defaultdict(int)
    samples = defaultdict(list)

    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"counts": {}, "samples": {}, "lines_scanned": 0}

    lines = text.splitlines()

    for line in lines:
        for signal_name, pattern in MECHANICAL_SIGNALS.items():
            if pattern.search(line):
                counts[signal_name] += 1
                if len(samples[signal_name]) < 3:
                    # Extract a snippet around the match
                    snippet = line[:200].replace("\n", " ")
                    samples[signal_name].append(snippet)

    return {
        "counts": dict(counts),
        "samples": dict(samples),
        "lines_scanned": len(lines),
    }


def extract_obligations_from_session(
    session_dir: Path, chat_file: Path
) -> list[dict]:
    """Extract open obligations from a single session.

    Scans chat_history.jsonl + compaction segments for:
    - Mechanical signals (exit codes, tracebacks, hook blocks)
    - Operator corrections (behavioral feedback)
    - Unfulfilled operator commands (requests near session end)

    Returns a list of obligation dicts suitable for pending/ output.
    """
    obligations = []
    session_id = session_dir.name

    # Scan chat_history.jsonl
    raw = scan_raw_signals(chat_file)

    # Scan compaction segments ONLY if chat_history is empty or very short
    # (post-compaction sessions have minimal chat_history). Scanning both
    # when chat_history is substantial causes double-counting because
    # compaction segments contain summaries of earlier turns.
    if raw["lines_scanned"] < 50:
        compaction_dir = session_dir / "compaction"
        if compaction_dir.exists():
            for seg in sorted(compaction_dir.glob("segment_*.md")):
                seg_raw = scan_raw_signals(seg)
                for sig, count in seg_raw["counts"].items():
                    raw["counts"][sig] = raw["counts"].get(sig, 0) + count
                    raw["samples"].setdefault(sig, []).extend(
                        seg_raw["samples"].get(sig, [])
                    )

    # Convert mechanical signals to obligations
    SIGNAL_TO_OBLIGATION = {
        "failed_tool_call": ("Failed tool calls recurring across sessions", "GENERALIZE"),
        "traceback": ("Code errors / tracebacks in session", "GENERALIZE"),
        "permission_denied": ("Permission denials blocking work", "CONVERT"),
        "timeout": ("Timeouts auto-backgrounding commands", "CONVERT"),
        "hook_block": ("Stop-hook blocks (verification receipts)", "GENERALIZE"),
        "secret_detected": ("Secret detection events", "COMPLETE"),
        "post_verify_mutation": ("Post-verify file mutations", "GENERALIZE"),
        "file_disappeared": ("Files disappearing (multi-agent contention)", "GENERALIZE"),
        "git_conflict": ("Git merge conflicts", "GENERALIZE"),
    }

    for signal_name, count in raw["counts"].items():
        if count < 2:
            continue  # Single occurrences aren't obligations yet
        if signal_name not in SIGNAL_TO_OBLIGATION:
            continue

        title, operation = SIGNAL_TO_OBLIGATION[signal_name]
        # Dedup key: signal + session
        dedup = hashlib.md5(f"{signal_name}_{session_id}".encode()).hexdigest()[:12]

        obligations.append({
            "title": f"{title} ({count} occurrences in {session_id[:8]})",
            "obligation": f"{count} instances of {signal_name} in session {session_id[:8]}. "
                          f"Sample: {raw['samples'].get(signal_name, ['(no sample)'])[0][:100]}",
            "operation": operation,
            "source": f"cross_session_scanner:{session_id}",
            "dedup_key": dedup,
            "signal_type": signal_name,
            "count": count,
        })

    # Scan user messages for operator corrections
    messages = extract_user_messages(chat_file)
    corrections_found = []
    for msg in messages:
        for pattern in OPERATOR_CORRECTIONS:
            if pattern.search(msg):
                corrections_found.append(msg[:150])
                break

    if len(corrections_found) >= 2:
        dedup = hashlib.md5(f"corrections_{session_id}".encode()).hexdigest()[:12]
        obligations.append({
            "title": f"Operator corrections ({len(corrections_found)} in {session_id[:8]})",
            "obligation": f"{len(corrections_found)} operator corrections in session {session_id[:8]}. "
                          f"Pattern: {corrections_found[0][:100]}",
            "operation": "GENERALIZE",
            "source": f"cross_session_scanner:{session_id}",
            "dedup_key": dedup,
            "signal_type": "operator_correction",
            "count": len(corrections_found),
        })

    return obligations


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


def scan_sessions(n: int = 20, extract_obligations: bool = False) -> tuple[list[dict], list[dict]]:
    """Scan the last N sessions. Returns (session_analyses, obligations)."""
    if not SESSIONS_ROOT.exists():
        return [], []

    # Sessions are nested: sessions/<encoded-cwd>/<session-id>/chat_history.jsonl
    chat_files = []
    for session_dir in SESSIONS_ROOT.rglob("chat_history.jsonl"):
        chat_files.append(session_dir)
    chat_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    sessions = []
    all_obligations = []

    for chat_file in chat_files[:n]:
        session_dir = chat_file.parent
        messages = extract_user_messages(chat_file)
        if not messages:
            continue
        analysis = classify_session(messages)
        analysis["session_id"] = session_dir.name
        analysis["cwd"] = session_dir.parent.name
        sessions.append(analysis)

        if extract_obligations:
            obs = extract_obligations_from_session(session_dir, chat_file)
            all_obligations.extend(obs)

    return sessions, all_obligations


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions", type=int, default=20, help="number of sessions to scan")
    parser.add_argument("--output", default="", help="output JSON path (default: stdout)")
    parser.add_argument("--obligations-only", action="store_true",
                        help="skip pattern analysis, only extract obligations")
    parser.add_argument("--no-obligations", action="store_true",
                        help="skip obligation extraction (legacy mode, routing patterns only)")
    args = parser.parse_args()

    extract_obs = not args.no_obligations
    results, obligations = scan_sessions(args.sessions, extract_obligations=extract_obs)

    if not args.obligations_only:
        # Pattern analysis (original behavior)
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

        # Routing frustration suggestions (original behavior)
        suggestions = []
        if total_frustration >= 5:
            suggestions.append({
                "title": f"Routing-correct pattern: {total_frustration} frustration signals across {len(results)} sessions",
                "obligation": "Operator repeatedly corrects routing — the exploration-vs-execution rule should be reviewed for effectiveness",
                "operation": "GENERALIZE",
                "hint": "grep session transcripts for 'I wasn't looking for' to track recurrence",
            })
    else:
        suggestions = []

    # Obligation extraction (new behavior)
    if obligations:
        # Deduplicate by dedup_key, keeping highest count
        seen = {}
        for obs in obligations:
            key = obs.get("dedup_key", obs["title"][:50])
            if key not in seen or obs.get("count", 0) > seen[key].get("count", 0):
                seen[key] = obs
        deduped = list(seen.values())

        print(f"\n=== Cross-Session Obligation Extraction ({len(deduped)} unique items) ===\n")
        by_type = Counter(o.get("signal_type", "unknown") for o in deduped)
        for sig_type, count in by_type.most_common():
            print(f"  {sig_type}: {count} items")

        # Merge with routing suggestions
        all_suggestions = suggestions + [
            {
                "title": o["title"],
                "obligation": o["obligation"],
                "operation": o.get("operation", "CONVERT"),
            }
            for o in deduped
        ]
    else:
        all_suggestions = suggestions

    # Write harvest suggestions to pending/ (always, regardless of --output)
    if all_suggestions:
        HARVEST_PENDING.mkdir(parents=True, exist_ok=True)
        pending_path = HARVEST_PENDING / "analyze_session_patterns.json"
        pending_path.write_text(json.dumps(all_suggestions, indent=2), encoding="utf-8")
        print(f"\nHarvest suggestions written to: {pending_path} ({len(all_suggestions)} items)")
    else:
        print("\nNo harvest suggestions")

    # Full results to --output path (separate from harvest pending)
    if args.output:
        Path(args.output).write_text(json.dumps({"sessions": results, "obligations": obligations}, indent=2), encoding="utf-8")
        print(f"Full results: {args.output}")


if __name__ == "__main__":
    main()
