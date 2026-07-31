#!/usr/bin/env python3
"""Extract per-model spawn latency from Grok Build session transcripts.

Grok Build's subagent system works in two phases:
1. spawn_subagent(model=X) → returns "Subagent started in background. subagent_id: Y"
2. get_command_or_subagent_output(task_ids=[Y]) → returns result with duration_ms

So the correlation is two-hop: model → subagent_id → duration_ms.

Output: JSON benchmark file at ~/.cache/opencode/spawn-latency-benchmarks.json

Usage:
    python extract_spawn_latency.py [--sessions-dir <path>] [--output <path>] [--verbose]
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

DEFAULT_SESSIONS_DIR = Path.home() / ".grok" / "sessions"
DEFAULT_OUTPUT = Path.home() / ".cache" / "opencode" / "spawn-latency-benchmarks.json"

# Regex patterns
SUBAGENT_ID_RE = re.compile(r'subagent_id[:\s]*([0-9a-f-]+)')
DURATION_RE = re.compile(r'duration_ms[=:]\s*(\d+)')
# Match task sections in get_command_or_subagent_output results
# Format: "--- Task <id> [status] ---" followed later by "duration_ms=<value>"
TASK_SECTION_RE = re.compile(r'(?:--- Task |id=)([0-9a-f-]+|call_[a-f0-9]+).*?duration_ms[=:]\s*(\d+)', re.DOTALL)


def extract_from_session(transcript_path: Path) -> list[dict]:
    """Extract spawn latency records from a single session transcript.

    Two-pass approach:
    Pass 1: Build subagent_id → model map from spawn_subagent calls and results.
    Pass 2: Parse get_command_or_subagent_output results for duration data.
    """
    records = []

    try:
        lines = transcript_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return records

    # Pass 1: build subagent_id → model map
    # Also track: tool_call_id → subagent_id (from spawn result text)
    subagent_to_model: dict[str, str] = {}
    call_id_to_subagent: dict[str, str] = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue

        # Extract model from spawn_subagent tool calls
        if data.get("type") == "assistant":
            for tc in data.get("tool_calls", []):
                if not isinstance(tc, dict):
                    continue
                if tc.get("name") not in ("spawn_subagent", "Task"):
                    continue
                call_id = tc.get("id", "")
                args_raw = tc.get("arguments", "{}")
                if isinstance(args_raw, str):
                    try:
                        args = json.loads(args_raw)
                    except json.JSONDecodeError:
                        args = {}
                elif isinstance(args_raw, dict):
                    args = args_raw
                else:
                    args = {}
                model = args.get("model", "")
                if call_id and model:
                    # Store model by call_id; will link to subagent_id when result arrives
                    call_id_to_subagent[call_id] = {"model": model, "subagent_id": None}

        # Extract subagent_id from spawn_subagent results
        elif data.get("type") == "tool_result":
            tcid = data.get("tool_call_id", "")
            content = str(data.get("content", ""))
            if tcid in call_id_to_subagent and call_id_to_subagent[tcid]["subagent_id"] is None:
                sid_match = SUBAGENT_ID_RE.search(content)
                if sid_match:
                    sid = sid_match.group(1)
                    model = call_id_to_subagent[tcid]["model"]
                    call_id_to_subagent[tcid]["subagent_id"] = sid
                    subagent_to_model[sid] = model

    # Pass 2: find duration data in get_command_or_subagent_output results
    # and any tool_result with duration_ms in content
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "duration_ms" not in line:
            continue
        try:
            data = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue

        if data.get("type") != "tool_result":
            continue

        content = str(data.get("content", ""))
        session_id = transcript_path.parent.name

        # Method 1: parse per-task sections (multi-result get_command_or_subagent_output)
        # Look for patterns like: "id=<subagent_id>...duration_ms=<value>"
        # or "--- Task <id>...duration_ms=<value>"
        found_in_section = False

        # Split by task sections and extract per-task durations
        # The format is typically: --- Task <id> [status] --- ... <subagent_meta>id=<id>, ..., duration_ms=<val>
        task_splits = re.split(r'--- Task ', content)
        for section in task_splits[1:]:  # skip preamble before first "--- Task"
            # First line of section has the task ID
            id_match = re.match(r'([0-9a-f-]+|call_[a-f0-9]+)', section)
            dur_match = DURATION_RE.search(section)
            if id_match and dur_match:
                sid = id_match.group(1)
                duration_ms = int(dur_match.group(1))
                model = subagent_to_model.get(sid, "")
                if model:
                    records.append({
                        "model": model,
                        "duration_ms": duration_ms,
                        "session_id": session_id,
                    })
                    found_in_section = True

        # Method 2: single-result (inline duration with subagent_meta)
        if not found_in_section:
            # Look for subagent_meta tag with id and duration
            meta_matches = re.findall(
                r'id=([0-9a-f-]+).*?duration_ms[=:]\s*(\d+)', content, re.DOTALL
            )
            for sid, dur in meta_matches:
                model = subagent_to_model.get(sid, "")
                if model:
                    duration_ms = int(dur)
                    records.append({
                        "model": model,
                        "duration_ms": duration_ms,
                        "session_id": session_id,
                    })
                    found_in_section = True

    return records


def aggregate_benchmarks(records: list[dict]) -> dict:
    """Aggregate raw records into per-model benchmark statistics."""
    by_model: dict[str, list[int]] = {}
    for r in records:
        model = r["model"]
        by_model.setdefault(model, []).append(r["duration_ms"])

    benchmarks = {}
    for model, durations in sorted(by_model.items()):
        durations_sorted = sorted(durations)
        n = len(durations_sorted)
        avg = statistics.mean(durations_sorted)
        p50 = durations_sorted[n // 2] if n > 0 else 0
        p95_idx = max(0, int(0.95 * n) - 1) if n > 1 else 0
        p95 = durations_sorted[p95_idx] if n > 0 else 0
        max_val = max(durations_sorted) if durations_sorted else 0
        stdev = statistics.stdev(durations_sorted) if n > 1 else 0

        benchmarks[model] = {
            "count": n,
            "avg_ms": round(avg),
            "p50_ms": p50,
            "p95_ms": p95,
            "max_ms": max_val,
            "stdev_ms": round(stdev),
        }

    return benchmarks


def main():
    parser = argparse.ArgumentParser(description="Extract spawn latency from session transcripts")
    parser.add_argument("--sessions-dir", type=Path, default=DEFAULT_SESSIONS_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not args.sessions_dir.exists():
        print(f"ERROR: sessions dir not found: {args.sessions_dir}", file=sys.stderr)
        sys.exit(1)

    all_records = []
    session_count = 0

    for transcript in sorted(args.sessions_dir.rglob("chat_history.jsonl")):
        records = extract_from_session(transcript)
        if records:
            all_records.extend(records)
            session_count += 1
            if args.verbose:
                print(f"  {transcript.parent.name}: {len(records)} spawn records")

    if not all_records:
        print("No spawn latency records found in any transcript.", file=sys.stderr)
        # Debug: check if any sessions have subagent_id mappings
        print("(Debug: checking for subagent activity in recent sessions...)", file=sys.stderr)
        count_with_subagents = 0
        for transcript in sorted(args.sessions_dir.rglob("chat_history.jsonl"))[-50:]:
            text = transcript.read_text(encoding="utf-8", errors="replace")
            if "subagent_id" in text:
                count_with_subagents += 1
        print(f"(Found {count_with_subagents} of last 50 sessions with subagent_id references)", file=sys.stderr)
        sys.exit(0)

    benchmarks = aggregate_benchmarks(all_records)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "version": 1,
        "sessions_scanned": session_count,
        "total_spawns": len(all_records),
        "models": benchmarks,
    }
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"\nSpawn Latency Benchmarks ({len(all_records)} spawns from {session_count} sessions)")
    print(f"{'Model':<35} {'Count':>5} {'Avg':>8} {'P50':>8} {'P95':>8} {'Max':>8} {'Stdev':>8}")
    print("-" * 90)
    for model, stats in sorted(benchmarks.items(), key=lambda x: -x[1]["count"]):
        print(f"{model:<35} {stats['count']:>5} "
              f"{stats['avg_ms']/1000:>7.1f}s "
              f"{stats['p50_ms']/1000:>7.1f}s "
              f"{stats['p95_ms']/1000:>7.1f}s "
              f"{stats['max_ms']/1000:>7.1f}s "
              f"{stats['stdev_ms']/1000:>7.1f}s")

    print(f"\nWritten to: {args.output}")


if __name__ == "__main__":
    main()
