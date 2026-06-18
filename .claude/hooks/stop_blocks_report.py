#!/usr/bin/env python3
"""stop_blocks_report.py — read the Stop-block diagnostic log.

Companion reader for the rows written by the cc-aca-authority Stop router
(_log_stop_block in __lib/router.py). Turns a "Blocked by hook" event into a
one-query diagnosis: which gate blocked, why, and which response.

Usage:
    python stop_blocks_report.py                 # last 10 blocks
    python stop_blocks_report.py --last 50
    python stop_blocks_report.py --gate Stop_behavior_gates.py
    python stop_blocks_report.py --session <id>
    python stop_blocks_report.py --json          # raw rows, one per line

The log is append-only JSONL at <diag_dir>/stop_blocks.jsonl, where diag_dir is
$CC_DIAGNOSTICS_DIR or P:/.claude/hooks/logs/diagnostics.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _diag_dir() -> Path:
    env = os.environ.get("CC_DIAGNOSTICS_DIR")
    if env:
        return Path(env)
    return Path("P:/.claude/hooks/logs/diagnostics")


def _load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue  # tolerate a torn line from concurrent append
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Read the Stop-block diagnostic log.")
    parser.add_argument("--last", "-n", type=int, default=10, help="show the last N blocks")
    parser.add_argument("--gate", "-g", help="filter by gate_name (substring match)")
    parser.add_argument("--session", "-s", help="filter by session_id (exact match)")
    parser.add_argument("--json", action="store_true", help="emit raw JSON rows")
    args = parser.parse_args()

    log_path = _diag_dir() / "stop_blocks.jsonl"
    rows = _load_rows(log_path)

    if args.gate:
        rows = [r for r in rows if args.gate in str(r.get("gate_name", ""))]
    if args.session:
        rows = [r for r in rows if str(r.get("session_id", "")) == args.session]

    rows = rows[-args.last :]

    if not rows:
        print(f"No Stop blocks recorded at {log_path}")
        return 0

    if args.json:
        for r in rows:
            print(json.dumps(r, ensure_ascii=False))
        return 0

    for r in rows:
        print(f"[{r.get('timestamp', '?')}] {r.get('gate_name', '?')}")
        print(f"  reason : {r.get('reason', '')}")
        span = r.get("matched_span", "")
        if span and span != r.get("reason", ""):
            print(f"  span   : {span}")
        print(
            f"  ctx    : response={r.get('response_hash', '?')} "
            f"session={r.get('session_id', '?')} terminal={r.get('terminal_id', '?')}"
        )
        print()
    print(f"{len(rows)} block(s) shown from {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
