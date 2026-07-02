#!/usr/bin/env python3
"""Approval gate telemetry dashboard - monitor gate fires, block rate, CSV/PNG output."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


HOOKS_DIR = Path(__file__).resolve().parent


def _resolve_telemetry_file() -> Path:
    """Resolve telemetry path via shared state_paths contract (state lives outside code tree)."""
    try:
        sys.path.insert(0, str(HOOKS_DIR / "__lib"))
        from state_paths import SHARED_DIR  # type: ignore[import-not-found]
        return SHARED_DIR / "stop_gate_telemetry.jsonl"
    except Exception:
        return HOOKS_DIR / ".state" / "stop_gate_telemetry.jsonl"


TELEMETRY_FILE = _resolve_telemetry_file()
ARTIFACTS_BASE = Path(os.environ.get("CLAUDE_ARTIFACTS_DIR", str(HOOKS_DIR.parent / ".artifacts")))


def load_telemetry(limit: int | None = None) -> list[dict]:
    """Load telemetry records from JSONL file."""
    records = []
    if not TELEMETRY_FILE.exists():
        return records
    with open(TELEMETRY_FILE, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            try:
                records.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                pass
    return records


def load_approval_states() -> dict[str, dict]:
    """Load all approval state files from artifacts directory."""
    approvals = {}
    if not ARTIFACTS_BASE.exists():
        return approvals
    for approval_file in ARTIFACTS_BASE.glob("*/*approval*.json"):
        try:
            data = json.loads(approval_file.read_text(encoding="utf-8"))
            tid = approval_file.parent.name
            approvals[tid] = {
                "skill": data.get("skill", "unknown"),
                "phase": data.get("phase", "unknown"),
                "approved": data.get("approved", False),
                "ts": data.get("ts", 0),
                "file": str(approval_file),
            }
        except (json.JSONDecodeError, OSError):
            pass
    return approvals


def analyze_gate(gate_name: str, records: list[dict]) -> dict:
    """Analyze a specific gate's performance."""
    gate_records = [r for r in records if r.get("gatename") == gate_name]
    if not gate_records:
        return {"total": 0, "allow": 0, "block": 0, "warn": 0, "block_rate": 0.0}

    decisions = Counter(r.get("decision") for r in gate_records)
    total = len(gate_records)
    return {
        "total": total,
        "allow": decisions.get("allow", 0),
        "block": decisions.get("block", 0),
        "warn": decisions.get("warn", 0),
        "block_rate": decisions.get("block", 0) / total if total > 0 else 0.0,
    }


def print_summary(gate_name: str | None, records: list[dict], approvals: dict[str, dict]) -> None:
    """Print terminal summary of gate performance."""
    print(f"\n{'='*60}")
    print(f" Approval Gate Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    if gate_name:
        stats = analyze_gate(gate_name, records)
        print(f"\n Gate: {gate_name}")
        print(f"   Total fires: {stats['total']}")
        print(f"   Allow: {stats['allow']} | Block: {stats['block']} | Warn: {stats['warn']}")
        print(f"   Block rate: {stats['block_rate']*100:.1f}%")
    else:
        # All gates summary
        gate_stats = defaultdict(lambda: {"total": 0, "block": 0, "allow": 0})
        for r in records:
            gn = r.get("gatename", "unknown") or "unknown"
            gate_stats[gn]["total"] += 1
            d = r.get("decision", "allow")
            gate_stats[gn][d] = gate_stats[gn].get(d, 0) + 1

        print(f"\n Total records: {len(records)}")
        print(f" Unique gates: {len(gate_stats)}")
        print(f"\n {'Gate':<30} {'Total':>8} {'Block':>8} {'Rate':>8}")
        print(f" {'-'*30} {'-'*8} {'-'*8} {'-'*8}")

        for gn, stats in sorted(gate_stats.items(), key=lambda x: -x[1]["total"]):
            rate = stats["block"] / stats["total"] if stats["total"] > 0 else 0
            print(f" {gn:<30} {stats['total']:>8} {stats['block']:>8} {rate*100:>7.1f}%")

    # Active approvals
    print(f"\n Active Approvals: {len(approvals)}")
    if approvals:
        print(f" {'Terminal':<40} {'Skill':<15} {'Phase':<10} {'Age':>8}")
        print(f" {'-'*40} {'-'*15} {'-'*10} {'-'*8}")
        for tid, data in sorted(approvals.items()):
            age = int((time.time() - data["ts"]) / 3600)
            print(f" {tid[:40]:<40} {data['skill']:<15} {data['phase']:<10} {age:>7}h")
    else:
        print("  No active approval states")


def export_csv(gate_name: str | None, records: list[dict], output: Path) -> None:
    """Export telemetry to CSV file."""
    fieldnames = ["timestamp", "gatename", "decision", "reason", "session_id", "terminal_id"]
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            if gate_name and r.get("gatename") != gate_name:
                continue
            writer.writerow({
                "timestamp": r.get("ts", ""),
                "gatename": r.get("gatename", ""),
                "decision": r.get("decision", ""),
                "reason": (r.get("reason") or "")[:100],
                "session_id": r.get("session_id", ""),
                "terminal_id": r.get("terminal_id", ""),
            })
    print(f"\nCSV exported: {output}")


def export_png(gate_name: str | None, records: list[dict], output: Path) -> None:
    """Export telemetry to PNG chart using plotly."""
    if not PLOTLY_AVAILABLE:
        print("\nError: plotly not installed. Install with: pip install plotly")
        return

    # Filter records for gate if specified
    filtered = records if not gate_name else [r for r in records if r.get("gatename") == gate_name]
    if not filtered:
        print(f"\nNo records found for gate: {gate_name}")
        return

    # Aggregate by hour
    hourly = defaultdict(lambda: {"allow": 0, "block": 0, "warn": 0})
    for r in filtered:
        ts = r.get("ts", 0)
        if ts:
            hour = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:00")
            decision = r.get("decision", "allow")
            hourly[hour][decision] = hourly[hour].get(decision, 0) + 1

    # Prepare data for plotly
    hours = sorted(hourly.keys())
    allow_counts = [hourly[h].get("allow", 0) for h in hours]
    block_counts = [hourly[h].get("block", 0) for h in hours]
    warn_counts = [hourly[h].get("warn", 0) for h in hours]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Allow", x=hours, y=allow_counts, marker_color="green"))
    fig.add_trace(go.Bar(name="Block", x=hours, y=block_counts, marker_color="red"))
    fig.add_trace(go.Bar(name="Warn", x=hours, y=warn_counts, marker_color="yellow"))

    fig.update_layout(
        barmode="group",
        title=f"Gate Telemetry: {gate_name or 'All Gates'}",
        xaxis_title="Hour",
        yaxis_title="Count",
        legend_title="Decision",
        height=500,
    )
    fig.write_image(output, width=1200, height=500)
    print(f"\nPNG exported: {output}")


def main():
    parser = argparse.ArgumentParser(description="Approval gate telemetry dashboard")
    parser.add_argument("gate", nargs="?", default=None, help="Gate name to analyze (default: all)")
    parser.add_argument("--limit", "-n", type=int, default=None, help="Limit to last N records")
    parser.add_argument("--csv", "-c", type=Path, default=None, help="Export to CSV file")
    parser.add_argument("--png", "-p", type=Path, default=None, help="Export to PNG chart")
    args = parser.parse_args()

    records = load_telemetry(limit=args.limit)
    approvals = load_approval_states()

    if args.csv:
        export_csv(args.gate, records, args.csv)
    if args.png:
        export_png(args.gate, records, args.png)

    # Always print summary
    print_summary(args.gate, records, approvals)


if __name__ == "__main__":
    main()