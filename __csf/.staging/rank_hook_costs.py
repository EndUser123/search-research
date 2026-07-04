"""Aggregate two JSONL telemetry files into ranked text tables. Read-only, stdlib-only."""
import json
from collections import defaultdict

F1 = r"P:/.claude/hooks/logs/diagnostics/ups_execution_trace.jsonl"
F2 = r"P:/.claude/hooks/logs/diagnostics/stop_blocks.jsonl"


def load_lines(path):
    ok, skipped = [], 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ok.append(json.loads(line))
            except json.JSONDecodeError:
                skipped += 1
    return ok, skipped


def report_ups(path):
    rows, skipped = load_lines(path)
    agg = defaultdict(lambda: {"fires": 0, "with_ctx": 0, "tokens": 0, "dur_ms": 0.0, "turns": set()})
    all_ts = []
    for r in rows:
        try:
            hook = r["hook_name"]
            res = r.get("result", {})
            a = agg[hook]
            a["fires"] += 1
            if res.get("has_context"):
                a["with_ctx"] += 1
            a["tokens"] += int(res.get("tokens_added", 0) or 0)
            a["dur_ms"] += float(r.get("duration_ms", 0.0) or 0.0)
            ts = r.get("ts", "")
            all_ts.append(ts)
            a["turns"].add((r.get("session_id"), ts[:19]))  # to-the-second
        except (KeyError, TypeError, ValueError):
            skipped += 1

    min_ts = min(all_ts) if all_ts else None
    max_ts = max(all_ts) if all_ts else None

    ranked = sorted(agg.items(), key=lambda kv: kv[1]["tokens"], reverse=True)

    print("=" * 100)
    print(f"TABLE 1: {path}")
    print(f"file min ts: {min_ts}   file max ts: {max_ts}")
    print(f"skipped malformed lines: {skipped}")
    print("=" * 100)
    hdr = f"{'hook_name':<32}{'fires':>8}{'w/ctx':>8}{'tokens':>12}{'dur_ms':>14}{'turns':>8}"
    print(hdr)
    print("-" * len(hdr))
    tot_fires = tot_ctx = tot_tokens = 0
    tot_dur = 0.0
    all_turns = set()
    for hook, a in ranked[:15]:
        print(f"{hook:<32}{a['fires']:>8}{a['with_ctx']:>8}{a['tokens']:>12}{a['dur_ms']:>14.2f}{len(a['turns']):>8}")
    for hook, a in ranked:
        tot_fires += a["fires"]
        tot_ctx += a["with_ctx"]
        tot_tokens += a["tokens"]
        tot_dur += a["dur_ms"]
        all_turns |= a["turns"]
    print("-" * len(hdr))
    print(f"{'GRAND TOTAL (all hooks)':<32}{tot_fires:>8}{tot_ctx:>8}{tot_tokens:>12}{tot_dur:>14.2f}{len(all_turns):>8}")
    print()


def report_stop(path):
    rows, skipped = load_lines(path)
    agg = defaultdict(lambda: {"blocks": 0, "recent": 0, "reason_bytes": 0, "ts": []})
    CUTOFF = "2026-06-27"
    for r in rows:
        try:
            gate = r["gate_name"]
            ts = r.get("timestamp", "")
            reason = r.get("reason", "") or ""
            a = agg[gate]
            a["blocks"] += 1
            if ts[:10] >= CUTOFF:
                a["recent"] += 1
            a["reason_bytes"] += len(reason.encode("utf-8"))
            a["ts"].append(ts)
        except (KeyError, TypeError):
            skipped += 1

    ranked = sorted(agg.items(), key=lambda kv: kv[1]["blocks"], reverse=True)

    print("=" * 100)
    print(f"TABLE 2: {path}")
    print(f"skipped malformed lines: {skipped}")
    print("=" * 100)
    hdr = f"{'gate_name':<32}{'blocks':>8}{'last7d':>8}{'reason_bytes':>14}  {'min_ts':<32}{'max_ts':<32}"
    print(hdr)
    print("-" * len(hdr))
    tot_blocks = tot_recent = tot_bytes = 0
    for gate, a in ranked:
        mn, mx = min(a["ts"]), max(a["ts"])
        print(f"{gate:<32}{a['blocks']:>8}{a['recent']:>8}{a['reason_bytes']:>14}  {mn:<32}{mx:<32}")
        tot_blocks += a["blocks"]
        tot_recent += a["recent"]
        tot_bytes += a["reason_bytes"]
    print("-" * len(hdr))
    print(f"{'GRAND TOTAL (all gates)':<32}{tot_blocks:>8}{tot_recent:>8}{tot_bytes:>14}")
    print()


if __name__ == "__main__":
    report_ups(F1)
    report_stop(F2)
