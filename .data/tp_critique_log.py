"""Append a critique entry to the /tp critique log.

Atomic append to P:/.data/tp-critique-log.jsonl.
Called by /tp after Step 3 synthesis is complete.

Usage:
    python tp_critique_log.py append \\
        --target "should we use worktrees for all multi-file work" \\
        --verdict PROCEED \\
        --horizon now \\
        --domains "framing,anchoring,solution-space" \\
        --findings "anchoring on first option; worktrees already validated" \\
        --model glm-5-2

    python tp_critique_log.py patterns [--limit 20]

    python tp_critique_log.py outcome <entry-id> --outcome "acted-on"
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path("P:/.data/tp-critique-log.jsonl")


def append_entry(
    target: str,
    verdict: str,
    horizon: str,
    domains: str,
    findings: str,
    model: str,
) -> str:
    """Append a critique entry. Returns the entry ID."""
    entry_id = uuid.uuid4().hex[:12]
    entry = {
        "id": entry_id,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target": target,
        "verdict": verdict,
        "horizon": horizon,
        "domains": [d.strip() for d in domains.split(",") if d.strip()],
        "findings": [f.strip() for f in findings.split(";") if f.strip()],
        "model": model,
        "outcome": None,  # filled later via update_outcome
    }

    # Atomic append (single write call, OS-level atomicity for small writes)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry_id


def update_outcome(entry_id: str, outcome: str) -> bool:
    """Update the outcome field of an entry by ID. Returns True if found."""
    if not LOG_PATH.exists():
        return False

    lines = LOG_PATH.read_text(encoding="utf-8").strip().split("\n")
    updated = False
    new_lines = []
    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            if entry.get("id") == entry_id:
                entry["outcome"] = outcome
                updated = True
            new_lines.append(json.dumps(entry, ensure_ascii=False))
        except json.JSONDecodeError:
            # Bug 2 fix: preserve unparseable lines instead of dropping them silently
            new_lines.append(line)

    if updated:
        LOG_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return updated


def show_patterns(limit: int = 20) -> str:
    """Analyze recent critiques and return a patterns summary string."""
    if not LOG_PATH.exists():
        return "📊 /tp history: no critiques logged yet."

    lines_raw = LOG_PATH.read_text(encoding="utf-8").strip().split("\n")
    entries = []
    for line in lines_raw:
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not entries:
        return "📊 /tp history: no critiques logged yet."

    recent = entries[-limit:]

    # Verdict distribution
    verdicts = {}
    for e in recent:
        v = e.get("verdict", "UNKNOWN")
        verdicts[v] = verdicts.get(v, 0) + 1
    verdict_str = ", ".join(f"{count} {v}" for v, count in sorted(verdicts.items(), key=lambda x: -x[1]))

    # Unresolved count (REVISE/BLOCK with no outcome)
    unresolved = sum(
        1 for e in recent
        if e.get("verdict") in ("REVISE", "BLOCK") and not e.get("outcome")
    )

    # Domain action rates (from outcome data)
    # Accept BOTH manual vocabulary (acted-on, ignored, partially-applied)
    # AND inferred vocabulary (likely-acted-on, likely-ignored, stale-unresolved, proceeded)
    ACTED_OUTCOMES = {"acted-on", "partially-applied", "likely-acted-on"}
    IGNORED_OUTCOMES = {"ignored", "likely-ignored", "stale-unresolved"}
    domain_acted = {}
    domain_ignored = {}
    domain_total = {}
    for e in recent:
        outcome = e.get("outcome")
        for d in e.get("domains", []):
            domain_total[d] = domain_total.get(d, 0) + 1
            if outcome in ACTED_OUTCOMES:
                domain_acted[d] = domain_acted.get(d, 0) + 1
            elif outcome in IGNORED_OUTCOMES:
                domain_ignored[d] = domain_ignored.get(d, 0) + 1

    # Recurring findings (simple keyword overlap)
    finding_words = {}
    for e in recent:
        for f in e.get("findings", []):
            fl = f.lower()
            for key in ["anchoring", "sycophancy", "pre-mortem", "gold-plating",
                        "over-engineering", "root cause", "framing", "binary",
                        "session-state", "max_tokens", "serialization"]:
                if key in fl:
                    finding_words[key] = finding_words.get(key, 0) + 1

    lines_out = [f"📊 /tp history (last {len(recent)} of {len(entries)} critiques):"]
    lines_out.append(f"  Verdicts: {verdict_str}")
    if unresolved:
        lines_out.append(f"  ⚠️ Unresolved: {unresolved} REVISE/BLOCK with no recorded outcome")

    # Domain patterns (only if we have outcome data)
    has_outcomes = any(e.get("outcome") for e in recent)    if has_outcomes:
        # Domains with highest ignore rate
        ignore_rates = []
        for d, total in domain_total.items():
            ignored = domain_ignored.get(d, 0)
            if total >= 2:  # need at least 2 data points
                rate = ignored / total
                ignore_rates.append((d, rate, ignored, total))
        ignore_rates.sort(key=lambda x: -x[1])
        if ignore_rates:
            top_ignored = ignore_rates[:3]
            ignored_str = "; ".join(
                f"{d} ({ign}/{tot} ignored)" for d, _, ign, tot in top_ignored
            )
            lines_out.append(f"  Domains you skip: {ignored_str}")

        # Domains with highest action rate
        action_rates = []
        for d, total in domain_total.items():
            acted = domain_acted.get(d, 0)
            if total >= 2:
                rate = acted / total
                action_rates.append((d, rate, acted, total))
        action_rates.sort(key=lambda x: -x[1])
        if action_rates:
            top_acted = action_rates[:3]
            acted_str = "; ".join(
                f"{d} ({act}/{tot} acted on)" for d, _, act, tot in top_acted
            )
            lines_out.append(f"  Domains you act on: {acted_str}")
    else:
        lines_out.append("  (outcome tracking: no outcomes recorded yet — run 'auto' to infer from git history)")

    # Recurring findings
    recurring = [(k, c) for k, c in finding_words.items() if c >= 2]
    recurring.sort(key=lambda x: -x[1])
    if recurring:
        rec_str = ", ".join(f'"{k}" ({c}x)' for k, c in recurring[:3])
        lines_out.append(f"  Recurring themes: {rec_str}")

    return "\n".join(lines_out)


def infer_outcomes(dry_run: bool = False) -> str:
    """Infer outcomes for critiques with null outcome using git history.

    Heuristic:
    - REVISE/BLOCK with commits after timestamp in P:/ or ~/.grok → "likely-acted-on"
    - REVISE/BLOCK with no commits after timestamp → "likely-ignored"
    - PROCEED → always "proceeded" (doesn't need action tracking)
    - Stale (>7 days, REVISE/BLOCK, no outcome) → "stale-unresolved"

    Returns a summary of inferences made.
    """
    if not LOG_PATH.exists():
        return "No critique log found."

    lines_raw = LOG_PATH.read_text(encoding="utf-8").strip().split("\n")
    entries = []
    unparseable_lines = []  # Bug 2 fix: preserve corrupt lines
    for line in lines_raw:
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            unparseable_lines.append(line)  # preserve for writeback

    if not entries:
        return "No critiques to infer."

    # Get git commits since each entry's timestamp
    inferred = 0
    already_set = 0
    results = []

    for entry in entries:
        if entry.get("outcome") is not None:
            already_set += 1
            continue

        verdict = entry.get("verdict", "UNKNOWN")
        ts = entry.get("timestamp", "")

        if verdict == "PROCEED":
            entry["outcome"] = "proceeded"
            inferred += 1
            results.append(f"  {entry['id']}: PROCEED → proceeded")
            continue

        # For REVISE/BLOCK: check git history
        if verdict in ("REVISE", "BLOCK") and ts:
            # Check both repos
            commits_after = 0
            for repo in ["P:/", str(Path.home() / ".grok")]:
                try:
                    result = subprocess.run(
                        ["git", "-C", repo, "log", "--oneline", f"--since={ts}", "--format=%h"],
                        capture_output=True, text=True, timeout=5,
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        commits_after += len(result.stdout.strip().split("\n"))
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

            # Check age
            try:
                entry_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                age_days = (datetime.now(timezone.utc) - entry_time).days
            except (ValueError, TypeError):
                age_days = 0

            if commits_after > 0:
                entry["outcome"] = "likely-acted-on"
                results.append(f"  {entry['id']}: {verdict} → likely-acted-on ({commits_after} commits after)")
            elif age_days >= 7:
                entry["outcome"] = "stale-unresolved"
                results.append(f"  {entry['id']}: {verdict} → stale-unresolved ({age_days} days, no commits)")
            else:
                entry["outcome"] = "likely-ignored"
                results.append(f"  {entry['id']}: {verdict} → likely-ignored ({age_days} days, no commits)")
            inferred += 1

    if not dry_run and inferred > 0:
        new_lines = [json.dumps(e, ensure_ascii=False) for e in entries if e]
        new_lines.extend(unparseable_lines)  # Bug 2 fix: preserve corrupt lines
        LOG_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    summary = f"Inferred {inferred} outcomes ({already_set} already set).\n"
    if results:
        summary += "\n".join(results)
    return summary


def main():
    parser = argparse.ArgumentParser(description="/tp critique log manager")
    sub = parser.add_subparsers(dest="command")

    # append
    p_append = sub.add_parser("append", help="Append a critique entry")
    p_append.add_argument("--target", required=True)
    p_append.add_argument("--verdict", required=True)
    p_append.add_argument("--horizon", default="all")
    p_append.add_argument("--domains", default="")
    p_append.add_argument("--findings", default="")
    p_append.add_argument("--model", default="parent-inherited")

    # patterns
    p_patterns = sub.add_parser("patterns", help="Show patterns from recent critiques")
    p_patterns.add_argument("--limit", type=int, default=20)

    # outcome
    p_outcome = sub.add_parser("outcome", help="Update outcome for an entry")
    p_outcome.add_argument("entry_id")
    p_outcome.add_argument("--outcome", required=True, choices=["acted-on", "ignored", "partially-applied"])

    # infer
    p_infer = sub.add_parser("infer", help="Auto-infer outcomes from git history")
    p_infer.add_argument("--dry-run", action="store_true", help="Show what would be inferred without writing")

    # auto (infer + patterns in one call — what /tp calls at Step 0.5)
    p_auto = sub.add_parser("auto", help="Infer outcomes then show patterns (the /tp Step 0.5 call)")
    p_auto.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    if args.command == "append":
        entry_id = append_entry(
            args.target, args.verdict, args.horizon,
            args.domains, args.findings, args.model
        )
        print(f"Logged critique {entry_id}. To record outcome later:")
        print(f'  python P:/.data/tp_critique_log.py outcome {entry_id} --outcome acted-on')

    elif args.command == "patterns":
        print(show_patterns(args.limit))

    elif args.command == "outcome":
        if update_outcome(args.entry_id, args.outcome):
            print(f"Updated {args.entry_id} -> {args.outcome}")
        else:
            print(f"Entry {args.entry_id} not found", file=sys.stderr)
            sys.exit(1)

    elif args.command == "infer":
        result = infer_outcomes(dry_run=args.dry_run)
        print(result)

    elif args.command == "auto":
        # Infer outcomes silently, then show patterns
        infer_outcomes(dry_run=False)
        print(show_patterns(args.limit))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
