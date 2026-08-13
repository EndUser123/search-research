#!/usr/bin/env python3
"""Unified findings index — append-only JSONL store for all finding-producing mechanisms.

Replaces 6+ scattered stores (wiki, critique log, handoffs, AAR, todo JSON, 
close-py state) with a single append-only index. Each entry is session-scoped
by session_id, providing multi-terminal isolation.

Usage:
    # Append a finding
    python findings_index.py append --source scanner --category defects \\
        --severity high --session-id <UUID> \\
        --title "fleet_health.py UNGUARDED-FILE-NOT-FOUND" \\
        --detail "line 497" --pattern-id FC-03
    
    # Query findings (session-scoped)
    python findings_index.py query --session-id <UUID>
    
    # Query findings (all, for scheduled scans)
    python findings_index.py query --category defects --since 7d
    
    # Compute act-on rate (for adaptive thresholds)
    python findings_index.py act-on-rate --category defects --since 30d

Entry schema:
    {
        "id": "<uuid>",
        "timestamp": "<ISO-8601>",
        "session_id": "<UUID>",         # session that produced the finding
        "source": "scanner|critique|aar|todo|close-py|handoff|manual",
        "category": "defects|stale-refs|coverage|epistemic-debt|friction|gaps",
        "severity": "high|medium|low|info",
        "title": "<one-line summary>",
        "detail": "<description>",
        "path": "<file path if applicable>",
        "action_taken": "fixed|ignored|deferred|handed-off|null",
        "pattern_id": "FC-XX|null",      # known failure class if applicable
        "acted_at": "<ISO-8601>|null"     # when action was taken
    }
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

INDEX_PATH = Path("P:/.artifacts/findings-index.jsonl")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_index() -> Path:
    """Ensure the index file exists and is writable."""
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not INDEX_PATH.exists():
        INDEX_PATH.touch()
    return INDEX_PATH


def append(
    source: str,
    category: str,
    severity: str,
    title: str,
    session_id: str = "",
    detail: str = "",
    path: str = "",
    pattern_id: str = "",
    action_taken: str = "",
) -> dict:
    """Append a finding to the index."""
    _ensure_index()
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": _now(),
        "session_id": session_id,
        "source": source,
        "category": category,
        "severity": severity,
        "title": title,
        "detail": detail,
        "path": path,
        "action_taken": action_taken or None,
        "pattern_id": pattern_id or None,
        "acted_at": None,
    }
    with open(INDEX_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def query(
    session_id: str = "",
    category: str = "",
    source: str = "",
    severity: str = "",
    since_days: int = 0,
    limit: int = 100,
) -> list[dict]:
    """Query findings from the index."""
    if not INDEX_PATH.exists():
        return []

    cutoff = None
    if since_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    results = []
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Filters
            if session_id and entry.get("session_id") != session_id:
                continue
            if category and entry.get("category") != category:
                continue
            if source and entry.get("source") != source:
                continue
            if severity and entry.get("severity") != severity:
                continue
            if cutoff:
                try:
                    ts = datetime.fromisoformat(
                        entry.get("timestamp", "").replace("Z", "+00:00")
                    )
                    if ts < cutoff:
                        continue
                except (ValueError, TypeError):
                    continue

            results.append(entry)

    return results[-limit:] if limit > 0 else results


def act_on_rate(category: str = "", since_days: int = 30) -> dict:
    """Compute the act-on rate for a category (for adaptive thresholds)."""
    findings = query(category=category, since_days=since_days, limit=0)
    if not findings:
        return {"category": category, "total": 0, "acted": 0, "rate": 0.0}

    acted = sum(1 for f in findings if f.get("action_taken") in ("fixed", "deferred", "handed-off"))
    return {
        "category": category,
        "total": len(findings),
        "acted": acted,
        "rate": round(acted / len(findings), 3),
    }


def mark_actioned(finding_id: str, action: str) -> bool:
    """Mark a finding as acted upon (updates the entry in-place)."""
    if not INDEX_PATH.exists():
        return False

    lines = INDEX_PATH.read_text(encoding="utf-8").strip().split("\n")
    updated = False
    new_lines = []

    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            new_lines.append(line)
            continue

        if entry.get("id") == finding_id:
            entry["action_taken"] = action
            entry["acted_at"] = _now()
            updated = True

        new_lines.append(json.dumps(entry))

    if updated:
        INDEX_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified findings index")
    sub = parser.add_subparsers(dest="command")

    # Append
    p_append = sub.add_parser("append", help="Append a finding")
    p_append.add_argument("--source", required=True)
    p_append.add_argument("--category", required=True)
    p_append.add_argument("--severity", required=True)
    p_append.add_argument("--title", required=True)
    p_append.add_argument("--session-id", default="")
    p_append.add_argument("--detail", default="")
    p_append.add_argument("--path", default="")
    p_append.add_argument("--pattern-id", default="")
    p_append.add_argument("--action-taken", default="")

    # Query
    p_query = sub.add_parser("query", help="Query findings")
    p_query.add_argument("--session-id", default="")
    p_query.add_argument("--category", default="")
    p_query.add_argument("--source", default="")
    p_query.add_argument("--severity", default="")
    p_query.add_argument("--since", type=int, default=0, help="Days to look back")
    p_query.add_argument("--limit", type=int, default=100)
    p_query.add_argument("--json", action="store_true", help="Output as JSON")

    # Act-on rate
    p_rate = sub.add_parser("act-on-rate", help="Compute act-on rate")
    p_rate.add_argument("--category", default="")
    p_rate.add_argument("--since", type=int, default=30)

    # Mark actioned
    p_mark = sub.add_parser("mark", help="Mark a finding as acted upon")
    p_mark.add_argument("--id", required=True)
    p_mark.add_argument("--action", required=True)

    args = parser.parse_args()

    if args.command == "append":
        entry = append(
            source=args.source,
            category=args.category,
            severity=args.severity,
            title=args.title,
            session_id=args.session_id,
            detail=args.detail,
            path=args.path,
            pattern_id=args.pattern_id,
            action_taken=args.action_taken,
        )
        print(json.dumps(entry, indent=2))

    elif args.command == "query":
        results = query(
            session_id=args.session_id,
            category=args.category,
            source=args.source,
            severity=args.severity,
            since_days=args.since,
            limit=args.limit,
        )
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for r in results:
                print(f"  [{r.get('severity', '?')}] {r.get('title', '?')[:80]} ({r.get('source', '?')})")

    elif args.command == "act-on-rate":
        rate = act_on_rate(category=args.category, since_days=args.since)
        print(json.dumps(rate, indent=2))

    elif args.command == "mark":
        success = mark_actioned(args.id, args.action)
        print(json.dumps({"success": success}))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
