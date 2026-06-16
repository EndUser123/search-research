#!/usr/bin/env python3
"""Regen-cap threshold tuning report.

Reads logs/diagnostics/regen_cap_telemetry.jsonl (written by Stop._log_regen_iteration)
and reports the distribution of quality-gate repair-loop depths, so the circuit-breaker
threshold (DEFAULT_THRESHOLD in __lib/circuit_breaker.py) can be tuned on evidence.

# NOTE: summarize()/_segment_chains() are new -- grep over .claude + packages confirmed
# no existing regen_cap telemetry reader to reuse (this telemetry stream is new).

A "chain" = one continuation/regenerate loop within a terminal, segmented by terminal_id
+ count resets. Per chain we record the max depth reached and whether the cap tripped.

Usage:
  python regen_cap_stats.py            # full report
  python regen_cap_stats.py --check    # one-line verdict; exit 10 if tuning signalled
  python regen_cap_stats.py --json     # machine-readable summary
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
TELEMETRY = HOOKS_DIR / "logs" / "diagnostics" / "regen_cap_telemetry.jsonl"

MIN_CHAINS = 20        # need a stable sample before recommending a change
HIGH_CAP_HIT = 0.40    # >=40% of loops exhausting the cap is worth surfacing


def _load_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _segment_chains(rows: list[dict]) -> list[dict]:
    """Group rows into loop chains. Returns [{max_count, tripped, gate}] per chain."""
    by_term: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_term[r.get("terminal_id", "")].append(r)
    chains: list[dict] = []
    for _term, term_rows in by_term.items():
        term_rows.sort(key=lambda r: r.get("ts", 0))
        cur: dict | None = None
        prev_count = 0
        for r in term_rows:
            c = int(r.get("count", 0))
            if cur is None or c <= prev_count:
                if cur is not None:
                    chains.append(cur)
                cur = {"max_count": c, "tripped": bool(r.get("tripped")), "gate": r.get("gate", "")}
            else:
                cur["max_count"] = max(cur["max_count"], c)
                cur["tripped"] = cur["tripped"] or bool(r.get("tripped"))
            prev_count = c
        if cur is not None:
            chains.append(cur)
    return chains


def summarize(rows: list[dict]) -> dict:
    chains = _segment_chains(rows)
    n = len(chains)
    tripped = sum(1 for c in chains if c["tripped"])
    depth_hist = Counter(c["max_count"] for c in chains)
    gate_hist = Counter(c["gate"] for c in chains if c["tripped"])
    cap_hit_rate = (tripped / n) if n else 0.0
    if n < MIN_CHAINS:
        verdict = f"INSUFFICIENT DATA ({n}/{MIN_CHAINS} loop chains) -- keep current threshold"
        signal = False
    elif cap_hit_rate >= HIGH_CAP_HIT:
        dom = gate_hist.most_common(1)[0][0] if gate_hist else "n/a"
        verdict = (f"TUNE SIGNAL -- {cap_hit_rate:.0%} of loops exhaust the cap. Lower the "
                   f"threshold if genuine non-convergence, or inspect dominant gate ({dom}).")
        signal = True
    else:
        verdict = f"HEALTHY -- {cap_hit_rate:.0%} cap-hit; most loops resolve within budget"
        signal = False
    return {
        "loop_chains": n, "tripped": tripped, "cap_hit_rate": round(cap_hit_rate, 3),
        "depth_histogram": dict(sorted(depth_hist.items())),
        "tripped_by_gate": dict(gate_hist.most_common()),
        "verdict": verdict, "tune_signal": signal,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Regen-cap threshold tuning report")
    ap.add_argument("--check", action="store_true", help="One-line verdict; exit 10 if tuning signalled")
    ap.add_argument("--json", action="store_true", help="Machine-readable summary")
    ap.add_argument("--file", default=str(TELEMETRY), help="Telemetry jsonl path")
    args = ap.parse_args()
    s = summarize(_load_rows(Path(args.file)))
    if args.json:
        print(json.dumps(s, indent=2))
    elif args.check:
        print(f"[regen-cap] {s['verdict']}")
    else:
        print("=== Regen-Cap Threshold Tuning Report ===")
        print(f"Telemetry: {args.file}")
        print(f"Loop chains: {s['loop_chains']}  |  cap-hit: {s['tripped']} ({s['cap_hit_rate']:.0%})")
        print(f"Depth histogram (max repair iterations per loop): {s['depth_histogram']}")
        if s["tripped_by_gate"]:
            print(f"Cap hits by gate: {s['tripped_by_gate']}")
        print(f"\nVERDICT: {s['verdict']}")
    return 10 if (args.check and s["tune_signal"]) else 0


if __name__ == "__main__":
    sys.exit(main())
